"""Ask screen: Grounded remembrance conversational retrieval with verifiable citations."""

import streamlit as st
from echovault.orchestrator import orchestrator


def render_ask():
    st.markdown("### Ask Your Memories")
    st.write(
        "Inquire about past family stories, relationships, places, and events. "
        "Answers are drawn strictly from evidence preserved in your vault. "
        "If a fact was not recorded, EchoVault will honestly abstain rather than inventing a detail."
    )

    sample_questions = [
        "What did my family say about moving houses?",
        "Where was grandfather stationed during the war?",
        "What was grandmother's favorite memory on the farm?",
    ]

    selected_sample = st.selectbox("Sample Inquiries (or type your own below):", [""] + sample_questions)
    user_query = st.text_input(
        "Your Question",
        value=selected_sample if selected_sample else "",
        placeholder="e.g. What did my father remember about his first job?",
    )

    if st.button("Search Memories & Retrieve Answer"):
        if not user_query.strip():
            st.error("Please enter a question to ask your memory vault.")
        else:
            with st.spinner("Retrieving evidence and synthesizing grounded remembrance..."):
                answer, traces = orchestrator.answer_question(user_query)

            # Display Grounded Answer
            st.markdown("#### Answer")
            if answer.is_abstention:
                st.warning(f"**{answer.answer}**")
                if answer.abstention_reason:
                    st.caption(f"Reason: {answer.abstention_reason}")
            else:
                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <div style="font-size: 1.15rem; line-height: 1.6; color: #1B3B2B;">
                            {answer.answer}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if answer.uncertainty_disclosure:
                    st.caption(f"🛡️ **Integrity Verification:** {answer.uncertainty_disclosure}")

                # Display Verifiable Citations
                if answer.citations:
                    st.markdown("#### Supporting Evidence & Citations")
                    for idx, c in enumerate(answer.citations, 1):
                        st.markdown(
                            f"""
                            <div class="citation-pill">
                                <strong>[{idx}] {c.title}</strong> (Narrated by {c.narrator or 'Family Member'}) &bull; 
                                <span style="color: #8C6B24;">Relevance Rank: {c.relevance_score}</span>
                                <div style="margin-top: 6px; font-style: italic; color: #3A473E;">
                                    "{c.passage}"
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Display Multi-Agent Execution Steps
            with st.expander("Orchestration Traces (3 Agents Coordinated)", expanded=False):
                for t in traces:
                    st.markdown(f"- **{t.agent_name}** &rarr; *{t.stage}* ({t.duration_ms} ms): {t.message}")
