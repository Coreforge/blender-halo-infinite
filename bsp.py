import mathutils

from . Header import Header
from . TagRefTable import TagRefTable, TagRefTableEntry
from . DataTable import DataTable, DataTableEntry
from . StringTable import StringTable
from . ContentTable import ContentTable, ContentTableEntry
from . Material import Material
from . import ModulesManager

from . util import readVec3

class RTGOInstance:
    def __init__(self):
        self.scale = mathutils.Vector()
        self.forward = mathutils.Vector()
        self.left = mathutils.Vector()
        self.up = mathutils.Vector()
        self.position = mathutils.Vector()
        self.rtgo_path = TagRefTableEntry()
        self.foliage_material_palette = TagRefTableEntry()
        # there's still some missing stuff here
        pass

class BSPFile:

    def __init__(self,f):

        # read the file
        self.file_header = Header()
        self.file_header.readHeader(f)

        self.tag_ref_table = TagRefTable()
        self.tag_ref_table.readTable(f,self.file_header)

        self.data_table = DataTable()
        self.data_table.readTable(f,self.file_header)

        self.string_table = StringTable()
        self.string_table.readStrings(f,self.file_header)

        self.content_table = ContentTable()
        self.content_table.readTable(f,self.file_header,self.data_table)
        pass


    # essentially, iterate over the content table and if the 'hash' or rather GUID matches b'\xe6\x06\xed\x1a\xb4F\xac\xf1\xd2\xf2*\x8aJ\xb5Q\xda' and content_table_entry.data_reference is not None
    # call this function and pass to it the file handle for the bsp, the total instance count and the Data Table entry (content_table_entry.data_reference)
    def readInstances(self,f,count : int, dte : DataTableEntry):
        instances = [RTGOInstance(),]*count
        for x in range(count):
            offset = dte.offset + x * 0x140
            instance = RTGOInstance()
            f.seek(offset)
            instance.scale = readVec3(f.read(12))
            instance.forward = readVec3(f.read(12))
            instance.left = readVec3(f.read(12))
            instance.up = readVec3(f.read(12))
            instance.position = readVec3(f.read(12))
            instance.rtgo_path = self.tag_ref_table.getRef(f.read(28))
            instance.foliage_material_palette = self.tag_ref_table.getRef(f.read(28))
            instances[x] = instance       

        return instances
        