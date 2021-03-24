from PyQt5.QtCore import QThread, pyqtSignal

import shutil
import os
import sqlite3
import numpy as np
# import webrtcvad
from webrtcvad_package import webrtcvad
from core.wav_reader import get_fft_spectrum
from core.webrtc_vad import read_wave, frame_generator, vad_collector, write_wave
import constants as c


class LoadThread(QThread):
    set_max_progress_signal = pyqtSignal(int)
    progress_signal = pyqtSignal()
    finish_signal = pyqtSignal(int)

    def __init__(self, parent, db_file, files):
        super().__init__()

        self.parent = parent
        self.db_file = db_file
        self.files = files

        self.is_running = True

    def run(self):
        embeddings = []
        connection = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_COLNAMES)
        cur = connection.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM SOUNDS")
            total = cur.fetchone()[0]
            self.set_max_progress_signal.emit(total)
            cur.execute("SELECT FILENAME, SPEAKER, EMBEDDINGS FROM SOUNDS")
            for name, speaker, vec in cur:
                if not self.is_running:
                    connection.close()
                    return
                self.files[name] = speaker
                embeddings.append(eval(vec))
                self.progress_signal.emit()
        except sqlite3.OperationalError:
            pass
        connection.close()
        c.data = np.array(embeddings)
        self.progress_signal.emit()
        self.finish_signal.emit(len(embeddings))

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()


class InsertThread(QThread):
    progress_signal = pyqtSignal()
    finish_signal = pyqtSignal(int)

    def __init__(self, db, files):
        super(InsertThread, self).__init__()
        self.db = db
        self.files = files

        self.is_running = True

    def run(self):
        connection = sqlite3.Connection(self.db, detect_types=sqlite3.PARSE_COLNAMES)
        cursor = connection.cursor()
        counter = 0
        insert_counter = 0
        update_counter = 0
        for file in self.files:
            if not self.is_running:
                break

            name = os.path.basename(file).split('.')[0]
            parent_dir = os.path.dirname(file)
            speaker = os.path.basename(parent_dir)

            chunks_dir = os.path.join(parent_dir, '{}_chunks'.format(name))
            os.mkdir(chunks_dir)

            try:
                audio, sample_rate = read_wave(file)
                vad = webrtcvad.Vad(3)
                frames = frame_generator(30, audio, sample_rate)
                frames = list(frames)
                segments = vad_collector(sample_rate, 30, 300, vad, frames)
            except AssertionError:
                shutil.rmtree(chunks_dir)
                try:
                    x = get_fft_spectrum(file, c.buckets)
                    with c.graph.as_default():
                        embs = np.squeeze(c.model.predict(x.reshape(1, *x.shape, 1)))
                except:
                    continue
                try:
                    cursor.execute("INSERT INTO SOUNDS (FILENAME, SPEAKER, EMBEDDINGS) VALUES (?, ?, ?)",
                                   (name, speaker, str(embs.tolist())))
                    insert_counter += 1
                except sqlite3.IntegrityError:
                    continue
                continue

            for i, segment in enumerate(segments):
                # path = '‪chunk-%002d.wav' % (i,)
                path = os.path.join(chunks_dir, '‪{}_chunk-%002d.wav'.format(name) % (i,))
                print(' Writing %s' % (path,))
                write_wave(path, segment, sample_rate)
                basename = os.path.basename(path).split('.')[0]

                try:
                    x = get_fft_spectrum(path, c.buckets)
                    with c.graph.as_default():
                        embs = np.squeeze(c.model.predict(x.reshape(1, *x.shape, 1)))
                except:
                    break
                try:
                    cursor.execute("INSERT INTO SOUNDS (FILENAME, SPEAKER, EMBEDDINGS) VALUES (?, ?, ?)",
                                   (basename, speaker, str(embs.tolist())))
                    insert_counter += 1
                except sqlite3.IntegrityError:
                    # cursor.execute("UPDATE SOUNDS SET SPEAKER=?, EMBEDDINGS=? WHERE FILENAME=?",
                    #              (str(embs.tolist()), speaker, name))
                    break
                counter += 1
            if counter >= 1000:
                connection.commit()
            shutil.rmtree(chunks_dir)
            self.progress_signal.emit()
        connection.commit()
        connection.close()
        self.finish_signal.emit(insert_counter)

    def stop(self):
        self.quit()
        self.wait()
