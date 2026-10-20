# -*- coding: utf-8 -*-
"""
schema_kit — des schémas d'architecture propres en quelques lignes de Python.

Conçu pour être piloté par un LLM, qui est mauvais en calcul de coordonnées :
  * on NOMME les boîtes, et les flèches se branchent seules sur le bon côté ;
  * un texte trop long se replie, et la police réduit si la boîte est petite ;
  * chaine() et pile() placent et relient des boîtes sans aucun calcul ;
  * enregistrer() signale les boîtes qui se chevauchent ou sortent du cadre,
    pour que le modèle corrige son script au tour suivant ;
  * les marges blanches sont rognées à l'enregistrement.

Exemple minimal :

    from schema_kit import Schema
    s = Schema(12, 4, titre="Le parcours d'un composant")
    s.chaine(["Examen", "Contrôle", "Sceau", "Passage"],
             couleurs=["bleu", "rouge", "vert", "ambre"])
    s.enregistrer("parcours.png")

Repère : origine en BAS à GAUCHE, unités en pouces. Une boîte est placée par
son coin bas-gauche (x, y) et sa taille (l, h).
"""
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.transforms import Bbox

plt.rcParams["font.family"] = "DejaVu Sans"   # couvre tous les accents français

# Couleurs SÉMANTIQUES : on choisit une couleur pour ce qu'elle veut dire.
#            fond        bord et texte d'accent
COULEURS = {
    "bleu":   ("#DCE6F5", "#1F3864"),   # neutre, technique, étape ordinaire
    "vert":   ("#DDF0E3", "#2E7D32"),   # accepté, confiance, résultat positif
    "rouge":  ("#F6DADA", "#B23A2E"),   # contrôle, refus, danger
    "ambre":  ("#FBEBD0", "#9A6212"),   # passage, transit, attente
    "violet": ("#E9E1F5", "#5B3F8C"),   # stockage, coffre, donnée sensible
    "gris":   ("#EFF1F4", "#5A6B7D"),   # secondaire, hors périmètre
    "blanc":  ("#FFFFFF", "#1F3864"),   # acteur extérieur (Internet, utilisateurs)
}
TEXTE = "#10243F"
GRIS = "#5A6B7D"


def _couleur(nom):
    if nom not in COULEURS:
        raise ValueError("Couleur inconnue : %r. Couleurs possibles : %s"
                         % (nom, ", ".join(COULEURS)))
    return COULEURS[nom]


def _ajuster(texte, l, h, taille, gras, mini=7.0):
    """Replie le texte à la largeur de la boîte ; réduit la police s'il déborde."""
    t = float(taille)
    while True:
        larg_car = (0.64 if gras else 0.58) * t / 72.0     # largeur moyenne d'un caractère
        n = max(4, int((l - 0.18) / larg_car))
        lignes = []
        for para in str(texte).split("\n"):
            # Ni mot coupé, ni coupure au trait d'union (« coffre- / fort »).
            lignes += textwrap.wrap(para, n, break_long_words=False,
                                    break_on_hyphens=False) or [""]
        trop_large = max(len(x) for x in lignes) > n
        trop_haut = len(lignes) * 1.25 * t / 72.0 > h - 0.1
        if not (trop_large or trop_haut) or t <= mini:
            return "\n".join(lignes), t
        t -= 0.5


class Schema:
    """Une feuille de dessin. largeur x hauteur en pouces (12 x 5 convient à une slide)."""

    def __init__(self, largeur=12, hauteur=5, titre=None, sous_titre=None, grille=False):
        self.L, self.H = float(largeur), float(hauteur)
        self.fig, self.ax = plt.subplots(figsize=(self.L, self.H))
        self.fig.subplots_adjust(0, 0, 1, 1)
        self.ax.set_xlim(0, self.L)
        self.ax.set_ylim(0, self.H)
        self.ax.axis("off")
        self.boites = {}
        # Bande réservée en haut pour le titre : rien ne doit monter au-dessus.
        self.haut_utile = self.H - (1.0 if sous_titre else 0.7 if titre else 0.15)
        self._titre_txt = self._sous_txt = None
        if titre:
            self._titre_txt = self.ax.text(self.L / 2, self.H - 0.32, titre, ha="center",
                                           va="center", fontsize=13, color=TEXTE, weight="bold")
        if sous_titre:
            self._sous_txt = self.ax.text(self.L / 2, self.H - 0.68, sous_titre, ha="center",
                                          va="center", fontsize=10, color=GRIS, style="italic")
        self._grille_on = grille
        if grille:
            self._grille()

    # ------------------------------------------------------------------ boîtes
    def boite(self, nom, x, y, texte, l=2.2, h=1.0, couleur="bleu", gras=True, taille=10):
        """Boîte arrondie. (x, y) = coin BAS-GAUCHE. Le texte se replie tout seul.
        `nom` sert ensuite à tirer des flèches : s.fleche("a", "b")."""
        if nom in self.boites:
            raise ValueError("Le nom de boîte %r est déjà utilisé." % nom)
        fond, bord = _couleur(couleur)
        self.ax.add_patch(FancyBboxPatch(
            (x, y), l, h, boxstyle="round,pad=0,rounding_size=0.12",
            fc=fond, ec=bord, lw=1.6, zorder=2))
        txt, t = _ajuster(texte, l, h, taille, gras)
        self.ax.text(x + l / 2, y + h / 2, txt, ha="center", va="center", fontsize=t,
                     color=TEXTE, weight="bold" if gras else "normal",
                     linespacing=1.25, zorder=3)
        self.boites[nom] = (x, y, l, h)
        return nom

    def chaine(self, etapes, y=None, l=2.2, h=1.0, ecart=0.9, couleurs=None, prefixe="etape"):
        """Aligne des étapes de gauche à droite, centrées, reliées par des flèches.
        Renvoie les noms créés : etape1, etape2...  Rétrécit tout seul si besoin."""
        n = len(etapes)
        couleurs = couleurs or ["bleu"] * n
        if len(couleurs) != n:
            raise ValueError("chaine() : %d étapes mais %d couleurs." % (n, len(couleurs)))
        dispo = self.L - 0.4
        if n * l + (n - 1) * ecart > dispo:
            ecart = min(ecart, 0.6)
            l = (dispo - (n - 1) * ecart) / n
        x0 = (self.L - (n * l + (n - 1) * ecart)) / 2
        if y is None:
            y = (0.2 + self.haut_utile) / 2 - h / 2
        noms = []
        for i, (txt, c) in enumerate(zip(etapes, couleurs)):
            nom = "%s%d" % (prefixe, i + 1)
            self.boite(nom, x0 + i * (l + ecart), y, txt, l=l, h=h, couleur=c)
            if noms:
                self.fleche(noms[-1], nom)
            noms.append(nom)
        return noms

    def pile(self, textes, x, y_centre=None, l=2.4, h=0.9, ecart=0.5, couleurs=None,
             prefixe="pile"):
        """Empile des boîtes verticalement (la première en haut), centrées sur
        y_centre. Sert aux embranchements : une étape qui se divise en deux."""
        n = len(textes)
        couleurs = couleurs or ["bleu"] * n
        if y_centre is None:
            y_centre = (0.2 + self.haut_utile) / 2
        haut_total = n * h + (n - 1) * ecart
        y = y_centre + haut_total / 2 - h
        noms = []
        for i, (txt, c) in enumerate(zip(textes, couleurs)):
            nom = "%s%d" % (prefixe, i + 1)
            self.boite(nom, x, y - i * (h + ecart), txt, l=l, h=h, couleur=c)
            noms.append(nom)
        return noms

    def zone(self, x, y, l, h, titre, couleur="bleu"):
        """Grand cadre de regroupement (zone réseau, équipe, phase). À tracer AVANT
        les boîtes qu'il contient. Son titre occupe ~0,5 en haut du cadre."""
        _fond, bord = _couleur(couleur)
        self.ax.add_patch(FancyBboxPatch(
            (x, y), l, h, boxstyle="round,pad=0,rounding_size=0.15",
            fc="#F7F9FC", ec=bord, lw=1.3, zorder=1))
        self.ax.text(x + 0.18, y + h - 0.24, titre, ha="left", va="center",
                     fontsize=10, color=bord, weight="bold", zorder=3)

    # ------------------------------------------------------------------ flèches
    def fleche(self, de, vers, couleur=None, pointille=False, texte=None):
        """Flèche de `de` vers `vers` : deux noms de boîtes (ou des points (x, y)).
        Les points d'accroche sont choisis automatiquement sur les bons côtés."""
        x1, y1 = self._accroche(de, vers)
        x2, y2 = self._accroche(vers, de)
        col = _couleur(couleur)[1] if couleur else TEXTE
        self.ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16, color=col, lw=1.8,
            linestyle="--" if pointille else "-", shrinkA=1, shrinkB=1, zorder=4))
        if texte:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if abs(x2 - x1) >= abs(y2 - y1):         # flèche plutôt horizontale
                # Replié à la longueur de la flèche : sinon il déborde sur les boîtes.
                n = max(8, int((abs(x2 - x1) - 0.1) / (0.58 * 8.5 / 72.0)))
                texte = "\n".join(textwrap.wrap(texte, n, break_long_words=False,
                                                break_on_hyphens=False))
                self.ax.text(mx, my + 0.12, texte, ha="center", va="bottom", fontsize=8.5,
                             color=col, style="italic", zorder=5, linespacing=1.2)
            else:                                     # plutôt verticale : à droite
                self.ax.text(mx + 0.12, my, texte, ha="left", va="center", fontsize=8.5,
                             color=col, style="italic", zorder=5)

    # ------------------------------------------------------------------ textes
    def note(self, x, y, texte, couleur="gris", taille=9, italique=True, gras=False):
        """Texte libre centré sur (x, y)."""
        col = GRIS if couleur == "gris" else _couleur(couleur)[1]
        self.ax.text(x, y, texte, ha="center", va="center", fontsize=taille, color=col,
                     style="italic" if italique else "normal",
                     weight="bold" if gras else "normal", zorder=5)

    def annoter(self, nom, texte, cote="dessous", couleur="gris", taille=8.5):
        """Petite légende collée à une boîte, 'dessous' ou 'dessus'."""
        x, y, l, h = self._boite(nom)
        col = GRIS if couleur == "gris" else _couleur(couleur)[1]
        if cote == "dessus":
            self.ax.text(x + l / 2, y + h + 0.1, texte, ha="center", va="bottom",
                         fontsize=taille, color=col, style="italic", zorder=5)
        else:
            self.ax.text(x + l / 2, y - 0.1, texte, ha="center", va="top",
                         fontsize=taille, color=col, style="italic", zorder=5)

    # ------------------------------------------------------------------ sortie
    def enregistrer(self, chemin="schema.png", dpi=200):
        """Vérifie la mise en page puis écrit le schéma, rogné au plus près du contenu.

        Le format suit l'extension : .png (image), .pdf ou .svg (VECTORIEL : net à
        toute taille, le bon choix pour un document PDF ou imprimé). On peut en
        demander plusieurs d'un coup : s.enregistrer(["x.png", "x.pdf"])."""
        for alerte in self._verifier():
            print("ATTENTION : " + alerte, file=sys.stderr)
        chemins = [chemin] if isinstance(chemin, str) else list(chemin)
        # Formats supplémentaires demandés par l'appelant (generer.py s'en sert
        # pour obtenir le PDF même quand le modèle n'a écrit que le PNG).
        for ext in os.environ.get("SCHEMA_KIT_AUSSI", "").split(","):
            ext = ext.strip().lstrip(".")
            if ext:
                autre = os.path.splitext(chemins[0])[0] + "." + ext
                if autre not in chemins:
                    chemins.append(autre)
        self._recaler_titre()
        cadre = self._cadre_contenu()
        for c in chemins:
            os.makedirs(os.path.dirname(os.path.abspath(c)), exist_ok=True)
            self.fig.savefig(c, dpi=dpi, bbox_inches=cadre, facecolor="white")
            print("Schema ecrit : %s" % c)
        plt.close(self.fig)
        return chemins[0] if isinstance(chemin, str) else chemins

    # ------------------------------------------------------------------ interne
    def _boite(self, nom):
        if nom not in self.boites:
            raise KeyError("Boîte inconnue : %r. Boîtes définies : %s"
                           % (nom, ", ".join(self.boites) or "(aucune)"))
        return self.boites[nom]

    def _centre(self, ref):
        if isinstance(ref, str):
            x, y, l, h = self._boite(ref)
            return x + l / 2, y + h / 2
        return tuple(ref)

    def _accroche(self, a, b):
        if not isinstance(a, str):
            return tuple(a)
        x, y, l, h = self._boite(a)
        cx, cy = x + l / 2, y + h / 2
        bx, by = self._centre(b)
        dx, dy = bx - cx, by - cy
        if abs(dx) * h >= abs(dy) * l:            # cible plutôt à gauche / à droite
            return (x + l if dx > 0 else x), cy
        return cx, (y + h if dy > 0 else y)       # cible plutôt au-dessus / en dessous

    def _recaler_titre(self):
        """Centre le titre AU-DESSUS DU DESSIN réel, juste au-dessus de lui.
        Sans cela, un dessin qui n'occupe pas toute la feuille laisse un titre
        décentré qui flotte loin au-dessus des boîtes."""
        if self._titre_txt is None or self._grille_on:
            return
        rendu = self.fig.canvas.get_renderer()
        autres = [a for a in list(self.ax.patches) + list(self.ax.texts)
                  if a is not self._titre_txt and a is not self._sous_txt]
        if not autres:
            return
        bb = Bbox.union([a.get_window_extent(rendu) for a in autres]) \
                 .transformed(self.ax.transData.inverted())
        cx, y = (bb.x0 + bb.x1) / 2, bb.y1 + 0.32
        if self._sous_txt is not None:
            self._sous_txt.set_position((cx, y))
            y += 0.36
        self._titre_txt.set_position((cx, y))

    def _cadre_contenu(self, marge=0.12):
        """Rectangle (en pouces) qui englobe tout ce qui est dessiné, plus une marge.
        Sert à rogner les blancs, pour TOUS les formats, vectoriels compris."""
        rendu = self.fig.canvas.get_renderer()
        etendues = [a.get_window_extent(rendu)
                    for a in list(self.ax.patches) + list(self.ax.texts) + list(self.ax.lines)]
        if not etendues:
            return "tight"
        bb = Bbox.union(etendues).transformed(self.fig.dpi_scale_trans.inverted())
        return Bbox.from_extents(bb.x0 - marge, bb.y0 - marge, bb.x1 + marge, bb.y1 + marge)

    def _verifier(self):
        alertes, noms = [], list(self.boites)
        for i, a in enumerate(noms):
            xa, ya, la, ha = self.boites[a]
            if xa < 0 or ya < 0 or xa + la > self.L or ya + ha > self.H:
                alertes.append("la boite %r sort du cadre (cadre : %g x %g)" % (a, self.L, self.H))
            elif ya + ha > self.haut_utile + 1e-6:
                alertes.append("la boite %r empiete sur le titre : son haut (y+h = %.2f) "
                               "doit rester sous %.2f" % (a, ya + ha, self.haut_utile))
            for b in noms[i + 1:]:
                xb, yb, lb, hb = self.boites[b]
                if xa < xb + lb and xb < xa + la and ya < yb + hb and yb < ya + ha:
                    alertes.append("les boites %r et %r se chevauchent" % (a, b))
        return alertes

    def _grille(self):
        """Quadrillage d'aide à la mise en place (Schema(..., grille=True))."""
        for x in range(int(self.L) + 1):
            self.ax.axvline(x, color="#E3E7EC", lw=0.6, zorder=0)
            self.ax.text(x, 0.03, str(x), fontsize=7, color="#9AA5B1", ha="center")
        for y in range(int(self.H) + 1):
            self.ax.axhline(y, color="#E3E7EC", lw=0.6, zorder=0)
            self.ax.text(0.05, y, str(y), fontsize=7, color="#9AA5B1", va="center")
