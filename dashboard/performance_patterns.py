import sqlite3
import pandas as pd
from datetime import timedelta
import os

DB_PATH = "data/activities.db"

DISTANCE_BUCKETS = {
    "5K": (4900, 5100),
    "10K": (9500, 10500),
    "21K": (20000, 22000),
}

WINDOW_DAYS = 28  # 4 semanas


def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def get_top_activities(conn, min_dist, max_dist, limit=5):
    query = """
        SELECT id, start_date, distance, moving_time
        FROM activities
        WHERE type = 'Run'
          AND distance BETWEEN ? AND ?
        ORDER BY (moving_time * 1.0 / distance) ASC
        LIMIT ?
    """
    return pd.read_sql(query, conn, params=(min_dist, max_dist, limit))


def get_weekly_km(conn, start_date, end_date):

    # 🔹 FIX CLAVE: convertir fechas a string
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")

    query = """
        SELECT
            date(start_date) as day,
            distance / 1000.0 as km
        FROM activities
        WHERE type = 'Run'
          AND date(start_date) BETWEEN date(?) AND date(?)
    """

    df = pd.read_sql(query, conn, params=(start_date, end_date))

    if df.empty:
        return pd.DataFrame(columns=["week_offset", "km"])

    df["day"] = pd.to_datetime(df["day"])

    # calcular semana relativa
    max_day = df["day"].max()
    df["week_offset"] = ((df["day"] - max_day).dt.days // 7)

    weekly = (
        df.groupby("week_offset")["km"]
        .sum()
        .reset_index()
    )

    return weekly


def compute_patterns(conn):
    all_results = []

    for label, (min_d, max_d) in DISTANCE_BUCKETS.items():
        top_df = get_top_activities(conn, min_d, max_d)

        if top_df.empty:
            continue

        pattern_accumulator = []

        for _, row in top_df.iterrows():
            race_date = pd.to_datetime(row["start_date"])
            start_window = race_date - timedelta(days=WINDOW_DAYS)

            weekly = get_weekly_km(conn, start_window, race_date)

            if weekly.empty:
                continue

            weekly["distance"] = label
            pattern_accumulator.append(weekly)

        if not pattern_accumulator:
            continue

        combined = pd.concat(pattern_accumulator)

        avg_pattern = (
            combined.groupby(["distance", "week_offset"])["km"]
            .mean()
            .reset_index()
        )

        all_results.append(avg_pattern)

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results)


def save_patterns(conn, df):
    conn.execute("DROP TABLE IF EXISTS performance_patterns")
    df.to_sql("performance_patterns", conn, index=False)

def load_patterns():
    import sqlite3
    import pandas as pd

    conn = sqlite3.connect("data/activities.db")

    try:
        df = pd.read_sql("SELECT * FROM performance_patterns", conn)
    except Exception:
        df = pd.DataFrame()

    conn.close()

    return df
    
def main():
    conn = get_connection()

    patterns = compute_patterns(conn)

    if patterns.empty:
        print("No data to compute patterns.")
        return

    save_patterns(conn, patterns)

    print("Patterns computed and saved.")


if __name__ == "__main__":
    main()
