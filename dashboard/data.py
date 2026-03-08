import sqlite3
import pandas as pd
import streamlit as st
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
    # DATE PARSING
    # -----------------------------

    if "start_date" in df.columns:

        df["date"] = pd.to_datetime(
            df["start_date"],
            errors="coerce",
            utc=True
        ).dt.tz_convert(None)

    else:

        df["date"] = pd.NaT

    # -----------------------------
    # BASIC METRICS
    # -----------------------------

    if "moving_time" in df.columns:
        df["hours"] = df["moving_time"] / 3600
    else:
        df["hours"] = 0

    if "distance" in df.columns:
        df["distance_km"] = df["distance"] / 1000
    else:
        df["distance_km"] = 0

    # -----------------------------
    # WEEK COLUMN
    # -----------------------------

    df["week"] = df["date"].dt.to_period("W").dt.start_time

    return df
