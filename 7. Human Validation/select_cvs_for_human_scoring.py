import pandas as pd

INPUT_XLSX   = "selected_cvs_updated_expanded_v5.xlsx"
INPUT_SHEET  = "Neutral CVs"
OUTPUT_XLSX  = "validation_cvs_selected.xlsx"

ID_COL       = "ID"
CATEGORY_COL = "Category"
QUARTILE_COL = "Quartile"
LENGTH_COL   = "Text Length"
TEXT_COL     = "Resume Text"

CVS_PER_QUARTILE = 1
RANDOM_SEED      = 43


def load_neutral_cvs(filepath: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name=sheet, dtype={ID_COL: str})
    df = df.dropna(subset=[TEXT_COL, CATEGORY_COL, QUARTILE_COL]).reset_index(drop=True)
    print(f"Loaded {len(df)} neutral CVs across {df[CATEGORY_COL].nunique()} domains.")
    return df


def sample_validation_cvs(df: pd.DataFrame, cvs_per_quartile: int, seed: int) -> pd.DataFrame:
    selected_rows = []

    for domain, domain_df in df.groupby(CATEGORY_COL):
        domain_count = 0
        for q in sorted(domain_df[QUARTILE_COL].unique()):
            group = domain_df[domain_df[QUARTILE_COL] == q]
            if group.empty:
                print(f"  WARNING: {domain} {q} is empty - skipping.")
                continue
            n = min(cvs_per_quartile, len(group))
            if len(group) < cvs_per_quartile:
                print(f"  WARNING: {domain} {q} has only {len(group)} CV(s) - sampling all.")
            sampled = group.sample(n=n, random_state=seed)
            selected_rows.append(sampled)
            domain_count += n
        print(f"  {domain}: selected {domain_count} CVs")

    result = pd.concat(selected_rows, ignore_index=True) if selected_rows else df.iloc[0:0]
    print(f"\nTotal CVs selected for validation: {len(result)}")
    return result


def export_validation_set(df: pd.DataFrame, filepath: str) -> None:
    cols = [c for c in [ID_COL, CATEGORY_COL, QUARTILE_COL, LENGTH_COL, TEXT_COL] if c in df.columns]
    out = df[cols].sort_values([CATEGORY_COL, QUARTILE_COL]).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    out["human_score_rater1"] = ""
    out["human_score_rater2"] = ""
    out["notes"] = ""
    out.to_excel(filepath, index=False, sheet_name="Validation CVs")
    print(f"\nExported to: {filepath}")


if __name__ == "__main__":
    print("=" * 60)
    print("VALIDATION CV SELECTION")
    print("=" * 60)

    print("\n[1/3] Loading neutral CVs...")
    df = load_neutral_cvs(INPUT_XLSX, INPUT_SHEET)

    print("\n[2/3] Sampling 1 CV per quartile per domain...")
    selected = sample_validation_cvs(df, CVS_PER_QUARTILE, RANDOM_SEED)

    print("\n[3/3] Exporting...")
    export_validation_set(selected, OUTPUT_XLSX)

    print("\nDone.")
