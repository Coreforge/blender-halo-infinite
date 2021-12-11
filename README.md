# blender-halo-infinite

This plugin is based on HIME by MontagueM (https://github.com/MontagueM/HaloInfiniteModelExtractor).

To import models, make sure all related chunk files are in the same folder and import the .render_model file. 
Importing Textures requires the module texture2ddecoder to be installed for blender.

# Installing texture2ddecoder

To install python modules for blender, they have to be installed into blenders python environment, not the system environment. To do ths, go to the python console in blender (for example in the scripting workspace) and enter
```
import ensurepip
ensurepip.bootstrap()
```
to install pip into blenders python environment. Then enter
```
import pip
pip._internal.cli.main.main(['install','texture2ddecoder'])
```
to install the module texture2ddecoder. Pip might complain that a newer version of pip is available, but that can just be ignored.
