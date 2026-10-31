"""People & Places screen: Entity catalog for family relationships and ancestral locations."""

import streamlit as st
from echovault.database import db


def render_people_places():
    st.markdown("### People & Ancestral Places")
    st.write("Browse individuals and geographical anchors documented in your family archive.")

    data = db.get_all_entities_grouped()
    people = data.get("people", [])
    places = data.get("places", [])

    tab_people, tab_places = st.tabs([f"👥 People ({len(people)})", f"📍 Places ({len(places)})"])

    with tab_people:
        if not people:
            st.info("No individuals identified yet. As you capture stories, family members will be cataloged here.")
        else:
            cols = st.columns(3)
            for idx, p in enumerate(people):
                with cols[idx % 3]:
                    rel = f"<div style='font-size:0.85rem; color:#8C6B24;'>{p['secondary_value']}</div>" if p.get('secondary_value') else ""
                    st.markdown(
                        f"""
                        <div class="parchment-card">
                            <h4 style="margin: 0; color: #1B3B2B;">{p['entity_name']}</h4>
                            {rel}
                            <div style="margin-top: 8px; font-size: 0.8rem; color: #57615A;">
                                Appears in {p['memory_count']} saved stories
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab_places:
        if not places:
            st.info("No places recorded yet. Locations from your family stories will appear here.")
        else:
            cols = st.columns(3)
            for idx, pl in enumerate(places):
                with cols[idx % 3]:
                    loc_type = f"<div style='font-size:0.85rem; color:#8C6B24;'>{pl['secondary_value']}</div>" if pl.get('secondary_value') else ""
                    st.markdown(
                        f"""
                        <div class="parchment-card">
                            <h4 style="margin: 0; color: #1B3B2B;">{pl['entity_name']}</h4>
                            {loc_type}
                            <div style="margin-top: 8px; font-size: 0.8rem; color: #57615A;">
                                Mentioned in {pl['memory_count']} memories
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
