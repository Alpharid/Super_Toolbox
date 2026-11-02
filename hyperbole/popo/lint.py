"""Le contrôle « sans triche » : la Tête d'un Einherjar ne lit rien d'autre que ses Sens et son Corps.

On grep les fichiers de la tête (globs de la mission) à la recherche de chemins vers l'intérieur du jeu. Les fichiers
« autorisés » (la façade Senses, le Body) sont exemptés. Même idée que le test des Descellés de Guardians
(« Un_Descelle_ne_sait_que_ce_qu_un_joueur_peut_savoir ») et que la règle de Stryder (R240).
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

# Préréglages par moteur : ce qu'une tête de bot n'a jamais le droit d'écrire. Le jeu ajoute ses propres interdits
# (tables de butin, chances, recettes cachées, état des autres joueurs...).
PRESETS = {
    "godot": [r"get_tree\(\)", r"/root/", r"get_nodes_in_group", r"Engine\.get_singleton", r"\bget_parent\(\)\.get_parent",
              r"find_child\(", r"get_node\(\"/", r"\$/root", r"ProjectSettings\.get_setting", r"\.get_meta\("],
    "csharp": [r"GetTree\(\)", r"\bFindChild\(", r"GetNodesInGroup", r"\.GetField\(", r"BindingFlags\.NonPublic", r"typeof\([^)]*\)\.Get(Property|Field)"],
    "python": [r"\bimport\s+game\b", r"\bfrom\s+game\b", r"\bglobals\(\)", r"__dict__", r"\bgetattr\([^,]+,\s*['\"]_"],
}


def check(root: str | Path, cfg: dict) -> list[str]:
    root = Path(root)
    pats = [re.compile(p) for preset in cfg.get("presets", []) for p in PRESETS.get(preset, [])]
    pats += [re.compile(p) for p in cfg.get("interdits", [])]
    allowed = cfg.get("autorises", [])
    problems = []
    files = set()
    for g in cfg.get("fichiers", []):
        files.update(root.glob(g))
    if not files:
        return [f"aucun fichier de tête trouvé sous {root} pour {cfg.get('fichiers')} : le contrôle ne contrôle rien"]
    for f in sorted(files):
        rel = f.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(rel, a) or fnmatch.fnmatch(f.name, a) for a in allowed):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            code = line.split("#", 1)[0] if f.suffix in (".gd", ".py") else line.split("//", 1)[0]
            for p in pats:
                m = p.search(code)
                if m:
                    problems.append(f"{rel}:{n} lit l'intérieur du jeu : « {m.group(0)} »")
    return problems
