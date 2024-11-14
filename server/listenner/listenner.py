import base64
import json
import logging
import os
import socket
import time
import netifaces
from flask import Flask, jsonify, request, Response, send_file
from threading import Thread
import sqlite3
from flask import g

app, port, connection, cursor, qapp = None, None, None, None, None
all_users_updating = False
pos2lvl = {"Директор": 4,
           "Менеджер": 3,
           "Рабочий": 2,
           "Посетитель": 1}
database = "database/database.sqlite"
online_users_by_pos = {
    "Директор": [],
    "Менеджер": [],
    "Рабочий": [],
    "Посетитель": []
}
all_users_by_pos = {
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
        cursor = conn.cursor()
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
            SELECT Status, Position, Name FROM Users WHERE SystemLogin = ?
        ''', (username,))

        status, position, name = cursor.fetchone()
        logging.info(f"{username} статус отправлен: {status}")
        if status == 'waiting':
            return status, 403
        elif status == 'approved':
            global online_users_by_pos
            userdata = {"name": name, "ip": request.remote_addr, "status": status}
            logging.info(f"{position} {username} добавлен в список IP адресов")
            online_users_by_pos[position].append(userdata)
            fetch_all_users()
            return position, 200
        else:
            return 'Registration Denied', 404

    @app.route("/pendingProjects", methods=["GET"])
    def pendingProjects():
        cursor = get_db().cursor()
        cursor.execute('''SELECT * FROM Projects WHERE Status = ?''', ('waiting',))
        pr = cursor.fetchall()
        if not pr:
            return 404

        return jsonify(pr)

    @app.route("/getup", methods=["GET"])
    def getup():
        login = request.json.get("login")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                Projects.ProjectID,
                Projects.ProjectName,
                Projects.ProjectDesc,
                Projects.CreatorID,
                Projects.Status
            FROM 
                Projects
            JOIN 
                UserProjects ON Projects.ProjectID = UserProjects.ProjectID
            JOIN 
                Users ON UserProjects.UserID = Users.UserID
            WHERE 
                Users.SystemLogin = ?;
        ''', (login,))
        projects = cursor.fetchall()
        if projects:
            return jsonify(projects), 200
        else:
            return "No projects", 404

    @app.route('/projectimg/<name>', methods=['GET'])
    def getProjectImage(name):
        return send_file(f"projects/{name}/{name}.png", mimetype='image/png')

    @app.route("/GetProjectInfo", methods=["GET"])
    def get_project_info():
        id = request.json.get("id")
        cursor = get_db().cursor()
        cursor.execute('''SELECT * FROM Projects WHERE ProjectID = ?''', (id,))
        project = cursor.fetchone()
        print(project)
        if project is None:
            return jsonify(project), 404
        return jsonify(project), 200

    @app.route("/userid", methods=["GET"])
    def userid():
        cursor = get_db().cursor()
        cursor.execute("SELECT Name, Status, Position, SystemLogin FROM Users WHERE UserID = ?;",
                       (request.json.get("id"),))
        data = cursor.fetchone()
        return jsonify(data)

    @app.route("/newproject", methods=["POST"])
    def add_project():
        data = request.json
        login = data.get("login")
        name = data.get("name")
        desc = data.get("desc")
        participants = data.get("participants")
        image = base64.b64decode(data.get("image"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM Projects WHERE ProjectName = ?
        ''', (name,))
        project_count = cursor.fetchone()[0]

        if project_count > 0:
            return "Already Exists", 400
        os.mkdir(f"projects/{name}")
        with open(f"projects/{name}/{name}.png", "wb") as f:
            f.write(image)
        cursor.execute('''
            SELECT UserID, Position FROM Users WHERE SystemLogin = ?
        ''', (login,))
        userid, position = cursor.fetchone()
        if pos2lvl[position] > 2:
            cursor.execute('''
                INSERT INTO Projects (ProjectName, ProjectDesc, CreatorID, Status)
                VALUES (?, ?, ?, ?)
            ''', (name, desc, userid, 'approved'))
        else:
            cursor.execute('''
                INSERT INTO Projects (ProjectName, ProjectDesc, CreatorID, Status)
                VALUES (?, ?, ?, ?)
            ''', (name, desc, userid, 'waiting'))
        conn.commit()
        cursor.execute('''SELECT ProjectID From Projects WHERE ProjectName = ?''', (name,))
        project_id = cursor.fetchone()[0]
        participants.append(userid)
        for user_id in participants:
            cursor.execute('''
                INSERT INTO UserProjects (UserID, ProjectID)
                VALUES (?, ?)
            ''', (user_id, project_id))
        conn.commit()
        return "Created", 200

    @app.route("/checkproject", methods=["GET"])
    def checkProjectStatus():
        conn = get_db()
        cursor = conn.cursor()
        projectid = request.json.get('id')
        cursor.execute('''SELECT Status FROM Projects WHERE ProjectID = ?''', (projectid,))
        status = cursor.fetchone()[0]
        return status

    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        ip = request.remote_addr
        global online_users_by_pos
        for role, users in online_users_by_pos.items():
            online_users_by_pos[role] = [user for user in users if user['ip'] != ip]
            if any(user['ip'] == ip for user in users):
                logging.info(f"{role} с IPv4 адресом {ip} был удален.")

        return "OK", 200

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
            pass
        return "WaitForStatus", 200

    @app.route("/allusers", methods=["GET"])
    def all_users():
        users = fetch_all_users()
        return users

    @app.route("/ping", methods=["GET"])
    def ping():
        return "OK"

    @app.route("/user", methods=["GET"])
    def send_users():
        global online_users_by_pos
        return Response(json.dumps(online_users_by_pos, ensure_ascii=False),
                        content_type='application/json; charset=utf-8')

    @app.route("/pendingusers")
    def pending_users():
        cursor = get_db().cursor()
        cursor.execute('''
            SELECT UserID, Name, Status, Position, SystemLogin FROM Users 
            WHERE Status = ? 
            AND Position IN (?, ?, ?)
        ''', ('waiting', 'Менеджер', 'Рабочий', 'Посетитель'))

        us = cursor.fetchall()
        if not us:
            return 404
        return us

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()


def fetch_all_users():
    global all_users_by_pos
    all_users_by_pos = {
        "Директор": [],
        "Менеджер": [],
        "Рабочий": [],
        "Посетитель": []
    }
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT UserID, SystemLogin, Name, Position, Status FROM Users
        ''')
        users = cursor.fetchall()
        for user in users:
            all_users_by_pos[user[3]].append([user[0], user[1], user[2]])
        return all_users_by_pos


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
    if not os.path.exists("projects"):
        os.mkdir("projects")
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
                SystemLogin  TEXT    NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProjectName TEXT NOT NULL,
                ProjectDesc TEXT,
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
            );
        ''')
        connection.commit()

    return app
