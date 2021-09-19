import json
import os
import libraries.utils.web as web
import libraries.utils._file as _file
import re
import logging

class parse_minecraft_version:

    def __init__(self, system=None,version=None, minecraft_root=".", libraries_root="libraries", binary_root="bin", assets_root="assets", versions_root="versions", username=None, inherit=False):
        
        self.system = None
        if system == None:
            self.system = _file.get_os()
        else:
            if system == "windows" or system == "linux":
                self.system = system
            else:
                self.system = _file.get_os()

        self.minecraft_root = minecraft_root

        self.assets_root = assets_root
        self.versions_root = versions_root
        self.libraries_root = libraries_root
        self.binary_root = binary_root
        self.skin = None
        
        self.inherit = inherit
        self.version = version
        self.username = username
        
        if version:
            self.load_version(version)

    def load_version(self, version=None):
        logging.debug("loading %s" % version)
        if version:
            self.version = version
            json_file = open("%s/%s/%s/%s.json" % (self.minecraft_root, self.versions_root, self.version, self.version),"r")
        else:
            logging.error("%s don't exist" % version)
            return None

        self.json_loaded = json.load(json_file)
        self.lastest_lwjgl_version = None
    
        if "inheritsFrom" in self.json_loaded:
            self.inheritsFrom = self.json_loaded["inheritsFrom"]
            self.inheritsFrom_parse = parse_minecraft_version(version=self.inheritsFrom,minecraft_root=self.minecraft_root, libraries_root=self.libraries_root, binary_root=self.binary_root,assets_root=self.assets_root,versions_root=self.versions_root, username=self.username, inherit=True)
        else:
            self.inheritsFrom = False
        
        self.mainclass = self.get_mainclass()
        self.version_type = self.get_versionType()
        self.lastest_lwjgl_version = self.get_lastest_lwjgl_version()
        self.assetIndex = self.get_assetIndex()
        self.binary_path = None



    def get_lastest_lwjgl_version(self):
        
        if self.inheritsFrom:
            lastest_inherits = self.inheritsFrom_parse.lastest_lwjgl_version

        lwjgl_version = []
        if "libraries" in self.json_loaded:
            for i in self.json_loaded["libraries"]:
                if "lwjgl" in i["name"] and i["name"].split(":")[-1] not in lwjgl_version:
                    lwjgl_version.append(i["name"].split(":")[-1])

        sorted(lwjgl_version)
        if lwjgl_version:
            reggex = re.search(r"(?P<version>[0-9]\.[0-9]\.[0-9])(-(?P<type>.+)-(?P<build>.+)\\)?",lwjgl_version[-1])
            logging.debug("getting the lastest version of lwjgl : %s " % reggex.group("version"))
            return reggex.group("version")
        else:
            logging.debug("getting the lastest version of lwjgl : %s " % lastest_inherits)
            return lastest_inherits

    def get_classpath(self):

        if os.path.isfile("debug/classpath"):
           classpath_file = open("classpath",'r')
           return classpath_file.read()
        
        if self.minecraft_root == ".":
            minecraft_root = os.getcwd()
        else:
            if self.minecraft_root[:3] == "C:\\" or self.minecraft_root[0] == "/":
                minecraft_root = self.minecraft_root
            else:
                minecraft_root = "%s/%s" % (os.getcwd(), self.minecraft_root)

        
        if self.inheritsFrom:
            classpath_inherits = self.inheritsFrom_parse.get_classpath()

        libraries = self.json_loaded["libraries"]

        libraries_path = "%s/%s" % (minecraft_root, self.libraries_root)
        
        classpath = []

        for librarie in libraries:

            if "lwjgl" in librarie["name"]:
                librarie_lwjgl_version = re.search(r"(?P<version>[0-9]\.[0-9]\.[0-9])(-(?P<type>.+)-(?P<build>.+)\\)?", librarie["name"].split(":")[-1][1])
                
                if librarie_lwjgl_version:
                    if librarie_lwjgl_version.group("version") != self.lastest_lwjgl_version:
                        continue

            librarie_path = ""
            for i in range(len(librarie["name"].split(":"))):
                if i <= 1:
                    librarie_path += "%s/" % librarie["name"].split(":")[i].replace(".","/")
                else:
                    librarie_path += "%s" % librarie["name"].split(":")[i]

            libraries_files = _file.ls("%s/%s" % (libraries_path, librarie_path))
            
            for i in libraries_files:
                classpath_file = "%s/%s" % (librarie_path, i)
                if classpath_file not in classpath:
                    classpath.append(classpath_file)

        for i in range(len(classpath)):
            classpath[i] = "./%s/%s" % (self.libraries_root, classpath[i])

        classpath.append(self.get_jar())
            
        if self.inheritsFrom:
            classpath.append(classpath_inherits)

        for i in range(len(classpath)-1):
            if classpath[i] == None:
                classpath.pop(i)
        
        logging.debug("getting classpath")
        if self.system == "windows":
            return ";".join(classpath)
        else:
            return ":".join(classpath)

    def set_skin(self, username):
        self.skin = username

    def download_server(self, path="."):
        exist = False
        if "downloads" in self.json_loaded:
            if "server" in self.json_loaded["downloads"]:
                url = self.json_loaded["downloads"]["server"]["url"]
                exist = web.download(url, "%s/server.jar" % path)
        return exist
        
    
    def get_jar(self):

        if self.minecraft_root == ".":
            minecraft_root = os.getcwd()
        else:
            if self.minecraft_root[:3] == "C:\\" or self.minecraft_root[0] == "/":
                minecraft_root = self.minecraft_root
            else:
                minecraft_root = "%s/%s" % (os.getcwd(), self.minecraft_root)

        default_jar = "./%s/%s/%s.jar" % (self.versions_root, self.version, self.version)
        default_jar_fullpath = "%s/%s/%s/%s.jar" % (minecraft_root, self.versions_root, self.version, self.version)

        if os.path.isfile(default_jar_fullpath):
            logging.debug("getting jar path %s" % default_jar)
            return default_jar

        if self.inheritsFrom:
            jar = self.inheritsFrom_parse.get_jar()
            return jar
        
    def download_libraries(self):
        logging.debug("prepare the downloading of libraries")
        
        if self.inheritsFrom:
            self.inheritsFrom_parse.download_libraries()

        to_download = []

        for i in self.json_loaded["libraries"]:
            librarie_name = None
            librarie_url = None

            if "downloads" not in i:
                if "name" in i:
                    librarie_name = i["name"]
                    splitted_name = librarie_name.split(":")
                    librarie_filename = "%s-%s.jar" % (splitted_name[-2], splitted_name[-1])

                    librarie_path = ""
                    for j in range(len(splitted_name)):
                        if j < len(splitted_name)-1:
                            librarie_path += "%s/" % splitted_name[j].replace(".","/")
                    else:
                        librarie_path += "%s" % (splitted_name[j])

                if "url" in i:
                    if librarie_name:
                        librarie_url = "%s/%s/%s" % (i["url"], librarie_path, librarie_filename)

                if librarie_url:

                    download_path = "/".join((self.minecraft_root, self.libraries_root, librarie_path, librarie_filename))
                    to_download.append((librarie_url, download_path))

                continue

            librairie = i["downloads"]
            librarie_name = i["name"]

            if "lwjgl" in librarie_name:
                librarie_lwjgl_version = re.search(r"(?P<version>[0-9]\.[0-9]\.[0-9])(-(?P<type>.+)-(?P<build>.+)\\)?", librarie_name.split(":")[-1])
                
                if librarie_lwjgl_version:
                    if librarie_lwjgl_version.group("version") != self.lastest_lwjgl_version:
                        continue

            if "classifiers" in librairie:
                if "natives-%s" % self.system in librairie["classifiers"]:
                    native_url = librairie["classifiers"]["natives-%s" % self.system]["url"]
                    native_path = librairie["classifiers"]["natives-%s" % self.system]["path"]

                    if "/" in native_path:
                        delim = "/"
                    elif "\\" in native_path:
                        delim = "\\"

                    native_path = delim.join((self.minecraft_root, self.libraries_root, native_path))
                    to_download.append((native_url, native_path))

            if "artifact" in librairie:
                url = librairie["artifact"]["url"]
                full_path = librairie["artifact"]["path"]

                if "/" in full_path:
                    delim = "/"
                elif "\\" in full_path:
                    delim = "\\"

                full_path = delim.join((self.minecraft_root, self.libraries_root, full_path))
                to_download.append((url, full_path))

        for librarie_ in to_download:
            should_download = False
            if "lwjgl" in librarie_[1]:
                lwjgl_regex = re.search(r"(?P<version>[0-9]\.[0-9]\.[0-9])(-(?P<type>.+)-(?P<build>.+)\\)?", librarie_[1])
                
                if lwjgl_regex:
                    if lwjgl_regex.group("version") == self.lastest_lwjgl_version:
                        should_download = True
                elif lwjgl_regex == None:
                    should_download = True
            else:
                should_download = True

            if should_download:
                web.download(librarie_[0], librarie_[1])
        
        return True

    def download_binary(self):
        if self.minecraft_root == ".":
            minecraft_root = os.getcwd()
        else:
            if self.minecraft_root[:3] == "C:\\" or self.minecraft_root[0] == "/":
                minecraft_root = self.minecraft_root
            else:
                minecraft_root = "%s/%s" % (os.getcwd(), self.minecraft_root)

        logging.debug("prepare the downloading of binaries")
        binary_url = []

        if self.lastest_lwjgl_version.split(".")[0] == "3":
            
            if os.path.isdir("%s/%s" % (self.binary_root, self.lastest_lwjgl_version)) == False:
                base_url_x64 = "https://build.lwjgl.org/release/%s/%s/x64" % (self.lastest_lwjgl_version, self.system)
                base_url_x86 = "https://build.lwjgl.org/release/%s/windows/x86" % self.lastest_lwjgl_version

                if self.system == "windows":

                    binary_url.append("%s/%s" % (base_url_x64, "glfw.dll"))
                    binary_url.append("%s/%s" % (base_url_x64, "jemalloc.dll"))
                    binary_url.append("%s/%s" % (base_url_x64, "lwjgl.dll"))
                    binary_url.append("%s/%s" % (base_url_x64, "lwjgl_opengl.dll"))
                    binary_url.append("%s/%s" % (base_url_x64, "lwjgl_stb.dll"))
                    binary_url.append("%s/%s" % (base_url_x64, "OpenAL.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "glfw32.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "jemalloc32.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "lwjgl_opengl32.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "lwjgl_stb32.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "lwjgl32.dll"))
                    binary_url.append("%s/%s" % (base_url_x86, "OpenAL32.dll"))

                elif self.system == "linux":
                    # binary_url.append("%s/%s" % (base_url_x64, "libfliteWrapper.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "libglfw.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "libglfw_wayland.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "libjemalloc.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "liblwjgl.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "liblwjgl_opengl.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "liblwjgl_stb.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "libopenal.so"))
                    binary_url.append("%s/%s" % (base_url_x64, "liblwjgl_tinyfd.so"))
            else:
                 return "%s/%s/%s/" % (minecraft_root, self.binary_root, self.lastest_lwjgl_version)

        elif self.lastest_lwjgl_version.split(".")[0] == "2":
            if os.path.isdir("%s/%s/%s" % (minecraft_root, self.binary_root, self.lastest_lwjgl_version)) == False:
                if self.lastest_lwjgl_version == "2.9.4":
                    zip_url = "http://ci.newdawnsoftware.com/job/LWJGL-git-dist/lastBuild/artifact/dist/lwjgl-2.9.4.zip"
                else:
                    zip_url = "https://versaweb.dl.sourceforge.net/project/java-game-lib/Official Releases/LWJGL %s/lwjgl-%s.zip" % (self.lastest_lwjgl_version, self.lastest_lwjgl_version)
            else:
                return "%s/%s/%s/native/%s/" % (minecraft_root, self.binary_root, self.lastest_lwjgl_version, self.system)
        
        temp_path = "%s/.temp" % self.minecraft_root
        zip_filename = "%s/%s.zip" % (temp_path, self.lastest_lwjgl_version)

        if binary_url:
            binary_full_path = "%s/%s/" % (self.binary_root, self.lastest_lwjgl_version)
            for url in binary_url:
                binary_filename = url.split("/")[-1]
                binary_file = "%s/%s/%s" % (self.minecraft_root, binary_full_path, binary_filename)
                web.download(url, binary_file)

        elif zip_url:

            web.download(zip_url, zip_filename)
            if os.path.isfile(zip_filename):
                list_folder_extracted = _file.extract_zip(zip_filename, "%s/%s" % (self.minecraft_root, self.binary_root))
            
                for folder in list_folder_extracted:
                    if folder == "lwjgl-%s" % self.lastest_lwjgl_version:
                        folder = "%s/%s" % (self.binary_root, self.lastest_lwjgl_version)
                        _file.mv("%s/%s/lwjgl-%s" % (self.minecraft_root, self.binary_root, self.lastest_lwjgl_version), "%s/%s" % (self.minecraft_root, folder))

                        binary_full_path = "%s/native/%s/" % (folder, self.system)

        _file.rm_rf(temp_path)

        self.binary_path = binary_full_path

        return binary_full_path

    def get_mainclass(self):
        logging.debug("getting mainclass")

        if os.path.isfile("debug/mainclass"):
            with open("debug/mainclass", "r") as mainclass_file:
                return mainclass_file.read()

        re_version = re.search(r"(?P<version>([0-9]+\.[0-9]+(\.[0-9]+)?))(?P<type>(\-)(.+))?", self.version) 
        if re_version:
            version = re_version.group("version")
            version = int(version.split(".")[1])
            type = re_version.group("type")
        
        if self.inheritsFrom:
            mainclass_inherits = self.inheritsFrom_parse.get_mainclass()
        
        if type:
            if "mainClass" in self.json_loaded:
                return self.json_loaded["mainClass"]
            else:
                return mainclass_inherits

        if version >= 6:
            return "net.minecraft.client.main.Main"
        else:
            return "net.minecraft.client.Minecraft"


    def get_assetIndex(self):
        assetIndex = False

        if self.inheritsFrom:
            assetIndex = self.inheritsFrom_parse.get_assetIndex()
            
        if "assetIndex" in self.json_loaded:
            if "id" in self.json_loaded["assetIndex"]:
                assetIndex = self.json_loaded["assetIndex"]["id"]
        logging.debug("get the asset index : %s" %assetIndex)
        return assetIndex

    def get_versionType(self):

        assetIndex = False
        if self.inheritsFrom:
            assetIndex = self.inheritsFrom_parse.get_versionType()

        if "type" in self.json_loaded:
            assetIndex = self.json_loaded["type"]
        logging.debug("get the version type : %s" % assetIndex)
        return assetIndex

    def download_client(self):
        logging.debug("downloading client for %s" % self.version)
        client_path = "%s/%s/%s" % (self.minecraft_root, self.versions_root, self.version)

        if os.path.isfile("%s/%s.jar" % (client_path, self.version)) == False:
            if "downloads" in self.json_loaded:
                url = self.json_loaded["downloads"]["client"]["url"]
                web.download(url, "%s/%s.jar" % (client_path, self.version))
        else:
            return True

    def download_assets(self):
        logging.debug("download assets..")

        if self.inheritsFrom:
            self.inheritsFrom_parse.download_assets()

        to_download = []
        if "assetIndex" not in self.json_loaded:
            return False

        asset_index_url = self.json_loaded["assetIndex"]["url"]
        asset_index_filename = self.json_loaded["assetIndex"]["id"]
        asset_index_fullpath = "%s/%s/indexes/%s.json" % (self.minecraft_root, self.assets_root, asset_index_filename)

        if "logging" in self.json_loaded:
            config_filename = self.json_loaded["logging"]["client"]["file"]["id"]
            config_url = self.json_loaded["logging"]["client"]["file"]["url"]
            config_fullpath = "%s/%s/log_configs/%s" % (self.minecraft_root, self.assets_root, config_filename)
            to_download.append((config_url, config_fullpath))

        to_download.append((asset_index_url, asset_index_fullpath))

        for asset_indexes in to_download:
            web.download(asset_indexes[0], asset_indexes[1])

        asset_index_file = open(asset_index_fullpath,'r')
        asset_index_json = json.load(asset_index_file)

        for i in asset_index_json["objects"]:
            asset_hash = asset_index_json["objects"][i]["hash"]
            asset_folder = asset_hash[:2]
            web.download("https://resources.download.minecraft.net/%s/%s" % (asset_folder, asset_hash), "%s/%s/objects/%s/%s" % (self.minecraft_root, self.assets_root, asset_folder, asset_hash))

    def get_minecraft_arguments(self, access_token=None, game_directory=None):

        if game_directory == None:
            game_directory = "."
            if os.path.isfile("debug/game_directory"):
                with open("debug/game_directory", "r") as game_dir_file:
                    game_directory = game_dir_file.read()
        
        if access_token == None:
            access_token = "xxxxxxxxxx"
        
        inherits_arguments = None
        if self.inheritsFrom:
            inherits_arguments = self.inheritsFrom_parse.get_minecraft_arguments()
        
        if self.skin:
            username = self.skin
        else:
            username = self.username

        minecraft_arguments = []

        arguments_var = {}
        arguments_var["${auth_player_name}"] = self.username
        arguments_var["${version_name}"] = self.version
        arguments_var["${game_directory}"] = "\"%s\"" % game_directory
        arguments_var["${assets_root}"] = arguments_var["${game_assets}"] = self.assets_root
        arguments_var["${assets_index_name}"] = self.assetIndex
        arguments_var["${auth_uuid}"] = web.get_uuid(username=username)
        arguments_var["${auth_access_token}"] = arguments_var["${auth_session}"] = access_token
        arguments_var["${user_type}"] = "mojang"
        arguments_var["${version_type}"] = self.version_type
        arguments_var["${user_properties}"] = "."

        json_arguments = []
        if "minecraftArguments" in self.json_loaded:
            json_arguments = self.json_loaded["minecraftArguments"].split(" ")
        elif "arguments" in self.json_loaded:
            json_arguments = self.json_loaded["arguments"]["game"]

        for argument in json_arguments:
            if type(argument) == str:
                if argument in arguments_var:
                    minecraft_arguments.append(arguments_var[argument])
                else:
                    minecraft_arguments.append(argument)
                    
        if self.inheritsFrom:
            for i in range(len(inherits_arguments)):
                if inherits_arguments[i]:
                    if "--" == inherits_arguments[i][:2]:
                        if inherits_arguments[i] not in minecraft_arguments:
                            if type(inherits_arguments[i]) == list:
                                minecraft_arguments += inherits_arguments[i]
                            elif type(inherits_arguments[i]) == str:
                                minecraft_arguments.append(inherits_arguments[i])
                            
                            if type(inherits_arguments[i+1]) == list:
                                minecraft_arguments += inherits_arguments[i+1]
                            elif type(inherits_arguments[i+1]) == str:
                                minecraft_arguments.append(inherits_arguments[i+1])
        
        logging.debug("getting minecraft arguments")
        return minecraft_arguments

    def get_java_arguments(self, classpath=None):

        values_temp = []
        values = []

        inherits_arguments = None
        if self.inheritsFrom:
            inherits_arguments = self.inheritsFrom_parse.get_java_arguments(self.get_classpath())

        
        arguments_var = {}
        arguments_var["${launcher_name}"] = "coni_python"
        arguments_var["${launcher_version}"] = "unknown"

        if classpath == None:
            arguments_var["${classpath}"] = self.get_classpath()
        else:
            arguments_var["${classpath}"] = classpath


        
        os.environ["classpath"] = arguments_var["${classpath}"]
        if self.system == "windows":
            arguments_var["${classpath}"] = "\"%classpath%\""
        elif self.system == "linux":
            arguments_var["${classpath}"] = "\"$classpath\""


        if self.binary_path:
            arguments_var["${natives_directory}"] = self.binary_path
        else:
            arguments_var["${natives_directory}"] = self.download_binary()
        
        if "arguments" in self.json_loaded:
            if "jvm" not in self.json_loaded["arguments"]:
                if inherits_arguments:
                    return inherits_arguments
                else:
                    return False
        else:
            values.append("-Djava.library.path=%s" % arguments_var["${natives_directory}"])
            values.append("-cp")
            values.append(arguments_var["${classpath}"])
            return values

        for i in self.json_loaded["arguments"]["jvm"]:
            if type(i) == dict:
                if "name" in i["rules"][0]["os"]:
                    if i["rules"][0]["os"]["name"] == "windows":
                        values_temp.append(i["value"])
            else:
                values_temp.append(i.replace(" ",""))
        
        for value in values_temp:
            is_in_value = False
            for argument in arguments_var:
                if argument in value:
                    is_in_value = True
                    if type(value) == list:
                            values += value.replace(argument, arguments_var[argument])
                    elif type(value) == str:
                        if argument in value:
                            values.append(value.replace(argument, arguments_var[argument]))

            if is_in_value == False:
                if type(value) == list:
                    values += value
                elif type(value) == str:
                    values.append(value)
        
        to_remove = []
        for i in range(len(values)-1):
            if " " in values[i]:
                to_remove.append(i)
        
        for i in to_remove:
            values.pop(i)


        if inherits_arguments:
            values += inherits_arguments
        logging.debug("getting java arguments")
        logging.debug("classpath : %s" % os.environ["classpath"])
        return values

    def get_default_java_arguments(self):
        default_java_arg = []

        default_java_arg.append("-Xmx2G") 
        default_java_arg.append("-XX:+UnlockExperimentalVMOptions") 
        default_java_arg.append("-XX:+UseG1GC -XX:G1NewSizePercent=20") 
        default_java_arg.append("-XX:G1ReservePercent=20")
        default_java_arg.append("-XX:MaxGCPauseMillis=50")
        default_java_arg.append("-XX:G1HeapRegionSize=32M")

        logging.debug("getting default java arguments : %s" % ' '.join(default_java_arg))

        return default_java_arg
    
    def set_username(self, username):
        logging.debug("setting username : %s" % username)
        self.username = username
        return self.username