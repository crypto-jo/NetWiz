import queue
import threading
import os
import urllib.error
import urllib.request



threads = 10

target = "http://www..com"
directory = "./dir/" # local install directory of cms
filters = [".jpg", ".gif", ".png", ".css"]

os.chdir(directory)

web_paths = queue.Queue()

for dirpath, dirnames, filenames in os.walk("."):
    for f in filenames:
        remote_path = os.path.join(dirpath, f) # build path to file
        if remote_path.startswith("."):
            remote_path = remote_path[1:] # remove leading "."
        if os.path.splitext(f)[1] not in filters:
            web_paths.put(remote_path)

def test_remote():
    while not web_paths.empty():
        path = web_paths.get() # get item from queue
        url = "{0}{1}".format(target, path) # build query url

        try:
            response = urllib.request.urlopen(url)
            content = response.read()

            print("[{0} ==> {1}".format(response.code, path))
        except urllib.error as error:
            print("Failed {1}", error.code)

for i in range(0, threads):
    print("Spawning threads: {0}".format(i))
    t = threading.Thread(target=test_remote)
    t.start()