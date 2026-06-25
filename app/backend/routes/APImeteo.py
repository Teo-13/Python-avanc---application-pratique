import zipfile

import pandas as pd
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

try:
    from app.backend.modules.recupdataset import (
        fichiers_contenant_nombre,
        get_dataset_archive_path,
        lister_fichiers_datasets,
    )
    from app.backend.modules.ville import CoodonnesVille, distance, testeVille
except ModuleNotFoundError:
    from backend.modules.recupdataset import (
        fichiers_contenant_nombre,
        get_dataset_archive_path,
        lister_fichiers_datasets,
    )
    from backend.modules.ville import CoodonnesVille, distance, testeVille


meteo_bp = Blueprint("distance", __name__)

COLONNES_STATION = ["NUM_POSTE", "NOM_USUEL", "LAT", "LON"]
COLONNES_METEO = ["NUM_POSTE", "AAAAMMJJ", "TN", "TX", "TM"]
DISTANCE_MAX_DEPARTEMENT = 40
DATE_MIN = 20130101
DATE_MAX = 20241231


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

    # Une station apparait sur plusieurs dates : on la garde une seule fois.
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

    df = df.dropna(subset=["TN", "TX", "TM"], how="all")
    return df


def calculer_tableau_distances(coord_ville: tuple[float, float], fichiers: list[str]) -> list[dict]:
    tableau_distances = []

    for fichier in fichiers:
        stations = lire_stations_fichier(fichier)

        for station in stations:
            coord_station = station["coord_station"]
            distance_km = distance(coord_ville, coord_station)

            tableau_distances.append(
                {
                    "fichier": fichier,
                    "num_poste": station["num_poste"],
                    "nom_station": station["nom_station"],
                    "lat": coord_station[0],
                    "lon": coord_station[1],
                    "distance_km": round(distance_km, 2),
                }
            )

    return tableau_distances


def station_plus_proche(tableau_distances: list[dict]) -> dict | None:
    if not tableau_distances:
        return None

    return min(tableau_distances, key=lambda station: station["distance_km"])


def formater_mesure(row: pd.Series) -> dict:
    return {
        "date": row["date"].strftime("%Y-%m-%d"),
        "TN": None if pd.isna(row["TN"]) else round(float(row["TN"]), 1),
        "TX": None if pd.isna(row["TX"]) else round(float(row["TX"]), 1),
        "TM": None if pd.isna(row["TM"]) else round(float(row["TM"]), 1),
    }


def lire_mesures_station(nom_fichier: str, num_poste: str) -> dict:
    df = lire_mesures_fichier(nom_fichier)
    df = df[df["NUM_POSTE"] == str(num_poste)].copy()

    if df.empty:
        return {
            "num_poste": str(num_poste),
            "nombre_mesures": 0,
            "premiere_date": None,
            "derniere_date": None,
            "mesure_plus_recente": None,
            "gelees_par_annee": {},
            "historique_complet": [],
        }

    df["date"] = pd.to_datetime(df["AAAAMMJJ"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    historique_complet = []
    for _, row in df.iterrows():
        historique_complet.append(formater_mesure(row))

    derniere_ligne = df.iloc[-1]
    premiere_ligne = df.iloc[0]
    mesure_plus_recente = formater_mesure(derniere_ligne)

    df["annee"] = df["date"].dt.year
    gelees_par_annee = {}
    for annee in range(2013, 2025):
        gelees_par_annee[str(annee)] = int(
            ((df["annee"] == annee) & (df["TN"].notna()) & (df["TN"] <= 0)).sum()
        )

    return {
        "num_poste": str(num_poste),
        "nombre_mesures": int(len(df)),
        "premiere_date": premiere_ligne["date"].strftime("%Y-%m-%d"),
        "derniere_date": derniere_ligne["date"].strftime("%Y-%m-%d"),
        "mesure_plus_recente": mesure_plus_recente,
        "gelees_par_annee": gelees_par_annee,
        "historique_complet": historique_complet,
    }


@meteo_bp.route("/", methods=["POST", "OPTIONS"])
@cross_origin()
def meteo():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    ville =  data.get("ville", "").strip()

    print(f"Ville : {ville}")

    if not ville:
        return jsonify({"error": "Veuillez fournir une ville."}), 400

    coord_ville = CoodonnesVille(ville)
    if not coord_ville:
        return jsonify({
            "error": "Impossible de recuperer les coordonnees de cette ville pour le moment. Reessaie dans quelques secondes."
        }), 400

    try:
        numerodepartement = testeVille(ville)
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400

    fichiers_departement = fichiers_contenant_nombre(numerodepartement)
    if not fichiers_departement:
        return jsonify({"error": "Aucun fichier trouve pour ce departement."}), 404

    tableau_distances = calculer_tableau_distances(coord_ville, fichiers_departement)
    station_min = station_plus_proche(tableau_distances)

    if station_min is None:
        return jsonify({"error": "Aucune station exploitable dans le departement."}), 404

    recherche_autres_datasets = False

    if station_min["distance_km"] > DISTANCE_MAX_DEPARTEMENT:
        autres_fichiers = [
            fichier
            for fichier in lister_fichiers_datasets()
            if fichier not in fichiers_departement
        ]

        tableau_autres_distances = calculer_tableau_distances(coord_ville, autres_fichiers)
        station_min_autres = station_plus_proche(tableau_autres_distances)

        if station_min_autres is not None:
            tableau_distances.extend(tableau_autres_distances)

            if station_min_autres["distance_km"] < station_min["distance_km"]:
                station_min = station_min_autres
                recherche_autres_datasets = True

    mesures_station = lire_mesures_station(
        station_min["fichier"],
        station_min["num_poste"],
    )

    return jsonify(
        {
            "ville": ville,
            "coord_ville": {"lat": coord_ville[0], "lon": coord_ville[1]},
            "departement": numerodepartement,
            "station_plus_proche": station_min,
            "mesures_station": mesures_station,
            "recherche_autres_datasets": recherche_autres_datasets,
            "distance_limite_km": DISTANCE_MAX_DEPARTEMENT,
        }
    )
