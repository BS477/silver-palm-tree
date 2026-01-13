import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

DB_PATH = "results.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_url TEXT NOT NULL,
        count INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

class ResultIn(BaseModel):
    image_url: HttpUrl
    count: int
    timestamp: Optional[datetime] = None

class ResultOut(BaseModel):
    id: int
    image_url: HttpUrl
    count: int
    created_at: datetime

app = FastAPI(title="Service A - Results API")

@app.on_event("startup")
def startup():
    init_db()

@app.post("/results", status_code=201)
def post_result(payload: ResultIn):
    created_at = payload.timestamp.isoformat() if payload.timestamp else datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO results (image_url, count, created_at) VALUES (?, ?, ?)",
                (str(payload.image_url), payload.count, created_at))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return {"id": rowid, "image_url": str(payload.image_url), "count": payload.count, "created_at": created_at}

@app.get("/results", response_model=List[ResultOut])
def list_results():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, image_url, count, created_at FROM results ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "image_url": r[1], "count": r[2], "created_at": r[3]} for r in rows]