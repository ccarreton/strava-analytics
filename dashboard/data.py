import sqlite3
import pandas as pd
import json
import os
import streamlit as st


DB_PATH = "data/activities.db"


def load_data():

    if not os.path.exists(DB_PATH):
        st.error(f"Database not found: {DB_PATH}")
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql("SELECT * FROM activities", conn)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

    conn.close()

    # -------------------------
    # DATE HANDLING
    # -------------------------

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    elif "start_date" in df.columns:
        df["date"] = pd.to_datetime(df["start_date"], errors="coerce")

    elif "start_date_local" in df.columns:
        df["date"] = pd.to_datetime(df["start_date_local"], errors="coerce")

    else:
        st.error("No date column found in database.")
        return pd.DataFrame()

    # -------------------------
    # WEEK COLUMN
    # -------------------------

    df["week"] = df["date"].dt.to_period("W").dt.start_time

    # -------------------------
    # TRAINING HOURS
    # -------------------------

    if "moving_time" not in df.columns:
        st.error("Column 'moving_time' missing.")
        return pd.DataFrame()

    df["hours"] = df["moving_time"] / 3600

    # -------------------------
    # DEFAULT METRIC COLUMNS
    # -------------------------

    df["max_watts"] = None
    df["avg_watts"] = None
    df["max_hr"] = None
    df["avg_hr"] = None

    # -------------------------
    # PARSE RAW JSON
    # -------------------------

    if "raw_json" in df.columns:

        parsed = df["raw_json"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else {}
        )

        df["max_watts"] = parsed.apply(
            lambda x: x.get("max_watts")
        )

        df["avg_watts"] = parsed.apply(
            lambda x: x.get("average_watts") or x.get("weighted_average_watts")
        )

        df["max_hr"] = parsed.apply(
            lambda x: x.get("max_heartrate")
        )

        df["avg_hr"] = parsed.apply(
            lambda x: x.get("average_heartrate")
        )

    df = df[df["date"] >= "2022-01-01"]
    return df
