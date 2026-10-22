"""SQLite storage: users (login) and history (past diagnoses)."""
import hashlib
import json
import os
import sqlite3
from datetime import datetime

DB_FILE = "baking.db"
os.makedirs("uploads", exist_ok=True)


def _conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, salt BLOB, pw_hash BLOB)""")
        c.execute("""CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, created TEXT, product TEXT, temp REAL, minutes REAL,
            rod TEXT, tin TEXT, recipe TEXT, guesses TEXT,
            image_path TEXT, result TEXT)""")


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)


def register(username, password):
    salt = os.urandom(16)
    try:
        with _conn() as c:
            c.execute("INSERT INTO users(username, salt, pw_hash) VALUES (?,?,?)",
                      (username, salt, _hash(password, salt)))
        return True
    except sqlite3.IntegrityError:
        return False  # username already taken


def login(username, password):
    with _conn() as c:
        row = c.execute("SELECT id, salt, pw_hash FROM users WHERE username=?", (username,)).fetchone()
    if row and _hash(password, row[1]) == row[2]:
        return row[0]
    return None


def save_history(user_id, inp, image, result):
    path = ""
    if image is not None:
        path = f"uploads/{user_id}_{datetime.now():%Y%m%d%H%M%S}.png"
        image.convert("RGB").save(path)
    with _conn() as c:
        c.execute("""INSERT INTO history(user_id, created, product, temp, minutes, rod, tin,
                     recipe, guesses, image_path, result) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), inp["product"], inp["temp"],
                   inp["minutes"], inp["rod"], inp["tin"], inp["recipe"],
                   json.dumps(inp["guesses"]), path, json.dumps(result)))


def get_history(user_id):
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    return [dict(r) for r in rows]
