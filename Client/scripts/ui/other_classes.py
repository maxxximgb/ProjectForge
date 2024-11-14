import asyncio
import base64
import json
import os.path
import sys
from operator import imatmul

import requests
from PyQt6.QtCore import QSize, QRect, Qt, QLine, QTimer, pyqtSignal, QByteArray, QBuffer, QIODevice, QRectF
from PyQt6.QtGui import QFont, QTextFrame, QCloseEvent, QIcon, QPixmap, QImage, QPainter, QBrush, QPainterPath
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QGridLayout, QSizePolicy, QSpacerItem, QLineEdit, \
    QHBoxLayout, QFormLayout, QDialog, QTextEdit, QMessageBox, QCheckBox, QComboBox, QFileDialog

online_users_by_pos = None
all_users_by_pos = None
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
cr_menu_ss = '''
QDialog {
    background-color: #2c2c2c;
    font-family: Arial, sans-serif;
    color: #ffffff;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 5px;
    transition: background-color 0.3s ease;
}

QPushButton:hover {
    background-color: #2980b9;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 5px;
    border-radius: 3px;
    font-size: 14px;
}

QLineEdit:focus {
    border: 1px solid #3498db;
    outline: none;
}

QTextEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 5px;
    border-radius: 3px;
    font-size: 14px;
}

QTextEdit:focus {
    border: 1px solid #3498db;
    outline: none;
}

QLabel {
    color: #ffffff;
    font-size: 14px;
}



QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 5px;
    border-radius: 3px;
    font-size: 14px;
}

QComboBox:focus {
    border: 1px solid #3498db;
    outline: none;
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #444444;
    selection-background-color: #3498db;
}
'''
proj_ss = """
QVBoxLayout {
    spacing: 10px;
}

QLabel {
    font-family: Arial, sans-serif;
    font-size: 16px;
}

QLabel#imagelabel {
    border: 2px solid #cccccc;
    border-radius: 20px;
    padding: 5px;
    background-color: #ffffff;
}

QLabel#imagelabel QPixmap {
    border-radius: 20px;
}

QPushButton {
    background-color: #FF5733;
    color: white;
    padding: 8px 16px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 5px;
}

QPushButton:hover {
    background-color: #E64A19;
}

QPushButton:pressed {
    background-color: #D84315;
}
"""
pending_users = []
pending_projects = []
userpos = None
pos2lvl = {"Директор": 4,
           "Менеджер": 3,
           "Рабочий": 2,
           "Посетитель": 1}
eng_to_rus = {
    "waiting": "Ожидает подтверждения",
    "approved": "Подтвержден",
    "denied": "Отклонен"
}
host = None
port = None
glogin = None


def roundCorners(pixmap, radius):
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(pixmap))
    painter.setPen(Qt.PenStyle.NoPen)
    path = QPainterPath()
    path.addRoundedRect(QRectF(pixmap.rect()), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(pixmap.rect(), pixmap)
    painter.end()
    return rounded


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
        self.add_btn.setMaximumSize(300, 300)
        self.add_btn.setText('+')
        self.setSpacing(0)
        self.add_btn.clicked.connect(self.add_project)
        self.addWidget(self.add_btn)
        self.addWidget(self.textlabel)

    def add_project(self):
        self.addpr_widget = AddProjectWidget(self)
        self.addpr_widget.initialize()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    pixmapChanged = pyqtSignal()

    def __init__(self, *args):
        super().__init__()
        self.ispixmap = False

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.ispixmap = True
        self.pixmapChanged.emit()


class AddProjectWidget(QDialog):
    def __init__(self, btn):
        super().__init__()
        self.removed_user_row = False
        self.file_path = None
        self.hide()
        self.save_btn = QPushButton()
        self.txt = None
        self.need_add = True
        self.project_name = ''
        self.project_desc = ''
        self.input_project_name = QLineEdit()
        self.input_project_desc = QTextEdit()
        self.people_working_on_project = QVBoxLayout()
        self.people_list = []
        self.layout = QVBoxLayout()
        self.formlayout = QFormLayout()
        self.setLayout(self.layout)
        self.supported_formats = [
            "*.bmp", "*.gif", "*.jpg", "*.jpeg", "*.png", "*.pbm", "*.pgm", "*.ppm", "*.xbm", "*.xpm"
        ]
        self.users = []
        self.selected_users = set()  # Множество для отслеживания выбранных пользователей

    def initialize(self):
        self.setStyleSheet(cr_menu_ss)
        self.setWindowTitle("Добавить проект")
        self.formlayout.setSpacing(20)
        self.image = ClickableLabel()
        self.image.setStyleSheet('''
        ClickableLabel {
            color: #3498db;
            font-size: 14px;
            border: 1px solid #444444;
            padding: 5px;
            border-radius: 3px;
            background-color: #3c3c3c;
            transition: background-color 0.3s ease;
        }
        ClickableLabel:hover {
            background-color: #444444;
            cursor: pointer;
        }
        ''')
        self.image.setText("*Добавить картинку")
        self.image.setMaximumSize(150, 200)
        self.image.clicked.connect(self.addImage)
        self.input_project_desc.setMaximumHeight(60)
        self.input_project_name.setPlaceholderText("Название")
        self.input_project_desc.setPlaceholderText("Описание")
        self.formlayout.addRow(self.image)
        self.formlayout.addRow(QLabel(text='*Назовите проект.'), self.input_project_name)
        self.formlayout.addRow(QLabel(text='Опишите проект.'), self.input_project_desc)

        self.save_btn.setText("Добавить проект")
        self.save_btn.clicked.connect(self.save)
        self.layout.addLayout(self.formlayout)
        self.layout.addWidget(self.save_btn)

        self.formlayout.addRow(QLabel("Добавьте пользователей"), self.people_working_on_project)

        asyncio.create_task(self.empty_users_task())
        self.exec()

    async def empty_users_task(self):
        global all_users_by_pos, host, port, glogin
        while self.isVisible():
            r = requests.get(f"http://{host}:{port}/allusers")
            all_users_by_pos = json.loads(r.text)
            self.updateUsers()
            await asyncio.sleep(9)

    def updateUsers(self):
        global all_users_by_pos, glogin

        all_users = {user[0] for users in all_users_by_pos.values() for user in users if user[1] != glogin}
        if not all_users:
            if not self.removed_user_row:
                self.formlayout.removeRow(self.people_working_on_project)
                self.removed_user_row = True
            return
        else:
            if self.removed_user_row:
                self.people_working_on_project = QVBoxLayout()
                self.formlayout.addRow(QLabel("Добавьте пользователей"), self.people_working_on_project)
                self.removed_user_row = False

        current_users = {combo_box.currentData() for combo_box in self.people_list if combo_box.currentIndex() >= 0}

        new_users = all_users - current_users
        removed_users = current_users - all_users

        for i in reversed(range(self.people_working_on_project.count())):
            item = self.people_working_on_project.itemAt(i)
            hbox_layout = item.layout()
            combo_box = hbox_layout.itemAt(0).widget()
            if combo_box.currentIndex() >= 0:
                user_id = combo_box.currentData()
                if user_id in removed_users:
                    self.people_working_on_project.removeItem(item)
                    combo_box.deleteLater()
                    hbox_layout.itemAt(1).widget().deleteLater()
                    hbox_layout.deleteLater()
                    self.people_list.remove(combo_box)

        for combo_box in self.people_list:
            for i in range(combo_box.count()):
                if combo_box.itemData(i) in removed_users:
                    combo_box.removeItem(i)

        current_values = {combo_box: combo_box.currentData() for combo_box in self.people_list}

        for combo_box in self.people_list:
            combo_box.clear()
            for position, users in all_users_by_pos.items():
                if users:
                    for user in users:
                        if user[1] != glogin and user[0] not in self.selected_users:
                            combo_box.addItem(f"{position} {user[2]}", user[0])

        for combo_box, user_id in current_values.items():
            index = combo_box.findData(user_id)
            if index >= 0:
                combo_box.setCurrentIndex(index)

        if len(self.people_list) == 0:
            self.addNewComboBox()
        self.updateAddButton()

    def updateAddButton(self):
        global all_users_by_pos, glogin
        last_combo_box = self.people_list[-1]
        if last_combo_box.currentIndex() >= 0:
            total_users = sum(len(users) for users in all_users_by_pos.values()) - 1
            if len(self.people_list) < total_users:
                last_hbox_layout = self.people_working_on_project.itemAt(
                    self.people_working_on_project.count() - 1).layout()
                last_add_button = last_hbox_layout.itemAt(1).widget()
                last_add_button.setVisible(True)
            else:
                for i in range(self.people_working_on_project.count()):
                    hbox_layout = self.people_working_on_project.itemAt(i).layout()
                    add_button = hbox_layout.itemAt(1).widget()
                    add_button.setVisible(False)
        else:
            for i in range(self.people_working_on_project.count()):
                hbox_layout = self.people_working_on_project.itemAt(i).layout()
                add_button = hbox_layout.itemAt(1).widget()
                add_button.setVisible(False)

    def addNewComboBox(self):
        global all_users_by_pos, glogin
        new_combo_box = QComboBox()
        new_combo_box.setPlaceholderText("Выберите участников")
        for position, users in all_users_by_pos.items():
            if users:
                for user in users:
                    if user[1] != glogin and user[0] not in self.selected_users:
                        new_combo_box.addItem(f"{position} {user[2]}", user[0])
        new_combo_box.currentIndexChanged.connect(self.updateAddButton)
        self.people_list.append(new_combo_box)
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(new_combo_box)
        add_button = QPushButton("+")
        add_button.clicked.connect(self.addNewComboBox)
        add_button.setVisible(False)
        hbox_layout.addWidget(add_button)
        self.people_working_on_project.addLayout(hbox_layout)
        self.updateAddButton()

    def save(self):
        global host, port
        r = False
        if not self.image.ispixmap:
            self.image.setStyleSheet("border: 2px solid red;")
            self.image.pixmapChanged.connect(lambda: self.image.setStyleSheet(""))
            r = True
        if not self.input_project_name.text():
            self.input_project_name.setStyleSheet("border: 2px solid red;")
            self.input_project_name.textChanged.connect(lambda: self.input_project_name.setStyleSheet(""))
            r = True
        if r: return
        global glogin
        self.project_name = self.input_project_name.text()
        self.project_desc = self.input_project_desc.toPlainText()
        data = {
            "login": glogin,
            "name": self.project_name,
            "desc": self.project_desc,
            "image": None
        }
        image = self.image.pixmap().toImage()
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        image_base64 = base64.b64encode(byte_array).decode('utf-8')
        data["image"] = image_base64
        participants = []
        for combo_box in self.people_list:
            if combo_box.currentIndex() >= 0:
                user_id = combo_box.currentData()
                participants.append(user_id)
                self.selected_users.add(user_id)
        data["participants"] = participants
        r = requests.post(f"http://{host}:{port}/newproject", json=data)
        if r.status_code == 200:
            mbox = QMessageBox()
            mbox.setText("Проект успешно создан в системе и ждет подтверждения.")
            mbox.setIcon(QMessageBox.Icon.Information)
            mbox.setWindowTitle("Проект успешно создан.")
            mbox.exec()
            self.close()
        elif r.status_code == 400:
            self.input_project_name.setStyleSheet("border: 2px solid red;")
            self.input_project_name.textChanged.connect(lambda: self.input_project_name.setStyleSheet(""))
            mbox = QMessageBox()
            mbox.setText("Проект с выбранным названием уже существует в системе.")
            mbox.setIcon(QMessageBox.Icon.Information)
            mbox.setWindowTitle("Проект существует.")
            mbox.exec()
            return

    def addImage(self):
        filter_string = "Картинки (" + " ".join(self.supported_formats) + ")"
        self.file_path, _ = QFileDialog.getOpenFileName(None, "Выберите картинку проекта", "", filter_string)
        if not self.file_path: return
        image = QImage(self.file_path)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(QSize(100, 150), Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        self.image.setPixmap(scaled_pixmap)
        self.image.setStyleSheet("")


class MenuCentralWidget(QWidget):
    def __init__(self, server, pos):
        super().__init__()
        self.pending_projects_label = None
        self.pendings = None
        self.showPending = None
        self.pending_users_label = None
        self.current_row_width = 0
        self.rows = []
        global userpos
        userpos = pos
        self.server = server
        self.no_projects = None
        self.no_project_widget = None
        self.cur_project_widget = None
        self.gl = QGridLayout()
        self.layout = QVBoxLayout()
        self.pending_users = None
        self.pending_layout = None
        self.pr_layouts = []
        self.projects = []
        self.cur_col = 0
        self.cur_row = 0
        self.add_project_btn = None
        self.empty_widgets = []
        self.setLayout(self.gl)
        self.InitUI()

    async def updateProjects(self):
        global host, port, glogin
        while True:
            r = requests.get(f"http://{host}:{port}/getup", json={"login": glogin})
            if r.status_code != 404:
                projects = json.loads(r.text)
                for project in projects:
                    project_img_r = requests.get(f"http://{host}:{port}/projectimg/{project[1]}")
                    project_img = project_img_r.content
                    project.append(project_img)
                    self.insertProject(project)
            await asyncio.sleep(5)

    def InitUI(self):
        global userpos, pos2lvl, glogin

        r = requests.get(f"http://{host}:{port}/getup", json={"login": glogin})
        if r.status_code == 404 and pos2lvl[userpos] == 1:
            mbox = QMessageBox()
            mbox.setText("У вас нет доступа к проектам пользователей.")
            mbox.setIcon(QMessageBox.Icon.Information)
            mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
            mbox.setWindowTitle("Нет доступа")
            mbox.exec()
            os.abort()
        asyncio.create_task(self.updateProjects())
        if pos2lvl[userpos] > 2:
            self.pending_layout = QHBoxLayout()
            self.pending_users_label = QLabel()
            self.pending_projects_label = QLabel()
            self.pendings = QVBoxLayout()
            self.pendings.addWidget(self.pending_users_label)
            self.pendings.addWidget(self.pending_projects_label)
            self.pending_layout.addLayout(self.pendings)
            self.showPending = QPushButton()
            self.showPending.setText("Проверить")
            self.showPending.clicked.connect(self.showpending)
            self.pending_layout.addWidget(self.showPending)
            self.showPending.setVisible(False)
            self.gl.addLayout(self.pending_layout, 0, 0,
                              alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            asyncio.create_task(self.UserPingTask())
        if pos2lvl[userpos] > 1:
            self.add_project_btn = QWidget()
            self.add_project_btn.setLayout(AddProjectBtn())
            self.add_project_btn.setMaximumSize(300, 310)
            self.layout.addWidget(self.add_project_btn,
                                  alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.gl.addLayout(self.layout, 0, 0)

    def showpending(self):
        pass

    def insertProject(self, project):
        if project[0] not in self.projects:
            global proj_ss
            self.projects.append(project[0])
            pr = Project(project)
            pwidget = QWidget()
            pwidget.setLayout(pr)
            pwidget.setMaximumSize(200, 300)
            pwidget.setStyleSheet(proj_ss)
            pr.initUI()
            self.pr_layouts.append([pr, project])
            if self.cur_col == 0:
                self.cur_row += 1
                hbox = QHBoxLayout()
                self.layout.addLayout(hbox)
                self.current_row_width = 0
                self.rows.append(hbox)

            self.rows[-1].addWidget(pwidget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.current_row_width += pr.sizeHint().width()

            if self.current_row_width >= 700:
                self.cur_col = 0
                self.cur_row += 1
                hbox = QHBoxLayout()
                self.layout.addLayout(hbox)
                self.current_row_width = 0
                self.rows.append(hbox)
                self.rows[-1].addWidget(self.add_project_btn,
                                        alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            else:
                self.cur_col += 1
                self.rows[-1].addWidget(self.add_project_btn,
                                        alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    async def UserPingTask(self):
        global host, port, pending_users, pending_projects
        while self.isVisible():
            a = False
            pu = requests.get(f"http://{host}:{port}/pendingusers")
            pp = requests.get(f"http://{host}:{port}/pendingProjects")
            if pu.status_code == 200:
                users = json.loads(pu.text)
                for el in users:
                    if el not in pending_users:
                        pending_users.append(el)
                if len(pending_users) > 0:
                    a = True
                    self.pending_users_label.setText(f"Пользователей, ожидающих регистрации: {len(pending_users)}")
            else:
                self.pending_users_label.setText(f"Никто не ожидает регистрации")
            if pp.status_code == 200:
                a = True
                projects = json.loads(pp.text)
                self.pending_projects_label.setText(f"Проектов, ожидающих регистрации: {len(projects)}")
                print(projects)
            else:
                self.pending_projects_label.setText("Нет ожидающих подтверждения проектов")
            self.showPending.setVisible(a)
            await asyncio.sleep(9)


class PendingUP(QDialog):
    def __init__(self):
        super().__init__()
        self.headers = [QLabel("Проекты"), QLabel("Пользователи")]
        self.lout = QVBoxLayout()
        self.hlout = QHBoxLayout()
        self.ulout = QHBoxLayout()
        self.initUI()

    def initUI(self):
        global pending_projects, pending_users
        self.lout.addLayout(self.hlout)
        if pending_projects:
            self.hlout.addWidget(self.headers[0])
        if pending_users:
            self.hlout.addWidget(self.headers[1])


class Project(QVBoxLayout):
    def __init__(self, project):
        super().__init__()
        self.project = project
        self.more_btn = QPushButton("О проекте")
        self.planning_btn = QPushButton("Планирование проекта")
        self.pixmap = None
        self.qimage = QImage()
        self.image = project[-1]
        self.imagelabel = QLabel()
        self.imagepixmap = None
        self.name = QLabel(project[1])
        self.desc = QLabel(project[2])
        self.status = project[4]

    def initUI(self):
        asyncio.create_task(self.selfPingTask())
        self.qimage.loadFromData(self.image)
        self.pixmap = QPixmap.fromImage(self.qimage)
        self.updateImage()
        self.more_btn.clicked.connect(self.showMore)
        self.planning_btn.clicked.connect(self.showplan)
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.imagelabel)
        self.addWidget(self.name)
        self.addWidget(self.more_btn)
        self.addWidget(self.planning_btn)
        self.setSpacing(5)

    def updateImage(self):
        if self.status == "waiting":
            grayscale_image = self.pixmap.toImage().convertToFormat(QImage.Format.Format_Grayscale8)
            self.pixmap = QPixmap.fromImage(grayscale_image)
        elif self.status == "approved":
            self.pixmap = QPixmap.fromImage(self.qimage)

        if self.pixmap.width() > self.pixmap.height():
            target_height = 165
            aspect_ratio = self.pixmap.width() / self.pixmap.height()
            target_width = int(target_height * aspect_ratio)
            self.parentWidget().setMaximumWidth(target_width + 20)
        else:
            target_width = 165
            target_height = 165

        scaled_pixmap = self.pixmap.scaled(target_width, target_height, Qt.AspectRatioMode.IgnoreAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        self.imagelabel.resize(scaled_pixmap.size())
        self.imagelabel.setPixmap(roundCorners(scaled_pixmap, 10))

    async def selfPingTask(self):
        global host, port
        while True:
            r = requests.get(f"http://{host}:{port}/GetProjectInfo", json={"id": self.project[0]})
            if r.status_code == 404:
                self.imagelabel.setPixmap(QPixmap(resource_path('images/projectdenied.png')))
                self.project[4] = 'denied'
                self.status = 'denied'
                break
            l = json.loads(r.text)
            if self.status == 'waiting' and l[4] == 'approved':
                self.status = 'approved'
                self.updateImage()
            await asyncio.sleep(9)

    def showplan(self):
        board = KanbanBoard()
        board.show()

    def showMore(self):
        info = ProjectInfo(self.project)
        info.exec()


class KanbanBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Канбан Доска BETA")
        self.headers = ["Не назначено", "Выполняется", "Выполнено"]
        self.header = QHBoxLayout()
        self.initUI()

    def initUI(self):
        [self.header.addWidget(QLabel(el)) for el in self.headers]


class ProjectInfo(QDialog):
    def __init__(self, project):
        super().__init__()
        self.creator = QLabel()
        self.status = QLabel(f"Состояние: {eng_to_rus[project[4]]}")
        self.project = project
        self.name = QLabel(f"Название: {project[1]}")
        if not project[2]:
            self.desc = QLabel(f"Описание отсутствует")
        else:
            self.desc = QLabel(f"Описание: {project[2]}")
        self.lout = QVBoxLayout()
        self.setLayout(self.lout)
        self.initUI()

    def initUI(self):
        global host, port, eng_to_rus
        self.setWindowTitle("Сведения о проекте")
        self.status.setWordWrap(True)
        self.desc.setWordWrap(True)
        r = requests.get(f"http://{host}:{port}/userid", json={"id": self.project[3]})
        l = json.loads(r.text)
        self.creator.setWordWrap(True)
        self.creator.setText(f"Создатель: {l[2]} {l[0]}, {l[3]}")
        self.lout.addWidget(self.status)
        self.lout.addWidget(self.name)
        self.lout.addWidget(self.desc)
        self.lout.addWidget(self.creator)


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
    def __init__(self, hosts, ports, loading_ui):
        global host, port
        super().__init__()
        host, port = hosts, ports
        self.ui = loading_ui
        self.mbox = None
        self.qbox = QComboBox()
        self.fio = QLineEdit()
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
        self.setMinimumSize(350, 200)
        self.setMaximumSize(400, 300)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.uname_input.setPlaceholderText("Логин")
        self.password_input.setPlaceholderText("Пароль")
        self.show_password_checkbox.setText("Показать пароль")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        if not os.path.exists('data/user.dat'):
            self.show_reg_mbox()
        else:
            try:
                global host, port
                with open('data/user.dat', 'r') as f:
                    d = f.read()
                    if d:
                        auth = self.check_auth(d.split())
                        if auth == 0:
                            asyncio.ensure_future(self.ui.wait_for_server(host, port, d.split()[1]))
                            self.close()
                            f.close()
                            return 0
            except:
                os.remove('data/user.dat')
                mbox = QMessageBox()
                mbox.setIcon(QMessageBox.Icon.Critical)
                mbox.setText("Файл user.dat был изменен, неоходима повторная авторизация.")
                mbox.exec()
                os.abort()

    def check_auth(self, d):
        global host, port, glogin
        password, login = d
        glogin = login
        data = {"password": password,
                "login": login}
        r = requests.post(f"http://{host}:{port}/authuser", json=data)
        if r.status_code == 403 or r.status_code == 404:
            mbox = QMessageBox()
            mbox.setIcon(QMessageBox.Icon.Critical)
            mbox.setWindowTitle("Статус авторизации")
            if r.text == "Incorrect password" or r.status_code == 404:
                mbox.setText(
                    "Похоже ваш аккаунт удален в системе или файл user.dat был изменен. Авторизируйтесь еще раз.")
                mbox.setStandardButtons(
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close)
                ans = mbox.exec()
                if ans == QMessageBox.StandardButton.Ok:
                    self.show_reg_mbox()
                else:
                    os.abort()
            elif r.text == "You are not approved":
                mbox.setText(
                    "Ваш запрос не регистрацию все еще ожидает ответа от администратора. Пожалуйста, подождите пока его одобрят. Стоит ли автоматически открыть программу при получении ответа?")
                mbox.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                ans = mbox.exec()
                if ans == QMessageBox.StandardButton.Yes:
                    self.close()
                    asyncio.ensure_future(self.ui.wait_for_server(host, port, login))
                    return 0
                else:
                    os.abort()
        else:
            global userpos
            userpos = r.text

            return 0

    def show_reg_mbox(self):
        self.mbox = QMessageBox()
        self.mbox.setText("Выберите действие.")
        self.mbox.setWindowTitle("Авторизация")
        self.mbox.closeEvent = self.mboxcloseevent
        self.mbox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.mbox.button(QMessageBox.StandardButton.Yes).setText("Вход")
        self.mbox.button(QMessageBox.StandardButton.No).setText("Регистрация")
        self.mbox.buttonClicked.connect(self.handle_button_click)
        self.mbox.exec()

    def mboxcloseevent(self, event: QCloseEvent):
        if event.spontaneous():
            os.abort()
        else:
            event.accept()

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
        if not self.validate_inputs(datatype):
            self.fio.textChanged.connect(self.validate_inputs)
            self.password_input.textChanged.connect(self.validate_inputs)
            self.uname_input.textChanged.connect(self.validate_inputs)
            self.qbox.currentIndexChanged.connect(self.validate_inputs)
            return 1

        self.send_data(datatype, login, password, name, position)

    def send_data(self, datatype, login, password, name='', position=''):
        global host, port, glogin
        glogin = login
        if datatype == "register":
            data = {
                "password": password,
                "login": login,
                "pos": position,
                "name": name
            }
            r = requests.post(f"http://{host}:{port}/newuser", json=data)
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
                    asyncio.ensure_future(self.ui.wait_for_server(host, port, login))
                    return 0
                else:
                    os.abort()
        else:
            auth = self.check_auth([password, login])
            if auth == 0:
                self.save_data(password, login)
                self.close()
                asyncio.ensure_future(self.ui.wait_for_server(host, port, login))
                return 0

    def save_data(self, password, login):
        if not os.path.exists('data'): os.mkdir('data')
        with open('data/user.dat', 'w') as f:
            f.write(f"{password} {login}")

    def validate_inputs(self, datatype):
        valid = True
        if datatype == "register":
            if self.fio.text():
                self.fio.setStyleSheet("")
            else:
                self.fio.setStyleSheet("border: 1px solid red;")
                valid = False
            if self.qbox.isVisible() and not self.qbox.currentText():
                self.qbox.setStyleSheet("border: 1px solid red;")
                valid = False
            else:
                self.qbox.setStyleSheet("")

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

        return valid
