"""Settings screen: Privacy controls, model configuration, export, backup, and restore."""

import streamlit as st
from echovault.config import config
from echovault.services.gemma_service import gemma_service
from echovault.services.export_service import export_service
from echovault.services.transcription_service import transcription_service


def render_settings():
    st.markdown("### Privacy & System Configuration")
    st.write("EchoVault is built on the belief that private family history should never leave your personal computer.")

    # Model & Runtime Diagnostics
    st.markdown("#### Local Inference Health")
    is_up, status_msg, models = gemma_service.check_health()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Ollama Endpoint:** `{config.ollama_base_url}`")
        st.markdown(f"**Target Gemma Model:** `{config.gemma_model}`")
        if is_up:
            st.success(f"Status: {status_msg}")
            if models:
                st.caption(f"Installed Models on Ollama: {', '.join(models)}")
        else:
            st.warning(f"Status: {status_msg}")
    
    with col2:
        st.markdown(f"**Whisper Audio Model:** `{config.whisper_model_size}`")
        st.markdown(f"**Transcription Status:** {'Installed' if transcription_service.is_available else 'Offline fallback'}")
        st.markdown(f"**Local Database Path:** `{config.db_path}`")
        st.markdown(f"**Audio Vault Directory:** `{config.audio_storage_dir}`")

    st.markdown("---")

    # Export & Backup
    st.markdown("#### Vault Backup & Portability")
    st.write("Export your complete family memory archive into open formats (JSON and Markdown book).")

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        json_data = export_service.export_archive_to_json()
        st.download_button(
            label="Download Complete Archive (JSON)",
            data=json_data,
            file_name="echovault_family_archive.json",
            mime="application/json",
            help="Contains all memories, entities, quotes, timestamps, and hashes.",
        )
    with col_exp2:
        md_book = export_service.export_archive_to_markdown()
        st.download_button(
            label="Download Memory Book (Markdown)",
            data=md_book,
            file_name="echovault_memory_book.md",
            mime="text/markdown",
            help="Human-readable formatted archive ready for printing or e-readers.",
        )

    # Restore from Backup
    st.markdown("---")
    st.markdown("#### Restore Archive from Backup")
    uploaded_backup = st.file_uploader("Upload EchoVault JSON Backup File", type=["json"])
    if uploaded_backup:
        if st.button("Restore Backup Into Vault"):
            content = uploaded_backup.read().decode("utf-8")
            try:
                imported, skipped = export_service.restore_archive_from_json(content)
                st.success(f"Restoration complete: {imported} memories imported, {skipped} duplicate entries skipped.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to restore archive: {str(e)}")
