"""La Fosse : un jeu jouet (sans moteur) pour éprouver Hyperbole de bout en bout, et son banc de bugs injectés.

Un village, une forêt, une mine, un marais, une crête ; une quête en 5 étapes jusqu'au Wyrm. Les Einherjar y jouent par
OPTIONS de joueur (aller, récolter, chasser, forger…) et ne voient que ce qu'un joueur voit (Senses). Des bugs plantés
s'activent par params.bugs (voir BUGS) : le banc mesure lesquels les Einherjar retrouvent.

Lancé par Mr. Popo :  python la_fosse.py <chamber.json>
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from einherjar.head import Head  # noqa: E402
from popo.journal import Journal  # noqa: E402

BUGS = {
    "blocage_marais": "un trou de collision sur le chemin du marais bloque le joueur",
    "double_vente": "vendre deux fois dans la même image paie deux fois",
    "fuite_memoire": "la mémoire grimpe avec le temps de jeu",
    "boss_injuste": "le Wyrm est presque imbattable",
    "erreur_forge": "la forge plante (erreur de script) à partir de la lame +3",
    "teleport_mine": "entrer dans la mine téléporte le joueur",
    "potion_morte": "les potions ne font rien dans le marais",
}

AREAS = {
    "village": {"c": (20, 20), "threat": None, "power": 0, "res": None},
    "foret": {"c": (8, 30), "threat": "loup", "power": 1.0, "res": "bois"},
    "mine": {"c": (32, 30), "threat": "golem", "power": 1.8, "res": "minerai"},
    "marais": {"c": (30, 8), "threat": "sangsue", "power": 1.6, "res": "herbe"},
    "crete": {"c": (6, 6), "threat": "drake", "power": 3.6, "res": None},
}
QUEST = [("parler_ancien", "village"), ("bois_x10", "foret"), ("forger_lame", "village"), ("herbes_x5", "marais"),
         ("vaincre_wyrm", "crete")]
SPEED = 4.0  # unités par seconde de jeu


class Player:
    def __init__(self, b, rng, head, t):
        self.bot, self.pid, self.p = b["bot"], b["persona_id"], b["persona"]
        self.head = head
        self.rng = rng
        self.area = "village"
        self.pos = list(self.jitter("village"))
        self.hp, self.gear, self.gold, self.potions = 100.0, 1, 10, 1
        self.inv = {"bois": 0, "minerai": 0, "herbe": 0}
        self.total = {"bois": 0, "herbe": 0}
        self.quest = 0
        self.join = t
        self.next = t + rng.uniform(0, 30)
        self.gone = False
        self.stuck_until = 0.0
        self.leader_area = None

    def jitter(self, area):
        cx, cy = AREAS[area]["c"]
        return (cx + self.rng.uniform(-3, 3), cy + self.rng.uniform(-3, 3))


class LaFosse:
    def __init__(self, c: dict):
        self.c = c
        self.bugs = set(c["params"].get("bugs", []))
        self.rng = random.Random(c["seed"])
        self.t = 0.0
        self.jr = Journal(c["journal"], c["world"], clock=lambda: self.t)
        self.players: list[Player] = []
        for b in c["lobby"]:
            head = Head(b["bot"], b["persona"], random.Random(self.rng.random()), c["lobby_knowledge"], emit=self.jr.write)
            self.players.append(Player(b, random.Random(self.rng.random()), head, 0.0))
        self.leader = next((p for p in self.players if p.p.get("social_role") == "leader"), None)
        self.mem = 310.0
        self.next_perf = 0.0
        self.wyrm = 14.0 if "boss_injuste" in self.bugs else 5.2

    def e(self, kind, **d):
        self.jr.write(kind, **d)

    # ---------------------------------------------------------------- options vues par un joueur
    def options(self, pl: Player) -> list[dict]:
        a = pl.area
        A = AREAS[a]
        q = QUEST[pl.quest][0] if pl.quest < len(QUEST) else None
        q_area = QUEST[pl.quest][1] if pl.quest < len(QUEST) else None
        o = []
        for other, info in AREAS.items():
            if other == a:
                continue
            tags = {"explore": 0.6}
            if other == q_area and not (q == "forger_lame" and pl.inv["minerai"] < 2 * pl.gear):
                tags["progress"] = 1.0
            hint = "Le journal de quête indique : " + other if other == q_area else None
            if other == "mine" and q == "forger_lame" and pl.inv["minerai"] < 2 * pl.gear:
                tags["progress"] = 0.9  # le journal de quête dit où trouver le minerai
                hint = "Forgeron : « Il me faut du minerai de la mine. »"
            if other == "village" and (sum(pl.inv.values()) > 6 or pl.hp < 50):
                tags["survive"] = 0.8
                tags["collect"] = 0.4
            o.append({"id": f"aller:{other}", "verb": "aller", "area": other, "tags": tags,
                      "risk": min(1.0, info["power"] / 6), "wiki": {"value": 0.6 if other == q_area else 0.0},
                      "hint": hint})
        if A["res"]:
            o.append({"id": f"recolter:{a}", "verb": "recolter", "area": a, "tags": {"collect": 1.0, "progress": 0.6 if q in ("bois_x10", "herbes_x5") else 0.1}})
        if A["threat"]:
            o.append({"id": f"chasser:{a}", "verb": "chasser", "area": a, "tags": {"mastery": 1.0, "progress": 0.2, "show": 0.2},
                      "risk": min(1.0, A["power"] / (pl.gear * 2.2))})
            o.append({"id": f"esbroufe:{a}", "verb": "esbroufe", "area": a, "tags": {"show": 1.2}, "risk": 0.5})
        if a == "crete" and q == "vaincre_wyrm":
            o.append({"id": "affronter_wyrm", "verb": "affronter", "area": a, "tags": {"progress": 1.2, "mastery": 1.0, "show": 0.8},
                      "risk": min(1.0, self.wyrm / (pl.gear * 2.5)), "wiki": {"value": 0.8 if pl.gear >= 3 else -0.6}})
        if a == "village":
            if sum(pl.inv.values()):
                o.append({"id": "vendre", "verb": "vendre", "area": a, "tags": {"collect": 0.5, "progress": 0.3}})
                o.append({"id": "vendre_en_rafale", "verb": "vendre_rafale", "area": a, "tags": {}, "break": True})
            if pl.gold >= 8 and pl.potions < 3:
                o.append({"id": "acheter_potion", "verb": "acheter", "area": a, "tags": {"survive": 0.9}, "hint": "Potions : 8 or."})
            if pl.inv["bois"] >= 4 and pl.inv["minerai"] >= 2 * pl.gear:
                o.append({"id": "forger", "verb": "forger", "area": a, "tags": {"create": 1.0, "progress": 1.0 if q == "forger_lame" else 0.5, "mastery": 0.4}})
            if q == "parler_ancien":
                o.append({"id": "parler_ancien", "verb": "parler", "area": a, "tags": {"progress": 1.2}, "hint": "Un vieil homme vous fait signe."})
            o.append({"id": "discuter", "verb": "discuter", "area": a, "tags": {"social": 1.0, "rest": 0.3}})
        if pl.potions and pl.hp < 60:
            o.append({"id": "boire_potion", "verb": "boire", "area": a, "tags": {"survive": 1.2}})
        o.append({"id": "se_reposer", "verb": "repos", "area": a, "tags": {"rest": 0.8, "survive": 0.4 if pl.hp < 70 else 0.0}})
        for other in self.players:
            if other is pl or other.gone or other.area != a:
                continue
            if a != "village" and AREAS[a]["threat"]:
                o.append({"id": f"aider:{other.bot}", "verb": "aider", "area": a, "tags": {"help": 1.0, "social": 0.5}, "target": other.bot, "group": True})
                o.append({"id": f"voler_cible:{other.bot}", "verb": "voler_cible", "area": a, "tags": {"disrupt": 1.0}, "target": other.bot, "disrupt": True})
        if self.leader and pl is not self.leader and not self.leader.gone and self.leader.area != a:
            o.append({"id": "suivre_meneur", "verb": "aller", "area": self.leader.area, "tags": {"social": 0.6, "progress": 0.3}, "group": True})
        if pl is self.leader:
            o.append({"id": "organiser", "verb": "organiser", "area": a, "tags": {"lead": 1.0, "social": 0.4}})
        return o

    # ---------------------------------------------------------------- jouer un geste
    def act(self, pl: Player, o: dict) -> tuple[bool, float, float, bool]:
        """Renvoie (réussi, récompense perçue, durée, résultat nouveau)."""
        v, a = o["verb"], pl.area
        aim = pl.p.get("skill", {}).get("aim", 0.5)
        r = pl.rng
        self.e("act", bot=pl.bot, verb=v, area=o["area"], pos=[round(x, 1) for x in pl.pos], inputs=o["id"])
        if v == "aller" and o["id"] in (f"aller:{o['area']}", "suivre_meneur"):
            dest = o["area"]
            tx, ty = pl.jitter(dest)
            dist = math.dist(pl.pos, (tx, ty))
            dur = dist / SPEED
            if dest == "marais" and "blocage_marais" in self.bugs and r.random() < 0.35:
                pl.pos = [27.6 + r.uniform(-.5, .5), 12.4 + r.uniform(-.5, .5)]
                stuck = r.uniform(30, 90)
                self.e("stuck", bot=pl.bot, pos=[round(x, 1) for x in pl.pos], intent=o["id"], area="chemin_marais", duration=round(stuck))
                self.e("fail", bot=pl.bot, verb="aller", area=dest, reason="bloque")
                pl.pos = list(pl.jitter(a))
                return False, -0.2, stuck, False
            new = dest not in pl.head.tried or pl.head.tried.get(o["id"], 0) <= 1
            pl.area = dest
            pl.pos = [tx, ty]
            if dest == "mine" and "teleport_mine" in self.bugs and r.random() < 0.5:
                self.e("act", bot=pl.bot, verb="arriver", area=dest, pos=[round(tx + 40, 1), round(ty, 1)])
            q = QUEST[pl.quest] if pl.quest < len(QUEST) else None
            return True, 0.4 if (q and q[1] == dest) else 0.05, dur, new
        if v == "recolter":
            res = AREAS[a]["res"]
            trap = self._trap(pl)
            if trap:
                return False, -0.5, 8, False
            if r.random() > 0.55 + 0.4 * aim:
                self.e("fail", bot=pl.bot, verb=v, area=a, reason="rate")
                return False, 0.0, 6, False
            n = r.randint(1, 3)
            pl.inv[res] += n
            if res in pl.total:
                pl.total[res] += n
            self.e("gain", bot=pl.bot, resource=res, amount=n, source="recolte", total=pl.inv[res], pos=[round(x, 1) for x in pl.pos])
            self._quest_check(pl)
            return True, 0.2, 7, False
        if v in ("chasser", "esbroufe", "affronter"):
            if v != "affronter" and self._trap(pl):
                return False, -0.5, 8, False
            power = self.wyrm if v == "affronter" else AREAS[a]["power"]
            threat = "wyrm" if v == "affronter" else AREAS[a]["threat"]
            helped = sum(1 for x in self.players if x is not pl and not x.gone and x.area == a and x.head.last_option == f"aider:{pl.bot}")
            edge = pl.gear * 1.5 + aim * 2 + helped * 0.8 - power - (1.0 if v == "esbroufe" else 0)
            win = r.random() < 1 / (1 + math.exp(-edge * 1.1))
            thief = next((x for x in self.players if x is not pl and not x.gone and x.area == a and x.head.last_option == f"voler_cible:{pl.bot}"), None)
            if thief and win:
                self.e("fail", bot=pl.bot, verb=v, area=a, reason="cible_volee", blame=thief.bot)
                self.e("social", bot=thief.bot, **{"with": pl.bot}, what="vol_de_cible")
                return False, -0.3, 10, False
            self.e("encounter", bot=pl.bot, threat=threat, outcome="win" if win else "lose", pos=[round(x, 1) for x in pl.pos])
            if win:
                gold = int(power * 3) + r.randint(0, 3)
                pl.gold += gold
                self.e("gain", bot=pl.bot, resource="or", amount=gold, source=threat, total=pl.gold)
                if v == "affronter":
                    self.e("moment", bot=pl.bot, what="Wyrm vaincu", intensity=1.0)
                    self._advance(pl)
                elif v == "esbroufe":
                    self.e("moment", bot=pl.bot, what=f"esbroufe réussie contre un {threat}", intensity=0.6)
                elif pl.hp < 25:
                    self.e("moment", bot=pl.bot, what="victoire de justesse", intensity=0.7)
                return True, 0.6 if v == "affronter" else 0.3, 12, v == "esbroufe"
            pl.hp -= 12 * power * r.uniform(0.6, 1.2)
            if pl.hp <= 0:
                self._death(pl, threat, v)
                return False, -1.0, 15, False
            return False, -0.2, 12, False
        if v == "vendre":
            n = sum(pl.inv.values())
            keep = {"bois": 4, "minerai": 2 * pl.gear, "herbe": 0 if pl.quest != 3 else 5}
            sold = sum(max(0, pl.inv[k] - keep[k]) for k in pl.inv)
            if not sold:
                self.e("fail", bot=pl.bot, verb=v, area=a, reason="rien_a_vendre")
                return False, -0.1, 3, False
            for k in pl.inv:
                pl.inv[k] = min(pl.inv[k], keep[k])
            pl.gold += sold * 2
            self.e("gain", bot=pl.bot, resource="or", amount=sold * 2, source="vente", total=pl.gold)
            return True, 0.25, 5, False
        if v == "vendre_rafale":
            n = sum(pl.inv.values())
            if "double_vente" in self.bugs and n:
                pl.gold += n * 4
                for k in pl.inv:
                    pl.inv[k] = 0
                self.e("gain", bot=pl.bot, resource="or", amount=n * 4, source="vente_rafale", total=pl.gold)
                pl.head.found_exploit(o, "vendre deux fois dans la même image paie deux fois",
                                      ["avoir des objets", "ouvrir le marchand", "cliquer « vendre » deux fois très vite"], self.t)
                return True, 0.5, 3, True
            self.e("refusal", bot=pl.bot, what="vente déjà en cours")
            self.e("fail", bot=pl.bot, verb=v, area=a, reason="refus")
            return False, 0.0, 2, False
        if v == "acheter":
            pl.gold -= 8
            pl.potions += 1
            self.e("spend", bot=pl.bot, resource="or", amount=8, sink="potion", total=pl.gold)
            return True, 0.1, 3, False
        if v == "boire":
            pl.potions -= 1
            if a == "marais" and "potion_morte" in self.bugs:
                self.e("fail", bot=pl.bot, verb=v, area=a, reason="no_effect")
                return False, -0.3, 2, False
            pl.hp = min(100, pl.hp + 50)
            return True, 0.3, 2, False
        if v == "forger":
            if pl.gear >= 2 and "erreur_forge" in self.bugs:  # la lame +3
                print(f"SCRIPT ERROR: forge.gd:88 - Invalid get index 'lame' (on base: 'Nil'). bot={pl.bot} gear={pl.gear}", flush=True)
                self.e("fail", bot=pl.bot, verb=v, area=a, reason="erreur")
                return False, -0.4, 5, False
            pl.inv["bois"] -= 4
            pl.inv["minerai"] -= 2 * pl.gear
            pl.gear += 1
            self.e("spend", bot=pl.bot, resource="minerai", amount=2 * (pl.gear - 1), sink="forge", total=pl.inv["minerai"])
            self.e("moment", bot=pl.bot, what=f"lame +{pl.gear} forgée", intensity=0.4)
            self._quest_check(pl)
            return True, 0.6, 10, True
        if v == "parler":
            self._advance(pl)
            return True, 0.5, 6, True
        if v in ("discuter", "organiser"):
            if v == "discuter":
                self.e("social", bot=pl.bot, **{"with": "village"}, what="discussion")
            return True, 0.1 + 0.2 * pl.p.get("drives", {}).get("social", 0.3), 20, False
        if v == "repos":
            pl.hp = min(100, pl.hp + 15)
            return True, 0.02, 30, False
        if v == "aider":
            self.e("social", bot=pl.bot, **{"with": o["target"]}, what="aide")
            return True, 0.2, 12, False
        if v == "voler_cible":
            return True, 0.2, 10, False
        return True, 0.0, 5, False

    def _trap(self, pl: Player) -> bool:
        if pl.area != "marais" or pl.rng.random() > 0.18:
            return False
        glow = pl.rng.random() < 0.8
        if glow and pl.head.see_cue("lueur_rouge", self.t):
            return False  # il a compris la lueur : il contourne
        pl.hp -= 25
        if glow:
            pl.head.see_cue("lueur_rouge", self.t, then_hurt=True)
        self.e("fail", bot=pl.bot, verb="piege", area="marais", reason="piege")
        if pl.hp <= 0:
            self._death(pl, "piege_marais", "recolter")
        return True

    def _death(self, pl: Player, cause, doing):
        self.e("death", bot=pl.bot, cause=cause, doing=doing, pos=[round(x, 1) for x in pl.pos], area=pl.area)
        lost = pl.gold // 5
        pl.gold -= lost
        if lost:
            self.e("spend", bot=pl.bot, resource="or", amount=lost, sink="mort", total=pl.gold)
        pl.hp, pl.area = 100.0, "village"
        pl.pos = list(pl.jitter("village"))
        self.e("respawn", bot=pl.bot, pos=[round(x, 1) for x in pl.pos])

    def _quest_check(self, pl: Player):
        q = QUEST[pl.quest][0] if pl.quest < len(QUEST) else None
        if (q == "bois_x10" and pl.total["bois"] >= 10) or (q == "forger_lame" and pl.gear >= 2) or (q == "herbes_x5" and pl.total["herbe"] >= 5):
            self._advance(pl)

    def _advance(self, pl: Player):
        if pl.quest < len(QUEST):
            self.e("progress", bot=pl.bot, milestone=QUEST[pl.quest][0])
            pl.quest += 1

    # ---------------------------------------------------------------- boucle
    def run(self):
        c = self.c
        stop = Path(c["stop_file"])
        wall_max = c.get("wall_seconds") or 600
        game_max = c.get("game_seconds_max") or 10 ** 9
        speed = c.get("speed")
        t_wall0 = time.perf_counter()
        self.e("chamber_start", seed=c["seed"], mode=c["mode"], speed=speed, game="la_fosse", bugs=sorted(self.bugs),
               lobby=[b["persona_id"] for b in c["lobby"]], milestones=[q for q, _ in QUEST])
        joined = set()
        steps = 0
        while True:
            live = [p for p in self.players if not p.gone]
            if not live:
                reason = "tous partis"
                break
            pl = min(live, key=lambda p: p.next)
            self.t = pl.next
            if isinstance(speed, (int, float)) and speed > 0:  # vitesse fixe : on attend l'horloge
                lag = self.t / speed - (time.perf_counter() - t_wall0)
                if lag > 0:
                    time.sleep(min(lag, 0.5))
            steps += 1
            if steps % 200 == 0:
                if stop.exists():
                    reason = "stop"
                    break
                if time.perf_counter() - t_wall0 > wall_max:
                    reason = "durée réelle"
                    break
            if self.t > game_max:
                reason = "durée de jeu"
                break
            while self.t >= self.next_perf:
                if "fuite_memoire" in self.bugs:
                    self.mem += 0.9
                self.e("perf", fps=round(60 - pl.rng.random() * 3, 1), frame_ms_p99=round(17 + pl.rng.random() * 4, 1),
                       mem_mb=round(self.mem + pl.rng.random() * 2, 1), nodes=900 + 40 * len(live), entities=60 + 5 * len(live))
                self.next_perf += 60
            if pl.bot not in joined:
                joined.add(pl.bot)
                pl.join = self.t
                self.e("bot_join", bot=pl.bot, persona=pl.pid, session_planned_s=round(pl.head.session_s))
            leave = pl.head.wants_to_leave(self.t - pl.join)
            if leave:
                pl.gone = True
                self.e("bot_leave", bot=pl.bot, reason=leave, quest=pl.quest, gear=pl.gear)
                continue
            o, delay = pl.head.decide(self.options(pl), self.t)
            if not o:
                pl.next = self.t + 5
                continue
            ok, reward, dur, novel = self.act(pl, o)
            pl.head.feedback(o, ok, reward, self.t, dur, novel)
            pl.next = self.t + delay + dur
        for p in self.players:
            if not p.gone:
                self.e("bot_leave", bot=p.bot, reason="fin_de_chambre", quest=p.quest, gear=p.gear)
        self.e("chamber_end", reason=reason)
        self.jr.close()


if __name__ == "__main__":
    LaFosse(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))).run()
