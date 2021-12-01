class ContentTableEntry:
    hash = None
    data_reference = None
    data_parent = None
    def __init__(self) -> None:
        pass

class ContentTable:
    entries = []
    def __init__(self) -> None:
        pass

    def readTable(self,f,header,data_table):
        for x in range(header.content_table_count):
            offset = header.content_table_offset + x * 0x20
            entry = ContentTableEntry()
            f.seek(offset)
            entry.hash = f.read(0x10)
            f.seek(offset + 0x14)
            ref_index = int.from_bytes(f.read(4),'little')
            if ref_index  < header.data_table_count:
                entry.data_reference = data_table.entries[ref_index]
            parent_index = int.from_bytes(f.read(4),'little')
            if parent_index < header.data_table_count:
                entry.data_parent = data_table.entries[parent_index]
            self.entries.append(entry)