import os
import re

import os

def fichiers_contenant_nombre(dossier: str, nombre: int):
    """
    Retourne les fichiers dont le nom contient le nombre donné.
    Exemple: 12 -> 'truc_12exemple.csv'
    """

    nombre = str(nombre)
    resultats = []

    for fichier in os.listdir(dossier):
        if nombre in fichier:
            resultats.append(fichier)

    return resultats

dossier = "C:/Users/teome/Documents/github/Python-avanc---application-pratique/data"

resultat = fichiers_contenant_nombre(dossier,nombre=24)

print(resultat)