from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.uic import loadUiType

import os

from components.database import database_helper
import constants

db_dialog_class, _ = loadUiType(os.path.join(constants.bundle_dir, "ui//db_dialog.ui"))


class DbDialog(QDialog, db_dialog_class):
    def __init__(self, parent=None):
        super(DbDialog, self).__init__(parent)
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.handle_ui()
        self.handle_buttons()

        self.parent = parent
        self.folder = None

    def handle_ui(self):
        self.setFixedSize(635, 135)

    def handle_buttons(self):
        self.browse_btn.clicked.connect(self.browse)
        self.ok_btn.clicked.connect(self.ok)

    def browse(self):
        f = QFileDialog.getExistingDirectory(self, " اختر مجلد ")
        if f is not None:
            self.folder_path.setText(f)
            self.folder = f

    def ok(self):
        if self.folder is None:
            self.folder_path.setFocus()
            return
        if self.db_name.text() == '':
            self.db_name.setFocus()
            return
        db_file = self.folder + '/{}.db'.format(self.db_name.text())
        try:
            open(db_file, 'r')
            result = QMessageBox.question(self, "انتباه", "قاعدة البيانات موجودة، هل تريد استبدالها؟",
                                          QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                os.remove(db_file)
            else:
                self.db_name.setText('')
                return
        except FileNotFoundError:
            pass
        database_helper.create_db(db_file)
        self.parent.new_db_signal.emit(db_file)
        self.close()
