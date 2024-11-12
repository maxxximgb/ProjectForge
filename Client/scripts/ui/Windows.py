import asyncio
import os
import shutil
import time
import asyncbg
import requests
from flask import request
from qasync import asyncSlot, QEventLoop
from Client.scripts.db_mgr.db_mgr import find_active_servers
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QProgressBar, QApplication, QVBoxLayout, QLabel, QHBoxLayout, QMainWindow, \
    QMessageBox
from Client.scripts.ui.other_classes import MenuCentralWidget, NoServerFound, AuthWidget


class LoadingUI(QWidget):
    def __init__(self):
        super().__init__()
        self.login = None
        self.position = None
        self.port = None
        self.host = None
        self.percent = 0
        self.cnt = 3
        self.screen = QApplication.primaryScreen()
        self.menu = None
        self.setWindowTitle("Программа запускается")
        self.screen = QApplication.primaryScreen().availableGeometry()
        self.bar = QProgressBar(self)
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Инициализация.", self)
        self.init_ui()

    def authorize_user(self, host, port):
        aw = AuthWidget(host, port, self)
        aw.initialize()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.layout.addWidget(self.bar)
        self.layout.addLayout(self.h_layout)
        self.setFixedSize(QSize(self.screen.size().width() // 5 - 20, self.screen.size().height() // 10))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bar.setValue(0)
        self.bar.resize(300, 30)
        self.resize(self.bar.size().width(), self.bar.size().height() + self.label.sizeHint().height())
        self.show()
        asyncio.ensure_future(self.launch_program())

    def change_tasks_count(self):
        self.cnt -= 1
        self.percent += 30
        self.label.setText(f"Выполняется задач перед запуском: {self.cnt}")
        self.bar.setValue(self.percent)
        if self.cnt == 0:
            self.menu = MainMenu()
            self.close()

    @asyncSlot()
    async def launch_program(self):
        self.change_tasks_count()
        await self.find_servers()

    @asyncSlot()
    async def find_servers(self):
        host, port = 0, 0
        while host == 0 or port == 0:
            host, port = await asyncbg.call_thread(find_active_servers)
            if host == 0 or port == 0:
                await self.unable_to_find_server()
        self.change_tasks_count()
        self.host, self.port = host, port
        self.authorize_user(host, port)
        return 0

    @asyncSlot()
    async def checkStatus(self, login, host, port):
        r = requests.get(f"http://{host}:{port}/userstatus", json={"name": login})
        if r.status_code == 403:
            return 403
        elif r.status_code == 200:
            self.position = r.text
            self.login = login
            return 200
        else:
            return 404

    @asyncSlot()
    async def wait_for_server(self, host, port, login):
        t = 0
        while True:
            try:
                s = await self.checkStatus(login, host, port)
            except:
                mbox = QMessageBox()
                mbox.setText("Сервер не отвечает на запросы клиента. Обратитесь к системному администратору с просьбой перезапустить его.")
                mbox.setIcon(QMessageBox.Icon.Critical)
                mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
                mbox.setWindowTitle("Сервер не отвечвает")
                mbox.finished.connect(os.abort)
                mbox.exec()
            self.label.setText(f"Ожидание ответа от сервера. Запросов выполнено: {t}")
            if s == 500:
                mbox = QMessageBox()
                mbox.setText("На сервере произошла ошибка, пожалуйста, обратитесь к системному администратору за помощью.")
                mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
                mbox.setIcon(QMessageBox.Icon.Critical)
                mbox.setWindowTitle("Ошибка сервера")
                mbox.finished.connect(os.abort)
                mbox.exec()

            elif s == 404:
                mbox = QMessageBox()
                mbox.setText("Ваш запрос на регистрацию отклонен.")
                mbox.setIcon(QMessageBox.Icon.Warning)
                mbox.setWindowTitle("Запрос отклонен.")
                mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
                mbox.finished.connect(self.registration_denied)
                mbox.exec()

            elif s == 200:
                self.change_tasks_count()
                break
            else:
                await asyncio.sleep(4)
                t += 1

    def registration_denied(self):
        shutil.rmtree("data")
        os.abort()

    @asyncSlot()
    async def unable_to_find_server(self):
        nsf = NoServerFound()
        nsf.initui()


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cw = MenuCentralWidget()
        self.InitUI()

    def InitUI(self):
        self.setWindowTitle("Панель управления")
        self.resize(1280, 720)
        self.setCentralWidget(self.cw)
        self.show()