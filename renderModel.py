
import bmesh
import bpy
import pathlib
import os
import struct
import sys


if 'DEBUG_MODE' in sys.argv:
    from Header import Header
    from DataTable import DataTable, DataTableEntry
    from StringTable import StringTable
    from ContentTable import ContentTable, ContentTableEntry 
    from Material import Material   
else:
    from . Header import Header
    from . DataTable import DataTable, DataTableEntry
    from . StringTable import StringTable
    from . ContentTable import ContentTable, ContentTableEntry
    from . Material import Material



class Table1Entry:
    offset = int
    size = int
    def __init__(self):
        self.offset = -1
        self.size = -1

class Table2Entry:
    hash = None
    ref = None
    parent = None
    def __init__(self):
        self.hash = ""
        self.ref = None
        self.parent = None

class Part:
    material_index = int
    index_offset = int
    index_count = int
    vertex_count = int
    material_path = ""

    def __init__(self):
        self.material_index = -1
        self.index_offset = -1
        self.index_count = -1
        self.vertex_count = -1
        self.material_path = ""

class ModelPartEnty:
    def __init__(self):
        self.type = -1
        self.parent_index = -1
        self.offset = -1

class Block:
    def __init__(self):
        self.offset = -1
        self.size = -1
        self.type = -1

class MeshBlock:
    first_vblock = -1
    index_block = -1
    mesh_part = None
    def __init__(self):
        self.first_vblock = -1
        self.index_block = -1
        self.mesh_part = None

class SourceMesh:
    def __init__(self):
        self.vert_pos = []
        self.vert_uv0 = []
        self.vert_uv1 = []
        self.vert_norm = []
        self.vert_tangent = []
        self.faces = []
        self.name = ""
        self.weight_indices = []
        self.weights = []
        self.weight_pairs = []
        self.parts = []

class SourceMeshParts:
    def __init__(self):
        self.parts = []
        self.vertices = -1
        self.lod = -1

class Scale:
    x_min = -1
    x_max = -1
    y_min = -1
    y_max = -1
    z_min = -1
    z_max = -1
    model_scale = [[],[],[]]

    u0_min = -1
    u0_max = -1
    v0_min = -1
    v0_max = -1
    uv0_scale = [[],[]]
    def __init__(self):
        self.x_min = -1
        self.x_max = -1


class ScaleModifier:
    x = 1.0
    y = 1.0
    z = 1.0
    def __init__(self):
        self.x = 1.0
        self.y = 1.0
        self.z = 1.0

def readNullString(f, start):
    string = []
    f.seek(start)
    while True:
        char = f.read(1)
        if char == b'\x00':
            return "".join(string)
        string.append(char.decode("utf-8"))

class ImportRenderModel(bpy.types.Operator):
    bl_idname = "import.rendermodel"
    bl_label = "Import rendermodel"
    bl_description = "rendermodel"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    auto_import_dependencies: bpy.props.BoolProperty(
        name="Import dependencies",
        description="Automatically import data like Textures from the specified root path",
        default=False
    )

    root_folder: bpy.props.StringProperty(
        subtype="FILE_PATH",
        name="Asset Root",
        description="Path to use for additional data. Uses relative path from imported file if none is specified and import dependencies is active",
        default="/home/ich/haloRIP/HIMU/output"
    )

    lod: bpy.props.IntProperty(
        name="LOD",
        description="The LOD of the meshes to import. Meshes with a different LOD get ignored",
        default=0
    )
    
    scale_modifier: bpy.props.FloatVectorProperty(
        name="Scale Modifier",
        description="Scale that gets applied to the model to get more reasonable scaling for blender",
        default=[1.0,1.0,1.0])

    def execute(self, context):

        def processMesh(src_mesh, chunk_data, scale, scaleModifier):

            mesh = bpy.data.meshes.new("test mesh")
            object = bpy.data.objects.new("test object",mesh)
            bpy.context.view_layer.active_layer_collection.collection.objects.link(object)
            vert_count = 0

            uv0 = []
            uv1 = []

            # add all the vertices
            for idx in range(len(src_mesh.vertex_blocks)):

                # Position data
                if src_mesh.vertex_blocks[idx].vertex_type == 0:
                    #print(f"Block Size: {hex(src_mesh.vertex_blocks[x].size)} stride: {hex(src_mesh.vertex_blocks[x].vertex_stride)}")
                    if src_mesh.vertex_blocks[idx].vertex_stride == 0 or src_mesh.vertex_blocks[idx].size == 0:
                        continue
                    for j in range(src_mesh.vertex_blocks[idx].offset,src_mesh.vertex_blocks[idx].offset + src_mesh.vertex_blocks[idx].size,src_mesh.vertex_blocks[idx].vertex_stride):
                        #f.seek(vertex_blocks[x].offset + j * vertex_blocks[x].vertex_stride)
                        #chunk_offset = vertex_blocks[x].offset + j * vertex_blocks[x].vertex_stride
                        chunk_offset = j
                        x = int.from_bytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * scale.model_scale[0][-1] + scale.model_scale[0][0]
                        y = int.from_bytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * scale.model_scale[1][-1] + scale.model_scale[1][0]
                        z = int.from_bytes(chunk_data[chunk_offset+4:chunk_offset+6],'little') / (2 ** 16 - 1) * scale.model_scale[2][-1] + scale.model_scale[2][0]

                        # apply scale modifier
                        x *= scaleModifier.x
                        y *= scaleModifier.y
                        z *= scaleModifier.z

                        #x += scale.model_scale[0][0]
                        #y += scale.model_scale[1][0]
                        #z += scale.model_scale[2][0]

                        mesh.vertices.add(1)
                        mesh.vertices[-1].co = (x,y,z)
                        vert_count += 1

                # UV
                if src_mesh.vertex_blocks[idx].vertex_type == 1:
                    #nVerts = (int)(src_mesh.vertex_blocks[x].size / src_mesh.vertex_blocks[x].vertex_stride)
                    current_vert = 0
                    for j in range(src_mesh.vertex_blocks[idx].offset,src_mesh.vertex_blocks[idx].offset + src_mesh.vertex_blocks[idx].size,src_mesh.vertex_blocks[idx].vertex_stride):
                        chunk_offset = j

                        u = int.from_bytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * scale.uv0_scale[0][-1] + scale.uv0_scale[0][0]
                        v = int.from_bytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * scale.uv0_scale[1][-1] + scale.uv0_scale[1][0]
                        uv0.append([u,v])
                        #print(f"UV0: {u} {v}")

                if src_mesh.vertex_blocks[idx].vertex_type == 2:
                    #nVerts = (int)(src_mesh.vertex_blocks[x].size / src_mesh.vertex_blocks[x].vertex_stride)
                    current_vert = 0
                    for j in range(src_mesh.vertex_blocks[idx].offset,src_mesh.vertex_blocks[idx].offset + src_mesh.vertex_blocks[idx].size,src_mesh.vertex_blocks[idx].vertex_stride):
                        chunk_offset = j

                        u = int.from_bytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) #* scale.model_scale[0][-1] + scale.model_scale[0][0]
                        v = int.from_bytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1)# * scale.model_scale[1][-1] + scale.model_scale[1][0]
                        uv1.append([u,v])
                        #print(f"UV1: {u} {v}")

            print(f"UV0 len: {len(uv0[0])}")
            print(f"UV1 len: {len(uv1)}")
            # combine the vertices into faces
            if vert_count >= 0x10000:
                index_len = 4
            else:
                index_len = 2
            #print(f"Mesh has {hex(vert_count)} vertices")
            if vert_count == 0:
                return
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for face_start in range(src_mesh.index_block.offset, src_mesh.index_block.offset + src_mesh.index_block.size, index_len*3):
                # read 3 16-bit integers that correspond to the vertex ids of the vertices of the face
                bm.verts.ensure_lookup_table()
                index_1 = int.from_bytes(chunk_data[face_start:face_start+index_len],'little')
                index_2 = int.from_bytes(chunk_data[face_start+index_len:face_start+index_len*2],'little')
                index_3 = int.from_bytes(chunk_data[face_start+index_len*2:face_start+index_len*3],'little')
                if index_1 > len(bm.verts) or index_2 > len(bm.verts) or index_3 > len(bm.verts):
                    continue
                bm.faces.ensure_lookup_table()
                try:
                    bm.faces.new([bm.verts[index_1],bm.verts[index_2],bm.verts[index_3]])
                except:
                    bm.to_mesh(mesh)
                    bm.free()  
                    print("Error creating face")      
                    return

            bm.verts.ensure_lookup_table()
            bm.verts.index_update()
            bm.faces.ensure_lookup_table()
            uv = bm.loops.layers.uv.new()
            for face in range(len(bm.faces)):
                for vLoop in range(len(bm.faces[face].loops)):
                    loop = bm.faces[face].loops[vLoop]
                    #print(f"{loop.vert.index} {uv0}")
                    loop[uv].uv = (uv0[loop.vert.index][0],uv0[loop.vert.index][1])
                    
            bm.to_mesh(mesh)
            bm.free()
            return

        def openRenderModel(f):
            #header_length = 0x50
            #f.seek(0x18)
            #table_1_count = int.from_bytes(f.read(4),'little')              # 0x18  section headers?
            #table_2_count = int.from_bytes(f.read(4),'little')              # 0x1c  data table
            #table_3_count = int.from_bytes(f.read(4),'little')              # 0x20  content table
            #table_4_count = int.from_bytes(f.read(4),'little')              # 0x24  data block table
            #string_count = int.from_bytes(f.read(4),'little')      # 0x28
            #string_length = int.from_bytes(f.read(4),"little")              # 0x2c
            #field_6_length = int.from_bytes(f.read(4),'little')             # 0x30      length in bytes
            #table_7_length = int.from_bytes(f.read(4),'little')             # 0x34      each element is 0x2a0 long
            #f.seek(0x38)
            #model_data_offset = int.from_bytes(f.read(4),'little')          # adding up the previous lengths also gets to this offset, so idk why this exists

            # Markers used in HIME are 0x1e0 bytes apart (may or may not mean anything)
            source_mesh_parts= []
            part_entries = []
            index_blocks = []
            vertex_blocks = []
            scale = None
            data_offset = None

            mesh_blocks = []
            materials = []


            file_header = Header()
            data_entry_table = DataTable()
            string_table = StringTable()
            content_table = ContentTable()

            if not file_header.checkMagic(f):
                self.report({"ERROR"},"Wrong magic")
                return {"CANCELLED"}
            file_header.readHeader(f)
            data_entry_table.readTable(f,file_header)
            string_table.readStrings(f,file_header)
            content_table.readTable(f,file_header,data_entry_table)

            


            # process content Table to populate the different Arrays for later use
            # sorts the entries based on the hash
            current_lod = -1
            current_max_lod = -1

            for x in range(len(content_table.entries)):

                # Scale data Block
                if content_table.entries[x].hash == b"\xAC\xFD\x51\xFE\x78\x47\xFF\x62\x54\x30\xC3\xA8\x6C\xA9\x23\xA0":

                    f.seek(content_table.entries[x].data_reference.offset + 4)
                    scale = Scale()
                    scale.x_min = struct.unpack('f',f.read(4))[0]
                    scale.x_max = struct.unpack('f',f.read(4))[0]
                    scale.y_min = struct.unpack('f',f.read(4))[0]
                    scale.y_max = struct.unpack('f',f.read(4))[0]
                    scale.z_min = struct.unpack('f',f.read(4))[0]
                    scale.z_max = struct.unpack('f',f.read(4))[0]
                    scale.model_scale = [[scale.x_min, scale.x_max, scale.x_max-scale.x_min], [scale.y_min, scale.y_max, scale.y_max-scale.y_min], [scale.z_min, scale.z_max, scale.z_max-scale.z_min]]
                    scale.u0_min = struct.unpack('f',f.read(4))[0]
                    scale.u0_max = struct.unpack('f',f.read(4))[0]
                    scale.v0_min = struct.unpack('f',f.read(4))[0]
                    scale.v0_max = struct.unpack('f',f.read(4))[0]
                    scale.uv0_scale = [[scale.u0_min,scale.u0_max,scale.u0_max-scale.u0_min],[scale.v0_min,scale.v0_max,scale.v0_max-scale.v0_min]]

                # Mesh data Block
                if content_table.entries[x].hash == b"\x9D\x84\x81\x4A\xB4\x42\xEE\xFB\xAC\x56\xC9\xA3\x18\x0F\x53\xE6":
                    ref_offset = content_table.entries[x].data_reference.offset
                    ref_length = content_table.entries[x].data_reference.size
                    nParts = (int)(ref_length/0x18)

                    source_mesh = SourceMeshParts()
                    nVerts = 0
                    for p in range(nParts):
                        part_offset = ref_offset + p * 0x18
                        #print(f"Part data is at {hex(part_offset)} with ref offset {hex(ref_offset)}")
                        part = Part()
                        f.seek(part_offset)
                        part.material_index = int.from_bytes(f.read(2),'little')
                        f.seek(part_offset + 4)
                        part.index_offset = int.from_bytes(f.read(4),'little')
                        part.index_count = int.from_bytes(f.read(4),'little')
                        f.seek(part_offset + 0x14)
                        part.vertex_count = int.from_bytes(f.read(2),'little')
                        #print(part.material_index)
                        part.material_path = string_table.strings[part.material_index]
                        #print(f"Using material: {part.material_path}")
                        if len(materials)-1 < part.material_index:
                            for additional_entries in range(part.material_index + 1 - len(materials)):
                                materials.append(Material())
                        if not materials[part.material_index].read_data and self.auto_import_dependencies:
                            #print(f"Reading material {part.material_path}")
                            materials[part.material_index].readMaterial(self.root_folder + "/" + part.material_path.replace("\\","/").replace("//","/") + ".material",self.root_folder)
                        nVerts += part.vertex_count
                        source_mesh.parts.append(part)
                        #print(f"Part has {hex(part.vertex_count)} vertices and uses material {hex(part.material_index)}")
                    source_mesh.lod = current_lod
                    source_mesh.vertices = nVerts
                    source_mesh_parts.append(source_mesh)
                    #print(f"mesh block array length: {hex(len(mesh_blocks))} current LOD: {hex(current_lod)}")
                    mesh_blocks[len(mesh_blocks) - current_max_lod  + current_lod].mesh_part = source_mesh
                    current_lod += 1

                # Mesh meta data block
                if content_table.entries[x].hash == b'\x97\xc4\xfag}N=\x88\xa2\xf7\x94\xb7\xf8\x93\xff\x8d':
                    #print("LOD/Mesh hash?")
                    ref_offset = content_table.entries[x].data_reference.offset
                    ref_length = content_table.entries[x].data_reference.size
                    #print(f"Ref data offset: {hex(entry.ref.offset)}")
                    #print(f"Ref data size: {hex(entry.ref.size)}")
                    #print(f"Parent index: {hex(parent_index)}")
                    current_lod = 0
                    current_max_lod = 0
                    for part in range(ref_offset,ref_offset + ref_length,0x90):
                        f.seek(part + 0x64)
                        first_vblock = int.from_bytes(f.read(2),'little')   # first vertex block index in the mesh
                        f.seek(part + 0x8a)     # 0x8a might be index block index
                        index_block_index = int.from_bytes(f.read(2),'little')
                        #print(f"LOD?: {hex(first_vblock)} {hex(index_block_index)} {hex(int.from_bytes(f.read(4),'little'))}")
                        mesh_block = MeshBlock()
                        mesh_block.first_vblock = first_vblock
                        mesh_block.index_block = index_block_index
                        mesh_blocks.append(mesh_block)
                        current_max_lod += 1

                if content_table.entries[x].hash == b")s\xdd\x10\x80H\x7f\xe0\x9a\xb7\x8b\xbc\xee'2%":
                    # seems to be the entry for the parts
                    #print("Marker hash?")
                    ref_offset = content_table.entries[x].data_reference.offset
                    ref_length = content_table.entries[x].data_reference.size
                    data_offset = content_table.entries[x].data_reference.offset - 0xc   # should work, might not (-0xc to get the same offset HIME would get from searching)
                    #print(f"Ref data offset: {hex(entry.ref.offset)}")
                    #print(f"Ref data size: {hex(entry.ref.size)}")


            # data block table (points to model data?)
            print(f"calculated data offset would be {hex(data_offset)}")
            if data_offset is None:
                print("Didn't find model offset content table entry, ")
                return

            print(f"data offset is {hex(data_offset)}")
            for x in range(file_header.data_block_table_count):  # table 4 count
                offset = file_header.data_block_table_offset + x * 0x14 # header_length + table_1_count * 0x18 + table_2_count * 0x10 + table_3_count * 0x20 + x * 0x14
                entry = ModelPartEnty()
                f.seek(offset)
                entry.type = int.from_bytes(f.read(4),'little')
                f.seek(offset + 0x8)
                entry.parent_index = int.from_bytes(f.read(4),'little')
                #entry.unknown_0xc = int.from_bytes(f.read(4), 'little')
                #print(f"Part entry unknown int 0xc: {hex(unknown_0xc)}")
                f.seek(offset + 0x10)
                entry.offset = int.from_bytes(f.read(4),'little') # model data offset + table 7 length comes out at the first marker HIME is searching for
                if x == 0:
                    #print(f"First entry offset: {hex(entry.offset)}")
                    data_offset -= entry.offset
                entry.offset += data_offset
                part_entries.append(entry)


            print(f"data offset is now {hex(data_offset)}")
            # sort entries into index and vertex blocks and parse those blocks
            offset = part_entries[0].offset
            print(f"first entry offset: {hex(part_entries[0].offset)}")
            for x in range(len(part_entries)):
                block = Block()

                if part_entries[x].type == part_entries[0].type:
                    #print(f"vertex unk0xc: {hex(part_entries[x].unknown_0xc)}")
                    # vertex block
                    #print(f"Block entry {hex(x)} at offset {hex(offset)}")
                    f.seek(offset)
                    #print(f"unknown 32bit int at 0x00: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x04: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x08: {hex(int.from_bytes(f.read(4),'little'))}")
                    f.seek(offset + 0xC)
                    block.vertex_type = int.from_bytes(f.read(4),'little')
                    #print(f"unknown 32bit int at 0x10: {hex(int.from_bytes(f.read(4),'little'))}")
                    f.seek(offset + 0x14)
                    block.vertex_stride = int.from_bytes(f.read(2),'little')
                    f.seek(offset + 0x18)
                    block.vertex_count = int.from_bytes(f.read(4),'little') # 0x18
                    block.offset = int.from_bytes(f.read(4),'little')       # 0x1c
                    block.size = int.from_bytes(f.read(4),'little')         # 0x20
                    block.type = int.from_bytes(f.read(4),'little')         # 0x24
                    #print(f"unknown 32bit int at 0x28: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x2c: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x30: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x34: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x38: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x3c: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x40: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x44: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x48: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x4c: {hex(int.from_bytes(f.read(4),'little'))}")
                    vertex_blocks.append(block)
                    offset += 0x50
                    continue
                
                if part_entries[x].type == part_entries[0].type + 1:
                    # index block
                    #print(f"index unk0xc: {hex(part_entries[x].unknown_0xc)}")
                    #print(f"index block")
                    f.seek(offset)
                    #print(f"unknown 32bit int at 0x00: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x04: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x08: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x0c: {hex(int.from_bytes(f.read(4),'little'))}")
                    f.seek(offset + 0x10)
                    block.index_count = int.from_bytes(f.read(2),'little')  # 0x10
                    f.seek(offset + 0x14)
                    block.offset = int.from_bytes(f.read(4),'little')       # 0x14
                    block.size = int.from_bytes(f.read(4),'little')         # 0x18
                    block.type = int.from_bytes(f.read(4),'little')         # 0x1c
                    #print(f"unknown 32bit int at 0x20: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x24: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x28: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x2c: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x30: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x34: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x38: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x3c: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x40: {hex(int.from_bytes(f.read(4),'little'))}")
                    #print(f"unknown 32bit int at 0x44: {hex(int.from_bytes(f.read(4),'little'))}")
                    index_blocks.append(block)
                    offset += 0x48
                    continue

                #print(f"unknown block type {hex(part_entries[x].type)} at offset {hex(offset)}")

            folder = pathlib.Path(self.filepath).parent
            
            # load all of the chunks into one array
            # this part of the code is just copied over from HIME
            chunk_data_map = {}
            for i, chunk in enumerate([x for x in os.listdir(folder) if ".chunk" in x and ".render_model" in x]):  # praying they read in order - TODO check this with a large file >10 or >100 chunks
                cdata = open(f"{folder}/{chunk}", "rb").read()
                index = int(chunk[:-1].split(".chunk")[-1])
                chunk_data_map[index] = cdata

            chunk_data = b""
            for i in range(len(chunk_data_map.keys())):
                chunk_data += chunk_data_map[i]




            # group the blocks into meshes. The processing is done later

            current_vertex_block = 0
            for mesh_block in range(len(mesh_blocks)):
                src_mesh = SourceMesh()
                current_vertex_block = mesh_blocks[mesh_block].first_vblock     # start at this vertex block

                vblocks = [vertex_blocks[current_vertex_block]]

                for j in range(current_vertex_block + 1, len(vertex_blocks)):
                    if vertex_blocks[j].vertex_type == 0:
                        # if the current block contains position data, end this mesh
                        current_vertex_block = j
                        #print(f"Mesh starts at vertex block {hex(current_vertex_block)} and uses index block {hex(mesh_blocks[mesh_block].index_block)}")
                        break
                    else:
                        # not the end of the mesh yet, just add this block
                        vblocks.append(vertex_blocks[j])

                mesh_part = mesh_blocks[mesh_block].mesh_part

                if mesh_part is None:
                    print("Mesh block doesn't have a mesh part assigned, weird. skipping!")
                    continue
                
                if mesh_part.lod != self.lod:
                    #print("LOD doesn't match, ignoring Mesh")
                    continue

                src_mesh.vertex_blocks = vblocks
                src_mesh.index_block = index_blocks[mesh_blocks[mesh_block].index_block]
                scaleModifier = ScaleModifier()
                scaleModifier.x = self.scale_modifier[0]
                scaleModifier.y = self.scale_modifier[1]
                scaleModifier.z = self.scale_modifier[2]
                processMesh(src_mesh,chunk_data, scale, scaleModifier)

            

            return


        with open(self.filepath,'rb') as f:
            if f.read(4) != b'ucsh':
                self.report({"ERROR"},"Wrong magic")
                return {"CANCELLED"}
            openRenderModel(f)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self,context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ImportRenderModel.bl_idname,text="Halo Infinite Rendermodel")

def register():
    print("loaded")
    bpy.utils.register_class(ImportRenderModel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    
def unregister():
    print("unloaded")
    bpy.utils.unregister_class(ImportRenderModel)

if __name__ == "__main__":
    register()