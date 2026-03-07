import sqlite3
import pandas as pd


def load_data():

    conn = sqlite3.connect("data/activities.db")

    df = pd.read_sql("""
        SELECT
            id,
            name,
            type,
            start_date,
            distance,
            moving_time,
            raw_json
        FROM activities
    """, conn)

    conn.close()

    if df.empty:
        return df

    # parse strava datetime
    df["date"] = pd.to_datetime(df["start_date"], errors="coerce")

    # eliminar timezone si existe
    try:
        df["date"] = df["date"].dt.tz_localize(None)
    except:
        pass

    df = df.dropna(subset=["date"])

    # metrics
    df["hours"] = df["moving_time"] / 3600
    df["km"] = df["distance"] / 1000

    # week key
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    df["location"] = df["name"]

    return df
