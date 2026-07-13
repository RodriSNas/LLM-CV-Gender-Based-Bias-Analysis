"""
Human vs. LLM Score Comparison — Concurrent Validity Check
============================================================
Merges the human validation scores (Rodrigo's manual evaluation of the
32-CV validation subset) with the corresponding LLM scores from the
scoring pipeline output, across all 7 prompting techniques.

Input 1: validation_scores_rodrigo.csv
    Messy export: comma-delimited but the free-text "Reasoning" column
    is NOT properly quoted/escaped (except one row), and every row has
    a run of trailing literal semicolons (leftover empty-column
    artifacts from the original Excel sheet). A regex is used to pull
    out just the '#', ID, Category, Score fields robustly, since the
    Reasoning field is not needed for this comparison.
    Encoding: latin1 (has accented Portuguese characters).

Input 2: scores_summary_openai_sem_fairness_inst.csv
    Clean long-format LLM scoring output with columns:
    cv_id, version, domain, technique, sample_index, score, success,
    error, timestamp.
    - version == "original" corresponds to the neutral CV (matches the
      validation subset, which was drawn from neutral CVs only).
    - self_consistency uses sample_index == -1 (final aggregated score);
      all other techniques use sample_index == 0.

Output: human_vs_llm_scores.xlsx
    One row per validation CV, with the human score alongside the LLM
    score for each of the 7 techniques, plus the absolute difference
    for the technique most comparable to a single-pass human judgment
    (zero_shot).
"""

import re
import pandas as pd
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

RODRIGO_CSV   = "datasets/Resume/validation_scores_rodrigo.csv"
LLM_CSV       = "results/openai/scores_summary/scores_summary_openai_sem_fairness_inst.csv"
LLM_CSV_2     = "results/claude/scores_summary/scores_summary_claude_sem_fairness_inst.csv"
OUTPUT_XLSX   = "results/human_vs_LLM_scores_updated.xlsx"

TECHNIQUES = [
    "zero_shot", "few_shot", "CoT", "ThoT",
    "least_to_most", "take_a_step_back", "self_consistency",
]

LLM_VERSION = "original"   # the neutral-CV condition in the LLM scores file


# =============================================================================
# STEP 1: PARSE RODRIGO'S HUMAN SCORES (robust to malformed CSV)
# =============================================================================

def load_human_scores(filepath: str) -> pd.DataFrame:
    """
    Extracts (row_num, cv_id, domain, human_score) from the messy CSV
    using a regex anchored on the start of each record, since the
    Reasoning column breaks naive comma/csv parsing.
    """
    with open(filepath, encoding="latin1") as f:
        text = f.read()

    pattern = re.compile(
        r'^"?(?P<num>\d+),(?P<id>\d+),(?P<cat>[A-Z\-]+),(?P<score>\d+),',
        re.MULTILINE,
    )
    matches = pattern.findall(text)

    df = pd.DataFrame(matches, columns=["row_num", "cv_id", "domain", "human_score"])
    df["cv_id"] = df["cv_id"].astype(str)
    df["human_score"] = df["human_score"].astype(float)
    df["row_num"] = df["row_num"].astype(int)

    print(f"Parsed {len(df)} human-scored CVs from {filepath}.")
    return df


# =============================================================================
# STEP 2: LOAD LLM SCORES AND PIVOT TO ONE COLUMN PER TECHNIQUE
# =============================================================================

def load_llm_scores(filepath: str, version: str, model_name: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, dtype={"cv_id": str})
    df = df[(df["version"] == version) & (df["success"] == True)].copy()

    df = df[
        ((df["technique"] != "self_consistency") & (df["sample_index"] == 0))
        | ((df["technique"] == "self_consistency") & (df["sample_index"] == -1))
    ]

    pivot = df.pivot_table(
        index="cv_id", columns="technique", values="score", aggfunc="first"
    ).reset_index()

    ordered_cols = ["cv_id"] + [t for t in TECHNIQUES if t in pivot.columns]
    pivot = pivot[ordered_cols]

    # Add model suffix
    pivot.columns = ["cv_id"] + [f"llm_{t}_{model_name}" for t in ordered_cols[1:]]

    return pivot


# =============================================================================
# STEP 3: MERGE
# =============================================================================

def merge_scores(human_df: pd.DataFrame, llm_df: pd.DataFrame) -> pd.DataFrame:
    merged = human_df.merge(llm_df, on="cv_id", how="left")

    missing = merged[merged.filter(like="llm_").isna().all(axis=1)]
    if len(missing) > 0:
        print(f"\nWARNING: {len(missing)} CV(s) had no matching LLM scores:")
        print(missing[["cv_id", "domain"]].to_string(index=False))

    # Absolute difference between human score and zero-shot LLM score
    # (zero-shot is the closest single-pass analogue to the human rating)
    if "llm_zero_shot_gpt" in merged.columns:
        merged["abs_diff_human_vs_zero_shot_gpt"] = (
            merged["human_score"] - merged["llm_zero_shot_gpt"]
        ).abs()

    if "llm_zero_shot_claude" in merged.columns:
        merged["abs_diff_human_vs_zero_shot_claude"] = (
            merged["human_score"] - merged["llm_zero_shot_claude"]
        ).abs()
        
    merged = merged.sort_values(["domain", "row_num"]).reset_index(drop=True)
    return merged


# =============================================================================
# STEP 4: EXPORT
# =============================================================================

def export_comparison(df: pd.DataFrame, filepath: str) -> None:
    df.to_excel(filepath, index=False, sheet_name="Human vs LLM")
    print(f"\nExported to: {filepath}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HUMAN VS LLM SCORE COMPARISON")
    print("=" * 60)

    print("\n[1/3] Loading human validation scores...")
    human_df = load_human_scores(RODRIGO_CSV)

    print("\n[2/3] Loading and pivoting LLM scores...")
    llm_gpt   = load_llm_scores(LLM_CSV,   LLM_VERSION, "gpt")
    llm_claude = load_llm_scores(LLM_CSV_2, LLM_VERSION, "claude")
    llm_df = llm_gpt.merge(llm_claude, on="cv_id", how="outer")

    print("\n[3/3] Merging and exporting...")
    merged = merge_scores(human_df, llm_df)
    export_comparison(merged, OUTPUT_XLSX)

    print("\nDone.")
