import requests
import socket

working_ports = ['18965', '09761', '5000', '27815']
host, port = 0, 0
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

def find_active_servers():
    active_servers = []
    for port in working_ports:
        try:
            response = requests.get(f"http://{local_ip}:{port}/ping")
            if response.ok:
                host, port = local_ip, port
                return local_ip, port
        except requests.exceptions.RequestException as e:
            print(f"Port {port} is not active: {e}")
    return 0, 0