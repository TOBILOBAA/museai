import vertexai
from vertexai.generative_models import GenerativeModel
from app.rag import build_context_for_artifact_id, build_context_for_query

def museai_reason(
    user_query: str,
    artifact_id: int | None,
    language: str = "en",
):
    """
    - If artifact_id is known (from Vision), pull artifact-specific RAG context
    - Otherwise use query-based RAG search
    - Then pass both into Gemini for reasoning
    """

    if artifact_id:
        rag_context = build_context_for_artifact_id(artifact_id)
    else:
        rag_context = build_context_for_query(user_query, k=3)

    system_prompt = f"""
You are MuseAI, a multilingual museum companion.

Language to reply in: {language}

Use ONLY factual information from the RAG context below.
If external knowledge is used, mark it as: "[additional context]".

RAG CONTEXT:
{rag_context}
"""

    model = GenerativeModel("gemini-2.0-flash-001")

    response = model.generate_content(
        [system_prompt, user_query],
        generation_config={"temperature": 0.4}
    )

    return response.text.strip()