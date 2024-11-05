import ipaddress

import requests
import socket
import nmap
import netifaces as ni

working_ports = [18965, 21761, 50002, 27815]
host, port = 0, 0
s_host, s_port = None, None

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def find_active_servers():
    for port in working_ports:
        s = check_server(port)
        if is_valid_ip(s):
            print(requests.get(url=f"http://{s}:{port}/ping").text)
            s_host = s
            s_port = port
            return s
    return 0, 0

def check_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(5)
    message = 'GET IP no_key'
    sock.sendto(message.encode('utf-8'), ('255.255.255.255', port))
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            sock.close()
            return data.decode('utf-8')
    except socket.timeout:
        sock.close()
        return "Failed"