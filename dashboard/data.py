import sqlite3
import pandas as pd
import json


def load_data():

    conn = sqlite3.connect("data/strava.db")

    df = pd.read_sql("SELECT * FROM activities", conn)

    conn.close()

    # --- DATE PARSING ---
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # --- WEEK COLUMN ---
    df["week"] = df["date"].dt.to_period("W").dt.start_time

    # --- TRAINING HOURS ---
    df["hours"] = df["moving_time"] / 3600

    # --- DEFAULT COLUMNS (important for stability) ---
    df["max_watts"] = None
    df["avg_watts"] = None
    df["max_hr"] = None
    df["avg_hr"] = None

    # --- PARSE RAW JSON IF EXISTS ---
    if "raw_json" in df.columns:

        parsed = df["raw_json"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else {}
        )

        df["max_watts"] = parsed.apply(
            lambda x: x.get("max_watts")
        )

        df["avg_watts"] = parsed.apply(
            lambda x: x.get("average_watts")
            or x.get("weighted_average_watts")
        )

        df["max_hr"] = parsed.apply(
            lambda x: x.get("max_heartrate")
        )

        df["avg_hr"] = parsed.apply(
            lambda x: x.get("average_heartrate")
        )

    return df
