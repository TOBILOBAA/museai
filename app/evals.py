from __future__ import annotations

import sys 
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from app.rag import retrieve_artifacts

ROOT_DIR = Path(__file__).resolve().parent.parent  
sys.path.append(str(ROOT_DIR))



# ##############################################
# # EVALUTING RETRIEVAL QUALITY
# ##############################################

# def load_csv(path: Path) -> pd.DataFrame:
#     if not path.exists():
#         raise FileNotFoundError(f"File not found: {path}")
#     return pd.read_csv(path)


# def build_retrieval_log(
#     queries_path: Path,
#     output_path: Path,
#     k: int = 3,
# ):
#     queries_df = pd.read_csv(queries_path)
#     rows = []

#     for _, row in queries_df.iterrows():
#         query_id = row["query_id"]
#         query_text = row["query"]

#         results = retrieve_artifacts(query_text, k=k)

#         for rank, r in enumerate(results, start=1):
#             rows.append({
#                 "query_id": query_id,
#                 "query": query_text,
#                 "rank": rank,
#                 "retrieved_artifact_id": r["artifact_id"],
#                 "score": r["score"],
#             })

#     log_df = pd.DataFrame(rows)
#     output_path.parent.mkdir(parents=True, exist_ok=True)
#     log_df.to_csv(output_path, index=False)

#     return log_df


# def build_retrieval_evaluation(
#     queries_path: Path,
#     retrieval_log_path: Path,
#     ground_truth_path: Path,
#     k: int = 3,
#     output_path: Path | None = None,
# ) -> pd.DataFrame:
#     """
#     Creates a human-readable evaluation table comparing:
#     - queries
#     - retrieved artifacts
#     - ground truth
#     """

#     queries_df = load_csv(queries_path)
#     retrieval_df = load_csv(retrieval_log_path)
#     gt_df = load_csv(ground_truth_path)

#     rows = []

#     for _, q_row in queries_df.iterrows():
#         query_id = q_row["query_id"]
#         query_text = q_row["query"]

#         # ground truth artifact
#         gt_row = gt_df[gt_df["query_id"] == query_id]
#         if gt_row.empty:
#             continue
#         correct_artifact = int(gt_row.iloc[0]["relevant_artifact_id"])

#         # retrieved artifacts (ordered by rank)
#         retrieved = (
#             retrieval_df[retrieval_df["query_id"] == query_id]
#             .sort_values("rank")
#         )

#         retrieved_ids = retrieved["retrieved_artifact_id"].tolist()

#         # evaluation logic
#         correct_found = correct_artifact in retrieved_ids

#         if correct_found:
#             position = retrieved_ids.index(correct_artifact) + 1
#         else:
#             position = None

#         row = {
#             "query_id": query_id,
#             "query": query_text,
#             "retrieved_artifacts": retrieved_ids,
#             "correct_artifact": correct_artifact,
#             "correct_found": "Yes" if correct_found else "No",
#             "position_of_correct": position,
#             "hit@1": int(position == 1),
#             "hit@2": int(position is not None and position <= 2),
#             "hit@3": int(position is not None and position <= 3),
#             f"hit@{k}": int(position is not None and position <= k),
#         }

#         rows.append(row)

#     eval_df = pd.DataFrame(rows)

#     if output_path:
#         output_path.parent.mkdir(parents=True, exist_ok=True)
#         eval_df.to_csv(output_path, index=False)

#     return eval_df


# def summarize_retrieval_metrics(eval_df: pd.DataFrame, k: int = 3) -> dict:
#     return {
#         "Total Queries": len(eval_df),
#         "Recall@1": eval_df["hit@1"].mean(),
#         "Recall@2": eval_df["hit@2"].mean(),
#         "Recall@3": eval_df["hit@3"].mean(),
#         f"Recall@{k}": eval_df[f"hit@{k}"].mean(),
#     }


# def main():
#     queries_path = Path("data/queries.csv")
#     retrieval_log_path = Path("data/retrieval_log.csv")
#     ground_truth_path = Path("data/ground_truth.csv")
#     evaluation_path = Path("data/retrieval_evaluation.csv")

#     print("🔎 Building retrieval log...")
#     build_retrieval_log(
#         queries_path=queries_path,
#         output_path=retrieval_log_path,
#         k=3,
#     )

#     print("📊 Evaluating retrieval...")
#     eval_df = build_retrieval_evaluation(
#         queries_path=queries_path,
#         retrieval_log_path=retrieval_log_path,
#         ground_truth_path=ground_truth_path,
#         k=3,
#         output_path=evaluation_path,
#     )

#     metrics = summarize_retrieval_metrics(eval_df, k=3)

#     print("\n📈 Retrieval Evaluation Summary")
#     for k, v in metrics.items():
#         print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")

#     print(f"\n✅ Saved evaluation table to {evaluation_path}")


# if __name__ == "__main__":
#     main()








##########################################################
# MEASURING HOW GROUDNING EFFECTS OUTPUT ACCURACY 
##########################################################

"""
MuseAI Grounding Evaluation

GOAL
----
Measure how grounding (retrieval / RAG) affects output accuracy.

We do this by:
1. Generating answers WITHOUT grounding (no museum context)
2. Generating answers WITH grounding (RAG context)
3. Comparing both answers to the correct artifact base_context
4. Using:
   - Semantic similarity as factual accuracy
   - (1 - similarity) as hallucination proxy
5. Measuring whether grounding improves output accuracy

IMPORTANT
---------
- We DO NOT touch reasoning.py
- We DO NOT modify production logic
- Everything here is evaluation-only
"""
import time
import os
import numpy as np
import pandas as pd
from typing import Dict
from pathlib import Path

import vertexai
from vertexai.generative_models import GenerativeModel

# ---- Import retrieval & embedding utilities (read-only use) ----
from app.rag import (
    build_context_for_artifact_id,
    embed_texts,
)

# ============================================================
# Environment & Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

QUERIES_PATH = DATA_DIR / "queries.csv"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth.csv"
ARTIFACTS_PATH = DATA_DIR / "artifacts.csv"
OUTPUT_PATH = DATA_DIR / "grounding_eval.csv"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
LLM_MODEL_NAME = "gemini-2.0-flash-001"

# ============================================================
# Vertex / Gemini Setup (Evaluation Only)
# ============================================================

def init_vertex():
    """
    Initialize Vertex AI.
    This mirrors your production setup but lives ONLY in evals.
    """
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID not set.")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)


def get_llm() -> GenerativeModel:
    """
    Return Gemini 2.0 Flash model.
    """
    init_vertex()
    return GenerativeModel(LLM_MODEL_NAME)


# ============================================================
# Evaluation-only Generation Function
# ============================================================

def generate_answer_eval(
    query: str,
    context: str | None,
    language: str = "en"
) -> str:
    """
    Generate an answer using Gemini, with optional grounding context.

    WHY THIS EXISTS:
    - reasoning.py always uses grounding
    - evaluation needs to turn grounding ON / OFF
    - we recreate the SAME prompt style here
    """

    prompt = f"""
You are MuseAI, a multilingual museum guide.

- Answer in this language: {language}.
- Use the museum context below as your primary source IF provided.
- If you add information from outside the context, mark it with "[additional context]".
- If you genuinely don't know, say that you are not sure.

Museum context:
----------------
{context if context else ""}
----------------

User question:
{query}

Now respond in a clear, friendly way.
"""

    model = get_llm()
    response = model.generate_content(prompt)
    return response.text.strip()


# ============================================================
# Utility Functions
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """
    Load CSV safely.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    INTERPRETATION:
    - Higher = more semantically aligned
    - Used as factual accuracy proxy
    """
    return float(
        np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    )


def get_ground_truth_context(
    query_id: str,
    ground_truth_df: pd.DataFrame,
    artifacts_df: pd.DataFrame
) -> tuple[int, str]:
    """
    Resolve ground truth for a query.

    1. ground_truth.csv → correct artifact_id
    2. artifacts.csv → base_context (factual truth)
    """

    artifact_id = ground_truth_df.loc[
        ground_truth_df["query_id"] == query_id,
        "relevant_artifact_id"
    ].values[0]

    artifact_row = artifacts_df[
        artifacts_df["artifact_id"] == artifact_id
    ].iloc[0]

    return artifact_id, artifact_row["base_context"]


# ============================================================
# Core Evaluation Logic
# ============================================================

def evaluate_grounding_effect() -> pd.DataFrame:
    """
    Main evaluation pipeline.

    For each query:
    - Generate answer WITHOUT grounding
    - Generate answer WITH grounding
    - Compare both to ground truth
    - Measure grounding impact on output accuracy
    """

    queries_df = load_csv(QUERIES_PATH)
    ground_truth_df = load_csv(GROUND_TRUTH_PATH)
    artifacts_df = load_csv(ARTIFACTS_PATH)

    results = []

    for _, q in queries_df.iterrows():
        query_id = q["query_id"]
        query_text = q["query"]

        # --- Resolve ground truth ---
        correct_artifact_id, ground_truth_text = get_ground_truth_context(
            query_id, ground_truth_df, artifacts_df
        )

        # ====================================================
        # Generate Answers
        # ====================================================

        # 1️⃣ WITHOUT grounding
        answer_no_rag = generate_answer_eval(
            query=query_text,
            context=None
        )

        # 2️⃣ WITH grounding
        rag_context = build_context_for_artifact_id(correct_artifact_id)

        answer_with_rag = generate_answer_eval(
            query=query_text,
            context=rag_context
        )

        # ====================================================
        # Embeddings
        # ====================================================

        emb_no_rag = embed_with_cache(answer_no_rag)
        emb_with_rag = embed_with_cache(answer_with_rag)
        emb_gt = embed_with_cache(ground_truth_text)

        # ====================================================
        # Metrics
        # ====================================================

        # Semantic similarity = factual accuracy
        sim_no_rag = cosine_similarity(emb_no_rag, emb_gt)
        sim_with_rag = cosine_similarity(emb_with_rag, emb_gt)

        # Hallucination proxy = semantic drift
        halluc_no_rag = 1 - sim_no_rag
        halluc_with_rag = 1 - sim_with_rag

        # Grounding effect
        grounding_gain = sim_with_rag - sim_no_rag

        results.append({
            "query_id": query_id,
            "query": query_text,
            "correct_artifact_id": correct_artifact_id,

            "sim_no_rag": sim_no_rag,
            "sim_with_rag": sim_with_rag,

            "halluc_no_rag": halluc_no_rag,
            "halluc_with_rag": halluc_with_rag,

            "grounding_gain": grounding_gain,
            "grounding_improved": grounding_gain > 0
        })

    eval_df = pd.DataFrame(results)
    eval_df.to_csv(OUTPUT_PATH, index=False)
    return eval_df


# ============================================================
# Embedding Cache
# ============================================================

# Cache to avoid re-embedding the same text repeatedly
EMBEDDING_CACHE: Dict[str, np.ndarray] = {}


def embed_with_cache(text: str, max_retries: int = 5) -> np.ndarray:
    """
    Embed text with:
    - caching (Fix 1)
    - retry + exponential backoff (Fix 3)

    This protects evaluation from Vertex API instability.
    """

    # --- Return cached embedding if exists ---
    if text in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[text]

    # --- Retry loop ---
    for attempt in range(max_retries):
        try:
            embedding = embed_texts([text])[0]
            EMBEDDING_CACHE[text] = embedding
            return embedding

        except Exception as e:
            wait_time = 2 ** attempt
            print(
                f"⚠️ Embedding failed (attempt {attempt + 1}/{max_retries}). "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    # If all retries fail
    raise RuntimeError("❌ Embedding failed after multiple retries.")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    print("📊 Evaluating how grounding affects output accuracy...\n")

    df = evaluate_grounding_effect()

    improvement_rate = df["grounding_improved"].mean()

    print("✅ Evaluation complete")
    print(f"Queries evaluated: {len(df)}")
    print(f"Grounding improved accuracy for: {improvement_rate:.2%} of queries")
    print(f"Results saved to: {OUTPUT_PATH}")