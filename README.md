# blender-halo-infinite

This plugin is based on HIME by MontagueM (https://github.com/MontagueM/HaloInfiniteModelExtractor).

To import models, make sure all related chunk files are in the same folder and import the .render_model file. 
Importing Textures requires the module texture2ddecoder to be installed for blender.

# Shaders
To automatically apply the textures to the models, the shader needs to have Image Texture nodes named "normal", "asg", "mask_0" and "mask_1", corresponding to the textures. If there are issues with shaders not getting copied properly (the position of nodes currently doesn't work, but that's not a functional thing), please open an issue.

# Installing texture2ddecoder
## All platforms
To install python modules for blender, they have to be installed into blenders python environment, not the system environment. To do ths, go to the python console in blender (for example in the scripting workspace) and enter
```
import ensurepip
ensurepip.bootstrap()
```
to install pip into blenders python environment. Then enter
```
import pip
pip.main(['install','texture2ddecoder'])
```
to install the module texture2ddecoder. Pip might complain that a newer version of pip is available, but that can just be ignored.
There will also likely be a warning that the way pip is called might not work in the future, but the other method of calling pip from python doesn't always work.
## Windows
If the platform independent method for some reason doesn't work, this one just calls the python binary instead of using the modules directly, which should allways work. For other platforms, the name of the binary may be different (python3.9 on linux), the rest should be the same though.
```
import subprocess
import sys
import os
python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
subprocess.call([python_exe, "-m", "ensurepip"])
subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
subprocess.call([python_exe, "-m", "pip", "install", "texture2ddecoder"])
```
