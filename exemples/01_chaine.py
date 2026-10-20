# -*- coding: utf-8 -*-
# Exemple 1 — une suite d'étapes, le cas le plus courant.
# chaine() place, centre et relie les boîtes : aucune coordonnée à calculer.
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from schema_kit import Schema

s = Schema(12, 3.6, titre="Le parcours d'une commande, du panier à la livraison")
e = s.chaine(
    ["Panier\nvalidé", "Paiement\naccepté", "Préparation\nen entrepôt", "Livraison\nau client"],
    couleurs=["blanc", "bleu", "ambre", "vert"])
s.annoter(e[1], "aucune donnée bancaire stockée")
s.annoter(e[3], "suivi envoyé par SMS")
s.enregistrer(os.path.join(ICI, "images", "01_chaine.png"))
