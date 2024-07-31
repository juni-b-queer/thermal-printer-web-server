import sqlite3

DB_PATH='/home/pi/WebServer/data.db'

def setup_sqlite():
    conn = sqlite3.connect(DB_PATH)  # Creates `data.db` file if it doesn't exist
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS print_queue
              (id INTEGER PRIMARY KEY AUTOINCREMENT, 
               timestamp TEXT DEFAULT (datetime('now','localtime')), 
               filehash TEXT NOT NULL, 
               printed INTEGER DEFAULT 0)
              ''')  # Creates the table if it does not exist
    conn.commit()
    conn.close()


def insert_to_db(filehash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO print_queue (filehash) VALUES (?)", (filehash,))
    conn.commit()
    conn.close()


def count_unprinted_rows():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM print_queue WHERE printed=0")
    count = c.fetchone()[0]
    conn.close()
    return count

def count_printed_rows():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM print_queue WHERE printed=1")
    count = c.fetchone()[0]
    conn.close()
    return count

def count_unprinted_before_hash(filehash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM print_queue WHERE filehash=?", (filehash,))
    row_id = c.fetchone()
    if row_id is None:
        return None  # or raise an exception, or whatever you prefer
    c.execute("SELECT COUNT(*) FROM print_queue WHERE printed=0 AND id<?", row_id)
    count = c.fetchone()[0]
    conn.close()
    return count


def hash_exists(filehash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM print_queue WHERE filehash=?", (filehash,))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def is_printed(filehash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT printed FROM print_queue WHERE filehash=?", (filehash,))
    printed = c.fetchone()
    conn.close()
    if printed is None:
        return False  # or raise an exception, or whatever you prefer
    return printed[0] == 1


def get_unprinted_hashes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filehash FROM print_queue WHERE printed=0 ORDER BY timestamp ASC LIMIT 10")
    hashes = [row[0] for row in c.fetchall()]
    conn.close()
    return hashes
    
def get_printed_hashes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filehash FROM print_queue WHERE printed=1 ORDER BY timestamp DESC LIMIT 10")
    hashes = [row[0] for row in c.fetchall()]
    conn.close()
    return hashes

def get_next_unprinted_hash():
    """Return the next filehash in the print queue that has not been printed yet."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filehash FROM print_queue WHERE printed=0 ORDER BY timestamp ASC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def mark_as_printed(filehash):
    """Set the printed flag to True for the specified filehash in the print queue."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE print_queue SET printed=1 WHERE filehash=?", (filehash,))
    conn.commit()
    conn.close()


def get_timestamp(filehash):
    """Return the timestamp for the specified filehash in the print queue."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp FROM print_queue WHERE filehash=?", (filehash,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
