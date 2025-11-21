import io
import os
from pathlib import Path
from typing import Literal

import streamlit as st

from app.vision import classify_artifact_from_image
from app.voice import transcribe_and_detect_language, LanguageCode
from app.reasoning import museai_reason
from app.tts import tts_generate_audio

# ------------------------------------------------------------------------------------
# Basic config
# ------------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

LanguageCode = Literal["en", "fr", "he"]

LANG_OPTIONS = {
    "English 🇬🇧": "en",
    "Français 🇫🇷": "fr",
    "עברית 🇮🇱": "he",
}


def get_lang_label(lang_code: LanguageCode) -> str:
    for label, code in LANG_OPTIONS.items():
        if code == lang_code:
            return label
    return "English 🇬🇧"


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

    # NEW: keep track of recognition state + last camera frame to avoid re-running
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

def show_splash_screen():
    """Simple splash screen before the main UI."""
    st.markdown(
        """
        <div style="height: 100vh; display: flex; flex-direction: column;
                    align-items: center; justify-content: center;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">MuseAI</h1>
            <p style="font-size: 1.2rem; opacity: 0.8;">
                Multimodal Museum Companion
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Enter MuseAI tour", type="primary"):
        st.session_state.started = True
        st.rerun()  # replace experimental_rerun


def render_sidebar():
    with st.sidebar:
        st.markdown("### MuseAI Tour")
        st.write("Your multilingual museum companion.")

        # Language selector
        current_label = get_lang_label(st.session_state.language)
        selected_label = st.selectbox(
            "Language",
            options=list(LANG_OPTIONS.keys()),
            index=list(LANG_OPTIONS.keys()).index(current_label),
        )
        st.session_state.language = LANG_OPTIONS[selected_label]

        st.markdown("---")
        if st.button("Start new artifact tour", use_container_width=True):
            reset_tour()
            st.rerun()  # replace experimental_rerun

        st.markdown("---")
        st.caption(
            "Tip: Aim the camera at the artifact, then speak your question "
            "once MuseAI has identified it."
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
            st.markdown(f"**You’re now looking at:** {title}")
        else:
            st.markdown(
                "_No artifact yet. Start by taking a photo below to begin your tour._"
            )


def handle_camera_step():
    """
    Step 1 – Take a picture of the artifact.
    We save the image to disk and call the Vision pipeline.
    """
    st.markdown("### Step 1 – Capture the artifact")

    # Use a fixed key so the widget state survives reruns
    img_file = st.camera_input("Point at an artifact and take a photo", key="camera_capture")

    # No image yet – just show a gentle hint
    if img_file is None and not st.session_state.artifact:
        st.caption("Take a photo of an artifact to unlock the voice companion.")
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

            with st.spinner("Trying to recognize your artifact…"):
                vision_result = classify_artifact_from_image(img_path)

            st.session_state.artifact = vision_result

            # First assistant message after recognition
            title = vision_result.get("title") or "this artifact"
            opening_line = (
                f"Great shot! I believe this is **{title}**. "
                "I'm MuseAI, your museum guide. "
                "Ask me anything about its history, meaning, or how it was used."
            )

            # Only add the opening line once per tour
            if not st.session_state.chat:
                st.session_state.chat.append({"role": "assistant", "text": opening_line})

            st.session_state.is_recognizing = False

    # Status under the camera
    if st.session_state.is_recognizing:
        st.info("⏳ Trying to recognize your artifact…")
    elif st.session_state.artifact:
        st.success("✅ Artifact recognized! Scroll down to start talking to MuseAI.")
    else:
        st.caption("Take a photo of an artifact to unlock the voice companion.")


def render_conversation_area():
    st.markdown("### Step 2 – Talk to MuseAI")

    if not st.session_state.artifact:
        st.info("Take a photo of an artifact first to unlock the voice companion.")
        return

    st.write(
        "Hold the mic button below, ask your question, and release when you’re done."
    )

    # Real microphone input
    audio_file = st.audio_input("Tap to record your question")

    # Render existing chat history
    st.markdown("### Conversation so far")
    for msg in st.session_state.chat:
        if msg["role"] == "assistant":
            st.markdown(
                f"<div style='background:#f3f3fb;padding:0.6rem 0.8rem;"
                f"border-radius:0.6rem;margin-bottom:0.4rem;'>🤖 {msg['text']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:#e9f7ff;padding:0.6rem 0.8rem;"
                f"border-radius:0.6rem;margin-bottom:0.4rem;text-align:right;'>🧑 {msg['text']}</div>",
                unsafe_allow_html=True,
            )

    # No new recording yet → just show the history
    if audio_file is None:
        return

    # ---------------------------------------------------------------
    # Once we have audio, run the full pipeline:
    # STT (with language detection) -> RAG reasoning -> TTS,
    # then append to chat.
    # ---------------------------------------------------------------
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
    )

    init_session_state()

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