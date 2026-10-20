# -*- coding: utf-8 -*-
# Exemple 3 — une architecture en zones. Les zones se tracent AVANT les boîtes,
# et on laisse ~0,5 en haut de chaque zone pour son titre.
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from schema_kit import Schema

s = Schema(12, 6, titre="Trois zones, un seul sens de passage")
s.zone(0.2, 0.3, 4.8, 4.9, "ZONE EXTÉRIEURE  (reliée à Internet)", "bleu")
s.zone(5.3, 0.3, 1.6, 4.9, "PASSAGE", "ambre")
s.zone(7.2, 0.3, 4.6, 4.9, "ZONE PROTÉGÉE  (coupée du monde)", "vert")

# Zone extérieure : une colonne qui descend.
s.boite("sortie", 1.1, 3.6, "Point de sortie unique : la seule machine reliée à Internet", l=2.8, h=0.9)
s.boite("controles", 1.1, 2.1, "Les deux contrôles : vulnérabilités + antivirus", l=2.8, h=0.9, couleur="rouge")
s.boite("sceau", 1.1, 0.7, "Sceau apposé par le coffre-fort", l=2.8, h=0.9, couleur="violet")
s.fleche("sortie", "controles")
s.fleche("controles", "sceau")

# Le passage, puis la zone protégée qui remonte.
s.boite("passage", 5.45, 0.7, "Sens unique", l=1.3, h=0.9, couleur="ambre")
s.boite("reception", 7.6, 0.7, "Réception : vérifie le sceau", l=2.4, h=0.9, couleur="vert")
s.boite("magasin", 7.6, 2.1, "Magasin interne de confiance", l=2.4, h=0.9)
s.boite("equipes", 7.6, 3.6, "Équipes internes", l=2.4, h=0.9, couleur="blanc")
s.boite("coffre", 10.4, 0.7, "Coffre interne", l=1.2, h=0.9, couleur="violet")

s.fleche("sceau", "passage", couleur="ambre")
s.fleche("passage", "reception", couleur="ambre")
s.fleche("reception", "magasin", couleur="vert")
s.fleche("magasin", "equipes")
s.fleche("coffre", "reception", pointille=True, couleur="violet")
s.enregistrer(os.path.join(ICI, "images", "03_zones.png"))
