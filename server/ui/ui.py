import os.path
import ipaddress
import re
import sys
import socket
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from listenner.listenner import run_app, create_app
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QMessageBox, QMainWindow, QMenu, QFormLayout, QLineEdit, \
    QCheckBox, QHBoxLayout, QSizePolicy, QVBoxLayout, QDialog, QPushButton, QSystemTrayIcon

sv = None


class Server(QMainWindow):
    def __init__(self):
        super().__init__()
        global sv
        sv = self
        self.messagebox = None
        self.init_ui()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("images/icon.png"))

    def closeEvent(self, a0):
        os.abort()

    def init_ui(self):
        if not os.path.exists("app.conf"):
            self.configure_server(None)
        else:
            self.run_server()

    def configure_server(self, is_error):
        must_start = True
        self.messagebox = QMessageBox()
        if is_error == "HostOrPortBusy":
            self.messagebox.setText(
                "Произошла ошибка, возможно хост или порт занят другим процессом или вы указали не локальный IPv4 адрес. Попробуйте сменить их")
            self.messagebox.setWindowTitle("Ошибка сервера")
            self.messagebox.setIcon(QMessageBox.Icon.Critical)
            with open("server.conf", "r") as f:
                args = f.read().split()
            if 3>=len(args)>=1:
                self.messagebox.setText("Не изменяйте содержимое файла app.conf и перезапустите приложение.")
                must_start = False
            self.messagebox.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif is_error == "ChangeConf":
            self.messagebox.setText(
                "Сейчас будет выполнена повторная настройка сервера. Нажмите ОК для продолжения.")
            self.messagebox.setWindowTitle("Настройка сервера")
            self.messagebox.setIcon(QMessageBox.Icon.Information)
            with open("server.conf", "r") as f:
                args = f.read().split()
            must_start = False
        else:
            self.messagebox.setText("Сервер не настроен. Необходимо произвести настройку.")
            self.messagebox.setWindowTitle("Данный сервер не настроен")
            self.messagebox.setIcon(QMessageBox.Icon.Warning)
            args = ''
            self.messagebox.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok)
        self.configure_widget = ConfigureServer()
        self.setMaximumHeight(self.configure_widget.height())
        self.messagebox.open()
        self.messagebox.finished.connect(lambda a: self.configure_widget.init_ui(a, args))
        self.configure_widget.finished.connect(self.init_ui) if must_start else self.configure_widget.finished.connect(
            self.force_restart_app)

    def force_restart_app(self):
        self.restart_messagebox = QMessageBox(text='Перезапустите приложение для применения изменений')
        self.restart_messagebox.show()
        self.restart_messagebox.finished.connect(os.abort)

    def run_server(self):
        self.setFixedSize(300, 100)
        self.r = create_app()
        self.setWindowTitle("Сервер")
        if self.r == 1:
            self.configure_server("HostOrPortBusy")
        else:
            self.cw = CentralWidget()
            self.setCentralWidget(self.cw)
            self.show()


class ConfigureServer(QDialog):
    def __init__(self):
        super().__init__()
        self.info = None
        self.lines = None
        self.vboxlayout = None
        self.save_btn = None
        self.label = None

    def init_ui(self, a, args=''):
        if a != 1024:
            os.abort()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        self.setWindowTitle("Настройка сервера")
        self.vboxlayout = QVBoxLayout()
        self.setLayout(self.vboxlayout)
        self.lines = [QCheckBox(), QCheckBox()]
        self.info = [[QLabel("Сворачивать сервер в трей при запуске?"), self.lines[0]],
                     [QLabel("Открывать программу при запуске компьютера?"), self.lines[1]]]
        if args:
            for i in range(2):
                self.lines[i].setChecked(not bool(args[i]))
        for label, input_el in self.info:
            temp = QHBoxLayout()
            temp.addWidget(label)
            temp.addWidget(input_el)
            self.vboxlayout.addLayout(temp)
        self.vboxlayout.addWidget(self.save_btn)
        self.exec()

    def save(self):
        with open("app.conf", "w") as f:
            f.write(
                f"{self.lines[0].isChecked()} {self.lines[1].isChecked()}")
            f.close()
            self.close()


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.vert_layout = QVBoxLayout()
        self.edit_cfg_btn = QPushButton()
        self.port_and_host_layout = QHBoxLayout()
        self.port = QLabel()
        self.host = QLabel("0.0.0.0 (dynamic broadcast)")
        self.is_app_running = False
        self.setLayout(self.vert_layout)
        self.app = sv.r
        self.init_ui()

    def init_ui(self):
        self.host.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.port.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.port_and_host_layout.addWidget(self.host)
        self.port_and_host_layout.addWidget(self.port)
        self.vert_layout.addLayout(self.port_and_host_layout)
        self.vert_layout.addWidget(self.edit_cfg_btn)
        self.edit_cfg_btn.setText("Изменить конфигурацию приложения")
        self.edit_cfg_btn.clicked.connect(self.change_cfg)
        port = self.GetFreePort()
        run_app(self.app, port)
        self.show()

    def GetFreePort(self):
        for port in ['18965', '09761', '5000', '27815']:
            if (check_host_busy(port)):
                self.port.setText(f"Порт: {port}")
                return port

    def change_cfg(self):
        sv.configure_server("ChangeConf")


def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def check_host_busy(port):
    s = socket.socket()
    try:
        s.bind(("0.0.0.0", int(port)))
        s.shutdown(0)
    except OSError:
        return 1
    else:
        return 0