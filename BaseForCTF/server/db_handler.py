__author__ = "Adel Tchernitsky"


import sqlite3
from datetime import datetime
import os
import hashlib
import secrets


DB_FILE = "server//ctf.db"
PEPPER = "my_super_secret_pepper_is_Taylor_Swift_<3" 


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
        password_hash TEXT,
        salt TEXT,
        last_played_ctf TEXT)
        """)

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


def create_player(name, password):
    """
    Create a new player in the database
    """
    salt, password_hash = hash_password(password)

    conn, cursor = get_connection()
    cursor.execute("""
    INSERT OR IGNORE INTO players (name, password_hash, salt)
    VALUES (?, ?, ?)
    """, (name, password_hash, salt)
    )

    conn.commit()
    conn.close()


def get_player(name):
    """
    Retrieve player information from database
    :param name: Player username
    :return: Dict with player data or None if not found
    """
    conn, cursor = get_connection()

    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {"name": row[0], "password_hash": row[1], "salt": row[2], "last_played_ctf": row[3]}


def authenticate_player(name, password):
    """
    Authenticate a player by checking username and password hash
    :param name: Player username
    :param password: Plain text password
    :return: True if authentication successful, False otherwise
    """
    player = get_player(name)
    if not player:
        return False

    return verify_password(password, player["salt"], player["password_hash"])


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


def hash_password(password, salt=None):
    """
    Hash password using:
    - PBKDF2
    - SHA256
    - Salt
    - Pepper
    """
    if salt is None:
        salt = secrets.token_bytes(16)

    peppered_password = (password + PEPPER).encode()

    password_hash = hashlib.pbkdf2_hmac("sha256", peppered_password, salt, 100_000)
    return salt.hex(), password_hash.hex()


def verify_password(password, stored_salt, stored_hash):
    salt = bytes.fromhex(stored_salt)
    _, new_hash = hash_password(password, salt)
    return new_hash == stored_hash