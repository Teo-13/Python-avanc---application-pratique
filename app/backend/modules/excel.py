import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPORTS_DIR = REPO_ROOT / "app" / "backend" / "exports"


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return cleaned.strip("-") or "ville"


def exporter_donnees_excel(
    nom_ville: str,
    numero_departement: str,
    station_info: dict,
    mesures_df: pd.DataFrame,
) -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{_slugify(nom_ville)}_dep-{numero_departement}_"
        f"station-{station_info['num_poste']}.xlsx"
    )
    file_path = EXPORTS_DIR / filename

    wb = Workbook()
    ws = wb.active
    ws.title = "Meteo"

    ws.append(
        [
            "ville",
            "departement",
            "station",
            "num_poste",
            "distance_km",
            "date",
            "TN",
            "TX",
            "TM",
        ]
    )

    for _, row in mesures_df.iterrows():
        ws.append(
            [
                nom_ville,
                numero_departement,
                station_info["nom_station"],
                station_info["num_poste"],
                station_info["distance_km"],
                row["date"].strftime("%Y-%m-%d"),
                None if pd.isna(row["TN"]) else round(float(row["TN"]), 1),
                None if pd.isna(row["TX"]) else round(float(row["TX"]), 1),
                None if pd.isna(row["TM"]) else round(float(row["TM"]), 1),
            ]
        )

    wb.save(file_path)

    return {
        "filename": filename,
        "path": str(file_path),
    }
