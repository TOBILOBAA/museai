import os
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

# === Paths & env ===
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is not set in .env")

VOICE_ID_MULTI = os.getenv("VOICE_ID_MULTI")
if not VOICE_ID_MULTI:
    raise RuntimeError("VOICE_ID_MULTI is not set in .env")

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



    