"""L'analyse d'un run : des journaux aux mesures et aux constats.

Tout ce qui sort d'ici est MESURÉ dans les journaux (aucune note inventée). Chaque constat porte ses preuves
(mesure, chambre, graine, instant) pour qu'on puisse rejouer la même graine après un correctif.
"""
from __future__ import annotations

import json
import math
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

from . import journal as J
from . import oracles

LEAK_FIELDS = ("mem_mb", "mem_static_mb", "nodes", "objects", "orphans", "resources", "entities", "handles")
WIN = {"win", "won", "victoire", "gagne", "kill"}
LOSE = {"lose", "lost", "defaite", "perdu", "death", "ko"}
QUIT_REASONS = {"bored", "frustrated", "quit", "ennui", "frustration", "abandon"}


# ------------------------------------------------------------------ chargement
def load_run(run_dir: str | Path) -> dict:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    worlds: dict[str, list[dict]] = {}
    for d in sorted((run_dir / "chambres").glob("*")):
        evs: list[dict] = []
        for f in sorted(d.glob("*.jsonl")):  # journal.jsonl (le jeu), popo.jsonl (l'extérieur), tete*.jsonl (cerveaux déportés)
            evs.extend(J.read(f))
        for e in evs:
            e.setdefault("world", d.name)
        worlds[d.name] = evs
    return {"dir": run_dir, "manifest": manifest, "worlds": worlds}


def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _q(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _med(values):
    v = [x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return st.median(v) if v else None


def _r(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, n)


def _entropy(counter: Counter, universe: int) -> float:
    total = sum(counter.values())
    if total == 0 or universe <= 1:
        return 0.0
    h = -sum((c / total) * math.log(c / total) for c in counter.values() if c)
    return h / math.log(universe)


def _norm_error(text: str) -> str:
    t = re.sub(r"0x[0-9a-fA-F]+", "#", text)
    t = re.sub(r"[A-Za-z]:[\\/][^\s:]+|res://[^\s:]+|/[\w./-]{6,}", "<chemin>", t)
    t = re.sub(r"\d+(\.\d+)?", "#", t)
    t = re.sub(r"'[^']*'|\"[^\"]*\"", "'…'", t)
    return t.strip()[:220]


def _linreg(xs: list[float], ys: list[float]):
    n = len(xs)
    if n < 4:
        return None, None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx, sxy / math.sqrt(sxx * syy)


def kaplan_meier(durations: list[tuple[float, bool]]) -> list[tuple[float, float]]:
    """Courbe de survie (rétention) : [(t, part encore là)]. durations = [(durée, l'événement a-t-il eu lieu)]."""
    if not durations:
        return []
    pts = [(0.0, 1.0)]
    s = 1.0
    at_risk = len(durations)
    for t in sorted({d for d, _ in durations}):
        events = sum(1 for d, e in durations if d == t and e)
        if events:
            s *= (1 - events / at_risk)
            pts.append((t, s))
        at_risk -= sum(1 for d, _ in durations if d == t)
    return pts


def _km_at(curve, t):
    s = 1.0
    for x, y in curve:
        if x <= t:
            s = y
    return s


def _pos_cell(pos, size: float):
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return None
    a, b = (pos[0], pos[2]) if len(pos) >= 3 else (pos[0], pos[1])  # 3D : plan x/z (y vers le haut, Godot)
    return (math.floor(_num(a) / size), math.floor(_num(b) / size))


# ------------------------------------------------------------------ par bot
def bot_metrics(evs: list[dict], t_end: float) -> dict:
    b: dict = {"acts": 0, "verbs": Counter(), "fails": Counter(), "moments": [], "bored_n": 0, "bored_s": 0.0,
               "frustrated": 0, "enc_win": 0, "enc_lose": 0, "enc_other": 0, "enc_by_threat": defaultdict(lambda: [0, 0]),
               "deaths": Counter(), "death_events": [], "milestones": {}, "gains": Counter(), "spends": Counter(),
               "gain_sources": Counter(), "learned": {}, "stuck": [], "leave": None, "join_t": None, "planned_s": None,
               "novel": [], "socials": Counter(), "says": 0, "exploits": [], "refusals": Counter(), "runs": [],
               "intents": Counter(), "persona": None, "afk_s": 0.0}
    seen = set()
    for e in evs:
        k = e.get("kind")
        t = _num(e.get("t_game"), None) if e.get("t_game") is not None else None
        if k == "bot_join":
            b["join_t"] = t
            b["persona"] = e.get("persona")
            b["planned_s"] = _num(e.get("session_planned_s"), None) if e.get("session_planned_s") else None
        elif k == "bot_leave":
            b["leave"] = {"t": t, "reason": str(e.get("reason", ""))}
        elif k == "act":
            b["acts"] += 1
            verb = str(e.get("verb"))
            b["verbs"][verb] += 1
            key = (verb, str(e.get("area", "")))
            if key not in seen:
                seen.add(key)
                b["novel"].append(t)
        elif k == "intent":
            b["intents"][str(e.get("option"))] += 1
        elif k == "fail":
            b["fails"][str(e.get("verb"))] += 1
        elif k == "moment":
            b["moments"].append({"t": t, "what": e.get("what"), "intensity": e.get("intensity")})
        elif k == "bored":
            b["bored_n"] += 1
            b["bored_s"] += _num(e.get("duration"), 10.0)
        elif k == "frustrated":
            b["frustrated"] += 1
        elif k == "encounter":
            o = str(e.get("outcome", "")).lower()
            th = str(e.get("threat"))
            if o in WIN:
                b["enc_win"] += 1
                b["enc_by_threat"][th][0] += 1
            elif o in LOSE:
                b["enc_lose"] += 1
                b["enc_by_threat"][th][1] += 1
            else:
                b["enc_other"] += 1
        elif k == "death":
            b["deaths"][str(e.get("cause"))] += 1
            b["death_events"].append({"t": t, "cause": e.get("cause"), "pos": e.get("pos"), "doing": e.get("doing"),
                                      "blame": e.get("blame")})
        elif k == "progress":
            m = str(e.get("milestone"))
            if m not in b["milestones"]:
                b["milestones"][m] = t
        elif k == "gain":
            b["gains"][str(e.get("resource"))] += _num(e.get("amount"))
            b["gain_sources"][(str(e.get("resource")), str(e.get("source", "?")))] += _num(e.get("amount"))
        elif k == "spend":
            b["spends"][str(e.get("resource"))] += _num(e.get("amount"))
        elif k == "learn":
            b["learned"][str(e.get("cue"))] = _num(e.get("after"), None) if e.get("after") is not None else t
        elif k == "stuck":
            b["stuck"].append({"t": t, "pos": e.get("pos"), "intent": e.get("intent"), "area": e.get("area"),
                               "duration": e.get("duration")})
        elif k == "social":
            b["socials"][str(e.get("what"))] += 1
        elif k == "say":
            b["says"] += 1
        elif k == "exploit":
            b["exploits"].append({k2: v for k2, v in e.items() if k2 not in ("world",)})
        elif k == "refusal":
            b["refusals"][str(e.get("what"))] += 1
        elif k == "run_end":
            b["runs"].append({"duration": _num(e.get("duration")), "cause": e.get("cause"), "score": e.get("score")})
        elif k == "afk":
            b["afk_s"] += _num(e.get("duration"))
    start = b["join_t"] if b["join_t"] is not None else 0.0
    end = b["leave"]["t"] if b["leave"] and b["leave"]["t"] is not None else t_end
    b["play_s"] = max(0.0, (end or 0) - start)
    b["active_s"] = max(1e-6, b["play_s"] - b["afk_s"])
    return b


# ------------------------------------------------------------------ run
def analyse(run: dict) -> dict:
    man = run["manifest"]
    S = man["mission"].get("seuils", {})
    chambers_meta = {c["id"]: c for c in man.get("chambres", [])}
    results = {r["world"]: r for r in man.get("resultats", []) if "world" in r}
    out: dict = {"run": man["run"], "version": man.get("version"), "mission": man["mission"].get("nom"),
                 "objectifs": man["mission"].get("objectif"), "chambres": {}, "bots": {}, "constats": []}
    verbs_universe: set = set()
    all_bots: dict[str, dict] = {}
    perf_by_world: dict[str, list[dict]] = {}
    errors = defaultdict(lambda: {"n": 0, "worlds": set(), "first": None, "level": "error", "lanes": set()})
    anomalies = defaultdict(lambda: {"n": 0, "worlds": set(), "first": None})
    blame = Counter()

    cover = defaultdict(lambda: defaultdict(set))  # profil -> cellule -> bots
    mech = defaultdict(lambda: defaultdict(lambda: {"first_ok": [], "early": [0, 0], "late": [0, 0]}))
    for world, evs in run["worlds"].items():
        evs = evs + oracles.scan(sorted([e for e in evs if e.get("source") != "popo"],
                                        key=lambda e: _num(e.get("t_game"), 0)), S)
        meta = chambers_meta.get(world, {})
        lane = meta.get("lane", "chambre")
        tg = [_num(e["t_game"]) for e in evs if e.get("t_game") is not None]
        tw = [_num(e["t_wall"]) for e in evs if e.get("t_wall") is not None and e.get("source") != "popo"]
        t_end = max(tg) if tg else 0.0
        wall = max(tw) if tw else 0.0
        speed = (t_end / wall) if wall > 0 else None
        by_bot = defaultdict(list)
        for e in evs:
            k = e.get("kind")
            if e.get("bot"):
                by_bot[e["bot"]].append(e)
            if k == "act":
                verbs_universe.add(str(e.get("verb")))
            elif k == "perf":
                perf_by_world.setdefault(world, []).append(e)
            elif k == "error":
                key = _norm_error(str(e.get("text", "")))
                g = errors[key]
                g["n"] += 1
                g["worlds"].add(world)
                g["lanes"].add(lane)
                g["level"] = e.get("level", g["level"])
                if g["first"] is None:
                    g["first"] = {"world": world, "t_game": e.get("t_game"), "text": str(e.get("text"))[:300],
                                  "seed": meta.get("seed")}
            elif k in ("anomaly", "hang", "crash"):
                key = k if k != "anomaly" else str(e.get("what"))
                g = anomalies[(k, key)]
                g["n"] += 1
                g["worlds"].add(world)
                if g["first"] is None:
                    g["first"] = {"world": world, "t_game": e.get("t_game"), "seed": meta.get("seed"),
                                  "detail": {kk: vv for kk, vv in e.items() if kk not in ("world", "kind")}}
            if e.get("blame"):
                blame[str(e["blame"])] += 1
        cm = {"lane": lane, "seed": meta.get("seed"), "variant": meta.get("variant"), "twin_of": meta.get("twin_of"),
              "cycle": meta.get("cycle"), "lobby_index": meta.get("lobby_index"), "t_game_s": round(t_end, 1),
              "wall_s": round(wall, 1), "speed": _r(speed, 1), "bots": [], "crashed": results.get(world, {}).get("crashed"),
              "reason": results.get(world, {}).get("reason")}
        for bot, bevs in by_bot.items():
            bm = bot_metrics(bevs, t_end)
            _cover_and_mechanics(bevs, bm, cover, mech, float(S.get("cell_size", 4.0)), bot)
            bm["world"] = world
            bm["lane"] = lane
            bm["variant"] = meta.get("variant")
            bm["twin_of"] = meta.get("twin_of")
            bm["seed"] = meta.get("seed")
            uid = f"{world}/{bot}"
            all_bots[uid] = bm
            cm["bots"].append(bot)
        cm["bot_hours"] = round(sum(all_bots[f"{world}/{b}"]["play_s"] for b in cm["bots"]) / 3600, 3)
        out["chambres"][world] = cm

    U = max(2, len(verbs_universe))
    # ---- mesures par bot
    for uid, b in all_bots.items():
        h = b["active_s"] / 3600
        enc = b["enc_win"] + b["enc_lose"]
        fails = sum(b["fails"].values())
        planned = b["planned_s"]
        left = b["leave"]
        early = bool(left and left["reason"].lower() in QUIT_REASONS and planned and b["play_s"] < 0.5 * planned)
        nov = [t for t in b["novel"] if t is not None]
        last_new = (max(nov) - (b["join_t"] or 0)) if nov else None
        b["m"] = {
            "persona": b["persona"], "play_min": _r(b["play_s"] / 60, 1),
            "moments_h": _r(len(b["moments"]) / h if h else 0), "downtime": _r(min(1.0, b["bored_s"] / b["active_s"])),
            "frustration_h": _r(b["frustrated"] / h if h else 0), "variety": _r(_entropy(b["verbs"], U)),
            "fail_rate": _r(fails / b["acts"] if b["acts"] else 0), "success": _r(b["enc_win"] / enc) if enc else None,
            "deaths_h": _r(sum(b["deaths"].values()) / h if h else 0), "early_quit": early,
            "leave": left["reason"] if left else "fin de chambre", "last_new_min": _r(last_new / 60, 1) if last_new else None,
            "gains_h": {r: _r(v / h if h else 0) for r, v in b["gains"].items()},
            "spends_h": {r: _r(v / h if h else 0) for r, v in b["spends"].items()},
            "says": b["says"],
        }
    out["bots"] = {uid: {**b["m"], "world": b["world"], "lane": b["lane"], "variant": b["variant"]} for uid, b in all_bots.items()}

    # ---- par profil
    per_p = defaultdict(list)
    for uid, b in all_bots.items():
        per_p[b["persona"] or "?"].append(b)
    personas_out = {}
    for pid, bs in per_p.items():
        ms = [b["m"] for b in bs]
        retention = kaplan_meier([(b["play_s"] / 60, bool(b["leave"] and b["leave"]["reason"].lower() in QUIT_REASONS)) for b in bs])
        runs = [r["duration"] / 60 for b in bs for r in b["runs"]]
        personas_out[pid] = {
            "bots": len(bs), "bot_hours": _r(sum(b["play_s"] for b in bs) / 3600, 2),
            "moments_h": _r(_med([m["moments_h"] for m in ms])), "downtime": _r(_med([m["downtime"] for m in ms])),
            "frustration_h": _r(_med([m["frustration_h"] for m in ms])), "variety": _r(_med([m["variety"] for m in ms])),
            "fail_rate": _r(_med([m["fail_rate"] for m in ms])),
            "success": _r(_med([m["success"] for m in ms if m["success"] is not None])),
            "deaths_h": _r(_med([m["deaths_h"] for m in ms])), "early_quit": _r(sum(m["early_quit"] for m in ms) / len(ms)),
            "play_min": _r(_med([m["play_min"] for m in ms]), 1), "last_new_min": _r(_med([m["last_new_min"] for m in ms]), 1),
            "leave_reasons": dict(Counter(m["leave"] for m in ms)),
            "retention": [(_r(t, 1), _r(s, 3)) for t, s in retention],
            "run_median_min": _r(_med(runs), 1), "runs": len(runs),
            "death_causes": dict(sum((b["deaths"] for b in bs), Counter()).most_common(8)),
        }
    out["personas"] = personas_out

    # ---- étapes (progression) par profil : temps médian depuis l'arrivée, part qui l'atteint
    declared = []  # étapes annoncées par le jeu (chamber_start.milestones) : on voit aussi celles que personne n'atteint
    for evs in run["worlds"].values():
        for e in evs:
            if e.get("kind") == "chamber_start" and isinstance(e.get("milestones"), list):
                declared += [m for m in e["milestones"] if m not in declared]
    milestones = defaultdict(lambda: defaultdict(list))
    for b in all_bots.values():
        for m, t in b["milestones"].items():
            if t is not None:
                milestones[m][b["persona"]].append((t - (b["join_t"] or 0)) / 60)
    ms_out = {}
    for i, m in enumerate(declared + [x for x in milestones if x not in declared]):
        by = milestones.get(m, {})
        first_t = min((min(v) for v in by.values()), default=None)
        row = {}
        for p in per_p:
            v = by.get(p, [])
            row[p] = {"median_min": _r(_med(v), 1), "min_min": _r(min(v), 1) if v else None,
                      "atteint": _r(len(v) / max(1, len(per_p[p])))}
        ms_out[m] = {"order": i if declared else (first_t or 0), "jamais": not by, "par_profil": row}
    out["etapes"] = dict(sorted(ms_out.items(), key=lambda kv: kv[1]["order"]))

    # ---- apprentissage
    learn = defaultdict(lambda: defaultdict(list))
    for b in all_bots.values():
        for cue, after in b["learned"].items():
            if after is not None:
                learn[cue][b["persona"]].append(after / 60)
    out["apprentissage"] = {cue: {p: {"median_min": _r(_med(v), 1), "part": _r(len(v) / max(1, len(per_p.get(p, []))))}
                                  for p, v in by.items()} for cue, by in learn.items()}

    # ---- défi par menace
    threats = defaultdict(lambda: [0, 0])
    for b in all_bots.values():
        for th, (w, l) in b["enc_by_threat"].items():
            threats[th][0] += w
            threats[th][1] += l
    out["menaces"] = {th: {"victoires": w, "defaites": l, "succes": _r(w / (w + l)) if w + l else None}
                      for th, (w, l) in sorted(threats.items(), key=lambda kv: -sum(kv[1]))}

    # ---- causes de mort
    causes = sum((b["deaths"] for b in all_bots.values()), Counter())
    out["morts"] = dict(causes.most_common(15))

    # ---- économie
    econ = defaultdict(lambda: {"gain": 0.0, "spend": 0.0, "sources": Counter()})
    total_h = sum(b["active_s"] for b in all_bots.values()) / 3600 or 1
    for b in all_bots.values():
        for r, v in b["gains"].items():
            econ[r]["gain"] += v
        for r, v in b["spends"].items():
            econ[r]["spend"] += v
        for (r, src), v in b["gain_sources"].items():
            econ[r]["sources"][src] += v
    out["economie"] = {r: {"gain_h": _r(e["gain"] / total_h), "spend_h": _r(e["spend"] / total_h),
                           "net_h": _r((e["gain"] - e["spend"]) / total_h), "sources": dict(e["sources"].most_common(6))}
                       for r, e in econ.items()}

    # ---- blocages : carte
    cell = float(S.get("cell_size", 4.0))
    cells = defaultdict(lambda: {"n": 0, "bots": set(), "worlds": set(), "intents": Counter(), "areas": Counter(), "first": None})
    for uid, b in all_bots.items():
        for s in b["stuck"]:
            c = _pos_cell(s["pos"], cell)
            key = c if c is not None else ("zone", str(s.get("area") or "?"))
            g = cells[key]
            g["n"] += 1
            g["bots"].add(uid)
            g["worlds"].add(b["world"])
            g["intents"][str(s.get("intent"))] += 1
            g["areas"][str(s.get("area"))] += 1
            if g["first"] is None:
                g["first"] = {"world": b["world"], "seed": b["seed"], "t_game": s["t"], "pos": s["pos"]}
    # cellules voisines (8-connexité) = un même point de blocage (une position bruitée chevauche deux cellules)
    keys = [k for k in cells if isinstance(k, tuple) and len(k) == 2 and k[0] != "zone"]
    parent = {k: k for k in keys}

    def root(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    for k in keys:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (k[0] + dx, k[1] + dy)
                if n in parent:
                    parent[root(n)] = root(k)
    merged = {}
    for k in keys:
        r = root(k)
        if r not in merged:
            merged[r] = cells[r] if r == k else {"n": 0, "bots": set(), "worlds": set(), "intents": Counter(), "areas": Counter(), "first": None}
        if r != k or merged[r] is not cells[k]:
            g, src = merged[r], cells[k]
            if g is not src:
                g["n"] += src["n"]
                g["bots"] |= src["bots"]
                g["worlds"] |= src["worlds"]
                g["intents"] += src["intents"]
                g["areas"] += src["areas"]
                g["first"] = g["first"] or src["first"]
    cells = {**{k: v for k, v in cells.items() if k not in parent}, **merged}
    out["blocages"] = sorted([{"cellule": list(k) if isinstance(k, tuple) else k, "n": g["n"], "bots": len(g["bots"]),
                               "chambres": len(g["worlds"]), "intentions": dict(g["intents"].most_common(3)),
                               "zones": dict(g["areas"].most_common(2)), "premier": g["first"]}
                              for k, g in cells.items()], key=lambda x: -x["bots"])

    # ---- erreurs, anomalies
    out["erreurs"] = sorted([{"message": k, "n": g["n"], "chambres": len(g["worlds"]), "niveau": g["level"],
                              "voies": sorted(g["lanes"]), "premier": g["first"]} for k, g in errors.items()],
                            key=lambda x: (x["niveau"] != "error", -x["n"]))
    out["anomalies"] = sorted([{"genre": k[0], "quoi": k[1], "n": g["n"], "chambres": len(g["worlds"]), "premier": g["first"]}
                               for k, g in anomalies.items()], key=lambda x: -x["n"])
    out["exploits"] = [x | {"world": b["world"], "seed": b["seed"]} for b in all_bots.values() for x in b["exploits"]]

    # ---- perf : fuites (croissance par heure de jeu)
    leaks = []
    perf_out = {}
    for world, rows in perf_by_world.items():
        rows = [r for r in rows if r.get("t_game") is not None]
        if len(rows) < 4:
            continue
        xs = [_num(r["t_game"]) / 3600 for r in rows]
        summary = {}
        for f in sorted({k for r in rows for k, v in r.items() if isinstance(v, (int, float)) and k not in ("t_game", "t_wall")}):
            ys = [_num(r.get(f)) for r in rows if f in r]
            if len(ys) != len(xs):
                continue
            summary[f] = {"min": _r(min(ys)), "max": _r(max(ys)), "median": _r(_med(ys))}
            if f in LEAK_FIELDS or f.startswith("mem"):
                slope, corr = _linreg(xs, ys)
                mean = sum(ys) / len(ys)
                if slope and mean and corr is not None:
                    pct = slope / abs(mean) * 100
                    summary[f]["pente_pct_h"] = _r(pct, 1)
                    if pct > S.get("leak_per_hour_pct", 5.0) and corr > 0.7 and (xs[-1] - xs[0]) > 0.05:
                        leaks.append({"world": world, "mesure": f, "pct_h": _r(pct, 1), "corr": _r(corr),
                                      "de": _r(ys[0]), "a": _r(ys[-1]), "heures_jeu": _r(xs[-1] - xs[0])})
        if "fps" in summary:
            fps = [_num(r.get("fps")) for r in rows if "fps" in r]
            summary["fps"]["p5"] = _r(_q(fps, 0.05))
        perf_out[world] = summary
    out["perf"] = perf_out
    out["fuites"] = leaks

    # ---- jumeaux : l'effet d'un saboteur / meneur sur les autres
    twins = []
    for world, cm in out["chambres"].items():
        if not cm.get("twin_of"):
            continue
        orig = cm["twin_of"]
        def others(w):
            return [all_bots[f"{w}/{b}"]["m"] for b in out["chambres"].get(w, {}).get("bots", [])
                    if (all_bots[f"{w}/{b}"]["persona"] not in ("saboteur", "leader"))]
        a, z = others(orig), others(world)
        if not a or not z:
            continue
        row = {"avec": orig, "sans": world}
        for k in ("frustration_h", "downtime", "moments_h", "deaths_h", "success"):
            va, vz = _med([m[k] for m in a if m[k] is not None]), _med([m[k] for m in z if m[k] is not None])
            row[k] = {"avec": _r(va), "sans": _r(vz)}
        disruptive = [all_bots[f"{orig}/{b}"]["persona"] for b in out["chambres"][orig]["bots"]
                      if all_bots[f"{orig}/{b}"]["persona"] in ("saboteur", "leader")]
        row["role"] = disruptive[0] if disruptive else "?"
        twins.append(row)
    out["jumeaux"] = twins
    out["blame"] = dict(blame.most_common(10))

    # ---- variantes (A/B) et voies (accélérée / x1)
    def group_stats(key):
        g = defaultdict(list)
        for b in all_bots.values():
            g[b[key]].append(b["m"])
        res = {}
        for k, ms in g.items():
            res[str(k)] = {f: _r(_med([m[f] for m in ms if m[f] is not None])) for f in
                           ("success", "deaths_h", "frustration_h", "downtime", "moments_h", "variety", "fail_rate")}
            res[str(k)]["bots"] = len(ms)
        return res
    out["variantes"] = group_stats("variant") if any(b["variant"] for b in all_bots.values()) else {}
    lanes = {b["lane"] for b in all_bots.values()}
    out["voies"] = group_stats("lane") if len(lanes) > 1 else {}

    # ---- vitesse et volume
    speeds = [c["speed"] for c in out["chambres"].values() if c["speed"]]
    wall_h = sum(c["wall_s"] for c in out["chambres"].values()) / 3600
    bot_h = sum(c["bot_hours"] for c in out["chambres"].values())
    par = man["mission"].get("chambres", 1)
    out["volume"] = {"chambres": len(out["chambres"]), "einherjar": len(all_bots), "heures_bot": _r(bot_h, 2),
                     "heures_chambre_reelles": _r(wall_h, 2), "vitesse_mediane": _r(_med(speeds), 1),
                     "vitesse_min": _r(min(speeds), 1) if speeds else None,
                     "heures_bot_par_heure_pc": _r(bot_h / (wall_h / max(1, par)) if wall_h else 0, 1)}

    # ---- couverture : cellules visitées par profil (les zones jamais vues = contenu perdu ou inaccessible)
    allcells = set().union(*[set(c) for c in cover.values()]) if cover else set()
    out["couverture"] = {"cellules": len(allcells), "taille": float(S.get("cell_size", 4.0)),
                         "par_profil": {p: len(c) for p, c in cover.items()},
                         "carte": {f"{x},{y}": len({b for c in cover.values() for b in c.get((x, y), ())}) for x, y in allcells}}
    # ---- mécaniques : premier succès et progrès entre la 1re et la 2e moitié des essais
    out["mecaniques"] = {v: {p: {"premier_succes_min": _r(_med(d["first_ok"]), 1),
                                 "rate_debut": _r(d["early"][1] / d["early"][0]) if d["early"][0] else None,
                                 "rate_fin": _r(d["late"][1] / d["late"][0]) if d["late"][0] else None}
                             for p, d in by.items()} for v, by in mech.items()}
    out["constats"] = findings(out, S)
    return out


def _cover_and_mechanics(bevs, bm, cover, mech, size, bot):
    pid = bm["persona"] or "?"
    join = bm["join_t"] or 0
    tries = defaultdict(list)  # verbe -> [(t, raté ?)]
    for e in bevs:
        c = _pos_cell(e.get("pos"), size)
        if c is not None:
            cover[pid][c].add(bot + "@" + str(e.get("world")))
        k = e.get("kind")
        if k == "act" and e.get("verb") is not None:
            tries[str(e["verb"])].append([_num(e.get("t_game"), 0), False])
        elif k == "fail" and e.get("verb") is not None:  # un `fail` qualifie le dernier `act` du même verbe
            lst = tries[str(e["verb"])]
            if lst and not lst[-1][1]:
                lst[-1][1] = True
            else:
                lst.append([_num(e.get("t_game"), 0), True])
    for verb, ts in tries.items():
        d = mech[verb][pid]
        ok = [t for t, failed in ts if not failed]
        if ok:
            d["first_ok"].append((min(ok) - join) / 60)
        half = len(ts) // 2
        for i, (t, failed) in enumerate(ts):
            part = d["early"] if i < half else d["late"]
            part[0] += 1
            part[1] += 1 if failed else 0


# ------------------------------------------------------------------ constats
def findings(a: dict, S: dict) -> list[dict]:
    """Les constats, du plus grave au moins grave. Gravité : probleme / surveiller / info."""
    F = []

    def add(sev, dom, titre, preuve, ou=None):
        F.append({"gravite": sev, "domaine": dom, "titre": titre, "preuve": preuve, "rejouer": ou})

    for c in [x for x in a["anomalies"] if x["genre"] == "crash"]:
        add("probleme", "bugs", f"Crash d'une chambre ({c['n']} fois)", f"{c['quoi']} — {c['premier']['detail'].get('reason', '')}", c["premier"])
    for c in [x for x in a["anomalies"] if x["genre"] == "hang"]:
        add("probleme", "bugs", "Chambre figée (journal immobile)", f"{c['n']} fois, {c['chambres']} chambre(s)", c["premier"])
    for e in a["erreurs"]:
        if e["niveau"] == "error":
            only = " — vue seulement en chambre accélérée : revérifier à x1" if e["voies"] == ["chambre"] and a["voies"] else ""
            add("probleme", "bugs", f"Erreur moteur ×{e['n']} : {e['message'][:90]}", f"{e['chambres']} chambre(s){only}", e["premier"])
    for x in a["anomalies"]:
        if x["genre"] == "anomaly":
            d = (x["premier"] or {}).get("detail", {})
            add(d.get("gravite", "probleme"), d.get("domaine", "bugs"), f"Anomalie ×{x['n']} : {x['quoi']}",
                f"{x['chambres']} chambre(s), {d.get('bots', '')}".rstrip(", "), x["premier"])
    for b in a["blocages"]:
        if b["bots"] >= S.get("stuck_cluster_min", 3):
            add("probleme", "bugs", f"Point de blocage cellule {b['cellule']} ({b['bots']} Einherjar, {b['n']} fois)",
                f"intentions : {b['intentions']} ; zones : {b['zones']}", b["premier"])
        elif b["n"] >= 2:
            add("surveiller", "bugs", f"Blocage répété cellule {b['cellule']} ({b['n']} fois)", f"intentions : {b['intentions']}", b["premier"])
    groups = {}
    for x in a["exploits"]:
        g = groups.setdefault(str(x.get("what")), {"first": x, "bots": set(), "n": 0})
        g["bots"].add(str(x.get("bot")))
        g["n"] += 1
    for what, g in groups.items():
        x = g["first"]
        add("probleme", "exploit", f"Faille : {what} (trouvée par {len(g['bots'])} Einherjar)",
            "étapes : " + "; ".join(map(str, x.get("steps", []) or [])) + f" — 1er : {x.get('bot')}",
            {"world": x["world"], "seed": x["seed"], "t_game": x.get("t_game")})
    for l in a["fuites"]:
        add("probleme", "perf", f"Fuite probable : {l['mesure']} +{l['pct_h']} %/h de jeu",
            f"{l['de']} → {l['a']} en {l['heures_jeu']} h de jeu (corrélation {l['corr']})", {"world": l["world"]})

    # économie : gains aberrants (hors fouineur, il a ses propres signalements)
    per_res = defaultdict(list)
    for uid, b in a["bots"].items():
        if b["persona"] == "fouineur":
            continue
        for r, v in (b.get("gains_h") or {}).items():
            per_res[r].append((v, uid))
    for r, vals in per_res.items():
        vs = [v for v, _ in vals]
        if len(vs) < 5:
            continue
        q1, q3 = _q(vs, .25), _q(vs, .75)
        lim = q3 + S.get("exploit_iqr", 3.0) * max(q3 - q1, 1e-9)
        for v, uid in vals:
            if v > lim and v > 0:
                add("surveiller", "exploit", f"Gain aberrant de {r} : {uid} à {v}/h", f"limite Q3+{S.get('exploit_iqr')}·IQR = {_r(lim)}/h",
                    {"world": a["bots"][uid]["world"]})

    # par profil : fun, défi, jouabilité
    lo, hi = S.get("success_band", [0.55, 0.85])
    for pid, p in a["personas"].items():
        if p["success"] is not None:
            if p["success"] < lo:
                add("probleme" if p["success"] < lo - 0.15 else "surveiller", "defi", f"Trop dur pour {pid} : {int(p['success'] * 100)} % de rencontres gagnées",
                    f"bande visée {int(lo * 100)}–{int(hi * 100)} % ; morts/h {p['deaths_h']} ; causes {p['death_causes']}")
            elif p["success"] > hi:
                add("surveiller", "defi", f"Trop facile pour {pid} : {int(p['success'] * 100)} % de rencontres gagnées",
                    f"bande visée {int(lo * 100)}–{int(hi * 100)} %")
        if p["early_quit"] and p["early_quit"] > S.get("early_quit_max", 0.3):
            add("probleme", "jouabilite", f"{pid} abandonne tôt : {int(p['early_quit'] * 100)} % des séances avant la moitié prévue",
                f"raisons : {p['leave_reasons']}")
        if p["downtime"] is not None and p["downtime"] > S.get("downtime_max", 0.25):
            add("surveiller", "fun", f"{pid} s'ennuie {int(p['downtime'] * 100)} % du temps", f"variété {p['variety']}, moments/h {p['moments_h']}")
        if p["frustration_h"] is not None and p["frustration_h"] > S.get("frustration_per_hour_max", 6):
            add("surveiller", "fun", f"{pid} frustré {p['frustration_h']} fois/h", f"gestes ratés {p['fail_rate']}, morts/h {p['deaths_h']}")
        if p["variety"] is not None and p["variety"] < S.get("variety_min", 0.45):
            add("surveiller", "fun", f"{pid} répète toujours les mêmes gestes (variété {p['variety']})", "peu d'options intéressantes pour ce profil")
        if p["fail_rate"] is not None and p["fail_rate"] > S.get("fail_rate_max", 0.3):
            add("surveiller", "ergonomie", f"{pid} rate {int(p['fail_rate'] * 100)} % de ses gestes", "contrôles, lisibilité ou bug d'un verbe")
    st_ = a["personas"].get("streamer")
    if st_ and st_["moments_h"] is not None and st_["moments_h"] < S.get("moments_per_hour_min", 4):
        add("surveiller", "fun", f"Le streamer n'a que {st_['moments_h']} moments à montrer par heure", f"seuil {S.get('moments_per_hour_min')}")
    for pid, p in a["personas"].items():
        if p["last_new_min"] is not None and p["play_min"] and p["play_min"] > 2 * p["last_new_min"] and p["play_min"] > 20:
            add("info", "contenu", f"{pid} n'a plus rien découvert de neuf après {p['last_new_min']} min (séance de {p['play_min']} min)",
                "le contenu s'épuise pour ce profil (geste+lieu nouveau)")

    # équilibre : cause de mort dominante, écarts de progression
    total = sum(a["morts"].values())
    if total >= 10:
        top, n = next(iter(a["morts"].items()))
        if n / total > S.get("cause_dominance", 0.5):
            add("surveiller", "equilibre", f"Une cause écrase les autres : « {top} » = {int(n / total * 100)} % des morts", f"{a['morts']}")
    for th, t in a["menaces"].items():
        if t["succes"] is not None and t["victoires"] + t["defaites"] >= 8 and (t["succes"] < 0.25 or t["succes"] > 0.97):
            add("surveiller", "equilibre", f"Menace « {th} » : {int(t['succes'] * 100)} % de victoires sur {t['victoires'] + t['defaites']} rencontres",
                "presque imbattable" if t["succes"] < 0.25 else "aucune menace réelle")
    for m, info in a["etapes"].items():
        pp = info["par_profil"]
        ref = (pp.get("moyen") or {}).get("median_min")
        cas = (pp.get("casual") or pp.get("debutant") or {})
        if ref and cas.get("median_min") and cas["median_min"] > 3 * ref:
            add("surveiller", "apprentissage", f"Étape « {m} » : le casual met {cas['median_min']} min contre {ref} pour le moyen",
                "mal expliquée ou mal signalée ?")
        tr = (pp.get("tryhard") or {}).get("median_min")
        if ref and tr is not None and tr < ref / 4:
            add("info", "equilibre", f"Étape « {m} » : le tryhard la boucle en {tr} min (moyen {ref})", "contournable ?")
        if info.get("jamais"):
            add("surveiller", "progression", f"Étape « {m} » jamais atteinte, par aucun Einherjar",
                "contenu hors de portée, mur de progression, ou séances trop courtes")
            continue
        for p, v in pp.items():
            if v["atteint"] is not None and v["atteint"] < 0.5 and p not in ("saboteur",):
                sev = "surveiller" if p in ("moyen", "tryhard") else "info"
                add(sev, "progression", f"Étape « {m} » atteinte par {int(v['atteint'] * 100)} % des {p}", "")
    for cue, by in a["apprentissage"].items():
        for p, v in by.items():
            if v["part"] is not None and v["part"] < 0.5:
                add("surveiller", "apprentissage", f"Signal « {cue} » compris par {int(v['part'] * 100)} % des {p}", "le jeu l'enseigne mal sans UI ?")
    for t in a["jumeaux"]:
        fa, fs = t["frustration_h"]["avec"], t["frustration_h"]["sans"]
        if fa is not None and fs is not None and fa > fs * 1.5 + 0.5:
            add("info" if t["role"] == "leader" else "surveiller", "social",
                f"Avec un {t['role']}, les autres sont frustrés {fa}/h contre {fs}/h sans lui", f"{t['avec']} vs {t['sans']}")
    for verb, by in a.get("mecaniques", {}).items():
        for p, v in by.items():
            if v["rate_debut"] is not None and v["rate_fin"] is not None and v["rate_fin"] >= 0.5 and v["rate_fin"] >= v["rate_debut"]:
                add("surveiller", "apprentissage", f"« {verb} » jamais maîtrisé par {p} : {int(v['rate_fin'] * 100)} % ratés en fin de séance",
                    f"{int(v['rate_debut'] * 100)} % au début ; pas de progrès avec la pratique")
    order = {"probleme": 0, "surveiller": 1, "info": 2}
    F.sort(key=lambda f: order[f["gravite"]])
    return F
