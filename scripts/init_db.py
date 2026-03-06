import sqlite3

conn = sqlite3.connect("data/activities.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    start_date TEXT,
    type TEXT,
    name TEXT,
    distance REAL,
    moving_time INTEGER,
    total_elevation_gain REAL,
    raw_json TEXT
)
""")

# índice para acelerar filtros y ingestión incremental
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_start_date
ON activities(start_date)
""")

conn.commit()
conn.close()

print("Database initialized")
