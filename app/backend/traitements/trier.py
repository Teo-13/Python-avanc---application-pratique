import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


KEEP_COLUMNS = [
    "NUM_POSTE",
    "NOM_USUEL",
    "LAT",
    "LON",
    "ALTI",
    "AAAAMMJJ",
    "TN",
    "TX",
    "TM",
]
DATE_COLUMN = "AAAAMMJJ"
DATE_MIN = 20130101
DATE_MAX = 20241231
CHUNK_SIZE = 50_000

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_ZIP = REPO_ROOT / "datdatda.zip"
DEFAULT_OUTPUT_ZIP = REPO_ROOT / "datdatda_cleaned.zip"
OUTPUT_FOLDER_NAME = "datdatda_cleaned"


def clean_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk[DATE_COLUMN] = pd.to_numeric(chunk[DATE_COLUMN], errors="coerce")
    chunk = chunk[chunk[DATE_COLUMN].between(DATE_MIN, DATE_MAX, inclusive="both")]
    return chunk[KEEP_COLUMNS]


def iter_csv_members(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as archive:
        return sorted(
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv") and not name.endswith("/")
        )


def clean_zip_dataset(input_zip: Path, output_zip: Path) -> None:
    if not input_zip.exists():
        raise FileNotFoundError(f"Archive introuvable : {input_zip}")

    csv_members = iter_csv_members(input_zip)
    if not csv_members:
        raise ValueError(f"Aucun fichier CSV trouvé dans : {input_zip}")

    temp_dir = Path(tempfile.mkdtemp(prefix="clean_meteo_", dir=REPO_ROOT))
    output_dir = temp_dir / OUTPUT_FOLDER_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(input_zip, "r") as archive:
            for member_name in csv_members:
                output_file = output_dir / Path(member_name).name
                rows_read = 0
                rows_kept = 0
                wrote_header = False

                print(f"Nettoyage de {member_name}")

                with archive.open(member_name, "r") as source, output_file.open(
                    "w",
                    encoding="utf-8",
                    newline="",
                ) as destination:
                    for chunk in pd.read_csv(
                        source,
                        sep=";",
                        usecols=lambda column: column in KEEP_COLUMNS,
                        na_values=["mq", ""],
                        on_bad_lines="skip",
                        chunksize=CHUNK_SIZE,
                        low_memory=False,
                    ):
                        missing_columns = [col for col in KEEP_COLUMNS if col not in chunk.columns]
                        if missing_columns:
                            raise ValueError(
                                f"Colonnes manquantes dans {member_name} : {missing_columns}"
                            )

                        rows_read += len(chunk)
                        cleaned_chunk = clean_chunk(chunk)
                        rows_kept += len(cleaned_chunk)

                        cleaned_chunk.to_csv(
                            destination,
                            sep=";",
                            index=False,
                            header=not wrote_header,
                        )
                        wrote_header = True

                    if not wrote_header:
                        pd.DataFrame(columns=KEEP_COLUMNS).to_csv(
                            destination,
                            sep=";",
                            index=False,
                        )

                print(f"  lignes lues : {rows_read:,}")
                print(f"  lignes gardees : {rows_kept:,}")

        output_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for csv_file in sorted(output_dir.glob("*.csv")):
                archive.write(csv_file, arcname=f"{OUTPUT_FOLDER_NAME}/{csv_file.name}")

        print(f"Archive nettoyee creee : {output_zip}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Nettoie les CSV de datdatda.zip en gardant seulement certaines "
            "colonnes et les dates entre 20130101 et 20241231."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_ZIP,
        help=f"Archive zip source. Defaut : {DEFAULT_INPUT_ZIP}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_ZIP,
        help=f"Archive zip nettoyee. Defaut : {DEFAULT_OUTPUT_ZIP}",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_zip_dataset(args.input, args.output)
