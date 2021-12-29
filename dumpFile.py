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
    print("Usage: python3 dumpFile.py <options> <file>")
    print()
    print("Dumps the content Table and Strings of the file")
    print()
    print("Options:")
    print("\t-e\tprints external (additional data with external format) to stdout and exits")
    exit()

export_external_data = False
file_path = ""

for o in sys.argv[1:]:
    if o[0] == '-':
        # option, not path
        if o == '-e':
            export_external_data = True
            continue
        print(f"Unknown option {o}")
        exit()
    else:
        # file path
        file_path = o

with open(file_path,'rb') as f:
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

    print(f"File has {hex(file_header.data_offset - file_header.string_offset - file_header.string_length - file_header.some_field_length)} bytes of additional (external) data")

    if export_external_data:
        external_data = file_header.getOtherData(f)
        sys.stdout.buffer.write(external_data)
        exit()


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