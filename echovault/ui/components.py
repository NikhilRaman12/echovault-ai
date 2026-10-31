"""Custom CSS styling and editorial UI components for EchoVault AI."""

import streamlit as st

ARCHIVAL_CSS = """
<style>
/* EchoVault AI Editorial Archival Theme */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --forest-dark: #0F231B;
    --forest-medium: #1B3B2B;
    --forest-light: #2A543E;
    --antique-gold: #C5A059;
    --gold-glow: #DFC185;
    --warm-ivory: #FDFBF7;
    --parchment: #F6F1E8;
    --parchment-border: #E5DBCE;
    --ink-dark: #1E221F;
    --ink-muted: #57615A;
}

html, body, [class*="css"] {
    font-family: 'Newsreader', Georgia, serif;
    color: var(--ink-dark);
}

.stApp {
    background-color: var(--warm-ivory);
}

/* Headings */
h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    font-weight: 600 !important;
    color: var(--forest-dark) !important;
    letter-spacing: 0.5px;
}

h4, h5, h6, p, span, label {
    font-family: 'Newsreader', Georgia, serif;
}

/* Custom Hero Banner */
.echovault-hero {
    background: linear-gradient(135deg, #0D1F17 0%, #1B3B2B 100%);
    color: #FDFBF7;
    padding: 2.2rem 2.5rem;
    border-radius: 8px;
    border-left: 5px solid var(--antique-gold);
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(13, 31, 23, 0.08);
}

.echovault-hero h1 {
    color: #FDFBF7 !important;
    margin: 0;
    font-size: 2.4rem;
    letter-spacing: 1px;
}

.echovault-tagline {
    color: var(--gold-glow);
    font-family: 'Newsreader', Georgia, serif;
    font-style: italic;
    font-size: 1.25rem;
    margin-top: 0.5rem;
    margin-bottom: 0;
}

/* Parchment Card */
.parchment-card {
    background-color: #FFFFFF;
    border: 1px solid var(--parchment-border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.parchment-card:hover {
    box-shadow: 0 4px 14px rgba(27, 59, 43, 0.07);
    border-color: var(--antique-gold);
}

/* Golden Badges */
.badge-gold {
    display: inline-block;
    background-color: #FAF4E8;
    color: #8C6B24;
    border: 1px solid #DFC185;
    padding: 2px 10px;
    border-radius: 12px;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 6px;
}

.badge-forest {
    display: inline-block;
    background-color: #EBF2ED;
    color: #1B3B2B;
    border: 1px solid #B7CABE;
    padding: 2px 10px;
    border-radius: 12px;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 6px;
}

/* Grounded Evidence Box */
.evidence-card {
    background-color: #F4F8F5;
    border-left: 4px solid var(--forest-medium);
    padding: 1.2rem;
    border-radius: 0 8px 8px 0;
    margin-top: 1rem;
    margin-bottom: 1rem;
}

/* Citation Source Box */
.citation-pill {
    background: #FFFFFF;
    border: 1px solid #D1DDD5;
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 6px;
    font-size: 0.9rem;
}

/* Buttons */
.stButton > button {
    background-color: var(--forest-medium) !important;
    color: #FDFBF7 !important;
    border: 1px solid var(--antique-gold) !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.5px;
    border-radius: 4px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: var(--forest-dark) !important;
    border-color: var(--gold-glow) !important;
    color: #FFFFFF !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #F5EFEB !important;
    border-right: 1px solid var(--parchment-border);
}
</style>
"""

def inject_styles():
    """Inject global custom CSS into Streamlit page."""
    st.markdown(ARCHIVAL_CSS, unsafe_allow_html=True)

def render_hero(title: str = "EchoVault AI", subtitle: str = "Some voices fade. Their stories don't have to."):
    """Render the editorial archival hero banner."""
    st.markdown(f"""
    <div class="echovault-hero">
        <h1>{title}</h1>
        <p class="echovault-tagline">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
