"""Processing Studio screen: Multi-agent execution monitor, stage telemetry, and audit logs."""

import json
import streamlit as st
from echovault.database import db


def render_studio():
    st.markdown("### Multi-Agent Processing Studio")
    st.write(
        "Inspect the coordinated execution stages of EchoVault's 7 specialized agents. "
        "Every operation leaves a verifiable audit trace for privacy and transparency."
    )

    st.markdown("#### Coordinated Agent Architecture")
    agents_info = [
        ("Agent 1 — Memory Intake Agent", "Validates file sizes, mime types, computes SHA-256 hashes, sandboxes input."),
        ("Agent 2 — Transcription Agent", "Runs faster-whisper locally; handles missing ffmpeg/whisper offline gracefully."),
        ("Agent 3 — Memory Intelligence Agent", "Gemma (Ollama): extracts people, places, dates, quotes, and detects uncertainty."),
        ("Agent 4 — Memory Archivist Agent", "Atomically commits records to SQLite, updates FTS5 indices, detects duplicates."),
        ("Agent 5 — Memory Retrieval Agent", "Queries SQLite FTS5 with BM25 passage ranking and snippet extraction."),
        ("Agent 6 — Remembrance Intelligence Agent", "Answers user inquiries grounded exclusively in retrieved memory passages."),
        ("Agent 7 — Integrity and Privacy Agent", "Validates citation authenticity, prevents hallucinated answers, logs audits."),
    ]

    for title, desc in agents_info:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border-left:3px solid #1B3B2B; padding:10px 14px; margin-bottom:8px; border-radius:4px;">
                <strong style="color:#1B3B2B;">{title}:</strong> <span style="color:#3A473E; font-size:0.92rem;">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### Live Archival Audit Log")
    audits = db.get_audit_trail(limit=25)

    if not audits:
        st.info("No audit events recorded yet.")
    else:
        for a in audits:
            details = a.get("details_json", "{}")
            try:
                details_parsed = json.loads(details)
            except Exception:
                details_parsed = details

            col1, col2, col3 = st.columns([1, 1.5, 3])
            with col1:
                st.caption(a["timestamp"][:19])
            with col2:
                st.markdown(f"<span class='badge-forest'>{a['action']}</span>", unsafe_allow_html=True)
                st.caption(f"Agent: {a['agent_name']}")
            with col3:
                st.code(json.dumps(details_parsed, indent=1), language="json")
