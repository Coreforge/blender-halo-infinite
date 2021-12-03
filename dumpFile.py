#################################################################################
#
#   This script reads Halo Infinite files and dumps the Strings
#   and the Content Table. 
#
#   This script does not export any data. It's purpose is to help find and
#   identify data in Halo infinites file format.
#
#################################################################################

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
    for x in range(len(content_table.entries)):
        entry = content_table.entries[x]
        hash = entry.hash
        print(f"\nContent Entry:")
        print(f"\tHash: {hash}")
        if entry.data_reference is not None:
            print(f"\tReferenced Data:\n\t\tOffset: {hex(entry.data_reference.offset)}\n\t\tSize: {hex(entry.data_reference.size)}")
        if entry.data_parent is not None:
            print(f"\tParent Data:\n\t\tOffset: {hex(entry.data_parent.offset)}\n\t\tSize: {hex(entry.data_parent.size)}")