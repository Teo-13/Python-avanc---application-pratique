import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import zipfile

import pandas as pd

from app.backend.modules.excel import exporter_donnees_excel
from app.backend.modules.recupdataset import (
    fichiers_contenant_nombre,
    get_dataset_archive_path,
    lister_fichiers_datasets,
)
from app.backend.modules.ville import CoodonnesVille, distance


VILLE = "Asnières-sur-Saône"
NUMERO_DEPARTEMENT = "01"
DISTANCE_MAX_DEPARTEMENT = 40
COLONNES_STATION = ["NUM_POSTE", "NOM_USUEL", "LAT", "LON"]
COLONNES_METEO = ["NUM_POSTE", "AAAAMMJJ", "TN", "TX", "TM"]
DATE_MIN = 20130101
DATE_MAX = 20241231


def lire_mesures_fichier(nom_fichier: str) -> pd.DataFrame:
    archive_path = get_dataset_archive_path()

    with zipfile.ZipFile(archive_path, "r") as archive:
        with archive.open(nom_fichier, "r") as source:
            df = pd.read_csv(
                source,
                sep=";",
                usecols=lambda colonne: colonne in COLONNES_METEO,
                na_values=["mq", ""],
                on_bad_lines="skip",
                low_memory=False,
            )

    df["AAAAMMJJ"] = pd.to_numeric(df["AAAAMMJJ"], errors="coerce")
    df = df[df["AAAAMMJJ"].between(DATE_MIN, DATE_MAX, inclusive="both")]
    df = df.dropna(subset=["NUM_POSTE"])
    df["NUM_POSTE"] = df["NUM_POSTE"].astype(str)

    for colonne in ["TN", "TX", "TM"]:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    return df.dropna(subset=["TN", "TX", "TM"], how="all")


def lire_stations_fichier(nom_fichier: str) -> list[dict]:
    archive_path = get_dataset_archive_path()

    with zipfile.ZipFile(archive_path, "r") as archive:
        with archive.open(nom_fichier, "r") as source:
            df = pd.read_csv(
                source,
                sep=";",
                usecols=lambda colonne: colonne in COLONNES_STATION,
                na_values=["mq", ""],
                on_bad_lines="skip",
                low_memory=False,
            )

    mesures = lire_mesures_fichier(nom_fichier)
    stations_actives = set(mesures["NUM_POSTE"].astype(str).tolist())

    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")
    df = df.dropna(subset=["NUM_POSTE", "NOM_USUEL", "LAT", "LON"])
    df["NUM_POSTE"] = df["NUM_POSTE"].astype(str)
    df = df[df["NUM_POSTE"].isin(stations_actives)]
    df = df.drop_duplicates(subset=["NUM_POSTE", "NOM_USUEL", "LAT", "LON"])

    stations = []
    for _, row in df.iterrows():
        stations.append(
            {
                "num_poste": str(row["NUM_POSTE"]),
                "nom_station": row["NOM_USUEL"],
                "coord_station": (float(row["LAT"]), float(row["LON"])),
            }
        )
    return stations


def calculer_tableau_distances(coord_ville: tuple[float, float], fichiers: list[str]) -> list[dict]:
    tableau_distances = []

    for fichier in fichiers:
        stations = lire_stations_fichier(fichier)
        for station in stations:
            distance_km = distance(coord_ville, station["coord_station"])
            tableau_distances.append(
                {
                    "fichier": fichier,
                    "num_poste": station["num_poste"],
                    "nom_station": station["nom_station"],
                    "lat": station["coord_station"][0],
                    "lon": station["coord_station"][1],
                    "distance_km": round(distance_km, 2),
                }
            )

    return tableau_distances


def station_plus_proche(tableau_distances: list[dict]) -> dict | None:
    if not tableau_distances:
        return None
    return min(tableau_distances, key=lambda station: station["distance_km"])


def lire_mesures_station_dataframe(nom_fichier: str, num_poste: str) -> pd.DataFrame:
    df = lire_mesures_fichier(nom_fichier)
    df = df[df["NUM_POSTE"] == str(num_poste)].copy()

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["AAAAMMJJ"].astype("Int64").astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


def exporter_pour_ville() -> None:
    coord_ville = CoodonnesVille(VILLE)
    if not coord_ville:
        raise ValueError(f"Impossible de recuperer les coordonnees pour {VILLE}.")

    fichiers_departement = fichiers_contenant_nombre(NUMERO_DEPARTEMENT)
    if not fichiers_departement:
        raise FileNotFoundError(
            f"Aucun dataset trouve pour le departement {NUMERO_DEPARTEMENT}."
        )

    tableau_distances = calculer_tableau_distances(coord_ville, fichiers_departement)
    station_min = station_plus_proche(tableau_distances)
    if station_min is None:
        raise ValueError("Aucune station exploitable trouvee dans le departement.")

    if station_min["distance_km"] > DISTANCE_MAX_DEPARTEMENT:
        autres_fichiers = [
            fichier
            for fichier in lister_fichiers_datasets()
            if fichier not in fichiers_departement
        ]
        autres_distances = calculer_tableau_distances(coord_ville, autres_fichiers)
        station_hors_dep = station_plus_proche(autres_distances)

        if (
            station_hors_dep is not None
            and station_hors_dep["distance_km"] < station_min["distance_km"]
        ):
            station_min = station_hors_dep

    mesures_df = lire_mesures_station_dataframe(
        station_min["fichier"],
        station_min["num_poste"],
    )
    if mesures_df.empty:
        raise ValueError("Aucune mesure meteo disponible pour la station retenue.")

    export_result = exporter_donnees_excel(
        nom_ville=VILLE,
        numero_departement=NUMERO_DEPARTEMENT,
        station_info=station_min,
        mesures_df=mesures_df,
    )

    print(f"Ville : {VILLE}")
    print(f"Departement : {NUMERO_DEPARTEMENT}")
    print(f"Station : {station_min['nom_station']} ({station_min['num_poste']})")
    print(f"Distance : {station_min['distance_km']} km")
    print(f"Fichier cree : {export_result['path']}")


if __name__ == "__main__":
    exporter_pour_ville()
