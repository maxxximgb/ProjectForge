import logging
import os
import socket
import time
import netifaces
import requests
from flask import Flask, jsonify, request
from threading import Thread
import sqlite3
from flask import g

app, port, connection, cursor, qapp = None, None, None, None, None
pos2lvl = {"Директор": 4,
           "Менеджер": 3,
           "Рабочий": 2,
           "Посетитель": 1}
database = "database/database.sqlite"
user_ip_by_pos = {
    "Директор": [],
    "Менеджер": [],
    "Рабочий": [],
    "Посетитель": []
}


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(database)
    return db


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


def share(pyqt_app):
    global qapp
    qapp = pyqt_app


def ForceCreateProject(username, projectname, status):
    with app.app_context():
        connection = get_db()
        cursor = connection.cursor()
        logging.info(f"Пользователь {username} создает проект.")
        cursor.execute('''
            INSERT INTO Projects (ProjectName, CreatorID, Status)
            VALUES (?, ?, ?)
        ''', (projectname, username, status))
        connection.commit()

def get_waiting_directors():
    with app.app_context():
        conn = get_db()
        cursor=conn.cursor()
        cursor.execute('''
            SELECT * FROM Users
            WHERE Position = 'Директор' AND Status = 'waiting'
        ''')
        waitingdirectors = cursor.fetchall()
    return waitingdirectors


def create_routes(app):
    @app.route("/userstatus", methods=["GET"])
    def get_userstatus():
        username = request.json.get('name')
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT Status, Position FROM Users WHERE SystemLogin = ?
        ''', (username,))

        status, position = cursor.fetchone()
        logging.info(f"{username} статус отправлен: {status[0]}")
        if status == 'waiting':
            return status[0], 403
        elif status == 'approved':
            global user_ip_by_pos
            logging.info(f"{position} {username} добавлен в список IP адресов")
            user_ip_by_pos[position].append(request.remote_addr)
            return status[0], 200
        else:
            return 'Registration Denied', 404

    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        ip = request.remote_addr
        pos = request.json.get("position")
        global user_ip_by_pos
        user_ip_by_pos[pos].remove(ip)
        logging.info(f"{pos} с IPv4 адресом {ip} был удален.")

    @app.route("/authuser", methods=["POST"])
    def auth_user():
        data = request.json
        password = data.get('password')
        login = data.get('login')
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT Password, Status, Position FROM Users WHERE SystemLogin = ?
        ''', (login,))
        try:
            pwd, status, position = cursor.fetchone()
        except:
            return "Not found", 404
        if pwd == password and status != 'waiting':
            return position, 200
        elif pwd != password:
            return "Incorrect password", 403
        elif status == "waiting":
            return "You are not approved", 403


    @app.route("/newuser", methods=["POST"])
    def reg_user():
        global pos2lvl
        data = request.json
        username = data.get('login')
        userpos = data.get('pos')
        userpassword = data.get('password')
        name = data.get('name')
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''
                    SELECT COUNT(*) FROM Users WHERE SystemLogin = ?
                ''', (username,))
        is_registered = int(cursor.fetchone()[0]) > 0
        if is_registered: return "User id already registered", 403
        cursor.execute('''
            INSERT INTO Users (Name, Password, Status, Position, SystemLogin)
            VALUES (?, ?, 'waiting', ?, ?)
        ''', (name, userpassword, userpos, username))
        connection.commit()


        if pos2lvl[userpos] == 4:
            logging.info(f"Пользователь {username} запрашивает регистрацию как директор.")
            qapp.RequestRegister4Director()
            logging.info(f"Пользователь {username} успешно регистрируется как директор.")
        elif pos2lvl[userpos] == 2 or pos2lvl[userpos] == 3:
            #TODO запрос регистрации у директора и менеджера
            pass
        return "WaitForStatus", 200

    @app.route("/ping", methods=["GET"])
    def ping():
        userpos = request.json.get('userpos')
        return "OK"

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

def accept_director(login):
    global app
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Users SET Status = ? WHERE SystemLogin = ?
        ''', ('approved', login))
        conn.commit()

def decline_director(login):
    global app
    with app.app_context():
        connection = get_db()
        cursor = connection.cursor()

        cursor.execute('''
        SELECT UserID FROM Users WHERE SystemLogin = ?
        ''', (login,))

        ID = cursor.fetchone()[0]

        cursor.execute('''
        DELETE FROM UserProjects
        WHERE UserID = ?
        ''', (ID,))

        cursor.execute('''
        DELETE FROM Users
        WHERE UserID = ?
        ''', (ID,))

        connection.commit()

def create_app():
    global host, port, app, cursor, connection
    if not os.path.exists("database"):
        os.mkdir("database")
    app = Flask("ServerListenner")
    with app.app_context():
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID       INTEGER PRIMARY KEY AUTOINCREMENT,
            Name         TEXT    NOT NULL,
            Password     TEXT    NOT NULL,
            Status       TEXT    NOT NULL,
            Position     TEXT    NOT NULL,
            SystemLogin  TEXT    NOT NULL,
            UserProjects         REFERENCES UserProjects (UserID) 
        );
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Projects (
            ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectName TEXT NOT NULL,
            CreatorID INTEGER NOT NULL,
            Status TEXT NOT NULL,
            FOREIGN KEY (CreatorID) REFERENCES Users(UserID)
        );
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserProjects (
            UserID INTEGER,
            ProjectID INTEGER,
            PRIMARY KEY (UserID, ProjectID),
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
        )
        ''')
        connection.commit()

    return app
