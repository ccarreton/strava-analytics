import streamlit as st
import pandas as pd


SPORT_GROUPS = {

    "Run": ["Run"],
    "Ride": ["Ride", "VirtualRide"],
    "Swim": ["Swim"],
    "Strength": ["WeightTraining", "Workout"],
    "Outdoor": ["Hike", "Walk"]

}


def apply_filters(df):

    st.markdown("### Filters")

    # -------- SPORT FILTER --------

    sport = st.multiselect(
        "Sport",
        list(SPORT_GROUPS.keys()),
        default=list(SPORT_GROUPS.keys())
    )

    selected_types = []

    for s in sport:
        selected_types += SPORT_GROUPS[s]

    if "type" in df.columns:
        df = df[df["type"].isin(selected_types)]

    # -------- TIME FILTER --------

    time_range = st.radio(
        "Time range",
        [
            "Last 6 months",
            "YTD",
            "2YTD",
            "4YTD",
            "All time"
        ]
    )

    now = pd.Timestamp.now()

    if time_range == "Last 6 months":

        cutoff = now - pd.DateOffset(months=6)
        df = df[df["date"] >= cutoff]

    elif time_range == "YTD":

        cutoff = pd.Timestamp(year=now.year, month=1, day=1)
        df = df[df["date"] >= cutoff]

    elif time_range == "2YTD":

        cutoff = now - pd.DateOffset(years=2)
        df = df[df["date"] >= cutoff]

    elif time_range == "4YTD":

        cutoff = now - pd.DateOffset(years=4)
        df = df[df["date"] >= cutoff]

    return df
