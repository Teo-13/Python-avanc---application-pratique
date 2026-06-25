import re
import unicodedata

from geopy.geocoders import Nominatim
from geopy.distance  import geodesic

DEPARTEMENTS = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte"
}

# ======== calcule coordonnées ville ======
def CoodonnesVille(ville):
    geolocator = Nominatim(user_agent="mon_application_voyage")
    try:
        location = geolocator.geocode(ville)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception:
        return None

# ======= s'avoir le numéro du département de la ville =====  
def get_departement(ville: str) -> str | None:
    geolocator = Nominatim(user_agent="mon_application")

    location = geolocator.geocode(
        f"{ville}, France",
        addressdetails=True
    )

    if location is None:
        return None

    adresse = location.raw.get("address", {})
    return adresse.get("county")  # département


def get_departement(ville: str) -> str | None:
    geolocator = Nominatim(user_agent="mon_application")
    
    if ville.lower() == "paris" :
        return "Paris" 

    location = geolocator.geocode(
        f"{ville}, France",
        addressdetails=True
    )

    if location is None:
        return None

    adresse = location.raw.get("address", {})
    return adresse.get("county")  # département


def normalize_departement_name(nom: str) -> str:
    texte = unicodedata.normalize("NFKD", nom).casefold()
    texte = "".join(char for char in texte if not unicodedata.combining(char))
    texte = texte.replace("’", "'")
    return re.sub(r"[\s'-]+", " ", texte).strip()

def testeVille(ville):
    departement = get_departement(ville)
    print(departement)

    DEPARTEMENTS_INV = {
        normalize_departement_name(nom): code for code, nom in DEPARTEMENTS.items()
    }

    if departement is None:
        raise ValueError("Impossible de trouver le département pour cette ville.")

    code_departement = DEPARTEMENTS_INV.get(normalize_departement_name(departement))
    if code_departement is None:
        raise KeyError(f"Département introuvable dans le référentiel : {departement}")

    print(code_departement)
    return code_departement

def distance(coordA, coordB):
    distance = geodesic(coordA, coordB).km
    return distance





