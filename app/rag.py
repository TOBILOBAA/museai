import os
import json
import faiss
import numpy as np
import pandas as pd
import vertexai

from pathlib import Path
from typing import List, Dict
from google.oauth2 import service_account
from vertexai.language_models import TextEmbeddingModel
from dotenv import load_dotenv
load_dotenv()

try:
    import streamlit as st   # available on Streamlit Cloud
except Exception:
    st = None               # harmless fallback for local CLI tests



# ====== Config ======
BASE_DIR = Path(__file__).resolve().parent.parent   # MuseAI/

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
ARTIFACTS_CSV = DATA_DIR / "artifacts.csv"
VECTOR_INDEX_PATH = DATA_DIR / "artifacts_index.faiss"
METADATA_PARQUET_PATH = DATA_DIR / "artifacts_metadata.parquet"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
EMBEDDING_MODEL_NAME = "text-embedding-004"   # Vertex AI Text Embedding Model


# ====== Vertex / Embeddings helpers ======
def _get_gcp_config() -> tuple[str, str]:
    """
    Get project + location from environment variables only.

    This is used for the local CLI tool (rag.py) to build the FAISS index,
    and by the app in production. It does NOT rely on st.secrets.
    """
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION") or "us-central1"

    if not project:
        raise RuntimeError(
            "GCP_PROJECT_ID is not set in environment variables. "
            "Make sure your .env has GCP_PROJECT_ID and you've loaded it."
        )

    return project, location


def _load_sa_credentials():
    """
    Load Google Cloud service-account credentials from either:
    - GOOGLE_APPLICATION_CREDENTIALS file (local dev), OR
    - GCP_SERVICE_ACCOUNT_JSON in env.

    No use of st.secrets here so it works fine in plain python.
    Streamlit Cloud will also expose secrets as env vars, so this works there too.
    """
    # Local JSON file (for laptop dev)
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if path and Path(path).exists():
        return service_account.Credentials.from_service_account_file(path)

    # Environment variable (for all hosts, including Streamlit Cloud)
    sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if sa_json:
        info = json.loads(sa_json)
        return service_account.Credentials.from_service_account_info(info)

    raise RuntimeError(
        "No service account JSON found. "
        "Set GCP_SERVICE_ACCOUNT_JSON (env) or GOOGLE_APPLICATION_CREDENTIALS."
    )


def init_vertex():
    """
    Initialize Vertex AI for embeddings using explicit SA creds.
    Works both locally and on Streamlit Cloud.
    """
    project, location = _get_gcp_config()
    creds = _load_sa_credentials()

    vertexai.init(
        project=project,
        location=location,
        credentials=creds,
    )


def get_embedding_model() -> TextEmbeddingModel:
    init_vertex()
    return TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Return embeddings as a 2D float32 numpy array."""
    model = get_embedding_model()
    embeddings = model.get_embeddings(texts)
    vectors = np.array([e.values for e in embeddings], dtype="float32")
    return vectors


# ====== Index building ======
def load_artifact_metadata(path: Path = ARTIFACTS_CSV) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    df = pd.read_csv(path)
    # Ensures a simple integer index
    df = df.reset_index(drop=True)
    return df


def build_and_save_vectorstore():
    """Create FAISS index from artifacts.csv and save index + metadata."""
    df = load_artifact_metadata()

    # Text we embed = title + short label + base_context
    texts = (
        df["title"].fillna("") + " - " +
        df["short_label"].fillna("") + " | " +
        df["base_context"].fillna("")
    ).tolist()

    print(f"Embedding {len(texts)} artifacts…")
    vectors = embed_texts(texts)

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    # Save FAISS index
    faiss.write_index(index, str(VECTOR_INDEX_PATH))
    print(f"Saved FAISS index to {VECTOR_INDEX_PATH}")

    # Save metadata (parquet keeps schema nicely)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(METADATA_PARQUET_PATH, index=False)
    print(f"Saved metadata to {METADATA_PARQUET_PATH}")


# ====== Index loading & retrieval ======
def load_vectorstore():
    if not VECTOR_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Vector index not found at {VECTOR_INDEX_PATH}. "
            "Run build_and_save_vectorstore() first."
        )
    if not METADATA_PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Metadata parquet not found at {METADATA_PARQUET_PATH}. "
            "Run build_and_save_vectorstore() first."
        )

    index = faiss.read_index(str(VECTOR_INDEX_PATH))
    df = pd.read_parquet(METADATA_PARQUET_PATH)
    return index, df


def retrieve_artifacts(query: str, k: int = 3) -> List[Dict]:
    """Return top-k artifacts as list of dicts with a distance score."""
    index, df = load_vectorstore()
    query_vec = embed_texts([query])
    distances, indices = index.search(query_vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        row = df.iloc[int(idx)].to_dict()
        row["score"] = float(dist)
        results.append(row)

    return results


def build_context_for_query(query: str, k: int = 3) -> str:
    """
    Return a text block you will pass into the LLM as RAG context.
    """
    results = retrieve_artifacts(query, k=k)

    if not results:
        return "No matching artifacts found in the museum knowledge base."

    chunks = []
    for r in results:
        chunk = (
            f"Artifact: {r['title']} "
            f"(ID: {r['artifact_id']}, Period: {r.get('period', 'Unknown')})\n"
            f"Location: {r.get('location', 'Unknown')}\n"
            f"Material: {r.get('material', 'Unknown')}\n"
            f"Description: {r['base_context']}\n"
        )
        chunks.append(chunk)

    return "\n---\n".join(chunks)


def build_context_for_artifact_id(artifact_id: int) -> str:
    """Return RAG context specifically for a known artifact."""
    _, df = load_vectorstore()  # loads FAISS + metadata

    row = df[df["artifact_id"] == artifact_id]
    if row.empty:
        return "No RAG context found for this artifact."

    r = row.iloc[0]

    return (
        f"Artifact: {r['title']} (ID: {r['artifact_id']})\n"
        f"Period: {r.get('period', 'Unknown')}\n"
        f"Location: {r.get('location', 'Unknown')}\n"
        f"Material: {r.get('material', 'Unknown')}\n"
        f"Description: {r['base_context']}\n"
    )



# ================================================================
# Manual Test (RAG Pipeline)
# ---------------------------------------------------------------
# This block allows me to test the RAG pipeline independently
# from the rest of the MuseAI application.
#
# WHY THIS TEST EXISTS:
# - I follow a "code → test → code → test" workflow.
# - After implementing the RAG pipeline (FAISS + embeddings),
#   I needed a simple way to verify that:
#       1. The artifacts.csv file loads correctly
#       2. Embeddings are generated successfully
#       3. The FAISS index builds without errors
#       4. Retrieval returns the top-k matching artifacts
#       5. The RAG context format looks correct before connecting reasoning.py
#
# WHAT THIS TEST DOES:
# - Rebuilds the vector index from artifacts.csv
# - Saves FAISS + metadata parquet
# - Performs a sample retrieval using a simple query string
# - Prints out the final RAG context block that will later be
#   injected into the reasoning LLM during the full pipeline.
#
# WHEN I USE THIS:
# - Every time I update artifacts.csv
# - Every time I refine how context is constructed
# - Before integrating this RAG output with reasoning.py
#
# HOW TO RUN:
#   python app/rag.py
# ================================================================
if __name__ == "__main__":
    print("Building vector store from artifacts.csv …")
    build_and_save_vectorstore()
    print("\nTesting retrieval…")
    test_query = "religious silver object used with the Torah"
    ctx = build_context_for_query(test_query, k=2)
    print("\nContext for test query:\n")
    print(ctx)