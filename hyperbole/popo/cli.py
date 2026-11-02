"""Ligne de commande de Mr. Popo.  python hyperbole.py <commande> …   (aide : python hyperbole.py -h)"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

from . import analyse as A
from . import compare as C
from . import journal as J
from . import lint as L
from . import mission as M
from . import narrate as N
from . import orchestrator as O
from . import personas as P
from . import report as R
from . import spirit as SP

HERE = Path(__file__).resolve().parent.parent


def _say(*a):
    print(*a, flush=True)


def make_report(run_dir: Path, esprit: bool | None = None, ouvrir: bool = False, forcer: bool = False) -> Path:
    run = A.load_run(run_dir)
    a = A.analyse(run)
    mission = run["manifest"]["mission"]
    S = mission.get("seuils", {})
    stories = N.stories(a, S)
    triage, slog = None, []
    cfg = dict(mission.get("esprit", {}))
    if forcer:
        cfg["forcer"] = True
    use = cfg.get("actif") if esprit is None else esprit
    if use:
        ok, why = SP.available(cfg)
        if not ok:
            slog.append(f"Esprit endormi : {why}")
        elif SP.gpu_busy() and not cfg.get("forcer"):
            slog.append("Esprit endormi : GPU occupé")
        else:
            sp = SP.Spirit(cfg)
            personas = P.load_all(mission.get("personas_dirs", []))
            for pid, p in a["personas"].items():
                v = sp.voice(pid, personas.get(pid, {}), {k: x for k, x in p.items() if k not in ("retention",)}, stories[pid])
                if v:
                    stories[pid] = v
            triage = sp.triage(a["constats"])
            sp.unload()
            slog += sp.log + [f"Esprit : {sp.calls} appels ({cfg.get('modele')})"]
    out = R.write(run_dir, a, stories, triage, slog)
    _say(f"Rapport : {out / 'rapport.html'}  ·  pour une IA : {out / 'brief_ia.md'}")
    n = {k: sum(1 for f in a['constats'] if f['gravite'] == k) for k in ('probleme', 'surveiller', 'info')}
    _say(f"Constats : {n['probleme']} problème(s), {n['surveiller']} à surveiller, {n['info']} info.")
    if ouvrir:
        webbrowser.open((out / "rapport.html").as_uri())
    return out


def cmd_lancer(a):
    m = M.load(a.mission)
    if a.minutes:
        m["duree_min"] = a.minutes
    if a.cycles:
        m["valhalla"]["cycles"] = a.cycles
    if a.chambres:
        m["chambres"] = a.chambres
    if m.get("lint", {}).get("fichiers"):
        pb = L.check(Path(m["_dir"]) / (m["lint"].get("racine") or "."), m["lint"])
        if pb:
            _say("Contrôle sans-triche ÉCHOUÉ, les Einherjar ne partent pas :\n  " + "\n  ".join(pb[:30]))
            return 2
    run_dir = O.run(m, a.sortie, dry=a.dry, log=_say)
    if not a.dry:
        make_report(run_dir, a.esprit, a.ouvrir)
    return 0


def cmd_rapport(a):
    make_report(Path(a.run), a.esprit, a.ouvrir, a.forcer)
    return 0


def cmd_comparer(a):
    c = C.compare(a.avant, a.apres, a.pct)
    md = C.to_md(c)
    if a.sortie:
        Path(a.sortie).write_text(md, encoding="utf-8")
    _say(md)
    return 1 if c["regressions"] and a.strict else 0


def cmd_rejouer(a):
    """Rejoue une chambre à l'identique (même graine, même lobby, mêmes paramètres) : vérifier un correctif."""
    src = Path(a.run)
    man = json.loads((src / "run.json").read_text(encoding="utf-8"))
    contract = json.loads((src / "chambres" / a.chambre / "chamber.json").read_text(encoding="utf-8"))
    m = M.finish({**M.DEFAULTS, **man["mission"]})
    m["_dir"] = str(Path(man.get("mission_file") or src).parent)
    m["lobbies"] = [{"personas": {}}]
    m["valhalla"] = {"cycles": 1}
    m["jumeaux"] = False
    if a.minutes:
        m["duree_min"] = a.minutes
    stamp = datetime.now().strftime("%H%M%S")
    m["_run_id"] = f"{man['run']}_rejeu-{a.chambre}-{stamp}"
    run_dir = src.parent / m["_run_id"]
    run_dir.mkdir(parents=True)
    from .chamber import Chamber
    lobby = [{"bot": b["bot"], "persona_id": b["persona_id"], "persona": b["persona"]} for b in contract["lobby"]]
    ch = Chamber(run_dir, a.chambre, m, lobby, contract["seed"], contract["mode"], contract["speed"], contract["params"],
                 contract.get("variant"), None, 1)
    (run_dir / "run.json").write_text(json.dumps({"run": m["_run_id"], "mission": {k: v for k, v in m.items() if not k.startswith("_")},
        "rejeu_de": str(src), "chambres": [{"id": a.chambre, "seed": contract["seed"], "lane": contract["mode"],
        "variant": contract.get("variant"), "cycle": 1, "lobby_index": 1, "twin_of": None}]}, ensure_ascii=False, indent=1), encoding="utf-8")
    ch.start()
    _say(f"Rejeu de {a.chambre} (graine {contract['seed']}) → {run_dir}")
    r = ch.watch(threading.Event())
    man2 = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    man2["resultats"] = [r]
    (run_dir / "run.json").write_text(json.dumps(man2, ensure_ascii=False, indent=1), encoding="utf-8")
    make_report(run_dir, False, a.ouvrir)
    return 0


def cmd_repro(a):
    """Exporte la suite d'entrées d'un Einherjar jusqu'à un instant : un scénario rejouable (test de non-régression)."""
    d = Path(a.run) / "chambres" / a.chambre
    contract = json.loads((d / "chamber.json").read_text(encoding="utf-8"))
    steps = []
    for e in J.read(d / "journal.jsonl"):
        if e.get("bot") != a.bot:
            continue
        if a.jusqua is not None and (e.get("t_game") or 0) > a.jusqua:
            break
        if e.get("kind") == "act":
            steps.append({"t": e.get("t_game"), "verb": e.get("verb"), "inputs": e.get("inputs"), "target": e.get("target")})
    scen = {"hyperbole_repro": 1, "seed": contract["seed"], "params": contract["params"], "bot": a.bot,
            "persona": next((b["persona_id"] for b in contract["lobby"] if b["bot"] == a.bot), None),
            "lobby": [b["persona_id"] for b in contract["lobby"]], "jusqua": a.jusqua, "etapes": steps}
    out = Path(a.sortie or (d / f"repro_{a.bot}.json"))
    out.write_text(json.dumps(scen, ensure_ascii=False, indent=1), encoding="utf-8")
    _say(f"{len(steps)} gestes → {out}")
    return 0


def cmd_profils(a):
    ps = P.load_all(a.dossier or [])
    bad = 0
    for pid, p in sorted(ps.items()):
        pb = P.check(p)
        bad += len(pb)
        _say(f"{'OK ' if not pb else 'ERR'} {pid:16} {p.get('nom', '')} — {p.get('description', '')[:90]}")
        for x in pb:
            _say("    " + x)
    return 1 if bad else 0


def cmd_valider(a):
    b = J.validate(J.read(a.journal))
    _say(json.dumps(b, ensure_ascii=False, indent=1))
    return 0 if b["ok"] else 1


def cmd_lint(a):
    m = M.load(a.mission)
    pb = L.check(Path(m["_dir"]) / (m["lint"].get("racine") or "."), m["lint"])
    _say("Sans triche : OK" if not pb else "Sans triche : ÉCHEC\n  " + "\n  ".join(pb))
    return 1 if pb else 0


def cmd_demo(a):
    if not a.banc:
        m = M.load(HERE / "demo" / "mission.json")
        if a.minutes:
            m["duree_min"] = a.minutes
        run_dir = O.run(m, a.sortie, log=_say)
        make_report(run_dir, a.esprit, a.ouvrir)
        return 0
    sys.path.insert(0, str(HERE))
    from demo import banc  # noqa: E402
    outs = {}
    for label, bugs in (("bugs", None), ("propre", [])):
        m = M.load(HERE / "demo" / "banc.json")
        if a.minutes:
            m["duree_min"] = a.minutes
        planted = m["bugs_plantes"]
        if bugs is not None:
            m["params"]["bugs"] = bugs
        m["nom"] = f"banc-{label}"
        outs[label] = make_report(O.run(m, a.sortie, log=_say), False, False)
    res = banc.score(outs["bugs"] / "summary.json", outs["propre"] / "summary.json", planted)
    (outs["bugs"] / "banc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if res["rappel"] >= a.rappel_min and not res["fausses_alertes_jeu_propre"] else 1


def cmd_pont(a):
    sys.path.insert(0, str(HERE))
    from einherjar.bridge import serve  # noqa: E402
    return serve(a.chamber, a.jeu[1:] if a.jeu[:1] == ["--"] else a.jeu)


def cmd_init(a):
    """Prépare un projet de jeu : <projet>/hyperbole/{mission.json, personas/, README.md} + .gitignore des runs."""
    root = Path(a.projet).resolve()
    d = root / "hyperbole"
    (d / "personas").mkdir(parents=True, exist_ok=True)
    tpl = json.loads((HERE / "missions" / f"modele-{a.moteur}.json").read_text(encoding="utf-8"))
    tpl["nom"] = root.name.lower()
    mf = d / "mission.json"
    if mf.exists() and not a.force:
        _say(f"{mf} existe déjà (--force pour écraser)")
    else:
        mf.write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "README.md").write_text(
        f"# Hyperbole pour {root.name}\n\nLe moteur vit dans la Super_Toolbox : `{HERE}` (lire son README.md).\n\n"
        f"- Mission : `mission.json` · profils propres au jeu : `personas/` (surchargent ceux de la toolbox)\n"
        f"- Lancer : `python {HERE / 'hyperbole.py'} lancer hyperbole/mission.json --ouvrir`\n"
        f"- Les runs vont dans `hyperbole/runs/` (hors git).\n", encoding="utf-8")
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("runs/\n", encoding="utf-8")
    if a.moteur == "godot":
        dst = root / "addons" / "hyperbole"
        if dst.exists() and not a.force:
            _say(f"{dst} existe déjà (--force pour remplacer)")
        else:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(HERE / "godot" / "addons" / "hyperbole", dst)
            _say(f"Addon Godot copié → {dst}")
    _say(f"Prêt : {d}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="hyperbole", description="Hyperbole — la salle du temps des Einherjar (Mr. Popo)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lancer", help="lancer une mission (chambres + Valhalla + rapport)")
    s.add_argument("mission")
    s.add_argument("--minutes", type=float, help="durée réelle par chambre")
    s.add_argument("--cycles", type=int, help="cycles du Valhalla")
    s.add_argument("--chambres", type=int, help="chambres en parallèle")
    s.add_argument("--sortie", help="dossier des runs")
    s.add_argument("--dry", action="store_true", help="préparer sans lancer")
    s.add_argument("--esprit", action="store_true", default=None, help="récits et tri par le LLM local")
    s.add_argument("--ouvrir", action="store_true", help="ouvrir la page du rapport")
    s.set_defaults(f=cmd_lancer)
    s = sub.add_parser("valhalla", help="= lancer avec plusieurs cycles (défaut 3)")
    s.add_argument("mission")
    s.add_argument("--cycles", type=int, default=3)
    s.add_argument("--minutes", type=float)
    s.add_argument("--chambres", type=int)
    s.add_argument("--sortie")
    s.add_argument("--dry", action="store_true")
    s.add_argument("--esprit", action="store_true", default=None)
    s.add_argument("--ouvrir", action="store_true")
    s.set_defaults(f=cmd_lancer)
    s = sub.add_parser("rapport", help="(re)faire le rapport d'un run")
    s.add_argument("run")
    s.add_argument("--forcer", action="store_true", help="réveiller l'Esprit même si le GPU est occupé")
    s.add_argument("--esprit", action="store_true", default=None)
    s.add_argument("--ouvrir", action="store_true")
    s.set_defaults(f=cmd_rapport)
    s = sub.add_parser("comparer", help="comparer deux runs (non-régression)")
    s.add_argument("avant")
    s.add_argument("apres")
    s.add_argument("--pct", type=float, default=15.0)
    s.add_argument("--sortie")
    s.add_argument("--strict", action="store_true", help="code 1 s'il y a des régressions (CI)")
    s.set_defaults(f=cmd_comparer)
    s = sub.add_parser("rejouer", help="rejouer une chambre (même graine, même lobby)")
    s.add_argument("run")
    s.add_argument("chambre")
    s.add_argument("--minutes", type=float)
    s.add_argument("--ouvrir", action="store_true")
    s.set_defaults(f=cmd_rejouer)
    s = sub.add_parser("repro", help="exporter les entrées d'un Einherjar jusqu'à t (scénario)")
    s.add_argument("run")
    s.add_argument("chambre")
    s.add_argument("bot")
    s.add_argument("--jusqua", type=float)
    s.add_argument("--sortie")
    s.set_defaults(f=cmd_repro)
    s = sub.add_parser("profils", help="lister et contrôler les profils")
    s.add_argument("--dossier", action="append")
    s.set_defaults(f=cmd_profils)
    s = sub.add_parser("valider", help="contrôler un journal JSONL contre le contrat")
    s.add_argument("journal")
    s.set_defaults(f=cmd_valider)
    s = sub.add_parser("lint", help="contrôle sans-triche des fichiers de la tête")
    s.add_argument("mission")
    s.set_defaults(f=cmd_lint)
    s = sub.add_parser("demo", help="mission de démonstration sur le jeu jouet (aucun moteur requis)")
    s.add_argument("--minutes", type=float)
    s.add_argument("--banc", action="store_true", help="banc de bugs injectés : mesure ce que les Einherjar trouvent")
    s.add_argument("--rappel-min", type=float, default=0.85, dest="rappel_min")
    s.add_argument("--sortie")
    s.add_argument("--esprit", action="store_true", default=None)
    s.add_argument("--ouvrir", action="store_true")
    s.set_defaults(f=cmd_demo)
    s = sub.add_parser("pont", help="têtes Python pour un jeu d'un autre moteur (TCP, voir docs/PROTOCOLE.md)")
    s.add_argument("chamber")
    s.add_argument("jeu", nargs=argparse.REMAINDER, help="-- commande du jeu (avec {port})")
    s.set_defaults(f=cmd_pont)
    s = sub.add_parser("init", help="préparer un projet de jeu (mission, profils, addon)")
    s.add_argument("projet")
    s.add_argument("--moteur", choices=["godot", "python", "commande"], default="godot")
    s.add_argument("--force", action="store_true")
    s.set_defaults(f=cmd_init)
    a = p.parse_args(argv)
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    return a.f(a) or 0
