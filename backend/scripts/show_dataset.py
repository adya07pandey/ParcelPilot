from pathlib import Path

import pandas as pd

dataset = Path(__file__).resolve().parents[2] / "data" / "ParcelPilot_full_dataset.xlsx"
excel = pd.ExcelFile(dataset)

print(excel.sheet_names)
for sheet in excel.sheet_names:
    df = pd.read_excel(dataset, sheet_name=sheet)
    print(f"{sheet}: {df.shape[0]} rows x {df.shape[1]} columns")
    print(", ".join(str(column) for column in df.columns))
