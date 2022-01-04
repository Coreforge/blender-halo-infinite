bl_info = {
    "name" : "Halo Infinite render model importer",
    "blender" : (2,90,0),
    "category" : "Import/Export",
    "description" : "Based on HIME (https://github.com/MontagueM/HaloInfiniteModelExtractor)\nImports rendermodels from Halo Infinite",
    "author" : "Coreforge"
}
modulesNames = ["Header", "DataTable", "StringTable", "ContentTable", "renderModel"]

import sys
import bpy

class HaloInfiniteAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    print(__name__)

    root_folder: bpy.props.StringProperty(
        subtype="FILE_PATH",
        name="Asset Root",
        description="Path to use for additional data. Uses relative path from imported file if none is specified and import dependencies is active",
        default="/home/ich/haloRIP/HIMU/output"
    )

    shader_file: bpy.props.StringProperty(
        name="Shader library",
        description="Path to the blend file containing the shader",
        default="/home/ich/haloRIP/blender_plugin/shaders/Infinite_MP_Shader_v1.8_Made_by_Grand_Bacon.blend"
    )

    shader_name: bpy.props.StringProperty(
        name="Shader name",
        description="Name of the shader within the library",
        default="Infinite MP Shader v1.8 Made by Grand_Bacon"
    )

    def draw(self,context):
        layout = self.layout
        layout.label(text="Halo Infinite importer preferences")
        layout.prop(self,"root_folder")
        layout.prop(self,"shader_file")
        layout.prop(self,"shader_name")


if 'DEBUG_MODE' in sys.argv:
    import renderModel
else:
    from . import renderModel
    from . import TextureOp

def register():
    bpy.utils.register_class(HaloInfiniteAddonPreferences)
    TextureOp.register()
    renderModel.register()
 
def unregister():
    bpy.utils.unregister_class(HaloInfiniteAddonPreferences)
    TextureOp.unregister()
    renderModel.unregister()
 
if __name__ == "__main__":
    register()