# app/test_full_pipeline.py

from pathlib import Path

from app.voice import transcribe_audio_file
from app.reasoning import museai_reason
from app.tts import tts_generate_audio


def main():
    base_dir = Path(__file__).resolve().parent.parent

    # 1) Use your existing WAV recording
    audio_path = base_dir / "data" / "audio" / "sample_en.wav"
    print(f"🎤 Using audio file: {audio_path}")

    # 2) Speech-to-Text
    print("\n=== STEP 1: SPEECH-TO-TEXT (Google STT) ===")
    transcript = transcribe_audio_file(audio_path, lang="en", sample_rate_hz=48000)

    print("\nTranscript:\n")
    print(transcript or "[EMPTY TRANSCRIPT]")

    if not transcript.strip():
        print("\n⚠️ Transcript is empty — stopping test.")
        return

    # For demo: assume the user is standing in front of artifact_id = 3 (Torah Crown)
    artifact_id = 3

    languages = [
        ("en", "English"),
        ("fr", "French"),
        ("he", "Hebrew"),
    ]

    for lang_code, lang_label in languages:
        print("\n" + "=" * 70)
        print(f"=== {lang_label.upper()} RESPONSE ===")
        print("=" * 70)

        # 3) RAG + LLM reasoning
        raw_answer = museai_reason(
            user_query=transcript,
            artifact_id=artifact_id,
            language=lang_code,
        )

        print("\n💬 Raw LLM Answer:")
        print(raw_answer)

        # Handle both dict and plain string cases
        if isinstance(raw_answer, dict):
            answer_text = raw_answer.get("answer", "").strip()
        else:
            answer_text = str(raw_answer).strip()

        if not answer_text:
            print("⚠️ Empty answer_text, skipping TTS for this language.")
            continue

        print("\n💬 Final text to speak:")
        print(answer_text)

        # 4) Text-to-Speech
        audio_out = tts_generate_audio(answer_text, language=lang_code)
        print(f"\n🔊 TTS saved to: {audio_out}")


if __name__ == "__main__":
    main()