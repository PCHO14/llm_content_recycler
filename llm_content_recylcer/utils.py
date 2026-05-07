import dataclasses
import sqlite3
from pathlib import Path


@dataclasses.dataclass
class VideoData:
    db_row_idx: int
    video_id: str
    url: str
    title: str
    transcription: str
    tag: str


def read_db(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('PRAGMA table_info(videos)')
    cursor.execute('SELECT transcription FROM videos')
    rows = cursor.fetchall()
    return rows[0][0]


def get_row_by_index(db_path: Path, index: int) -> VideoData | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos LIMIT 1 OFFSET ?', (index,))
    row = cursor.fetchone()
    conn.close()
    if row:
        db_row_id, video_id, url, title, transcription, tag = row
        return VideoData(db_row_id, video_id, url, title, transcription, tag)
    return None
