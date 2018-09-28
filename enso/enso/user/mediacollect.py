import os
import re
import time
import shutil
import requests

def get_utorrent_inprogress_items(host, port, user, password):
    """Returns list of files and directories of the jobs being currently downloaded by uTorrent.
    Will remove any finished downloads from uTorrent job list."""

    UTORRENT_URL = 'http://%s:%s/gui/' % (host, port)
    UTORRENT_URL_TOKEN = '%stoken.html' % UTORRENT_URL
    REGEX_UTORRENT_TOKEN = r'<div[^>]*id=[\"\']token[\"\'][^>]*>([^<]*)</div>'
    unmovable_items = []
    unmovable_dirs = []
    auth = requests.auth.HTTPBasicAuth(user, password)
    r = requests.get(UTORRENT_URL_TOKEN, auth=auth)
    token = re.search(REGEX_UTORRENT_TOKEN, r.text).group(1)
    guid = r.cookies['GUID']
    cookies = dict(GUID=guid)

    def torget(params):
        return requests.get(UTORRENT_URL + "?token=" + token + params, auth=auth, cookies=cookies)

    #t[0], t[4], t[26]
    torrents = torget("&list=1").json()

    for t in torrents["torrents"]:
        if (t[4] != 1000):
            unmovable_dirs = unmovable_dirs + [t[26]]
            files = torget("&action=getfiles&hash=" + t[0]).json()["files"][1]
            for f in files:
                unmovable_items = unmovable_items + [os.path.join(t[26], f[0])]
        else:
            torget("&action=remove&hash=" + t[0])
    return unmovable_items + unmovable_dirs


# The function is useful to collect wanted files (for example, movies of the size not less than chosen)
# from a large littery torrent dump without keeping hierarchy.
# All unwanted movable files are placed into the directory named 'remnants.<some number>' under the destination.
# Arguments:
#   source - source directory
#   destination - destination directory
#   wanted - function that determines if a path passed as a parameter is wanted
#   unmovable - function that determines if a path passed as a parameter is unmovable
#   add - add files to the destination when True, or rename the existing destination and create new one when False
def collect_media(source, destination, wanted, unmovable, add=True):
    def collect(root):
        result = []

        for root, dirs, files in os.walk(root):
            #path = root.split(os.sep)
            for file in files:
                with_path = os.path.join(root, file)
                if wanted(with_path):
                    result = result + [[with_path, file]]
        return result

    if not add:
        if os.path.exists(destination) and os.listdir(destination):
            new_destination = destination + "." + str(int(time.time()))
            shutil.move(destination, new_destination)
            os.mkdir(destination)

    for [with_path, name] in collect(source):
        new_name = os.path.join(destination, name)
        if not os.path.exists(new_name):
            try:
                shutil.move(with_path, destination)
            except Exception as e:
                print(e)

    if os.listdir(source):
        remnants = os.path.join(destination, "remnants" + "." + str(int(time.time())))
        if not os.path.exists(remnants):
            os.mkdir(remnants)
        for i in os.listdir(source):
            item = os.path.join(source, i)
            if not unmovable(item):
                shutil.move(item, remnants)
