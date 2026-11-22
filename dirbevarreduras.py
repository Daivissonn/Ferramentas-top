#vamos criar um script que ele faz uma varredura de portas e que ele me retorna se a porta esta aberta ou fechada, e tambem o status code da porta.

import socket #serve para criar uma conexão com a porta e verificar se ela esta aberta ou fechada.
import requests #serve para fazer uma requisição HTTP e verificar o status code da porta.

url = "https://example.com"
response = requests.get(url)
print(response.status_code)

def scan_ports(host, ports, self):
    self.host = host
    self.ports = ports

    for port in ports:
        if ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#o sock é o objeto que representa a conexão com a porta tipo uma variavel que vai armazenar a conexão com a porta, e o socket.AF_INET é o tipo de conexão que vai ser usada, no caso é uma conexão TCP/IP, e o socket.SOCK_STREAM é o tipo de socket que vai ser usado, no caso é um socket do tipo stream que é usado para conexões TCP.
#socket.socket serve para criar uma conexão com a porta ou seja, ele cria um socket que é um ponto de comunicação entre o cliente e o servidor.
#socket.AF_INET serve para definir o tipo de conexão que vai ser usada, no caso é uma conexão TCP/IP.
#socket.SOCK_STREAM serve para definir o tipo de socket que vai ser usado, no caso é um socket do tipo stream que é usado para conexões TCP.

            sock.settimeout(1) #define um tempo limite para a conexão, de 1 segundo, caso a conexão demore mais que isso, ele vai considerar que a porta esta fechada.
            result = sock.connect_ex((host, port)) #tenta conectar na porta
            if result == 0: #se a conexão for bem sucedida
                print(f"Port {port} is open")
            else: #se a conexão falhar
                print(f"Port {port} is closed")
            sock.close() #fecha a conexão

print("Scanning ports...")

print("Enter the host to scan: ")
host = input() #pega o host que o usuario quer escanear
print("Enter the ports to scan (comma separated): ")
ports_input = input() #pega as portas que o usuario quer escanear
ports = [int(port.strip()) for port in ports_input.split(",")] #transforma a string de portas em uma lista de inteiros

print(f"Scanning {host} on ports: {ports}")
    