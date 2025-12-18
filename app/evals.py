from __future__ import annotations

import sys 
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent  
sys.path.append(str(ROOT_DIR))

from app.rag import retrieve_artifacts

import argparse
from pathlib import Path
import pandas as pd

def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)


def build_retrieval_log(
    queries_path: Path,
    output_path: Path,
    k: int = 3,
):
    queries_df = pd.read_csv(queries_path)
    rows = []

    for _, row in queries_df.iterrows():
        query_id = row["query_id"]
        query_text = row["query"]

        results = retrieve_artifacts(query_text, k=k)

        for rank, r in enumerate(results, start=1):
            rows.append({
                "query_id": query_id,
                "query": query_text,
                "rank": rank,
                "retrieved_artifact_id": r["artifact_id"],
                "score": r["score"],
            })

    log_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_df.to_csv(output_path, index=False)

    return log_df


def build_retrieval_evaluation(
    queries_path: Path,
    retrieval_log_path: Path,
    ground_truth_path: Path,
    k: int = 3,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Creates a human-readable evaluation table comparing:
    - queries
    - retrieved artifacts
    - ground truth
    """

    queries_df = load_csv(queries_path)
    retrieval_df = load_csv(retrieval_log_path)
    gt_df = load_csv(ground_truth_path)

    rows = []

    for _, q_row in queries_df.iterrows():
        query_id = q_row["query_id"]
        query_text = q_row["query"]

        # ground truth artifact
        gt_row = gt_df[gt_df["query_id"] == query_id]
        if gt_row.empty:
            continue
        correct_artifact = int(gt_row.iloc[0]["relevant_artifact_id"])

        # retrieved artifacts (ordered by rank)
        retrieved = (
            retrieval_df[retrieval_df["query_id"] == query_id]
            .sort_values("rank")
        )

        retrieved_ids = retrieved["retrieved_artifact_id"].tolist()

        # evaluation logic
        correct_found = correct_artifact in retrieved_ids

        if correct_found:
            position = retrieved_ids.index(correct_artifact) + 1
        else:
            position = None

        row = {
            "query_id": query_id,
            "query": query_text,
            "retrieved_artifacts": retrieved_ids,
            "correct_artifact": correct_artifact,
            "correct_found": "Yes" if correct_found else "No",
            "position_of_correct": position,
            "hit@1": int(position == 1),
            "hit@2": int(position is not None and position <= 2),
            "hit@3": int(position is not None and position <= 3),
            f"hit@{k}": int(position is not None and position <= k),
        }

        rows.append(row)

    eval_df = pd.DataFrame(rows)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        eval_df.to_csv(output_path, index=False)

    return eval_df


def summarize_retrieval_metrics(eval_df: pd.DataFrame, k: int = 3) -> dict:
    return {
        "Total Queries": len(eval_df),
        "Recall@1": eval_df["hit@1"].mean(),
        "Recall@2": eval_df["hit@2"].mean(),
        "Recall@3": eval_df["hit@3"].mean(),
        f"Recall@{k}": eval_df[f"hit@{k}"].mean(),
    }


def main():
    queries_path = Path("data/queries.csv")
    retrieval_log_path = Path("data/retrieval_log.csv")
    ground_truth_path = Path("data/ground_truth.csv")
    evaluation_path = Path("data/retrieval_evaluation.csv")

    print("🔎 Building retrieval log...")
    build_retrieval_log(
        queries_path=queries_path,
        output_path=retrieval_log_path,
        k=3,
    )

    print("📊 Evaluating retrieval...")
    eval_df = build_retrieval_evaluation(
        queries_path=queries_path,
        retrieval_log_path=retrieval_log_path,
        ground_truth_path=ground_truth_path,
        k=3,
        output_path=evaluation_path,
    )

    metrics = summarize_retrieval_metrics(eval_df, k=3)

    print("\n📈 Retrieval Evaluation Summary")
    for k, v in metrics.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")

    print(f"\n✅ Saved evaluation table to {evaluation_path}")


if __name__ == "__main__":
    main()
