"""Une chambre : un processus du jeu (headless) qui fait jouer un lobby d'Einherjar et écrit son journal.

Mr. Popo n'entre jamais dans le jeu. Il écrit `chamber.json` (le lobby, la graine, la vitesse, où écrire), lance la
commande du jeu, surveille que le journal avance, demande l'arrêt par un fichier `stop`, tue après un délai de grâce,
et note ce qu'il voit de l'extérieur (crash, gel, lignes d'erreur sur la sortie) dans `popo.jsonl`.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Lignes de la sortie du jeu qui deviennent des événements `error` (moteurs courants).
ERROR_PATTERNS = re.compile(
    r"(SCRIPT ERROR|USER ERROR|^ERROR:|\bERROR\b:|Unhandled exception|Exception:|Traceback \(most recent call last\)|"
    r"\bFatal\b|Assertion failed|Segmentation fault|LogScript: Error|LogOutputDevice: Error)", re.I)
WARNING_PATTERNS = re.compile(r"(WARNING:|\bWarning\b:)", re.I)


class Chamber:
    def __init__(self, run_dir: Path, chamber_id: str, mission: dict, lobby: list[dict], seed: int, lane: str,
                 speed, params: dict, variant: str | None, twin_of: str | None, cycle: int):
        self.id = chamber_id
        self.dir = run_dir / "chambres" / chamber_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.mission = mission
        self.lobby = lobby
        self.seed = seed
        self.lane = lane  # "chambre" (accélérée) ou "reel" (x1)
        self.speed = 1 if lane == "reel" else speed
        self.params = params
        self.variant = variant
        self.twin_of = twin_of
        self.cycle = cycle
        self.journal = self.dir / "journal.jsonl"
        self.popo_log = self.dir / "popo.jsonl"
        self.stop_file = self.dir / "stop"
        self.out_log = self.dir / "sortie.log"
        self.proc: subprocess.Popen | None = None
        self.result: dict = {}
        self._t0 = 0.0

    # ---- le contrat écrit pour le jeu ----
    def contract(self) -> dict:
        m = self.mission
        from .personas import lobby_knowledge
        return {
            "hyperbole": 1,
            "run": m["_run_id"],
            "world": self.id,
            "cycle": self.cycle,
            "seed": self.seed,
            "mode": self.lane,
            "speed": self.speed,
            "wall_seconds": int(m["duree_min"] * 60),
            "game_seconds_max": int(m["duree_jeu_h"] * 3600) if m.get("duree_jeu_h") else None,
            "variant": self.variant,
            "params": self.params,
            "twin_of": self.twin_of,
            "journal": str(self.journal),
            "stop_file": str(self.stop_file),
            "out_dir": str(self.dir),
            "lobby": [{"bot": b["bot"], "persona_id": b["persona_id"], "persona": b["persona"]} for b in self.lobby],
            "lobby_knowledge": lobby_knowledge(self.lobby),
        }

    def _fmt(self, s: str, contract_path: Path) -> str:
        return (s.replace("{chamber_json}", str(contract_path)).replace("{seed}", str(self.seed))
                .replace("{world}", self.id).replace("{speed}", str(self.speed)).replace("{mode}", self.lane)
                .replace("{out_dir}", str(self.dir)).replace("{bots}", str(len(self.lobby))))

    def _note(self, kind: str, **data):
        ev = {"t_game": None, "t_wall": round(time.time() - self._t0, 3), "world": self.id, "kind": kind, "source": "popo"}
        ev.update(data)
        with open(self.popo_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # ---- cycle de vie ----
    def start(self):
        path = self.dir / "chamber.json"
        path.write_text(json.dumps(self.contract(), ensure_ascii=False, indent=1), encoding="utf-8")
        jeu = self.mission["jeu"]
        cmd = [self._fmt(str(a), path) for a in jeu["cmd"]]
        env = {**os.environ, **{k: self._fmt(str(v), path) for k, v in jeu.get("env", {}).items()},
               "HYPERBOLE_CHAMBER": str(path)}
        cwd = jeu.get("cwd") or self.mission.get("_dir")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        self._t0 = time.time()
        self._out = open(self.out_log, "w", encoding="utf-8", errors="replace")
        self.proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, creationflags=flags,
                                     start_new_session=(sys.platform != "win32"))
        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()

    def _read_output(self):
        assert self.proc and self.proc.stdout
        errors = 0
        for raw in iter(self.proc.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            self._out.write(line + "\n")
            if ERROR_PATTERNS.search(line) and errors < 5000:
                errors += 1
                self._note("error", text=line[:500], level="error")
            elif WARNING_PATTERNS.search(line) and errors < 5000:
                errors += 1
                self._note("error", text=line[:500], level="warning")
        self._out.flush()

    def _journal_size(self) -> int:
        try:
            return self.journal.stat().st_size
        except OSError:
            return 0

    def watch(self, stop_event: threading.Event) -> dict:
        """Bloque jusqu'à la fin de la chambre. Renvoie le bilan vu de l'extérieur."""
        m = self.mission
        wall_max = m["duree_min"] * 60
        last_size, last_change = 0, time.time()
        asked_stop_at = None
        reason = "fin normale"
        while True:
            code = self.proc.poll()
            now = time.time()
            if code is not None:
                break
            size = self._journal_size()
            if size != last_size:
                last_size, last_change = size, now
            elapsed = now - self._t0
            if asked_stop_at is None:
                if stop_event.is_set():
                    reason = "arrêt demandé (kill switch)"
                elif elapsed > wall_max:
                    reason = "durée atteinte"
                elif now - last_change > m["heartbeat_s"] and elapsed > m["heartbeat_s"]:
                    reason = f"figée : journal immobile depuis {int(now - last_change)} s"
                    self._note("hang", seconds=int(now - last_change))
                else:
                    time.sleep(0.5)
                    continue
                self.stop_file.write_text(reason, encoding="utf-8")
                asked_stop_at = now
            elif now - asked_stop_at > m["grace_s"]:
                self._kill()
                reason += " ; tuée après le délai de grâce"
                self._note("anomaly", what="la chambre n'a pas obéi au fichier stop", grace_s=m["grace_s"])
                break
            time.sleep(0.5)
        code = self.proc.wait()
        self._reader.join(timeout=5)
        if self.proc.stdout:
            self.proc.stdout.close()
        self._out.close()
        crashed = code not in (0, None) and asked_stop_at is None
        if crashed:
            self._note("crash", reason=f"code de sortie {code}", code=code, tail=self._tail())
        if self._journal_size() == 0:
            self._note("anomaly", what="aucun journal écrit par la chambre (adaptateur absent ou chemin faux ?)")
        self.result = {"world": self.id, "code": code, "crashed": crashed, "reason": reason,
                       "wall_s": round(time.time() - self._t0, 1), "lane": self.lane, "variant": self.variant,
                       "twin_of": self.twin_of, "cycle": self.cycle, "seed": self.seed,
                       "bots": [b["bot"] for b in self.lobby]}
        return self.result

    def _tail(self, n: int = 30) -> str:
        try:
            return "\n".join(self.out_log.read_text(encoding="utf-8", errors="replace").splitlines()[-n:])
        except OSError:
            return ""

    def _kill(self):
        if not self.proc or self.proc.poll() is not None:
            return
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True)
        else:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
