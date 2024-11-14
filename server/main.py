import ctypes
import os
import logging
from ui.ui import Server
from PyQt6.QtWidgets import QApplication
import sys


def run():
    app = QApplication([])
    server = Server()
    sys.exit(app.exec())


if not os.path.exists('logs'): os.mkdir('logs')

logging.basicConfig(
    filename='logs/server.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

try:
    if os.name == "posix":
        os.abort()
    if ctypes.windll.shell32.IsUserAnAdmin() and hasattr(sys, '_MEIPASS'):
        run()
    elif not hasattr(sys, '_MEIPASS'):
        run()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        os.abort()
except Exception as e:
    logging.error(e)
    os.abort()
