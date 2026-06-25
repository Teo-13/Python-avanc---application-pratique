"""
data_loader.py
--------------
Télécharge à la volée uniquement le fichier CSV météo Météo-France
nécessaire pour un département donné.

Règles :
  - Un seul type de fichier : Q_{dep}_previous-1950-2024_RR-T-Vent.csv.gz
  - Filtrage sur les années >= 2013 directement au chargement
  - On garde LAT et LON pour le croisement avec les communes (Haversine)
  - Zéro écriture sur disque (tout en RAM via io.BytesIO)
"""

import io
import requests
import pandas as pd
from functools import lru_cache

# ── Constantes ────────────────────────────────────────────────────────────────

DATASET_ID  = "6569b51ae64326786e4e8e1a"
API_URL     = f"https://www.data.gouv.fr/api/2/datasets/{DATASET_ID}/resources/"
MIN_YEAR    = 2013          # on filtre tout ce qui est avant

# Colonnes à charger (on ignore les ~25 autres colonnes inutiles)
USECOLS = ["NUM_POSTE", "LAT", "LON", "AAAAMMJJ", "TN"]


# ── Catalogue des ressources (appelé une seule fois, mis en cache) ─────────────

@lru_cache(maxsize=1)
def _get_catalogue() -> pd.DataFrame:
    """
    Récupère via l'API data.gouv.fr la liste de toutes les ressources
    du dataset quotidien et retourne un DataFrame filtré sur les fichiers
    du type : Q_{dep}_previous-1950-2024_RR-T-Vent
    """
    print("📡 Récupération du catalogue depuis data.gouv.fr…")

    # 1) On récupère le nombre total de ressources
    r = requests.get(API_URL, params={"page_size": 1}, timeout=30)
    r.raise_for_status()
    total = r.json()["total"]

    # 2) On les récupère toutes en une seule requête
    r = requests.get(API_URL, params={"page_size": total, "type": "main"}, timeout=60)
    r.raise_for_status()

    rows = []
    for res in r.json()["data"]:
        title = res.get("title", "")
        url   = res.get("url",   "")

        # On ne garde que les fichiers RR-T-Vent de type "previous-1950-2024"
        if "RR-T-Vent" not in title or "previous-1950-2024" not in title:
            continue

        # Extraction du numéro de département depuis le nom
        # Exemple : "Q_75_previous-1950-2024_RR-T-Vent"
        parts = title.split("_")
        if len(parts) < 2:
            continue
        dep = parts[1]

        rows.append({"title": title, "url": url, "dep": dep})

    df = pd.DataFrame(rows)
    print(f"   → {len(df)} fichiers 'previous-1950-2024' trouvés dans le catalogue.")
    return df


# ── Sélection du fichier pour un département ──────────────────────────────────

def _get_resource_for_dep(dep: str) -> dict:
    """
    Retourne la ressource (dict avec title + url) pour le département demandé.
    Lève une ValueError si le département est introuvable.
    """
    catalogue = _get_catalogue()
    match = catalogue[catalogue["dep"] == dep]

    if match.empty:
        available = sorted(catalogue["dep"].tolist())
        raise ValueError(
            f"Département '{dep}' introuvable.\n"
            f"Exemples de valeurs valides : {available[:10]} …"
        )

    resource = match.iloc[0].to_dict()
    print(f"   ✅ Fichier trouvé : {resource['title']}")
    return resource


# ── Téléchargement + parsing en mémoire ──────────────────────────────────────

def _download_and_parse(resource: dict) -> pd.DataFrame:
    """
    Télécharge le .csv.gz en RAM (io.BytesIO, sans écriture disque),
    charge uniquement les colonnes utiles, convertit les types
    et filtre sur MIN_YEAR.
    """
    print(f"   ⬇️  Téléchargement de {resource['title']}…")
    r = requests.get(resource["url"], timeout=180, stream=True)
    r.raise_for_status()

    content = io.BytesIO(r.content)

    df = pd.read_csv(
        content,
        sep=";",
        compression="gzip",
        usecols=lambda c: c in USECOLS,
        dtype={
            "NUM_POSTE": str,
            "AAAAMMJJ":  str,
            "LAT":       float,
            "LON":       float,
            "TN":        float,
        },
        na_values=["mq", ""],   # "mq" = manquant chez Météo-France
        low_memory=False,
    )

    # Conversion de la date
    df["date"] = pd.to_datetime(df["AAAAMMJJ"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"])

    # Filtre : on ne garde que >= 2013
    df = df[df["date"].dt.year >= MIN_YEAR]

    # TN est en dixièmes de °C → conversion en °C
    df["TN"] = df["TN"] / 10.0

    print(f"      → {len(df):,} lignes chargées (>= {MIN_YEAR}).")
    return df


# ── Fonction publique principale ──────────────────────────────────────────────

def load_temperature_data(dep: str) -> pd.DataFrame:
    """
    Télécharge et retourne les données de température minimale (TN)
    pour un département, filtrées à partir de 2013.

    Paramètres
    ----------
    dep : numéro de département sous forme de chaîne
          Exemples : "75", "01", "2A", "971"

    Retourne
    --------
    DataFrame avec colonnes :
        NUM_POSTE  – identifiant de la station (str)
        LAT        – latitude de la station (float, WGS84)
        LON        – longitude de la station (float, WGS84)
        date       – date de la mesure (datetime)
        TN         – température minimale journalière en °C (float, NaN si manquant)
    """
    print(f"\n🌡️  Chargement des données pour le département {dep}…")
    resource = _get_resource_for_dep(dep)
    df = _download_and_parse(resource)

    # Colonnes finales ordonnées
    df = df[["NUM_POSTE", "LAT", "LON", "date", "TN"]].sort_values(
        ["NUM_POSTE", "date"]
    ).reset_index(drop=True)

    print(f"\n✅ {len(df):,} enregistrements — {df['NUM_POSTE'].nunique()} stations "
          f"— période {df['date'].dt.year.min()}–{df['date'].dt.year.max()}")
    return df


# ── Test rapide ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = load_temperature_data("75")
    print(df.head(10))
    print(f"\nTN min : {df['TN'].min():.1f}°C  |  TN max : {df['TN'].max():.1f}°C")
    print(f"Valeurs manquantes TN : {df['TN'].isna().mean()*100:.1f}%")
    print(f"Stations : {df[['NUM_POSTE','LAT','LON']].drop_duplicates()}")
