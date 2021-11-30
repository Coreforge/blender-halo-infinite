bl_info = {
    "name" : "Halo Infinite render model importer",
    "blender" : (2,90,0),
    "category" : "Import/Export",
    "description" : "Based on HIME (https://github.com/MontagueM/HaloInfiniteModelExtractor)\nImports rendermodels from Halo Infinite",
    "author" : "Coreforge"
}
modulesNames = ["Header", "DataTable", "StringTable", "ContentTable", "renderModel"]

import renderModel

def register():
    renderModel.register()
 
def unregister():
    renderModel.unregister()
 
if __name__ == "__main__":
    register()