import sys


if 'DEBUG_MODE' in sys.argv:
    from Header import Header
    from DataTable import DataTable, DataTableEntry
    from StringTable import StringTable
    from ContentTable import ContentTable, ContentTableEntry
    from Texture import Texture
else:
    from . Header import Header
    from . DataTable import DataTable, DataTableEntry
    from . StringTable import StringTable
    from . ContentTable import ContentTable, ContentTableEntry
    from . Texture import Texture

class Material:
    file_header = Header
    data_entry_table = DataTable
    string_table = StringTable
    material_content_table = ContentTable
    read_data = False
    def __init__(self):
        self.file_header = Header()
        self.data_entry_table = DataTable()
        self.string_table = StringTable()
        self.material_content_table = ContentTable()
        self.read_data = False
        pass

    def readMaterial(self,path,root):
        with open(path,'rb') as fmat:
            #print(path)
            if not self.file_header.checkMagic(fmat):
                print(f"File {path} has the wrong magic")
            self.file_header.readHeader(fmat)
            #print(f"{hex(self.file_header.content_table_count)} {hex(self.file_header.data_table_count)}")
            self.data_entry_table.readTable(fmat,self.file_header)
            self.string_table.readStrings(fmat,self.file_header)
            self.material_content_table.readTable(fmat,self.file_header,self.data_entry_table)
            #print(f"Content table length: {hex(len(self.material_content_table.entries))}")
            #for s in range(len(self.string_table.strings)):
            #    print(f"Material uses String id {hex(s)}{self.string_table.strings[s]}")

            for x in range(len(self.material_content_table.entries)):
                content_entry = self.material_content_table.entries[x]

                if self.material_content_table.entries[x].data_reference is None:
                    # Entry has no data linked
                    continue

                if content_entry.hash == b'/\x04A\x1b\xed@\x9asd\x15\xdd\xad\r\xd4[\x19':
                    # Texture Entry
                    for off in range(content_entry.data_reference.offset,content_entry.data_reference.offset + content_entry.data_reference.size,0x9c):
                        fmat.seek(off)
                        id = int.from_bytes(fmat.read(4),'little')
                        fmat.seek(off+0x94)
                        idx = int.from_bytes(fmat.read(2),'little')
                        #print(f"Texture? entry id/type: {hex(id)} idx: {hex(idx)}")
                        if id == 0xe5562d34:
                            print(f"Normal map: {self.string_table.strings[idx]}")
                            tex = Texture()
                            tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", path.split("/")[-1]+"normal")
                        if id == 0x1a319e59:
                            print(f"ASG Control map: {self.string_table.strings[idx]}")
                            tex = Texture()
                            tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", path.split("/")[-1]+"asg")
                        if id == 0x9c06e777:
                            print(f"Mask 0 Control map: {self.string_table.strings[idx]}")
                            tex = Texture()
                            tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", path.split("/")[-1]+"mask_0")
                        if id == 0x7fb4ec19:
                            print(f"Mask 1 Control map: {self.string_table.strings[idx]}")
                            tex = Texture()
                            tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", path.split("/")[-1]+"mask_1")
                            
                
                #print(f"Content Table: offset {hex(self.material_content_table.entries[x].data_reference.offset)} size {hex(self.material_content_table.entries[x].data_reference.size)} hash {self.material_content_table.entries[x].hash}")
            self.read_data = True