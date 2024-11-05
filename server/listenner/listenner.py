import os
import socket
import time
import netifaces
from flask import Flask, jsonify, request
from threading import Thread
import sqlite3

app, port, connection, cursor = None, None, None, None
newpr = ''' CREATE TABLE IF NOT EXISTS {name} ( ID INTEGER PRIMARY KEY AUTOINCREMENT, {name} TEXT NOT NULL , {maintainer} TEXT NOT NULL) '''

def get_local_ip():
    try:
        interfaces = netifaces.interfaces()
        for iface in interfaces:
            if_addresses = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in if_addresses:
                for link in if_addresses[netifaces.AF_INET]:
                    ip = link['addr']
                    if ip != "127.0.0.1":
                        return ip
    except Exception as e:
        return str(e)


def run_app(app, portik):
    global port
    port = portik
    create_routes(app)
    app_thr = Thread(target=lambda: app.run(host='0.0.0.0', port=portik))
    resp_thr = Thread(target=listen_and_respond)
    app_thr.start()
    resp_thr.start()
    return 0

def listen_and_respond():
    global port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', int(port)))
    response = str(get_local_ip())

    while True:
        time.sleep(1)
        data, addr = sock.recvfrom(1024)
        if data.decode('utf-8') == 'GET IP no_key':
            sock.sendto(response.encode('utf-8'), addr)


def create_routes(app):
    @app.route("/newproject", methods=["POST"])
    def create_project():
        data = request.json
        name = data.get("name")
        maintainer = data.get("maintainer")
        if not name or not maintainer:
            return jsonify(message="Отправлены неверные данные"), 403
        cmd = newpr.format(name = name, maintainer = maintainer)
        cursor.execute(cmd)
        connection.commit(cursor)
        return jsonify(message="Таблица '{name}' успешно создана.".format(name)), 200
    
    @app.route("/authuser", methods = ["POST"])
    def auth_user():
        data = request.json
        #TODO авторизировать пользователя
    
    @app.route("/newuser", methods = ["POST"])
    def reg_user():
        data = request.json
        #TODO зарегать пользователя

    @app.route("/ping", methods=["GET"])
    def ping():
        return "OK"

def create_app():
    global host, port, app, cursor, connection
    if not os.path.exists("database"):
        os.mkdir("database")
    connection = sqlite3.connect("database/database.sqlite")
    cursor = connection.cursor()
    app = Flask("ServerListenner")
    return app


