import os.path

from PyQt6.QtCore import QSize, QRect, Qt
from PyQt6.QtGui import QFont, QTextFrame
from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QGridLayout, QSizePolicy, QSpacerItem, QLineEdit, \
    QHBoxLayout, QFormLayout, QDialog, QTextEdit

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
        self.add_btn.setMinimumSize(200,200)
        self.add_btn.setText('+')
        self.setSpacing(0)
        self.add_btn.clicked.connect(self.add_project)
        self.addWidget(self.add_btn)
        self.addWidget(self.textlabel)

    def add_project(self):
        self.addpr_widget = AddProjectWidget(self)
        self.addpr_widget.initialize()

    #TODO проверить сохраняемые данные.

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
        self.txt = QLabel(text='*Добавьте людей, которые будут работать над проектом.(хотя бы одного) и назначьте им должность.')
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
        #TODO сохранить проекты в бд.

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
        #TODO подключиться к бд и проверить есть ли проекты
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
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(500,100)
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
        self.setWindowTitle("Не удалось найти сервер в сети")