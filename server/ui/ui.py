import logging
import os.path
import ipaddress
import winreg
import sys
import socket
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from server.listenner.listenner import run_app, create_app, share, ForceCreateProject, get_waiting_directors, \
    accept_director, decline_director
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QMessageBox, QMainWindow, QMenu, QFormLayout, QLineEdit, \
    QCheckBox, QHBoxLayout, QSizePolicy, QVBoxLayout, QDialog, QPushButton, QSystemTrayIcon, QScrollArea
import pkg_resources

sv = None


def add_to_startup():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0,
                         winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "ProjectManagerServer", 0, winreg.REG_SZ, sys.executable)
    winreg.CloseKey(key)


def remove_from_startup():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0,
                         winreg.KEY_SET_VALUE)
    try:
        winreg.DeleteValue(key, "ProjectManagerServer")
    except FileNotFoundError:
        pass
    winreg.CloseKey(key)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Server(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tray = None
        global sv
        sv = self
        share(self)
        self.messagebox = None
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("images/icon.png")))
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.init_ui()

    def closeEvent(self, event):
        os.abort()

    def showEvent(self, event):
        super().showEvent(event)
        self.tray_icon.setVisible(False)
        self.tray = False

    def init_ui(self):
        if not os.path.exists("conf/app.conf"):
            os.mkdir("conf")
            self.configure_server(None)
        else:
            self.create_tray_icon_menu()
            self.run_server()

    def minimize_to_tray(self):
        self.tray = True
        self.hide()
        self.tray_icon.setVisible(True)
        self.tray_icon.showMessage("Внимание", "Сервер свернут в трей.", QSystemTrayIcon.MessageIcon.Warning, 5000)

    def create_tray_icon_menu(self):
        menu = QMenu()
        quit_action = QAction("Закрыть", self)
        quit_action.triggered.connect(os.abort)
        menu.addAction(quit_action)
        self.tray_icon.setToolTip("Сервер")
        self.tray_icon.setContextMenu(menu)

    def RequestRegister4Director(self):
        self.tray_icon.showMessage("Внимание", "Пользователь запрашивает регистрацию.",
                                   QSystemTrayIcon.MessageIcon.Information, 2000)
        self.cw.addDirectorCnt()

    def configure_server(self, is_error):
        self.messagebox = QMessageBox()
        if is_error == "ChangeConf":
            self.messagebox.setText(
                "Сейчас будет выполнена повторная настройка сервера. Нажмите ОК для продолжения.")
            self.messagebox.setWindowTitle("Настройка сервера")
            self.messagebox.setIcon(QMessageBox.Icon.Information)
            with open("conf/app.conf", "r") as f:
                args = f.read().split()
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
        self.configure_widget.finished.connect(self.force_restart_app)

    def force_restart_app(self):
        self.restart_messagebox = QMessageBox(text='Перезапустите приложение для применения изменений')
        self.restart_messagebox.setWindowTitle("Внимание!")
        self.restart_messagebox.show()
        self.restart_messagebox.finished.connect(os.abort)

    def run_server(self):
        self.setFixedSize(300, 200)
        self.r = create_app()
        self.setWindowTitle("Сервер")
        self.cw = CentralWidget()
        self.setCentralWidget(self.cw)
        print(open('conf/app.conf', 'r').read().split()[0].lower())
        if open('conf/app.conf', 'r').read().split()[0].lower() == 'true':
            self.minimize_to_tray()
        else:
            self.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
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
                self.lines[i].setChecked(args[i].lower() == 'true')
        for label, input_el in self.info:
            temp = QHBoxLayout()
            temp.addWidget(label)
            temp.addWidget(input_el)
            self.vboxlayout.addLayout(temp)
        self.vboxlayout.addWidget(self.save_btn)
        self.exec()

    def save(self):
        with open("conf/app.conf", "w") as f:
            f.write(
                f"{self.lines[0].isChecked()} {self.lines[1].isChecked()}")
            f.close()
            self.apply_settings()
            self.close()

    def apply_settings(self):
        with open("conf/app.conf", "r") as f:
            settings = f.read().split()
            minimize_to_tray = settings[0].lower() == 'true'
            add_to_startup_b = settings[1].lower() == 'true'

        if minimize_to_tray:
            sv.tray_icon.show()
            sv.hide()
        else:
            sv.tray_icon.hide()
            sv.show()

        if add_to_startup_b:
            add_to_startup()
        else:
            remove_from_startup()


class WaitingDirectors(QDialog):
    def __init__(self, cw):
        super().__init__()
        self.vlayout = QVBoxLayout()
        self.setLayout(self.vlayout)
        self.waitingdirectors = []
        self.cw = cw
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(500, 130)
        self.setMaximumSize(600, 250)
        self.setWindowTitle("Ожидающие разрешения директоры")
        self.setStyleSheet("""
        QPushButton {
            background-color: #00FF00;
            color: #000000;
            border: 2px solid #00FF00;
            border-radius: 5px;
            padding: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #00CC00;
            border: 2px solid #00CC00;
        }
        QPushButton:pressed {
            background-color: #009900;
            border: 2px solid #009900;
        }
        """)
        self.waitingdirectors = get_waiting_directors()
        logging.info(self.waitingdirectors)
        print(self.waitingdirectors)

        if not self.waitingdirectors:
            self.close()
        else:
            self.scroll_area = QScrollArea(self)
            self.scroll_area.setWidgetResizable(True)

            self.scroll_widget = QWidget()
            self.scroll_layout = QVBoxLayout(self.scroll_widget)

            for director in self.waitingdirectors:
                self.add_director_widget(director)

            self.scroll_area.setWidget(self.scroll_widget)
            self.vlayout.addWidget(self.scroll_area)
            self.update_window_size()

    def add_director_widget(self, director):
        dname = director[1]
        dlogin = director[5]
        dpos = director[4]
        director_widget = QWidget()
        director_layout = QHBoxLayout(director_widget)
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel(dpos))
        text_layout.addWidget(QLabel(f"ФИО: {dname}"))
        text_layout.addWidget(QLabel(f"Логин: {dlogin}"))
        button_layout = QVBoxLayout()
        accept_button = QPushButton("Принять")
        decline_button = QPushButton("Отклонить")
        decline_button.setFixedWidth(100)
        accept_button.setFixedWidth(100)
        accept_button.clicked.connect(lambda _, d=director: self.accept_director(d))
        decline_button.clicked.connect(lambda _, d=director: self.decline_director(d))
        button_layout.addWidget(accept_button)
        button_layout.addWidget(decline_button)
        director_layout.addLayout(text_layout)
        director_layout.addLayout(button_layout)
        self.scroll_layout.addWidget(director_widget)

    def accept_director(self, director):
        accept_director(director[5])
        logging.info(f"Директор {director[5]} принят")
        self.waitingdirectors.remove(director)
        self.cw.addDirectorCnt(-1)
        self.update_ui()

    def decline_director(self, director):
        decline_director(director[5])
        logging.info(f"Директор {director[5]} отклонен")
        self.waitingdirectors.remove(director)
        self.cw.addDirectorCnt(-1)
        self.update_ui()

    def update_ui(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for director in self.waitingdirectors:
            self.add_director_widget(director)
        if not self.waitingdirectors:
            self.close()
        self.update_window_size()

    def update_window_size(self):
        director_widget_height = 100
        total_height = len(self.waitingdirectors) * director_widget_height
        min_height = 130
        max_height = 250

        if total_height < min_height:
            self.resize(self.width(), min_height)
        elif total_height > max_height:
            self.resize(self.width(), max_height)
        else:
            self.resize(self.width(), total_height)


def change_cfg():
    sv.configure_server("ChangeConf")


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.waiting_directors = QHBoxLayout()
        self.addDirectors = QPushButton()
        self.waiting_directors_cnt = QLabel("Загрузка...")
        self.wd = 0
        self.vert_layout = QVBoxLayout()
        self.edit_cfg_btn = QPushButton()
        self.minimize_btn = QPushButton()
        self.port_and_host_layout = QHBoxLayout()
        self.port = QLabel()
        self.host = QLabel("Хост: Шир-вещ. канал (BETA)")
        self.is_app_running = False
        self.setLayout(self.vert_layout)
        self.app = sv.r
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.waiting_directors.addWidget(self.waiting_directors_cnt)
        self.waiting_directors.addWidget(self.addDirectors)
        self.addDirectors.clicked.connect(self.showDirectorsPanel)
        self.addDirectors.hide()
        self.addDirectorCnt(0)
        self.host.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.port.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.port_and_host_layout.addWidget(self.host)
        self.port_and_host_layout.addWidget(self.port)
        self.vert_layout.addLayout(self.port_and_host_layout)
        self.vert_layout.addLayout(self.waiting_directors)
        self.vert_layout.addWidget(self.edit_cfg_btn)
        self.vert_layout.addWidget(self.minimize_btn)
        self.addDirectors.setText("Просмотреть")
        self.edit_cfg_btn.setText("Изменить конфигурацию приложения")
        self.minimize_btn.setText("Свернуть сервер в трей")
        self.edit_cfg_btn.clicked.connect(change_cfg)
        self.minimize_btn.clicked.connect(sv.minimize_to_tray)
        port = self.GetFreePort()
        run_app(self.app, port)
        self.checkDirectors()

    def checkDirectors(self):
        d = get_waiting_directors()
        if len(d) > 0:
            self.addDirectorCnt(len(d))

    def showDirectorsPanel(self):
        wd = WaitingDirectors(self)
        wd.exec()

    def GetFreePort(self):
        for port in ['18965', '21761', '5000', '27815']:
            if (check_host_busy(port)):
                self.port.setText(f"Порт: {port}")
                return port

    def addDirectorCnt(self, cnt=1):
        self.wd += cnt
        self.waiting_directors_cnt.setText(f"Ожидают регистрации: {self.wd}")
        if self.wd != 0:
            self.addDirectors.show()
        else:
            self.addDirectors.hide()


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
