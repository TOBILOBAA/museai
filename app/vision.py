from dotenv import load_dotenv
load_dotenv()

import os
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import mimetypes
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part
from google.api_core.exceptions import GoogleAPICallError, ServiceUnavailable

from PIL import Image
import io

# ====== Paths & Config ======
BASE_DIR = Path(__file__).resolve().parent.parent  # museai/
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_CSV = DATA_DIR / "artifacts.csv"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-2.0-flash-001")

def _load_service_account_credentials():
    """
    Load service account credentials from either:
    - Streamlit Cloud secrets["GCP_SERVICE_ACCOUNT_JSON"], or
    - env var GCP_SERVICE_ACCOUNT_JSON (as JSON string).

    Returns:
        google.oauth2.service_account.Credentials or None
    """
    sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")

    # Try Streamlit secrets if env var is not set
    if not sa_json:
        try:
            import streamlit as st  # type: ignore
            if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
                raw = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
                # Streamlit secrets can give str or dict
                if isinstance(raw, dict):
                    info = raw
                else:
                    info = json.loads(str(raw))
                return service_account.Credentials.from_service_account_info(info)
        except Exception:
            return None
    else:
        try:
            info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(info)
        except json.JSONDecodeError:
            raise RuntimeError("GCP_SERVICE_ACCOUNT_JSON is not valid JSON")

    return None


# ===== Helper: resize + normalize image for Gemini Vision =====

def prepare_image_bytes(path: Path, max_side: int = 1024) -> bytes:
    """
    Open the image, downscale it so the longest side <= max_side,
    and return JPEG bytes.

    This keeps payload small enough for cloud inference and avoids
    issues with giant phone camera images.
    """
    with Image.open(path) as img:
        img = img.convert("RGB")  # ensure 3-channel
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

def _load_sa_credentials():
    """
    Load service account credentials in this order:
    1) Streamlit Cloud secrets["GCP_SERVICE_ACCOUNT_JSON"]
    2) Env var GCP_SERVICE_ACCOUNT_JSON
    3) File pointed to by GOOGLE_APPLICATION_CREDENTIALS

    If nothing works, raise so we don't silently fall back to metadata server.
    """
    info = None

    # 1) Streamlit secrets (Streamlit Cloud)
    try:
        import streamlit as st
        sa_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            # secrets can be parsed as dict or string
            if isinstance(sa_json, dict):
                info = sa_json
            else:
                info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(info)
    except Exception as e:
        print("[_load_sa_credentials] failed reading st.secrets:", e)

    # 2) Environment variable (local dev or other hosts)
    sa_env = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if sa_env:
        try:
            info = json.loads(sa_env)
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            print("[_load_sa_credentials] failed parsing GCP_SERVICE_ACCOUNT_JSON env:", e)

    # 3) Local JSON file (GOOGLE_APPLICATION_CREDENTIALS)
    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and Path(sa_path).exists():
        try:
            return service_account.Credentials.from_service_account_file(sa_path)
        except Exception as e:
            print("[_load_sa_credentials] failed loading GOOGLE_APPLICATION_CREDENTIALS file:", e)

    # If we get here, we really have no usable credentials
    raise RuntimeError(
        "No service account JSON found. "
        "Set GCP_SERVICE_ACCOUNT_JSON (Streamlit secret or env) or GOOGLE_APPLICATION_CREDENTIALS."
    )


def init_vertex():
    """
    Initialize Vertex AI client with project + location, ALWAYS using explicit
    service account credentials (no metadata server fallback).
    """
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment (.env or secrets).")

    creds = _load_sa_credentials()
    vertexai.init(
        project=GCP_PROJECT_ID,
        location=GCP_LOCATION,
        credentials=creds,
    )


def get_vision_model() -> GenerativeModel:
    """
    Return a Gemini Vision-capable model instance.
    """
    init_vertex()
    return GenerativeModel(VISION_MODEL_NAME)


# ====== Load artifact metadata ======

def load_artifacts() -> pd.DataFrame:
    """
    Load the artifacts table you created in artifacts.csv.
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
    - artifact_id
    - title
    - confidence
    - reason
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
        # This is what you just saw in Streamlit Cloud
        # You can log this in Streamlit as well later if needed.
        raise RuntimeError(
            "Gemini Vision service is temporarily unavailable. "
            "Please wait a moment and try capturing the artifact again."
        ) from e
    except GoogleAPICallError as e:
        # Catch other API-level issues, so your app doesn't just crash.
        raise RuntimeError(
            f"Error calling Gemini Vision API: {e}"
        ) from e

    # response.text should be a JSON string according to our instructions
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_image = Path(sys.argv[1])
    else:
        test_image = DATA_DIR / "images" / "lamp_ancient.jpg"

    print(f"Testing classification with image: {test_image}")
    out = classify_artifact_from_image(test_image)
    print(json.dumps(out, indent=2, ensure_ascii=False))