import asyncio
from Client.scripts.ui.Windows import LoadingUI
import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    ui = LoadingUI()
    with loop:
        loop.run_forever()
