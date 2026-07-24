import streamlit as st

st.set_page_config(page_title="London Airbnb Analytics", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

pg = st.navigation([
    st.Page(
        "pages/01_market.py",
        title="Is London Airbnb expensive right now?",
        icon="🏠",
    ),
    st.Page(
        "pages/02_drilldown.py",
        title="Which neighbourhoods drive the premium?",
        icon="📍",
    ),
    st.Page(
        "pages/03_demand.py",
        title="Where is guest demand strongest?",
        icon="📈",
    ),
])
pg.run()

