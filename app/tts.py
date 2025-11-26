"""
TTS module for MuseAI.
Handles multilingual text-to-speech using ElevenLabs v3 with a unified voice.
"""

import os
import streamlit as st

from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

# === Paths & env ===
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Try local .env first (for your laptop), then Streamlit Cloud secrets
ELEVEN_API_KEY = (
    os.getenv("ELEVENLABS_API_KEY")
    or st.secrets.get("ELEVENLABS_API_KEY")
)

if not ELEVEN_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is not set in environment or secrets")

VOICE_ID_MULTI = (
    os.getenv("VOICE_ID_MULTI")
    or st.secrets.get("VOICE_ID_MULTI")
)
if not VOICE_ID_MULTI:
    raise RuntimeError("VOICE_ID_MULTI is not set in environment or secrets")

client = ElevenLabs(api_key=ELEVEN_API_KEY)


def tts_generate_audio(text: str, language: str = "en") -> str:
    """
    Generate multilingual speech using ElevenLabs v3.
    One universal multilingual voice ID.
    """
    
    output_dir = BASE_DIR / "data" / "audio_output"
    output_dir.mkdir(exist_ok=True, parents=True)

    out_path = output_dir / f"tts_{language}.mp3"

    audio_stream = client.text_to_speech.convert(
        voice_id=VOICE_ID_MULTI,
        model_id="eleven_v3",
        text=text,
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.9,
            style=0.3,
            use_speaker_boost=True
        )
    )

    with open(out_path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    return str(out_path)


if __name__ == "__main__":
    demo_path = tts_generate_audio("Hello from MuseAI test.", language="en")
    print("Generated demo audio at:", demo_path)





# # ===== Manual Test (TTS verification) =====
# """
# This block allows you to manually test the TTS pipeline from the terminal.

# Run this from the project root:

#     (venv) python app/tts.py

# It will:
#     - Generate short demo audio clips in English, French, and Hebrew
#     - Use the multilingual ElevenLabs voice you configured
#     - Save the resulting .mp3 files in: data/audio_output/

# This is useful for confirming:
#     Your ElevenLabs API key is working
#     Your VOICE_ID_MULTI supports multilingual output
#     Audio files are being generated and saved correctly
# """

# # app/test_tts.py

# from app.tts import tts_generate_audio

# if __name__ == "__main__":
#     texts = {
#         "en": (
#             "Welcome to the museum. I am MuseAI, your virtual guide. "
#             "Ask me anything about the artifacts you see."
#         ),
#         "fr": (
#             "Bienvenue au musée. Je suis MuseAI, votre guide virtuel. "
#             "Demandez-moi tout ce que vous voulez sur les objets que vous voyez."
#         ),
#         "he": (
#             "ברוכים הבאים למוזיאון. אני מְיוּז־איי, המדריך הווירטואלי שלכם. "
#             "תוכלו לשאול אותי כל דבר על המוצגים שאתם רואים."
#         ),
#     }

#     for lang, text in texts.items():
#         print(f"\nGenerating audio for: {lang} ...")
#         out_path = tts_generate_audio(text, language=lang)
#         print("Saved to:", out_path)

    