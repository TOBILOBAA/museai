import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------
# Basic page config
# ---------------------------------------------------
st.set_page_config(
    page_title="MuseAI – Multimodal Museum Companion",
    page_icon="🎧",
    layout="wide",
)

# ---------------------------------------------------
# Global styles (dark theme, logo pill, buttons, sidebar)
# ---------------------------------------------------
st.markdown(
    """
    <style>
    /* Global body */
    .stApp {
        background: radial-gradient(circle at top, #181b22 0, #050608 45%, #050608 100%);
        color: #f5f5f5;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    /* Top logo pill */
    .museai-logo-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.25);
        background: rgba(10,10,10,0.8);
        backdrop-filter: blur(10px);
        font-weight: 600;
        letter-spacing: 0.06em;
        font-size: 0.8rem;
        text-transform: uppercase;
    }

    /* Hero centre container */
    .museai-hero {
        text-align: center;
        padding-top: 5rem;
        padding-bottom: 4rem;
    }

    .museai-hero h1 {
        font-size: 3rem;
        margin-bottom: 0.6rem;
    }

    .museai-hero p {
        font-size: 1.1rem;
        opacity: 0.88;
        margin-bottom: 2rem;
    }

    /* Primary button style */
    .stButton>button {
        border-radius: 999px;
        padding: 0.6rem 1.6rem;
        font-weight: 600;
        border: none;
        background: #f5f5f5;
        color: #050608;
        box-shadow: 0 10px 30px rgba(0,0,0,0.55);
        transition: transform 0.12s ease-out, box-shadow 0.12s ease-out, background 0.12s;
    }

    .stButton>button:hover {
        background: #ffffff;
        transform: translateY(-1px);
        box-shadow: 0 14px 40px rgba(0,0,0,0.7);
    }

    .stButton>button:active {
        transform: translateY(1px) scale(0.99);
        box-shadow: 0 6px 18px rgba(0,0,0,0.6);
        background: #e5e5e5;
    }

    /* Sidebar dark theme */
    [data-testid="stSidebar"] {
        background: #050608;
        color: #f5f5f5;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    [data-testid="stSidebar"] .stSelectbox label {
        color: #f5f5f5 !important;
    }

    [data-testid="stSidebar"] .stButton>button {
        background: #f5f5f5;
        color: #050608;
    }

    /* Camera card */
    .camera-card {
        background: rgba(15,16,24,0.9);
        border-radius: 1rem;
        padding: 1.2rem 1.2rem 1.5rem 1.2rem;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 18px 40px rgba(0,0,0,0.6);
    }

    /* Chat bubbles */
    .bubble-assistant {
        background:#202020;
        padding:0.7rem 0.9rem;
        border-radius:0.8rem;
        margin-bottom:0.45rem;
        color:#f5f5f5;
    }
    .bubble-user {
        background:#2b3b4a;
        padding:0.7rem 0.9rem;
        border-radius:0.8rem;
        margin-bottom:0.45rem;
        text-align:right;
        color:#ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# Language & copy system
# ---------------------------------------------------
LANG_LABELS = {
    "en": "English 🇬🇧",
    "fr": "Français 🇫🇷",
    "he": "עברית 🇮🇱",
}
LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

STRINGS = {
    "en": {
        "hero_title": "MuseAI",
        "hero_sub": "A smart museum guide that sees, listens, and explains.",
        "hero_button": "Start museum tour",
        "step1_title": "Step 1 – Capture the artifact",
        "step1_hint": "Take a photo of an artifact to unlock your tour.",
        "scanning": "Scanning your photo… stand by.",
        "step2_title": "Step 2 – Ask MuseAI",
        "step2_hint": "Use your voice or text to ask anything about this artifact.",
        "fake_answer": "This is a demo answer explaining your artifact in a friendly way.",
        "error_title": "Something went wrong",
        "error_body": "This is how a user-friendly error message will appear in the real app.",
        "sidebar_language": "Language",
        "sidebar_new_tour": "Start new tour",
    },
    "fr": {
        "hero_title": "MuseAI",
        "hero_sub": "Un guide de musée intelligent qui voit, écoute et explique.",
        "hero_button": "Commencer la visite du musée",
        "step1_title": "Étape 1 – Photographiez l’objet",
        "step1_hint": "Prenez une photo d’un objet pour lancer votre visite.",
        "scanning": "Analyse de votre photo… un instant.",
        "step2_title": "Étape 2 – Parlez à MuseAI",
        "step2_hint": "Utilisez votre voix ou du texte pour poser vos questions.",
        "fake_answer": "Ceci est une réponse de démonstration qui explique l’objet.",
        "error_title": "Un problème est survenu",
        "error_body": "Voici comment un message d’erreur convivial apparaîtra dans l’application.",
        "sidebar_language": "Langue",
        "sidebar_new_tour": "Commencer un nouveau tour",
    },
    "he": {
        "hero_title": "MuseAI",
        "hero_sub": "מדריך מוזיאון חכם שרואה, מקשיב ומסביר.",
        "hero_button": "התחלת סיור במוזיאון",
        "step1_title": "שלב 1 – צלמו את הפריט",
        "step1_hint": "צלמו פריט כדי להתחיל את הסיור.",
        "scanning": "סורק את התמונה… רגע אחד.",
        "step2_title": "שלב 2 – דברו עם MuseAI",
        "step2_hint": "דברו או כתבו שאלה על הפריט.",
        "fake_answer": "זו תשובת דמו שמסבירה את הפריט בצורה נעימה.",
        "error_title": "אירעה שגיאה",
        "error_body": "כך הודעת שגיאה ידידותית תיראה באפליקציה האמיתית.",
        "sidebar_language": "שפה",
        "sidebar_new_tour": "התחל סיור חדש",
    },
}

# ---------------------------------------------------
# Session state
# ---------------------------------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"

if "hero_started" not in st.session_state:
    st.session_state.hero_started = False

if "camera_has_photo" not in st.session_state:
    st.session_state.camera_has_photo = False

if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

if "fake_chat" not in st.session_state:
    st.session_state.fake_chat = []  # list of dicts {role, text}


def on_change_language_top():
    """Update language when splash dropdown changes."""
    label = st.session_state._lang_select_label_top
    st.session_state.language = LABEL_TO_LANG[label]


def on_change_language_sidebar():
    """Update language from sidebar dropdown."""
    label = st.session_state._lang_select_label_side
    st.session_state.language = LABEL_TO_LANG[label]


def reset_demo_tour():
    """Reset demo state for 'Start new tour'."""
    st.session_state.camera_has_photo = False
    st.session_state.is_scanning = False
    st.session_state.fake_chat = []


# ---------------------------------------------------
# SPLASH SCREEN (no sidebar)
# ---------------------------------------------------
if not st.session_state.hero_started:
    lang = st.session_state.language
    txt = STRINGS[lang]

    top_col1, top_col2 = st.columns([3, 1])

    with top_col1:
        st.markdown(
            "<div class='museai-logo-pill'>MuseAI</div>",
            unsafe_allow_html=True,
        )

    with top_col2:
        current_label = LANG_LABELS[lang]
        st.selectbox(
            "Language",
            options=list(LANG_LABELS.values()),
            index=list(LANG_LABELS.values()).index(current_label),
            key="_lang_select_label_top",
            on_change=on_change_language_top,
        )

    st.markdown("---")

    # Hero
    st.markdown(
        f"""
        <div class="museai-hero">
            <h1>{txt['hero_title']}</h1>
            <p>{txt['hero_sub']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    btn_col = st.columns([3, 2, 3])[1]
    with btn_col:
        if st.button(txt["hero_button"], use_container_width=True):
            st.session_state.hero_started = True
            st.experimental_rerun()  # safe here

    st.stop()

# ---------------------------------------------------
# MAIN UI (with sidebar, camera demo, chat, error preview)
# ---------------------------------------------------
lang = st.session_state.language
txt = STRINGS[lang]

# Sidebar: language + new tour
with st.sidebar:
    st.markdown("### " + txt["sidebar_language"])
    current_label = LANG_LABELS[lang]
    st.selectbox(
        "",
        options=list(LANG_LABELS.values()),
        index=list(LANG_LABELS.values()).index(current_label),
        key="_lang_select_label_side",
        on_change=on_change_language_sidebar,
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button(txt["sidebar_new_tour"]):
        reset_demo_tour()
        st.experimental_rerun()

# Top logo only (no language, no duplicate tagline)
top_col_main, _ = st.columns([3, 1])
with top_col_main:
    st.markdown(
        "<div class='museai-logo-pill' style='margin-top:0.7rem;'>MuseAI</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------
# STEP 1 – CAMERA DEMO
# ---------------------------------------------------
st.markdown(f"### {txt['step1_title']}")
st.caption(txt["step1_hint"])  # directly under the title, not off to the side

cam_col1, cam_col2 = st.columns([1.6, 1])

with cam_col1:
    st.markdown("<div class='camera-card'>", unsafe_allow_html=True)

    camera_file = st.camera_input(
        " ",
        key="demo_camera",
        label_visibility="collapsed",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if camera_file is not None and not st.session_state.is_scanning:
        st.session_state.camera_has_photo = True
        st.session_state.is_scanning = True

with cam_col2:
    if not st.session_state.camera_has_photo:
        st.caption(" ")
    else:
        with st.spinner(txt["scanning"]):
            time.sleep(1.5)  # fake delay
        st.success("✅ Artifact recognized (demo)")
        st.session_state.is_scanning = False

st.markdown("---")

# ---------------------------------------------------
# STEP 2 – CONVERSATION DEMO
# ---------------------------------------------------
st.markdown(f"### {txt['step2_title']}")
st.write(txt["step2_hint"])

user_question = st.text_input("Type a demo question here:")

if user_question:
    st.session_state.fake_chat.append({"role": "user", "text": user_question})
    st.session_state.fake_chat.append({"role": "assistant", "text": txt["fake_answer"]})

for msg in st.session_state.fake_chat:
    if msg["role"] == "assistant":
        st.markdown(
            f"<div class='bubble-assistant'>🤖 {msg['text']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='bubble-user'>🧑 {msg['text']}</div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ---------------------------------------------------
# ERROR PREVIEW AREA
# ---------------------------------------------------
with st.expander("Demo: what an error message will look like"):
    st.error(
        f"**{txt['error_title']}**\n\n"
        f"{txt['error_body']}\n\n"
        "_Technical details will be hidden behind this friendly message._"
    )