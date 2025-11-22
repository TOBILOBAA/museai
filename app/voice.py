from dotenv import load_dotenv
load_dotenv()

import os
import json
from pathlib import Path
from typing import Literal, Tuple

from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account


# ===== Config / Environment =====

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# Not strictly required by the v1 speech API, but we keep it for consistency
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Short codes we’ll use in the app
LanguageCode = Literal["en", "he", "fr"]

LANGUAGE_CODE_MAP = {
    "en": "en-US",   # English
    "he": "he-IL",   # Hebrew
    "fr": "fr-FR",   # French
}

def _load_service_account_credentials():
    """
    Load service account credentials from either:
    - Streamlit Cloud secrets["GCP_SERVICE_ACCOUNT_JSON"], or
    - env var GCP_SERVICE_ACCOUNT_JSON (as JSON string).

    Returns:
        google.oauth2.service_account.Credentials or None
    """
    sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")

    if not sa_json:
        try:
            import streamlit as st  # type: ignore
            if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
                raw = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
                if isinstance(raw, dict):
                    info = raw
                else:
                    info = json.loads(str(raw))
                return service_account.Credentials.from_service_account_info(info)
        except Exception:
            return None
    else:
        try:
            info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(info)
        except json.JSONDecodeError:
            raise RuntimeError("GCP_SERVICE_ACCOUNT_JSON is not valid JSON")

    return None

def get_gcp_language_code(lang: LanguageCode) -> str:
    """
    Map our short app language codes ('en', 'he', 'fr')
    to Google Cloud Speech language codes.
    """
    try:
        return LANGUAGE_CODE_MAP[lang]
    except KeyError:
        raise ValueError(f"Unsupported language: {lang}")


# ===== Core STT functions =====



def _get_speech_client() -> speech.SpeechClient:
    """
    Create a SpeechClient using explicit service account credentials if available.
    Falls back to Application Default Credentials for local dev.
    """
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment (.env or secrets).")

    creds = None
    try:
        import streamlit as st

        if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
            sa_value = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

            if isinstance(sa_value, dict):
                info = sa_value
            else:
                info = json.loads(sa_value)

            creds = service_account.Credentials.from_service_account_info(info)
            print("[voice._get_speech_client] Using service account from Streamlit secrets")
    except Exception as e:
        print(f"[voice._get_speech_client] Could not load SA from secrets, will try ADC. Error: {e}")
        creds = None

    if creds is not None:
        # ✅ Streamlit Cloud path
        return speech.SpeechClient(credentials=creds)
    else:
        # ✅ Local dev path (GOOGLE_APPLICATION_CREDENTIALS, gcloud, etc.)
        print("[voice._get_speech_client] Using default application credentials (local dev).")
        return speech.SpeechClient()


def _recognize_with_multilang(
    audio_bytes: bytes,
    lang_hint: LanguageCode | None = None,
) -> Tuple[str, LanguageCode]:
    """
    Internal helper:
    - Uses one primary language (hint) + the others as alternatives.
    - Lets Google decide which of EN / FR / HE was actually spoken.
    - Returns (transcript, detected_language_code).
    """
    client = _get_speech_client()

    # Choose primary + alternatives for EN/FR/HE
    if lang_hint and lang_hint in LANGUAGE_CODE_MAP:
        primary_full = LANGUAGE_CODE_MAP[lang_hint]
    else:
        primary_full = LANGUAGE_CODE_MAP["en"]

    alt_full = [code for code in LANGUAGE_CODE_MAP.values() if code != primary_full]

    audio = speech.RecognitionAudio(content=audio_bytes)

    # NOTE: we do NOT set sample_rate_hertz here.
    # Google will read it from the WAV header, avoiding mismatch errors.
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code=primary_full,
        alternative_language_codes=alt_full,
        enable_automatic_punctuation=True,
        model="default",
    )

    response = client.recognize(config=config, audio=audio)

    # Join all results into a single sentence/paragraph
    chunks = [result.alternatives[0].transcript for result in response.results]
    transcript = " ".join(chunks).strip()

    # Try to read the detected language from the first alternative
    detected_full = primary_full
    if response.results:
        alt0 = response.results[0].alternatives[0]
        if getattr(alt0, "language_code", None):
            detected_full = alt0.language_code

    # Map back to our short LanguageCode
    detected_short: LanguageCode = "en"
    for short, full in LANGUAGE_CODE_MAP.items():
        if full == detected_full:
            detected_short = short  # type: ignore[assignment]
            break

    return transcript, detected_short


def transcribe_and_detect_language(
    audio_bytes: bytes,
    lang_hint: LanguageCode | None = None,
) -> Tuple[str, LanguageCode]:
    """
    Main function for Streamlit:
    - Takes raw audio bytes.
    - Uses EN/FR/HE as possible languages.
    - Returns (transcript, detected_language_code).
    """
    return _recognize_with_multilang(audio_bytes, lang_hint=lang_hint)


def transcribe_audio_bytes(
    audio_bytes: bytes,
    lang: LanguageCode = "en",
    sample_rate_hz: int | None = None,
) -> str:
    """
    Backwards-compatible wrapper used in CLI tests.
    Ignores sample_rate_hz and just returns transcript as a string.
    """
    transcript, _ = _recognize_with_multilang(audio_bytes, lang_hint=lang)
    return transcript


def transcribe_audio_file(
    file_path: str | Path,
    lang: LanguageCode = "en",
    sample_rate_hz: int | None = None,
) -> str:
    """
    Convenience helper for CLI testing.

    Reads a local audio file (e.g., a small mono WAV) and
    returns the transcript using transcribe_audio_bytes().
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    audio_bytes = path.read_bytes()
    return transcribe_audio_bytes(audio_bytes, lang=lang, sample_rate_hz=sample_rate_hz)


# ===== Manual test (Task 4 verification) =====

if __name__ == "__main__":
    """
    Quick manual test for the STT pipeline.

    From project root, run:

        (venv) python app/voice.py data/audio/sample_en.wav

    You’ll need to place a small WAV file at that path or change it below.
    """
    import sys

    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        # Change this to whatever test file you create later
        audio_path = "data/audio/sample_en.wav"

    print(f"Transcribing file: {audio_path}")

    try:
        text = transcribe_audio_file(audio_path, lang="en")
        print("\nTranscript:\n")
        print(text or "[EMPTY TRANSCRIPT]")
    except Exception as e:
        print("\nError during transcription:")
        print(e)