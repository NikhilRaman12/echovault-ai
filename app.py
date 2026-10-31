"""EchoVault AI — Primary Application Entry Point."""

import streamlit as st
from echovault.ui.components import inject_styles, render_hero
from echovault.ui.home import render_home
from echovault.ui.capture import render_capture
from echovault.ui.vault import render_vault
from echovault.ui.ask import render_ask
from echovault.ui.timeline import render_timeline
from echovault.ui.people_places import render_people_places
from echovault.ui.studio import render_studio
from echovault.ui.settings import render_settings

st.set_page_config(
    page_title="EchoVault AI — Family Memory Preservation",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply editorial archival design
inject_styles()

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🏛️ EchoVault AI")
    st.markdown("*Some voices fade. Their stories don't have to.*")
    st.markdown("---")
    
    page = st.radio(
        "Archive Navigation",
        [
            "Home Overview",
            "Capture Memory",
            "Memory Vault",
            "Ask Memories",
            "Timeline Journey",
            "People & Places",
            "Processing Studio",
            "Privacy & Settings",
        ],
        index=0,
    )
    
    st.markdown("---")
    st.caption("Hacktoberfest 2026: Ghost in the Machine")
    st.caption("100% Local Inference & SQLite Storage")

# Render Top Archival Banner
render_hero()

# Route to active screen
if page == "Home Overview":
    render_home()
elif page == "Capture Memory":
    render_capture()
elif page == "Memory Vault":
    render_vault()
elif page == "Ask Memories":
    render_ask()
elif page == "Timeline Journey":
    render_timeline()
elif page == "People & Places":
    render_people_places()
elif page == "Processing Studio":
    render_studio()
elif page == "Privacy & Settings":
    render_settings()
