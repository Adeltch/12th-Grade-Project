import random
import sqlite3

DB_FILE = "ctf.db"

# Sample fake data
PLAYER_NAMES = [
    "alice", "bob", "charlie", "david", "eve", "frank", "grace",
    "henry", "israel", "jack", "kate", "leo", "maya", "nina",
    "oscar", "paul", "queen", "ryan", "sarah", "tom", "uri",
    "victor", "will", "xena", "yossi", "zoe"
]

CTF_NAMES = [
    "intro_ctf",
    "network_ctf",
    "crypto_ctf",
    "forensics_ctf",
    "web_ctf",
    "reverse_ctf"
]


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    return conn, cursor


def generate_fake_data(amount=100):
    conn, cursor = get_connection()

    inserted = 0

    for i in range(amount):
        # Create unique player name
        player_name = f"{random.choice(PLAYER_NAMES)}_{i}"

        # Random CTF
        ctf_name = random.choice(CTF_NAMES)

        # Random progress values
        current_stage_id = random.randint(1, 10)
        score = random.randint(0, 1000)
        used_hint = random.randint(0, 1)
        attempts = random.randint(1, 20)
        total_time = random.randint(60, 10000)

        # Insert player
        cursor.execute("""
        INSERT OR IGNORE INTO players (name, last_played_ctf)
        VALUES (?, ?)
        """, (player_name, ctf_name))

        # Insert progress
        cursor.execute("""
        INSERT OR REPLACE INTO player_progress
        (player_name, ctf_name, current_stage_id,
         score, used_hint, attempts, total_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player_name,
            ctf_name,
            current_stage_id,
            score,
            used_hint,
            attempts,
            total_time
        ))

        inserted += 1

    conn.commit()
    conn.close()

    print(f"Inserted {inserted} fake rows successfully.")


if __name__ == "__main__":
    generate_fake_data(100)