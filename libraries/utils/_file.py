import os
import subprocess
import platform
import zipfile
import logging
import tarfile
import shutil

def get_os():
    os_name = platform.uname()[0].lower()
    if os_name == "windows" or os_name == "linux":
        return os_name
    else:
        return "unknow"


def chdir(directory):
    os.chdir(directory)
    logging.debug("[CHDIR] %s" % os.getcwd())


def get_architechture():
    architecture = platform.machine()
    logging.debug("getting architechture : %s" % architecture)
    return architecture

def mkdir_recurcive(path):
    logging.debug("[file] making directory %s" % path)
    if os.path.isdir(path):
        return True

    delim = ""
    if "/" in path:
        delim = "/"
    elif "\\" in path:
        delim = "\\"
    
    if delim != "":
        path_splitted = path.split(delim)

        full_path = ""

        for i in range(len(path_splitted)):
            if i != len(path_splitted) - 1:
                separator = delim
            else:
                separator = ""
                
            full_path += "%s%s" % (path_splitted[i], separator)

            if os.path.isdir(full_path) == False:
                os.mkdir(full_path)
    else:
        os.mkdir(path)

    return True

def rm_rf(path):
    logging.debug("[file] deleting %s" % path)
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))

        for name in dirs:
            os.rmdir(os.path.join(root, name))

    if os.path.isdir(path):
        os.rmdir(path)
    elif os.path.isfile(path):
        os.remove(path)

def find_folder(folder_name, path="."):
    list_folders = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            if folder_name in dirs:
                list_folders.append(os.path.join(root, folder_name).replace("\\","/"))
    return list_folders

def extract_zip(filename, path):
    if filename[-4:] == ".zip":
        logging.debug("[file] extracting %s to %s" % (filename, path) )
        with zipfile.ZipFile(filename, 'r') as zipObj:
            zipObj.extractall(path=path)
            return ls(path, type="folder") + ls(path, type="file")
    elif filename[-7:] == ".tar.gz":
        logging.debug("[file] extracting %s to %s" % (filename, path) )
        file = tarfile.open(filename)
        file.extractall(path) 
        file.close()
        return ls(path, type="folder") + ls(path, type="file")

def mv(source, destination):
    logging.debug("[file] moving %s to %s" % (source, destination))
    os.rename(source, destination)

def cp(source, destination):
    logging.debug("[file] copying %s to %s" % (source, destination))

    if "/" in source:
        filename = source.split("/")[-1]
    elif "\\" in source:
        filename = source.split("\\")[-1]
    else:
        filename = source
    
    shutil.copyfile(source, "C:\\Users\\coni\\AppData\\Roaming\\gally_launcher\\%s" % (filename))

def ls(folder, type="file"):
    list_files = []
    for root, dirs, files in os.walk(folder, topdown=False):
        if root == folder:
            if type == "folder" or type == "all":
                for dir in dirs:
                    list_files.append(dir)
                    
            if type == "file" or type == "all":
                for file in files:
                    list_files.append("%s" % (file))

    return list_files

def get_content_file(file):
    with open(file,'r') as text_file:
        text = text_file.read()
    return text

def command(command, console=True):
    logging.debug("[command] executing %s" % command)
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    if console:
        for stdout_line in iter(popen.stdout.readline, ""):
            print(stdout_line.replace("\n",""))
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

def set_path(path=None):
    logging.debug("[setx] setting path : %s" % path)

    if os.environ["path"][-1] == ";":
        delim = ""
    else:
        delim = ";"
        
    if path not in os.environ["path"]:
        command("setx path \"%s%s%s\"" % (os.environ["path"], delim, path))
    logging.debug("[setx] specified path already in path")