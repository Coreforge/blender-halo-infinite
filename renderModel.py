
import bmesh
import bpy
import pathlib
import os
import struct
import sys
import mathutils


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
    from . import ModulesManager



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
    material = None

    def __init__(self):
        self.material_index = -1
        self.index_offset = -1
        self.index_count = -1
        self.vertex_count = -1
        self.material_path = ""
        self.material = None

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
        self.index_count = -1
        self.mesh_parts = []

class SourceMeshParts:
    def __init__(self):
        self.parts = []
        self.vertices = -1
        self.lod = -1
        self.index_count = -1

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

    u1_min = -1
    u1_max = -1
    v1_min = -1
    v1_max = -1
    uv1_scale = [[],[]]

    u2_min = -1
    u2_max = -1
    v2_min = -1
    v2_max = -1
    uv2_scale = [[],[]]
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

class ImportSettings:
    lod = -1
    mipmap = -1
    norm_signed = True
    reuse_textures = True
    def __init__(self):
        self.lod = -1
        self.mipmap = -1
        self.norm_signed = True
        self.reuse_textures = True

def readNullString(f, start):
    string = []
    f.seek(start)
    while True:
        char = f.read(1)
        if char == b'\x00':
            return "".join(string)
        string.append(char.decode("utf-8"))

class ImportRenderModel(bpy.types.Operator):
    bl_idname = "infinite.rendermodel"
    bl_label = "Import rendermodel"
    bl_description = "rendermodel"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    auto_import_dependencies: bpy.props.BoolProperty(
        name="Import dependencies",
        description="Automatically import data like Textures from the specified root path",
        default=False
    )

    import_uvs: bpy.props.BoolProperty(
        name="Import UVs",
        description="import UV data. Takes some additional time",
        default=True
    )

    import_weights: bpy.props.BoolProperty(
        name="Import vertex weights",
        description="imports the vertex weights and vertex groups",
        default=True
    )

    import_normals: bpy.props.BoolProperty(
        name="(potentialy broken) Import Normals",
        description="(potentially broken) import mesh normals",
        default=True
    )

    reuse_textures: bpy.props.BoolProperty(
        name="Reuse existing Textures",
        description="use the existing texture if a referenced Texture with the same name already exists in the file",
        default=True
    )
    
    add_materials: bpy.props.BoolProperty(
        name="Add materials",
        description="adds an empty material for the materials used by the model",
        default=True
    )

    populate_shader: bpy.props.BoolProperty(
        name="Setup shaders",
        description="sets up textures for materials automatically (requires import dependencies)",
        default=False
    )

    import_model: bpy.props.BoolProperty(
        name="Import 3D Model",
        description="import the 3D model",
        default=True
    )

    use_modules: bpy.props.BoolProperty(
        default=False,
        name="use modules",
        options={"HIDDEN"}
    )

    root_folder = None
    shader_file = None
    shader_name = None

    #root_folder: bpy.props.StringProperty(
    #    subtype="FILE_PATH",
    #    name="Asset Root",
    #    description="Path to use for additional data. Uses relative path from imported file if none is specified and import dependencies is active",
    #    default="/home/ich/haloRIP/HIMU/output"
    #)
#
    #shader_file: bpy.props.StringProperty(
    #    name="Shader library",
    #    description="Path to the blend file containing the shader",
    #    default="/home/ich/haloRIP/blender_plugin/shaders/Infinite_MP_Shader_v1.8_Made_by_Grand_Bacon.blend"
    #)
#
    #shader_name: bpy.props.StringProperty(
    #    name="Shader name",
    #    description="Name of the shader within the library",
    #    default="Infinite MP Shader v1.8 Made by Grand_Bacon"
    #)

    mipmap: bpy.props.IntProperty(
        name="Mipmap level",
        description="Mipmap level of the textures to import.",
        default=0
    )

    norm_signed: bpy.props.BoolProperty(
        name="Signed Texture Range",
        description="import texures with a signed format as signed",
        default=False
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

        def processMesh(src_mesh, chunk_data, scale, scaleModifier, name):

            mesh = bpy.data.meshes.new(name)
            object = bpy.data.objects.new(name,mesh)
            bpy.context.view_layer.active_layer_collection.collection.objects.link(object)
            vert_count = 0

            uv0 = []
            uv1 = []
            uv2 = []

            weights = []
            weight_indicies = []

            frombytes = int.from_bytes
            model_scale = scale.model_scale
            uv0_scale = scale.uv0_scale
            uv1_scale = scale.uv1_scale
            uv2_scale = scale.uv2_scale

            modX = scaleModifier.x
            modY = scaleModifier.y
            modZ = scaleModifier.z

            blocks = src_mesh.vertex_blocks

            vert_arr = []

            normals = []
            material_slots = {}
            material_slot_indicies = {}

            #print("importing mesh")
            # add all the vertices
            for idx in range(len(blocks)):
                block = blocks[idx]
                # Position data
                if block.vertex_type == 0:
                    #print(f"Block Size: {hex(src_mesh.vertex_blocks[x].size)} stride: {hex(src_mesh.vertex_blocks[x].vertex_stride)}")
                    if block.vertex_stride == 0 or block.size == 0:
                        continue
                    nVerts = block.size//block.vertex_stride
                    #print(f"Adding {nVerts} vertices")
                    #mesh.vertices.add(nVerts)
                    vert_arr.extend((0.0,)*nVerts)
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        #f.seek(vertex_blocks[x].offset + j * vertex_blocks[x].vertex_stride)
                        #chunk_offset = vertex_blocks[x].offset + j * vertex_blocks[x].vertex_stride
                        chunk_offset = j
                        
                        x = frombytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * model_scale[0][-1] + model_scale[0][0]
                        y = frombytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * model_scale[1][-1] + model_scale[1][0]
                        z = frombytes(chunk_data[chunk_offset+4:chunk_offset+6],'little') / (2 ** 16 - 1) * model_scale[2][-1] + model_scale[2][0]
                        # apply scale modifier
                        x *= modX
                        y *= modY
                        z *= modZ

                        #x += scale.model_scale[0][0]
                        #y += scale.model_scale[1][0]
                        #z += scale.model_scale[2][0]

                        #mesh.vertices.add(1)
                        #mesh.vertices[vert_count].co = (x,y,z)
                        vert_arr[vert_count] = (x,y,z)
                        vert_count += 1
                    continue

                # UV
                if block.vertex_type == 1:
                    #nVerts = (int)(src_mesh.vertex_blocks[x].size / src_mesh.vertex_blocks[x].vertex_stride)
                    current_vert = len(uv0)
                    uv0.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j
                        #print(f"Vertex UV0 block at {hex(chunk_offset)} stride: {hex(block.vertex_stride)}")
                        u = frombytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * uv0_scale[0][-1] + uv0_scale[0][0]
                        v = frombytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * uv0_scale[1][-1] + uv0_scale[1][0]
                        #uv0.append([u,v])
                        uv0[current_vert] = (u,v)
                        current_vert += 1
                        #print(f"UV0: {u} {v}")
                    continue

                if src_mesh.vertex_blocks[idx].vertex_type == 2:
                    #nVerts = (int)(src_mesh.vertex_blocks[x].size / src_mesh.vertex_blocks[x].vertex_stride)
                    current_vert = len(uv1)
                    uv1.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j

                        u = frombytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * uv1_scale[0][-1] + uv1_scale[0][0]
                        v = frombytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * uv1_scale[1][-1] + uv1_scale[1][0]
                        #uv1.append([u,v])
                        uv1[current_vert] = [u,v]
                        current_vert += 1
                        #print(f"UV1: {u} {v}")
                    continue

                if src_mesh.vertex_blocks[idx].vertex_type == 3:
                    #nVerts = (int)(src_mesh.vertex_blocks[x].size / src_mesh.vertex_blocks[x].vertex_stride)
                    current_vert = len(uv2)
                    uv2.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j

                        u = frombytes(chunk_data[chunk_offset:chunk_offset+2],'little') / (2 ** 16 - 1) * uv2_scale[0][-1] + uv2_scale[0][0]
                        v = frombytes(chunk_data[chunk_offset+2:chunk_offset+4],'little') / (2 ** 16 - 1) * uv2_scale[1][-1] + uv2_scale[1][0]
                        #uv1.append([u,v])
                        uv2[current_vert] = [u,v]
                        #print(f"U {u} V {v}")
                        current_vert += 1
                        #print(f"UV1: {u} {v}")
                    continue

                if block.vertex_type == 5:
                    print(f"Normal stride: {hex(block.vertex_stride)}")
                    current_vert = len(normals)
                    normals.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j
                        x = (frombytes(chunk_data[j:j+2],'little') & 0x3ff) / 1023 - 0.5
                        y = ((frombytes(chunk_data[j+1:j+3],'little') & 0xffc) >> 2) / 1023 - 0.5
                        z = ((frombytes(chunk_data[j+2:j+4],'little') & 0x3ff0) >> 4) / 1023 - 0.5
                        
                        sqrt_of_two = 2 ** 0.5

                        #x /= sqrt_of_two
                        #y /= sqrt_of_two
                        #z /= sqrt_of_two
                        w = (1-x**2-y**2-z**2)**0.5

                        missing = chunk_data[j+3] >> 6
                        #print(missing)
                        if missing == 1:
                            quat = mathutils.Quaternion((w,x,y,z))
                        elif missing == 2:
                            quat = mathutils.Quaternion((x,w,y,z))
                        elif missing == 3:
                            quat = mathutils.Quaternion((x,y,w,z))
                        elif missing == 0:
                            quat = mathutils.Quaternion((x,y,z,w))
                        #print(f"Normal: {quat.to_euler()}")
                        #norm_data = frombytes(chunk_data[j:j+4],'little')
                        #x = (norm_data & 0x3ff) / 1023
                        #y = ((norm_data >> 10) & 0x3ff) / 1023
                        #z = ((norm_data >> 20) & 0x3ff) / 1023
                        #quat.rotate(mathutils.Euler((1,0.8,0),'XYZ'))
                        normals[current_vert] = quat.to_axis_angle()[0]
                        current_vert += 1
                        #print(f"Normal data: {hex(frombytes(chunk_data[j:j+2],'little'))} {hex(frombytes(chunk_data[j+2:j+4],'little'))} dropped: {chunk_data[j+3] >> 6}")
                        #print(f"Normal {x} {y} {z} {w}")
                    continue
                
                if block.vertex_type == 6:
                    print(f"Tangent stride: {hex(block.vertex_stride)}")
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j
                        x = (frombytes(chunk_data[j:j+2],'little') & 0x3ff) / 1023 - 0.5
                        y = ((frombytes(chunk_data[j+1:j+3],'little') & 0xffc) >> 2) / 1023 - 0.5
                        z = ((frombytes(chunk_data[j+2:j+4],'little') & 0x3ff0) >> 4) / 1023 - 0.5
                        
                        #x /= 1023
                        #y /= 1023
                        #z /= 1023
                        #print(f"Tangent {x} {y} {z} {chunk_data[j+3] >> 6}")
                        #print(f"Tangent data: {hex(frombytes(chunk_data[j:j+2],'little'))} {hex(frombytes(chunk_data[j+2:j+4],'little'))}")
                    continue

                if block.vertex_type == 7:
                    # weights
                    current_weight = len(weight_indicies)
                    weight_indicies.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j
                        these_weights = [x for x in chunk_data[j:j+4]]
                        weight_indicies[current_weight] = these_weights
                        current_weight += 1
                        #print(these_weights)
                    continue

                if block.vertex_type == 8:
                    # weights
                    current_weight = len(weights)
                    weights.extend([0.0,]*((block.size//block.vertex_stride)))
                    for j in range(block.offset,block.offset + block.size,block.vertex_stride):
                        chunk_offset = j
                        these_weights = [x for x in chunk_data[j:j+4]]
                        s = sum(these_weights)
                        #s = 128
                        if s != 0:
                            norm_weights = [x/255 for x in these_weights]
                        else:
                            norm_weights = [0, 0, 0, 0]
                        weights[current_weight] = norm_weights
                        current_weight += 1
                        #print(norm_weights)
                    continue
                print(f"Unknown block type {block.vertex_type} with stride {hex(block.vertex_stride)} size {hex(block.size)} at {hex(block.offset)}")
                        
            #print(f"Weights len {len(weights)}")
            #print(f"Weight indicies len{len(weight_indicies)}")
            #print(f"UV0 len: {len(uv0)}")
            #print(f"UV1 len: {len(uv1)}")
            # combine the vertices into faces
            #if vert_count >= 0x10000:
            #    index_len = 4
            #    print(f"Index len 4 for vert count {vert_count}")
            #else:
            #    index_len = 2
            index_len = src_mesh.index_block.size // src_mesh.index_count
            #print(f"Mesh has {hex(vert_count)} vertices")
            if vert_count == 0:
                return
            edges = []
            faces = {}
            nFace = 0
            #faces.extend((0.0,)*(src_mesh.index_block.size//(index_len*3)))
            for face_start in range(src_mesh.index_block.offset, src_mesh.index_block.offset + src_mesh.index_block.size, index_len*3):
                # read 3 16-bit integers that correspond to the vertex ids of the vertices of the face
                
                index_1 = frombytes(chunk_data[face_start:face_start+index_len],'little')
                index_2 = frombytes(chunk_data[face_start+index_len:face_start+index_len*2],'little')
                index_3 = frombytes(chunk_data[face_start+index_len*2:face_start+index_len*3],'little')

                #if index_1 >= len(vert_arr) or index_2 >= len(vert_arr) or index_3 >= len(vert_arr):
                #    print(f"Invalid vertex index on face {nFace}! Skipping mesh (would likely be very broken otherwise)")
                #    print(f"(data at {hex(face_start)})")
                #    print(f"data array size {hex(len(chunk_data))}")
                #    return

                faces[nFace] = (index_1,index_2,index_3)
                nFace += 1


            #print("faces done")
            mesh.from_pydata(vert_arr,edges,list(faces.values()))
            #mesh.validate()
            #mesh.update()
            if self.import_uvs:
                uv_layer = mesh.uv_layers.new(name="UV0")
                for loop in range(len(mesh.loops)):
                    try:
                        uv_layer.data[mesh.loops[loop].index].uv = (uv0[mesh.loops[loop].vertex_index][0],uv0[mesh.loops[loop].vertex_index][1])
                    except:
                        break
                    
                uv_layer = mesh.uv_layers.new(name="UV1")
                for loop in range(len(mesh.loops)):
                    try:
                        uv_layer.data[mesh.loops[loop].index].uv = (uv1[mesh.loops[loop].vertex_index][0],uv1[mesh.loops[loop].vertex_index][1])
                    except:
                        break
                
                uv_layer = mesh.uv_layers.new(name="UV2")
                for loop in range(len(mesh.loops)):
                    try:
                        uv_layer.data[mesh.loops[loop].index].uv = (uv2[mesh.loops[loop].vertex_index][0],uv2[mesh.loops[loop].vertex_index][1])
                    except:
                        break

            #print("UV done")

            if self.import_normals:
                #normal_loops = [0.0,]*len(mesh.loops)
                #for l in range(len(mesh.loops)):
                #    #mesh.loops[l].normal = normals[mesh.loops[l].vertex_index][1]
                #    normal_loops[l] = normals[mesh.loops[l].vertex_index][0]
                #print(normal_loops)
                #mesh.calc_normals_split()
                mesh.normals_split_custom_set([(0,0,0) for l in mesh.loops])
                mesh.normals_split_custom_set_from_vertices(normals)
                mesh.update()
                    
            for p in range(len(src_mesh.mesh_parts)):
                print(f"Mesh part index offset: {hex(src_mesh.mesh_parts[p].index_offset)} count: {hex(src_mesh.mesh_parts[p].index_count)}")
                first_face = src_mesh.mesh_parts[p].index_offset // 3
                face_count = src_mesh.mesh_parts[p].index_count // 3
                part_faces = mesh.polygons[first_face:first_face+face_count]
                if src_mesh.mesh_parts[p].material not in material_slots.keys():
                    if self.add_materials:
                        if src_mesh.mesh_parts[p].material.name not in bpy.data.materials.keys():
                            bpy.data.materials.new(src_mesh.mesh_parts[p].material.name)
                            bpy.data.materials[src_mesh.mesh_parts[p].material.name].use_nodes = True
                        mesh.materials.append(bpy.data.materials[src_mesh.mesh_parts[p].material.name])
                    else:
                        mesh.materials.append(None)
                    material_slots[src_mesh.mesh_parts[p].material] = mesh.materials[-1]
                    material_slot_indicies[src_mesh.mesh_parts[p].material] = len(material_slot_indicies)
                    #print(f"Added material slot for material {src_mesh.mesh_parts[p].material.name}")
                for face in part_faces:
                    face.material_index = material_slot_indicies[src_mesh.mesh_parts[p].material]
                    pass
                pass

            # weights
            # calculate the number of vertex groups by joining all index lists and taking the maximum value
            if self.import_weights and len(weight_indicies) != 0 and len(weights) != 0:
                nVertexGroups = max([max(x) for x in weight_indicies])
                #print(f"Vertex groups: {nVertexGroups}")

                vertex_groups = [object.vertex_groups.new(name=f"vGroup{x}") for x in range(nVertexGroups+1)]

                for x in mesh.vertices:
                    if x.index >= len(weights):
                        continue
                    groups = []
                    i = 0
                    for g in weight_indicies[x.index]:
                        if i > 3: break
                        if not g in groups:
                            #print(g)
                            vertex_groups[g].add([x.index],weights[x.index][i],'REPLACE')
                            groups.append(g)
                        i += 1

            #vertex_group = object.vertex_groups.new(name="weights_group_0")
            #for x in mesh.vertices:
            #    if x.index >= len(weights):
            #        continue
            #    vertex_group.add([x.index],weights[x.index][0],'REPLACE')
            #vertex_group = object.vertex_groups.new(name="weights_group_1")
            #for x in mesh.vertices:
            #    if x.index >= len(weights):
            #        continue
            #    vertex_group.add([x.index],weights[x.index][1],'REPLACE')
            #vertex_group = object.vertex_groups.new(name="weights_group_2")
            #for x in mesh.vertices:
            #    if x.index >= len(weights):
            #        continue
            #    vertex_group.add([x.index],weights[x.index][2],'REPLACE')
            #vertex_group = object.vertex_groups.new(name="weights_group_3")
            #for x in mesh.vertices:
            #    if x.index >= len(weights):
            #        continue
            #    vertex_group.add([x.index],weights[x.index][3],'REPLACE')
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

            shader_prefab = None

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

            import_settings = ImportSettings()
            import_settings.mipmap = self.mipmap
            import_settings.lod = self.lod
            import_settings.norm_signed = self.norm_signed
            import_settings.reuse_textures = self.reuse_textures

            if self.populate_shader:
                
                # load the shader from the library
                with bpy.data.libraries.load(self.shader_file, link=False) as (data_from, data_to):
                    #shader_prefab = data_from.materials[self.shader_name]
                    data_to.materials = [self.shader_name]
                    #print(type(data_from.materials))
                    pass
                shader_prefab = bpy.data.materials[self.shader_name]
                print(shader_prefab)

            # process content Table to populate the different Arrays for later use
            # sorts the entries based on the hash
            current_lod = -1
            current_max_lod = -1

            for x in range(len(content_table.entries)):

                # Scale data Block
                if content_table.entries[x].hash == b"\xAC\xFD\x51\xFE\x78\x47\xFF\x62\x54\x30\xC3\xA8\x6C\xA9\x23\xA0":
                    print(f"Scale at {hex(content_table.entries[x].data_reference.offset)} size {hex(content_table.entries[x].data_reference.size)}")
                    f.seek(content_table.entries[x].data_reference.offset + 4)
                    scale = Scale()
                    scale.x_min = struct.unpack('f',f.read(4))[0]       # 0x04
                    scale.x_max = struct.unpack('f',f.read(4))[0]       # 0x08
                    scale.y_min = struct.unpack('f',f.read(4))[0]       # 0x0c
                    scale.y_max = struct.unpack('f',f.read(4))[0]       # 0x10
                    scale.z_min = struct.unpack('f',f.read(4))[0]       # 0x14
                    scale.z_max = struct.unpack('f',f.read(4))[0]       # 0x18
                    scale.model_scale = [[scale.x_min, scale.x_max, scale.x_max-scale.x_min], [scale.y_min, scale.y_max, scale.y_max-scale.y_min], [scale.z_min, scale.z_max, scale.z_max-scale.z_min]]
                    scale.u0_min = struct.unpack('f',f.read(4))[0]      # 0x1c
                    scale.u0_max = struct.unpack('f',f.read(4))[0]      # 0x20
                    scale.v0_min = struct.unpack('f',f.read(4))[0]      # 0x24
                    scale.v0_max = struct.unpack('f',f.read(4))[0]      # 0x28
                    scale.uv0_scale = [[scale.u0_min,scale.u0_max,scale.u0_max-scale.u0_min],[scale.v0_min,scale.v0_max,scale.v0_max-scale.v0_min]]
                    scale.u1_min = struct.unpack('f',f.read(4))[0]      # 0x2c
                    scale.u1_max = struct.unpack('f',f.read(4))[0]      # 0x30
                    scale.v1_min = struct.unpack('f',f.read(4))[0]      # 0x34
                    scale.v1_max = struct.unpack('f',f.read(4))[0]      # 0x38
                    scale.uv1_scale = [[scale.u1_min,scale.u1_max,scale.u1_max-scale.u1_min],[scale.v1_min,scale.v1_max,scale.v1_max-scale.v1_min]]
                    scale.u2_min = struct.unpack('f',f.read(4))[0]      # 0x3c
                    scale.u2_max = struct.unpack('f',f.read(4))[0]      # 0x40
                    scale.v2_min = struct.unpack('f',f.read(4))[0]      # 0x44
                    scale.v2_max = struct.unpack('f',f.read(4))[0]      # 0x48
                    scale.uv2_scale = [[scale.u2_min,scale.u2_max,scale.u2_max-scale.u2_min],[scale.v2_min,scale.v2_max,scale.v2_max-scale.v2_min]]

                # Mesh data Block
                if content_table.entries[x].hash == b"\x9D\x84\x81\x4A\xB4\x42\xEE\xFB\xAC\x56\xC9\xA3\x18\x0F\x53\xE6":
                    ref_offset = content_table.entries[x].data_reference.offset
                    ref_length = content_table.entries[x].data_reference.size
                    nParts = (int)(ref_length/0x18)

                    source_mesh = SourceMeshParts()
                    nVerts = 0
                    nIdx = 0
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
                        if part.material_index < len(string_table.strings):
                            part.material_path = string_table.strings[part.material_index]
                            #print(f"Using material: {part.material_path}")
                            if len(materials)-1 < part.material_index:
                                for additional_entries in range(part.material_index + 1 - len(materials)):
                                    materials.append(Material())

                            materials[part.material_index].name = part.material_path.split('\\')[-1]

                            if not materials[part.material_index].read_data and self.auto_import_dependencies:
                                #print(f"Reading material {part.material_path}")
                                if self.use_modules:
                                    path = "/" + part.material_path.replace("\\","/").replace("//","/") + ".material"
                                else:
                                    path = self.root_folder + "/" + part.material_path.replace("\\","/").replace("//","/") + ".material"
                                materials[part.material_index].readMaterial(path,
                                                                            self.root_folder,
                                                                            import_settings,
                                                                            add_material = self.populate_shader,
                                                                            material_name = materials[part.material_index].name,
                                                                            material_prefab = shader_prefab,
                                                                            use_modules = self.use_modules)
                            part.material = materials[part.material_index]
                        else:
                            # there seems to be no path specified for this material, so just create an unknown material
                            # this usually happens with runtime_geo files
                            if len(materials)-1 < part.material_index:
                                for additional_entries in range(part.material_index + 1 - len(materials)):
                                    materials.append(Material())
                            materials[part.material_index].name = f"unknown_material_{str(part.material_index)}"
                            part.material = materials[part.material_index]
                            
                        nVerts += part.vertex_count
                        nIdx += part.index_count
                        source_mesh.parts.append(part)
                        #print(f"Part has {hex(part.vertex_count)} vertices and uses material {hex(part.material_index)}")
                    source_mesh.lod = current_lod
                    source_mesh.vertices = nVerts
                    source_mesh.index_count = nIdx
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

            if not self.import_model:
                # everything after this is only needed for the 3D model, not if you only want the textures
                return

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
                    unknown_0x00 = int.from_bytes(f.read(4),'little')
                    unknown_0x04 = int.from_bytes(f.read(4),'little')
                    unknown_0x08 = int.from_bytes(f.read(4),'little')
                    #print(f"unknown 32bit int at 0x00: {hex(unknown_0x00)}")
                    #print(f"unknown 32bit int at 0x04: {hex(unknown_0x04)}")
                    #print(f"unknown 32bit int at 0x08: {hex(unknown_0x08)}")
                    f.seek(offset + 0xC)
                    block.vertex_type = int.from_bytes(f.read(4),'little')
                    unknown_0x10 = int.from_bytes(f.read(4),'little')
                    #print(f"unknown 32bit int at 0x10: {hex(unknown_0x10)}")
                    f.seek(offset + 0x14)
                    block.vertex_stride = int.from_bytes(f.read(2),'little')
                    f.seek(offset + 0x18)
                    block.vertex_count = int.from_bytes(f.read(4),'little') # 0x18
                    block.offset = int.from_bytes(f.read(4),'little')       # 0x1c
                    block.size = int.from_bytes(f.read(4),'little')         # 0x20
                    block.type = int.from_bytes(f.read(4),'little')         # 0x24
                    unknown_0x28 = int.from_bytes(f.read(4),'little')
                    unknown_0x2c = int.from_bytes(f.read(4),'little')
                    unknown_0x30 = int.from_bytes(f.read(4),'little')
                    unknown_0x34 = int.from_bytes(f.read(4),'little')
                    unknown_0x38 = int.from_bytes(f.read(4),'little')
                    unknown_0x3c = int.from_bytes(f.read(4),'little')
                    unknown_0x40 = int.from_bytes(f.read(4),'little')
                    unknown_0x44 = int.from_bytes(f.read(4),'little')
                    unknown_0x48 = int.from_bytes(f.read(4),'little')
                    unknown_0x4c = int.from_bytes(f.read(4),'little')
                    #print(f"unknown 32bit int at 0x28: {hex(unknown_0x28)}")
                    #print(f"unknown 32bit int at 0x2c: {hex(unknown_0x2c)}")
                    #print(f"unknown 32bit int at 0x30: {hex(unknown_0x30)}")
                    #print(f"unknown 32bit int at 0x34: {hex(unknown_0x34)}")
                    #print(f"unknown 32bit int at 0x38: {hex(unknown_0x38)}")
                    #print(f"unknown 32bit int at 0x3c: {hex(unknown_0x3c)}")
                    #print(f"unknown 32bit int at 0x40: {hex(unknown_0x40)}")
                    #print(f"unknown 32bit int at 0x44: {hex(unknown_0x44)}")
                    #print(f"unknown 32bit int at 0x48: {hex(unknown_0x48)}")
                    #print(f"unknown 32bit int at 0x4c: {hex(unknown_0x4c)}")
                    vertex_blocks.append(block)
                    offset += 0x50
                    continue
                
                if part_entries[x].type == part_entries[0].type + 1:
                    # index block
                    #print(f"index unk0xc: {hex(part_entries[x].unknown_0xc)}")
                    #print(f"index block at {hex(offset)}")
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
            
            chunk_data_map = {}
            more_chunks = True
            chunk_data = b""
            nChunk = 0
            manager = ModulesManager.ModulesManagerContainer.manager
            while more_chunks:
                try:
                    chunk_path = f"{self.filepath}[{nChunk}_mesh_resource.chunk{nChunk}]"
                    #print(f"Trying to read chunk {chunk_path}")
                    chunk = manager.getFileHandle(chunk_path,self.use_modules)
                    chunk_data += chunk.read()#open(chunk_path,'rb').read()
                    chunk.close()
                    nChunk += 1
                except:
                    more_chunks = False
            print(f"Read {nChunk} chunks ({hex(len(chunk_data))} bytes)")

            # this part of the code is just copied over from HIME
            #for i, chunk in enumerate([x for x in os.listdir(folder) if ".chunk" in x and ".render_model" in x]):  # praying they read in order - TODO check this with a large file >10 or >100 chunks
            #    cdata = open(f"{folder}/{chunk}", "rb").read()
            #    index = int(chunk[:-1].split(".chunk")[-1])
            #    chunk_data_map[index] = cdata
#
            #chunk_data = b""
            #for i in range(len(chunk_data_map.keys())):
            #    chunk_data += chunk_data_map[i]




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
                
                if mesh_part.lod != import_settings.lod:
                    #print("LOD doesn't match, ignoring Mesh")
                    continue

                material_path = mesh_part.parts[0].material_path
                mesh_name = ""
                if len(string_table.name_string.split('\\')) >= 2:
                    mesh_name += string_table.name_string.split('\\')[-2]
                if len(material_path.split('\\')) >= 1:
                    mesh_name += "."
                    mesh_name += material_path.split('\\')[-1]
                #mesh_name = string_table.name_string.split('\\')[-2] + "." + material_path.split('\\')[-1]
                if mesh_name == "":
                    mesh_name = "unknown mesh"
                print(f"Using mesh name {mesh_name}")
                #print("Mesh")
                #for p in range(len(mesh_part.parts)):
                #    print(f"unk 0xc: {hex(mesh_part.parts[p].unk0xc)} unk 0x10: {hex(mesh_part.parts[p].unk0x10)}")
                src_mesh.index_count = mesh_part.index_count
                src_mesh.vertex_blocks = vblocks
                src_mesh.index_block = index_blocks[mesh_blocks[mesh_block].index_block]
                src_mesh.mesh_parts = mesh_part.parts
                scaleModifier = ScaleModifier()
                scaleModifier.x = self.scale_modifier[0]
                scaleModifier.y = self.scale_modifier[1]
                scaleModifier.z = self.scale_modifier[2]
                processMesh(src_mesh,chunk_data, scale, scaleModifier,mesh_name)

            

            return


        addon_prefs = context.preferences.addons[__package__].preferences

        self.root_folder = addon_prefs.root_folder
        self.shader_file = addon_prefs.shader_file
        self.shader_name = addon_prefs.shader_name

        #with open(self.filepath,'rb') as f:
        #    if f.read(4) != b'ucsh':
        #        self.report({"ERROR"},"Wrong magic")
        #        return {"CANCELLED"}
        #    openRenderModel(f)
        f = ModulesManager.ModulesManagerContainer.manager.getFileHandle(self.filepath,self.use_modules)
        openRenderModel(f)
        f.close()
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.use_modules:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.execute(context)
            return {'FINISHED'}
        

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