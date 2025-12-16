# producer.py
import sqlite3
from datetime import datetime

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_task():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    task = (
        datetime.now().isoformat(),
        "pending"
    )

    cur.execute(
        "INSERT INTO tasks (created_at, status) VALUES (?, ?)",
        task
    )

    conn.commit()
    conn.close()

    print("Dodano zadanie:", task)

if __name__ == "__main__":
    init_db()
    add_task()
