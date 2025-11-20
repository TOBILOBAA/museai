from dotenv import load_dotenv
load_dotenv()

import os
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import mimetypes
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# ====== Paths & Config ======
BASE_DIR = Path(__file__).resolve().parent.parent  # museai/
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_CSV = DATA_DIR / "artifacts.csv"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-2.0-flash-001")

# ===== Helper: normalize image input for Gemini Vision =====

def make_image_part(image):
    """
    Accepts:
      - Streamlit uploaded/camera input (has .getvalue())
      - OR a local file path (Path or str)

    Returns:
      - A Gemini Part object ready for the Vision model
    """


    # -------- CASE 1: Streamlit upload (BytesIO-like object) --------
    if hasattr(image, "getvalue"):
        return Part.from_data(
            data=image.getvalue(),
            mime_type="image/jpeg"  # Good default; can refine later
        )

    # -------- CASE 2: Local file path --------
    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")

    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        mime = "image/jpeg"

    return Part.from_data(
        data=path.read_bytes(),
        mime_type=mime
    )



# ====== Vertex init / model loader ======

def init_vertex():
    """
    Initialize Vertex AI client with project + location.

    We call this once before using any Gemini model.
    """
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment (.env).")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)


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

    Columns we expect:
    - artifact_id
    - title
    - short_label
    - location
    - image_filename
    - period
    - material
    - base_context
    """
    if not ARTIFACTS_CSV.exists():
        raise FileNotFoundError(f"Artifacts CSV not found: {ARTIFACTS_CSV}")
    df = pd.read_csv(ARTIFACTS_CSV)
    df = df.reset_index(drop=True)
    return df


def build_artifact_prompt(df: pd.DataFrame) -> str:
    """
    Build a text description of all known artifacts for Gemini.

    We tell the model:
    - Here is the list of possible artifacts (with id, title, description).
    - Look at the uploaded image and choose the *closest* match.
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

def classify_artifact_from_image(image) -> Dict[str, Any]:
    """
    Given an image (either:
      - Streamlit uploaded/camera object (has .getvalue()), OR
      - Local file path (str or Path)
    ask Gemini Vision to decide which known artifact it is most likely showing.

    Returns a dict with:
    - artifact_id
    - title
    - confidence
    - reason
    """
    # Only check the filesystem if this looks like a path (no .getvalue)
    if not hasattr(image, "getvalue"):
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

    df = load_artifacts()
    prompt = build_artifact_prompt(df)

    model = get_vision_model()

    # Build the input for Gemini: text prompt + image
    img_part = make_image_part(image)

    response = model.generate_content(
        [prompt, img_part],
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )

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


# ====== Quick manual test ======
if __name__ == "__main__":
    """
    Run this from project root:

        (venv) python app/vision.py

    or:

        (venv) python app/vision.py /path/to/test_image.jpg

    For now we just hard-code a test path inside data/images.
    """
    import sys

    if len(sys.argv) > 1:
        test_image = Path(sys.argv[1])
    else:
        # Adjust this to whatever image you add later
        test_image = DATA_DIR / "images" / "lamp_ancient.jpg"

    print(f"Testing classification with image: {test_image}")
    result = classify_artifact_from_image(test_image)
    print("\nGemini classification result:\n")
    print(json.dumps(result, indent=2))