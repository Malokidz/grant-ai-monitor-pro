# app/db/database.py
import sqlite3
import os

DB_PATH = "grants.db"

def init_db():
    """Initializes the database with a new schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS seen_grants (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT,
            title TEXT,
            first_seen TEXT,
            score INTEGER,
            ai_reason TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized.")

def already_seen(opportunity_id):
    """Checks if a specific grant ID has been processed."""
    if not opportunity_id:
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM seen_grants WHERE opportunity_id = ?", (opportunity_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def mark_seen(opportunity_id, title, score, reason):
    """Records a processed grant in the database."""
    if not opportunity_id:
        print("⚠️ Warning: Attempted to mark a grant without an ID as seen. Skipping.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    from datetime import datetime
    c.execute("""
        INSERT OR REPLACE INTO seen_grants (opportunity_id, title, first_seen, score, ai_reason)
        VALUES (?, ?, ?, ?, ?)
    """, (opportunity_id, title, datetime.now().isoformat(), score, reason))
    conn.commit()
    conn.close()
