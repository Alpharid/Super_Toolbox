"""Une mission de Mr. Popo : quel jeu, quel objectif, quels lobbies, combien de chambres, combien de temps.

Fichier JSON (exemples dans missions/, schéma dans schemas/mission.schema.json). Tout a une valeur par défaut :
une mission minimale tient en trois lignes (jeu.cmd + objectif).
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

# Ce que chaque objectif demande par défaut (si la mission ne donne pas ses lobbies).
# Les profils qui agissent sur les autres (saboteur, meneur) reçoivent automatiquement un jumeau sans eux.
OBJECTIVES = {
    "equilibre": [{"pure": "moyen", "bots": 4}, {"pure": "tryhard", "bots": 4}, {"pure": "casual", "bots": 4}],
    "fun": [{"personas": {"moyen": 2, "casual": 1, "chill": 1, "streamer": 1}}, {"pure": "streamer", "bots": 3}],
    "bugs": [{"pure": "fouineur", "bots": 3}, {"personas": {"moyen": 2, "tryhard": 1, "completionniste": 1}}],
    "apprentissage": [{"pure": "debutant", "bots": 4}, {"pure": "casual", "bots": 4}],
    "social": [{"personas": {"moyen": 2, "casual": 1, "chill": 1, "leader": 1}},
               {"personas": {"moyen": 2, "casual": 1, "chill": 1, "saboteur": 1}}],
    "economie": [{"personas": {"moyen": 3, "tryhard": 1, "chill": 2, "completionniste": 1}}],
    "charge": [{"personas": {"moyen": 8, "casual": 4, "tryhard": 2, "chill": 2}}],
    "non-regression": [{"personas": {"moyen": 2, "tryhard": 1, "casual": 1}}],
}

THRESHOLDS = {
    "moments_per_hour_min": 4.0,        # fun : moins que ça par heure de jeu = rien à montrer
    "downtime_max": 0.25,               # fun : part du temps passée à s'ennuyer
    "frustration_per_hour_max": 6.0,    # fun : épisodes de frustration par heure
    "variety_min": 0.45,                # fun : entropie normalisée des gestes (0 = toujours le même, 1 = tout varié)
    "success_band": [0.55, 0.85],       # défi : part des rencontres gagnées ; en dessous trop dur, au-dessus trop facile
    "fail_rate_max": 0.30,              # bugs/ergonomie : gestes ratés / gestes
    "early_quit_max": 0.30,             # jouabilité : part des séances quittées avant la moitié prévue
    "stuck_cluster_min": 3,             # bugs : blocages au même endroit (cellule) pour en faire un « point de blocage »
    "cell_size": 4.0,                   # bugs : taille d'une cellule de la carte des blocages (unités du jeu)
    "leak_per_hour_pct": 5.0,           # perf : croissance par heure de jeu (mémoire, nœuds, objets) au-delà = fuite
    "exploit_iqr": 3.0,                 # exploits : gain/h au-delà de Q3 + k*IQR des autres = aberrant
    "cause_dominance": 0.5,             # équilibre : une seule cause de mort au-delà de cette part = déséquilibre
    "regression_pct": 15.0,             # comparaison : écart d'une mesure clé au-delà duquel on parle de régression
}

DEFAULTS = {
    "nom": "mission",
    "objectif": ["equilibre", "fun", "bugs"],
    "mode": "chambre",            # chambre (accélérée) | reel (x1) | mixte (les deux)
    "vitesse": "max",             # "max" ou un multiple ; ignoré en reel (toujours 1)
    "duree_min": 10,              # minutes RÉELLES par chambre
    "duree_jeu_h": None,          # plafond en heures DE JEU par chambre (s'arrête au premier atteint)
    "chambres": "auto",           # chambres en parallèle ; auto = cœurs / 2
    "jumeaux": True,              # jumeau sans saboteur/meneur pour chaque lobby qui en a un
    "graines": None,              # liste de graines fixes (non-régression) ; sinon tirées
    "valhalla": {"cycles": 1},    # nombre de passages ; chaque cycle rejoue tous les lobbies avec de nouvelles graines
    "variantes": [],              # [{"nom": "A", "params": {...}}] : chaque lobby joué pour chaque variante (A/B)
    "params": {},                 # passés tels quels au jeu (difficulté, carte...)
    "personas_dirs": [],
    "seuils": {},
    "esprit": {"actif": False, "url": "http://127.0.0.1:11434", "modele": "mistral-nemo:12b"},
    "lint": {"fichiers": [], "interdits": [], "autorises": []},
    "heartbeat_s": 60,            # sans nouvelle ligne de journal pendant ce temps : chambre figée -> tuée
    "grace_s": 20,                # délai entre la demande d'arrêt (fichier stop) et le kill
}


def _merge(a: dict, b: dict) -> dict:
    out = copy.deepcopy(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load(path: str | os.PathLike) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    m = _merge(DEFAULTS, data)
    m["_path"] = str(path.resolve())
    m["_dir"] = str(path.resolve().parent)
    return finish(m)


def finish(m: dict) -> dict:
    if isinstance(m["objectif"], str):
        m["objectif"] = [m["objectif"]]
    for o in m["objectif"]:
        if o not in OBJECTIVES:
            raise ValueError(f"objectif inconnu : {o} (connus : {', '.join(OBJECTIVES)})")
    if m["mode"] not in ("chambre", "reel", "mixte"):
        raise ValueError("mode = chambre | reel | mixte")
    if "jeu" not in m or not m["jeu"].get("cmd"):
        raise ValueError("la mission doit donner jeu.cmd (la commande qui ouvre une chambre ; voir docs/PROTOCOLE.md)")
    if not m.get("lobbies"):
        lobbies = []
        for o in m["objectif"]:
            for spec in OBJECTIVES[o]:
                if spec not in lobbies:
                    lobbies.append(copy.deepcopy(spec))
        m["lobbies"] = lobbies
    m["seuils"] = {**THRESHOLDS, **m.get("seuils", {})}
    if m["chambres"] == "auto":
        m["chambres"] = max(1, (os.cpu_count() or 2) // 2)
    base = Path(m.get("_dir", "."))
    m["personas_dirs"] = [str((base / d).resolve()) for d in m.get("personas_dirs", [])]
    return m
