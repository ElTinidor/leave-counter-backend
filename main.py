from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io

app = FastAPI()

# Allow CORS for your React frontend URL (127.0.0.1:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "https://eltinidor.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/count-leaves")
async def count_leaves(file: UploadFile = File(...), name: str = Form(...)):
    content = await file.read()
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, header=2,  engine="openpyxl")

    target = name.strip().upper()
    unique_al_dates = {}
    unique_sl_dates = {}
    unique_ph_dates = {}

    for _, sheet_df in sheets.items():
        sheet_df = sheet_df.fillna("")
        dates = list(sheet_df.columns[2:])
        col0 = sheet_df.iloc[:, 0].astype(str).str.strip().str.upper()
        matches = col0 == target
        if not matches.any():
            continue

        row = sheet_df.loc[matches].iloc[0, 2:]
        for idx, cell in enumerate(row):
            if idx >= len(dates):
                break
            date_val = dates[idx]
            if pd.isna(date_val) or date_val == "":
                continue
            try:
                dt = pd.to_datetime(date_val)
                date_key = dt.date()
            except Exception:
                continue

            cell_value = str(cell).strip().upper()
            if cell_value in ("AL", "ANNUAL LEAVE"):
                unique_al_dates[date_key] = 1
            elif "SL" in cell_value:
                increment = 0.5 if cell_value in ("AM SL", "PM SL") else 1
                unique_sl_dates[date_key] = min(1, unique_sl_dates.get(date_key, 0) + increment)
            elif "PH" in cell_value or "PUBLIC HOLIDAY" in cell_value:
                unique_ph_dates[date_key] = 1

    al_total = sum(unique_al_dates.values())
    sl_total = sum(unique_sl_dates.values())
    ph_total = sum(unique_ph_dates.values())

    al_dates = [str(d) for d in sorted(unique_al_dates)]
    sl_dates = [str(d) for d in sorted(unique_sl_dates)]
    ph_dates = [str(d) for d in sorted(unique_ph_dates)]

    return JSONResponse({
        "name": name,
        "al_count": al_total,
        "sl_count": sl_total,
        "ph_count": ph_total,
        "al_dates": al_dates,
        "sl_dates": sl_dates,
        "ph_dates": ph_dates,
    })
