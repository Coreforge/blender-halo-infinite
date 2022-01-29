import sys
from bl_ui.space_sequencer import selected_sequences_len
import bpy

if 'DEBUG_MODE' in sys.argv:
    from Texture import Texture
else:
    from . Texture import Texture

class ImportSettings:
    lod = -1
    mipmap = -1
    norm_signed = True
    def __init__(self):
        self.lod = -1
        self.mipmap = -1
        self.norm_signed = True

class ImportTextureOp(bpy.types.Operator):
    bl_idname = "infinite.infinitetexture"
    bl_label = "Import Halo Infinite Bitmap"
    bl_description = "import a halo infinite bitmap"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    use_modules: bpy.props.BoolProperty(
        default=False,
        name="use modules",
        options={"HIDDEN"}
    )

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

    def execute(self, context):
        name = self.filepath.replace('\\','/').split('/')[-1].split('.')[0].split('{')[0] # get the file name and remove unneccesary stuff
        settings = ImportSettings()
        settings.mipmap = self.mipmap
        settings.norm_signed = self.norm_signed
        tex = Texture()
        tex.readTexture(self.filepath,name,settings, self.use_modules)

        return {'FINISHED'}

    def invoke(self,context,event):
        if not self.use_modules:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.execute(context)
            return {"FINISHED"}
        

def menu_func(self,context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ImportTextureOp.bl_idname,text="Halo Infinite Bitmap")

def register():
    print("loaded")
    bpy.utils.register_class(ImportTextureOp)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    
def unregister():
    print("unloaded")
    bpy.utils.unregister_class(ImportTextureOp)