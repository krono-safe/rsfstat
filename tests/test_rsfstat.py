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

"""Minimal test suite"""

import itertools
import math

from collections.abc import Iterable

import pytest

import rsfstat as r
from rt_rsf.FrameType import FrameType

################################################################################
# UTILITIES
################################################################################

class DictObj:
    """Utility class to quickly build mock objects from Python dicts"""
    def __init__(self, in_dict:dict):
        assert isinstance(in_dict, dict)
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
                setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
            else:
                setattr(self, key, DictObj(val) if isinstance(val, dict) else val)

    def __str__(self):
        return str(self.__dict__)

    __repr__ = __str__


################################################################################
# TEST DATASETS
################################################################################

rsf0 = DictObj({
    'core': 0,
    'intervals': [
        # 0
        {
            'frames': [
                {
                    'type': FrameType.IDLE,
                    'length_qt': 20000,
                },
            ],
            'length_qtt': 20000,
            'length_st': 2000,
        },

        # 1
        {
            'frames': [
                {
                    'type': FrameType.EXEC,
                    'task': 'T0',
                    'length_qt': 100,
                },
                {
                    'type': FrameType.PADDING,
                    'length_qt': 10,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'T1',
                    'length_qt': 1000,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'T2',
                    'length_qt': 2000,
                },
                {
                    'type': FrameType.IDLE,
                    'length_qt': 20000,
                },
            ],
            'length_qtt': 23110,
            'length_st': 2311,
        },

        # 2
        {
            'frames': [
                {
                    'type': FrameType.EXEC,
                    'task': 'T0',
                    'length_qt': 10000,
                },
                {
                    'type': FrameType.IDLE,
                    'length_qt': 12,
                },
            ],
            'length_qtt': 10012,
            'length_st': 1001,
        },

        # 3
        {
            'frames': [
                {
                    'type': FrameType.EXEC,
                    'task': 'T2',
                    'length_qt': 10000,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'T0',
                    'length_qt': 20000,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'T1',
                    'length_qt': 30000,
                },
                {
                    'type': FrameType.IDLE,
                    'length_qt': 13,
                },
            ],
            'length_qtt': 60013,
            'length_st': 6001,
        },
    ],
    'loop_interval': 1
})

rsf1 = DictObj({
    'core': 1,
    'intervals': [
        # 0
        {
            'frames': [
                {
                    'type': FrameType.IDLE,
                    'length_qt': 43110,
                },
            ],
            'length_qtt': 43110,
            'length_st': 4311,
        },

        # 1
        {
            'frames': [
                {
                    'type': FrameType.EXEC,
                    'task': 'Lorem',
                    'length_qt': 10000,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'Ipsum',
                    'length_qt': 20000,
                },
                {
                    'type': FrameType.EXEC,
                    'task': 'dolor',
                    'length_qt': 30000,
                },
                {
                    'type': FrameType.IDLE,
                    'length_qt': 33135,
                },
            ],
            'length_qtt': 93135,
            'length_st': 9313,
        },
    ],
    'loop_interval': 1
})

_RSF_LEN = 93135

EXPECTED_STEADY_START = 4311
EXPECTED_OVERALL_CPU_LOAD = (
    ((100 + 1000 + 2000) + (10000) + (60000) + (60000)) / (2*_RSF_LEN)
)
EXPECTED_RSF0_LOAD = (100 + 1000 + 2000 + 10000 + 60000) / _RSF_LEN
EXPECTED_RSF1_LOAD = (60000) / 93135
EXPECTED_TASKS_LOAD = {
    0: {
        'T0': (100 + 10000 + 20000) / _RSF_LEN,
        'T1': (1000 + 30000) / _RSF_LEN,
        'T2': (2000 + 10000) / _RSF_LEN,
    },

    1: {
        'Lorem': 10000 / _RSF_LEN,
        'Ipsum': 20000 / _RSF_LEN,
        'Dolor': 30000 / _RSF_LEN,
    }
}

################################################################################

def test_compute_cpu_loads():
    load = r.compute_cpu_loads((rsf0, rsf1))

    assert math.isclose(load.by_core[0], EXPECTED_RSF0_LOAD)
    assert math.isclose(load.by_core[1], EXPECTED_RSF1_LOAD)

    for coreid, coreloads in EXPECTED_TASKS_LOAD.items():
        for task, taskload in coreloads.items():
            assert math.isclose(taskload, EXPECTED_TASKS_LOAD[coreid][task])

    assert math.isclose(load.overall, EXPECTED_OVERALL_CPU_LOAD)


def test_compute_steady_state_start():
    assert r.compute_steady_state_start((rsf0, rsf1)) == EXPECTED_STEADY_START
    return


@pytest.fixture
def walker0() -> r.RSFWalker:
    return r.RSFWalker(rsf0, EXPECTED_STEADY_START)

@pytest.fixture
def walker1() -> r.RSFWalker:
    return r.RSFWalker(rsf1, EXPECTED_STEADY_START)


class TestRSFWalker:

    def test_init(self, walker0, walker1):
        assert walker0.current_interval_idx == 2
        assert walker0.current_frame_idx == 0
        assert walker0.date_in_current_frame == 0
        assert walker0.remaining_intervals_to_finish == 3
        assert not walker0.finished()
        assert walker0.current_interval() == rsf0.intervals[2]
        assert walker0.current_frame() == rsf0.intervals[2].frames[0]
        assert walker0.is_running()

        assert walker1.current_interval_idx == 1
        assert walker1.current_frame_idx == 0
        assert walker1.date_in_current_frame == 0
        assert not walker1.finished()
        assert walker1.current_interval() == rsf1.intervals[1]
        assert walker1.current_frame() == rsf1.intervals[1].frames[0]
        assert walker1.is_running()
        assert walker1.remaining_intervals_to_finish == 1


    def test_compute_next_interval_idx(self, walker0, walker1):
        assert walker0.compute_next_interval_idx(0) == 1
        assert walker0.compute_next_interval_idx(1) == 2
        assert walker0.compute_next_interval_idx(3) == 1

        assert walker1.compute_next_interval_idx(0) == 1
        assert walker1.compute_next_interval_idx(1) == 1


    def test_advance(self, walker0): # also move_to_next_frame()
        walker0.advance(5000)

        assert walker0.is_running()
        assert walker0.date_in_current_frame == 5000
        assert walker0.current_interval() == rsf0.intervals[2]
        assert walker0.current_frame() == rsf0.intervals[2].frames[0]
        assert not walker0.finished()

        walker0.advance(5000)
        assert not walker0.is_running()
        assert walker0.date_in_current_frame == 0
        assert walker0.current_interval() == rsf0.intervals[2]
        assert walker0.current_frame() == rsf0.intervals[2].frames[1]
        assert not walker0.finished()

        walker0.advance(10012)
        assert walker0.is_running()
        assert walker0.date_in_current_frame == 0
        assert walker0.current_interval() == rsf0.intervals[3]
        assert walker0.current_frame() == rsf0.intervals[3].frames[1]
        assert not walker0.finished()

        walker0.advance(30000)
        assert walker0.is_running()
        assert walker0.date_in_current_frame == 10000
        assert walker0.current_interval() == rsf0.intervals[3]
        assert walker0.current_frame() == rsf0.intervals[3].frames[2]
        assert not walker0.finished()


    def test_finished(self, walker0):
        walker0.advance(1)
        assert not walker0.finished()

        walker0.advance(93133)
        assert not walker0.finished()

        walker0.advance(1)
        assert walker0.finished()

        walker0.advance(10)
        assert walker0.finished()


    @staticmethod
    def _getn(it: Iterable, n: int):
        """Return the n first elements of an infinite iterable it"""
        return [
            item for _, item in
            itertools.takewhile(lambda idx: idx[0] < n, enumerate(it))
        ]


    def test_generators(self, walker0):
        """Test the methods `intervals_generator()` and `frames_generator()`"""
        intervals = self._getn(walker0.intervals_generator(), 4)
        frames = self._getn(walker0.frames_generator(), 3)
        assert intervals == rsf0.intervals[2:] + rsf0.intervals[1:3]
        assert frames == rsf0.intervals[2].frames + rsf0.intervals[3].frames[:1]

        # move to the begining of the next interval
        walker0.advance(10012)
        intervals = self._getn(walker0.intervals_generator(), 4)
        assert intervals == rsf0.intervals[3:] + rsf0.intervals[1:]

        # test frame generator when in the middle of a frame
        walker0.advance(5000)
        frames = self._getn(walker0.frames_generator(), 5)
        assert frames == rsf0.intervals[3].frames + rsf0.intervals[1].frames[:1]


    def test_next_running_switch(self, walker0):
        assert walker0.next_running_switch() == 10000

        walker0.advance(5)
        assert walker0.next_running_switch() == 9995

        walker0.advance(9995)
        assert walker0.next_running_switch() == 12

        walker0.advance(12 + 8)
        assert walker0.next_running_switch() == 60000 - 8



def test_compute_parallelism_ratio():
    assert math.isclose(
        r.compute_parallelism_ratio((rsf0, rsf1)),
        (10000 + 50000 - 12)/93135
    )
