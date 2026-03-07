import sqlite3
import pandas as pd


def load_data():

    conn = sqlite3.connect("data/activities.db")

    df = pd.read_sql(
        """
        SELECT
        id,
        name,
        type,
        start_date,
        distance,
        moving_time
        FROM activities
        """,
        conn,
    )

    conn.close()

    if df.empty:
        return df

    # sanitize types
    df["date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["hours"] = df["moving_time"] / 3600
    df["km"] = df["distance"] / 1000

    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    df["location"] = df["name"]

    return df
