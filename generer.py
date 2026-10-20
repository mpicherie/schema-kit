# -*- coding: utf-8 -*-
"""Fait dessiner un schéma par un LLM (local ou via API), avec correction automatique.

    python generer.py "le parcours d'une commande : panier, paiement, livraison" -o commande.png

Le LLM reçoit PROMPT_SYSTEME.md et écrit un script schema_kit, que ce lanceur
exécute. En cas d'erreur Python ou d'alerte de mise en page (boîtes qui se
chevauchent, qui sortent du cadre...), l'erreur lui est renvoyée telle quelle
et il corrige son script, jusqu'à --essais tentatives. Le script final est
gardé à côté de l'image (même nom, en .py) pour être retouché à la main.

Fonctionne avec tout serveur compatible avec l'API OpenAI :
    DeepSeek   --url https://api.deepseek.com/v1  + clé dans DEEPSEEK_API_KEY
    Ollama     --url http://localhost:11434/v1   (défaut)
    LM Studio  --url http://localhost:1234/v1
Modèle : --modele, ou la variable d'environnement SCHEMA_MODELE.
Identifiants disponibles chez ton fournisseur : python generer.py --modeles --url ...
Clé d'API : --cle, ou SCHEMA_CLE, DEEPSEEK_API_KEY, OPENAI_API_KEY (dans cet ordre).

ATTENTION : le script écrit par le modèle est EXÉCUTÉ sur ta machine, avec tes
droits. Il tourne dans un dossier temporaire, mais ce n'est pas un bac à sable.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(errors="replace")


def _entetes(cle):
    h = {"Content-Type": "application/json"}
    if cle:
        h["Authorization"] = "Bearer " + cle
    return h


def appeler(url, modele, messages, temperature=0.2, cle=None):
    """Un tour de conversation via l'API /chat/completions (format OpenAI)."""
    corps = json.dumps({"model": modele, "messages": messages,
                        "temperature": temperature}).encode("utf-8")
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=corps,
                                 headers=_entetes(cle))
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def lister_modeles(url, cle=None):
    req = urllib.request.Request(url.rstrip("/") + "/models", headers=_entetes(cle))
    with urllib.request.urlopen(req, timeout=60) as r:
        return sorted(m["id"] for m in json.load(r).get("data", []))


def extraire(reponse):
    """Le plus long bloc ```python de la réponse (les modèles bavards en mettent parfois deux)."""
    blocs = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", reponse, re.S)
    return max(blocs, key=len) if blocs else None


FORMATS = ("png", "pdf", "svg")


def executer(code, dossier, aussi):
    with open(os.path.join(dossier, "schema_genere.py"), "w", encoding="utf-8") as f:
        f.write(code)
    for ext in FORMATS:                       # ne jamais valider l'image d'un essai précédent
        ancien = os.path.join(dossier, "schema." + ext)
        if os.path.exists(ancien):
            os.remove(ancien)
    image = os.path.join(dossier, "schema.png")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg",
               SCHEMA_KIT_AUSSI=",".join(aussi),
               PYTHONPATH=ICI + os.pathsep + os.environ.get("PYTHONPATH", ""))
    try:
        p = subprocess.run([sys.executable, "schema_genere.py"], cwd=dossier, env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        return False, "Le script a dépassé 120 secondes d'exécution.", []
    alertes = [l for l in p.stderr.splitlines() if l.startswith("ATTENTION")]
    ok = p.returncode == 0 and os.path.exists(image)
    detail = p.stderr.strip() or ("" if ok else "Le script n'a pas écrit schema.png.")
    return ok, detail, alertes


def main():
    ap = argparse.ArgumentParser(description="Génère un schéma avec un LLM local.")
    ap.add_argument("demande", nargs="?", help="ce que le schéma doit montrer, en français courant")
    ap.add_argument("-o", "--sortie", default="schema.png")
    ap.add_argument("--url", default=os.environ.get("SCHEMA_URL", "http://localhost:11434/v1"))
    ap.add_argument("--modele", default=os.environ.get("SCHEMA_MODELE", "qwen2.5-coder:14b"))
    ap.add_argument("--essais", type=int, default=3)
    ap.add_argument("--cle", default=os.environ.get("SCHEMA_CLE")
                    or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"),
                    help="clé d'API (préférer une variable d'environnement)")
    ap.add_argument("--modeles", action="store_true",
                    help="liste les modèles disponibles sur --url, puis s'arrête")
    a = ap.parse_args()

    if a.modeles:
        try:
            for m in lister_modeles(a.url, a.cle):
                print(m)
            return 0
        except urllib.error.URLError as e:
            print("Liste des modèles indisponible sur %s : %s" % (a.url, getattr(e, "reason", e)))
            return 2
    if not a.demande:
        ap.error("décris le schéma voulu, entre guillemets")

    with open(os.path.join(ICI, "PROMPT_SYSTEME.md"), encoding="utf-8") as f:
        messages = [{"role": "system", "content": f.read()},
                    {"role": "user", "content": a.demande}]

    # On produit toujours le PNG (aperçu) ET le PDF vectoriel (pour les documents),
    # quelle que soit l'extension demandée ; -o x.svg ajoute le SVG.
    base, ext_demandee = os.path.splitext(os.path.abspath(a.sortie))
    aussi = ["pdf"] + (["svg"] if ext_demandee.lower() == ".svg" else [])
    sortie = base + ".png"
    script_sortie = base + ".py"
    dossier = tempfile.mkdtemp(prefix="schema_")
    dernier_code = None
    try:
        for essai in range(1, a.essais + 1):
            print("[%d/%d] %s dessine..." % (essai, a.essais, a.modele), flush=True)
            try:
                reponse = appeler(a.url, a.modele, messages, cle=a.cle)
            except urllib.error.HTTPError as e:
                # Le serveur a répondu, mais refuse : clé absente ou fausse,
                # identifiant de modèle inconnu... Son message dit pourquoi.
                corps = e.read().decode("utf-8", "replace")[:400]
                print("Le serveur %s a refusé la requête (HTTP %d) :" % (a.url, e.code))
                print("  " + corps)
                if e.code in (401, 403):
                    print("Clé d'API manquante ou invalide : définis DEEPSEEK_API_KEY.")
                elif e.code in (400, 404):
                    print("Identifiant de modèle inconnu ? Liste-les avec : "
                          "python generer.py --modeles --url %s" % a.url)
                return 2
            except urllib.error.URLError as e:
                print("Impossible de joindre le LLM sur %s (%s).\n"
                      "Le serveur est-il lancé ? Ollama : `ollama serve` ; LM Studio : "
                      "onglet Developer > Start Server." % (a.url, e.reason))
                return 2
            messages.append({"role": "assistant", "content": reponse})
            code = extraire(reponse)
            if code is None:
                print("  -> pas de bloc python dans la réponse, on redemande")
                messages.append({"role": "user", "content":
                    "Ta réponse ne contient aucun bloc ```python. Renvoie UNIQUEMENT le "
                    "script complet, dans un seul bloc ```python."})
                continue
            dernier_code = code
            ok, detail, alertes = executer(code, dossier, aussi)

            if ok and (not alertes or essai == a.essais):
                os.makedirs(os.path.dirname(sortie), exist_ok=True)
                ecrits = []
                for ext in FORMATS:
                    src = os.path.join(dossier, "schema." + ext)
                    if os.path.exists(src):
                        shutil.copyfile(src, base + "." + ext)
                        ecrits.append(base + "." + ext)
                with open(script_sortie, "w", encoding="utf-8") as f:
                    f.write(code)
                for e in ecrits:
                    print("Schéma : %s" % e)
                print("Script : %s" % script_sortie)
                if alertes:
                    print("Mise en page imparfaite, à retoucher dans le script :")
                    for l in alertes:
                        print("  " + l)
                return 0

            probleme = "\n".join(alertes) if ok else detail[-2500:]
            print("  -> à corriger : %s" % probleme.splitlines()[-1][:110])
            messages.append({"role": "user", "content":
                "J'ai exécuté ton script. Il a produit ceci :\n\n" + probleme +
                "\n\nCorrige le problème et renvoie le script COMPLET dans un seul bloc "
                "```python. Il doit toujours se terminer par s.enregistrer(\"schema.png\")."})

        print("Échec après %d essais." % a.essais)
        if dernier_code:
            with open(script_sortie, "w", encoding="utf-8") as f:
                f.write(dernier_code)
            print("Dernier script, pour le reprendre à la main : %s" % script_sortie)
        return 1
    finally:
        shutil.rmtree(dossier, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
