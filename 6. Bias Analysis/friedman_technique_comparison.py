import itertools
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

CSV_PATH = "C:/Users/rodri/Desktop/Mestrado/Tese/Method/results/openai/scores_summary/scores_summary_openai_sem_fairness_inst.csv"  # <-- edit per run
MODEL_LABEL = "GPT-5.2"  # <-- edit per run (just used for printed labels)
OUTPUT_XLSX = "results/openai/friedman_results_openai.xlsx"  # <-- edit per run (e.g. "..._claude.xlsx")

TECHNIQUES = ["zero_shot", "few_shot", "CoT", "ThoT",
              "self_consistency", "least_to_most", "take_a_step_back"]
ALPHA = 0.05

def load_rank_gaps(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["success"] == True]
    df = df[df["version"].isin(["male", "female", "original"])]

    pivot = df.pivot_table(
        index=["cv_id", "technique"],
        columns="version",
        values="score",
        aggfunc="mean",
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(columns={
        "original": "score_neutral",
        "male": "score_male",
        "female": "score_female",
    })
    pivot = pivot.dropna(subset=["score_male", "score_female", "score_neutral"])

    def ras(row):
        s = pd.Series({"male": row.score_male, "female": row.score_female,
                        "neutral": row.score_neutral})
        r = s.rank(ascending=False, method="average")
        return pd.Series({"rank_male": r["male"], "rank_female": r["female"],
                           "rank_neutral": r["neutral"]})

    pivot = pd.concat([pivot, pivot.apply(ras, axis=1)], axis=1)
    pivot["rank_gap"] = pivot["rank_male"] - pivot["rank_female"]

    return pivot


def run_friedman(pivot: pd.DataFrame, techniques: list, model_label: str):
    wide = pivot.pivot(index="cv_id", columns="technique", values="rank_gap")[techniques]

    stat, p = friedmanchisquare(*[wide[t] for t in techniques])
    print(f"\n=== {model_label}: Friedman test (omnibus) ===")
    print(f"chi-square = {stat:.4f}, df = {len(techniques) - 1}, p = {p:.6g}")
    significant = p < ALPHA
    print(f"Result: {'SIGNIFICANT' if significant else 'not significant'} at alpha = {ALPHA}")
    return wide, significant


def run_posthoc(wide: pd.DataFrame, techniques: list, model_label: str) -> pd.DataFrame:
    n_pairs = len(list(itertools.combinations(techniques, 2)))
    alpha_bonf = round(ALPHA / n_pairs, 5)

    print(f"\n=== {model_label}: Pairwise Wilcoxon signed-rank (post-hoc) ===")
    print(f"Bonferroni-corrected alpha = {alpha_bonf} ({n_pairs} comparisons)\n")

    rows = []
    for t1, t2 in itertools.combinations(techniques, 2):
        w, pv = wilcoxon(wide[t1], wide[t2])
        rows.append({
            "technique_1": t1,
            "technique_2": t2,
            "W_statistic": w,
            "p_value": round(pv, 6),
            "significant_bonferroni": pv < alpha_bonf,
        })

    results_df = pd.DataFrame(rows).sort_values("p_value").reset_index(drop=True)
    pd.set_option("display.width", 120)
    print(results_df.to_string(index=False))

    n_sig = results_df["significant_bonferroni"].sum()
    print(f"\n{n_sig} of {n_pairs} technique pairs differ significantly "
          f"after Bonferroni correction.")
    return results_df


def save_to_excel(output_path: str, model_label: str, sanity_check: pd.Series,
                   friedman_stat: float, friedman_p: float, friedman_significant: bool,
                   posthoc_df: pd.DataFrame | None):
    """Writes a 3-sheet Excel file: mean rank gaps, Friedman result, post-hoc pairs."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        sanity_check.rename("mean_rank_gap").round(4).to_frame().to_excel(
            writer, sheet_name="Mean Rank Gap by Technique")

        friedman_df = pd.DataFrame([{
            "model": model_label,
            "chi_square": round(friedman_stat, 4),
            "df": len(TECHNIQUES) - 1,
            "p_value": friedman_p,
            "significant": friedman_significant,
            "alpha": ALPHA,
        }])
        friedman_df.to_excel(writer, sheet_name="Friedman Test", index=False)

        if posthoc_df is not None:
            posthoc_df.to_excel(writer, sheet_name="Post-hoc Wilcoxon", index=False)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    pivot = load_rank_gaps(CSV_PATH)


    sanity_check = pivot.groupby("technique")["rank_gap"].mean()
    print(f"Mean rank gap per technique ({MODEL_LABEL}) -- sanity check vs. thesis Section 5.2:")
    print(sanity_check.round(4))

    wide, is_significant = run_friedman(pivot, TECHNIQUES, MODEL_LABEL)
    friedman_stat, friedman_p = friedmanchisquare(*[wide[t] for t in TECHNIQUES])

    posthoc_df = None
    if is_significant:
        posthoc_df = run_posthoc(wide, TECHNIQUES, MODEL_LABEL)
    else:
        print(f"\nOmnibus test not significant for {MODEL_LABEL} -- "
              f"no valid basis for post-hoc pairwise comparisons (would "
              f"inflate Type I error). Report the Friedman result as-is: "
              f"no evidence that technique choice affects rank gap for "
              f"this model under this condition.")

    save_to_excel(OUTPUT_XLSX, MODEL_LABEL, sanity_check,
                  friedman_stat, friedman_p, is_significant, posthoc_df)
