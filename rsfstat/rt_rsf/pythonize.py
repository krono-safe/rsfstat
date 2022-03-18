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

# This file has been generated by Kmodel

from collections import UserDict, OrderedDict
import flatbuffers
from . import RSF

class DotDict(UserDict):
    """Key-value data accessor with dot access
    """
    def __init__(self, **kwargs):
        self.data = dict(**kwargs)

    def __getattr__(self, key):
        assert key in self.data, f"Element '{key}' does not exist"
        return self.data[key]

    def __eq__(self, other):
        if (isinstance(other, dict)):
            return self.data == other
        else:
            return self.data == other.__dict__


def _load_rt_rsf_RSF(obj, data):
    if data is None:
        return None

    s_source = data.Source()
    obj['source'] = '' if s_source is None else s_source.decode('utf-8')
    obj['core'] = data.Core()
    l_intervals = []
    for idx in range(0, data.IntervalsLength()):
        l_intervals.append(_load_rt_rsf_Interval(DotDict(), data.Intervals(idx)))
    obj['intervals'] = l_intervals
    obj['loop_frame'] = data.LoopFrame()
    obj['looping_frame_index'] = data.LoopingFrameIndex()
    obj['nb_frames'] = data.NbFrames()
    obj['ending_frame_index'] = data.EndingFrameIndex()
    obj['loop_interval'] = data.LoopInterval()
    obj['stop_date'] = data.StopDate()
    l_source_tuples = []
    for idx in range(0, data.SourceTuplesLength()):
        l_source_tuples.append(_load_rt_rsf_Tuple(DotDict(), data.SourceTuples(idx)))
    obj['source_tuples'] = l_source_tuples
    l_quota_tuples = []
    for idx in range(0, data.QuotaTuplesLength()):
        l_quota_tuples.append(_load_rt_rsf_Tuple(DotDict(), data.QuotaTuples(idx)))
    obj['quota_tuples'] = l_quota_tuples
    obj['quota_allow_intermediate_tick'] = data.QuotaAllowIntermediateTick()
    s_quota_timer_name = data.QuotaTimerName()
    obj['quota_timer_name'] = '' if s_quota_timer_name is None else s_quota_timer_name.decode('utf-8')
    s_source_timer_name = data.SourceTimerName()
    obj['source_timer_name'] = '' if s_source_timer_name is None else s_source_timer_name.decode('utf-8')
    obj['has_source_timer_name'] = data.HasSourceTimerName()
    return obj


def _load_rt_rsf_Interval(obj, data):
    if data is None:
        return None

    l_frames = []
    for idx in range(0, data.FramesLength()):
        l_frames.append(_load_rt_rsf_Frame(DotDict(), data.Frames(idx)))
    obj['frames'] = l_frames
    obj['nb_frames_to_dump'] = data.NbFramesToDump()
    obj['length_ns'] = data.LengthNs()
    obj['length_st'] = data.LengthSt()
    obj['index'] = data.Index()
    obj['tuple_index'] = data.TupleIndex()
    obj['length_qtt'] = data.LengthQtt()
    return obj


def _load_rt_rsf_Frame(obj, data):
    if data is None:
        return None

    obj['index_in_interval'] = data.IndexInInterval()
    obj['index_in_rsf'] = data.IndexInRsf()
    obj['index_in_frames_table'] = data.IndexInFramesTable()
    obj['distance_to_next_task_frame'] = data.DistanceToNextTaskFrame()
    obj['distance_to_next_frame_start'] = data.DistanceToNextFrameStart()
    obj['type'] = data.Type()
    s_task = data.Task()
    obj['task'] = '' if s_task is None else s_task.decode('utf-8')
    obj['task_core_local_index'] = data.TaskCoreLocalIndex()
    obj['index_in_quota_timer_tuples'] = data.IndexInQuotaTimerTuples()
    obj['has_waitfor_date'] = data.HasWaitforDate()
    obj['waitfor_date'] = data.WaitforDate()
    obj['has_releasein_date'] = data.HasReleaseinDate()
    obj['releasein_date'] = data.ReleaseinDate()
    obj['length_qt'] = data.LengthQt()
    return obj


def _load_rt_rsf_Tuple(obj, data):
    if data is None:
        return None

    obj['index'] = data.Index()
    obj['first_value'] = data.FirstValue()
    obj['reload_value'] = data.ReloadValue()
    obj['nb_reload'] = data.NbReload()
    return obj


def load_from_bytes(data):
    assert data[4:8] == b'KRSF', 'Invalid magic'
    db = RSF.RSF.GetRootAsRSF(data, 0)
    return _load_rt_rsf_RSF(DotDict(), db)

def load_from_file(db_at_path):
    with open(db_at_path, 'rb') as stream:
        data = bytearray(stream.read())
        return load_from_bytes(data)

