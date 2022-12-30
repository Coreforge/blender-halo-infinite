import mathutils
import struct

def readVec3(data : bytes):
    return mathutils.Vector(struct.unpack('fff',data))