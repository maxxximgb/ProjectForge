from scripts.ui.Windows import LoadingUI
import sys
from  PyQt6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    ui = LoadingUI()
    app.exec()
