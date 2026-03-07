import pandas as pd
import streamlit as st


def apply_filters(df):

    # asegurar columna date
    if "date" not in df.columns:
        return df

    # convertir SIEMPRE a datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # eliminar fechas corruptas
    df = df.dropna(subset=["date"])

    with st.expander("Filters", expanded=True):

        sports = st.multiselect(
            "Sport",
            sorted(df["type"].dropna().unique()),
            default=sorted(df["type"].dropna().unique())
        )

        time_range = st.radio(
            "Time range",
            ["All time", "YTD", "2YTD", "4YTD"]
        )

    # filtro deporte
    if sports:
        df = df[df["type"].isin(sports)]

    # si ya no hay datos, salimos
    if df.empty:
        return df

    now = pd.Timestamp.now()

    if time_range == "YTD":
        cutoff = now - pd.DateOffset(months=12)

    elif time_range == "2YTD":
        cutoff = now - pd.DateOffset(years=2)

    elif time_range == "4YTD":
        cutoff = now - pd.DateOffset(years=4)

    else:
        cutoff = None

    if cutoff is not None:

        # aseguramos datetime otra vez
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # eliminamos posibles NaT
        df = df[df["date"].notna()]

        df = df.loc[df["date"] >= cutoff]

    return df
