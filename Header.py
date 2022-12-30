class Header:
    data_table_count = -1
    data_table_offset = -1
    tag_ref_table_count = -1
    tag_ref_table_offset = 0x50   # always starts directly after the header
    content_table_count = -1
    content_table_offset = -1
    string_offset = -1
    string_count = -1
    string_length = -1
    data_block_table_count = -1
    data_block_table_offset = -1
    data_offset = -1
    data_len = -1   #   Length of the data that is part of the usual data structure and gets referenced by the tables
    other_data_len = -1     #   Length of additional data, in other formats
    some_field_length = -1  #   Length of the field after the strings (unknown purpose)

    def __init__(self):
        pass

    def checkMagic(self,f):
        f.seek(0x0)
        if f.read(4) != b'ucsh':
            self.magic = False
            return False
        else:
            self.magic = True
            return True

    def readHeader(self,f):
        f.seek(0x18)

        # Table 1 data (unknown purpose, but needed to calculate offsets)
        # entry size 0x18
        self.tag_ref_table_offset = 0x50  # fixed, directly after the header
        self.tag_ref_table_count = int.from_bytes(f.read(4),'little')     # 0x18

        # Data Table (contains offsets and sizes of data blocks, referenced by content table)
        # size 0x10
        self.data_table_offset = self.tag_ref_table_offset + self.tag_ref_table_count * 0x18    # 
        self.data_table_count = int.from_bytes(f.read(4),'little')     # 0x1c

        # Content Table (contains references to data table entries and a hash to identify the type of entry)
        # size 0x20
        self.content_table_offset = self.data_table_offset + self.data_table_count * 0x10
        self.content_table_count = int.from_bytes(f.read(4),'little')     # 0x20

        # Data Block Table (contains offsets to model data blocks)
        # size 0x14
        self.data_block_table_offset = self.content_table_offset + self.content_table_count * 0x20
        self.data_block_table_count = int.from_bytes(f.read(4),'little')     # 0x24

        # String stuff
        self.string_offset = self.data_block_table_offset + self.data_block_table_count * 0x14
        self.string_count = int.from_bytes(f.read(4),'little')     # 0x28
        self.string_length = int.from_bytes(f.read(4),'little')     # 0x2c

        self.some_field_length = int.from_bytes(f.read(4),'little')     # 0x30

        # Data offset
        f.seek(0x38)
        self.data_offset = int.from_bytes(f.read(4),'little')     # 0x38
        self.data_len = int.from_bytes(f.read(4),'little')     # 0x3c

    def getOtherData(self,f):
        data_start = self.string_offset + self.string_length + self.some_field_length
        data_len = self.data_offset - data_start
        f.seek(data_start)
        return f.read(data_len)