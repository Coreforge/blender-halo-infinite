import sys
import os
import math
from io import BytesIO

#from numpy.lib.function_base import append

import numpy as np
from dataclasses import dataclass, fields, field
from typing import List

#from BC5 import DecompressBC5_DualChannel_Internal, snorm

if 'DEBUG_MODE' in sys.argv:
    from Header import Header
    from DataTable import DataTable, DataTableEntry
    from StringTable import StringTable
    from ContentTable import ContentTable, ContentTableEntry    
    import BC5
else:
    from . Header import Header
    from . DataTable import DataTable, DataTableEntry
    from . StringTable import StringTable
    from . ContentTable import ContentTable, ContentTableEntry
    from . import BC5



DXGI_FORMAT = [ "DXGI_FORMAT_UNKNOWN",
                "DXGI_FORMAT_R32G32B32A32_TYPELESS",
                "DXGI_FORMAT_R32G32B32A32_FLOAT",
                "DXGI_FORMAT_R32G32B32A32_UINT",
                "DXGI_FORMAT_R32G32B32A32_SINT",
                "DXGI_FORMAT_R32G32B32_TYPELESS",
                "DXGI_FORMAT_R32G32B32_FLOAT",
                "DXGI_FORMAT_R32G32B32_UINT",
                "DXGI_FORMAT_R32G32B32_SINT",
                "DXGI_FORMAT_R16G16B16A16_TYPELESS",
                "DXGI_FORMAT_R16G16B16A16_FLOAT",
                "DXGI_FORMAT_R16G16B16A16_UNORM",
                "DXGI_FORMAT_R16G16B16A16_UINT",
                "DXGI_FORMAT_R16G16B16A16_SNORM",
                "DXGI_FORMAT_R16G16B16A16_SINT",
                "DXGI_FORMAT_R32G32_TYPELESS",
                "DXGI_FORMAT_R32G32_FLOAT",
                "DXGI_FORMAT_R32G32_UINT",
                "DXGI_FORMAT_R32G32_SINT",
                "DXGI_FORMAT_R32G8X24_TYPELESS",
                "DXGI_FORMAT_D32_FLOAT_S8X24_UINT",
                "DXGI_FORMAT_R32_FLOAT_X8X24_TYPELESS",
                "DXGI_FORMAT_X32_TYPELESS_G8X24_UINT",
                "DXGI_FORMAT_R10G10B10A2_TYPELESS",
                "DXGI_FORMAT_R10G10B10A2_UNORM",
                "DXGI_FORMAT_R10G10B10A2_UINT",
                "DXGI_FORMAT_R11G11B10_FLOAT",
                "DXGI_FORMAT_R8G8B8A8_TYPELESS",
                "DXGI_FORMAT_R8G8B8A8_UNORM",
                "DXGI_FORMAT_R8G8B8A8_UNORM_SRGB",
                "DXGI_FORMAT_R8G8B8A8_UINT",
                "DXGI_FORMAT_R8G8B8A8_SNORM",
                "DXGI_FORMAT_R8G8B8A8_SINT",
                "DXGI_FORMAT_R16G16_TYPELESS",
                "DXGI_FORMAT_R16G16_FLOAT",
                "DXGI_FORMAT_R16G16_UNORM",
                "DXGI_FORMAT_R16G16_UINT",
                "DXGI_FORMAT_R16G16_SNORM",
                "DXGI_FORMAT_R16G16_SINT",
                "DXGI_FORMAT_R32_TYPELESS",
                "DXGI_FORMAT_D32_FLOAT",
                "DXGI_FORMAT_R32_FLOAT",
                "DXGI_FORMAT_R32_UINT",
                "DXGI_FORMAT_R32_SINT",
                "DXGI_FORMAT_R24G8_TYPELESS",
                "DXGI_FORMAT_D24_UNORM_S8_UINT",
                "DXGI_FORMAT_R24_UNORM_X8_TYPELESS",
                "DXGI_FORMAT_X24_TYPELESS_G8_UINT",
                "DXGI_FORMAT_R8G8_TYPELESS",
                "DXGI_FORMAT_R8G8_UNORM",
                "DXGI_FORMAT_R8G8_UINT",
                "DXGI_FORMAT_R8G8_SNORM",
                "DXGI_FORMAT_R8G8_SINT",
                "DXGI_FORMAT_R16_TYPELESS",
                "DXGI_FORMAT_R16_FLOAT",
                "DXGI_FORMAT_D16_UNORM",
                "DXGI_FORMAT_R16_UNORM",
                "DXGI_FORMAT_R16_UINT",
                "DXGI_FORMAT_R16_SNORM",
                "DXGI_FORMAT_R16_SINT",
                "DXGI_FORMAT_R8_TYPELESS",
                "DXGI_FORMAT_R8_UNORM",
                "DXGI_FORMAT_R8_UINT",
                "DXGI_FORMAT_R8_SNORM",
                "DXGI_FORMAT_R8_SINT",
                "DXGI_FORMAT_A8_UNORM",
                "DXGI_FORMAT_R1_UNORM",
                "DXGI_FORMAT_R9G9B9E5_SHAREDEXP",
                "DXGI_FORMAT_R8G8_B8G8_UNORM",
                "DXGI_FORMAT_G8R8_G8B8_UNORM",
                "DXGI_FORMAT_BC1_TYPELESS",
                "DXGI_FORMAT_BC1_UNORM",
                "DXGI_FORMAT_BC1_UNORM_SRGB",
                "DXGI_FORMAT_BC2_TYPELESS",
                "DXGI_FORMAT_BC2_UNORM",
                "DXGI_FORMAT_BC2_UNORM_SRGB",
                "DXGI_FORMAT_BC3_TYPELESS",
                "DXGI_FORMAT_BC3_UNORM",
                "DXGI_FORMAT_BC3_UNORM_SRGB",
                "DXGI_FORMAT_BC4_TYPELESS",
                "DXGI_FORMAT_BC4_UNORM",
                "DXGI_FORMAT_BC4_SNORM",
                "DXGI_FORMAT_BC5_TYPELESS",
                "DXGI_FORMAT_BC5_UNORM",
                "DXGI_FORMAT_BC5_SNORM",
                "DXGI_FORMAT_B5G6R5_UNORM",
                "DXGI_FORMAT_B5G5R5A1_UNORM",
                "DXGI_FORMAT_B8G8R8A8_UNORM",
                "DXGI_FORMAT_B8G8R8X8_UNORM",
                "DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM",
                "DXGI_FORMAT_B8G8R8A8_TYPELESS",
                "DXGI_FORMAT_B8G8R8A8_UNORM_SRGB",
                "DXGI_FORMAT_B8G8R8X8_TYPELESS",
                "DXGI_FORMAT_B8G8R8X8_UNORM_SRGB",
                "DXGI_FORMAT_BC6H_TYPELESS",
                "DXGI_FORMAT_BC6H_UF16",
                "DXGI_FORMAT_BC6H_SF16",
                "DXGI_FORMAT_BC7_TYPELESS",
                "DXGI_FORMAT_BC7_UNORM",
                "DXGI_FORMAT_BC7_UNORM_SRGB",
                "DXGI_FORMAT_AYUV",
                "DXGI_FORMAT_Y410",
                "DXGI_FORMAT_Y416",
                "DXGI_FORMAT_NV12",
                "DXGI_FORMAT_P010",
                "DXGI_FORMAT_P016",
                "DXGI_FORMAT_420_OPAQUE",
                "DXGI_FORMAT_YUY2",
                "DXGI_FORMAT_Y210",
                "DXGI_FORMAT_Y216",
                "DXGI_FORMAT_NV11",
                "DXGI_FORMAT_AI44",
                "DXGI_FORMAT_IA44",
                "DXGI_FORMAT_P8",
                "DXGI_FORMAT_A8P8",
                "DXGI_FORMAT_B4G4R4A4_UNORM",
                "DXGI_FORMAT_P208",
                "DXGI_FORMAT_V208",
                "DXGI_FORMAT_V408",
                "DXGI_FORMAT_SAMPLER_FEEDBACK_MIN_MIP_OPAQUE",
                "DXGI_FORMAT_SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE",
                "DXGI_FORMAT_FORCE_UINT"]


@dataclass
class DX10Header:
    MagicNumber: int = int(0)
    dwSize: int = int(0)
    dwFlags: int = int(0)
    dwHeight: int = int(0)
    dwWidth: int = int(0)
    dwPitchOrLinearSize: int = int(0)
    dwDepth: int = int(0)
    dwMipMapCount: int = int(0)
    dwReserved1: List[int] = field(default_factory=list)  # size 11, [11]
    dwPFSize: int = int(0)
    dwPFFlags: int = int(0)
    dwPFFourCC: int = int(0)
    dwPFRGBBitCount: int = int(0)
    dwPFRBitMask: int = int(0)
    dwPFGBitMask: int = int(0)
    dwPFBBitMask: int = int(0)
    dwPFABitMask: int = int(0)
    dwCaps: int = int(0)
    dwCaps2: int = int(0)
    dwCaps3: int = int(0)
    dwCaps4: int = int(0)
    dwReserved2: int = int(0)
    dxgiFormat: int = int(0)
    resourceDimension: int = int(0)
    miscFlag: int = int(0)
    arraySize: int = int(0)
    miscFlags2: int = int(0)


@dataclass
class DDSHeader:
    MagicNumber: int = int(0)
    dwSize: int = int(0)
    dwFlags: int = int(0)
    dwHeight: int = int(0)
    dwWidth: int = int(0)
    dwPitchOrLinearSize: int = int(0)
    dwDepth: int = int(0)
    dwMipMapCount: int = int(0)
    dwReserved1: List[int] = field(default_factory=list)  # size 11, [11]
    dwPFSize: int = int(0)
    dwPFFlags: int = int(0)
    dwPFFourCC: int = int(0)
    dwPFRGBBitCount: int = int(0)
    dwPFRBitMask: int = int(0)
    dwPFGBitMask: int = int(0)
    dwPFBBitMask: int = int(0)
    dwPFABitMask: int = int(0)
    dwCaps: int = int(0)
    dwCaps2: int = int(0)
    dwCaps3: int = int(0)
    dwCaps4: int = int(0)
    dwReserved2: int = int(0)


class TextureObject:
    def __init__(self):
        self.width = -1
        self.height = -1
        self.texture_format = -1
        self.array_size = 1
        self.fb = b""

class Texture:
    file_header = Header
    data_entry_table = DataTable
    string_table = StringTable
    content_table = ContentTable
    read_data = False
    blender_texture = None

    def __init__(self):
        self.file_header = Header()
        self.data_entry_table = DataTable()
        self.string_table = StringTable()
        self.content_table = ContentTable()
        self.read_data = False
        self.blender_texture = None
        pass


    def createDDSHeader(self,tex):

        form = DXGI_FORMAT[tex.texture_format]
        if '_BC' in form:
            dds_header = DX10Header()  # 0x0
        else:
            dds_header = DDSHeader()  # 0x0

        dds_header.MagicNumber = int('20534444', 16)  # 0x4
        dds_header.dwSize = 124  # 0x8
        dds_header.dwFlags = (0x1 + 0x2 + 0x4 + 0x1000) + 0x8
        dds_header.dwHeight = tex.height  # 0xC
        dds_header.dwWidth = tex.width  # 0x10
        dds_header.dwDepth = 0
        dds_header.dwMipMapCount = 0
        dds_header.dwReserved1 = [0]*11
        dds_header.dwPFSize = 32
        dds_header.dwPFRGBBitCount = 0
        dds_header.dwPFRGBBitCount = 32
        dds_header.dwPFRBitMask = 0xFF  # RGBA so FF first, but this is endian flipped
        dds_header.dwPFGBitMask = 0xFF00
        dds_header.dwPFBBitMask = 0xFF0000
        dds_header.dwPFABitMask = 0xFF000000
        dds_header.dwCaps = 0x1000
        dds_header.dwCaps2 = 0
        dds_header.dwCaps3 = 0
        dds_header.dwCaps4 = 0
        dds_header.dwReserved2 = 0
        if '_BC' in form:
            dds_header.dwPFFlags = 0x1 + 0x4  # contains alpha data + contains compressed RGB data
            dds_header.dwPFFourCC = int.from_bytes(b'\x44\x58\x31\x30', byteorder='little')
            dds_header.dxgiFormat = tex.texture_format
            dds_header.resourceDimension = 3  # DDS_DIMENSION_TEXTURE2D
            if tex.array_size % 6 == 0:
                # Compressed cubemap
                dds_header.miscFlag = 4
                dds_header.arraySize = int(tex.array_size / 6)
            else:
                # Compressed BCn
                dds_header.miscFlag = 0
                dds_header.arraySize = 1
        else:
            # Uncompressed
            dds_header.dwPFFlags = 0x1 + 0x40  # contains alpha data + contains uncompressed RGB data
            dds_header.dwPFFourCC = 0
            dds_header.miscFlag = 0
            dds_header.arraySize = 1
            dds_header.miscFlags2 = 0x1

        dds_data = []
        # build dds header as bytes
        for f in fields(dds_header):
            if f.type == int:
                #flipped = "".join(gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(getattr(header, f.name)))[2:], 8), 8))
                dds_data.append(int.to_bytes(getattr(dds_header,f.name),4,'little'))
            elif f.type == List[int]:
                #flipped = ''
                for val in getattr(dds_header, f.name):
                    dds_data.append(int.to_bytes(val,4,'little'))
                    #flipped += "".join(
                    #    gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(val))[2:], 8), 8))
            else:
                print(f'ERROR {f.type}')
                return None
        return dds_data
        #write_file(dds_header, tex, full_save_path)

    def readTextureData(self,data,width,height,import_settings, format):
        if format == 0x54:
            #with open("/home/ich/haloRIP/blender_plugin/normal.dds",'w+b') as normal:
            #    normal.write(b''.join(dds_data))
            #decoded_data = texture2ddecoder.decode_bc5(img_data,width,height)
            decoded_data = [0,]*(width*height*4)
            for x in range(len(data)//16):
                block1 = int.from_bytes(data[x*16:(x*16)+4],'little')
                block2 = int.from_bytes(data[(x*16)+4:(x*16)+8],'little')
                block3 = int.from_bytes(data[(x*16)+8:(x*16)+12],'little')
                block4 = int.from_bytes(data[(x*16)+12:(x*16)+16],'little')
                decompressed_block = BC5.DecompressBC5_DualChannel_Internal([block1,block2,block3,block4])
                blockX = x % (width//4)
                blockY = x // (width//4)
                #print(f"Block X {blockX} Block Y {blockY}")
                if import_settings.norm_signed:
                    for subY in range(4):
                        for subX in range(4):
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4] = (decompressed_block[subY * 4 + subX][0])
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 1] = (decompressed_block[subY * 4 + subX][1])
                            intermediate = (1 - ((decompressed_block[subY * 4 + subX][0]))**2 - ((decompressed_block[subY * 4 + subX][1]))**2)
                            if intermediate < 0:
                                r = 0#-1+math.sqrt(abs(intermediate))
                            else:
                                r = math.sqrt(intermediate)
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 2] = r#mathutils.Vector(((decompressed_block[subY * 4 + subX][0]),(decompressed_block[subY * 4 + subX][1]))).dot(
                             #   mathutils.Vector(((decompressed_block[subY * 4 + subX][0]),(decompressed_block[subY * 4 + subX][1])))
                            #)
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 3] = 1
                else:
                    for subY in range(4):
                        for subX in range(4):
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4] = (decompressed_block[subY * 4 + subX][0]) / 2 + 0.5
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 1] = (decompressed_block[subY * 4 + subX][1]) / 2 + 0.5
                            intermediate = (1 - ((decompressed_block[subY * 4 + subX][0]))**2 - ((decompressed_block[subY * 4 + subX][1]))**2)
                            if intermediate < 0:
                                r = 0#-1+math.sqrt(abs(intermediate))
                            else:
                                r = math.sqrt(intermediate)
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 2] = r#mathutils.Vector(((decompressed_block[subY * 4 + subX][0]),(decompressed_block[subY * 4 + subX][1]))).dot(
                             #   mathutils.Vector(((decompressed_block[subY * 4 + subX][0]),(decompressed_block[subY * 4 + subX][1])))
                            #)
                            decoded_data[((((blockY * 4)+subY) * width) + (blockX * 4) + subX) * 4 + 3] = 1
            #img_final = [0.0]*(len(decoded_data))
            #for x in range(len(decoded_data)):
            #    img_final[x] = decoded_data[x] / 255
            #img_final = [snorm(x) for x in decoded_data]
            #for x in range(len(img_final)//4):
            #    img_final[(x*4)+3] = 1
            #print(f"max: {max(img_final)} min: {min(img_final)}")
            #img.pixels = decoded_data
            return decoded_data

        if format == 0x47 or format == 0x48:
            import texture2ddecoder
            decoded_data = texture2ddecoder.decode_bc1(data,width,height)
            #img_final = [0.0]*(len(decoded_data))
            #for x in range(len(decoded_data)):
            #    img_final[x] = decoded_data[x] / 255
            #img_final = [x/255 for x in decoded_data]
            dat = [0.0,]*(width*height*4)
            for x in range(width*height):
                dat[x*4] = decoded_data[x*4+2] / 255
                dat[x*4+1] = decoded_data[x*4+1] / 255
                dat[x*4+2] = decoded_data[x*4] / 255
                dat[x*4+3] = decoded_data[x*4+3] / 255
            #img.pixels = dat
            return dat

        if format == 0x62 or format == 0x63:
            # BC7_UNORM or BC7_
            import texture2ddecoder
            decoded_data = texture2ddecoder.decode_bc7(data,width,height)
            dat = [0.0,]*(width*height*4)
            for x in range(width*height):
                dat[x*4] = decoded_data[x*4+2] / 255
                dat[x*4+1] = decoded_data[x*4+1] / 255
                dat[x*4+2] = decoded_data[x*4] / 255
                dat[x*4+3] = decoded_data[x*4+3] / 255
            return dat


        if format == 0x41:
            # A8_UNORM
            dat = [0.0,]*(width*height*4)
            for x in range(len(data)):
                dat[x*4] = 0.0
                dat[x*4+1] = 0.0
                dat[x*4+2] = 0.0
                dat[x*4+3] = data[x]/255
            return dat

        if format == 0x57:
            # B8G8R8A8_UNORM
            dat = [0.0,]*(width*height*4)
            for x in range(width*height):
                dat[x*4] = data[x*4+2]/255
                dat[x*4+1] = data[x*4+1]/255
                dat[x*4+2] = data[x*4]/255
                dat[x*4+3] = data[x*4+3]/255
            return dat

        if format == 0x4d:
            # BC3_UNORM
            import texture2ddecoder
            decoded_data = texture2ddecoder.decode_bc3(data,width,height)
            dat = [0.0,]*(width*height*4)
            for x in range(width*height):
                dat[x*4] = decoded_data[x*4+2] / 255
                dat[x*4+1] = decoded_data[x*4+1] / 255
                dat[x*4+2] = decoded_data[x*4] / 255
                dat[x*4+3] = decoded_data[x*4+3] / 255
            return dat


        print("Texture format currently unsupported")
        #
        #img_final = [0.0]*(width*height*4)
        #src_pos = 0
        #print(f"Source Data Size: {hex(len(img_data))} Pixels: {hex(width*height)}")
        #for p in range(width*height-2):
        #    if src_pos >= len(img_data)-2:
        #        break
        #    img_final[p*4] = img_data[src_pos] / 255
        #    src_pos += 2
        #    img_final[p*4+1] = img_data[src_pos] / 255
        #    #src_pos += 
        #    img_final[p*4+2] = 0
        #    img_final[p*4+3] = 1
        #img.pixels = img_final[0:width*height*4]
        #tex.image = img
        #self.blender_texture = tex


    # return union of (width, height, data) with data being normalized RGBA
    def readTextureImage(self,path, import_settings):
        import texture2ddecoder
        with open(path,'rb') as f:
            local_fh = Header()
            local_det = DataTable()
            local_strt = StringTable()
            local_ctt = ContentTable()
            if not local_fh.checkMagic(f):
                print(f"File has the wrong magic")

            local_fh.readHeader(f)
            local_det.readTable(f,local_fh)
            local_strt.readStrings(f,local_fh)
            local_ctt.readTable(f,local_fh,local_det)

            handle_name = path.split('/')[-1]
            print(f"Texture File name: {handle_name}")
            format = -1
            max_width = -1
            max_height = -1

            for x in range(len(local_ctt.entries)):
                    content_entry = local_ctt.entries[x]

                    if local_ctt.entries[x].data_reference is None:
                        # Entry has no data linked
                        continue
                    
                    if content_entry.hash == b'R\xab5#hBJ\xc2}\x8fr\x94#\x19m\xd3':
                        # bitmap handle info stuff
                        offset = content_entry.data_reference.offset
                        f.seek(offset + 0xe4)
                        frame_count = int.from_bytes(f.read(4),'little')

                    if content_entry.hash == b'*\x80\xeb\x8akA\n\xf6\x9cp\x0c\x97MU6#':
                        # DDS Header info stuff
                        offset = content_entry.data_reference.offset
                        f.seek(offset + 0x14)
                        embed_data_len = int.from_bytes(f.read(4),'little')
                        embed_data_offset = offset + content_entry.data_reference.size
                        f.seek(offset + 0x1d)
                        format = int.from_bytes(f.read(2),'little')
                        f.seek(offset + 0x40)
                        resourceDimension = int.from_bytes(f.read(4),'little')

                    if content_entry.hash == b'jQ\xb0\xde\x98D\x1c\x02\xcd\xc6A\x99i\xaa\x94\xc2':
                        f.seek(content_entry.data_reference.offset)
                        max_width = int.from_bytes(f.read(2),'little')
                        max_height = int.from_bytes(f.read(2),'little')
                        pass

                    if content_entry.hash == b'9, \xd1\xdcH\xfc\xbdI\xde+\x81\x93\xaf\xe8\xb0':
                        # One of these hashes per resource file
                        nResourceFiles = content_entry.data_reference.size//0x10    # there are 0x10 bytes for each file
                        for chunk in range(nResourceFiles):
                            offset = content_entry.data_reference.offset + chunk * 0x10
                            f.seek(offset + 0xa)
                            mipmap = int.from_bytes(f.read(1),'little')
                            if mipmap != import_settings.mipmap:
                                continue
                            f.seek(offset + 0xc)
                            width = int.from_bytes(f.read(2),'little')
                            height = int.from_bytes(f.read(2),'little')
                            chunk_name = path + "[" + str(chunk) + "_bitmap_resource_handle.chunk" + str(chunk) + "]"
                            print(f"Reading texture block {chunk_name}")
                            print(f"Width: {width} Height: {height} Format: {DXGI_FORMAT[format]} {hex(format)}")
                            with open(chunk_name, 'rb') as chunk_file:
                                img_data = chunk_file.read()

                                #tex_obj = TextureObject()
                                #tex_obj.width = width
                                #tex_obj.height = height
                                #tex_obj.texture_format = format
                                pixels = self.readTextureData(img_data,width,height,import_settings,format)
                                #dds_data = self.createDDSHeader(tex_obj)
#
                                #if dds_data == None:
                                #    print("Couldn't build DDS Header")
                                #    continue
                                #dds_data.append(img_data)

            if embed_data_len != 0:
                # if the length is not 0, that means that there is some bitmap data embedded in the main .bitmap file.
                # This probably also means that there aren't any external chunk files, so the embedded data has to be read
                # There don't seem to be mipmaps with these files, so that won't get checked
                f.seek(embed_data_offset)
                img_data = f.read(embed_data_len)
                print(f"Bitmap with embedded data! Width: {max_width} Height: {max_height} Format: {DXGI_FORMAT[format]} {hex(format)}")

                pixels = self.readTextureData(img_data,max_width,max_height,import_settings,format)

            return (width,height,pixels)

    def readTexture(self,path,name, import_settings):
        frame_count = -1
        with open(path,'rb') as fh:
            local_fh = Header()
            if not local_fh.checkMagic(fh):
                print(f"File has the wrong magic")

            
            local_fh.readHeader(fh)
            local_det = DataTable()
            local_det.readTable(fh,local_fh)
            local_strt = StringTable()
            local_strt.readStrings(fh,local_fh)
            local_ctt = ContentTable()
            local_ctt.readTable(fh,local_fh,local_det)

            for x in range(len(local_ctt.entries)):
                    content_entry = local_ctt.entries[x]

                    if content_entry.data_reference is None:
                        # Entry has no data linked
                        continue
                    
                    if content_entry.hash == b'R\xab5#hBJ\xc2}\x8fr\x94#\x19m\xd3':
                        # bitmap handle info stuff
                        offset = content_entry.data_reference.offset
                        fh.seek(offset + 0xe4)
                        frame_count = int.from_bytes(fh.read(4),'little')
                        print(f"Texture has {frame_count} frames")
            import bpy
            if frame_count <= 1:
                
                print("Importing single frame Texture")
                textureData = self.readTextureImage(path,import_settings)
                tex = bpy.data.textures.new(name,type="IMAGE")
                img = bpy.data.images.new(name,textureData[0],textureData[1])
                img.pixels = textureData[2]
                tex.image = img
                self.blender_texture = tex
            else:
                #from PIL import Image
                frames = [] 
                print("Importing multiple frames")
                for frame in range(frame_count):
                    handle = path + f"[{frame}_bitmap_resource_handle]"
                    print(f"Using bitmap handle {handle} for frame {frame}")
                    textureData = self.readTextureImage(handle,import_settings)
                    tex = bpy.data.textures.new(name + "_frame_" + str(frame),type="IMAGE")
                    img = bpy.data.images.new(name + "_frame_" + str(frame),textureData[0],textureData[1])
                    img.pixels = textureData[2]
                    tex.image = img
                    #byte_data = [bytes(x) for x in textureData[2]]
                    #print(byte_data)
                    #try:
                    #    frames.append(Image.frombytes('RGBA',(textureData[0],textureData[1]),b''.join(byte_data)))
                    #except:
                    #    print(f"Error on frame {frame}")
                #final = BytesIO()
                #frames[0].save("/home/ich/haloRIP/anim.gif",format="GIF",append_images=frames,save_all=True,duration=100,loop=0)

    def exportTexture(self,path):
        with open(path,'rb') as f:
            if not self.file_header.checkMagic(f):
                print(f"File has the wrong magic")


            self.file_header.readHeader(f)
            self.data_entry_table.readTable(f,self.file_header)
            self.string_table.readStrings(f,self.file_header)
            self.content_table.readTable(f,self.file_header,self.data_entry_table)

            handle_name = path.split('/')[-1]
            print(f"Texture File name: {handle_name}")
            format = -1

            for x in range(len(self.content_table.entries)):
                    content_entry = self.content_table.entries[x]

                    #if self.content_table.entries[x].data_reference is None:
                    #    # Entry has no data linked
                    #    continue
                    
                    if content_entry.hash == b'*\x80\xeb\x8akA\n\xf6\x9cp\x0c\x97MU6#':
                        # DDS Header info stuff
                        offset = content_entry.data_reference.offset
                        f.seek(offset + 0x1d)
                        format = int.from_bytes(f.read(4),'little')
                        f.seek(offset + 0x40)
                        resourceDimension = int.from_bytes(f.read(4),'little')

                    if content_entry.hash == b'9, \xd1\xdcH\xfc\xbdI\xde+\x81\x93\xaf\xe8\xb0':
                        # One of these hashes per resource file
                        #nResourceFiles = content_entry.data_reference.size//0x10    # there are 0x10 bytes for each file
                        #for chunk in range(nResourceFiles):
                        #    offset = content_entry.data_reference.offset + chunk * 0x10
                        #    f.seek(offset + 0xa)
                        #    mipmap = int.from_bytes(f.read(1),'little')
                        #    if mipmap != import_settings.mipmap:
                        #        continue
                        #    f.seek(offset + 0xc)
                        #    width = int.from_bytes(f.read(2),'little')
                        #    height = int.from_bytes(f.read(2),'little')
                        #    chunk_name = path + "[" + str(chunk) + "_bitmap_resource_handle.chunk" + str(chunk) + "]"
                        #    print(f"Reading texture block {chunk_name}")
                        #    print(f"Width: {width} Height: {height} Format: {DXGI_FORMAT[format]} {hex(format)}")
                        data_start = content_entry.data_parent.offset + content_entry.data_parent.size
                        print(f"Texture data starts at {hex(data_start)}")
                        tex_obj = TextureObject()
                        tex_obj.width = 4096
                        tex_obj.height = 111
                        tex_obj.texture_format = format
                        dds_data = self.createDDSHeader(tex_obj)
                        print(f"Format: {DXGI_FORMAT[format]} {hex(format)}")
                        f.seek(data_start)
                        out = b''.join(dds_data) + f.read()
                        return out
