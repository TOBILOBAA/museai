from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from typing import Literal

from google.cloud import speech_v1p1beta1 as speech

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
    Create a SpeechClient using the credentials from GOOGLE_APPLICATION_CREDENTIALS.
    Safe to call multiple times; the underlying channel is reused by gRPC.
    """
    if not GCP_PROJECT_ID:
        # Not strictly needed by Speech, but good sanity check for our env
        raise RuntimeError("GCP_PROJECT_ID is not set in environment (.env).")
    return speech.SpeechClient()


def transcribe_audio_bytes(
    audio_bytes: bytes,
    lang: LanguageCode = "en",
    sample_rate_hz: int = 48000,
) -> str:
    """
    Main function you will call from the app.

    Parameters
    ----------
    audio_bytes : bytes
        Raw audio bytes (e.g. from Streamlit mic input or a WAV file).
    lang : 'en' | 'he' | 'fr'
        Desired transcription language.
    sample_rate_hz : int
        Sample rate of the audio. For now we assume 48 kHz
        (we can adjust later when we integrate Streamlit).

    Returns
    -------
    transcript : str
        Concatenated transcript text.
    """
    client = _get_speech_client()
    language_code = get_gcp_language_code(lang)

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hz,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="default",
    )

    response = client.recognize(config=config, audio=audio)

    # Join all results into a single sentence/paragraph
    chunks = [result.alternatives[0].transcript for result in response.results]
    transcript = " ".join(chunks).strip()
    return transcript


def transcribe_audio_file(
    file_path: str | Path,
    lang: LanguageCode = "en",
    sample_rate_hz: int = 48000,
) -> str:
    """
    Convenience helper for CLI testing.

    Reads a local audio file (e.g., a small mono 16kHz WAV) and
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