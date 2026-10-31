"""Timeline screen: Chronological visualization of preserved family memories."""

import streamlit as st
from echovault.database import db


def render_timeline():
    st.markdown("### Family Memory Chronology")
    st.write("Explore your family's journey ordered by historical event dates and recorded recollections.")

    memories = db.get_timeline_memories()

    if not memories:
        st.info("No memories currently cataloged. Add memories in the Capture tab to generate the timeline.")
        return

    st.markdown("---")

    for idx, m in enumerate(memories):
        date_badge = m.get("event_date_raw") or m.get("created_at")[:10]
        narrator = m.get("narrator") or "Family Member"
        summary = m.get("summary") or "Oral history recording."
        
        col_time, col_card = st.columns([1, 4])
        with col_time:
            st.markdown(
                f"""
                <div style="text-align: right; padding-right: 12px; border-right: 2px solid #DFC185;">
                    <span class="badge-gold" style="font-size: 0.95rem;">{date_badge}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_card:
            st.markdown(
                f"""
                <div class="parchment-card" style="margin-bottom: 1.5rem;">
                    <h4 style="margin: 0; color: #1B3B2B;">{m['title']}</h4>
                    <span style="font-size: 0.85rem; color: #736E65;">Recounted by {narrator}</span>
                    <p style="margin-top: 8px; color: #2B332E;">{summary}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
