import socket
import sys

for porta in range(1, 65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex((sys.argv[1], porta)) == 0:
        print(f"Porta {porta} está aberta")
    sock.close()