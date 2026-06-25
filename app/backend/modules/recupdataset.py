import re
import zipfile
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ARCHIVES_DATASETS = [
    REPO_ROOT / "datdatda_cleaned.zip",
    REPO_ROOT / "datdatda.zip",
]


def get_dataset_archive_path() -> Path:
    for archive_path in ARCHIVES_DATASETS:
        if archive_path.exists():
            return archive_path
    raise FileNotFoundError("Aucune archive de datasets trouvee.")


@lru_cache(maxsize=1)
def lister_fichiers_datasets() -> list[str]:
    archive_path = get_dataset_archive_path()

    with zipfile.ZipFile(archive_path, "r") as archive:
        return sorted(
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv") and "rr-t-vent" in name.lower()
        )

# ficher centenant le numéro de département
def fichiers_contenant_nombre(nombre: str) -> list[str]:
    dep = str(nombre).strip().upper()

    if dep.isdigit() and len(dep) == 1:
        dep = dep.zfill(2)

    pattern = re.compile(rf"Q_{re.escape(dep)}_.*\.csv$", re.IGNORECASE)

    return [
        fichier
        for fichier in lister_fichiers_datasets()
        if pattern.search(Path(fichier).name)
    ]
