import logging
import os

from warriorfit.mom.message import Message
import sqlite3
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import json


class MessageContainer:
    """
    Thread-safe message container backed by SQLite.
    Public API preserved:
      - push_message(message: Message) -> int (returns DB id)
      - get_message() -> Optional[Message]
      - delete_message(message: Message) -> bool
    """
    def __init__(self, db_path: Path | str = Path("data/messages.db")):
        self._messages = queue.Queue()
        self._lock = threading.Lock()
        self._db_path = Path(db_path)
        self._init_db()
        self._logger = logging.getLogger(__name__)


    def push_message(self, message: Message) :
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")
        with self._lock:
            db_id = self._save_message_sqlite(message.to_json(), getattr(message, "timestamp", None))


    def get_message(self) -> Optional[Message]:
        with self._lock:
            if self._messages.empty():
                # Try hydrate from DB if memory is empty
                row = self._get_oldest_message_sqlite()
                if not row:
                    return None
                msg_id, content, ts = row
                msg = Message(content=json.loads(content))
                msg.timestamp = self._parse_ts(ts)
                setattr(msg, "_db_id", msg_id)
                self._messages.put(msg)
            # Peek head (without removing)
            return self._messages.queue[0] if not self._messages.empty() else None

    def delete_message(self, message: Message) -> bool:
        with self._lock:
            # Remove from in-memory queue if present
            removed_mem = False
            if message in self._messages.queue:
                self._messages.queue.remove(message)
                removed_mem = True
            # Remove from DB by attached id or content/timestamp fallback
            db_removed = False
            db_id = getattr(message, "_db_id", None)
            if db_id is not None:
                db_removed = self._delete_message_sqlite_by_id(int(db_id))
            else:
                db_removed = self._delete_message_sqlite_by_signature(json.dumps(message.content.__dict__), message.timestamp)
            return removed_mem or db_removed

    # Internal: DB setup and operations
    def _conn(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path.as_posix())
        return conn

    def _init_db(self):
        # Check if the SQLite database file exists
        if not os.path.exists(self._db_path):
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._db_path)
            conn.close()

        if not self._check_table(self._db_path):
            with self._conn() as conn:         
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                    """
                )
                conn.commit()

    def _check_table(self,db_path, table_name="messages"):
        con=None
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if the table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,)
            )
            result = cursor.fetchone()

            if result:
                exists = True
            else:
                exists = False

        except sqlite3.Error as e:
            self._logger.error(f"SQLite error: {e}")
            exists = False

        finally:
            if 'conn' in locals():
                conn.close()

        return exists

    def _save_message_sqlite(self, content: str, timestamp: Optional[datetime] = None) -> int:
        ts = (timestamp or datetime.utcnow()).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO messages (content, timestamp) VALUES (?, ?)",
                (content, ts),
            )
            conn.commit()
            return cur.lastrowid

    def _get_oldest_message_sqlite(self) -> Optional[Tuple[int, str, str]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, content, timestamp FROM messages ORDER BY id ASC LIMIT 1"
            )
            row = cur.fetchone()
            return row if row else None

    def _delete_message_sqlite_by_id(self, msg_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            conn.commit()
            return cur.rowcount > 0

    def _delete_message_sqlite_by_signature(self, content: str, timestamp: Optional[datetime]) -> bool:
        ts = (timestamp or datetime.utcnow()).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM messages WHERE content = ? AND timestamp = ?",
                (content, ts),
            )
            conn.commit()
            return cur.rowcount > 0

    @staticmethod
    def _parse_ts(ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.utcnow()





