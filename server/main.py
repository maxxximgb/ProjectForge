from ui.ui import Server
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication([])
server = Server()
sys.exit(app.exec())