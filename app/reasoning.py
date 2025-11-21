import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

from app.rag import build_context_for_artifact_id, build_context_for_query

# ===== Environment & Vertex config =====

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
LLM_MODEL_NAME = "gemini-2.0-flash-001"   # same model you used in test_vertex


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

    # 1 — Language switching
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

    # 2 — Build RAG context
    if artifact_id is not None:
        rag_context = build_context_for_artifact_id(artifact_id)
    else:
        rag_context = build_context_for_query(user_query, k=3)

    # 3 — Prompt for the LLM
    prompt = f"""
You are MuseAI, a multilingual museum guide.

- Answer in this language: {language}.
- Use the museum context below as your primary source.
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




# import vertexai
# from vertexai.generative_models import GenerativeModel
# from app.rag import build_context_for_artifact_id, build_context_for_query

# def museai_reason(
#     user_query: str,
#     artifact_id: int | None,
#     language: str = "en",
# ):
#     """
#     - If artifact_id is known (from Vision), pull artifact-specific RAG context
#     - Otherwise use query-based RAG search
#     - Then pass both into Gemini for reasoning
#     """

#     if artifact_id:
#         rag_context = build_context_for_artifact_id(artifact_id)
#     else:
#         rag_context = build_context_for_query(user_query, k=3)

#     system_prompt = f"""
# You are MuseAI, a multilingual museum companion.

# Language to reply in: {language}

# Use ONLY factual information from the RAG context below.
# If external knowledge is used, mark it as: "[additional context]".

# RAG CONTEXT:
# {rag_context}
# """

#     model = GenerativeModel("gemini-2.0-flash-001")

#     response = model.generate_content(
#         [system_prompt, user_query],
#         generation_config={"temperature": 0.4}
#     )

#     return response.text.strip()