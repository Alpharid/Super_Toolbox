"""Recompte les chiffres de la vitrine de la méthode (guides/notre-methode.md et guides/vitrine/notre-methode.html) et les réécrit.

Un chiffre écrit à la main vieillit (un compte de tests avait un jour de retard) : chaque chiffre de la vitrine est posé entre
des marqueurs, et ce script les recompte dans le dépôt et les journaux du projet de référence (Guardians of the Seal).
- HTML : `<b data-n="tests">386</b>` ou `<span data-n="…">…</span>` (le texte de l'élément est remplacé),
  et `<!--n:cle-->…<!--/n-->` pour un bloc entier (barres et tableau des dépenses) ;
- Markdown : `<!--n:cle-->…<!--/n-->` (invisible une fois rendu).
Ce qui ne se recompte pas sûrement (bruitages, références, verdicts du tri musical) reste écrit à la main, hors marqueurs.

    python scripts/recompter_vitrine.py                 # montre ce qui changerait
    python scripts/recompter_vitrine.py --ecrire        # réécrit le .md et la vitrine
    python scripts/recompter_vitrine.py --ecrire --ach  # … et recopie la vitrine dans le site d'ACH (web/methode/index.html)
    python scripts/recompter_vitrine.py --sans-tests    # sans lister les tests (dotnet), plus rapide

Les tests sont comptés par `dotnet test <projet> --list-tests` (compile en Debug si besoin, ne lance rien) : c'est le même nombre
que celui d'un vrai passage (les théories comptent une fois par cas).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

for _flux in (sys.stdout, sys.stderr):
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

BOITE = Path(__file__).resolve().parents[1]
MD = BOITE / "guides" / "notre-methode.md"
VITRINE = BOITE / "guides" / "vitrine" / "notre-methode.html"
ACH = Path(r"C:\ACH\web\methode\index.html")

# Le projet de référence de la vitrine, et ce qu'on y compte.
PROJET = Path(r"C:\Guardians_of_the_Seal")
DEBUT = dt.date(2026, 10, 18)  # premier jour de Guardians
PROJETS_DE_TESTS = [  # (nom affiché, projet de tests)
    ("règles", "shared/Gardiens.Regles.Tests"),
    ("serveur", "server/Gardiens.Serveur.Tests"),
    ("joueurs IA", "bots/Gardiens.Descelles.Tests"),
    ("noyau du client", "noyau/Gardiens.Client.Noyau.Tests"),
]
MEMOIRE = Path.home() / ".claude" / "projects" / "C--Guardians-of-the-Seal" / "memory"
# Les dépenses de l'API, rangées par usage (préfixe du champ « usage » du journal) dans l'ordre de la vitrine.
FAMILLES = [
    ("Traduction et relecture", ("traduction", "relecture")),
    ("Le regard", ("regard",)),
    ("Gazette et rapports", ("gazette", "rapports")),
    ("L'Esprit des joueurs IA", ("esprit",)),
]
AUTRES = "Essais et autres"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOTS = ["zéro", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze"]


def entier(n: int) -> str:
    """1477 → « 1 477 » (espace fine insécable, comme le reste de la vitrine)."""
    return f"{n:,}".replace(",", "\u202f")


def dollars(x: float) -> str:
    return f"{x:,.2f}".replace(",", "\u202f").replace(".", ",") + " $"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJET, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def compter_tests() -> tuple[int, str]:
    total, detail = 0, []
    for nom, proj in PROJETS_DE_TESTS:
        r = subprocess.run(["dotnet", "test", str(PROJET / proj), "--list-tests"], cwd=PROJET, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        apres = r.stdout.split("Les tests suivants sont disponibles", 1)[-1] if "disponibles" in r.stdout else \
            r.stdout.split("The following Tests are available", 1)[-1]
        n = sum(1 for l in apres.splitlines() if l.startswith("    ") and l.strip())
        if r.returncode != 0 or n == 0:
            raise RuntimeError(f"tests de {proj} introuvables (code {r.returncode}) :\n{r.stdout[-800:]}{r.stderr[-400:]}")
        total += n
        detail.append(f"{nom} {n}")
    return total, ", ".join(detail)


def depenses() -> dict:
    journal = PROJET / "tools" / "claude_api" / "depenses.jsonl"
    par = defaultdict(float)
    n = 0
    for l in journal.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        n += 1
        u = d.get("usage", "")
        fam = next((f for f, pref in FAMILLES if u.startswith(pref)), AUTRES)
        par[fam] += d.get("cout", 0.0)
    lots = sum(1 for l in (journal.parent / "lots.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())
    return {"appels": n, "total": sum(par.values()), "par": par, "lots": lots}


def recompter(tests: bool) -> dict[str, str]:
    auj = dt.date.today()
    semaines = round((auj - DEBUT).days / 7)
    c: dict[str, str] = {
        "releve_iso": auj.isoformat(),
        "releve": f"{auj.day} {MOIS[auj.month - 1]} {auj.year}",
        "fin": f"{auj.day} {MOIS[auj.month - 1]}",
        "semaines": str(semaines),
        "semaines_mot": MOTS[semaines].capitalize() if semaines < len(MOTS) else str(semaines),
        "semaines_mot_min": MOTS[semaines] if semaines < len(MOTS) else str(semaines),
        "commits": entier(int(git("rev-list", "--count", "HEAD"))),
    }
    cl = PROJET / "server" / "maj" / "changelog.json"
    c["versions"] = entier(len(json.loads(cl.read_text(encoding="utf-8"))["changelog"]))
    c["chantiers"] = entier(len([f for f in (PROJET / "docs" / "chantiers").glob("*.md") if f.stem != "orchestrateur"]))
    c["pages"] = entier(len([f for f in (PROJET / "art" / "rendus" / "choix").glob("*.html") if "gabarit" not in f.stem]))
    c["lecons"] = entier(sum(1 for f in MEMOIRE.glob("*.md") if "type: feedback" in f.read_text(encoding="utf-8")))
    c["seances"] = entier(len([f for f in (PROJET / "bots" / "rapports").glob("*.jsonl")
                               if re.fullmatch(r"\d{4}-\d\d-\d\d_\d{4}", f.stem)]))
    ent = PROJET / "client" / "assets" / "entites"
    c["entites"] = entier(sum(1 for d in ent.iterdir() if all((d / f"dir_{k}.png").exists() for k in range(8))))
    c["tuiles"] = entier(len(list((PROJET / "client" / "assets" / "carte" / "tiziri").glob("sol_*.png"))))
    ic = PROJET / "client" / "assets" / "icones"
    c["icones"] = entier(len(list((ic / "objets").glob("*.png"))) + len(list((ic / "sceaux").glob("*.png"))))
    d = depenses()
    c["api_appels"] = entier(d["appels"])
    c["api_dollars"] = dollars(d["total"])
    c["api_lots"] = entier(d["lots"])
    lignes = [(f, d["par"].get(f, 0.0)) for f, _ in FAMILLES] + ([(AUTRES, d["par"][AUTRES])] if d["par"].get(AUTRES) else [])
    c["barres"] = barres(lignes)
    c["table"] = table(lignes, d["total"])
    if tests:
        n, detail = compter_tests()
        c["tests"], c["tests_detail"] = entier(n), detail
    return c


def barres(lignes: list[tuple[str, float]]) -> str:
    haut = max(v for _, v in lignes) or 1
    out = []
    for nom, v in lignes:
        largeur = f"calc((100% - 70px) * {v:.2f} / {haut:.2f})"
        out.append(f'    <div class="barre" tabindex="0"><span class="nom">{html.escape(nom)}</span><span class="piste">'
                   f'<span class="rempli" style="display:block;width:{largeur}"></span><span class="val" style="left:{largeur}">'
                   f'{dollars(v)}</span></span><span class="bulle">{html.escape(nom)} : {dollars(v)}</span></div>')
    return "\n".join(out) + "\n"


def table(lignes: list[tuple[str, float]], total: float) -> str:
    rangs = "".join(f"<tr><td>{html.escape(n)}</td><td>{dollars(v)}</td></tr>" for n, v in lignes)
    return (f"<table><tr><th>Usage</th><th>Dépense</th></tr>\n        {rangs}\n"
            f"        <tr><td><b>Total</b></td><td><b>{dollars(total)}</b></td></tr></table>")


def remplacer(texte: str, c: dict[str, str]) -> tuple[str, list[str]]:
    changes = []

    def par_attribut(m):
        cle, ancien = m.group(2), m.group(3)
        if cle not in c or c[cle] == ancien:
            return m.group(0)
        changes.append(f"{cle} : {ancien!r} → {c[cle]!r}")
        return m.group(1) + c[cle] + m.group(4)

    def par_commentaire(m):
        cle, ancien = m.group(1), m.group(2)
        if cle not in c or c[cle] == ancien:
            return m.group(0)
        changes.append(f"{cle} : {'(bloc)' if len(ancien) > 60 else repr(ancien)} → {'(bloc)' if len(c[cle]) > 60 else repr(c[cle])}")
        return f"<!--n:{cle}-->{c[cle]}<!--/n-->"

    texte = re.sub(r'(<(?:b|span)[^>]*\bdata-n="([a-z_]+)"[^>]*>)([^<]*)(</(?:b|span)>)', par_attribut, texte)
    texte = re.sub(r"<!--n:([a-z_]+)-->(.*?)<!--/n-->", par_commentaire, texte, flags=re.S)
    return texte, changes


def main():
    ap = argparse.ArgumentParser(description="Recompte les chiffres de la vitrine de la méthode.")
    ap.add_argument("--ecrire", action="store_true")
    ap.add_argument("--ach", action="store_true", help="recopier la vitrine dans le site d'ACH")
    ap.add_argument("--sans-tests", action="store_true")
    a = ap.parse_args()
    c = recompter(not a.sans_tests)
    for f in (MD, VITRINE):
        with f.open(encoding="utf-8", newline="") as h:  # garder les fins de ligne d'origine
            avant = h.read()
        apres, changes = remplacer(avant, c)
        print(f"{f.relative_to(BOITE)} : {len(changes)} chiffre(s) changé(s)")
        for x in changes:
            print("   ", x)
        if a.ecrire and apres != avant:
            f.write_bytes(apres.encode("utf-8"))
    if a.ach:
        if not a.ecrire:
            print("--ach demande --ecrire")
        elif ACH.parent.exists():
            shutil.copyfile(VITRINE, ACH)
            print(f"vitrine recopiée dans {ACH} (pousser ACH)")


if __name__ == "__main__":
    main()
