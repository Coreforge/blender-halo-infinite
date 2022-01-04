import sys

import bpy

if 'DEBUG_MODE' in sys.argv:
    from Header import Header
    from DataTable import DataTable, DataTableEntry
    from StringTable import StringTable
    from ContentTable import ContentTable, ContentTableEntry
    from Texture import Texture
else:
    from . Header import Header
    from . DataTable import DataTable, DataTableEntry
    from . StringTable import StringTable
    from . ContentTable import ContentTable, ContentTableEntry
    from . Texture import Texture

class Material:
    file_header = Header
    data_entry_table = DataTable
    string_table = StringTable
    material_content_table = ContentTable
    read_data = False
    def __init__(self):
        self.file_header = Header()
        self.data_entry_table = DataTable()
        self.string_table = StringTable()
        self.material_content_table = ContentTable()
        self.read_data = False
        self.name = ""
        pass

    #
    #   add_material: wether to create a material with textures using a premade shader or not
    #   material_name: name of the material to be created
    #
    #
    def readMaterial(self,path,root,import_settings, add_material = False, material_name = None, material_prefab = None):
        with open(path,'rb') as fmat:
            #print(path)
            if not self.file_header.checkMagic(fmat):
                print(f"File {path} has the wrong magic")
                return
            self.file_header.readHeader(fmat)
            #print(f"{hex(self.file_header.content_table_count)} {hex(self.file_header.data_table_count)}")
            self.data_entry_table.readTable(fmat,self.file_header)
            self.string_table.readStrings(fmat,self.file_header)
            self.material_content_table.readTable(fmat,self.file_header,self.data_entry_table)
            #print(f"Content table length: {hex(len(self.material_content_table.entries))}")
            #for s in range(len(self.string_table.strings)):
            #    print(f"Material uses String id {hex(s)}{self.string_table.strings[s]}")

            node_normal = None
            node_asg = None
            node_mask_0 = None
            node_mask_1 = None

            if add_material:
                if material_name not in bpy.data.materials.keys():
                    bpy.data.materials.new(material_name)
                    bpy.data.materials[material_name].use_nodes = True
                    
                    # remove all nodes that blender automatically creates
                    for node in bpy.data.materials[material_name].node_tree.nodes:
                        bpy.data.materials[material_name].node_tree.nodes.remove(node)

                    nodetree = bpy.data.materials[material_name].node_tree
                    #print(material_prefab.node_tree.nodes.keys())
                    for node in material_prefab.node_tree.nodes:
                        #print(node)
                        new_node = bpy.data.materials[material_name].node_tree.nodes.new(node.bl_idname)
                        new_node.location = node.location
                        new_node.label = node.label
                        #new_node.parent = node.parent
                        new_node.name = node.name

                        if new_node.name == 'normal':
                            node_normal = new_node
                        if new_node.name == 'asg':
                            node_asg = new_node
                        if new_node.name == 'mask_0':
                            node_mask_0 = new_node
                        if new_node.name == 'mask_1':
                            node_mask_1 = new_node

                        if(node.bl_idname == 'ShaderNodeGroup'):
                            #print("Copying group node")
                            new_node.node_tree = node.node_tree

                        #print(node.inputs)

                        #for input in node.inputs:
                        #    for link in input.links:
                        #        print(link)
                        #        
                        #        nodetree.links.new( nodetree.nodes[link.from_node.name].outputs[link.from_socket.name],
                        #                            nodetree.nodes[link.to_node.name].inputs[link.to_socket.name])
                        #print(node.outputs)
                        #for output in node.outputs:
                        #    for link in input.links:
                        #        print(link)
                        #        
                        #        nodetree.links.new(link.from_socket,link.to_socket)

                    for node in material_prefab.node_tree.nodes:
                        if node.parent is not None:
                            nodetree.nodes[node.name].parent = nodetree.nodes[node.parent.name]

                    for link in material_prefab.node_tree.links:
                        nodetree.links.new( nodetree.nodes[link.from_node.name].outputs[link.from_socket.name],
                                            nodetree.nodes[link.to_node.name].inputs[link.to_socket.name])
                    #bpy.data.materials[material_name].node_tree.nodes = material_prefab.node_tree.nodes  # = material_prefab.copy()
                    
                else:
                    print(f"Material {material_name} already exists. Overwriting")
                

            for x in range(len(self.material_content_table.entries)):
                content_entry = self.material_content_table.entries[x]

                if self.material_content_table.entries[x].data_reference is None:
                    # Entry has no data linked
                    continue

                if content_entry.hash == b'/\x04A\x1b\xed@\x9asd\x15\xdd\xad\r\xd4[\x19':
                    # Texture Entry
                    for off in range(content_entry.data_reference.offset,content_entry.data_reference.offset + content_entry.data_reference.size,0x9c):
                        fmat.seek(off)
                        id = int.from_bytes(fmat.read(4),'little')
                        entry_type = int.from_bytes(fmat.read(4),'little')
                        fmat.seek(off + 0x1c)
                        tag = fmat.read(4)
                        fmat.seek(off+0x94)
                        idx = int.from_bytes(fmat.read(2),'little')
                        #print(f"Material stuff type: {entry_type} idx: {idx} tag: {tag}")
                        #if entry_type == 0:
                        #    print(f"String: {self.string_table.strings[idx]}")
                        #print(f"Texture? entry id/type: {hex(id)} idx: {hex(idx)}")
                        if id == 0xe5562d34 and tag == b'mtib':
                            print(f"Normal map: {self.string_table.strings[idx]}")
                            name = self.string_table.strings[idx].replace('\\','/').split('/')[-1].split('.')[0].split('{')[0]
                            if name in bpy.data.textures.keys() and import_settings.reuse_textures:
                                blend_tex = bpy.data.textures[name]
                            else:
                                tex = Texture()
                                tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", name,import_settings)
                                blend_tex = tex.blender_texture
                            if node_normal is not None and blend_tex is not None:
                                node_normal.image = blend_tex.image

                        if id == 0x1a319e59:
                            print(f"ASG Control map: {self.string_table.strings[idx]}")
                            name = self.string_table.strings[idx].replace('\\','/').split('/')[-1].split('.')[0].split('{')[0]
                            if name in bpy.data.textures.keys() and import_settings.reuse_textures:
                                blend_tex = bpy.data.textures[name]
                            else:
                                tex = Texture()
                                tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", name,import_settings)
                                blend_tex = tex.blender_texture
                            if node_asg is not None and blend_tex is not None:
                                node_asg.image = blend_tex.image

                        if id == 0x9c06e777 and tag == b'mtib':
                            print(f"Mask 0 Control map: {self.string_table.strings[idx]}")
                            name = self.string_table.strings[idx].replace('\\','/').split('/')[-1].split('.')[0].split('{')[0]
                            if name in bpy.data.textures.keys() and import_settings.reuse_textures:
                                blend_tex = bpy.data.textures[name]
                            else:
                                tex = Texture()
                                tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", name,import_settings)
                                blend_tex = tex.blender_texture
                            if node_mask_0 is not None and blend_tex is not None:
                                node_mask_0.image = blend_tex.image

                        if id == 0x7fb4ec19 and tag == b'mtib':
                            print(f"Mask 1 Control map: {self.string_table.strings[idx]}")
                            name = self.string_table.strings[idx].replace('\\','/').split('/')[-1].split('.')[0].split('{')[0]
                            if name in bpy.data.textures.keys() and import_settings.reuse_textures:
                                blend_tex = bpy.data.textures[name]
                            else:
                                tex = Texture()
                                tex.readTexture(root + "/__chore/pc__/" + self.string_table.strings[idx].replace("\\","/") + "{pc}.bitmap", name,import_settings)
                                blend_tex = tex.blender_texture
                            if node_mask_1 is not None and blend_tex is not None:
                                node_mask_1.image = blend_tex.image
                            
                
                #print(f"Content Table: offset {hex(self.material_content_table.entries[x].data_reference.offset)} size {hex(self.material_content_table.entries[x].data_reference.size)} hash {self.material_content_table.entries[x].hash}")
            self.read_data = True