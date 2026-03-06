import sqlite3

conn = sqlite3.connect("data/activities.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    start_date TEXT,
    distance REAL,
    moving_time INTEGER,
    total_elevation_gain REAL
)
""")

conn.commit()
conn.close()

print("Database initialized")
