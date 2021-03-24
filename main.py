from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic import loadUiType

import os
import io
import sys
import sqlite3
import numpy as np

import constants

from components.database.db_frame import DbFrame
from components.detection.detection_frame import DetectionFrame


def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("ARRAY", convert_array)


main_class, _ = loadUiType(os.path.join(constants.bundle_dir, "ui//main.ui"))


class MainClass(QMainWindow, main_class):
    def __init__(self):
        super(MainClass, self).__init__()
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.detection_frame = DetectionFrame()
        self.db_frame = DbFrame(self.detection_frame)

        self.handle_ui()

    def handle_ui(self):
        self.db_tab.layout().addWidget(self.db_frame)
        self.detection_tab.layout().addWidget(self.detection_frame)


def main():
    app = QApplication(sys.argv)
    main_ui = MainClass()
    main_ui.show()
    app.exec_()


if __name__ == '__main__':
    main()
