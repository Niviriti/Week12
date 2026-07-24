# pages/03_demand.py
# TASK 3 — third page: demand analysis
# Colour type: highlight palette — blue for the selected/high-demand area,
# light grey for comparison areas.

import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, sidebar_filters

# Shared data and filters from pages 1 and 2
df, p95 = load_data()
filtered = sidebar_filters(df, p95)

st.title("Where is guest demand strongest?")
st.caption(
    f"Demand indicators for {len(filtered):,} filtered London Airbnb listings"
)

if filtered.empty:
    st.warning("No listings match the selected filters.")
    st.stop()

# Prepare neighbourhood-level demand indicators
demand = (
    filtered.groupby("neighbourhood", as_index=False)
    .agg(
        listings=("neighbourhood", "size"),
        total_reviews=("number_of_reviews", "sum"),
        avg_reviews_per_month=("reviews_per_month", "mean"),
        median_availability=("availability_365", "median"),
        median_price=("price", "median"),
    )
)

# Demand proxy:
# 70% review activity + 30% inverse availability.
# Higher reviews and fewer available days suggest stronger guest demand.
demand["demand_score"] = (
    demand["avg_reviews_per_month"].rank(pct=True) * 0.70
    + (1 - demand["median_availability"].rank(pct=True)) * 0.30
) * 100

demand = demand.sort_values("demand_score", ascending=False)

# Persist this page's neighbourhood widget
available_hoods = demand["neighbourhood"].tolist()

if "demand_hood" not in st.session_state:
    st.session_state.demand_hood = available_hoods[0]

# Keep the widget value alive between page switches
st.session_state.demand_hood = st.session_state.demand_hood

# Guard against a saved value being removed by sidebar filters
if st.session_state.demand_hood not in available_hoods:
    st.session_state.demand_hood = available_hoods[0]

st.selectbox(
    "Compare a neighbourhood",
    available_hoods,
    key="demand_hood",
)

selected = demand.loc[
    demand["neighbourhood"] == st.session_state.demand_hood
].iloc[0]

strongest = demand.iloc[0]

# KPI row — designed to pass the 5-second test
k1, k2, k3, k4 = st.columns(4)
k1.metric("Strongest Demand", strongest["neighbourhood"])
k2.metric("Top Demand Score", f"{strongest['demand_score']:.0f}/100")
k3.metric(
    "Selected Reviews/Month",
    f"{selected['avg_reviews_per_month']:.2f}",
)
k4.metric(
    "Selected Availability",
    f"{selected['median_availability']:.0f} days",
)

st.divider()

# Blue highlights the selected neighbourhood; grey provides context
demand["display_colour"] = demand["neighbourhood"].apply(
    lambda x: "Selected" if x == st.session_state.demand_hood else "Other"
)

chart_data = demand.sort_values("demand_score", ascending=True)

fig = px.bar(
    chart_data,
    x="demand_score",
    y="neighbourhood",
    orientation="h",
    color="display_colour",
    color_discrete_map={
        "Selected": "#2E75B6",
        "Other": "#D9D9D9",
    },
    custom_data=[
        "avg_reviews_per_month",
        "median_availability",
        "median_price",
        "listings",
    ],
)

fig.update_traces(
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Demand score: %{x:.1f}<br>"
        "Reviews/month: %{customdata[0]:.2f}<br>"
        "Median availability: %{customdata[1]:.0f} days<br>"
        "Median price: £%{customdata[2]:.0f}<br>"
        "Listings: %{customdata[3]:,.0f}<extra></extra>"
    )
)

fig.update_layout(
    title="Review activity and limited availability reveal the demand leaders",
    xaxis_title="Demand score (0–100)",
    yaxis_title="",
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Arial"),
    height=max(500, len(chart_data) * 28),
)

fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE", range=[0, 105])
fig.update_yaxes(showgrid=False)

st.plotly_chart(fig, use_container_width=True)

with st.expander("How is the demand score calculated?"):
    st.write(
        "The score combines average reviews per month (70%) with inverse "
        "median availability (30%). It is a demand proxy, not confirmed "
        "booking or occupancy data."
    )
    st.dataframe(
        demand[
            [
                "neighbourhood",
                "listings",
                "avg_reviews_per_month",
                "median_availability",
                "median_price",
                "demand_score",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
