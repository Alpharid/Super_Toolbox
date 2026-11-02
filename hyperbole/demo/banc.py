"""Le banc de bugs injectés : les Einherjar retrouvent-ils les bugs plantés dans La Fosse, et crient-ils au loup
quand il n'y en a pas ? Rappel = bugs retrouvés / bugs plantés ; fausses alertes = « problèmes » sur le jeu propre.
(Idée reprise de playtest-agent et GBQA, veille Heimdall 2026-11-02.)
"""
from __future__ import annotations

import json
from pathlib import Path

# Comment reconnaître, dans les constats, chaque bug planté (mots du titre, en minuscules).
MATCH = {
    "blocage_marais": lambda f: f["domaine"] == "bugs" and "blocage" in f["titre"].lower(),
    "double_vente": lambda f: f["domaine"] == "exploit" and ("vendre" in f["titre"].lower() or "gain aberrant de or" in f["titre"].lower()),
    "fuite_memoire": lambda f: f["domaine"] == "perf" and "mem" in f["titre"].lower(),
    "boss_injuste": lambda f: "wyrm" in f["titre"].lower() or "wyrm" in str(f["preuve"]).lower(),
    "erreur_forge": lambda f: "erreur moteur" in f["titre"].lower() and "forge" in f["titre"].lower(),
    "teleport_mine": lambda f: "téléportation" in f["titre"].lower(),
    "potion_morte": lambda f: "sans effet" in f["titre"].lower() and "boire" in f["titre"].lower(),
}


def _constats(summary) -> list[dict]:
    return json.loads(Path(summary).read_text(encoding="utf-8"))["analyse"]["constats"]


def score(summary_bugs, summary_clean, planted: list[str]) -> dict:
    fb = _constats(summary_bugs)
    fc = _constats(summary_clean)
    found = {b: [f["titre"] for f in fb if MATCH[b](f)] for b in planted}
    # Fausse alerte = un « problème » de bug/faille/perf sur le jeu propre. L'équilibre et le fun restent des avis de
    # design qu'un jeu sans bug peut mériter (La Fosse a un mur de progression voulu) : ils ne comptent pas ici.
    false_alarms = [f["titre"] for f in fc if f["gravite"] == "probleme" and f["domaine"] in ("bugs", "exploit", "perf")]
    unexplained = [f["titre"] for f in fb if f["gravite"] == "probleme" and not any(MATCH[b](f) for b in planted)]
    res = {"rappel": round(sum(1 for v in found.values() if v) / len(planted), 2), "trouves": found,
           "fausses_alertes_jeu_propre": false_alarms, "problemes_non_attribues": unexplained}
    print("\n== Banc de bugs injectés ==")
    for b, v in found.items():
        print(f"  {'TROUVÉ ' if v else 'MANQUÉ '} {b:16} {v[0] if v else ''}")
    print(f"  Rappel : {res['rappel'] * 100:.0f} %   ·   fausses alertes sur le jeu propre : {len(false_alarms)}")
    for t in false_alarms:
        print(f"    ! {t}")
    return res
