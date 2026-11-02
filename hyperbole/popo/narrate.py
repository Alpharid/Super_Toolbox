"""Le récit de chaque profil, dans sa voix, écrit SEULEMENT à partir des mesures (chaque phrase cite sa mesure).

Sans LLM : des gabarits par profil. Avec l'Esprit (spirit.py) : le LLM réécrit, puis on vérifie que chaque nombre
qu'il cite existe dans les mesures ; sinon on garde les gabarits (rien d'inventé).
"""
from __future__ import annotations

# Phrases par profil ; {x} est remplacé par la mesure. Un profil absent prend « defaut ».
VOICES = {
    "defaut": {
        "intro": "J'ai joué {play_min} min en médiane.",
        "dur": "Ça tape fort : je gagne {success_pct} % de mes rencontres et je meurs {deaths_h} fois par heure.",
        "facile": "Trop facile : {success_pct} % de rencontres gagnées.",
        "ennui": "Je me suis ennuyé {downtime_pct} % du temps.",
        "frustre": "Frustré {frustration_h} fois par heure, je rate {fail_pct} % de mes gestes.",
        "moments": "{moments_h} moments marquants par heure.",
        "epuise": "Après {last_new_min} min, plus rien de neuf à faire.",
        "quitte": "{early_pct} % d'entre nous ont lâché avant la moitié de la séance prévue.",
        "ok": "Rien de bloquant de mon côté.",
    },
    "tryhard": {
        "intro": "{play_min} min de grind en médiane.",
        "dur": "{success_pct} % de victoires, {deaths_h} morts/h : il y a un mur, et pas un mur de skill.",
        "facile": "{success_pct} % de victoires. Aucun défi, il faut monter la difficulté du contenu de fin.",
        "ennui": "{downtime_pct} % de temps mort. Inacceptable, c'est autant de temps sans optimiser.",
        "frustre": "{frustration_h} frustrations/h et {fail_pct} % de gestes ratés : les contrôles ne suivent pas.",
        "moments": "{moments_h} moments/h, rien qui me retienne.",
        "epuise": "Contenu bouclé en {last_new_min} min. Il en faut plus, ou plus profond.",
        "quitte": "{early_pct} % de mes pareils ont quitté tôt, le jeu ne tient pas la distance.",
        "ok": "Rien à redire sur le rythme, c'est rare.",
    },
    "casual": {
        "intro": "J'ai joué un peu, {play_min} min.",
        "dur": "Je meurs tout le temps ({deaths_h} fois par heure), je gagne {success_pct} % des combats. Bof.",
        "facile": "Tranquille, {success_pct} % de combats gagnés.",
        "ennui": "Je savais pas quoi faire {downtime_pct} % du temps.",
        "frustre": "Je rate {fail_pct} % de ce que j'essaie, ça m'a énervé {frustration_h} fois par heure.",
        "moments": "{moments_h} trucs sympas par heure.",
        "epuise": "Au bout de {last_new_min} min j'ai l'impression d'avoir tout vu.",
        "quitte": "{early_pct} % de nous ont lâché avant la moitié. Moi y compris, peut-être.",
        "ok": "C'était cool, je reviendrai.",
    },
    "chill": {
        "intro": "{play_min} min à flâner.",
        "dur": "Difficile de se poser : {deaths_h} morts par heure, {success_pct} % de rencontres gagnées.",
        "facile": "Le monde me laisse tranquille ({success_pct} % de rencontres gagnées), j'aime ça.",
        "ennui": "Le monde est vide {downtime_pct} % du temps, il manque de quoi s'occuper sans but.",
        "frustre": "{frustration_h} agacements par heure, ça casse l'ambiance.",
        "moments": "{moments_h} jolis moments par heure.",
        "epuise": "Après {last_new_min} min je n'avais plus de coin à découvrir.",
        "quitte": "{early_pct} % des flâneurs sont partis tôt.",
        "ok": "Un endroit où l'on reste.",
    },
    "streamer": {
        "intro": "Live de {play_min} min, salut le chat !",
        "dur": "{deaths_h} morts/h et {success_pct} % de victoires : le chat rage avec moi, ça peut se clipper, mais pas trop longtemps.",
        "facile": "{success_pct} % de victoires, aucune tension à l'écran.",
        "ennui": "{downtime_pct} % du live sans rien à montrer, le chat s'en va.",
        "frustre": "{frustration_h} rages/h, {fail_pct} % de ratés.",
        "moments": "{moments_h} moments à clipper par heure.",
        "epuise": "Plus rien de neuf à montrer après {last_new_min} min.",
        "quitte": "{early_pct} % des streamers ont coupé le live tôt.",
        "ok": "Bon live, je relance demain.",
    },
    "fouineur": {
        "intro": "{play_min} min à pousser les règles dans les coins.",
        "dur": "{deaths_h} morts/h en testant les limites, normal.",
        "facile": "{success_pct} % de victoires : je n'ai pas eu besoin de faille pour gagner.",
        "ennui": "{downtime_pct} % du temps sans rien à tester.",
        "frustre": "{fail_pct} % de gestes refusés : c'est mon travail.",
        "moments": "{moments_h} moments/h.",
        "epuise": "Plus de surface à tester après {last_new_min} min.",
        "quitte": "{early_pct} % ont arrêté tôt.",
        "ok": "Pas de faille trouvée cette fois. Je ne dis pas qu'il n'y en a pas.",
        "faille": "{failles} faille(s) trouvée(s), reproduite(s) une fois et signalée(s) : {failles_noms}.",
    },
    "debutant": {
        "intro": "Première fois, {play_min} min.",
        "dur": "Je comprends pas pourquoi je meurs ({deaths_h} fois par heure).",
        "facile": "J'ai réussi {success_pct} % de mes combats, je suis content.",
        "ennui": "J'étais perdu {downtime_pct} % du temps, je ne savais pas quoi faire.",
        "frustre": "Je rate {fail_pct} % de ce que j'essaie : je ne sais pas encore jouer.",
        "moments": "{moments_h} moments où j'ai fait « waouh » par heure.",
        "epuise": "Après {last_new_min} min, rien de nouveau.",
        "quitte": "{early_pct} % des débutants ont abandonné tôt.",
        "ok": "J'ai appris tout seul, c'était bien expliqué.",
    },
}


def _vals(p: dict) -> dict:
    def pct(x):
        return None if x is None else int(round(x * 100))
    return {"play_min": p.get("play_min"), "success_pct": pct(p.get("success")), "deaths_h": p.get("deaths_h"),
            "downtime_pct": pct(p.get("downtime")), "frustration_h": p.get("frustration_h"), "fail_pct": pct(p.get("fail_rate")),
            "moments_h": p.get("moments_h"), "last_new_min": p.get("last_new_min"), "early_pct": pct(p.get("early_quit"))}


def persona_story(pid: str, p: dict, S: dict, exploits: list[str] | None = None) -> list[dict]:
    """[{texte, mesures}] : chaque phrase porte les mesures qu'elle cite."""
    v = _vals(p)
    v["failles"] = len(exploits or []) or None
    v["failles_noms"] = " ; ".join(exploits or []) or None
    voice = {**VOICES["defaut"], **VOICES.get(pid, {})}
    lo, hi = S.get("success_band", [0.55, 0.85])
    out = []

    def say(key, *fields):
        if all(v.get(f) is not None for f in fields):
            out.append({"texte": voice[key].format(**v), "mesures": {f: v[f] for f in fields}})

    say("intro", "play_min")
    if p.get("success") is not None and p["success"] < lo:
        say("dur", "success_pct", "deaths_h")
    elif p.get("success") is not None and p["success"] > hi:
        say("facile", "success_pct")
    if (p.get("downtime") or 0) > S.get("downtime_max", 0.25):
        say("ennui", "downtime_pct")
    if (p.get("frustration_h") or 0) > S.get("frustration_per_hour_max", 6) or (p.get("fail_rate") or 0) > S.get("fail_rate_max", 0.3):
        say("frustre", "frustration_h", "fail_pct")
    if pid == "streamer" or (p.get("moments_h") or 0) < S.get("moments_per_hour_min", 4):
        say("moments", "moments_h")
    if p.get("last_new_min") and p.get("play_min") and p["play_min"] > 2 * p["last_new_min"]:
        say("epuise", "last_new_min")
    if (p.get("early_quit") or 0) > S.get("early_quit_max", 0.3):
        say("quitte", "early_pct")
    if "faille" in voice:
        say("faille", "failles", "failles_noms")
    if len(out) <= 1 and not v["failles"]:
        say("ok")
    return out


def stories(analysis: dict, S: dict) -> dict[str, list[dict]]:
    by_p: dict[str, list[str]] = {}
    for x in analysis.get("exploits", []):
        pid = next((b["persona"] for uid, b in analysis.get("bots", {}).items() if uid.endswith("/" + str(x.get("bot")))), None)
        if pid and x.get("what") not in by_p.setdefault(pid, []):
            by_p[pid].append(str(x.get("what")))
    return {pid: persona_story(pid, p, S, by_p.get(pid)) for pid, p in analysis.get("personas", {}).items()}
