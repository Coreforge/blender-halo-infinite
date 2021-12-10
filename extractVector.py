import sys

from Header import Header
from DataTable import DataTable
from StringTable import StringTable
from ContentTable import ContentTable


if len(sys.argv) < 2:
    print("Usage: python3 dumpFile.py <file>")
    print()
    print("Dumps the content Table and Strings of the file")
    exit()

class subtable_1_entry:
    def __init__(self):
        self.start = -1
        self.count = -1
        self.some_offset = -1

with open(sys.argv[1],'rb') as f:
    file_header = Header()
    data_entry_table = DataTable()
    string_table = StringTable()
    content_table = ContentTable()

    if not file_header.checkMagic(f):
        print(f"File has the wrong magic")
        exit()

    file_header.readHeader(f)
    data_entry_table.readTable(f,file_header)
    string_table.readStrings(f,file_header)
    content_table.readTable(f,file_header,data_entry_table)

    print(f"\nDumping {len(string_table.strings)} Strings with valid indicies:")
    for x in range(len(string_table.strings)):
        print(f"String {x}: {string_table.strings[x]}")
    
    print(f"\nDumping Content Table:")

    subtable_1 = []

    for x in range(len(content_table.entries)):
        entry = content_table.entries[x]
        hash = entry.hash
        #print(f"\nContent Entry:")
        #print(f"\tHash: {hash}")
        #if entry.data_reference is not None:
        #    print(f"\tReferenced Data:\n\t\tOffset: {hex(entry.data_reference.offset)}\n\t\tSize: {hex(entry.data_reference.size)}")
        #if entry.data_parent is not None:
        #    print(f"\tParent Data:\n\t\tOffset: {hex(entry.data_parent.offset)}\n\t\tSize: {hex(entry.data_parent.size)}")


        if hash == b'\xc2\xefI=1-\xaf\x7f\x8b\x1e,\xa4W\xf5\xbe\x9d':
            # vector header hash?
            offset = entry.data_reference.offset
            f.seek(offset + 0x20)
            some_count = int.from_bytes(f.read(4),'little') # looks like 0x1c sized entries directly after subtable 1, in block with hash b'A\r\x81\x13\x06D\x15<Y\x94v\xaa\x07=\xf1\xa7'
                    # (the offset isn't correct, probably has something to do with parent stuff, but the size fits)
            f.seek(offset + 0x34)
            data_entries_count = int.from_bytes(f.read(4),'little') # the counts of the subtable_1 entries added together result in this value, in block with hash b'B\r\x81\x13\x07D\x15<`\x94v\xaa\x08=\xf1\xa7'
                    # (offset isn't correct, as before), entry size 0x2
            f.seek(offset + 0x48)
            subtable_1_count = int.from_bytes(f.read(4),'little')
            print(f"Subtable 1: {hex(subtable_1_count)}")

        if hash == b'A\r\x81\x13\x06D\x15<Y\x94v\xaa\x07=\xf1\xa7':
            offset = entry.data_reference.offset + 0x68 +  subtable_1_count * 0x8   # something about the offset is broken, so this is needed
            print(f"Offset: {hex(offset)}")
            for  b in range(some_count):
                off = offset + b * 0x1c
                f.seek(off + 0x8)
                print("Data block")
                print(f"Some data block 0x8: {hex(int.from_bytes(f.read(4),'little'))}")
                f.seek(off + 0x18)
                print(f"Some data block 0x18: {hex(int.from_bytes(f.read(4),'little'))}")

        if hash == b'A-\x81\x13\x06D\x15<Y#v\xaa\x07=\xc2\xa7':
            # subtable 1
            offset = entry.data_reference.offset
            for x in range(subtable_1_count):
                entry_off = offset + x * 0x8
                entry = subtable_1_entry()
                f.seek(entry_off)
                print(f"Entry 0x00: {hex(int.from_bytes(f.read(2),'little'))}")
                entry.some_offset = int.from_bytes(f.read(2),'little')
                entry.start = int.from_bytes(f.read(2),'little')
                entry.count = int.from_bytes(f.read(2),'little')
                print(f"Some Offset: {hex(entry.some_offset)} Start: {hex(entry.start)} Length: {hex(entry.count)}")

        if hash == b'B\r\x81\x13\x07D\x15<`\x94v\xaa\x08=\xf1\xa7':
            # data at the end
            offset = entry.data_reference.offset + + 0x68 +  subtable_1_count * 0x8
            for b in range(data_entries_count):
                f.seek(offset + b * 2)
                print(f"Data stuff: {hex(int.from_bytes(f.read(2),'little')) }")