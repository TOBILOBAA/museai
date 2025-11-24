
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
        "hero_sub": "Discover artifacts through vision, voice, and AI.",
        "hero_button": "Start museum tour",
        "step1_title": "Step 1 – Capture the artifact",
        "step1_hint": "Take a photo of an artifact to unlock your tour.",
        "scanning": "Scanning your photo… stand by.",
        "step2_title": "Step 2 – Ask MuseAI",
        "step2_hint": "Use your voice or text to ask anything about this artifact.",
        "fake_answer": "This is a demo answer explaining your artifact in a friendly way.",
        "error_title": "Something went wrong",
        "error_body": "This is how a user-friendly error message will appear in the real app.",
    },
    "fr": {
        "hero_title": "MuseAI",
        "hero_sub": "Découvrez les objets grâce à la vision, la voix et l’IA.",
        "hero_button": "Commencer la visite du musée",
        "step1_title": "Étape 1 – Photographiez l’objet",
        "step1_hint": "Prenez une photo d’un objet pour lancer votre visite.",
        "scanning": "Analyse de votre photo… un instant.",
        "step2_title": "Étape 2 – Parlez à MuseAI",
        "step2_hint": "Utilisez votre voix ou du texte pour poser vos questions.",
        "fake_answer": "Ceci est une réponse de démonstration qui explique l’objet.",
        "error_title": "Un problème est survenu",
        "error_body": "Voici comment un message d’erreur convivial apparaîtra dans l’application.",
    },
    "he": {
        "hero_title": "MuseAI",
        "hero_sub": "גלו פריטים דרך צילום, קול ובינה מלאכותית.",
        "hero_button": "התחלת סיור במוזיאון",
        "step1_title": "שלב 1 – צלמו את הפריט",
        "step1_hint": "צלמו פריט כדי להתחיל את הסיור.",
        "scanning": "סורק את התמונה… רגע אחד.",
        "step2_title": "שלב 2 – דברו עם MuseAI",
        "step2_hint": "דברו או כתבו שאלה על הפריט.",
        "fake_answer": "זו תשובת דמו שמסבירה את הפריט בצורה נעימה.",
        "error_title": "אירעה שגיאה",
        "error_body": "כך הודעת שגיאה ידידותית תיראה באפליקציה האמיתית.",
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


def on_change_language():
    """Update language code when dropdown changes."""
    label = st.session_state._lang_select_label
    st.session_state.language = LABEL_TO_LANG[label]


# ---------------------------------------------------
# TOP BAR: logo + language switch
# ---------------------------------------------------
lang = st.session_state.language
txt = STRINGS[lang]

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    st.markdown(
        "<h3 style='margin-bottom:0;'>MuseAI</h3>",
        unsafe_allow_html=True,
    )

with top_col2:
    current_label = LANG_LABELS[lang]
    st.selectbox(
        " ",
        options=list(LANG_LABELS.values()),
        index=list(LANG_LABELS.values()).index(current_label),
        key="_lang_select_label",
        on_change=on_change_language,
        label_visibility="collapsed",
    )

st.markdown("---")

# ---------------------------------------------------
# HERO SECTION
# ---------------------------------------------------
hero_container = st.container()
with hero_container:
    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding-top:5rem;
            padding-bottom:4rem;
        ">
            <h1 style="font-size:3rem; margin-bottom:0.5rem;">{txt['hero_title']}</h1>
            <p style="font-size:1.1rem; opacity:0.85; margin-bottom:2rem;">
                {txt['hero_sub']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered button under text
    btn_col = st.columns([3, 2, 3])[1]
    with btn_col:
        start_clicked = st.button(
            txt["hero_button"],
            use_container_width=True,
        )

    if start_clicked:
        st.session_state.hero_started = True
        st.rerun()

# If hero not started, stop here
if not st.session_state.hero_started:
    st.stop()

st.markdown("---")

# ---------------------------------------------------
# STEP 1 – CAMERA DEMO
# ---------------------------------------------------
st.markdown(f"### {txt['step1_title']}")

cam_col1, cam_col2 = st.columns([1.5, 1])

with cam_col1:
    camera_file = st.camera_input(
        " ",
        key="demo_camera",
        label_visibility="collapsed",
    )

    if camera_file is not None and not st.session_state.is_scanning:
        st.session_state.camera_has_photo = True
        st.session_state.is_scanning = True

with cam_col2:
    if not st.session_state.camera_has_photo:
        st.caption(txt["step1_hint"])
    else:
        with st.spinner(txt["scanning"]):
            time.sleep(1.5)  # fake delay
        st.success("✅ Artifact recognized (demo)")

st.markdown("---")

# ---------------------------------------------------
# STEP 2 – CONVERSATION DEMO
# ---------------------------------------------------
st.markdown(f"### {txt['step2_title']}")

st.write(txt["step2_hint"])

# Fake input + reply
user_question = st.text_input("Type a demo question here:")

if user_question:
    st.session_state.fake_chat.append({"role": "user", "text": user_question})
    st.session_state.fake_chat.append({"role": "assistant", "text": txt["fake_answer"]})

# Chat bubbles
for msg in st.session_state.fake_chat:
    if msg["role"] == "assistant":
        st.markdown(
            f"<div style='background:#202020;padding:0.7rem 0.9rem;"
            f"border-radius:0.8rem;margin-bottom:0.4rem;color:#f5f5f5;'>🤖 {msg['text']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='background:#2b3b4a;padding:0.7rem 0.9rem;"
            f"border-radius:0.8rem;margin-bottom:0.4rem;text-align:right;color:#ffffff;'>🧑 {msg['text']}</div>",
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
