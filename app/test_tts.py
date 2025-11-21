# app/test_tts.py

from app.tts import tts_generate_audio

if __name__ == "__main__":
    texts = {
        "en": (
            "Welcome to the museum. I am MuseAI, your virtual guide. "
            "Ask me anything about the artifacts you see."
        ),
        "fr": (
            "Bienvenue au musée. Je suis MuseAI, votre guide virtuel. "
            "Demandez-moi tout ce que vous voulez sur les objets que vous voyez."
        ),
        "he": (
            "ברוכים הבאים למוזיאון. אני מְיוּז־איי, המדריך הווירטואלי שלכם. "
            "תוכלו לשאול אותי כל דבר על המוצגים שאתם רואים."
        ),
    }

    for lang, text in texts.items():
        print(f"\nGenerating audio for: {lang} ...")
        out_path = tts_generate_audio(text, language=lang)
        print("Saved to:", out_path)