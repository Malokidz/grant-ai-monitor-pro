import sqlite3

conn = sqlite3.connect("grants.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS seen (
    link TEXT PRIMARY KEY
)
""")

def already_seen(link):
    cursor.execute("SELECT 1 FROM seen WHERE link=?", (link,))
    return cursor.fetchone()

def mark_seen(link):
    cursor.execute("INSERT OR IGNORE INTO seen VALUES (?)", (link,))
    conn.commit()
