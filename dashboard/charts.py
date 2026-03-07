import plotly.graph_objects as go
import numpy as np
from config import TARGET_WEEKLY_HOURS, ROLLING_WINDOW


def weekly_chart(weekly):

    colors = np.where(weekly["hours"] < TARGET_WEEKLY_HOURS, "#ff4d4d", "#4A7DFF")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weekly["week"],
            y=weekly["hours"],
            name="Weekly hours",
            marker_color=colors,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["rolling"],
            name="4 week avg",
            line=dict(width=3),
        )
    )

    fig.add_hline(
        y=TARGET_WEEKLY_HOURS,
        line_dash="dash",
        line_color="green",
        annotation_text="target",
    )

    fig.update_layout(
        height=280,
        margin=dict(l=5, r=5, t=30, b=5),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center",
        ),
    )

    fig.update_xaxes(nticks=6)

    return fig
