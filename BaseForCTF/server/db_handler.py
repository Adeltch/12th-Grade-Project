__author__ = "Adel Tchernitsky"


import sqlite3
from datetime import datetime


DB_FILE = "server//ctf.db"


# Connection to DB
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    return conn, cursor


# Initialization of both DataBases
def init_db():
    conn, cursor = get_connection()

    # Create players table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
        name TEXT PRIMARY KEY,
        last_played_ctf TEXT)
        """) # TODO: idk if I want to store last_played_ctf...

    # Create table client progress per CTF
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_progress (
        player_name TEXT,
        ctf_name TEXT,
        current_stage_id INTEGER,
        score INTEGER,
        used_hint INTEGER,
        attempts INTEGER,
        total_time INTEGER,

        PRIMARY KEY (player_name, ctf_name)
    )
    """)

    conn.commit()
    conn.close()


def create_player(name):
    conn, cursor = get_connection()

    cursor.execute("""
    INSERT OR IGNORE INTO players (name)
    VALUES (?)
    """, (name,))

    conn.commit()
    conn.close()


def get_player(name):
    conn, cursor = get_connection()

    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {"name": row[0], "last_played_ctf": row[1]}


def update_last_ctf(player_name, ctf_name):
    conn, cursor = get_connection()

    cursor.execute("""
    UPDATE players
    SET last_played_ctf = ?
    WHERE name = ?
    """, (ctf_name, player_name))

    conn.commit()
    conn.close()


def get_progress(player_name, ctf_name):
    conn, cursor = get_connection()

    cursor.execute("""
    SELECT current_stage_id, score, used_hint, attempts, total_time
    FROM player_progress
    WHERE player_name = ? AND ctf_name = ?
    """, (player_name, ctf_name))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "current_stage_id": row[0],
        "score": row[1],
        "used_hint": bool(row[2]),
        "attempts": row[3],
        "total_time": row[4]
    }


def get_all_progress(player_name):
    conn, cursor = get_connection()

    cursor.execute("""
    SELECT ctf_name, current_stage_id, score, total_time
    FROM player_progress
    WHERE player_name = ?
    """, (player_name,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "ctf_name": row[0],
            "current_stage_id": row[1],
            "score": row[2],
            "total_time": row[3]
        }
        for row in rows
    ]


def save_progress(player_name, ctf_name, current_stage_id, score, used_hint, attempts, total_time):
    conn, cursor = get_connection()

    cursor.execute("""
    INSERT OR REPLACE INTO player_progress
    (player_name, ctf_name, current_stage_id, score, used_hint, attempts, total_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        player_name,
        ctf_name,
        current_stage_id,
        score,
        int(used_hint),
        attempts,
        int(total_time)
    ))

    conn.commit()
    conn.close()


def create_progress(player_name, ctf_name, first_stage_id):
    conn, cursor = get_connection()

    cursor.execute("""
    INSERT INTO player_progress
    (player_name, ctf_name, current_stage_id, score, used_hint, attempts, total_time)
    VALUES (?, ?, ?, 0, 0, 0, 0)
    """, (player_name, ctf_name, first_stage_id))

    conn.commit()
    conn.close()


# TODO - is this needed?
def update_player_time(player):
    if player.session_start_time:
        elapsed = (datetime.now() - player.session_start_time).total_seconds()
        player.total_time += int(elapsed)
        player.session_start_time = datetime.now()
