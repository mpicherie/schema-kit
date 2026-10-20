# Instructions pour l'agent

Ce dépôt sert à produire des **schémas d'architecture clairs** (images PNG) avec la bibliothèque `schema_kit`. Ton travail : transformer une demande en français courant en un schéma qu'on comprend en dix secondes.

## Avant le premier schéma

1. Lis **`PROMPT_SYSTEME.md` en entier**. Il contient le repère, l'API, les règles de style et trois exemples commentés. Les règles de style ne sont pas facultatives : ce sont elles qui font la différence entre un schéma correct et un bon schéma.
2. Vérifie que la bibliothèque s'importe, depuis la racine du dépôt :
   ```
   python -c "import schema_kit; print('ok')"
   ```
   En cas d'échec : `pip install -e .`

## Pour chaque schéma demandé

1. **Trouve le message.** Écris en une phrase ce que le lecteur doit comprendre. Ce sera le titre. Un titre est une phrase (« Un seul contrôle qui refuse, et le composant ne va pas plus loin »), pas un nom de sujet (« Architecture du pipeline »).
2. **Pars de l'exemple le plus proche** dans `exemples/` :

   | Fichier | Pour |
   |---|---|
   | `01_chaine.py` | une suite d'étapes |
   | `02_embranchement.py` | une étape qui se divise en branches parallèles, puis se rejoint |
   | `03_zones.py` | une architecture découpée en zones (réseaux, équipes, environnements) |
   | `04_decision.py` | une vérification qui mène à « accepté » ou « refusé » |

3. **Écris le script** dans `schemas/<nom-court>.py`, sur ce modèle :
   ```python
   import sys; sys.path.insert(0, ".")   # on lance depuis la racine du dépôt
   from schema_kit import Schema

   s = Schema(12, 5, titre="...")
   # ... boîtes, flèches ...
   s.enregistrer(["schemas/<nom-court>.png", "schemas/<nom-court>.pdf"])
   ```
   Écris toujours les deux : le PNG sert d'aperçu, le PDF sert aux documents (voir plus bas).
4. **Exécute-le depuis la racine** du dépôt : `python schemas/<nom-court>.py`
5. **Corrige jusqu'à zéro alerte.** Si la sortie contient une erreur ou une ligne `ATTENTION` (boîtes qui se chevauchent, boîte hors du cadre ou sur le titre), corrige les positions ou les tailles, puis relance. Ne livre jamais un schéma qui produit une alerte.
6. **Regarde l'image si tu le peux.** Si tu sais lire les images, ouvre le PNG et vérifie : texte lisible, aucune flèche qui traverse une boîte, ensemble équilibré, pas de grand vide inutile. Corrige si besoin.
7. **Livre** le chemin du PNG, et une phrase qui dit ce que le schéma montre.

## Insérer le schéma dans un document

| Le document est… | Utilise | Pourquoi |
|---|---|---|
| un PDF produit par code (PyMuPDF, reportlab…) | le **.pdf** | vectoriel : net à n'importe quel zoom, texte sélectionnable, fichier léger (~20 Ko) |
| du LaTeX | le **.pdf** : `\includegraphics[width=\linewidth]{schemas/<nom>.pdf}` | idem |
| Word, PowerPoint, Markdown, une page web | le **.png** | 200 dpi par défaut, suffisant pour une page A4 |
| imprimé en grand (affiche, A3) | le **.pdf**, ou un PNG réenregistré avec `dpi=300` | |

Exemple avec PyMuPDF, schéma vectoriel posé sur une page A4 :
```python
import fitz                                        # pip install pymupdf
doc = fitz.open(); page = doc.new_page(width=595, height=842)
page.show_pdf_page(fitz.Rect(56, 100, 539, 320), fitz.open("schemas/<nom>.pdf"), 0)
doc.save("rapport.pdf")
```
Le schéma est déjà rogné au plus près du dessin. Garde ses proportions : fixe la largeur et laisse la hauteur suivre.

## Contrôle avant de livrer

- [ ] Le titre est une phrase qui dit le message.
- [ ] Entre 3 et 8 boîtes. Au-delà, propose deux schémas.
- [ ] Deux lignes de texte au plus par boîte, cinq mots au plus par flèche.
- [ ] Chaque couleur est choisie pour son sens (voir `PROMPT_SYSTEME.md`), jamais pour décorer.
- [ ] Le flux se lit dans un seul sens : de gauche à droite, ou de haut en bas.
- [ ] Aucune ligne `ATTENTION` à l'exécution.
- [ ] Pas de jargon si le public n'est pas technique : on dit ce que la chose fait.

## À ne pas faire

- **Ne modifie pas `schema_kit.py`** pour faire taire une alerte. C'est le script du schéma qu'il faut corriger.
- N'utilise pas matplotlib directement : tout passe par `schema_kit`.
- N'écris pas en dehors de `schemas/`. Ce dossier est ignoré par git : les schémas de l'utilisateur ne sont jamais publiés par erreur.
- Ne pousse rien sur git sans qu'on te le demande.
