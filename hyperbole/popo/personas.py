"""Les profils de joueurs (personas) des Einherjar : chargement, héritage, contrôle, composition des lobbies.

Un profil est un fichier JSON (voir personas/ et schemas/persona.schema.json). Un jeu peut surcharger ou ajouter des
profils dans son propre dossier : le dernier dossier lu gagne, champ par champ (`extends` pour hériter).
"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BASE_DIR = HERE / "personas"

# Les envies (drives) reconnues par la Tête générique. Un jeu peut en ajouter : une option taguée « craft » est notée
# avec drives["craft"] si le profil l'a, sinon 0. Les tags des options du jeu doivent viser ce vocabulaire d'abord.
DRIVES = ("progress", "mastery", "explore", "collect", "create", "social", "help", "show", "break", "disrupt",
          "lead", "rest", "survive")

DEFAULTS = {
    "drives": {d: 0.3 for d in DRIVES},
    "skill": {"aim": 0.5, "reaction_ms": 350, "mistake_rate": 0.08, "apm": 60, "learning_rate": 0.5},
    "knowledge": "partial",
    "patience": 0.5,
    "frustration_tolerance": 0.5,
    "boredom_tolerance": 0.5,
    "risk": 0.5,
    "curiosity": 0.5,
    "reads_text": 0.5,
    "session": {"minutes": [45, 120], "afk_per_hour": 0.3, "afk_minutes": [1, 4]},
    "social_role": "none",
    "lobby": "both",
    "nuisance_cap_per_hour": None,
    "instructions": "",
    "goals": {},
    "tools": None,
    "voice": {"style": "neutre", "templates": {}},
    "surfaces": [],
}

KNOWLEDGE = ("none", "partial", "wiki")
ROLES = ("none", "leader", "saboteur", "follower")
# Rôles qui agissent sur les autres : au plus un par lobby, jamais en lobby pur, et un jumeau sans eux (même graine).
DISRUPTIVE = ("leader", "saboteur")


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_all(dirs: list[str | Path] | None = None) -> dict[str, dict]:
    """Charge les profils de base puis ceux des dossiers donnés (surcharge champ par champ), résout `extends`."""
    raw: dict[str, dict] = {}
    for d in [BASE_DIR, *(dirs or [])]:
        d = Path(d)
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8-sig"))
            pid = data.get("id") or f.stem
            data["id"] = pid
            data.setdefault("_source", str(f))
            raw[pid] = _merge(raw[pid], data) if pid in raw else data
    resolved: dict[str, dict] = {}

    def resolve(pid: str, chain: tuple = ()) -> dict:
        if pid in resolved:
            return resolved[pid]
        if pid in chain:
            raise ValueError(f"héritage circulaire : {' -> '.join(chain + (pid,))}")
        if pid not in raw:
            raise KeyError(f"profil inconnu : {pid}")
        p = raw[pid]
        parent = p.get("extends")
        base = resolve(parent, chain + (pid,)) if parent else DEFAULTS
        full = _merge(base, {k: v for k, v in p.items() if k != "extends"})
        full["id"] = pid
        resolved[pid] = full
        return full

    for pid in raw:
        resolve(pid)
    return resolved


def check(p: dict) -> list[str]:
    """Contrôle les bornes d'un profil résolu. Renvoie la liste des problèmes (vide = bon)."""
    pb = []
    for k, v in p.get("drives", {}).items():
        if not isinstance(v, (int, float)) or not 0 <= v <= 1:
            pb.append(f"{p['id']}: drives.{k} hors de [0,1] ({v})")
    for k in ("patience", "frustration_tolerance", "boredom_tolerance", "risk", "curiosity", "reads_text"):
        v = p.get(k)
        if not isinstance(v, (int, float)) or not 0 <= v <= 1:
            pb.append(f"{p['id']}: {k} hors de [0,1] ({v})")
    s = p.get("skill", {})
    for k in ("aim", "mistake_rate", "learning_rate"):
        if not 0 <= s.get(k, 0) <= 1:
            pb.append(f"{p['id']}: skill.{k} hors de [0,1]")
    if p.get("knowledge") not in KNOWLEDGE:
        pb.append(f"{p['id']}: knowledge doit être {KNOWLEDGE}")
    if p.get("social_role") not in ROLES:
        pb.append(f"{p['id']}: social_role doit être {ROLES}")
    if p.get("social_role") == "saboteur" and not p.get("nuisance_cap_per_hour"):
        pb.append(f"{p['id']}: un saboteur doit avoir nuisance_cap_per_hour (jamais une chasse au crash)")
    m = p.get("session", {}).get("minutes", [1, 1])
    if len(m) != 2 or m[0] > m[1] or m[0] <= 0:
        pb.append(f"{p['id']}: session.minutes = [min, max] en minutes de jeu")
    return pb


def compose(lobby_spec: dict, personas: dict[str, dict], rng: random.Random, prefix: str) -> list[dict]:
    """Un lobby concret : [{bot, persona_id, persona}]. Spécs acceptées :
    {"pure": "casual", "bots": 4}  ou  {"personas": {"moyen": 2, "casual": 1, "saboteur": 1}}."""
    if "pure" in lobby_spec:
        pid = lobby_spec["pure"]
        counts = {pid: int(lobby_spec.get("bots", 4))}
        if personas[pid].get("social_role") in DISRUPTIVE:
            raise ValueError(f"lobby pur interdit pour {pid} (il agit sur les autres : lobbies mélangés seulement)")
    else:
        counts = {k: int(v) for k, v in lobby_spec.get("personas", {}).items()}
    roles: dict[str, int] = {}
    bots = []
    n = 0
    for pid, c in counts.items():
        if pid not in personas:
            raise KeyError(f"profil inconnu dans le lobby : {pid}")
        p = personas[pid]
        if p.get("lobby") == "pure" and len(counts) > 1:
            raise ValueError(f"{pid} ne joue qu'en lobby pur")
        role = p.get("social_role", "none")
        if role in DISRUPTIVE:
            roles[role] = roles.get(role, 0) + c
            if roles[role] > 1:
                raise ValueError(f"au plus un {role} par lobby")
        for _ in range(c):
            n += 1
            bots.append({"bot": f"{prefix}{n:02d}-{pid}", "persona_id": pid, "persona": p})
    rng.shuffle(bots)  # l'ordre d'arrivée ne doit pas suivre le fichier
    return bots


def twin_without_disruptive(bots: list[dict]) -> list[dict] | None:
    """Le jumeau d'un lobby mélangé, sans meneur ni saboteur (même graine) : la mesure de leur effet sur les autres."""
    if not any(b["persona"].get("social_role") in DISRUPTIVE for b in bots):
        return None
    return [b for b in bots if b["persona"].get("social_role") not in DISRUPTIVE]


def lobby_knowledge(bots: list[dict]) -> dict[str, str]:
    """Ce que chaque Einherjar sait des autres : leur profil, comme des amis savent qui est le troll du groupe. Rien d'autre."""
    return {b["bot"]: b["persona_id"] for b in bots}
