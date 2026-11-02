"""Mr. Popo : il prépare les lobbies, envoie les Einherjar dans les chambres (K en parallèle), cycle après cycle
(le Valhalla), puis rassemble tout pour le rapport.

Kill switch : Ctrl+C, ou créer le fichier KILL dans le dossier du run. Chaque chambre reçoit alors son fichier stop.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import personas as P
from .chamber import Chamber


def _version(m: dict) -> str | None:
    cmd = m["jeu"].get("version_cmd")
    if not cmd:
        return None
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20, cwd=m.get("_dir"))
        return (r.stdout or r.stderr).strip()[:200] or None
    except Exception as e:  # noqa: BLE001 - la version est une aide, pas une condition
        return f"inconnue ({e})"


def plan(m: dict, personas: dict[str, dict]) -> list[dict]:
    """La liste des chambres à jouer (sans les lancer) : cycles x variantes x lobbies (+ jumeaux, + voie réelle)."""
    rng = random.Random(m.get("graine_plan", 12345))
    fixed = list(m.get("graines") or [])
    variants = m.get("variantes") or [{"nom": None, "params": {}}]
    out = []
    n = 0
    for cycle in range(1, int(m["valhalla"].get("cycles", 1)) + 1):
        for li, spec in enumerate(m["lobbies"]):
            seed = fixed[(li + (cycle - 1) * len(m["lobbies"])) % len(fixed)] if fixed else rng.randrange(1, 2**31)
            # Même composition et même graine pour toutes les variantes : seule la variante change (A/B honnête).
            lobby = P.compose(spec, personas, random.Random(seed), prefix=f"E{li + 1}")
            for v in variants:
                lanes = {"chambre": ["chambre"], "reel": ["reel"], "mixte": ["chambre", "reel"]}[m["mode"]]
                for lane in lanes:
                    n += 1
                    cid = f"c{cycle}-l{li + 1}" + (f"-{v['nom']}" if v["nom"] else "") + ("-x1" if lane == "reel" and m["mode"] == "mixte" else "")
                    params = {**m.get("params", {}), **v.get("params", {})}
                    base = {"id": cid, "cycle": cycle, "lobby_index": li + 1, "spec": spec, "lobby": lobby, "seed": seed,
                            "lane": lane, "variant": v["nom"], "params": params, "twin_of": None}
                    out.append(base)
                    twin = P.twin_without_disruptive(lobby) if m.get("jumeaux", True) else None
                    if twin:
                        out.append({**base, "id": cid + "-jumeau", "lobby": twin, "twin_of": cid})
    return out


def run(m: dict, out_root: str | None = None, dry: bool = False, log=print) -> Path:
    personas = P.load_all(m["personas_dirs"])
    problems = [p for pid in personas for p in P.check(personas[pid])]
    if problems:
        raise ValueError("profils invalides :\n  " + "\n  ".join(problems))
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{m['nom']}_{stamp}"
    m["_run_id"] = run_id
    root = Path(out_root or m.get("sortie") or Path(m.get("_dir", ".")) / "runs")
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    chambers_plan = plan(m, personas)
    manifest = {
        "run": run_id, "mission": {k: v for k, v in m.items() if not k.startswith("_")}, "mission_file": m.get("_path"),
        "version": _version(m), "debut": datetime.now().isoformat(timespec="seconds"), "machine": {"cpus": os.cpu_count()},
        "chambres": [{k: v for k, v in c.items() if k != "lobby"} | {"bots": [b["bot"] for b in c["lobby"]],
                     "personas": [b["persona_id"] for b in c["lobby"]]} for c in chambers_plan],
    }
    (run_dir / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total_min = len(chambers_plan) * m["duree_min"] / max(1, m["chambres"])
    log(f"Mr. Popo : {len(chambers_plan)} chambres, {m['chambres']} à la fois, ~{total_min:.0f} min réelles. Run : {run_dir}")
    if dry:
        return run_dir

    stop = threading.Event()
    kill_file = run_dir / "KILL"

    def kill_watch():
        while not stop.is_set():
            if kill_file.exists():
                log("Mr. Popo : fichier KILL vu, j'arrête toutes les chambres.")
                stop.set()
            time.sleep(1)

    threading.Thread(target=kill_watch, daemon=True).start()

    def one(c: dict) -> dict:
        if stop.is_set():
            return {"world": c["id"], "skipped": True}
        ch = Chamber(run_dir, c["id"], m, c["lobby"], c["seed"], c["lane"], m["vitesse"], c["params"], c["variant"],
                     c["twin_of"], c["cycle"])
        ch.start()
        log(f"  -> {c['id']} ({c['lane']}, {len(c['lobby'])} Einherjar : {', '.join(b['persona_id'] for b in c['lobby'])})")
        r = ch.watch(stop)
        log(f"  <- {c['id']} : {r['reason']}" + (" — CRASH" if r["crashed"] else ""))
        return r

    results = []
    try:
        with ThreadPoolExecutor(max_workers=m["chambres"]) as ex:
            futs = [ex.submit(one, c) for c in chambers_plan]
            for f in as_completed(futs):
                results.append(f.result())
    except KeyboardInterrupt:
        stop.set()
        log("Mr. Popo : Ctrl+C, arrêt des chambres en cours…")
    finally:
        stop.set()
    manifest["fin"] = datetime.now().isoformat(timespec="seconds")
    manifest["resultats"] = sorted(results, key=lambda r: r["world"])
    (run_dir / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return run_dir
