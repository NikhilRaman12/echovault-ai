"""Capture screen: Record or enter oral history stories with real-time agent workflow."""

import streamlit as st
from echovault.orchestrator import orchestrator


def render_capture():
    st.markdown("### Capture a Family Memory")
    st.write(
        "Preserve an authentic personal memory. "
        "Original words are never altered. The agent workflow indexes people, places, dates, and direct quotations."
    )

    tab_text, tab_audio = st.tabs(["✍️ Written Memory", "🎙️ Audio Recording"])

    # -------------------------------------------------------------
    # Written Memory Tab
    # -------------------------------------------------------------
    with tab_text:
        with st.form("form_text_capture"):
            narrator = st.text_input("Narrator / Speaker Name", placeholder="e.g. Grandfather Arthur, Aunt Clara, Self")
            user_title = st.text_input("Suggested Title (Optional)", placeholder="e.g. The 1958 Cross-Country Move")
            raw_content = st.text_area(
                "Personal Story or Recollection",
                height=220,
                placeholder=(
                    "Type the memory exactly as recounted. For example:\n\n"
                    "My grandmother Mary told me that in July 1944, right before my grandfather William departed for Europe, "
                    "they sat on the porch of the old stone house in Savannah. He gave her his silver pocket watch and said, "
                    "'Keep this ticking until I come through that wooden gate.' She kept it wound every morning for three years."
                ),
            )
            submit_text = st.form_submit_button("Preserve Memory in Vault")

        if submit_text:
            if not raw_content.strip():
                st.error("Please enter the memory text before preserving.")
            else:
                with st.spinner("Executing multi-agent preservation workflow..."):
                    state = orchestrator.process_text_memory(
                        content=raw_content,
                        narrator=narrator or "Family Member",
                        user_title=user_title,
                    )

                if state.errors:
                    st.error(f"Archival failed: {'; '.join(state.errors)}")
                else:
                    st.success(f"✨ Memory safely preserved and archived: **{state.archived_record.title}**")
                    
                    # Display Agent Execution Pipeline Traces
                    with st.expander("Agent Processing Trace", expanded=True):
                        for trace in state.traces:
                            st.markdown(f"- **{trace.agent_name}** ({trace.duration_ms} ms): {trace.message}")

                    if state.intelligence:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("##### Extracted Entities")
                            if state.intelligence.people:
                                for p in state.intelligence.people:
                                    rel = f" ({p.relationship})" if p.relationship else ""
                                    st.markdown(f"- **Person:** {p.name}{rel}")
                            if state.intelligence.places:
                                for pl in state.intelligence.places:
                                    st.markdown(f"- **Place:** {pl.name}")
                        with col2:
                            st.markdown("##### Temporal & Quotations")
                            if state.intelligence.dates:
                                for d in state.intelligence.dates:
                                    st.markdown(f"- **Date Reference:** {d.raw_date}")
                            if state.intelligence.quotes:
                                for q in state.intelligence.quotes:
                                    st.markdown(f"- *\"{q.quote_text}\"*")

    # -------------------------------------------------------------
    # Audio Recording Tab
    # -------------------------------------------------------------
    with tab_audio:
        st.markdown("##### Upload Family Voice Recording")
        st.write("Supported formats: WAV, MP3, M4A, OGG, FLAC (Max 25 MB). Audio is stored 100% locally.")

        audio_file = st.file_uploader(
            "Select Audio File",
            type=["wav", "mp3", "m4a", "ogg", "flac"],
            help="Audio recordings stay on this machine and are never uploaded to any cloud service.",
        )
        audio_narrator = st.text_input("Speaker in Recording", placeholder="e.g. Grandmother Eleanor", key="audio_narrator")
        manual_notes = st.text_area(
            "Optional Transcript or Notes (if available)",
            height=100,
            placeholder="If you already have a transcript or notes, enter them here to assist processing.",
        )

        if st.button("Ingest and Preserve Audio"):
            if not audio_file:
                st.error("Please select an audio file to upload.")
            else:
                with st.spinner("Processing audio through local agent pipeline..."):
                    audio_bytes = audio_file.read()
                    state = orchestrator.process_audio_memory(
                        audio_bytes=audio_bytes,
                        filename=audio_file.name,
                        narrator=audio_narrator or "Family Member",
                        manual_transcript_override=manual_notes,
                    )

                if state.errors:
                    st.error(f"Audio processing error: {'; '.join(state.errors)}")
                else:
                    st.success(f"🎙️ Audio preserved and cataloged: **{state.archived_record.title}**")
                    with st.expander("Agent Pipeline Trace", expanded=True):
                        for trace in state.traces:
                            st.markdown(f"- **{trace.agent_name}** ({trace.duration_ms} ms): {trace.message}")
