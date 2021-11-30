class DataTableEntry:
    offset = -1
    size = -1
    def __init__(self):
        pass

class DataTable:
    entries = []
    def __init__(self):
        self.entries = []
        pass

    def readTable(self,f,header):
        for x in range(header.data_table_count):
            offset = header.data_table_offset + x * 0x10
            entry = DataTableEntry()
            #print(offset)
            f.seek(offset)
            entry.size = int.from_bytes(f.read(4),'little')
            f.seek(offset + 0x8)
            entry.offset = int.from_bytes(f.read(4),'little') + header.data_offset
            self.entries.append(entry)
        return