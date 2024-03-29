# To be used paired with my_sshRcmd.py
# NOTE: this is used to emulate the ssh server on Windows and here the roles
# of the client and the server are reversed: the server is the one who sends the
# command to the client.

import socket
import paramiko
import threading
import sys

# using the server host key from the Paramiko demo files
host_key = paramiko.RSAKey(filename='test_rsa.key')

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == 'root' and password == "toor":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

server = sys.argv[1]
ssh_port = int(sys.argv[2])
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((server, ssh_port))
    sock.listen(100)
    print("[+] Listening for connection...")
    client, addr = sock.accept()
except Exception as e:
    print("[-] Listen failed: " + str(e))
    sys.exit(1)
print("[+] Got a connection!")

try:
    mySession = paramiko.Transport(client)
    mySession.add_server_key(host_key)
    server = Server()
    try:
        mySession.start_server(server=server)
    except paramiko.SSHException as x:
        print("[-] SSH negotiation failed.")
    chan = mySession.accept(20)
    print("[+] Authenticated!")
    print(chan.recv(1024))
    chan.send("Welcome to my_ssh!")
    while True:
        try:
            command = input("Enter command: ").strip("\n")
            if command != "exit":
                chan.send(command)
                print(chan.recv(1024).decode(errors="ignore") + "\n")
            else:
                chan.send("exit")
                print("Exiting...")
                mySession.close()
                raise Exception("exit")
        except KeyboardInterrupt as e:
            mySession.close()
except Exception as e:
    print("[-] Caught exception: " + str(e))
    try:
        mySession.close()
    except:
        pass
    sys.exit(1)