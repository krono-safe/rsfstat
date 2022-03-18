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

# automatically generated by the FlatBuffers compiler, do not modify

# namespace: rt_rsf

import flatbuffers

from typing import List
from . import Frame

class Interval(object):
    __slots__ = ['_tab']

    # the following type hints were added manually
    frames: List[Frame.Frame]
    length_qtt: int
    length_st: int

    @classmethod
    def GetRootAsInterval(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = Interval()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def IntervalBufferHasIdentifier(cls, buf, offset, size_prefixed=False):
        return flatbuffers.util.BufferHasIdentifier(buf, offset, b"\x4B\x52\x53\x46", size_prefixed=size_prefixed)

    # Interval
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # An interval is a list of frames
    # Interval
    def Frames(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from rt_rsf.Frame import Frame
            obj = Frame()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Interval
    def FramesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # The number of 'exec' frames in the current interval
    # Interval
    def NbFramesToDump(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # The interval length in nanoseconds
    # Interval
    def LengthNs(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint64Flags, o + self._tab.Pos)
        return 0

    # The interval length in source ticks
    # Interval
    def LengthSt(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # index of the interval in the array containing it, should be the key
    # Interval
    def Index(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # index of the source tuple embodying the interval
    # Interval
    def TupleIndex(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # The length of the interval in quota ticks
    # Interval
    def LengthQtt(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(16))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

def IntervalStart(builder): builder.StartObject(7)
def IntervalAddFrames(builder, frames): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(frames), 0)
def IntervalStartFramesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def IntervalAddNbFramesToDump(builder, nbFramesToDump): builder.PrependUint32Slot(1, nbFramesToDump, 0)
def IntervalAddLengthNs(builder, lengthNs): builder.PrependUint64Slot(2, lengthNs, 0)
def IntervalAddLengthSt(builder, lengthSt): builder.PrependUint32Slot(3, lengthSt, 0)
def IntervalAddIndex(builder, index): builder.PrependUint32Slot(4, index, 0)
def IntervalAddTupleIndex(builder, tupleIndex): builder.PrependUint32Slot(5, tupleIndex, 0)
def IntervalAddLengthQtt(builder, lengthQtt): builder.PrependUint32Slot(6, lengthQtt, 0)
def IntervalEnd(builder): return builder.EndObject()
