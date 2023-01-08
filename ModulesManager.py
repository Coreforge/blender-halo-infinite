import os
from pathlib import Path
from ctypes import cdll, c_char_p, create_string_buffer
from io import BytesIO

#
#   This part is just copied from HIME
#
#
class OodleDecompressor:
    """
    Oodle decompression implementation.
    Requires Windows and the external Oodle library.
    """

    def __init__(self, library_path: str) -> None:
        """
        Initialize instance and try to load the library.
        """
        if not os.path.exists(library_path):
            print(f'Looking in {library_path}')
            raise Exception("Could not open Oodle DLL, make sure it is configured correctly.")

        try:
            self.handle = cdll.LoadLibrary(library_path)
        except OSError as e:
            raise Exception(
                "Could not load Oodle DLL, requires Windows and 64bit python to run."
            ) from e

    def decompress(self, payload: bytes, output_size) -> bytes:
        """
        Decompress the payload using the given size.
        """
        output = create_string_buffer(output_size)
        try:
            self.handle.OodleLZ_Decompress(
                c_char_p(payload), len(payload), output, output_size,
                0, 0, 0, None, None, None, None, None, None, 3)
        except OSError:
            return False
        return output.raw



def readNullString(f, start):
    string = []
    f.seek(start)
    while True:
        char = f.read(1)
        if char == b'\x00':
            return "".join(string)
        string.append(char.decode("ascii"))

class ModuleDirectoryEntry:
    parent = None
    children = {}
    name = ""
    type = ""   # either "DIR" or "FILE"
    path = ""
    
    def __init__(self):
        self.children = {}

class ModulesManager:

    oodleDecompressor = None
    resources = []
    resources_updated = False

    modules = []

    # The entry representing the root directory
    rootEntry = ModuleDirectoryEntry()    
    rootEntry.parent = rootEntry
    # The entry that is currently displayed in the list.
    activeNode = rootEntry

    #########################################################
    #
    #   This function builds the file tree structure after
    #   the modules have been read
    #
    #########################################################    
    def buildFileTree(self):
        for mod in self.modules:
            for path in mod.items.keys():
                pathParts = path.split("/")
                currentNode = self.rootEntry
                for part in pathParts:
                    #print(currentNode.name)
                    #if currentNode != self.rootEntry:
                    #    print("Not root node")
                    if part not in currentNode.children.keys():
                        #if part != pathParts[-1]:
                        #    print(f"creating new Folder Node {part}")
                        newNode = ModuleDirectoryEntry()
                        newNode.name = part
                        newNode.parent = currentNode
                        newNode.path = currentNode.path + "/" + part
                        if part == pathParts[-1]:
                            # Last part of the path, so this is a file name
                            newNode.type = "FILE"
                        else:
                            newNode.type = "DIR"
                        currentNode.children[part] = newNode
                    currentNode = currentNode.children[part]
            #print(f"{len(self.rootEntry.children.keys())} Entries on Root")

    def recursiveList(self,path):
        for dir in os.listdir(path):
            if os.path.isfile(path+"/"+dir):
                filename = dir.split("/")[-1]
                if ".module" in filename and not ".module_" in filename:
                    mod = InfiniteModule()
                    mod.path = path+"/"+dir
                    self.modules.append(mod)
            else:
                self.recursiveList(path+"/"+dir)


    #########################################################
    #
    #   This function finds all modules in the deploy path
    #   and adds them to the modules list
    #
    #########################################################    
    def findModules(self,deployPath):
        self.modules = []   # clear current list

        self.recursiveList(deployPath)
        for x in self.modules:
            print(f"Found module {x.path}")

    def readModuleHeader(self,module,f):
        f.seek(0)
        module.header.magic = f.read(4)
        if module.header.magic != b'mohd':
            print(f"Module {module.path} has wrong magic!")
            return

        # The module passed the magic check
        module.valid = True
        f.seek(0x10)
        header = module.header
        header.filecount = int.from_bytes(f.read(4),'little')
        header.stringOffset = 0x48 + module.header.filecount * 0x58 + 0x8
        header.itemTableOffset = 0x48
        f.seek(0x24)
        header.stringSize = int.from_bytes(f.read(4),'little')
        header.table3Count = int.from_bytes(f.read(4),'little')
        header.blockCount = int.from_bytes(f.read(4),'little')
        header.blockTableOffset = header.stringOffset + header.stringSize + header.table3Count * 0x4
        current_offset = header.blockTableOffset + header.blockCount * 0x14
        data_lower = current_offset & 0xfffff000
        add = 0x1000 - (current_offset - data_lower)
        header.dataOffset = current_offset + add
        print(f"dataoffset: {hex(header.dataOffset)}")

    def readModuleItems(self,module,f):
        for off in range(module.header.itemTableOffset, module.header.itemTableOffset + 0x58 * module.header.filecount,0x58):
            item = ModuleItem()
            item.offset = off
            f.seek(off + 0x0a)
            item.blockCount = int.from_bytes(f.read(2),'little')
            item.firstBlockIndex = int.from_bytes(f.read(4),"little")
            f.seek(off + 0x18)
            item.localDataOffset = int.from_bytes(f.read(5),'little')
            f.seek(off + 0x20)
            item.compressedSize = int.from_bytes(f.read(4),'little')
            item.decompressedSize = int.from_bytes(f.read(4),'little')
            f.seek(off + 0x40)
            stringoff = module.header.stringOffset + int.from_bytes(f.read(4),'little')
            
            #print(item.blockCount)
            # replace some characters that aren't allowed/good in file names
            # so otherwise filenames can be handled the same, no matter if the modules were extracted
            # with HIMU or not
            # Also, no backslashes
            item.name = readNullString(f,stringoff).replace(" ","_").replace(":","_").replace("\\","/")
            #print(f"File name: {item.name}")
            item.module = module    # used to later decompressing
            module.items[item.name] = item

    def readModuleBlocks(self,module,f):
        blocks = module.blocks
        #blocks.extend((ModuleBlock(),)*module.header.blockCount)
        count = 0
        for i in range(module.header.blockTableOffset, module.header.blockTableOffset + module.header.blockCount * 0x14,0x14):
            block = ModuleBlock()
            f.seek(i)
            block.compressedOffset = int.from_bytes(f.read(4),'little')
            block.compressedSize = int.from_bytes(f.read(4),'little')
            block.decompressedOffset = int.from_bytes(f.read(4),'little')
            block.decompressedSize = int.from_bytes(f.read(4),'little')
            block.isCompressed = True if int.from_bytes(f.read(4),'little') == 1 else False
            blocks.append(block)
            
    def readItem(self,item):
        print(hex(item.offset))
        with open(item.module.path,'rb') as f:
            offset = item.module.header.dataOffset + item.localDataOffset
            final = BytesIO()
            currentData = []
            if offset > item.module.size:
                print(f"Item {item.name} is located outside of the module")
                return 

            if item.decompressedSize == 0:
                print(f"Item {item.name} is empty")
                return final

            if item.blockCount != 0:
                #print(f"Item {item.name} has {item.blockCount} blocks")
                
                for block in item.module.blocks[item.firstBlockIndex:item.firstBlockIndex + item.blockCount]:
                    #print("block")
                    if not block.isCompressed:
                        # block is not compressed, data can just be read straight
                        #print(f"Block is not compressed")
                        f.seek(offset + block.compressedOffset)
                        currentData.append(f.read(block.compressedSize))
                        #print(f"Size: {len(currentData)}")
                        

                    else:
                        #print(f"Block is compressed")
                        f.seek(offset + block.compressedOffset)
                        compressedData = f.read(block.compressedSize)
                        #print(f"Size: {hex(len(compressedData))}")
                        #print(f"Data offset: {hex(offset)}")
                        #with open("/tmp/extracted.tmp",'w+b') as tmp:
                        #    tmp.write(compressedData)
                        
                        decompressedData = self.oodleDecompressor.decompress(compressedData,block.decompressedSize)
                        if decompressedData == False:
                            print(f"Error decompressing block for item {item.name}")
                        
                        elif len(decompressedData) != block.decompressedSize:
                            print(f"Error decompressing block for item {item.name} (size mismatch)")

                        #else:
                            # everything should be fine
                        currentData.append(decompressedData)

            else:
                # block count of 0, which means there is only one implied block
                if item.compressedSize == item.decompressedSize:
                    #print("Uncompressed implied block")
                    # uncompressed
                    f.seek(offset)
                    currentData.append(f.read(item.compressedSize))
                else:
                    # compressed
                    #print("Compressed implied block")
                    f.seek(offset)
                    compressedData = f.read(item.compressedSize)
                    decompressedData = self.oodleDecompressor.decompress(compressedData,item.decompressedSize)
                    if decompressedData == False:
                        print(f"Error decompressing item {item.name}")
                    
                    elif len(decompressedData) != item.decompressedSize:
                        print(f"Error decompressing item {item.name} (size mismatch)")

                    else:
                        # everything should be fine
                        currentData.append(decompressedData)
            #with open("/tmp/extracted.tmp",'w+b') as tmp:
            #    final.seek(0)
            #    tmp.write(b''.join(currentData))
            final.write(b''.join(currentData))
            final.seek(0)
            return final


    def loadModuleData(self,module):
        with open(module.path,'rb') as f:
            module.size = f.seek(0,2)
            print(f"Reading module {module.path}")
            self.readModuleHeader(module,f)
            print(f"Module has {module.header.filecount} files")
            self.readModuleItems(module,f)
            self.readModuleBlocks(module,f)
            print(f"Module has {module.header.blockCount}")
        
    def loadModules(self):
        for mod in self.modules:
            self.loadModuleData(mod)

    def loadOodle(self,path):
        cwd = os.getcwd()
        tempCWD = Path(path).parent
        # changing the current working directory is needed for linoodle, because it expects the dll in the cwd
        # not needed on windows, but shouldn't hurt anything either
        os.chdir(tempCWD)
        print(tempCWD)
        self.oodleDecompressor = OodleDecompressor(path)
        os.chdir(cwd)
        print("oodle loaded")

    def getFileHandle(self,path,fromModule):
        if not fromModule:
            # reading the whole file into memory should reduce the amount of syscalls due to seeking and only reading a few bytes at a time drastically
            f = open(path,'rb')
            bio = BytesIO(f.read())
            f.close()
            return bio
        else:
            print(f"getting file {path} from module")
            if path[0] == '/':
                path = path[1:]
            usedModule = None
            for mod in self.modules:
                if path in mod.items.keys():
                    usedModule = mod
                    break
            if usedModule is None:
                print(f"Could not find file {path} in the loaded modules")
            #print(f"Item is in module {mod.path}")
            return self.readItem(usedModule.items[path])
            

class ModuleItem:
    offset = 0
    blockCount = 0
    firstBlockIndex = 0
    localDataOffset = 0
    compressedSize = 0
    decompressedSize = 0
    dataOffset = 0
    module = None
    name = ""

class ModuleHeader:
    magic = b''
    filecount = 0
    stringOffset = 0
    itemTableOffset = 0
    table3Count = 0
    blockCount = 0
    stringSize = 0
    blockTableOffset = 0
    dataOffset = 0

class ModuleBlock:
    compressedOffset = 0
    compressedSize = 0
    decompressedOffset = 0
    decompressedSize = 0
    isCompressed = False

class InfiniteModule:
    path = ""
    header = ModuleHeader()
    valid = False
    items = {}  # dict with filenames as keys so the files can be easily retrieved
    blocks = []
    size = 0
    def __init__(self):
        self.items = {}
        self.blocks = []
        self.header = ModuleHeader()


#########################################################
#
#   This class just holds one global object
#
#########################################################
class ModulesManagerContainer:
    manager = ModulesManager()