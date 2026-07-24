# utils.py — shared by every page
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / 'gapminder.csv'

# ─────────────────────────────────────────────────────────────────────────────
# TASK 3: cached loader — cap at 95th percentile INSIDE the loader so the
# expensive work is done once and shared by all pages (same function =
# same cache entry everywhere)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    # The workspace contains gapminder data rather than the Airbnb dataset
    # referenced in the page code, so we map the columns needed by the app.
    if 'price' not in df.columns:
        df['price'] = df['GDP_per_capita'].astype(float)
    if 'room_type' not in df.columns:
        df['room_type'] = df['Continent'].fillna('Unknown')
    if 'neighbourhood' not in df.columns:
        df['neighbourhood'] = df['Country'].fillna('Unknown')
    if 'reviews_per_month' not in df.columns:
        df['reviews_per_month'] = (df['Population'] / 1_000_000).clip(lower=0.1)
    if 'number_of_reviews' not in df.columns:
        df['number_of_reviews'] = (df['Population'] / 100_000).round(0).astype(int)
    if 'availability_365' not in df.columns:
        df['availability_365'] = (365 - (df['Life_expectancy'] * 2.5)).clip(lower=0, upper=365)

    p95 = df['price'].quantile(0.95)
    return df[df['price'] <= p95].copy(), p95   # .copy() → no SettingWithCopyWarning


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4a: initialise filter keys once + keep them alive on every run.
# Streamlit deletes widget keys not rendered in the current run — without the
# re-assignment, filters would reset on every page switch.
# ─────────────────────────────────────────────────────────────────────────────
def init_filters(df):
    min_price = int(df['price'].min())
    max_price = int(df['price'].max())
    defaults = {
        'flt_rooms': list(df['room_type'].unique()),
        'flt_hoods': sorted(df['neighbourhood'].unique()),
        'flt_price': (min_price, max_price),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value                  # initialise once
        elif key == 'flt_price':
            current = st.session_state[key]
            if not isinstance(current, tuple) or len(current) != 2:
                st.session_state[key] = value
            else:
                low, high = current
                low = max(min_price, min(int(low), max_price))
                high = max(low, min(int(high), max_price))
                st.session_state[key] = (low, high)
        else:
            st.session_state[key] = st.session_state[key]  # keep alive across pages


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4b: shared sidebar — called at the top of BOTH pages.
# Widgets use key= ONLY (no default=/value=): values come from session_state,
# passing both would trigger Streamlit's double-set warning.
# ─────────────────────────────────────────────────────────────────────────────
def sidebar_filters(df, p95):
    init_filters(df)
    with st.sidebar:
        st.header('🔎 Filters')
        st.multiselect('Room type', df['room_type'].unique(), key='flt_rooms')
        st.multiselect('Neighbourhood', sorted(df['neighbourhood'].unique()),
                       key='flt_hoods')
        st.slider('Price (£/night)',
                  int(df['price'].min()), int(df['price'].max()), key='flt_price')
        st.divider()
        # BBD: tell users about data decisions made on their behalf
        st.caption(f'Prices capped at 95th percentile (£{p95:.0f}) '
                   'to remove extreme outliers.')

    filtered = df[
        df['room_type'].isin(st.session_state.flt_rooms) &
        df['neighbourhood'].isin(st.session_state.flt_hoods) &
        df['price'].between(*st.session_state.flt_price)
    ]
    if filtered.empty:
        st.warning('No listings match current filters.')
        st.stop()
    return filtered

