import sqlite3


def create_db(db_file):
    connection = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
    c = connection.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS SOUNDS (FILENAME STRING PRIMARY KEY, SPEAKER STRING, EMBEDDINGS ARRAY);")
    connection.commit()
    connection.close()


def check_db(db_file):
    try:
        open(db_file, 'r')
        return
    except FileNotFoundError:
        create_db(db_file)
        return


def check_db_cols(db_file):
    connection = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
    c = connection.cursor()
    try:
        c.execute('SELECT FILENAME, SPEAKER, EMBEDDINGS FROM SOUNDS LIMIT 0')
        connection.close()
        return True
    except sqlite3.OperationalError:
        return False


def is_empty_db(db_file):
    connection = sqlite3.connect(db_file)
    c = connection.cursor()
    c.execute("SELECT COUNT(*) FROM SOUNDS")
    total = c.fetchone()[0]
    connection.close()
    if total == 0:
        return True
    else:
        return False
