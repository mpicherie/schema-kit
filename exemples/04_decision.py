# -*- coding: utf-8 -*-
# Exemple 4 — un point de décision : une vérification qui aboutit à
# ACCEPTÉ ou REFUSÉ. Le texte d'une flèche verticale se place tout seul à droite.
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from schema_kit import Schema

s = Schema(12, 4.6, titre="La confiance ne se transporte pas : elle se vérifie à l'arrivée")
s.boite("envoi", 0.4, 1.55, "Envoi\n(zone extérieure)", l=2.2, h=1.0)
s.boite("attente", 4.6, 1.6, "Zone d'attente\n(à l'arrivée)", l=2.3, h=0.9, couleur="ambre")
s.boite("verif", 7.9, 1.6, "Vérification du sceau, sans rien demander", l=2.6, h=0.9)
s.boite("ok", 8.2, 3.0, "ACCEPTÉ", l=2.0, h=0.7, couleur="vert")
s.boite("ko", 8.2, 0.2, "REFUSÉ", l=2.0, h=0.7, couleur="rouge")

s.fleche("envoi", "attente", couleur="ambre", pointille=True, texte="sens unique, sans réponse")
s.fleche("attente", "verif")
s.fleche("verif", "ok", couleur="vert", texte="sceau intact")
s.fleche("verif", "ko", couleur="rouge", texte="sceau absent ou faux")
s.enregistrer(os.path.join(ICI, "images", "04_decision.png"))
