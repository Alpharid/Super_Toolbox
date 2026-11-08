"""Le journal d'Hyperbole : un événement JSON par ligne (JSONL), le même pour tous les moteurs.

Chaque ligne a au moins : t_game (secondes de jeu depuis l'ouverture de la chambre), t_wall (secondes réelles),
world (id de la chambre), kind. La plupart ont aussi bot et persona. Le contrat complet : docs/PROTOCOLE.md.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, Iterator

# Les genres d'événements connus et les champs qu'ils exigent (en plus de t_game / t_wall / world / kind).
# Un genre inconnu n'est pas une erreur (un jeu peut en ajouter) : il est compté et signalé par `validate`.
KINDS: dict[str, tuple[str, ...]] = {
    # séance
    "chamber_start": ("seed", "mode"),
    "chamber_end": ("reason",),
    "bot_join": ("bot", "persona"),
    "bot_leave": ("bot", "reason"),
    # ce que fait un Einherjar
    "intent": ("bot", "option"),
    "act": ("bot", "verb"),
    "fail": ("bot", "verb"),
    "stuck": ("bot",),
    "learn": ("bot", "cue"),
    "progress": ("bot", "milestone"),
    "gain": ("bot", "resource", "amount"),
    "spend": ("bot", "resource", "amount"),
    "encounter": ("bot", "threat", "outcome"),
    "death": ("bot", "cause"),
    "run_end": ("bot", "duration"),
    "moment": ("bot", "what"),
    "bored": ("bot",),
    "afk": ("bot", "duration"),  # absence voulue (le joueur va se faire un thé) : retirée du temps actif, pas de l'ennui
    "frustrated": ("bot",),
    "social": ("bot", "with", "what"),
    "say": ("bot", "text"),
    "exploit": ("bot", "what"),
    "refusal": ("bot", "what"),
    "need": ("bot", "need", "value"),
    # ce que voit le moteur
    "error": ("text",),
    "anomaly": ("what",),
    "perf": (),
    "crash": ("reason",),
    "hang": (),
}

BASE_FIELDS = ("t_game", "t_wall", "world", "kind")


class Journal:
    """Écrit le journal d'une chambre. Une seule instance par fichier (pas d'écriture concurrente)."""

    def __init__(self, path: str | os.PathLike, world: str, clock=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.world = world
        self._t0 = time.perf_counter()
        self._clock = clock  # fonction -> t_game ; sinon t_game = t_wall
        self._f = open(self.path, "a", encoding="utf-8", newline="\n")

    def t_wall(self) -> float:
        return time.perf_counter() - self._t0

    def write(self, kind: str, **data) -> dict:
        tw = self.t_wall()
        tg = self._clock() if self._clock else tw
        ev = {"t_game": round(tg, 3), "t_wall": round(tw, 3), "world": self.world, "kind": kind}
        ev.update({k: v for k, v in data.items() if v is not None})
        self._f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")
        return ev

    def flush(self):
        self._f.flush()

    def close(self):
        if not self._f.closed:
            self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read(path: str | os.PathLike) -> Iterator[dict]:
    """Lit un journal ; une ligne illisible devient un événement `anomaly` (journal tronqué par un crash, par ex.)."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                yield {"t_game": None, "t_wall": None, "world": Path(path).stem, "kind": "anomaly",
                       "what": "ligne de journal illisible", "line": n, "source": "popo"}
                continue
            if isinstance(ev, dict):
                yield ev


def read_many(paths: Iterable[str | os.PathLike]) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        out.extend(read(p))
    return out


def validate(events: Iterable[dict]) -> dict:
    """Contrôle le contrat : champs de base, champs exigés par genre, genres inconnus. Renvoie un bilan."""
    bilan = {"events": 0, "kinds": {}, "missing": {}, "unknown_kinds": {}, "errors": []}
    for i, ev in enumerate(events):
        bilan["events"] += 1
        kind = ev.get("kind")
        bilan["kinds"][kind] = bilan["kinds"].get(kind, 0) + 1
        for f in BASE_FIELDS:
            if f not in ev:
                bilan["missing"][f] = bilan["missing"].get(f, 0) + 1
        if kind not in KINDS:
            bilan["unknown_kinds"][kind] = bilan["unknown_kinds"].get(kind, 0) + 1
            continue
        for f in KINDS[kind]:
            if f not in ev:
                key = f"{kind}.{f}"
                bilan["missing"][key] = bilan["missing"].get(key, 0) + 1
                if len(bilan["errors"]) < 20:
                    bilan["errors"].append(f"événement {i} ({kind}) sans « {f} »")
    bilan["ok"] = not bilan["missing"]
    return bilan
