"""Comparer deux runs (non-régression, avant/après un correctif, version N contre N-1).

Lit les summary.json et sort les écarts des mesures clés par profil, plus les constats apparus / disparus.
"""
from __future__ import annotations

import json
from pathlib import Path

KEYS = [("success", "victoires", +1), ("deaths_h", "morts/h", -1), ("frustration_h", "frustration/h", -1),
        ("downtime", "ennui", -1), ("moments_h", "moments/h", +1), ("variety", "variété", +1), ("fail_rate", "ratés", -1),
        ("early_quit", "abandon tôt", -1), ("play_min", "min jouées", +1)]


def _load(p: str | Path) -> dict:
    p = Path(p)
    f = p / "rapport" / "summary.json" if p.is_dir() else p
    return json.loads(f.read_text(encoding="utf-8"))["analyse"]


def compare(old: str | Path, new: str | Path, pct: float = 15.0) -> dict:
    a, b = _load(old), _load(new)
    rows, regressions, improvements = [], [], []
    for pid in sorted(set(a["personas"]) | set(b["personas"])):
        pa, pb = a["personas"].get(pid), b["personas"].get(pid)
        if not pa or not pb:
            rows.append({"profil": pid, "note": "absent d'un des runs"})
            continue
        for k, label, good in KEYS:
            va, vb = pa.get(k), pb.get(k)
            if va is None or vb is None:
                continue
            delta = vb - va
            rel = (delta / abs(va) * 100) if va else (100.0 if delta else 0.0)
            row = {"profil": pid, "mesure": label, "avant": va, "apres": vb, "ecart_pct": round(rel, 1)}
            rows.append(row)
            if abs(rel) >= pct and abs(delta) > 1e-9:
                (improvements if delta * good > 0 else regressions).append(row)
    ta = {f["titre"] for f in a["constats"]}
    tb = {f["titre"] for f in b["constats"]}
    return {"avant": a["run"], "apres": b["run"], "regressions": regressions, "ameliorations": improvements,
            "constats_nouveaux": sorted(tb - ta), "constats_disparus": sorted(ta - tb), "lignes": rows}


def to_md(c: dict) -> str:
    L = [f"# Hyperbole — comparaison {c['avant']} → {c['apres']}", ""]
    for title, key in (("Régressions", "regressions"), ("Améliorations", "ameliorations")):
        L.append(f"## {title} ({len(c[key])})")
        L += [f"- {r['profil']} · {r['mesure']} : {r['avant']} → {r['apres']} ({r['ecart_pct']:+} %)" for r in c[key]] or ["- aucune"]
        L.append("")
    L += [f"## Constats nouveaux ({len(c['constats_nouveaux'])})"] + [f"- {t}" for t in c["constats_nouveaux"]] + [""]
    L += [f"## Constats disparus ({len(c['constats_disparus'])})"] + [f"- {t}" for t in c["constats_disparus"]]
    return "\n".join(L) + "\n"
