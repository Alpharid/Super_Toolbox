"""Les oracles génériques : des invariants vrais pour presque tous les jeux, vérifiés sur le journal brut.

Ils ne demandent rien au jeu de plus que le journal normal (pos, total, progress…). Chaque oracle déclenché devient un
événement `anomaly` (source « oracle ») avec de quoi rejouer. Idée reprise de playtest-agent (veille Heimdall 2026-11-02).

- téléportation : un Einherjar bouge plus vite que `vitesse_max_deplacement` (unités/s de jeu) entre deux positions ;
- hors bornes : position hors de `bornes` ([[xmin, xmax], [ymin, ymax](, [zmin, zmax])]) ;
- ressource négative : un `total` < 0 sur gain/spend/need ;
- valeur non finie : NaN ou infini dans un champ numérique ;
- geste sans effet : `fail` avec reason = no_effect répété sur le même verbe ;
- progression figée : des gestes continuent mais aucun `progress` depuis `progression_figee_min` minutes de jeu ;
- oscillation : un Einherjar fait l'aller-retour entre deux lieux 6 fois de suite sans rien y faire (IA ou design qui tiraille).
"""
from __future__ import annotations

import math
from collections import defaultdict


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _dist(a, b):
    n = min(len(a), len(b))
    return math.sqrt(sum((_num(a[i]) - _num(b[i])) ** 2 for i in range(n)))


def scan(evs: list[dict], seuils: dict) -> list[dict]:
    out: list[dict] = []
    vmax = seuils.get("vitesse_max_deplacement")
    bornes = seuils.get("bornes")
    figee_s = float(seuils.get("progression_figee_min", 0) or 0) * 60
    last_pos: dict[str, tuple[float, list]] = {}
    last_prog: dict[str, float] = {}
    first_t: dict[str, float] = {}
    acts_since: dict[str, int] = defaultdict(int)
    flagged_figee: set[str] = set()
    no_effect = defaultdict(int)
    nan_seen = set()
    trips: dict[str, list] = defaultdict(list)
    osc_flagged: set = set()

    def anomaly(e, what, **kw):
        out.append({"t_game": e.get("t_game"), "t_wall": e.get("t_wall"), "world": e.get("world"), "kind": "anomaly",
                    "what": what, "bot": e.get("bot"), "source": "oracle", **kw})

    for e in evs:
        bot = e.get("bot")
        t = _num(e.get("t_game"))
        for k, v in e.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) and (e.get("kind"), k) not in nan_seen:
                nan_seen.add((e.get("kind"), k))
                anomaly(e, f"valeur non finie : {e.get('kind')}.{k}")
        if not bot or t is None:
            continue
        first_t.setdefault(bot, t)
        pos = e.get("pos")
        if isinstance(pos, (list, tuple)) and len(pos) >= 2 and all(_num(p) is not None for p in pos):
            if bornes:
                for i, (lo, hi) in enumerate(bornes[:len(pos)]):
                    if not lo <= _num(pos[i]) <= hi:
                        anomaly(e, "position hors des bornes du monde", pos=pos)
                        break
            if vmax and bot in last_pos:
                t0, p0 = last_pos[bot]
                dt = t - t0
                d = _dist(pos, p0)
                fast = (d / dt > float(vmax)) if dt > 0 else d > float(vmax) * 0.5  # dt = 0 : saut instantané
                if fast and e.get("kind") not in ("bot_join", "death", "respawn"):
                    anomaly(e, "téléportation (déplacement plus rapide que possible)", pos=pos, de=p0,
                            vitesse=round(d / dt, 1) if dt > 0 else "instantané")
            last_pos[bot] = (t, list(pos))
        if e.get("kind") in ("death", "respawn", "bot_join"):
            last_pos.pop(bot, None)
        tot = _num(e.get("total"))
        if tot is not None and tot < 0 and e.get("kind") in ("gain", "spend", "need"):
            anomaly(e, f"ressource négative : {e.get('resource') or e.get('need')}", total=tot)
        if e.get("kind") == "fail" and str(e.get("reason", "")).lower() in ("no_effect", "sans_effet"):
            no_effect[e.get("verb")] += 1  # compté sur toute la chambre : plusieurs joueurs, même geste inutile
            if no_effect[e.get("verb")] == 3:
                anomaly(e, f"geste sans effet : {e.get('verb')}", verb=e.get("verb"))
        if e.get("kind") == "act":
            tr = trips[bot]
            if e.get("verb") == "aller":
                tr.append(e.get("area"))
                if len(tr) >= 6 and len(set(tr[-6:])) == 2 and all(tr[-i] != tr[-i - 1] for i in range(1, 6)) and bot not in osc_flagged:
                    osc_flagged.add(bot)
                    anomaly(e, "oscillation : allers-retours sans rien faire entre deux lieux", lieux=sorted(set(tr[-6:])),
                            gravite="surveiller", domaine="ia-ou-design")
            else:
                tr.clear()
        if e.get("kind") == "progress":
            last_prog[bot] = t
            acts_since[bot] = 0
        elif e.get("kind") == "act":
            acts_since[bot] += 1
            ref = last_prog.get(bot, first_t[bot])
            if figee_s and t - ref > figee_s and acts_since[bot] > 20 and bot not in flagged_figee:
                flagged_figee.add(bot)
                anomaly(e, "progression figée (des gestes, aucune étape franchie)", depuis_min=round((t - ref) / 60, 1),
                        gravite="surveiller", domaine="progression")
    return out
