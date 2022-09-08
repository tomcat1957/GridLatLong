import json
import os
import pathlib
import sys

import axipy
import pip

name_folder_Axioma_Moduls='Plugins'

def GetHomeAxiomaFolder():
    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming/ESTI/Axioma.GIS"
    elif sys.platform == "linux":
        return home / ".local/share/ESTI/Axioma.GIS"
    elif sys.platform == "darwin":
        return home / "Library/Application Support/ESTI/Axioma.GIS"
def createFolder(name_folder):
    base_folder_axi=GetHomeAxiomaFolder()
    folder_new =base_folder_axi / name_folder
    if not folder_new.exists():
        #folder_new.mkdir()
        os.makedirs(str(folder_new))
    return str(folder_new)
def createFolderAxiomaModuls():
    createFolder(name_folder_Axioma_Moduls)
def ExistAxiomaModulesFolder():
    name_axioma=GetHomeAxiomaFolder()
    folder_modules=name_axioma / name_folder_Axioma_Moduls
    return folder_modules.exists()
def createFolderInModuls(name):
    bExistAxiomaModules=ExistAxiomaModulesFolder()
    if not bExistAxiomaModules:
        createFolderAxiomaModuls()
    name_axioma = GetHomeAxiomaFolder()
    folder_modules = name_axioma /  name_folder_Axioma_Moduls
    folder_name=folder_modules / name
    if not folder_name.exists():
        os.makedirs(str(folder_name))
    if folder_name.exists():
        return str(folder_name)
    return None
def writeJson(data,path):
    with open(path, "w",encoding='utf-8') as write_file:
        json.dump(data, write_file,ensure_ascii=False)
def readJson(path):
    data=None
    with open(path,  encoding='utf-8') as read_file:
        data = json.load(read_file)
    return data
def readPropertyes(name_plugin,file_name):
    name_folder_plugin = createFolderInModuls(name_plugin)
    path_properties = os.path.join(name_folder_plugin,file_name)
    if os.path.exists(path_properties):
        ''' Файл существует читаем '''
        data_proporties=readJson(path_properties)
        return data_proporties
    return None
def saveProperties(name_plugin,name_file,property_obj):
    name_folder_plugin = createFolderInModuls(name_plugin)
    path_properties = os.path.join(name_folder_plugin, name_file)
    writeJson(property_obj, path_properties)
def createPythonLib(name_folder_lib='pylib'):
    pathPyLib = createFolder(name_folder_lib)
    return pathPyLib
def installTool(name_pack,name_folder_lib='pylib'):
    '''
    установка требуемого пакета
    :param name_pack:
    :return:
    '''
    pathPyLib = createFolder(name_folder_lib)
    pip.main(['install', '-t', pathPyLib, name_pack])
    return
def addPathEnv(folder):
    '''
    Добавить директорию в python
    :param folder:
    :return:
    '''
    if folder in sys.path:
        return
    sys.path.append(folder)
def getMapViewByName(name_map):
    for view_map in axipy.gui.view_manager.views:
        if isinstance(view_map,axipy.MapView):
            name=view_map.widget.windowTitle()
            if name==name_map:
                return view_map
    return None
def getIdLayerinMap(list_layer,name_layer):
    index_layer=0
    for layer in list_layer:
        if layer.title==name_layer:
            return index_layer
    return -1
