# Copyright 2022 Krono-Safe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compute statistics on a set of static scheduling plans (RSFs) for an ASTERIOS
Application"""

import argparse
import itertools
import math

from collections import defaultdict
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence, Dict

import colorama

from rt_rsf import pythonize as rsfloader
from rt_rsf.Interval import Interval
from rt_rsf.Frame import Frame

from rt_rsf.RSF import RSF
from rt_rsf.FrameType import FrameType

__version__ = '1.0.0'

################################################################################
# TYPE ALIASES
################################################################################

QuotaTimerTicks = int
SourceTicks = int
Ratio = float # value between 0. and 1.
Index = int
CoreId = int
TaskName = str

################################################################################

class CpuLoads(NamedTuple):
    """Set of CPU load data that can be computed on a set of RSFs"""

    by_core: Dict[CoreId, Ratio]
    """CPU load computed only on a given core, indexed by core id"""

    by_task: Dict[CoreId, Dict[TaskName, Ratio]]
    """CPU load for a given Task (mapped on a single core), indexed by core id
    and then by Task name
    """

    overall: Ratio
    """Global CPU load"""


def compute_cpu_loads(rsfs: Iterable[RSF]) -> CpuLoads:
    """For a given set of RSFs `rsfs`, compute various CPU load data: see the
    documentation of `CpuLoads`.
    """
    # TODO: also compute peak and lowest?
    # TODO: compute CPU load during init?
    overall_load_qtt = 0
    overall_length_qtt = 0
    rsf_loads = {} # load by RSF
    task_loads = {} # load by core(RSF) by task name

    for rsf in rsfs:
        rsf_load_qtt = 0
        rsf_length_qtt = 0
        core_id = rsf.core
        task_loads[core_id] = defaultdict(lambda: 0)

        for interval in rsf.intervals[rsf.loop_interval:]:
            # just a sanity check
            assert interval.length_qtt == sum(frame.length_qt
                                              for frame in interval.frames), \
                "found an inconsistent interval length"

            # run over all exec frames, update the global load for this RSF, and
            # for each Task
            exec_frames = (f for f in interval.frames
                           if f.type == FrameType.EXEC)
            for frame in exec_frames:
                rsf_load_qtt += frame.length_qt
                task_loads[core_id][frame.task] += frame.length_qt

            rsf_length_qtt += interval.length_qtt

        # we've been adding the load for each Task, now we need to divide by the
        # length of the loop to get a ratio
        task_loads[core_id] = {
            taskname: taskload / rsf_length_qtt
            for taskname, taskload in task_loads[core_id].items()
        }

        # compute the load local to this RSF
        rsf_loads[core_id] = rsf_load_qtt / rsf_length_qtt

        # sanity check: the sum of the CPU load of all the Tasks on that core
        # should match the CPU load on that core
        assert math.isclose(
            sum(taskload for taskload in task_loads[core_id].values()),
            rsf_loads[core_id]
        )

        # update the overall load and length used to compute the global CPU load
        overall_load_qtt += rsf_load_qtt
        overall_length_qtt += rsf_length_qtt

    return CpuLoads(
        by_core=rsf_loads,
        by_task=task_loads,
        overall=(overall_load_qtt / overall_length_qtt)
    )


def compute_steady_state_start(rsfs: Iterable[RSF]) -> SourceTicks:
    """Compute the date after which all RSFs have entered their loop"""
    return max(sum(interval.length_st
                   for interval in rsf.intervals[0:rsf.loop_interval])
               for rsf in rsfs)


class RSFWalker:
    """Helper object to iterate over the frames and intervals of an RSF. An
    `RSFWalker` stores a position within the RSF (interval, frame, and date
    within the frame), and can "advance" (see `advance()`) to a given time in
    the future.

    Params:
        rsfdb: RSF database
        start: start date in quota timer ticks to initialize the iterator. It
            *must* match the begining of an interval, or an error is raised.

    Attributes:
        current_interval_idx: index of the current interval. Do not set
            manually, use `advance()`, `move_to_next_interval()` or
            `move_to_next_frame()`.
        current_frame_idx: index of the current frame in the current interval.
            Do not set manually, use `advance()`, `move_to_next_interval()` or
            `move_to_next_frame()`.
        date_in_current_frame: current date in the current frame; 0 means we're
            at the begining of the current frame. Do not set manually, use
            `advance()`, `move_to_next_interval()` or `move_to_next_frame()`.
        remaining_intervals_to_finish: number of intervals to walk before to
            have browsed once a complete loop of the RSF. Do not set manually,
            use `advance()`, `move_to_next_interval()` or
            `move_to_next_frame()`.
    """

    def __init__(self, rsfdb: RSF, start: QuotaTimerTicks):
        self.rsfdb = rsfdb # type: RSF

        def compute_start_interval_idx(start_date: QuotaTimerTicks) -> Index:
            """Compute the index of the interval starting at date
            `start_date`
            """
            cur_date = 0
            start_interval_idx = None

            for interval_idx, interval in enumerate(self.rsfdb.intervals):
                if cur_date == start_date:
                    start_interval_idx = interval_idx
                    break
                cur_date += interval.length_st

            assert start_interval_idx is not None, \
                (f"could not find an interval starting at date {start_date}")
            return start_interval_idx

        self.current_interval_idx = (
            compute_start_interval_idx(start)
        ) # type: Index

        self.current_frame_idx = 0 # type: Index

        assert self.current_interval_idx >= self.rsfdb.loop_interval

        self.date_in_current_frame = 0 # type: QuotaTimerTicks

        self.remaining_intervals_to_finish = (
            len(self.rsfdb.intervals) - self.rsfdb.loop_interval
            if self.current_interval_idx >= self.rsfdb.loop_interval else
            len(self.rsfdb.intervals) - self.current_interval_idx
        ) # type: int


    def current_interval(self) -> Interval:
        """Get the interval corresponding to the current date"""
        return self.rsfdb.intervals[self.current_interval_idx]


    def current_frame(self) -> Frame:
        """Get the frame corresponding to the current_date"""
        return self.current_interval().frames[self.current_frame_idx]


    @staticmethod
    def is_frame_exec(frame: Frame) -> bool:
        """Tells if `frame` is executable"""
        return frame.type == FrameType.EXEC


    def is_running(self) -> bool:
        """Tells if the current frame is executable"""
        return self.is_frame_exec(self.current_frame())


    def compute_next_interval_idx(self, interval_idx=None) -> Index:
        """Compute the index of the interval following the one of index
        `interval_idx`. If `interval_idx` is `None` (default value), then the
        index of the interval following the _current_ interval (as given by
        `current_interval()`) is returned.
        """
        interval_idx = (self.current_interval_idx if interval_idx is None
                        else interval_idx)
        return (interval_idx + 1 if interval_idx != len(self.rsfdb.intervals)-1
                else self.rsfdb.loop_interval)


    def move_to_next_interval(self) -> None:
        """Advance the current time to the begining of the first frame of the
        next interval.
        """
        self.current_frame_idx = 0
        self.date_in_current_frame = 0
        self.current_interval_idx = self.compute_next_interval_idx()
        self.remaining_intervals_to_finish -= 1


    def move_to_next_frame(self) -> None:
        """Advance the current time to the begining of the next frame, possibly
        changing the current interval.
        """
        self.date_in_current_frame = 0
        self.current_frame_idx += 1
        if self.current_frame_idx == len(self.current_interval().frames):
            self.move_to_next_interval()


    def intervals_generator(self, first_interval_idx=None) -> Iterable[Interval]:
        """Returns an infinite generator of `Interval` objects of the RSF in
        chronological order, starting from the interval identified by
        `first_interval_idx`. If `first_interval_idx` is `None` (default value),
        the first interval yielded by the generator matches the one returned by
        `current_interval()`.
        """
        first_interval_idx = first_interval_idx or self.current_interval_idx
        return itertools.chain(
            self.rsfdb.intervals[first_interval_idx:],
            itertools.cycle(self.rsfdb.intervals[self.rsfdb.loop_interval:])
        )


    def frames_generator(self) -> Iterable[Frame]:
        """Returns an infinite generator of `Frame` objects of the RSF in
        chronological order, starting with the current frame, as returned by
        `current_frame()`.
        """
        next_interval_idx = self.compute_next_interval_idx()
        return itertools.chain(
            self.rsfdb.intervals[self.current_interval_idx].frames[
                self.current_frame_idx:],
            itertools.chain.from_iterable(
                interval.frames
                for interval in self.intervals_generator(next_interval_idx)
            )
        )


    def next_running_switch(self) -> QuotaTimerTicks:
        """Compute the date of the next execution switch, i.e. the next date
        where the value returned by `is_running()` will change. In other words,
        if the current frame is executable, it returns the time to the next
        first frame that is *not* executable, and vice-versa.
        """
        # find the next time in qtt the running() will switch
        return sum(
            frame.length_qt
            for frame in itertools.takewhile(
                lambda f: self.is_frame_exec(f) == self.is_running(),
                self.frames_generator()
            )
        ) - self.date_in_current_frame


    def advance(self, advance_qtt: QuotaTimerTicks) -> None:
        """Advance the current date of `advance_qtt` quota timer ticks, possibly
        changing the current frame, and the current interval.
        """
        remaining_in_frame = (self.current_frame().length_qt
                              - self.date_in_current_frame)
        if remaining_in_frame > advance_qtt:
            # we're still within the same frame, just update the current date
            # and return
            self.date_in_current_frame += advance_qtt
            return

        advance_qtt -= remaining_in_frame
        self.move_to_next_frame()
        while advance_qtt > 0:
            if advance_qtt < self.current_frame().length_qt:
                self.date_in_current_frame = advance_qtt
                break

            advance_qtt -= self.current_frame().length_qt
            self.move_to_next_frame()


    def finished(self) -> bool:
        """Returns `True` as soon as we have walked one complete loop of the
        RSF. The object is still usable beyond that point, but `finished()` will
        keep returning `True`.
        """
        return self.remaining_intervals_to_finish <= 0



def compute_parallelism_ratio(rsfs: Sequence[RSF]) -> Ratio:
    """Compute an un-normalized parallelism ratio on all the RSFs listed in
    `rsfs`. The ratio is computed such that:

        - it is linear in time;
        - it equals 0 iff at any given time in steady state, at most one Task is
          scheduled among all the RSFs;
        - it equals 1 iff at any given time in steady state, all the RSFs
          schedule a Task (thus implying that the global CPU load is 100%).

    Because of that last property, the value returned by this function should be
    normalized with the global CPU load to be more meaningful.
    """
    if len(rsfs) < 2:
        return 0.

    steady_start = compute_steady_state_start(rsfs)
    walkers = [RSFWalker(rsf, steady_start) for rsf in rsfs]
    nb_cores = len(rsfs)

    total_len_qtt = 0
    workload_qtt = 0

    while True:
        next_switch = min(walker.next_running_switch() for walker in walkers)
        number_of_running_rsfs = len(
            [walker for walker in walkers if walker.is_running()])
        coeff = max(0, number_of_running_rsfs - 1)
        workload_qtt += coeff * next_switch
        total_len_qtt += next_switch * (nb_cores - 1)

        for walker in walkers:
            walker.advance(next_switch)
        if walkers[0].finished():
            assert all(walker.finished() for walker in walkers)
            break

    return workload_qtt / total_len_qtt


def main():
    """Makes the coffee"""
    colorama.init()

    # parse CLI args
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', '-v', action='version', version=__version__)
    parser.add_argument('rsfdb', nargs='+', type=Path, help="""Path to a runtime
                        RSF database generated by psyko app. These files are
                        found in the generation directory, under the name
                        `core_<N>_rt_rsf.ks` where <N> is the core
                        identifier.""")
    args = parser.parse_args()

    # load RSF dbs
    rsfdbs = []
    for db in args.rsfdb:
        # sanity check
        if not db.exists():
            raise FileNotFoundError(str(db))
        rsfdbs.append(rsfloader.load_from_file(db))

    # print out some nice stuff: CPU load
    from colorama import Fore, Style

    loads = compute_cpu_loads(rsfdbs)

    print(f'{Fore.CYAN}{Style.BRIGHT}⏳ AVERAGE CPU LOAD:'
          f' {Fore.WHITE}{loads.overall * 100.:.2f} %{Style.RESET_ALL}')

    for core_id, load in sorted(loads.by_core.items(), key=lambda k: k[0]):
        print(f'\n  {Fore.YELLOW}Core {core_id}:{Style.RESET_ALL} '
              f'{Style.BRIGHT}{load * 100.:.2f} %{Style.RESET_ALL}')
        for taskname, taskload in sorted(loads.by_task[core_id].items(),
                                         key=lambda k:k[0]):
            print(f'    {taskname:.<32} {taskload * 100.:.2f} %')


    # parallelism ratio
    norm_ratio = compute_parallelism_ratio(rsfdbs) / loads.overall
    print(f'\n{Fore.CYAN}{Style.BRIGHT}🚀 PARALLELISM RATIO: '
          f'{Fore.WHITE}{norm_ratio * 100.:.2f} %{Style.RESET_ALL}')


if __name__ == '__main__':
    main()
