from PyQt5.QtWidgets import QFrame, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.uic import loadUiType

import os
import numpy as np
from scipy.spatial.distance import cdist
from operator import itemgetter
from core.wav_reader import get_fft_spectrum

import constants


detection_frame_class, _ = loadUiType(os.path.join(constants.bundle_dir, "ui//detection_frame.ui"))


class DetectionFrame(QFrame, detection_frame_class):

    def __init__(self):
        super(DetectionFrame, self).__init__()
        QFrame.__init__(self)
        self.setupUi(self)
        self.handle_ui()
        self.handle_buttons()

        self.sound = self.db_file = None

        self.files = {}
        self.status = True

        self.detect_thread = None

    def handle_ui(self):
        # self.tableWidget.setFixedWidth(900)
        pass

    def handle_buttons(self):
        self.select_image_btn.clicked.connect(self.select_sound)
        self.detect_image_btn.clicked.connect(self.detect_sound)

    def from_db_frame(self, db_file, status):
        self.db_file = db_file
        self.status = status
        self.db_path_lbl.setText(self.db_file)

    def select_sound(self):
        target_path = QFileDialog.getOpenFileName(parent=self, caption='اختر ملف صوتي', filter='Sounds Files (*.wav)')
        if target_path[0] != '':
            self.sound = target_path[0]

            self.sound_path.setText(self.sound)

            self.tableWidget.setRowCount(0)

            self.detect_image_btn.setEnabled(True)

    def detect_sound(self):

        if self.db_file is None or self.db_file == '':
            QMessageBox.information(self, "انتباه", "لا يوجد قاعدة بيانات مربوطة")
            return

        if len(self.files) == 0:
            QMessageBox.information(self, "تحميل المعلومات", "الرجاء تحميل المعلومات من قاعدة البيانات")
            return

        if not self.status:
            QMessageBox.information(self, "انتباه", "قاعدة البيانات المربوطة غير صحيحة")
            return

        rows = self.alters_spin.value()
        if rows > len(self.files):
            rows = len(self.files)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(rows + 1)

        try:
            x = get_fft_spectrum(self.sound, constants.buckets)
            with constants.graph.as_default():
                embs = np.squeeze(constants.model.predict(x.reshape(1, *x.shape, 1)))
        except:
            QMessageBox.information(self, "انتباه", "هناك خطأ في الملف الصوتي")
            return

        embs_array = np.array([embs.tolist()])

        distances = cdist(embs_array, constants.data, metric=constants.COST_METRIC)
        dis = distances.tolist()
        # small = nsmallest(3, dis[0])
        result_dict = {}
        i = 0
        for file in self.files:
            result_dict[file] = dis[0][i]
            i += 1
        sorted_result = sorted(result_dict.items(), key=itemgetter(1))

        self.tableWidget.setItem(0, 0, QTableWidgetItem('Speaker'))
        self.tableWidget.item(0, 0).setBackground(QColor(240, 240, 240))
        self.tableWidget.setItem(0, 1, QTableWidgetItem('Accuracy'))
        self.tableWidget.item(0, 1).setBackground(QColor(240, 240, 240))
        j = 0
        for row in range(1, rows + 1):
            name = sorted_result[j][0]
            speaker = self.files[name]
            accuracy = '{}%'.format(float("{0:.2f}".format(100 - (100 * sorted_result[j][1]))))

            # self.tableWidget.setItem(row, 0, QTableWidgetItem(name))
            # self.tableWidget.item(row, 0).setBackground(QColor(200, 85, 100))
            self.tableWidget.setItem(row, 0, QTableWidgetItem(str(speaker)))
            # self.tableWidget.setItem(row, 1, QTableWidgetItem(str(sorted_result[j][1])))
            self.tableWidget.item(row, 0).setBackground(QColor(170, 240, 240))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(accuracy))
            self.tableWidget.item(row, 1).setBackground(QColor(170, 240, 240))
            self.tableWidget.update()
            self.tableWidget.repaint()
            j += 1
