"""Le pont : des Têtes d'Einherjar en Python pour un jeu écrit dans N'IMPORTE QUEL moteur (Unreal, C#, Electron…).

Le jeu ne fait que trois choses : se connecter en TCP sur 127.0.0.1:<port>, envoyer ce que chaque bot perçoit avec les
options qu'un joueur aurait, et exécuter le geste choisi par ses entrées de joueur. Une ligne JSON par message.

  jeu -> pont : {"type":"senses","bot":"E1-01-casual","t":12.5,"senses":{...},"options":[{...}, ...]}
  pont -> jeu : {"type":"act","bot":"E1-01-casual","option":"gather_wood","delay":0.42,"leave":null}
  jeu -> pont : {"type":"outcome","bot":"E1-01-casual","t":14.0,"option":"gather_wood","ok":true,"reward":0.3,
                 "novel":false,"cues":[{"cue":"lueur_rouge","hurt":true}],"exploit":null}
  jeu -> pont : {"type":"bye"}

Forme calquée sur les API multi-agents (PettingZoo) : une observation et une action par agent. Le jeu écrit son
journal (act, fail, death…) ; le pont écrit celui des têtes (intent, learn, bored, frustrated, exploit) dans tete.jsonl.

Lancer (dans jeu.cmd d'une mission) :  python hyperbole.py pont {chamber_json} -- MonJeu.exe --hyperbole-port={port}
"""
from __future__ import annotations

import json
import random
import socket
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from einherjar.head import Head  # noqa: E402
from popo.journal import Journal  # noqa: E402


def serve(chamber_json: str, game_cmd: list[str]) -> int:
    c = json.loads(Path(chamber_json).read_text(encoding="utf-8"))
    clock = {"t": 0.0}
    jr = Journal(Path(c["out_dir"]) / "tete.jsonl", c["world"], clock=lambda: clock["t"])
    rng = random.Random(c["seed"])
    heads = {b["bot"]: Head(b["bot"], b["persona"], random.Random(rng.random()), c["lobby_knowledge"], emit=jr.write)
             for b in c["lobby"]}
    joined: dict[str, float] = {}
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    port = srv.getsockname()[1]
    cmd = [a.replace("{port}", str(port)) for a in game_cmd]
    proc = subprocess.Popen(cmd)
    stop = threading.Event()

    def handle(conn: socket.socket):
        f = conn.makefile("rwb")
        options_by_bot: dict[str, dict] = {}
        for raw in f:
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            kind = msg.get("type")
            bot = msg.get("bot")
            clock["t"] = float(msg.get("t", clock["t"]))
            h = heads.get(bot)
            if kind == "bye":
                break
            if h is None:
                continue
            joined.setdefault(bot, clock["t"])
            if kind == "senses":
                h.context = str((msg.get("senses") or {}).get("context", ""))
                for cue in (msg.get("senses") or {}).get("cues", []):
                    h.see_cue(cue, clock["t"])
                o, delay = h.decide(msg.get("options") or [], clock["t"])
                if o:
                    options_by_bot[bot] = o
                leave = h.wants_to_leave(clock["t"] - joined[bot])
                f.write((json.dumps({"type": "act", "bot": bot, "option": o.get("id") if o else None,
                                     "delay": round(delay, 3), "leave": leave}) + "\n").encode("utf-8"))
                f.flush()
            elif kind == "outcome":
                o = options_by_bot.get(bot) or {"id": msg.get("option")}
                h.feedback(o, bool(msg.get("ok")), float(msg.get("reward", 0.0)), clock["t"], float(msg.get("dt", 1.0)),
                           bool(msg.get("novel")))
                for cue in msg.get("cues") or []:
                    h.see_cue(cue.get("cue"), clock["t"], cue.get("hurt"))
                if msg.get("exploit"):
                    h.found_exploit(o, msg["exploit"].get("what"), msg["exploit"].get("steps", []), clock["t"])
        conn.close()

    def accept():
        srv.settimeout(1.0)
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle, args=(conn,), daemon=True).start()

    threading.Thread(target=accept, daemon=True).start()
    code = proc.wait()
    stop.set()
    jr.close()
    return code


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--" not in args or not args:
        print("usage : bridge.py <chamber.json> -- <commande du jeu avec {port}>")
        sys.exit(2)
    i = args.index("--")
    sys.exit(serve(args[0], args[i + 1:]))
