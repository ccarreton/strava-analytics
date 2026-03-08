import sqlite3
import pandas as pd
import streamlit as st
import json
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "activities.db"


@st.cache_data
def load_data():

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM activities", conn)
        conn.close()

    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # -----------------------------
    # DATE
    # -----------------------------

    df["date"] = pd.to_datetime(
        df["start_date"],
        errors="coerce",
        utc=True
    ).dt.tz_convert(None)

    df["week"] = df["date"].dt.to_period("W-MON").dt.start_time

    # -----------------------------
    # BASIC METRICS
    # -----------------------------

    df["hours"] = df["moving_time"] / 3600
    df["distance_km"] = df["distance"] / 1000

    # -----------------------------
    # INIT METRICS
    # -----------------------------

    df["max_watts"] = None
    df["avg_watts"] = None
    df["max_hr"] = None
    df["avg_hr"] = None

    # -----------------------------
    # PARSE RAW JSON
    # -----------------------------

    def parse_json(raw):

        if raw is None:
            return {}

        try:
            return json.loads(raw)
        except:
            return {}

    parsed = df["raw_json"].apply(parse_json)

    df["max_watts"] = parsed.apply(lambda x: x.get("max_watts"))
    df["avg_watts"] = parsed.apply(lambda x: x.get("average_watts"))
    df["max_hr"] = parsed.apply(lambda x: x.get("max_heartrate"))
    df["avg_hr"] = parsed.apply(lambda x: x.get("average_heartrate"))

    return df
