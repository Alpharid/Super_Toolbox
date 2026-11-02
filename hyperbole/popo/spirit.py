"""L'Esprit : un LLM local (Ollama) qui donne une voix aux Einherjar et fait une passe de tri des constats.

Règles (guide joueurs-IA §5, veille Heimdall 2026-11-02) :
- optionnel : sans Ollama, ou GPU occupé, tout marche avec les gabarits ;
- appelé à la fin (récits + tri), jamais pour piloter un geste ; budget d'appels plafonné ;
- rien d'inventé : un récit dont un nombre n'existe pas dans les mesures est rejeté (on garde le gabarit) ;
- on décharge le modèle après usage (keep_alive: 0) : le GPU est partagé (atelier d'art, jeux, Alphred).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request


def _post(url: str, payload: dict, timeout: float = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def available(cfg: dict) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(cfg["url"].rstrip("/") + "/api/tags", timeout=3) as r:
            tags = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        return False, f"Ollama injoignable ({e})"
    names = {m.get("name") for m in tags.get("models", [])}
    if cfg["modele"] not in names:
        return False, f"modèle {cfg['modele']} absent (présents : {', '.join(sorted(n for n in names if n))})"
    return True, "ok"


def gpu_busy(limit_pct: int = 60) -> bool:
    """Vrai si le GPU est déjà très occupé (rendu, entraînement, jeu) : l'Esprit dort alors."""
    if not shutil.which("nvidia-smi"):
        return False
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=5)
        return max(int(x) for x in r.stdout.split()) > limit_pct
    except (ValueError, OSError, subprocess.SubprocessError):
        return False


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".").rstrip(".0") or "0" for n in re.findall(r"\d+(?:[.,]\d+)?", text)}


def _allowed_numbers(obj) -> set[str]:
    s: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            for form in (x, round(x), round(x, 1), round(x * 100) if abs(x) <= 1 else x):
                s.add(str(form).rstrip("0").rstrip(".") or "0")
        elif isinstance(x, str):
            s.update(_numbers(x))
    walk(obj)
    return s


class Spirit:
    def __init__(self, cfg: dict, max_calls: int = 24):
        self.cfg = cfg
        self.calls = 0
        self.max_calls = max_calls
        self.log: list[str] = []

    def _chat(self, system: str, user: str) -> dict | None:
        if self.calls >= self.max_calls:
            self.log.append("budget d'appels atteint")
            return None
        self.calls += 1
        try:
            r = _post(self.cfg["url"].rstrip("/") + "/api/chat", {
                "model": self.cfg["modele"], "stream": False, "format": "json", "think": False,
                "options": {"temperature": 0.6, "num_ctx": 8192},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
            return json.loads(r["message"]["content"])
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            self.log.append(f"appel raté : {e}")
            return None

    def voice(self, pid: str, persona: dict, measures: dict, template_story: list[dict]) -> list[dict] | None:
        """Réécrit les phrases MESURÉES dans la voix du profil. Il n'ajoute rien : chaque nombre de sa sortie doit
        figurer dans les phrases d'origine (pas seulement quelque part dans les mesures : un nombre mal attribué est
        une invention aussi)."""
        if not template_story:
            return None
        source = [s["texte"] for s in template_story]
        system = ("Tu réécris le compte rendu d'un joueur simulé après une séance de test d'un jeu vidéo, en français, à la "
                  "première personne, dans sa voix et son style. Règles absolues : tu gardes EXACTEMENT les mêmes faits et les "
                  "mêmes nombres que les phrases fournies, tu n'en ajoutes aucun, tu ne changes pas leur sens ; une phrase "
                  "réécrite par phrase fournie, au plus une phrase de ressenti sans nombre en plus. "
                  "Réponds en JSON : {\"phrases\": [\"...\"]}.")
        user = json.dumps({"profil": persona.get("nom", pid), "style": persona.get("voice", {}).get("style"),
                           "consignes_du_profil": persona.get("instructions") or None, "phrases": source}, ensure_ascii=False)
        out = self._chat(system, user)
        if not out or not isinstance(out.get("phrases"), list):
            return None
        phrases = [str(p) for p in out["phrases"]][:len(source) + 1]
        allowed = set().union(*[_numbers(t) for t in source])
        bad = [n for p in phrases for n in _numbers(p) if n not in allowed]
        if bad:
            self.log.append(f"récit {pid} rejeté : nombres absents des mesures {bad[:5]}")
            return None
        return [{"texte": p, "mesures": "réécrit par l'Esprit (nombres vérifiés)"} for p in phrases]

    def triage(self, findings: list[dict]) -> list[dict] | None:
        if not findings:
            return []
        system = ("Tu es le chef QA d'un studio. On te donne des constats MESURÉS par des bots de test. Regroupe ceux qui ont "
                  "sans doute la même cause, classe-les par priorité de correction, et propose pour chaque groupe UNE hypothèse "
                  "de cause, marquée comme hypothèse, et le premier test à faire. N'invente aucun fait ni aucun nombre. "
                  "JSON : {\"groupes\": [{\"titres\": [...], \"priorite\": 1, \"hypothese\": \"...\", \"test\": \"...\"}]}")
        out = self._chat(system, json.dumps([{"titre": f["titre"], "preuve": f["preuve"], "domaine": f["domaine"]}
                                             for f in findings[:30]], ensure_ascii=False))
        if not out or not isinstance(out.get("groupes"), list):
            return None
        return out["groupes"][:12]

    def unload(self):
        try:
            _post(self.cfg["url"].rstrip("/") + "/api/generate", {"model": self.cfg["modele"], "keep_alive": 0}, timeout=10)
        except (urllib.error.URLError, OSError, ValueError):
            pass
