"""Home screen: Emotional product introduction and vault overview."""

import streamlit as st
from echovault.database import db
from echovault.services.gemma_service import gemma_service
from echovault.services.transcription_service import transcription_service


def render_home():
    st.markdown("### The Sacred Archive of Family Voices")
    st.write(
        "EchoVault AI is a private, local-first platform designed to protect and honor family oral history. "
        "Unlike commercial cloud assistants that transmit personal stories to external servers or hallucinate fictional accounts, "
        "EchoVault operates under a strict preservation creed:"
    )

    st.info(
        "**Core Archival Philosophy:** Preserve what people actually said. "
        "Do not manufacture what they might have said. Never invent memories, dates, relationships, or quotations."
    )

    # Real Vault Metrics
    total_memories = db.count_memories()
    entities_grouped = db.get_all_entities_grouped()
    people_count = len(entities_grouped.get("people", []))
    places_count = len(entities_grouped.get("places", []))

    st.markdown("#### Vault Census")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Saved Memories", value=total_memories)
    with col2:
        st.metric(label="People Cataloged", value=people_count)
    with col3:
        st.metric(label="Places Preserved", value=places_count)
    with col4:
        st.metric(label="Local Privacy Status", value="100% Offline")

    # Local System Readiness
    st.markdown("#### Local Preservation Engine Status")
    is_ollama_up, ollama_status, models = gemma_service.check_health()
    
    col_a, col_b = st.columns(2)
    with col_a:
        if is_ollama_up:
            st.success(f"**Gemma AI Engine:** {ollama_status}")
        else:
            st.warning(
                f"**Gemma AI Engine Offline:** {ollama_status}\n\n"
                "*(Note: You can still record, write, edit, archive, and search memories with full-text FTS5 without AI.)*"
            )
    with col_b:
        if transcription_service.is_available:
            st.success("**Audio Transcription:** faster-whisper available locally.")
        else:
            st.info(
                "**Audio Transcription:** Optional local faster-whisper not detected. "
                "Audio recordings are preserved securely, and transcripts can be manually entered or edited."
            )

    # Empty State or Recent Stories
    st.markdown("---")
    st.markdown("#### Recent Vault Entries")
    recent = db.list_memories(limit=3)

    if not recent:
        st.markdown(
            """
            <div class="parchment-card" style="text-align: center; padding: 2.5rem;">
                <h4 style="color: #1B3B2B; margin-bottom: 0.5rem;">Your Family Vault is Currently Empty</h4>
                <p style="color: #57615A; max-width: 550px; margin: 0 auto 1.5rem auto;">
                    Every family story begins with a single voice. Record an elder's recollections, 
                    type a cherished childhood memory, or upload an audio recording to start your private archive.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for m in recent:
            with st.container():
                st.markdown(
                    f"""
                    <div class="parchment-card">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <h4 style="margin: 0; color: #1B3B2B;">{m.title}</h4>
                            <span style="font-size: 0.85rem; color: #8C6B24;">Narrated by {m.narrator or 'Family Member'}</span>
                        </div>
                        <p style="font-style: italic; color: #3A473E; margin-top: 0.6rem;">{m.summary or m.content[:200] + '...'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
