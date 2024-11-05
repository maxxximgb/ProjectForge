import os
import time

from scripts.db_mgr.db_mgr import find_active_servers
from scripts.core.messaging.flask_app import run_flask
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import QWidget, QProgressBar, QApplication, QVBoxLayout, QLabel, QHBoxLayout, \
    QMainWindow, QDialog, QPushButton, QTableWidget, QTableView, QStackedLayout
from threading import Thread

from scripts.ui.other_classes import MenuCentralWidget, NoServerFound



class LoadingUI(QWidget):
    def __init__(self):
        super().__init__()
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
        self.show()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.layout.addWidget(self.bar)
        self.layout.addLayout(self.h_layout)
        self.setFixedSize(QSize(self.screen.size().width() // 7 - 20,self.screen.size().height()  // 10))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bar.setValue(0)
        self.bar.resize(300, 30)
        self.resize(self.bar.size().width(), self.bar.size().height() + self.label.sizeHint().height())
        self.launch_program()

    def change_tasks_count(self):
        self.cnt -= 1
        self.percent += 30
        self.label.setText(f"Выполняется задач перед запуском: {self.cnt}")
        self.bar.setValue(self.percent)

    def launch_program(self):
        self.change_tasks_count()
        QTimer.singleShot(1200, self.find_servers)

    def finalize_launch(self):
        self.menu = MainMenu()
        self.menu.show()
        self.hide()

    def find_servers(self):
        host, port = 0, 0
        while host == 0 or port == 0:
            host, port = find_active_servers()
            if host == 0 or port == 0:
                self.unable_to_find_server()
        QTimer.singleShot(1300, self.finalize_launch)
        return 0

    def unable_to_find_server(self):
        nsf = NoServerFound()
        nsf.initui()
        nsf.finished.connect()

class GantDiagramm(QWidget):
    def __init__(self, project):
        super().__init__()
        self.project = project
        self.insert_btn = QPushButton()
        self.stackedlayout = QStackedLayout()
        self.setLayout(self.stackedlayout)
        self.buttonslayout = QHBoxLayout()
        self.table = QTableWidget()

    def init_ui(self):
        self.setWindowTitle(f"Диаграмма Ганта для проекта {self.project["name"]}")
        self.insert_btn.setFixedSize(30, 30)
        self.stackedlayout.addChildLayout(self.buttonslayout)
        self.stackedlayout.addWidget(self.table)
        self.show()

class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = MenuCentralWidget()
        self.init_ui()

    def init_ui(self):
        self.resize(QSize(1280, 720))
        self.setCentralWidget(self.central_widget)
        self.central_widget.show()
