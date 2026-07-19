import sqlite3
import json
import datetime
from utils.sync_manager import DB_PATH
from typing import List, Dict, Any

def init_chat_db():
    """Create the chat history table in the SQLite database if it does not exist."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                chart_data TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

def save_chat_message(project_id: str, role: str, content: str, chart_data: Dict[str, Any] = None):
    """Save a chat message to the SQLite database."""
    init_chat_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (project_id, role, content, chart_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id, role, content,
            json.dumps(chart_data) if chart_data else None,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
    finally:
        conn.close()

def get_chat_history(project_id: str) -> List[Dict[str, Any]]:
    """Retrieve chat history from SQLite for a given project workspace."""
    init_chat_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    messages = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, chart_data, timestamp 
            FROM chat_history 
            WHERE project_id = ? 
            ORDER BY id ASC
        """, (project_id,))
        rows = cursor.fetchall()
        for row in rows:
            msg = dict(row)
            msg["chart_data"] = json.loads(msg["chart_data"]) if msg["chart_data"] else None
            messages.append(msg)
    except Exception:
        pass
    finally:
        conn.close()
    return messages

def clear_chat_history(project_id: str):
    """Clear chat history from SQLite for a project."""
    init_chat_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE project_id = ?", (project_id,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
