class TagRefTableEntry:
    type = ''
    strOffset = -1
    assetID = -1
    globalID = -1
    parent = -1
    path = ""

    def __init__(self):
        self.type = -1
        self.strOffset = -1
        self.assetID = -1
        self.globalID = -1
        self.parent = -1
        self.path = ""

class TagRefTable:
    # key is the GlobalID
    entries = {}

    def __init__(self):
        self.entries = {}

    def readNullString(self, f, start):
        string = []
        f.seek(start)
        while True:
            char = f.read(1)
            if char == b'\x00':
                return "".join(string)
            string.append(char.decode("utf-8"))

    # pass the 28 byte TagRef struct as a bytes object
    def getRef(self,tagref : bytes):
        globalID = tagref[8:0xc]
        if globalID in self.entries.keys():
            return self.entries[globalID]
        else:
            print(f"Could not find Tag Dependency with Global ID {globalID}")
            return None
        pass

    def readTable(self,f,header):
        stringOffset = header.string_offset + header.string_count * 0x10
        for x in range(header.tag_ref_table_count):
            offset = header.tag_ref_table_offset + x * 0x18
            entry = TagRefTableEntry()
            f.seek(offset)
            entry.type = f.read(4)
            entry.strOffset = f.read(4)
            entry.assetID = f.read(8)
            entry.globalID = f.read(4)
            entry.parent = f.read(4)
            entry.path = self.readNullString(f,stringOffset + entry.strOffset)

            self.entries[entry.globalID] = entry