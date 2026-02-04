import os
import vertexai

from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional
from vertexai.generative_models import GenerativeModel
from app.rag import build_context_for_artifact_id, build_context_for_query


# ===== Environment & Vertex config =====
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
LLM_MODEL_NAME = "gemini-2.0-flash-001"   


def init_vertex():
    """Initialize Vertex AI once per process."""
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is missing from environment.")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)


def get_llm() -> GenerativeModel:
    init_vertex()
    return GenerativeModel(LLM_MODEL_NAME)


# ===== Language switching helpers =====
SWITCH_TO_EN = ["switch to english", "speak english", "english please"]
SWITCH_TO_FR = ["switch to french", "parle francais", "parlez français", "french please"]
SWITCH_TO_HE = ["תדבר עברית", "דבר איתי בעברית", "עברית בבקשה"]


def detect_language_switch(user_query: str) -> Optional[str]:
    q = user_query.lower()

    if any(p in q for p in SWITCH_TO_EN):
        return "en"
    if any(p in q for p in SWITCH_TO_FR):
        return "fr"
    if any(p in q for p in SWITCH_TO_HE):
        return "he"

    return None  # no language change requested


# ===== Main reasoning function used by the app =====
def museai_reason(
    user_query: str,
    artifact_id: Optional[int],
    language: str = "en",
) -> Dict[str, str]:
    """
    Central 'brain' for MuseAI.

    - Checks if user wants to switch language.
    - If artifact_id is known (from Vision), uses artifact-specific RAG.
    - Otherwise, uses query-based RAG search.
    - Calls Gemini to generate an answer in the current language.

    Returns:
        {
          "answer": <string>,
          "language": <"en" | "fr" | "he">
        }
    """

    # Language switching
    switch = detect_language_switch(user_query)
    if switch:
        new_lang = switch
        confirmations = {
            "en": "Okay, switching to English.",
            "fr": "Très bien, je passe au français.",
            "he": "בסדר, אנחנו עוברים לעברית."
        }
        return {
            "answer": confirmations[new_lang],
            "language": new_lang,
        }

    # Build RAG context
    if artifact_id is not None:
        rag_context = build_context_for_artifact_id(artifact_id)
    else:
        rag_context = build_context_for_query(user_query, k=3)

    # Prompt for the LLM
    # - Use the museum context below as your primary source.
    prompt = f"""
You are MuseAI, a multilingual museum guide.

- Answer STRICTLY in this language: {language}.
- Do NOT switch languages.
- Do NOT translate unless asked.
- If you add information from outside the context, mark it with "[additional context]".
- If you genuinely don't know, say that you are not sure.

Museum context:
----------------
{rag_context}
----------------

User question:
{user_query}

Now respond in a clear, friendly way.
"""

    model = get_llm()
    response = model.generate_content(prompt)

    return {
        "answer": response.text.strip(),
        "language": language,
    }





# -----------------------------------------------------------------------------
# OPTIONAL MANUAL TEST FOR THIS MODULE
#
# If you want to test the reasoning pipeline independently (without Streamlit),
# create a new file:
#
#     app/test_reasoning.py
#
# And paste the following code into it:
#
# -----------------------------------------------------------------------------
# app/test_reasoning.py

# from pathlib import Path
# import sys
# from dotenv import load_dotenv

# # --- Make sure the project root is on sys.path ---
# ROOT = Path(__file__).resolve().parent.parent  # /.../museai
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))

# # Load .env so Vertex / GCP works
# load_dotenv(ROOT / ".env")

# # NOW this import will work
# from app.reasoning import museai_reason


# def main():
#     # -------- Case 1: artifact_id known (e.g., from Vision) --------
#     print("\n=== Test 1: Known artifact_id (Torah Crown, id=3) ===\n")
#     answer1 = museai_reason(
#         user_query="Tell me about the religious and cultural role of this object.",
#         artifact_id=3,
#         language="en",
#     )
#     print(answer1)

#     # -------- Case 2: No artifact_id, only free-form query --------
#     print("\n=== Test 2: Query-based RAG (no artifact id) ===\n")
#     answer2 = museai_reason(
#         user_query="Which artifact in the museum collection relates to warfare?",
#         artifact_id=None,
#         language="en",
#     )
#     print(answer2)

#     # -------- Case 3: Same thing but in French --------
#     print("\n=== Test 3: French answer ===\n")
#     answer3 = museai_reason(
#         user_query="Parle-moi brièvement de cet objet.",
#         artifact_id=1,
#         language="fr",
#     )
#     print(answer3)


# if __name__ == "__main__":
#     main()