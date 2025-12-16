# consumer.py
import sqlite3
import time
from datetime import datetime

DB_NAME = "tasks.db"

CHECK_INTERVAL = 5
WORK_TIME = 30

def get_connection():
    return sqlite3.connect(DB_NAME)

def consume_task():
    conn = get_connection()
    cur = conn.cursor()

    # znajdź pierwsze pending
    cur.execute("""
        SELECT id FROM tasks
        WHERE status = 'pending'
        ORDER BY id
        LIMIT 1
    """)
    row = cur.fetchone()

    if row is None:
        conn.close()
        return None

    task_id = row[0]

    # oznacz jako in_progress
    cur.execute("""
        UPDATE tasks
        SET status = 'in_progress'
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

    print(f"[{datetime.now()}] Konsument pobiera zadanie {task_id}")
    return task_id

def finish_task(task_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tasks
        SET status = 'done'
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

def consumer_loop():
    print("Konsument wystartował...")

    while True:
        task_id = consume_task()

        if task_id is None:
            print("Brak zadań. Czekam...")
            time.sleep(CHECK_INTERVAL)
            continue

        print(f"Rozpoczynam pracę nad zadaniem {task_id} przez {WORK_TIME} sekund...")
        time.sleep(WORK_TIME)

        finish_task(task_id)
        print(f"Zadanie {task_id} zakończone.")

if __name__ == "__main__":
    consumer_loop()
