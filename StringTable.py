class StringTable:
    strings = []
    name_string = ""
    def __init__(self):
        self.strings = []
        self.name_string = "(unknown path)"
        pass

    def readNullString(self, f, start):
        string = []
        f.seek(start)
        while True:
            char = f.read(1)
            if char == b'\x00':
                return "".join(string)
            string.append(char.decode("utf-8"))

    def readStrings(self,f,header):
        for x in range(header.string_count):
            offset = header.string_offset + x * 0x10
            f.seek(offset)
            unknown_0x0 = int.from_bytes(f.read(4),'little')
            unknown_0x4 = int.from_bytes(f.read(4),'little')
            f.seek(offset + 0x8)
            string_offset = int.from_bytes(f.read(4),'little')
            string_index = int.from_bytes(f.read(4),'little')
            string = self.readNullString(f,offset + (header.string_count-x)*0x10 + string_offset)
            if unknown_0x0 == 0x1 and unknown_0x4 == 0x23c:
                self.name_string = string
            if string_index < header.string_count:
                self.strings.append(string)
                #print(f"Added String {string_index}: {string}")
            else:
                print(f"String {string} has no valid index and will be ignored")