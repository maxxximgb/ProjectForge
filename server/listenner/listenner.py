import os

from flask import Flask, jsonify, request
from threading import Thread
import socket
import sqlite3

app, port, connection, cursor = None, None, None, None
newpr = ''' CREATE TABLE IF NOT EXISTS {name} ( ID INTEGER PRIMARY KEY AUTOINCREMENT, {name} TEXT NOT NULL , {maintainer} TEXT NOT NULL) '''


def run_app(app, port):
    create_routes(app)
    thr = Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    thr.start()
    print('0.0.0.0', port)
    return 0

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



