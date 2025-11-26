import io
import os
import sys
import json
import pandas as pd
import vertexai

from PIL import Image
from pathlib import Path
from typing import Dict, Any, List
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part
from google.api_core.exceptions import GoogleAPICallError, ServiceUnavailable
from dotenv import load_dotenv
load_dotenv()

try:
    import streamlit as st   # available on Streamlit Cloud
except Exception:
    st = None               # harmless fallback for local CLI tests



# ====== Paths & Config ======
BASE_DIR = Path(__file__).resolve().parent.parent  # museai/
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_CSV = DATA_DIR / "artifacts.csv"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-2.0-flash-001") 

# ===== Helper: resize + normalize image for Gemini Vision =====
def prepare_image_bytes(path: Path, max_side: int = 1024) -> bytes:
    """
    Open the image, downscale it so the longest side <= max_side,
    and return JPEG bytes.

    This keeps payload small enough for cloud inference and avoids
    issues with giant phone camera images.
    """
    with Image.open(path) as img:
        img = img.convert("RGB")  
        w, h = img.size
        long_side = max(w, h)

        if long_side > max_side:
            scale = max_side / float(long_side)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()


def make_image_part(image: Path | str):
    """
    For this app we only expect:
      - A local file path (Path or str) saved from Streamlit camera_input.

    We:
      1. Downscale the photo (see prepare_image_bytes)
      2. Wrap it as a Gemini Part with the correct mime_type.
    """
    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")

    img_bytes = prepare_image_bytes(path)
    return Part.from_data(
        data=img_bytes,
        mime_type="image/jpeg",
    )


# ====== Vertex init / model loader ======
def _get_gcp_config() -> tuple[str, str]:
    """
    Get project + location from env OR Streamlit secrets.
    """
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION") or "us-central1"

    if st is not None:
        if not project and "GCP_PROJECT_ID" in st.secrets:
            project = st.secrets["GCP_PROJECT_ID"]
        if "GCP_LOCATION" in st.secrets:
            location = st.secrets["GCP_LOCATION"]

    if not project:
        raise RuntimeError(
            "GCP_PROJECT_ID is not set in environment variables or Streamlit secrets."
        )
    return project, location

def _load_sa_credentials():
    """
    Load Google Cloud service-account credentials from either:
    - GOOGLE_APPLICATION_CREDENTIALS file (local dev), OR
    - GCP_SERVICE_ACCOUNT_JSON in Streamlit secrets.

    Raises RuntimeError with a clear message if JSON is invalid.
    """
    # Local JSON file (for your laptop dev)
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if path and Path(path).exists():
        return service_account.Credentials.from_service_account_file(path)

    # Streamlit Cloud: value in st.secrets
    if st is not None and "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
        raw = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

        if isinstance(raw, dict):
            info = raw
        else:
            try:
                info = json.loads(raw)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    "GCP_SERVICE_ACCOUNT_JSON in Streamlit secrets is not valid JSON. "
                    "Inside the triple quotes it must be a plain JSON object "
                    "starting with '{' and ending with '}'."
                ) from e

        return service_account.Credentials.from_service_account_info(info)

    # Environment variable (for other hosts)
    sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            info = json.loads(sa_json)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "GCP_SERVICE_ACCOUNT_JSON env var is not valid JSON."
            ) from e
        return service_account.Credentials.from_service_account_info(info)

    # If nothing worked:
    raise RuntimeError(
        "No service account JSON found. "
        "Set GCP_SERVICE_ACCOUNT_JSON (Streamlit secret or env) or GOOGLE_APPLICATION_CREDENTIALS."
    )

def init_vertex():
    """
    Initialize Vertex AI client with project + location + credentials.
    Works both locally and on Streamlit Cloud.
    """
    project, location = _get_gcp_config()
    creds = _load_sa_credentials()

    if creds is not None:
        vertexai.init(project=project, location=location, credentials=creds)
    else:
        # fallback – local dev with ADC: Application Default Credientials
        vertexai.init(project=project, location=location)


def get_vision_model() -> GenerativeModel:
    """
    Return a Gemini Vision-capable model instance.
    """
    init_vertex()
    return GenerativeModel(VISION_MODEL_NAME)


# ====== Load artifact metadata ======
def load_artifacts() -> pd.DataFrame:
    """
    Load the artifacts table created in artifacts.csv.
    """
    if not ARTIFACTS_CSV.exists():
        raise FileNotFoundError(f"Artifacts CSV not found: {ARTIFACTS_CSV}")
    df = pd.read_csv(ARTIFACTS_CSV)
    df = df.reset_index(drop=True)
    return df


def build_artifact_prompt(df: pd.DataFrame) -> str:
    """
    Build a text description of all known artifacts for Gemini.
    """
    lines: List[str] = []
    lines.append(
        "You are a museum companion. I will give you a photo taken inside the "
        "museum and a list of known artifacts. Your job is to decide which "
        "artifact in the list best matches the photo."
    )
    lines.append("")
    lines.append("Here is the list of known artifacts:")

    for _, row in df.iterrows():
        lines.append(
            f"- ID {row['artifact_id']}: {row['title']} "
            f"({row.get('short_label', '')}) | "
            f"Location: {row.get('location', 'Unknown')} | "
            f"Period: {row.get('period', 'Unknown')} | "
            f"Material: {row.get('material', 'Unknown')} | "
            f"Description: {row.get('base_context', '')}"
        )

    lines.append("")
    lines.append(
        "Compare the uploaded image to these artifacts and choose the single "
        "best match. If none of them fit at all, you can return artifact_id = null."
    )
    lines.append(
        "Respond ONLY in **valid JSON** with this exact schema:\n"
        "{\n"
        '  "artifact_id": <int or null>,\n'
        '  "title": "<string or null>",\n'
        '  "confidence": "<high | medium | low>",\n'
        '  "reason": "<short explanation of why you chose this>"\n'
        "}"
    )

    return "\n".join(lines)


# ====== Main classification function ======
def classify_artifact_from_image(image_path: Path | str) -> Dict[str, Any]:
    """
    Given an image path (photo taken in museum), ask Gemini Vision to decide
    which known artifact it is most likely showing.

    Returns a dict with:
    - artifact_id (int or None)
    - title (str or None)
    - confidence ("high" | "medium" | "low")
    - reason (short explanation, or why no match was found)
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    df = load_artifacts()
    prompt = build_artifact_prompt(df)

    model = get_vision_model()
    img_part = make_image_part(image_path)

    try:
        response = model.generate_content(
            [prompt, img_part],
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )
    except ServiceUnavailable as e:
        raise RuntimeError(
            "Gemini Vision service is temporarily unavailable. "
            "Please wait a moment and try capturing the artifact again."
        ) from e
    except GoogleAPICallError as e:
        raise RuntimeError(
            f"Error calling Gemini Vision API: {e}"
        ) from e

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "artifact_id": None,
            "title": None,
            "confidence": "low",
            "reason": f"Model did not return valid JSON. Raw output: {response.text}",
        }

    for key in ["artifact_id", "title", "confidence", "reason"]:
        result.setdefault(key, None)

    return result

# ========================================================================
# OPTIONAL: Command-line test helper for developers
# ------------------------------------------------------------------------
# This block lets you test the artifact classification pipeline
# *without* running the Streamlit UI.
#
# Usage (from the project root, for example):
#     python app/vision.py path/to/your_image.jpg
#
# Requirements (developer must provide these):
#   1. An image file on disk (e.g. a museum artifact photo).
#   2. A CSV file at: data/artifacts.csv
#      - This is your own artifact "database" with columns like:
#            artifact_id, title, short_label, location, period,
#            material, base_context
#   3. Google Cloud / Vertex AI config:
#        - GCP_PROJECT_ID
#        - GCP_LOCATION   (optional, defaults to us-central1)
#        - AND EITHER:
#             - GOOGLE_APPLICATION_CREDENTIALS (path to SA JSON), OR
#             - GCP_SERVICE_ACCOUNT_JSON (full JSON in env or Streamlit secrets)
#
# What this does:
#   - Loads your artifacts from data/artifacts.csv
#   - Sends the provided image to Gemini Vision
#   - Prints the JSON classification result to the terminal
#
# This is ONLY for debugging / development:
# The Streamlit app calls classify_artifact_from_image(...) internally.
# ========================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_image = Path(sys.argv[1])
    else:
        test_image = DATA_DIR / "images" / "lamp_ancient.jpg"

    print(f"Testing classification with image: {test_image}")
    out = classify_artifact_from_image(test_image)
    print(json.dumps(out, indent=2, ensure_ascii=False))