from PyQt5.QtWidgets import QApplication, QFrame, QFileDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5.uic import loadUiType

import os

from core.model import vggvox_model
from core.scoring import build_buckets

from components.database.database_threads import InsertThread
from components.database.db_dialog import DbDialog
from components.database.load_dialog import LoadDialog
from components.database import database_helper
import constants

db_frame_class, _ = loadUiType(os.path.join(constants.bundle_dir, "ui//db_frame.ui"))


class DbFrame(QFrame, db_frame_class):
    send_vectors_signal = pyqtSignal(str, bool)
    get_vectors_signal = pyqtSignal(int)
    new_db_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, photo_frame):
        super(DbFrame, self).__init__()
        QFrame.__init__(self)
        self.setupUi(self)

        self.handle_ui()
        self.handle_buttons()
        self.photo_frame = photo_frame

        self.send_vectors_signal.connect(photo_frame.from_db_frame)
        self.new_db_signal.connect(self.attach)
        self.get_vectors_signal.connect(self.get_vectors)
        self.log_signal.connect(self.log_text.insertPlainText)

        self.db_file = constants.db_file

        self.sql = None

        self.threads = []

        self.total = self.step = 0

        self.check_db_configuration()

    def handle_ui(self):
        self.threads_spin.setVisible(False)
        self.stop_btn.setVisible(False)

    def handle_buttons(self):
        self.new_db_btn.clicked.connect(self.new_db)
        self.db_btn.clicked.connect(self.select_db)
        self.add_folder_to_db_btn.clicked.connect(self.add_folder_to_db)
        self.add_to_db_btn.clicked.connect(self.add_to_db)
        self.copy_btn.clicked.connect(self.copy_text)
        self.stop_btn.clicked.connect(self.stop_inserting)
        self.load_btn.clicked.connect(self.load_data)

    def check_db_configuration(self):
        if self.db_file == '':
            self.db_file = None
            self.add_folder_to_db_btn.setEnabled(False)
            self.add_to_db_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.log_text.insertPlainText('يجب تحديد قاعدة بيانات\n')
            self.log_text.insertPlainText('-------------------------------------------------\n')
            self.send_vectors_signal.emit(self.db_file, True)
            self.db_path.setText(self.db_file)
        else:
            self.attach_db()

    def new_db(self):
        db = DbDialog(self)
        db.exec_()

    def attach(self, file):
        self.log_text.clear()
        self.db_file = file
        f = open(constants.db_path, 'w')
        f.write(self.db_file)
        f.close()
        self.add_folder_to_db_btn.setEnabled(True)
        self.add_to_db_btn.setEnabled(True)
        self.load_btn.setEnabled(False)
        self.log_text.insertPlainText('يجب إضافة مقاطع صوتية على ' + self.db_file + "\n")
        self.log_text.insertPlainText('-------------------------------------------------\n')
        self.records_lbl.setText('')
        self.db_path.setText(self.db_file)
        self.send_vectors_signal.emit(self.db_file, True)

    def select_db(self):
        file = QFileDialog.getOpenFileName(parent=self, caption='اختر قاعدة البيانات', filter='DB Files (*.db)')

        if file[0] != '':
            self.db_file = file[0]
            f = open(constants.db_path, 'w')
            f.write(self.db_file)
            f.close()
            self.attach_db()

    def attach_db(self):
        self.log_text.clear()
        result = database_helper.check_db_cols(self.db_file)
        if result:
            self.add_folder_to_db_btn.setEnabled(True)
            self.add_to_db_btn.setEnabled(True)
            if database_helper.is_empty_db(self.db_file):
                self.load_btn.setEnabled(False)
                self.log_text.insertPlainText('يجب إضافة مقاطع صوتية على ' + self.db_file + "\n")
            else:
                self.load_btn.setEnabled(True)
                self.log_text.insertPlainText('يجب تحميل المعلومات من ' + self.db_file + "\n")
            self.send_vectors_signal.emit(self.db_file, True)
            self.log_text.insertPlainText('-------------------------------------------------\n')
            self.records_lbl.setText('')
        else:
            self.add_folder_to_db_btn.setEnabled(False)
            self.add_to_db_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.records_lbl.setText('قاعدة البيانات غير صحيحة')
            self.send_vectors_signal.emit(self.db_file, False)
        self.db_path.setText(self.db_file)

    def load_data(self):
        d = LoadDialog(self, self.db_file, self.photo_frame.files)
        d.exec()

    def get_vectors(self, total):
        self.log_text.clear()
        self.add_folder_to_db_btn.setEnabled(True)
        self.add_to_db_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.records_lbl.setText('عدد الأسطر: {}'.format(total))
        self.log_text.insertPlainText('تم تحميل المعلومات من قاعدة البيانات\n')
        self.log_text.insertPlainText('-------------------------------------------------\n')

    def copy_text(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.log_text.toPlainText(), mode=cb.Clipboard)

    def add_to_db(self):
        files = QFileDialog.getOpenFileNames(parent=self,
                                             caption='اختر مقطع صوتي أو مجموعة مقاطع صوتية لإضافتها على قاعدة البيانات',
                                             filter='Sounds Files (*.wav)')
        if len(files[0]) != 0:
            self.insert_to_database(files[0])

    def add_folder_to_db(self):
        folder_path = QFileDialog.getExistingDirectory(self, " اختر مجلد ")
        if folder_path is not None:
            files = [os.path.join(root, name)
                     for root, dirs, names in os.walk(folder_path)
                     for name in names
                     if name.endswith(".wav")]

            if len(files) != 0:
                self.insert_to_database(files)

    def insert_to_database(self, files):
        self.log_text.clear()
        self.add_folder_to_db_btn.setEnabled(False)
        self.add_to_db_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # self.log_text.clear()
        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)
        self.total = len(files)
        self.description_lbl.setText('{} / {}'.format(self.step, self.total))

        self.sql = InsertThread(self.db_file, files)
        self.sql.progress_signal.connect(self.step_progress)
        self.sql.finish_signal.connect(self.finish)
        self.sql.start()

    def step_progress(self):
        self.progress_bar.setValue(self.progress_bar.value()+1)
        self.step += 1
        self.description_lbl.setText('{} / {}'.format(self.step, self.total))
        self.update()

    def finish(self, insert_counter):
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        self.sql.stop()
        self.sql = None
        self.add_folder_to_db_btn.setEnabled(True)
        self.add_to_db_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.total = self.step = 0
        self.description_lbl.setText('')
        self.photo_frame.known_encodings = []
        self.photo_frame.dictionary_index = {}
        self.log_text.insertPlainText('عدد الأسطر المضافة: {}\n'.format(insert_counter))
        self.log_text.insertPlainText('-------------------------------------------------\n')
        self.log_text.insertPlainText('يجب تحميل المعلومات من ' + self.db_file + "\n")
        self.log_text.insertPlainText('-------------------------------------------------\n')

    def stop_inserting(self):
        for th in self.threads:
            th.stop()
