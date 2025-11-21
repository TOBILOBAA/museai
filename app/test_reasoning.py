# app/test_reasoning.py

from pathlib import Path
import sys
from dotenv import load_dotenv

# --- Make sure the project root is on sys.path ---
ROOT = Path(__file__).resolve().parent.parent  # /.../museai
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env so Vertex / GCP works
load_dotenv(ROOT / ".env")

# NOW this import will work
from app.reasoning import museai_reason


def main():
    # -------- Case 1: artifact_id known (e.g., from Vision) --------
    print("\n=== Test 1: Known artifact_id (Torah Crown, id=3) ===\n")
    answer1 = museai_reason(
        user_query="Tell me about the religious and cultural role of this object.",
        artifact_id=3,
        language="en",
    )
    print(answer1)

    # -------- Case 2: No artifact_id, only free-form query --------
    print("\n=== Test 2: Query-based RAG (no artifact id) ===\n")
    answer2 = museai_reason(
        user_query="Which artifact in the museum collection relates to warfare?",
        artifact_id=None,
        language="en",
    )
    print(answer2)

    # -------- Case 3: Same thing but in French --------
    print("\n=== Test 3: French answer ===\n")
    answer3 = museai_reason(
        user_query="Parle-moi brièvement de cet objet.",
        artifact_id=1,
        language="fr",
    )
    print(answer3)


if __name__ == "__main__":
    main()