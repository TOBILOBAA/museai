MuseAI — Multimodal Museum Companion

A vision-to-voice AI guide that sees, listens, reasons, and speaks.

MuseAI is a fully multimodal museum companion built with:
✔️ Gemini Vision → artifact recognition
✔️ FAISS RAG → artifact knowledge retrieval
✔️ Gemini Flash (LLM) → multilingual reasoning
✔️ Google Speech-to-Text → speech recognition
✔️ ElevenLabs → multilingual speech generation
✔️ Streamlit → interactive camera + audio UI

The system uses a camera snapshot to identify an artifact, listens to your spoken question, retrieves factual context from a vector database, reasons with an LLM, and speaks the answer back in English, French, or Hebrew.

⸻

🚀 Features

🔍 1. Vision Recognition (Gemini Vision)
	•	Users capture an artifact using the camera.
	•	Model compares image with your artifact dataset (artifacts.csv).
	•	Returns artifact ID, title, confidence, and reasoning.

📚 2. RAG (FAISS Vectorstore)
	•	Builds a text-embedding index of artifact metadata using text-embedding-004.
	•	Used for:
	•	Query-based retrieval
	•	Artifact ID → Context retrieval

🧠 3. Multilingual LLM Reasoning
	•	Reasoning powered by Gemini Flash.
	•	Answers in the user’s preferred language.
	•	Safely blends RAG context + LLM knowledge.

🎤 4. Speech-to-Text (Google STT)
	•	Supports English, French, Hebrew automatically.
	•	Detects the spoken language and updates UI language dynamically.

🔊 5. Text-to-Speech (ElevenLabs v3)
	•	One universal multilingual voice.
	•	Natural responses in EN/FR/HE.

💻 6. Streamlit Frontend
	•	Dark, elegant UI.
	•	Camera input, microphone input, real-time chat bubbles, and audio playback.

⸻


▶️ Running the Full App

1. Install dependencies

pip install -r requirements.txt

2. Create your .env

GCP_PROJECT_ID=your_project
GCP_LOCATION=us-central1
GCP_SERVICE_ACCOUNT_JSON="your JSON here"
ELEVENLABS_API_KEY=your_key
VOICE_ID_MULTI=your_voice_id

3. Build the vectorstore (one-time)

python app/rag.py

This creates:
	•	artifacts_index.faiss
	•	artifacts_metadata.parquet

4. Run Streamlit

streamlit run app/streamlit_app.py


⸻

💡 Development Workflow

MuseAI was built in a modular task-based flow:
	1.	Vision → Identify artifact
	2.	RAG → Build knowledge base
	3.	Voice STT → Understand speech
	4.	Reasoning → Combine all signals
	5.	TTS → Speak response
	6.	UI → Bind everything together
	7.	E2E Tests → Validate functionality on local CLI
	8.	Deployment → Streamlit Cloud + environment fixes

This ensures every component works independently before integration.

⸻

🧩 Why This Architecture?

We follow a “see → understand → reason → speak” flow:
	•	📷 Vision first: The app must know what object the user is standing in front of.
	•	🧠 RAG second: Retrieve factual metadata about that object.
	•	🎤 Voice next: Interpret the user’s spoken question.
	•	📝 Reasoning: Combine artifact + question into answer.
	•	🔊 TTS output: Deliver answer as natural audio.

Each module is independently testable and maintainable.

⸻

👥 For Developers

Add new artifacts

Edit data/artifacts.csv, then rebuild FAISS index:

python app/rag.py

Swap languages

Update LANGUAGE_CODE_MAP in voice.py, and TTS still works automatically.

Swap LLM model

Change LLM_MODEL_NAME in reasoning.py.

