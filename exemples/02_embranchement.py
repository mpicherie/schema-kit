# -*- coding: utf-8 -*-
# Exemple 2 — une étape qui se divise en deux contrôles parallèles, qui se
# rejoignent ensuite. pile() empile les deux branches ; fleche() relie par nom.
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from schema_kit import Schema

s = Schema(12, 5, titre="Un seul contrôle qui refuse, et le composant ne va pas plus loin")
s.boite("examen", 0.4, 1.6, "1. EXAMEN\ndu composant", l=2.2, h=1.1)
c1, c2 = s.pile(["2a. VULNÉRABILITÉS\ndéjà connues ?", "2b. ANTIVIRUS\ncomposant piégé ?"],
                x=3.4, y_centre=2.15, l=2.6, h=0.9, couleurs=["rouge", "rouge"])
s.boite("sceau", 6.9, 1.6, "3. SCEAU\napposé sur le composant", l=2.4, h=1.1, couleur="vert")
s.boite("passage", 9.8, 1.65, "4. PASSAGE\nà sens unique", l=2.0, h=1.0, couleur="ambre")

for c in (c1, c2):
    s.fleche("examen", c)
    s.fleche(c, "sceau")
s.fleche("sceau", "passage")

s.note(4.7, 3.75, "LES DEUX doivent donner leur feu vert", couleur="rouge", italique=False, gras=True)
s.annoter("examen", "on établit la liste\nde ses ingrédients")
s.annoter("sceau", "la matrice du sceau\nne sort jamais du coffre", couleur="vert")
s.enregistrer(os.path.join(ICI, "images", "02_embranchement.png"))
