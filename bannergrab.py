import socket

ip = input("Enter the IP address: ")
port = int(input("Enter the port number: "))

meusoquete = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
meusoquete.connect((ip, port))
banner = meusoquete.recv(1024)