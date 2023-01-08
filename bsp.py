import mathutils
from mathutils import Matrix
import bpy

from . Header import Header
from . TagRefTable import TagRefTable, TagRefTableEntry
from . DataTable import DataTable, DataTableEntry
from . StringTable import StringTable
from . ContentTable import ContentTable, ContentTableEntry
from . Material import Material
from . renderModel import renderModelImporter
from . import ModulesManager

from . util import readVec3

from time import perf_counter

import struct

class RTGOInstance:
    def __init__(self):
        self.scale = mathutils.Vector()
        self.forward = mathutils.Vector()
        self.left = mathutils.Vector()
        self.up = mathutils.Vector()
        self.position = mathutils.Vector()
        self.rtgo_path = TagRefTableEntry()
        self.foliage_material_palette = TagRefTableEntry()
        # there's still some missing stuff here
        pass

class BSPFile:

    def __init__(self,f):

        # read the file
        self.file_header = Header()
        self.file_header.readHeader(f)

        self.tag_ref_table = TagRefTable()
        self.tag_ref_table.readTable(f,self.file_header)

        self.data_table = DataTable()
        self.data_table.readTable(f,self.file_header)

        self.string_table = StringTable()
        self.string_table.readStrings(f,self.file_header)

        self.content_table = ContentTable()
        self.content_table.readTable(f,self.file_header,self.data_table)
        pass


    # essentially, iterate over the content table and if the 'hash' or rather GUID matches b'\xe6\x06\xed\x1a\xb4F\xac\xf1\xd2\xf2*\x8aJ\xb5Q\xda' and content_table_entry.data_reference is not None
    # call this function and pass to it the file handle for the bsp, the total instance count and the Data Table entry (content_table_entry.data_reference)
    def readInstances(self,f,count : int, dte : DataTableEntry):
        instances = [RTGOInstance(),]*count
        for x in range(count):
            offset = dte.offset + x * 0x140
            instance = RTGOInstance()
            f.seek(offset)
            instance.scale = readVec3(f.read(12))
            instance.forward = readVec3(f.read(12))
            instance.left = readVec3(f.read(12))
            instance.up = readVec3(f.read(12))
            instance.position = readVec3(f.read(12))
            instance.rtgo_path = self.tag_ref_table.getRef(f.read(28))
            instance.foliage_material_palette = self.tag_ref_table.getRef(f.read(28))
            instances[x] = instance       

        return instances
        
# crabs classes
class instance_materials:
    def __init__(self):
        self.BitmapName = ""
        self.File_Path = ""
        self.BitmapTagID = 0
        self.BitmapAssetID = 0
        
class rtgo_instance:
    def __init__(self):
        self.Instance_Index = 0
        self.Scale_Vec = []
        self.Forward_Vec = []
        self.Left_Vec = []
        self.Up_Vec = []
        self.Pos_Vec = []
        self.MaterialCount = 0
        self.MaterialsList = [] #holds list of Material classes

class rtgo_file:
    def __init__(self):
        self.type = -1
        self.parent_index = -1
        self.offset = -1
        self.Object_Name = ""
        self.File_Path = ""
        self.TagID = 0
        self.AssetID = 0
        self.InstanceCount = 0
        self.Rtgo_Instances = [] #holds list of rtgo_instances classes

class ImportBSP(bpy.types.Operator):
    bl_idname = "infinite.bsp"
    bl_label = "Import BSP"
    bl_description = "scenaria_structure_bsp"

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

    def execute(self,context : bpy.types.Context):
        # get the global preferences
        addon_prefs = context.preferences.addons[__package__].preferences

        self.root_folder = addon_prefs.root_folder
        self.shader_file = addon_prefs.shader_file
        self.shader_name = addon_prefs.shader_name

        # crabs BSP code

        total_start = perf_counter()    # not doing much profiling now, but it's still nice to have a total time
        s = ModulesManager.ModulesManagerContainer.manager.getFileHandle(self.filepath,self.use_modules)

        files = [] #list of RTGO files
        RuntimeGeoDirArray = []
        DirString = []
        InstanceTransformList = []

        INST_TRANSFORM_ZEROS = 0

        s.seek(0x0)    
        RTGOcount = s.read().count(b'\x6F\x67\x74\x72\xBC\xBC\xBC\xBC\x00\x00\x00\x00\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC')    
        s.seek(0x0)
        INST_TRANSFORM_COUNT = s.read().count(b'\x6F\x67\x74\x72\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xBC\xBC\xBC\xBC')        
        s.seek(0x0)
        
        file = s.read()        
        try:
            RuntimeGeoDirList_Offset = file.index(b'\x5F\x5F\x63\x68\x6F\x72\x65\x5C\x67\x65\x6E\x5F\x5F\x5C')
        except RuntimeGeoDirList_Offset_Error:
            print("RuntimeGeoDirList_Offset not found")
        try:
            InstanceInfoSection_Offset = file.index(b'\x6F\x67\x74\x72\xBC\xBC\xBC\xBC\x00\x00\x00\x00\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC') - 0x18
        except InstanceInfoSection_Offset_Error:
            print('InstanceInfoSection_Offset not found')
        try:
            RuntimeGeoInstanceIndex_Offset = InstanceInfoSection_Offset + (RTGOcount * 68)
        except RuntimeGeoInstanceIndex_Offset_Error:
            print('RuntimeGeoInstanceIndex_Offset not found')
        try:
            RuntimeGeoInstTransform_Offset = file.index(b'\x6F\x67\x74\x72\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xBC\xBC\xBC\xBC') - 0x50
        except RuntimeGeoInstTransform_Offset_Error:
            print('RuntimeGeoInstTransform_Offset not found')
        try:
            PerInstanceMaterial_Offset = file.index(b'\x74\x61\x6D\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC\xBC') - 0x15
        except PerInstanceMaterial_Offset_Error:
            print('PerInstanceMaterial_Offset not found')

        
        print("RuntimeGeoDirList_Offset: " + str(RuntimeGeoDirList_Offset))
        print("RTGOcount: " + str(RTGOcount))
        print("InstanceInfoSection_Offset: " + str(InstanceInfoSection_Offset))
        print("RuntimeGeoInstanceIndex_Offset: " + str(RuntimeGeoInstanceIndex_Offset))
        print("RuntimeGeoInstTransform_Offset: " + str(RuntimeGeoInstTransform_Offset))
        print("INST_TRANSFORM_COUNT: " + str(INST_TRANSFORM_COUNT))
        print("PerInstanceMaterial_Offset: " + str(PerInstanceMaterial_Offset))

        #DIRECTORY BUILDER
        #seeks to start of runtime geo directory list
        s.seek(RuntimeGeoDirList_Offset)
        for RTGOdir in range(RTGOcount):
            DirString = []
            SampleByte = ""
            Length = 0;
            while not SampleByte == '\x00':   #while loop to run through the directory lists and build strings until it finds a null byte then saves it to an array
                SampleByte = s.read(1).decode("UTF-8")
                if not SampleByte == '\x00':
                    if SampleByte == '\\':
                        SampleByte = '/'
                    #print(SampleByte)
                    #print(DirString)
                    Length = Length + 1
                    DirString.append(SampleByte)
            #print(DirString)
            #RuntimeGeoArray[RTGOdir] = DirString
            DirString = ''.join(DirString)
            #DirString.replace("\\","/")
            RuntimeGeoDirArray.append(DirString)
        
        print("File Directory Loaded")

        #INSTANCE TRANSFORM DATA INDEX BUILDER
        for index in range(INST_TRANSFORM_COUNT - INST_TRANSFORM_ZEROS): #loops through total number of instance transforms                                             HARD CODED (Must be manually counted)
            s.seek(RuntimeGeoInstTransform_Offset) #seek to current listed location in memory
            
            #instantiates class object
            rtgoT = rtgo_instance()
            
            #clears data from old rtgoT objects from other iterations
            rtgoT.Scale_Vec = []
            rtgoT.Forward_Vec = []
            rtgoT.Left_Vec = []
            rtgoT.Up_Vec = []
            rtgoT.Pos_Vec = []
            rtgoT.MaterialCount = 0
            
            #set the data for each index 
            rtgoT.Scale_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Scale_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Scale_Vec.append(struct.unpack('f', s.read(4))[0])
            #print("Instance Scale: (" + str(rtgoF.Rtgo_Instances[inst2].Scale_Vec[0]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Scale_Vec[1]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Scale_Vec[2]) + ")")
                
            rtgoT.Forward_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Forward_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Forward_Vec.append(struct.unpack('f', s.read(4))[0])
            #print("Instance Forward: (" + str(rtgoF.Rtgo_Instances[inst2].Forward_Vec[0]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Forward_Vec[1]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Forward_Vec[2]) + ")")
                
            rtgoT.Left_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Left_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Left_Vec.append(struct.unpack('f', s.read(4))[0])
            #print("Instance Left: (" + str(rtgoF.Rtgo_Instances[inst2].Left_Vec[0]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Left_Vec[1]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Left_Vec[2]) + ")")
                
            rtgoT.Up_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Up_Vec.append(struct.unpack('f', s.read(4))[0])
            rtgoT.Up_Vec.append(struct.unpack('f', s.read(4))[0])
            #print("Instance Up: (" + str(rtgoF.Rtgo_Instances[inst2].Up_Vec[0]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Up_Vec[1]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Up_Vec[2]) + ")")
                
            rtgoT.Pos_Vec.append((struct.unpack('f', s.read(4))[0]))
            rtgoT.Pos_Vec.append((struct.unpack('f', s.read(4))[0]))
            rtgoT.Pos_Vec.append((struct.unpack('f', s.read(4))[0]))
            
            #Saves correct data confirmed
            #print("Instance Pos: (" + str(rtgoT.Pos_Vec[0]) + ", " + str(rtgoT.Pos_Vec[1]) + ", " + str(rtgoT.Pos_Vec[2]) + ")")
                
                
            s.seek(s.tell() + 0xC + 0x8 + 0x24)
            s.seek(s.tell() + 0x8) #skips RuntimeGeoMeshIndex, Unique IO Index, and flags etc
            s.seek(s.tell() + 0x18) #skips Bounds XYZ Min/Max
            s.seek(s.tell() + 0x10) #skips World Bound Sphere Center XYZ and radius
            s.seek(s.tell() + 0x5C) #skips bunch of stuff that is likely not needed
                
            rtgoT.MaterialCount = int.from_bytes(s.read(4), 'little') #adds Material Count
                
            s.seek(s.tell() + 0x10)
            s.seek(s.tell() + 0xC + 0xC) #skips Rect XYZ Min and Max
            s.seek(s.tell() + 0x4) #skips ExternalGUID
            s.seek(s.tell() + 0x10) 
                
            RuntimeGeoInstTransform_Offset = s.tell() #save location in memory
            #print("   Instance Transforms Loaded: " + str(index + 1))
            
            #add Transform Info List to Array List
            InstanceTransformList.append(rtgoT)
            
        print("Instance Transform Index Data Loaded")



        #MAIN RUNTIME LIST BUILDER
        #for r in range(RTGOcount):
        for r in range(RTGOcount): #RTGOcount):                                             #might need to alter this for some bsps with odd index numbers
            #rtgo class object template
            rtgoF = rtgo_file()
            
            rtgoF.Object_Name = ""
            rtgoF.File_Path = ""
            rtgoF.TagID = 0
            rtgoF.AssetID = 0
            rtgoF.InstanceCount = 0
            rtgoF.Rtgo_Instances = [] #holds list of rtgo_instances classes
            
            #Get Object Name
            slashCount = RuntimeGeoDirArray[r].count('/')
            rtgoF.Object_Name = RuntimeGeoDirArray[r].split('/')[slashCount - 1] #grab object name
            #print("rtgoF.Object_Name later: " + rtgoF.Object_Name)
            #print("")
            
            #Get FILE PATH
            rtgoF.file_path = RuntimeGeoDirArray[r] + "{rt}.runtime_geo" #grabs full dir path
            
            #Get TAG ID + ASSET ID + INSTANCE COUNT
            s.seek(InstanceInfoSection_Offset)
            s.seek(s.tell() + 0xC) #skip 12 bytes
            rtgoF.TagID = int.from_bytes(s.read(4), 'little') #grabs TAG ID
            rtgoF.AssetID = int.from_bytes(s.read(8),'little') #grab Asset ID
            s.seek(s.tell() + 0x4) #skip 4 bytes [RTGO_TagGroup]
            s.seek(s.tell() + 0x18) #skip 24 bytes
            #print(str(s.tell()))
            rtgoF.InstanceCount = int.from_bytes(s.read(4), 'little') #grab Instance Count
            s.seek(s.tell() + 0xC) #skip 12 bytes
            
            InstanceInfoSection_Offset = s.tell() #Save current location in memory to offset variable                       
            #print("InstanceCount: " + str(rtgoF.InstanceCount))
            
            #Get INSTANCE Index LIST
            for inst1 in range(rtgoF.InstanceCount): #loop thrugh total instances for each rtgo object
                rtgoinst = rtgo_instance() 
                #possibly clear the list upon restart?
                SampleByte = ""
                
                s.seek(RuntimeGeoInstanceIndex_Offset)  #seek to current value of offset
                     
                #handling for null bytes added for alignment in this index
                SampleByte = s.read(2) #read 2 bytes ahead as a test
                #print("SampleByte: " + str(SampleByte))
                
                s.seek(s.tell() - 0x2) #go back 2 bytes
                if (r > 0 and SampleByte == b'\x00\x00'):
                    s.seek(s.tell() + 0x2) #seek past found null byte made for alignment
                    #print("Null Byte Found")
                    
                    
                rtgoinst.Instance_Index = int.from_bytes(s.read(2), 'little') #reads byte into index
                #print("        runtime instance index: " + str(rtgoinst.Instance_Index))
                rtgoF.Rtgo_Instances.append(rtgoinst) #add current rtgoinst object to list
                
                RuntimeGeoInstanceIndex_Offset = s.tell() #saves current spot in memory atvthe variable
                #print("Instance Indices Loaded: " + str(inst1 + 1))
            
            #Get INSTANCE TRANSFORM INFORMATION
            for inst2 in range(rtgoF.InstanceCount):
                
                #clear old data
                rtgoF.Rtgo_Instances[inst2].Scale_Vec = []
                rtgoF.Rtgo_Instances[inst2].Forward_Vec = []
                rtgoF.Rtgo_Instances[inst2].Left_Vec = []
                rtgoF.Rtgo_Instances[inst2].Up_Vec = []
                rtgoF.Rtgo_Instances[inst2].Pos_Vec = []
                
                #saves true instance transform index to temp variable
                instance_transform_index = rtgoF.Rtgo_Instances[inst2].Instance_Index
                
                
                #print("")
                #print("inst2: " + str(inst2))
                #print("InstanceTransformList Count: " + str(len(InstanceTransformList)))
                #print("instance_transform_index: " + str(instance_transform_index))
                #print("")
                
                
                #links up all transform data for each instance object
                rtgoF.Rtgo_Instances[inst2].Scale_Vec = InstanceTransformList[instance_transform_index].Scale_Vec
                rtgoF.Rtgo_Instances[inst2].Forward_Vec = InstanceTransformList[instance_transform_index].Forward_Vec
                rtgoF.Rtgo_Instances[inst2].Left_Vec = InstanceTransformList[instance_transform_index].Left_Vec
                rtgoF.Rtgo_Instances[inst2].Up_Vec = InstanceTransformList[instance_transform_index].Up_Vec
                rtgoF.Rtgo_Instances[inst2].Pos_Vec = InstanceTransformList[instance_transform_index].Pos_Vec
                
                #print("Instance Pos: (" + str(rtgoF.Rtgo_Instances[inst2].Pos_Vec[0]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Pos_Vec[1]) + ", " + str(rtgoF.Rtgo_Instances[inst2].Pos_Vec[2]) + ")")
                
                #links up Material Count for each instance object
                rtgoF.Rtgo_Instances[inst2].MaterialCount = InstanceTransformList[instance_transform_index].MaterialCount 
                                
                #print("   Instance Transforms Loaded: " + str(inst2 + 1))
                
                
                #Material List Builder
                for inst3 in range(rtgoF.Rtgo_Instances[inst2].MaterialCount):
                    mat = instance_materials()
                    
                    s.seek(PerInstanceMaterial_Offset) #jump to saved location in memory
                    s.seek(s.tell() + 0x8)
                    
                    #BUILD LIST OF ALL BITMAP DIRECTORIES AND FIND THE BITMAP LINK TO TAG ID                    ASSETID
                    #Get BITMAP NAME
                    
                    #Get BITMAP DIRECTORY
                    
                    #Get BITMAP TAG ID
                    mat.BitmapTagID = int.from_bytes(s.read(4), 'little')
                    
                    #Get BITMAP ASSET ID
                    mat.BitmapAssetID = int.from_bytes(s.read(4), 'little')
                    
                    s.seek(s.tell() + 0x8) 
                    
                    #Handles the 4 float values that come after each section of ijstance materials
                    if (inst3 == rtgoF.Rtgo_Instances[inst2].MaterialCount - 1):
                        PerInstanceMaterial_Offset = (PerInstanceMaterial_Offset + 0x10) #skips 12 at end of last material section
                    
                    PerInstanceMaterial_Offset = s.tell() #save location in memory
                    rtgoF.Rtgo_Instances[inst2].MaterialsList.append
                    #print("        Instance Materials Loaded: " + str(inst3 + 1))
            
            #BUILD LIST OF RUNTIME GEO INFORMATION
            #print("Runtime Geo Tags Loaded: " + str(r + 1))
            files.append(rtgoF)
            #print("Pos for 1st obj: " + str(files[0].Rtgo_Instances[0].Pos_Vec))
            
        #print(files)
        #print("Count of Runtime Geometry Directory: " + str(len(RuntimeGeoDirArray)))

        #profiling
        init_end = perf_counter()
        #loops through count of runtime objects on map and loads them into Blender one by one
        init_time = init_end - total_start
        inst_total = 0
        rtgo_total = 0
        obj_cpy_total = 0




        #reset loop values
        i=0
        k=0
        for i in range(RTGOcount):
            #f = ModulesManager.ModulesManagerContainer.manager.getFileHandle(self.filepath,self.use_modules)
            
            #rtgo_file.file_path = UnpackDir + RuntimeGeoDirArray[i]  + "{rt}.runtime_geo"
            rtgo = ModulesManager.ModulesManagerContainer.manager.getFileHandle(self.root_folder + "/" + files[i].file_path, self.use_modules)
            #print("Trying to read RTGO file: " + files[i].file_path)
            print("Loaded Object " + str(i + 1) + "/" + str(RTGOcount))
            #self.filepath = self.root_folder + "/" + files[i].file_path

            # object for this RTGO
            rtgo_start = perf_counter()
            rtgo_group_obj = bpy.data.objects.new(files[i].file_path.split('/')[-1].split('.')[0] + "_all",None)
            rtgo_group_obj.name = files[i].Object_Name
            bpy.context.view_layer.active_layer_collection.collection.objects.link(rtgo_group_obj)

            rtgo_obj = bpy.data.objects.new(files[i].file_path.split('/')[-1].split('.')[0],None)
            #tries to properly name each object
            rtgo_obj.name = files[i].Object_Name
            bpy.context.view_layer.active_layer_collection.collection.objects.link(rtgo_obj)
            rtgo_obj.parent = rtgo_group_obj

            ir = renderModelImporter()
            ir.filepath = self.root_folder + "/" + files[i].file_path
            ir.root_folder = self.root_folder
            ir.openRenderModel(rtgo,parent=rtgo_obj)
            rtgo_end = perf_counter()
            rtgo_total += rtgo_end - rtgo_start

    #COMMENTING THIS OUT FOR TESTING
 
        #store entire list of Instance Transforms from Instance List
        #For each RTGO store the list of indices for each instance
            #spawn objects with the transform data for each proper index
 
 
 
            for k in range(files[i].InstanceCount):
                #profiling
                #print("Instance Index: " + str(files[i].Rtgo_Instances[k].Instance_Index))
                inst_start = perf_counter()
                #print("i: " + str(i) + "k: " + str(k))
                
                #Create Position Offsets
                Pos_Vectors = files[i].Rtgo_Instances[k].Pos_Vec
                
                #Create Transform Matrix
                Scale_Vectors = files[i].Rtgo_Instances[k].Scale_Vec
                Forward_Vectors = files[i].Rtgo_Instances[k].Forward_Vec
                Left_Vectors = files[i].Rtgo_Instances[k].Left_Vec
                Up_Vectors = files[i].Rtgo_Instances[k].Up_Vec
                Right_Vectors = []
                
                #Create Right Vector from left Vector
                Right_Vectors.append(-1 * (Left_Vectors[0]))
                Right_Vectors.append(-1 * (Left_Vectors[1]))
                Right_Vectors.append(-1 * (Left_Vectors[2]))
                
                # print("")
                # print("i: " + str(i) + "   K:  " + str(k))
                # print("")
                # print("Position Values:")
                # print(files[i].Rtgo_Instances[k].Pos_Vec)
                # print("")
                # print("Position Vector:")
                # print(Pos_Vectors)
                # print("")
                # print("Forward Vector:")
                # print(Forward_Vectors)
                # print("")
                # print("Left Vector:")
                # print(Left_Vectors)
                # print("")
                # print("Right Vector:")
                # print(Right_Vectors)
                # print("")
                # print("Up Vector:")
                # print(Up_Vectors)
                # print("")
                
                PosVectorX = []
                PosVectorY = []
                PosVectorZ = []
                PosVecList = []
        
                ScaleVectorX = []
                ScaleVectorY = []
                ScaleVectorZ = []
                ScaleVecList = []
                
                #build scale vector list to make matrix like:
                #x00
                #0y0
                #00z
                #this will be fed into the ScaleMatrix
                
                ScaleVectorX.append(Scale_Vectors[0])
                ScaleVectorX.append(0.000)
                ScaleVectorX.append(0.00)
                
                ScaleVectorY.append(0.00)
                ScaleVectorY.append(Scale_Vectors[1])
                ScaleVectorY.append(0.00)
                
                ScaleVectorZ.append(0.00)
                ScaleVectorZ.append(0.00)
                ScaleVectorZ.append(Scale_Vectors[2])
                
                ScaleVecList.append(ScaleVectorX)
                ScaleVecList.append(ScaleVectorY)
                ScaleVecList.append(ScaleVectorZ)
                
                #build the Vector list that is fed into the Transform Matrix
                Vectors = []
                Vectors.append(Forward_Vectors)
                Vectors.append(Left_Vectors)
                Vectors.append(Up_Vectors)
                
                #print(Scale_Vectors)
                #print(Forward_Vectors)
                #print(Left_Vectors)
                #print(Up_Vectors)
                #print(Vectors)
                #NOTES
                #Left = Up x Forward
                matrix = Matrix(Vectors)
                ScaleMatrix = Matrix(ScaleVecList)
                
                #Vectors [Forward, Left/Right, Up] turned into Matrix 
                TransformMatrix = Matrix(Vectors)

                matrix = Matrix(Vectors)

                #TransformMatrix.normalize()

                
                #3x3 transform matrices multiplied together
                RotationMatrix = ScaleMatrix @ TransformMatrix
                
                #changing to a 4x4 matrix
                #RotationMatrix.resize_4x4()
                
                #print("")
                #print("Scale Vector:")
                #print(ScaleMatrix)
                
                #print("")
                #print("Transform Matrix:")
                #print(TransformMatrix)
                
                #print("")
                #print("Rotation Matrix Result:")
                #print(RotationMatrix)              
                
                
                
                #mat_source = ob.matrix_world.to_3x3()
                
                #forward = X
                #right = Y
                #up = Z
                
                #matrix = Matrix((forward, right, up))
                #matrix.normalize()
                #mat_target = Matrix.Translation(location) * mat.to_4x4()
                
                #print(mat_target)
                
                
                #print("Render Model Pos: (" + str(Pos_Vectors[0]) + ", " + str(Pos_Vectors[1]) + ", " + str(Pos_Vectors[2]) + ")")

                #profiling
                inst_end = perf_counter()

                # the first instance doesn't need a copy of the object, as we can just use the object created when importing the rtgo
                if k != 0:
                    #openRenderModel(rtgo, (Pos_Vectors[0],Pos_Vectors[1],Pos_Vectors[2]))
                    #print("")
                    #print("rtgo_obj.name: " + rtgo_obj.name)
                    #rtgo_obj.name = files[i].Object_Name 
                    #print("files[i].Object_Name later: " + files[i].Object_Name)
                    #print("")
                    
                    inst_obj = bpy.data.objects.new(rtgo_obj.name + "_inst_" + str(k),rtgo_obj.data)
                    #inst_obj.data = rtgo_obj.data.copy()
                    bpy.context.view_layer.active_layer_collection.collection.objects.link(inst_obj)
                    #bsp_collection.objects.link(inst_obj)
                    inst_obj.parent = rtgo_group_obj
                    # copy the child objects too and link their data
                    for obj in rtgo_obj.children:
                        inst_child_obj = bpy.data.objects.new(obj.name + "_inst_" + str(k),obj.data)
                        inst_child_obj.parent = inst_obj
                        bpy.context.view_layer.active_layer_collection.collection.objects.link(inst_child_obj)
                        #bsp_collection.objects.link(inst_child_obj)
                else:
                    inst_obj = rtgo_obj
                
                #transforms for the runtime_geo objects
                inst_obj.location = (Pos_Vectors[0],Pos_Vectors[1],Pos_Vectors[2])
                inst_obj.scale = (Scale_Vectors[0],Scale_Vectors[1],Scale_Vectors[2])
                
                #tries to fix Z axis issue
                Euler = matrix.to_euler('XYZ')
                Euler.z = Euler.z * -1
                inst_obj.rotation_euler = Euler
                #inst_obj.rotation_euler = matrix.to_euler('XYZ')


                #object rotation in Blender    
                #inst_obj.matrix_local = (RotationMatrix)
                #inst_obj.rotation_euler = RotationMatrix
                #inst_obj.rotation_euler = TransformMatrix.to_euler('XYZ')

                #object position in Blender
                #inst_obj.location = (Pos_Vectors[0],Pos_Vectors[1],Pos_Vectors[2])

                #profiling
                cpy_end = perf_counter()

                inst_total += inst_end - inst_start
                obj_cpy_total += cpy_end - inst_end
            
            rtgo.close()

        s.close()
        total_end = perf_counter()
        time_total = total_end - total_start
        print(f"Total time: {time_total}")
        print(f"Time reading bsp info: {init_time}")
        print(f"Time parsing instance data: {inst_total}")
        print(f"Time reading rtgo: {rtgo_total}")
        print(f"Total time instantiating objets: {obj_cpy_total}")

        return {'FINISHED'}

    def invoke(self,context : bpy.types.Context, event):
        if not self.use_modules:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}
        else:
            self.execute(context)
            return {"FINISHED"}

    
def menu_func(self,context : bpy.types.Context):
    self.layout.operator_context = "INVOKE_DEFAULT"
    self.layout.operator(ImportBSP.bl_idname,text = "Halo Infinte BSP")

def register():
    bpy.utils.register_class(ImportBSP)
    #bpy.utils.register_class(BSPFile)
    #bpy.utils.register_class(RTGOInstance)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ImportBSP)
    #bpy.utils.unregister_class(BSPFile)
    #bpy.utils.unregister_class(RTGOInstance)