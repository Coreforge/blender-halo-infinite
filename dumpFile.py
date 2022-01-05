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
import re

from Header import Header
from DataTable import DataTable
from StringTable import StringTable
from ContentTable import ContentTable


def bytesFromByteString(string):
    res = []
    x = 0
    while x < len(string):
        if string[x] == '\\':
            x+=2    # skip the '\x'
            res.append(bytes.fromhex(string[x:x+2]))
            x += 2  # skip the two hex digits
        else:
            res.append(bytes(string[x],'utf-8'))
            x += 1
    b = b''.join(res)
    return b
        

if len(sys.argv) < 2:
    print("Usage: python3 dumpFile.py <options> <file>")
    print()
    print("Dumps the content Table and Strings of the file")
    print()
    print("Options:")
    print("\t-e\t\tprints external (additional data with external format) to stdout and exits")
    print("\t-o\t\tprint each hash only once if it occurrs multiple times")
    print("\t-r <regex\tfilter Strings to match regex>")
    print("\t-rn\t\tnegate the regex")
    print("\t-nC\t\tdon't print content table")
    print("\t-c\t\tcount number of occurences of hashes")
    print("\t-sv\t\tprint out strings with invalid indicies too")
    print("\t-fh <hash>\tonly show entries with the given hash (python byte literal, but without the b infront, eg. '\\xa8\\xda')")
    print("\t-dh <hash> <index>\tdump the data of a specific hash out to the console")
    exit()

export_external_data = False
file_path = ""
only_once = False
match_regex = False
negative_regex = False
regex_filter = ""
print_content_table = True
count_hashes = False
strings_verbose = False
filter_hash = b''
dump_hash = b''
dump_hash_idx = -1

suppress_prints = False

argv_iter = iter(sys.argv[1:])
for o in argv_iter:
    if o[0] == '-':
        # option, not path
        if o == '-e':
            export_external_data = True
            suppress_prints = True
            continue
        if o == '-o':
            only_once = True
            continue
        if o == '-r':
            match_regex = True
            regex_filter = next(argv_iter)
            continue
        if o == '-rn':
            negative_regex = True
            continue
        if o == '-nC':
            print_content_table = False
            continue
        if o == '-c':
            count_hashes = True
            continue
        if o == '-sv':
            strings_verbose = True
            continue
        if o == '-fh':
            filter_hash = bytesFromByteString(next(argv_iter))
            print(f"using filter hash {filter_hash}")
            continue
        if o == '-dh':
            dump_hash = bytesFromByteString(next(argv_iter))
            dump_hash_idx = int(next(argv_iter))
            print_content_table = False     # would mess up printing the data
            suppress_prints = True
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
    string_table.readStrings(f,file_header,strings_verbose)
    content_table.readTable(f,file_header,data_entry_table)
    if not suppress_prints:
        print(f"File has {hex(file_header.data_offset - file_header.string_offset - file_header.string_length - file_header.some_field_length)} bytes of additional (external) data")

    if export_external_data:
        external_data = file_header.getOtherData(f)
        sys.stdout.buffer.write(external_data)
        exit()

    if not suppress_prints:
        print(f"\nDumping {len(string_table.strings)} Strings with valid indicies:")
        nMatch = 0
        for x in range(len(string_table.strings)):
            s = string_table.strings[x]
            if not match_regex:
                print(f"String {x}: {s}")
            elif re.search(regex_filter,s) is not None and not negative_regex:
                print(f"Match String {x}({nMatch}): {s}")
                nMatch += 1
            elif negative_regex and (re.search(regex_filter,s) is None):
                print(f"Match String {x}({nMatch}): {s}")
                nMatch += 1
    

    hashes = []
    hash_counts = {}
    if print_content_table:
        print(f"\nDumping Content Table:")
    for x in range(len(content_table.entries)):
        entry = content_table.entries[x]
        hash = entry.hash
        if hash in hash_counts.keys():
            hash_counts[hash] += 1
        else:
            hash_counts[hash] = 1

        if hash == dump_hash:
            if hash_counts[hash]-1 == dump_hash_idx:    # -1 because the dictionary stores the count, but we need the index here
                if entry.data_reference is not None:
                    f.seek(entry.data_reference.offset)
                    data = f.read(entry.data_reference.size)
                    sys.stdout.buffer.write(data)
                    exit()
        if only_once and hash in hashes:
            continue
        if only_once:
            hashes.append(hash)
        if print_content_table:
            if filter_hash == b'' or hash == filter_hash:
                print(f"\nContent Entry:")
                print(f"\tHash: {hash}")
                if entry.data_reference is not None:
                    print(f"\tReferenced Data:\n\t\tOffset: {hex(entry.data_reference.offset)}\n\t\tSize: {hex(entry.data_reference.size)}")
                if entry.data_parent is not None:
                    print(f"\tParent Data:\n\t\tOffset: {hex(entry.data_parent.offset)}\n\t\tSize: {hex(entry.data_parent.size)}")

    if count_hashes:
        print("Hash counts:")
        for hash in hash_counts.keys():
            print(f"Hash {hash}: {hash_counts[hash]}")                    