from os import path
import bpy
from . import ModulesManager


class ModuleEntry(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(name="active")
    filename: bpy.props.StringProperty(name="")
    path: bpy.props.StringProperty()
    type: bpy.props.StringProperty()

class ModuleEntryProxy(bpy.types.PropertyGroup):
    entries: bpy.props.CollectionProperty(type = ModuleEntry)
    index: bpy.props.IntProperty(name = "Index",default=0)

class ImporterSettings(bpy.types.PropertyGroup):

    #################################################
    #
    #   Settings for render_model import
    #
    #################################################
    auto_import_dependencies: bpy.props.BoolProperty(
        name="Import dependencies",
        description="Automatically import data like Textures",
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

class loadModulesOperator(bpy.types.Operator):
    bl_idname = "infinite.loadmodules"
    bl_name = "load modules"
    bl_label = "load modules"
    #global tree_view
    def execute(self, context):
        #global tree_view
        addon_prefs = context.preferences.addons[__package__].preferences

        ModulesManager.ModulesManager.resources.append("test")
        ModulesManager.ModulesManager.resources_updated = True
        manager = ModulesManager.ModulesManagerContainer.manager
        manager.loadOodle(addon_prefs.oodle_lib_path)
        manager.findModules(addon_prefs.module_deploy_path)
        manager.loadModules()
        manager.buildFileTree()
        bpy.context.scene.modules_list.entries.clear()
        print(f"Children of active Node: {len(ModulesManager.ModulesManagerContainer.manager.activeNode.children.keys())}")
        entries = bpy.context.scene.modules_list.entries
        node = ModulesManager.ModulesManagerContainer.manager.activeNode
        for i in node.children.keys():
            entries.add()
            entries[-1].filename = i
            entries[-1].path = node.children[i].path
            entries[-1].type = node.children[i].type
            pass
        return {"FINISHED"}

class setActiveNodeOperator(bpy.types.Operator):
    bl_idname = "infinite.setactivenode"
    bl_name = "set current directory"
    bl_label = "set current directory"
    path: bpy.props.StringProperty()
    def execute(self, context):
        entries = bpy.context.scene.modules_list.entries
        manager = ModulesManager.ModulesManagerContainer.manager

        # if we currently are at the root, do nothing
        if self.path == "" or self.path == "/":
            manager.activeNode = manager.rootEntry
        else:
            # set the active node to the node that was specified (which can't be directly passed)
            currentNode = manager.rootEntry
            if self.path[0] == '/':
                self.path = self.path[1:]
            for entry in self.path.split("/"):
                currentNode = currentNode.children[entry]
            manager.activeNode = currentNode

        node = manager.activeNode
        entries.clear()
        print(f"New path: {self.path}")
        print(f"Node path: {node.path}")
        for i in node.children.keys():
            entries.add()
            entries[-1].filename = i
            entries[-1].path = node.children[i].path
            entries[-1].type = node.children[i].type
        return {"FINISHED"}

class TREE_UL_List(bpy.types.UIList):
    
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):
        importer_settings = bpy.context.scene.infinite_importer_settings
        if item.type == "DIR":
            #layout.label(text=item.filename,icon="FILEBROWSER")
            layout.operator("infinite.setactivenode",icon="FILE_FOLDER",text=item.filename,emboss=False).path = item.path
        if item.type == "FILE":
            if item.filename.split(".")[-1] == "render_model" or item.filename.split(".")[-1] == "runtime_geo":
                #layout.label(text=item.filename,icon="FILE_3D")
                op = layout.operator("infinite.rendermodel",icon="FILE_3D",text=item.filename,emboss=False)
                op.filepath = item.path
                op.use_modules = True
                op.auto_import_dependencies = importer_settings.auto_import_dependencies
                op.import_uvs = importer_settings.import_uvs
                op.import_weights = importer_settings.import_weights
                op.import_normals = importer_settings.import_normals
                op.reuse_textures = importer_settings.reuse_textures
                op.add_materials = importer_settings.add_materials
                op.populate_shader = importer_settings.populate_shader
                op.import_model = importer_settings.import_model

            elif item.filename.split(".")[-1] == "bitmap":
                layout.label(text=item.filename,icon="FILE_IMAGE")

            else:
                layout.label(text=item.filename,icon="FILE_BLANK")

        #layout.label(text=item.filename,icon="TRIA_RIGHT")

class ModulePanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_halo_infinite_module_panel"
    bl_label = "Halo Infinite Modules"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    

    def draw(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences

        if addon_prefs.module_deploy_path == "":
            self.layout.label(text="Deploy Path not set")
            return

        if addon_prefs.oodle_lib_path == "":
            self.layout.label(text="Oodle lib not specified")
            return
        self.layout.label(text="Halo Infinite Module view")
        self.layout.operator("infinite.loadmodules",text="Load Modules")

        if ModulesManager.ModulesManager.resources_updated:
            ModulesManager.ModulesManager.resources_updated = False
            
            print("updating")
        manager = ModulesManager.ModulesManagerContainer.manager
        fileTree = self.layout.box()
        #entries: bpy.props.CollectionProperty(type=ModuleEntry)
        #for i in ModulesManager.ModulesManager.resources:
        #    curr = entries.add()
        #    curr.filename = i
        topBar = fileTree.row()
        topBarSplit = topBar.split(factor=0.9)
        topBarSplit.column().label(text=manager.activeNode.path)
        topBarSplit.column().operator("infinite.setactivenode",icon="FILE_PARENT",text="").path = manager.activeNode.parent.path
        #fileTree.operator("infinite.setactivenode",icon="FILE_PARENT",text="").path = manager.activeNode.parent.path
        #fileTree.label(text=manager.activeNode.path)
        fileTree.template_list("TREE_UL_List","modules_list",bpy.context.scene.modules_list,"entries",bpy.context.scene.modules_list,"index")
        self.layout.separator()

        modelSettings = self.layout.box()
        modelSettings.label(text="3D Model Settings")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"auto_import_dependencies")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"import_weights")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"import_normals")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"reuse_textures")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"add_materials")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"populate_shader")
        modelSettings.prop(bpy.context.scene.infinite_importer_settings,"import_model")

    @classmethod
    def poll(cls,context):
        return True

def register():
    bpy.utils.register_class(TREE_UL_List)
    bpy.utils.register_class(ModuleEntry)
    bpy.utils.register_class(ModuleEntryProxy)
    bpy.utils.register_class(ModulePanel)
    bpy.utils.register_class(loadModulesOperator)
    bpy.utils.register_class(setActiveNodeOperator)
    bpy.utils.register_class(ImporterSettings)
    bpy.types.Scene.modules_list = bpy.props.PointerProperty(type=ModuleEntryProxy)
    bpy.types.Scene.infinite_importer_settings = bpy.props.PointerProperty(type=ImporterSettings)

def unregister():
    bpy.utils.unregister_class(ModuleEntry)
    bpy.utils.unregister_class(ModulePanel)
    bpy.utils.unregister_class(loadModulesOperator)
    bpy.utils.unregister_class(TREE_UL_List)
    bpy.utils.unregister_class(setActiveNodeOperator)
    del bpy.types.Scene.modules_list
    del bpy.types.Scene.infinite_importer_settings
    