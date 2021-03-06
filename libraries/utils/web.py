import urllib.request
import urllib.parse
import os
import sys
import libraries.utils._file as _file
import uuid
import logging
import json

def download(url, filename, exist_ignore=False, retry=False):
    if exist_ignore:
        is_file = False
    else:
        is_file = os.path.isfile(filename)

    delim = None
    if "/" in filename:
        delim = "/"
    elif "\\" in filename:
        delim = "\\"

    if delim:
        _file.mkdir_recurcive(delim.join(filename.split(delim)[:-1]))

    url_fixed = urllib.parse.quote(url).replace("%3A",":")

    if retry:
        if "%20" in url_fixed:
            url_fixed = url_fixed.replace("%20","%2B")
        else:
            url_fixed = url_fixed.replace("%2B","%20")

    try:
        if is_file == False:
            logging.debug("[web] download %s from %s" % (filename, url_fixed))
            urllib.request.urlretrieve(url_fixed, filename)
        else:
            logging.debug("[web] %s already exist (from %s)" % (filename, url_fixed))

        return filename
    except KeyboardInterrupt:
        sys.exit()
    except:
        logging.debug("[web] can't download %s from %s" % (filename, url_fixed))
        if retry == False:
            return download(url, filename, retry=True)
        else:
            return False

def get_uuid(username=None):
    if username != None:
        req = get("https://api.mojang.com/users/profiles/minecraft/%s" % username)
        if req:
            return json.loads(req)["id"]

    uuid_ = str(uuid.uuid1()).replace("-","")
    logging.debug("[web] generate uuid : %s" % uuid_)
    return uuid_

def get(url):
    try:
        response = urllib.request.urlopen(url)
    except KeyboardInterrupt:
        sys.exit()
    except:
        logging.warning("[web] FAILED to request %s" % url)
        return False

    return response.read().decode()

def post(url, data, headers=None):
        data = json.dumps(data).encode()
        req =  urllib.request.Request(url)
        for i in headers:
            req.add_header(i, headers[i])
        resp = urllib.request.urlopen(
            req,
            data=data
            )
        return resp