import sqlite3
from pathlib import Path


def read_db(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('PRAGMA table_info(videos)')
    cursor.execute('SELECT transcription FROM videos')
    rows = cursor.fetchall()
    return rows[0][0]
