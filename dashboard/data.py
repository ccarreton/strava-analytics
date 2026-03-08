import sqlite3
import pandas as pd
import json
import os
import streamlit as st


DB_PATH = "data/strava.db"


def load_data():

    # ----------------------------
    # CHECK DATABASE EXISTS
    # ----------------------------

    if not os.path.exists(DB_PATH):

        st.error(f"Database not found: {DB_PATH}")
        return pd.DataFrame()

    try:

        conn = sqlite3.connect(DB_PATH)

        df = pd.read_sql("SELECT * FROM activities", conn)

        conn.close()

    except Exception as e:

        st.error(f"Database error: {e}")
        return pd.DataFrame()

    # ----------------------------
    # DATE PARSING
    # ----------------------------

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ----------------------------
    # WEEK
    # ----------------------------

    df["week"] = df["date"].dt.to_period("W").dt.start_time

    # ----------------------------
    # TRAINING HOURS
    # ----------------------------

    df["hours"] = df["moving_time"] / 3600

    # ----------------------------
    # DEFAULT METRIC COLUMNS
    # ----------------------------

    df["max_watts"] = None
    df["avg_watts"] = None
    df["max_hr"] = None
    df["avg_hr"] = None

    # ----------------------------
    # PARSE RAW JSON
    # ----------------------------

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

    return df
