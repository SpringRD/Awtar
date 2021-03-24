from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from components.database.circular_progress_bar import QRoundProgressBar
from components.database.database_threads import LoadThread


class LoadDialog(QDialog):
    def __init__(self, parent, db_file, files):
        super(LoadDialog, self).__init__(parent)
        QDialog.__init__(self, parent)

        self.parent = parent
        self.db_file = db_file
        self.files = files

        self.thread = None

        self.icon = QIcon(':/icons/images/db_download.ico')
        self.bar = QRoundProgressBar()
        self.handle_ui()

        self.start_thread()

    def handle_ui(self):
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(200, 200)
        self.setWindowTitle('تحميل البيانات')
        self.setWindowIcon(self.icon)
        self.setStyleSheet('background: white; color: black')
        v_box = QVBoxLayout()
        v_box.addWidget(self.bar)
        self.setLayout(v_box)

    def start_thread(self):
        self.thread = LoadThread(self, self.db_file, self.files)
        self.thread.set_max_progress_signal.connect(self.set_max_progress)
        self.thread.progress_signal.connect(self.step_progress)
        self.thread.finish_signal.connect(self.finish)
        self.thread.start()

    def set_max_progress(self, value):
        self.bar.setMaximum(value + 1)

    def step_progress(self):
        self.bar.setValue(self.bar.m_value + 1)
        self.bar.repaint()
        self.bar.update()

    def finish(self, total):
        self.bar.setValue(self.bar.m_max)
        self.parent.get_vectors_signal.emit(total)
        self.parent.log_signal.emit("تم تحميل {} أسطر.\n".format(total))
        self.parent.log_text.insertPlainText('-------------------------------------------------\n')
        self.close()
        self.thread.stop()
        self.thread = None

    def closeEvent(self, event):
        print('close')
        if self.thread is not None:
            self.thread.stop()
        super(LoadDialog, self).closeEvent(event)
