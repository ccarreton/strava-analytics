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

    sport = st.multiselect(
        "Sport",
        list(SPORT_GROUPS.keys()),
        default=list(SPORT_GROUPS.keys())
    )

    selected_types = []

    for s in sport:
        selected_types += SPORT_GROUPS[s]

    df = df[df["type"].isin(selected_types)]

    time_range = st.radio(
        "Time range",
        ["All time", "YTD", "2YTD", "4YTD"]
    )

    now = pd.Timestamp.now()

    if time_range == "YTD":

        cutoff = pd.Timestamp(now.year, 1, 1)
        df = df[df["date"] >= cutoff]

    elif time_range == "2YTD":

        cutoff = now - pd.DateOffset(years=2)
        df = df[df["date"] >= cutoff]

    elif time_range == "4YTD":

        cutoff = now - pd.DateOffset(years=4)
        df = df[df["date"] >= cutoff]

    return df
