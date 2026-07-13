from pathlib import Path
import pandas as pd

INPUT_PATH = r"C:\Users\rodri\Desktop\Mestrado\Tese\Method\datasets\Resume\selected_cvs_updated_expanded_v5_with_pronouns.xlsx"

GENDER_COL = "Gender Condition"
NAME_COL = "Injected Name"
TEXT_COL = "Resume Text"

GENDER_FIELD_BY_GENDER = {
    "male":   "Gender: Male",
    "female": "Gender: Female",
}

 
 
def insert_gender_field(text: str, gender_field: str) -> str:
    lines = text.split("\n", 2)  # separa só as primeiras 2 quebras de linha
    name_line, contact_line, rest = lines[0], lines[1], lines[2]
    return f"{name_line}\n{contact_line}\n{gender_field}\n{rest}"


def validate_linkedin_anchor(df: pd.DataFrame) -> pd.DataFrame:
    mask_gendered = df[GENDER_COL].isin(GENDER_FIELD_BY_GENDER.keys())
    mismatches = []
    for idx, row in df[mask_gendered].iterrows():
        text = row[TEXT_COL]
        if pd.isna(text):
            mismatches.append(idx)
            continue
        lines = str(text).split("\n", 2)
        if len(lines) < 3 or "linkedin.com" not in lines[1]:
            mismatches.append(idx)
    return df.loc[mismatches]


def add_gender_field_to_sheet(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df = df.copy()
    mismatches = validate_linkedin_anchor(df)
    if len(mismatches) > 0:
        print(f"  AVISO: {len(mismatches)} linha(s) onde o Resume Text não "
              f"tem a estrutura esperada (linha 2 com 'linkedin.com') — "
              f"estas linhas NÃO serão alteradas (para não inserir o campo "
              f"num sítio errado):")
        for idx in mismatches.index:
            row = mismatches.loc[idx]
            print(f"    linha {idx}: ID={row.get('ID')}, "
                  f"Gender={row.get(GENDER_COL)}, Name={row.get(NAME_COL)!r}")

    skip_idx = set(mismatches.index)
    n_changed = 0
    for idx, row in df.iterrows():
        gender = row[GENDER_COL]
        if gender not in GENDER_FIELD_BY_GENDER or idx in skip_idx:
            continue
        text = row[TEXT_COL]
        if pd.isna(text):
            continue
        gender_field = GENDER_FIELD_BY_GENDER[gender]
        df.at[idx, TEXT_COL] = insert_gender_field(str(text), gender_field)
        n_changed += 1

    return df, n_changed
 
 
def main() -> None:
    input_path = Path(INPUT_PATH)
    output_path = input_path.with_name(f"{input_path.stem}_with_gender_field.xlsx")

    sheets = pd.read_excel(input_path, sheet_name=None)

    print(f"A processar '{input_path.name}'...\n")
    new_sheets = {}
    for sheet_name, df in sheets.items():
        if GENDER_COL not in df.columns or NAME_COL not in df.columns:
            new_sheets[sheet_name] = df
            continue

        print(f"[{sheet_name}]")
        new_df, n_changed = add_gender_field_to_sheet(df)
        print(f"  Campo de género inserido em {n_changed} linha(s)\n")
        new_sheets[sheet_name] = new_df

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in new_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Ficheiro gerado: {output_path}")


if __name__ == "__main__":
    main()
