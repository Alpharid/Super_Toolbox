"""La Tête d'un Einherjar (version Python ; même logique que godot/addons/hyperbole/hyperbole_head.gd).

Utility AI : à chaque décision, le jeu propose les OPTIONS qu'un joueur verrait (aller quelque part, frapper, récolter,
fabriquer, parler…) ; la Tête note chacune selon le profil (envies, prudence, curiosité), ce qu'elle a appris en jouant,
son ennui et sa frustration, ce qu'elle sait du lobby ; elle en choisit une (ou se trompe, selon son adresse).

Elle ne lit JAMAIS le jeu : seulement ses Sens (Senses) et les retours de ses gestes. Les connaissances « wiki » d'une
option ne lui sont montrées que si le profil a ce savoir (knowledge = wiki) ou l'outil « wiki ».

Une option (dict) :
  id, verb, tags {tag: poids} ou [tags], area, risk (0-1, perçu), effort (s), target (bot visé), wiki {value},
  hint (texte affiché), group (bool, jeu en groupe), break (bool, cas limite pour le fouineur), disrupt (bool).
"""
from __future__ import annotations

import math
import random


class Head:
    def __init__(self, bot: str, persona: dict, rng: random.Random, lobby_knowledge: dict | None = None, emit=None,
                 tools: list[str] | None = None):
        self.bot = bot
        self.p = persona
        self.rng = rng
        self.lobby = {k: v for k, v in (lobby_knowledge or {}).items() if k != bot}
        self.emit = emit or (lambda kind, **d: None)
        allowed = persona.get("tools")
        self.tools = set(tools or []) if allowed is None else set(allowed) & set(tools or allowed)
        self.knows_wiki = persona.get("knowledge") == "wiki" or "wiki" in self.tools
        self.learned: dict[tuple, float] = {}
        self.tried: dict[str, int] = {}
        self.boredom = 0.0
        self.frustration = 0.0
        self.frustration_episodes = 0
        self.bored_episodes = 0
        self.fail_streak = 0
        self.last_option = None
        self.last_verb = None
        self.repeat = 0
        self.nuisance = []  # instants des gestes « disrupt » (plafond par heure)
        self.exploits_found: set = set()
        self.cue_seen: dict[str, list] = {}
        self.cues_learned: set = set()
        lo, hi = persona.get("session", {}).get("minutes", [45, 120])
        self.session_s = rng.uniform(lo, hi) * 60
        self.quit_reason = None

    # ------------------------------------------------------------ décider
    def _tag_value(self, tags) -> float:
        drives = self.p.get("drives", {})
        goals = self.p.get("goals", {}) or {}
        if isinstance(tags, (list, tuple)):
            tags = {t: 1.0 for t in tags}
        return sum(w * (drives.get(t, 0.0) + goals.get(t, 0.0)) for t, w in (tags or {}).items())

    def score(self, o: dict, t: float) -> float:
        p = self.p
        s = self._tag_value(o.get("tags"))
        key = (o.get("verb"), o.get("area"))
        n = self.tried.get(o.get("id"), 0)
        novelty = 1.0 / (1 + n)
        s += p.get("curiosity", 0.5) * novelty * (0.6 + self.boredom)
        s += self.learned.get(key, 0.0) * (0.4 + p.get("drives", {}).get("mastery", 0.3))
        s -= o.get("risk", 0.0) * (1.0 - p.get("risk", 0.5)) * 1.2
        if self.knows_wiki and isinstance(o.get("wiki"), dict):
            s += 0.5 * float(o["wiki"].get("value", 0.0))
        if o.get("hint") and self.rng.random() < p.get("reads_text", 0.5):
            s += 0.15
        if o.get("id") == self.last_option:
            s -= self.repeat * 0.05 * (1.2 - p.get("patience", 0.5)) * (0.5 + self.boredom)
        if o.get("verb") == "aller" and self.last_verb == "aller":
            s -= 0.5 * (0.5 + p.get("patience", 0.5))  # on vient d'arriver : on fait quelque chose avant de repartir
        target = o.get("target")
        if target and self.lobby.get(target) == "saboteur":
            s -= 0.6 * (1.0 - p.get("risk", 0.5))  # on se tient loin du troll du groupe
        if o.get("group") and "leader" in self.lobby.values():
            s += 0.3 * (1.0 - p.get("drives", {}).get("mastery", 0.5))  # les moins sûrs suivent le meneur
        if o.get("disrupt"):
            cap = p.get("nuisance_cap_per_hour") or 0
            recent = [x for x in self.nuisance if t - x < 3600]
            if p.get("social_role") != "saboteur" or len(recent) >= cap:
                return -9.0
        if o.get("break"):
            if (o.get("verb"), o.get("area")) in self.exploits_found:
                return -9.0  # faille déjà signalée : on ne l'exploite pas
            s += (p.get("drives", {}).get("break", 0.0) - 0.5) * 1.6  # les cas limites n'attirent que les fouineurs
        s += self.rng.gauss(0, 0.05 + p.get("skill", {}).get("mistake_rate", 0.08))
        return s

    def decide(self, options: list[dict], t: float) -> tuple[dict | None, float]:
        """Renvoie (option choisie, délai de réaction en s). None si rien à faire."""
        if not options:
            return None, 0.0
        sk = self.p.get("skill", {})
        if self.rng.random() < sk.get("mistake_rate", 0.08):
            o = self.rng.choice(options)  # erreur de joueur : mauvais bouton, mauvaise lecture
            sc = None
        else:
            scored = sorted(((self.score(o, t), o) for o in options), key=lambda x: -x[0])
            sc, o = scored[0]
            if sc <= -9.0:
                return None, 0.0
        if o.get("id") == self.last_option:
            self.repeat += 1
        else:
            self.repeat = 0
        self.last_option = o.get("id")
        self.last_verb = o.get("verb")
        self.tried[o.get("id")] = self.tried.get(o.get("id"), 0) + 1
        if o.get("disrupt"):
            self.nuisance.append(t)
        self.emit("intent", bot=self.bot, option=o.get("id"), score=None if sc is None else round(sc, 3), area=o.get("area"))
        delay = max(0.05, self.rng.gauss(sk.get("reaction_ms", 350), sk.get("reaction_ms", 350) * 0.2) / 1000)
        return o, delay

    # ------------------------------------------------------------ retours
    def feedback(self, o: dict, ok: bool, reward: float, t: float, dt: float, novel_result: bool = False):
        """Après le geste : apprendre (valeur du geste dans ce lieu), s'ennuyer, s'agacer."""
        p = self.p
        lr = p.get("skill", {}).get("learning_rate", 0.5) * 0.5
        key = (o.get("verb"), o.get("area"))
        self.learned[key] = (1 - lr) * self.learned.get(key, 0.0) + lr * (reward if ok else -0.5)
        if ok:
            self.fail_streak = 0
            self.frustration = max(0.0, self.frustration - 0.15)
        else:
            self.fail_streak += 1
            self.frustration += (0.25 + 0.1 * self.fail_streak) * (1.2 - p.get("frustration_tolerance", 0.5))
        if self.frustration >= 1.0:
            self.frustration_episodes += 1
            self.emit("frustrated", bot=self.bot, streak=self.fail_streak, area=o.get("area"))
            self.frustration = 0.4
            if self.frustration_episodes > 2 + 8 * p.get("frustration_tolerance", 0.5):
                self.quit_reason = "frustrated"
        interest = reward + (0.5 if novel_result else 0.0)
        if interest < 0.15:
            self.boredom += dt / 60 * (1.1 - p.get("boredom_tolerance", 0.5)) * 0.6
        else:
            self.boredom = max(0.0, self.boredom - interest * 0.5)
        if self.boredom >= 1.0:
            self.bored_episodes += 1
            self.emit("bored", bot=self.bot, duration=round(60 * (1.2 - p.get("boredom_tolerance", 0.5)), 1), area=o.get("area"))
            self.boredom = 0.3
            if self.bored_episodes > 2 + 6 * p.get("boredom_tolerance", 0.5):
                self.quit_reason = "bored"

    def see_cue(self, cue: str, t: float, then_hurt: bool | None = None):
        """Un signal perçu (une lueur, un son) ; s'il précède souvent une conséquence, il est compris (apprentissage)."""
        if cue in self.cues_learned:
            return True
        seen = self.cue_seen.setdefault(cue, [t, 0, 0])
        seen[1] += 1
        if then_hurt:
            seen[2] += 1
        need = max(1, round(6 * (1.1 - self.p.get("skill", {}).get("learning_rate", 0.5))))
        if seen[2] >= need:
            self.cues_learned.add(cue)
            self.emit("learn", bot=self.bot, cue=cue, after=round(t - seen[0], 1), essais=seen[1])
            return True
        return False

    def found_exploit(self, o: dict, what: str, steps: list[str], t: float):
        k = (o.get("verb"), o.get("area"))
        if k in self.exploits_found:
            return
        self.exploits_found.add(k)
        self.emit("exploit", bot=self.bot, what=what, steps=steps, area=o.get("area"))

    def wants_to_leave(self, play_s: float) -> str | None:
        if self.quit_reason:
            return self.quit_reason
        if play_s >= self.session_s:
            return "session_end"
        return None
