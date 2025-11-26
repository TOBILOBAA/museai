import io
import os
from pathlib import Path
from typing import Literal
import sys

# --- make sure the project root is on sys.path (needed on Streamlit Cloud) ---
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.vision import classify_artifact_from_image
from app.voice import transcribe_and_detect_language, LanguageCode
from app.reasoning import museai_reason
from app.tts import tts_generate_audio

# ------------------------------------------------------------------------------------
# Basic config
# ------------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

LANG_OPTIONS = {
    "English 🇬🇧": "en",
    "Français 🇫🇷": "fr",
    "עברית 🇮🇱": "he",
}

# Copy strings for UI text (what each language switches into)
STRINGS = {
    "en": {
        "hero_title": "MuseAI",
        "hero_sub": "A smart museum guide that sees, listens, and explains.",
        "hero_button": "Start museum tour",
        "step1_title": "Step 1 – Capture the artifact",
        "step1_hint": "Take a photo of an artifact to unlock your tour.",
        "scanning": "Scanning your photo… stand by.",
        "step2_title": "Step 2 – Talk to MuseAI",
        "step2_hint": "Tap the mic and ask your question out loud. No typing needed.",
        "error_title": "We ran into a problem",
        "error_body": "Something didn’t work as expected. Please try again, or capture the artifact once more. If this keeps happening, wait a moment and retry.",
    },
    "fr": {
        "hero_title": "MuseAI",
        "hero_sub": "Votre guide de musée intelligent qui voit, écoute et explique.",
        "hero_button": "Commencer la visite",
        "step1_title": "Étape 1 – Photographiez l’objet",
        "step1_hint": "Prenez une photo d’un objet pour lancer la visite.",
        "scanning": "Analyse de votre photo… un instant.",
        "step2_title": "Étape 2 – Parlez à MuseAI",
        "step2_hint": "Appuyez sur le micro et posez votre question à voix haute.",
        "error_title": "Un problème est survenu",
        "error_body": "Une erreur s’est produite. Réessayez ou photographiez à nouveau l’objet. Si le problème persiste, attendez un instant puis réessayez.",
    },
    "he": {
        "hero_title": "MuseAI",
        "hero_sub": "מדריך מוזיאוני חכם שרואה, שומע ומסביר.",
        "hero_button": "התחל סיור במוזיאון",
        "step1_title": "שלב 1 – צלמו את הפריט",
        "step1_hint": "צלמו פריט כדי לפתוח את הסיור.",
        "scanning": "סורק את התמונה… רגע אחד.",
        "step2_title": "שלב 2 – דברו עם MuseAI",
        "step2_hint": "לחצו על המיקרופון ושאלו בקול. אין צורך להקליד.",
        "error_title": "אירעה שגיאה",
        "error_body": "משהו לא עבד כמצופה. נסו שוב או צלמו את הפריט מחדש. אם זה ממשיך לקרות, המתינו רגע ונסו שוב.",
    },
}


def get_lang_label(lang_code: STRINGS) -> str:
    for label, code in LANG_OPTIONS.items():
        if code == lang_code:
            return label
    return "English 🇬🇧"


# ------------------------------------------------------------------------------------
# Global styles (from your new UI)
# ------------------------------------------------------------------------------------

def apply_global_styles():
    st.markdown(
        """
        <style>
        /* App background + text */
        .stApp {
            background-color: #050608;
            color: #f5f5f5;
        }
        /* Reduce default padding */
        .block-container {
            padding-top: 1.8rem;
        }
        /* Hide Streamlit's default white header */
        header {visibility: hidden;}

        /* Make the MUSEAI logo link white and remove underline */
        .logo-link {
            color: #ffffff !important;
            text-decoration: none !important;
        }

        .logo-link:hover {
            opacity: 0.8; /* subtle hover effect */
        }

        /* Logo pill */
        .muse-logo-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.25rem 0.9rem;
            border-radius: 999px;
            background: #111318;           /* slightly lighter than bg */
            border: 1px solid #252834;
            font-weight: 600;
            letter-spacing: 0.18em;
            font-size: 0.65rem;
            text-transform: uppercase;
        }

        /* Keep logo + language on same vertical line */
        .lang-select-box .stSelectbox > div {
            margin-top: 0;          /* remove extra top gap above select */
        }

        /* Hero card */
        .hero-card {
            background: radial-gradient(circle at top, #171922 0, #06070a 55%);
            border-radius: 1.6rem;
            padding: 3rem 2.8rem 2.4rem;
            box-shadow: 0 18px 45px rgba(0,0,0,0.75);
            max-width: 520px;
            margin: 4rem auto 3rem auto;
            text-align: center;
        }
        .hero-title {
            font-size: 2.4rem;
            font-weight: 650;
            margin-bottom: 0.5rem;
        }
        .hero-sub {
            font-size: 0.95rem;
            opacity: 0.86;
            margin-bottom: 2.2rem;
        }

        /* Buttons – global style + hover + pressed */
        .stButton > button {
            border-radius: 999px;
            padding: 0.7rem 1.9rem;
            border: 1px solid #f5f5f5;
            background: #f5f5f5;
            color: #050608;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(0,0,0,0.55);
            transition: all 0.13s ease-out;
        }
        .stButton > button:hover {
            background: #ffffff;
            border-color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 14px 32px rgba(0,0,0,0.7);
        }
        .stButton > button:active {
            transform: translateY(1px) scale(0.99);
            box-shadow: 0 6px 18px rgba(0,0,0,0.55);
        }

        # /* Language select – shrink width a bit (top-right) */
        # .lang-select-box .stSelectbox > div > div {
        #     max-width: 170px;
        # }

        /* TOP language select – dark mode */
        .lang-select-box .stSelectbox > div > div {
            max-width: 170px;
            background: #111318 !important;
            color: #f5f5f5 !important;
            border-radius: 10px !important;
            border: 1px solid #252834 !important;
        }
        
        /* Chat bubbles */
        .bubble-assistant {
            background: #181a23;
            padding: 0.7rem 0.9rem;
            border-radius: 0.9rem;
            margin-bottom: 0.45rem;
            color: #f5f5f5;
        }
        .bubble-user {
            background: #273646;
            padding: 0.7rem 0.9rem;
            border-radius: 0.9rem;
            margin-bottom: 0.45rem;
            color: #ffffff;
            text-align: right;
        }

        /* Remove the sidebar collapse / expand toggle button completely */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }

        /* Audio input label ("Tap to record your question") */
        [data-testid="stAudioInput"] label {
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }
        
        /* ===== CAMERA AREA DARK MODE FIX ===== */
        [data-testid="stCameraInput"] {
            background-color: #111318 !important;    /* dark background */
            border-radius: 12px !important;
            border: 1px solid #2c2f3a !important;
            padding: 1rem !important;
        }

        /* Camera inner container (the big white box) */
        [data-testid="stCameraInput"] > div {
            background-color: #111318 !important;
        }

        /* Permission message ("This app would like to use your camera.") */
        [data-testid="stCameraInput"] label {
            color: #121212 !important;               /* make visible */
            font-size: 0.9rem !important;
            opacity: 1 !important;
        }

        /* The link "Learn how to allow access" */
        [data-testid="stCameraInput"] a {
            color: #61a8ff !important;               /* light blue for contrast */
            text-decoration: underline !important;
        }


        /* === Camera buttons: base + hover + active === */
        [data-testid="stCameraInput"] button {
            opacity: 1 !important;
            visibility: visible !important;
            background: #111318 !important;          /* dark pill */
            color: #ffffff !important;               /* white text */
            border: 1px solid #2c2f3a !important;
            border-radius: 0px 0px 10px10px !important;
            padding: 0.5rem 1.4rem !important;
            font-weight: 600 !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.65);
            transition: all 0.12s ease-out;
        }

        /* Hover state */
        [data-testid="stCameraInput"] button:hover {
            background: #151824 !important;
            border-color: #3a3e4c !important;
            transform: translateY(-1px);
            box-shadow: 0 14px 30px rgba(0,0,0,0.75);
        }

        /* Pressed state */
        [data-testid="stCameraInput"] button:active {
            transform: translateY(1px) scale(0.99);
            box-shadow: 0 7px 18px rgba(0,0,0,0.6);
        }

        /* ===== SIDEBAR – dark like main area & nice button ===== */
        [data-testid="stSidebar"] {
            background: #050608; /* same dark base as main area */
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        /* Sidebar text colour + size */
        [data-testid="stSidebar"] * {
            color: #f7f7f7 !important;
            font-size: 0.9rem;
        }

        /* Sidebar language select – darker box, decent contrast */
        [data-testid="stSidebar"] .stSelectbox > div > div {
            background: #111318;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.18);
        }

        /* Sidebar primary button (Start new artifact tour) */
        [data-testid="stSidebar"] .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.25) !important;
            background: #0b0c10;
            color: #f5f5f5;
            font-weight: 600;
            padding: 0.55rem 1.6rem;
            box-shadow: 0 10px 24px rgba(0,0,0,0.65);
            transition: all 0.12s ease-out;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #111317;
            transform: translateY(-1px);
            border-color: rgba(255,255,255,0.35) !important;
            box-shadow: 0 14px 30px rgba(0,0,0,0.75);
        }
        [data-testid="stSidebar"] .stButton > button:active {
            transform: translateY(1px) scale(0.99);
            box-shadow: 0 7px 18px rgba(0,0,0,0.6);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------------------------
# Session state helpers
# ------------------------------------------------------------------------------------

def init_session_state():
    if "started" not in st.session_state:
        st.session_state.started = False  # splash vs main UI

    if "language" not in st.session_state:
        st.session_state.language: LanguageCode = "en"

    if "artifact" not in st.session_state:
        st.session_state.artifact = None  # dict from classify_artifact_from_image

    if "artifact_image_path" not in st.session_state:
        st.session_state.artifact_image_path: str | None = None

    if "chat" not in st.session_state:
        # List of {role: "assistant"/"user", "text": str}
        st.session_state.chat = []

    if "last_audio_path" not in st.session_state:
        st.session_state.last_audio_path = None

    # keep track of recognition state + last camera frame to avoid re-running
    if "is_recognizing" not in st.session_state:
        st.session_state.is_recognizing = False

    if "last_camera_bytes" not in st.session_state:
        st.session_state.last_camera_bytes = None


def reset_tour():
    """Reset state for a brand-new artifact tour."""
    st.session_state.artifact = None
    st.session_state.artifact_image_path = None
    st.session_state.chat = []
    st.session_state.last_audio_path = None
    st.session_state.is_recognizing = False
    st.session_state.last_camera_bytes = None


# ------------------------------------------------------------------------------------
# UI building blocks
# ------------------------------------------------------------------------------------

def render_top_bar():
    """
    Top strip with logo + language dropdown ONLY on splash screen.
    After the tour has started, we show just the logo (no language box on main page).
    """

    # Make sure 'started' exists even if init didn't run yet
    started = st.session_state.get("started", False)

    if not started:
        # SPLASH SCREEN STATE → logo + LANGUAGE DROPDOWN (top-right)
        current_label = get_lang_label(st.session_state.language)

        col_logo, col_spacer, col_lang = st.columns([1.2, 5, 1.4])

        with col_logo:
            st.markdown(
                "<a class='logo-link' href='/'><div class='muse-logo-pill'>MUSEAI</div></a>",
                unsafe_allow_html=True,
             )


        with col_lang:
            st.markdown("<div class='lang-select-box'>", unsafe_allow_html=True)
            selected_top_label = st.selectbox(
                " ",  # no label
                options=list(LANG_OPTIONS.keys()),
                index=list(LANG_OPTIONS.keys()).index(current_label),
                key="_top_lang_select",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # sync language from splash top-right selector
        st.session_state.language = LANG_OPTIONS[selected_top_label]

    else:
        # MAIN SCREEN STATE → ONLY LOGO (no language select here)
        col_logo, col_spacer = st.columns([1.2, 6])
        with col_logo:
            st.markdown(
                "<a class='logo-link' href='/'><div class='muse-logo-pill'>MUSEAI</div></a>",
                unsafe_allow_html=True,
            )
        # no col_lang, so no top-right dropdown on main page

def show_splash_screen():
    """Splash screen before the main UI – using STRINGS for text."""
    txt = STRINGS.get(st.session_state.language, STRINGS["en"])

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{txt['hero_title']}</div>
            <div class="hero-sub">{txt['hero_sub']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    center_col = st.columns([3, 2, 3])[1]
    with center_col:
        start_clicked = st.button(txt["hero_button"], use_container_width=True)

    if start_clicked:
        st.session_state.started = True
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("### MuseAI Tour")
        st.write("Your multilingual museum companion.")

        # Language selector (kept same logic, synced via session_state.language)
        current_label = get_lang_label(st.session_state.language)
        selected_label = st.selectbox(
            "Language",
            options=list(LANG_OPTIONS.keys()),
            index=list(LANG_OPTIONS.keys()).index(current_label),
            key="_sidebar_lang_select",
        )
        st.session_state.language = LANG_OPTIONS[selected_label]

        st.markdown("---")
        if st.button("Start new artifact tour", use_container_width=True):
            reset_tour()
            st.rerun()

        st.markdown("---")
        st.caption(
            "Tip: Aim the camera at the artifact, then speak your question to begin.\n Enjoy the Tour!"
        )


def render_artifact_header():
    """Top card showing captured artifact preview + title."""
    st.subheader("Current artifact")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.session_state.artifact_image_path:
            st.image(st.session_state.artifact_image_path, caption="Captured")

    with col2:
        if st.session_state.artifact:
            title = st.session_state.artifact.get("title") or "Unknown artifact"
            st.markdown(f"You’re now looking at: {title}")
        else:
            st.markdown(
                "_No artifact yet. Start by taking a photo below to begin your tour._"
            )


def handle_camera_step():
    """
    Step 1 – Take a picture of the artifact.
    We save the image to disk and call the Vision pipeline.
    """
    txt = STRINGS.get(st.session_state.language, STRINGS["en"])

    st.markdown(f"### {txt['step1_title']}")
    # Hint under the heading
    st.caption(txt["step1_hint"])

    # Use a fixed key so the widget state survives reruns
    img_file = st.camera_input(" ", key="camera_capture", label_visibility="collapsed")

    # No image yet – just show a gentle hint (we already showed step1_hint)
    if img_file is None and not st.session_state.artifact:
        return

    if img_file is not None:
        img_bytes = img_file.getvalue()

        # Detect if this is a NEW photo vs the same frame causing re-runs
        is_new_photo = (
            st.session_state.last_camera_bytes is None
            or st.session_state.last_camera_bytes != img_bytes
        )

        if is_new_photo and not st.session_state.is_recognizing:
            st.session_state.is_recognizing = True
            st.session_state.last_camera_bytes = img_bytes

            # Save captured image to a temp file so our existing vision pipeline
            # (which expects a file path) can use it.
            tmp_dir = BASE_DIR / "data" / "tmp_images"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            img_path = tmp_dir / "captured_artifact.jpg"
            img_path.write_bytes(img_bytes)

            # Store for UI preview
            st.session_state.artifact_image_path = str(img_path)

            with st.spinner(txt["scanning"]):
                vision_result = classify_artifact_from_image(img_path)

            st.session_state.artifact = vision_result

            # First assistant message after recognition
            title = vision_result.get("title") or "Unknown Artifact"
            opening_line = (
                f"Great shot! I believe this is {title}. "
                "I'm MuseAI, your museum guide. "
                "Ask me anything about its history, meaning, or purpose."
            )

            # Only add the opening line once per tour
            if not st.session_state.chat:
                st.session_state.chat.append({"role": "assistant", "text": opening_line})

            st.session_state.is_recognizing = False

    # Status under the camera
    if st.session_state.is_recognizing:
        st.info("⏳ Image received! MuseAI is analyzing it…")

    elif st.session_state.artifact:
        st.success("📸 Your photo has been analyzed. Scroll down to continue.")

    else:
        st.caption("If nothing appears, try taking another photo.")


def render_conversation_area():
    txt = STRINGS.get(st.session_state.language, STRINGS["en"])

    st.markdown(f"### {txt['step2_title']}")

    if not st.session_state.artifact:
        st.info("Take a photo of an artifact first to unlock the voice companion.")
        return

    st.write(txt["step2_hint"])

    # Real microphone input
    audio_file = st.audio_input("Tap to record your question")

    # Render existing chat history
    st.markdown("### Conversation so far")
    for msg in st.session_state.chat:
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

    # No new recording yet → just show the history
    if audio_file is None:
        return

    with st.spinner("Transcribing your question…"):
        audio_bytes = audio_file.getvalue()
        # Auto-detect between English / French / Hebrew
        transcript, detected_lang = transcribe_and_detect_language(audio_bytes)

    if not transcript:
        st.error("I couldn’t hear anything. Please try speaking again.")
        return

    # Add user message to chat
    st.session_state.chat.append({"role": "user", "text": transcript})

    # Decide which language to answer in
    if detected_lang in ("en", "fr", "he"):
        reply_language = detected_lang
        # keep UI language in sync with what we detected
        st.session_state.language = detected_lang
    else:
        reply_language = "en"

    artifact_id = None
    if isinstance(st.session_state.artifact, dict):
        artifact_id = st.session_state.artifact.get("artifact_id")

    # If we don't support the detected language, prepend a short notice
    notice_prefix = ""
    if detected_lang not in ("en", "fr", "he"):
        notice_prefix = (
            "I heard a language I don’t fully support yet. "
            "I’ll answer in English for now.\n\n"
        )

    with st.spinner("Thinking about the best answer…"):
        llm_raw = museai_reason(
            user_query=transcript,
            artifact_id=artifact_id,
            language=reply_language,
        )

    # Handle both string or dict response from museai_reason
    if isinstance(llm_raw, dict):
        answer_text = (
            llm_raw.get("answer")
            or llm_raw.get("text")
            or str(llm_raw)
        )
    else:
        answer_text = str(llm_raw)

    # Add any notice prefix (for unsupported languages)
    answer_text = notice_prefix + answer_text

    # Add assistant message to chat
    st.session_state.chat.append({"role": "assistant", "text": answer_text})

    # Text → speech
    with st.spinner("Preparing audio answer…"):
        audio_out_path = tts_generate_audio(
            text=answer_text,
            language=reply_language,
        )
        st.session_state.last_audio_path = audio_out_path

    st.success("New answer from MuseAI 👇")
    if st.session_state.last_audio_path:
        st.audio(st.session_state.last_audio_path)


# ------------------------------------------------------------------------------------
# Main app
# ------------------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="MuseAI – Multimodal Museum Companion",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="expanded",  # 👉 always show sidebar, no collapse
    )

    apply_global_styles()
    init_session_state()

    # Top bar (logo + language) – always visible
    render_top_bar()

    # Splash vs main
    if not st.session_state.started:
        show_splash_screen()
        return

    # Layout: sidebar + main content
    render_sidebar()

    st.title("MuseAI Tour")

    # Top artifact header
    render_artifact_header()
    st.markdown("---")

    # Two main steps
    handle_camera_step()
    st.markdown("---")
    render_conversation_area()


if __name__ == "__main__":
    main()