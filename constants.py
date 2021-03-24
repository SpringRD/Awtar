import os
import sys
import numpy as np

from core.model import vggvox_model
import tensorflow as tf

from core.scoring import build_buckets


bundle_dir = parent_dir = config_path = db_path = db_file =     = None
data = np.ndarray

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    parent_dir = os.path.dirname(sys.executable)
    # parent_dir = os.path.dirname(bundle_dir)
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = bundle_dir

config_path = os.path.join(parent_dir, "awtar_config")
if not os.path.isdir(config_path):
    os.makedirs(config_path)

db_path = os.path.join(config_path, "db")
try:
    f = open(db_path, 'r')
    db_file = f.readline()
    if not os.path.exists(db_file):
        db_file = ''
except FileNotFoundError:
    f = open(db_path, 'w')
    db_file = ''
f.close()

# Signal processing
SAMPLE_RATE = 16000
PREEMPHASIS_ALPHA = 0.97
FRAME_LEN = 0.025
FRAME_STEP = 0.01
NUM_FFT = 512
BUCKET_STEP = 0.1
MAX_SEC = 4

# Model
WEIGHTS_FILE = os.path.join(bundle_dir, "model/weights.h5")
COST_METRIC = "cosine"  # euclidean or cosine
INPUT_SHAPE = (NUM_FFT, None, 1)

model = vggvox_model()
model.load_weights(WEIGHTS_FILE)
model.summary()
graph = tf.get_default_graph()

buckets = build_buckets(MAX_SEC, BUCKET_STEP, FRAME_STEP)
