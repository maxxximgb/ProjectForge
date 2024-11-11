import asyncio
import hashlib
import os.path
import threading
from threading import Thread

import asyncbg
import requests
from PyQt6.QtCore import QSize, QRect, Qt, QLine, QTimer
from PyQt6.QtGui import QFont, QTextFrame
from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QGridLayout, QSizePolicy, QSpacerItem, QLineEdit, \
    QHBoxLayout, QFormLayout, QDialog, QTextEdit, QMessageBox, QCheckBox, QComboBox
from PyQt6.uic.Compiler.qtproxies import QtWidgets
from flask import request
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import hashlib

from Client.scripts.db_mgr.db_mgr import check_server

auth_ss = """
            QComboBox {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #388E3C;
                border-radius: 5px;
            }
            QComboBox:hover {
                background-color: #81C784;
            }
            QComboBox:on {
                background-color: #388E3C;
            }
            QLineEdit {
                border: 2px solid #888888;
                border-radius: 10px;
                padding: 5px;
                background-color: #f0f0f0;
                color: #333333;
                font-size: 14px;
                font-family: "Arial", sans-serif;
            }
            QLineEdit:hover {
                border: 2px solid #555555;
                background-color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
                background-color: #ffffff;
                color: #000000;
            }
            QLineEdit:disabled {
                background-color: #cccccc;
                color: #888888;
                border: 2px solid #aaaaaa;
            }
            QPushButton {
                background-color: #6a00ff;
                border: 2px solid #342a42;
                border-radius: 5px;
                padding: 8px 20px;
                color: white;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #0510a6;
                border: 2px solid #242645;
            }

            QPushButton:pressed {
                background-color: #3a0980;
                border: 2px solid #f500cc;
            }

            QPushButton[flat="true"] {
                background-color: transparent;
                border: none;
                color: #0078d4;
                text-decoration: underline;
                padding: 0;
            }

            QPushButton[flat="true"]:hover {
                color: #005a9e;
            }
        """


class AddProjectBtn(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.font = QFont()
        self.textlabel = None
        self.add_btn = None
        self.initialize()

    def initialize(self):
        self.add_btn = QPushButton()
        self.textlabel = QLabel()
        self.font.setBold(True)
        self.textlabel.setText('Добавить проект')
        self.textlabel.setFont(self.font)
        self.textlabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.textlabel.setFont(QFont())
        self.add_btn.setMinimumSize(200, 200)
        self.add_btn.setText('+')
        self.setSpacing(0)
        self.add_btn.clicked.connect(self.add_project)
        self.addWidget(self.add_btn)
        self.addWidget(self.textlabel)

    def add_project(self):
        self.addpr_widget = AddProjectWidget(self)
        self.addpr_widget.initialize()

    # TODO проверить сохраняемые данные.


class PersonWorkingOnProject(QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.initialize()

    def initialize(self):
        self.name = QLineEdit()
        self.name.setPlaceholderText("Инициалы рабочего")
        self.job_title = QLineEdit()
        self.job_title.setPlaceholderText("Должность рабочего")
        self.NameAndTitle = QVBoxLayout()
        self.NameAndTitle.setSpacing(1)
        self.NameAndTitle.addWidget(self.name)
        self.NameAndTitle.addWidget(self.job_title)
        self.add_person_button = QPushButton()
        self.add_person_button.setMaximumSize(20, 20)
        self.add_person_button.setMinimumSize(15, 15)
        self.add_person_button.setText("+")
        self.addLayout(self.NameAndTitle)
        self.addWidget(self.add_person_button)


class AddProjectWidget(QDialog):
    def __init__(self, btn):
        super().__init__()
        self.hide()
        self.save_btn = QPushButton()
        self.txt = None
        self.project_name = ''
        self.project_desc = ''
        self.input_project_name = QLineEdit()
        self.input_project_desc = QTextEdit()
        self.people_working_on_project = QVBoxLayout()
        self.people_list = []
        self.layout = QVBoxLayout()
        self.formlayout = QFormLayout()
        self.setLayout(self.layout)

    def initialize(self):
        self.setWindowTitle("Добавить проект")
        self.formlayout.setSpacing(20)
        self.input_project_desc.setMaximumHeight(60)
        self.input_project_name.setPlaceholderText("Название")
        self.formlayout.addRow(QLabel(text='*Назовите проект.'), self.input_project_name)
        self.formlayout.addRow(QLabel(text='Опишите проект.'), self.input_project_desc)
        self.txt = QLabel(
            text='*Добавьте людей, которые будут работать над проектом.(хотя бы одного) и назначьте им должность.')
        self.txt.setWordWrap(True)
        self.formlayout.addRow(self.txt, self.people_working_on_project)
        self.add_people()
        self.save_btn.setText("Добавить проект")
        self.save_btn.clicked.connect(self.save)
        self.layout.addLayout(self.formlayout)
        self.layout.addWidget(self.save_btn)
        self.exec()

    def save(self):
        self.project_name = self.input_project_name.text()
        self.project_desc = self.input_project_desc.toPlainText()
        print(self.project_desc, self.project_name, [text[0].text() for text in self.people_list])
        self.close()
        # TODO сохранить проекты в бд.

    def add_people(self):
        self.person = PersonWorkingOnProject()
        self.person.add_person_button.clicked.connect(self.add_people)
        self.people_list.append(tuple([self.person.name, self.person.job_title]))
        self.people_working_on_project.addLayout(self.person)


class MenuCentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.no_projects = None
        self.no_project_widget = None
        self.cur_project_widget = None
        self.layout = QGridLayout()
        self.cur_col = 0
        self.cur_row = 0
        self.setLayout(self.layout)
        # TODO подключиться к бд и проверить есть ли проекты
        self.no_project_exsist()

    def add_project(self, project):
        self.cur_project_widget = QWidget()
        self.cur_project_widget.setLayout(project)
        self.cur_project_widget.setFixedSize(QSize(200, 200))
        self.layout.addWidget(self.cur_project_widget, self.cur_row, self.cur_col)
        if self.cur_col == 5:
            self.cur_col = 0
            self.cur_row += 1
        else:
            self.cur_col += 1

    def no_project_exsist(self):
        self.no_project_widget = QWidget()
        self.no_projects = AddProjectBtn()
        self.no_project_widget.setLayout(self.no_projects)
        self.no_project_widget.setMaximumWidth(210)
        self.no_project_widget.setMaximumHeight(250)
        self.layout.addWidget(self.no_project_widget, 0, 0)


class NoServerFound(QDialog):
    def __init__(self):
        super().__init__()

    def initui(self):
        self.setWindowTitle("Не удалось найти сервер в сети")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(500, 100)
        l = [QLabel("Не удалось найти сервер в сети. Убедитесь что сервер запущен и повторите попытку."), QHBoxLayout()]
        retry = QPushButton("Повторить попытку")
        close = QPushButton("Закрыть")
        l[1].addWidget(retry)
        l[1].addWidget(close)
        layout.addWidget(l[0])
        layout.addLayout(l[1])
        retry.clicked.connect(self.close)
        close.clicked.connect(os.abort)
        self.exec()



class AuthWidget(QDialog):
    def __init__(self, host, port, loading_ui):
        super().__init__()
        self.ui = loading_ui
        self.mbox = None
        self.qbox = QComboBox()
        self.fio = QLineEdit()
        self.shost = host
        self.sport = port
        self.uname_input = QLineEdit()
        self.password_input = QLineEdit()
        self.register_btn = QPushButton()
        self.login_btn = QPushButton()
        self.show_password_checkbox = QCheckBox(self)
        self.logandpas = QVBoxLayout()
        self.logandpas.addWidget(self.uname_input)
        self.logandpas.addWidget(self.password_input)
        self.logandpas.addWidget(self.show_password_checkbox)

    def closeEvent(self, event):
        if event.spontaneous():
            os.abort()
        else:
            event.accept()

    def initialize(self):
        self.setLayout(self.logandpas)
        self.setStyleSheet(auth_ss)
        self.qbox.setPlaceholderText("Выберите должность")
        self.fio.setPlaceholderText("ФИО")
        self.qbox.addItem("Директор")
        self.qbox.addItem("Менеджер")
        self.qbox.addItem("Рабочий")
        self.qbox.addItem("Посетитель")
        self.setMinimumSize(350, 150)
        self.setMaximumSize(400, 300)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.uname_input.setPlaceholderText("Логин")
        self.password_input.setPlaceholderText("Пароль")
        self.show_password_checkbox.setText("Показать пароль")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        if not os.path.exists('data/user.dat'):
            self.mbox = QMessageBox()
            self.mbox.setText("Не найдены сохраненные пользователи. Необходимо войти.")
            self.mbox.setWindowTitle("Нет сохраненных пользователей")
            self.mbox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            self.mbox.button(QMessageBox.StandardButton.Yes).setText("Вход")
            self.mbox.button(QMessageBox.StandardButton.No).setText("Регистрация")
            self.mbox.buttonClicked.connect(self.handle_button_click)
            self.mbox.exec()
        else:
            # TODO авто авторизация
            pass

    def toggle_password_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def handle_button_click(self, button):
        self.mbox.close()
        if button.text() == "Вход":
            self.authorize()
        elif button.text() == "Регистрация":
            self.register()
        self.exec()

    def authorize(self):
        self.setWindowTitle("Авторизация пользователя")
        self.login_btn.setText("Войти")
        self.logandpas.addWidget(self.login_btn)
        self.login_btn.clicked.connect(
            lambda: self.validate_and_send("login", self.uname_input.text(), self.password_input.text()))

    def register(self):
        self.logandpas.insertWidget(0, self.fio)
        self.logandpas.addWidget(self.qbox)

        self.setWindowTitle("Регистрация пользователя")
        self.logandpas.addWidget(self.register_btn)
        self.register_btn.setText("Отправить запрос на регистрацию")
        self.register_btn.clicked.connect(
            lambda: self.validate_and_send("register", self.uname_input.text(), self.password_input.text(),
                                           self.fio.text(),
                                           self.qbox.currentText()))

    def validate_and_send(self, datatype, login, password, name='', position=''):

        if not self.validate_inputs():
            self.fio.textChanged.connect(self.validate_inputs)
            self.password_input.textChanged.connect(self.validate_inputs)
            self.uname_input.textChanged.connect(self.validate_inputs)
            self.qbox.currentIndexChanged.connect(self.validate_inputs)
            return 1

        self.send_data(datatype, login, password, name, position)

    def send_data(self, datatype, login, password, name='', position=''):
        if datatype == "register":
            data = {
                "password": password,
                "login": login,
                "pos": position,
                "name": name
            }
            r = requests.post(f"http://{self.shost}:{self.sport}/newuser", json=data)
            print(r.text)
            if r.status_code == 403:
                already_registered = QMessageBox()
                already_registered.setText(
                    f"Пользователь с заданным логином '{login}' уже существует в системе. Если это вы, то выберите опцию вход при запуске программы.")
                already_registered.setStandardButtons(QMessageBox.StandardButton.Ok)
                already_registered.exec()
                return
            else:
                succesful_request = QMessageBox()
                succesful_request.setText(
                    "Запрос на регистрацию успешно отправлен, ожидайте подтверждения. Стоит ли автоматически открыть программу при получении ответа?")
                succesful_request.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                ans = succesful_request.exec()
                self.save_data(password, login)
                if ans == QMessageBox.StandardButton.Yes:
                    self.close()
                    asyncio.ensure_future(self.ui.wait_for_server(self.shost, self.sport, login))
                    return 0
                else:
                    os.abort()
        else:
            data = {
                "password": password,
                "login": login
            }
            r = requests.post(f"http://{self.shost}:{self.sport}/authuser", json=data)
            print(r.text)

    def save_data(self, password, login):
        if not os.path.exists('data'): os.mkdir('data')
        with open('data/user.dat', 'w') as f:
            f.write(f"{password} {login}")



    def validate_inputs(self):
        valid = True
        if self.fio.text():
            self.fio.setStyleSheet("")
        else:
            self.fio.setStyleSheet("border: 1px solid red;")
            valid = False
        if not self.uname_input.text():
            self.uname_input.setStyleSheet("border: 1px solid red;")
            valid = False
        else:
            self.uname_input.setStyleSheet("")
        if not self.password_input.text():
            self.password_input.setStyleSheet("border: 1px solid red;")
            valid = False
        else:
            self.password_input.setStyleSheet("")
        if self.qbox.isVisible() and not self.qbox.currentText():
            self.qbox.setStyleSheet("border: 1px solid red;")
            valid = False
        else:
            self.qbox.setStyleSheet("")

        return valid
