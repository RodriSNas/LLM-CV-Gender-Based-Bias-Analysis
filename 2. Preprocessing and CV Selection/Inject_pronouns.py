from pathlib import Path
import pandas as pd
 
INPUT_PATH = r"C:\Users\rodri\Desktop\Mestrado\Tese\Method\datasets\Resume\selected_cvs_updated_expanded_v5.xlsx"
 
GENDER_COL = "Gender Condition"
NAME_COL = "Injected Name"
TEXT_COL = "Resume Text"
 
PRONOUN_BY_GENDER = {
    "male":   "(he/him)",
    "female": "(she/her)",
}
 
 
def insert_pronoun(name: str, text: str, pronoun: str) -> str:
    return f"{name} {pronoun}" + text[len(name):]
 
 
def validate_name_anchor(df: pd.DataFrame) -> pd.DataFrame:
    mask_gendered = df[GENDER_COL].isin(PRONOUN_BY_GENDER.keys())
    mismatches = []
    for idx, row in df[mask_gendered].iterrows():
        name = row[NAME_COL]
        text = row[TEXT_COL]
        if pd.isna(name) or pd.isna(text) or not str(text).startswith(str(name)):
            mismatches.append(idx)
    return df.loc[mismatches]
 
 
def add_pronouns_to_sheet(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df = df.copy()
    mismatches = validate_name_anchor(df)
    if len(mismatches) > 0:
        print(f"  AVISO: {len(mismatches)} linha(s) onde o Resume Text não "
              f"começa pelo Injected Name — estas linhas NÃO serão "
              f"alteradas (para não inserir o pronome num sítio errado):")
        for idx in mismatches.index:
            row = mismatches.loc[idx]
            print(f"    linha {idx}: ID={row.get('ID')}, "
                  f"Gender={row.get(GENDER_COL)}, Name={row.get(NAME_COL)!r}")
 
    skip_idx = set(mismatches.index)
    n_changed = 0
    for idx, row in df.iterrows():
        gender = row[GENDER_COL]
        if gender not in PRONOUN_BY_GENDER or idx in skip_idx:
            continue
        name = row[NAME_COL]
        text = row[TEXT_COL]
        if pd.isna(name) or pd.isna(text):
            continue
        pronoun = PRONOUN_BY_GENDER[gender]
        df.at[idx, TEXT_COL] = insert_pronoun(str(name), str(text), pronoun)
        n_changed += 1
 
    return df, n_changed
 
 
def main() -> None:
    input_path = Path(INPUT_PATH)
    output_path = input_path.with_name(f"{input_path.stem}_with_pronouns.xlsx")
 
    sheets = pd.read_excel(input_path, sheet_name=None)
 
    print(f"A processar '{input_path.name}'...\n")
    new_sheets = {}
    for sheet_name, df in sheets.items():
        if GENDER_COL not in df.columns or NAME_COL not in df.columns:
            # sheet sem estas colunas (não deveria acontecer nas 4 sheets
            # esperadas, mas protege contra sheets extra no futuro)
            new_sheets[sheet_name] = df
            continue
 
        print(f"[{sheet_name}]")
        new_df, n_changed = add_pronouns_to_sheet(df)
        print(f"  Pronomes inseridos em {n_changed} linha(s)\n")
        new_sheets[sheet_name] = new_df
 
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in new_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
 
    print(f"Ficheiro gerado: {output_path}")
 
 
if __name__ == "__main__":
    main()
