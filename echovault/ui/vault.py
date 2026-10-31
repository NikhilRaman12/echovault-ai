"""Memory Vault screen: Browse, search, inspect, and manage archived family memories."""

from pathlib import Path
import streamlit as st
from echovault.database import db
from echovault.schemas import AuditEvent, AuditAction


def render_vault():
    st.markdown("### The Memory Vault")
    st.write("Browse preserved stories, explore extracted entities, and review original recordings.")

    # Search Bar
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        query = st.text_input("Search Vault (FTS5 Full-Text Search)", placeholder="Search by name, place, event, or phrase...")
    with search_col2:
        st.write("")
        st.write("")
        show_all = st.button("Reset / Show All")

    if query and not show_all:
        memories = db.search_memories(query, limit=20)
        st.markdown(f"**Found {len(memories)} matching memory passages.**")
        for p in memories:
            full_mem = db.get_memory(p.memory_id)
            if full_mem:
                _render_memory_card(full_mem, highlighted_snippet=p.passage)
    else:
        memories = db.list_memories(limit=50)
        if not memories:
            st.info("The memory vault is currently empty. Use the 'Capture' tab to preserve your first story.")
        else:
            for mem in memories:
                _render_memory_card(mem)


def _render_memory_card(mem, highlighted_snippet: str = None):
    """Render a single memory card with archival styling and management options."""
    with st.container():
        st.markdown(
            f"""
            <div class="parchment-card">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <h3 style="margin: 0; color: #1B3B2B;">{mem.title}</h3>
                    <span class="badge-gold">Narrator: {mem.narrator or 'Family Member'}</span>
                </div>
                <div style="margin-top: 4px; font-size: 0.85rem; color: #736E65;">
                    Preserved on {mem.created_at.strftime('%B %d, %Y')} | Source: {mem.source_type.value}
                </div>
            """,
            unsafe_allow_html=True,
        )

        if mem.summary:
            st.markdown(f"**Summary:** *{mem.summary}*")

        if highlighted_snippet:
            st.markdown(f"**Matching Evidence:**\n> {highlighted_snippet}")

        with st.expander("Read Full Story & Entity Dossier"):
            st.markdown("#### Original Account")
            st.write(mem.content)

            col1, col2 = st.columns(2)
            with col1:
                if mem.people:
                    st.markdown("**People Identified:**")
                    for p in mem.people:
                        rel = f" *({p.relationship})*" if p.relationship else ""
                        st.markdown(f"- {p.name}{rel}")
                if mem.places:
                    st.markdown("**Places Mentioned:**")
                    for pl in mem.places:
                        st.markdown(f"- {pl.name}")

            with col2:
                if mem.quotes:
                    st.markdown("**Direct Quotes:**")
                    for q in mem.quotes:
                        spk = f" — {q.speaker}" if q.speaker else ""
                        st.markdown(f"- *\"{q.quote_text}\"*{spk}")
                if mem.themes:
                    st.markdown("**Themes:**")
                    theme_badges = "".join([f'<span class="badge-forest">{t}</span>' for t in mem.themes])
                    st.markdown(theme_badges, unsafe_allow_html=True)

            if mem.uncertainty_notes:
                st.caption(f"**Uncertainty / Verification Notes:** {mem.uncertainty_notes}")

            st.caption(f"**Provenance Hash (SHA-256):** `{mem.content_hash}`")

            # Safe Deletion Control
            del_col1, del_col2 = st.columns([4, 1])
            with del_col2:
                if st.button("Delete Memory", key=f"del_{mem.id}", help="Permanently delete from vault."):
                    db.delete_memory(mem.id)
                    db.record_audit_event(AuditEvent(
                        memory_id=mem.id,
                        action=AuditAction.MEMORY_DELETED,
                        agent_name="VaultUI",
                        details={"title": mem.title},
                    ))
                    st.success("Memory deleted safely.")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
