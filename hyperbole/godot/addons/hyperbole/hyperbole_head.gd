class_name HyperboleHead
extends RefCounted
## La Tête d'un Einherjar (même logique que einherjar/head.py) : utility AI réglée par le profil.
## Elle note les OPTIONS qu'un joueur verrait, apprend en jouant, s'ennuie, s'agace, sait qui est qui dans le lobby.
## Elle ne lit jamais le jeu : seulement ce que ses Sens lui donnent (le contrôle `hyperbole lint` le vérifie).
##
## Une option (Dictionary) : id, verb, tags {tag: poids}, area, risk (0-1 perçu), target (bot visé), wiki {value},
## hint (texte affiché), group (bool), break (bool, cas limite), disrupt (bool, nuisance).

signal event(kind: String, data: Dictionary)

var bot: String
var persona: Dictionary
var lobby: Dictionary = {}
var rng := RandomNumberGenerator.new()
var knows_wiki: bool = false
var learned: Dictionary = {}       # "verb|area" -> valeur apprise ; "verb|area#contexte" -> la même, dans ce contexte
var context: String = ""          # ce que le bot ressent en décidant (perceive()["context"]) : « faim », « calme »…
var tried: Dictionary = {}         # id -> nombre d'essais
var boredom: float = 0.0
var frustration: float = 0.0
var frustration_episodes: int = 0
var bored_episodes: int = 0
var fail_streak: int = 0
var last_option: String = ""
var last_verb: String = ""
var repeat: int = 0
var nuisance: Array[float] = []
var exploits_found: Dictionary = {}
var cue_seen: Dictionary = {}      # cue -> [t premier, vus, suivis d'une conséquence]
var cues_learned: Dictionary = {}
var session_s: float = 3600.0
var quit_reason: String = ""


func _init(bot_id: String, persona_dict: Dictionary, seed_value: int, lobby_knowledge: Dictionary) -> void:
	bot = bot_id
	persona = persona_dict
	rng.seed = seed_value
	for k: Variant in lobby_knowledge:
		if str(k) != bot:
			lobby[str(k)] = str(lobby_knowledge[k])
	var tools: Variant = persona.get("tools")
	knows_wiki = str(persona.get("knowledge", "partial")) == "wiki" or (tools is Array and (tools as Array).has("wiki"))
	var mins: Array = (persona.get("session", {}) as Dictionary).get("minutes", [45, 120])
	session_s = rng.randf_range(float(mins[0]), float(mins[1])) * 60.0


func _p(key: String, default_value: float = 0.5) -> float:
	return float(persona.get(key, default_value))


func _drive(tag: String) -> float:
	return float((persona.get("drives", {}) as Dictionary).get(tag, 0.0)) + float((persona.get("goals", {}) as Dictionary).get(tag, 0.0))


func _skill(key: String, default_value: float) -> float:
	return float((persona.get("skill", {}) as Dictionary).get(key, default_value))


func score(o: Dictionary, t: float) -> float:
	var s: float = 0.0
	var tags: Variant = o.get("tags", {})
	if tags is Dictionary:
		for tag: Variant in tags:
			s += float(tags[tag]) * _drive(str(tag))
	elif tags is Array:
		for tag: Variant in tags:
			s += _drive(str(tag))
	var id := str(o.get("id", ""))
	var key := "%s|%s" % [o.get("verb", ""), o.get("area", "")]
	var novelty: float = 1.0 / (1.0 + float(tried.get(id, 0)))
	s += _p("curiosity") * novelty * (0.6 + boredom)
	var value: float = float(learned.get(key, 0.0))
	if context != "" and learned.has(key + "#" + context):
		value = 0.4 * value + float(learned[key + "#" + context])  # ce qui a payé dans la même situation compte d'abord
	s += value * (0.4 + _drive("mastery"))
	s -= float(o.get("risk", 0.0)) * (1.0 - _p("risk")) * 1.2
	if knows_wiki and o.get("wiki") is Dictionary:
		s += 0.5 * float((o["wiki"] as Dictionary).get("value", 0.0))
	if o.get("hint") and rng.randf() < _p("reads_text"):
		s += 0.15
	if id == last_option:
		s -= repeat * 0.05 * (1.2 - _p("patience")) * (0.5 + boredom)
	if str(o.get("verb", "")) == "aller" and last_verb == "aller":
		s -= 0.5 * (0.5 + _p("patience"))
	var target := str(o.get("target", ""))
	if target != "" and lobby.get(target, "") == "saboteur":
		s -= 0.6 * (1.0 - _p("risk"))
	if o.get("group", false) and lobby.values().has("leader"):
		s += 0.3 * (1.0 - _drive("mastery"))
	if o.get("disrupt", false):
		var cap: float = float(persona.get("nuisance_cap_per_hour", 0) if persona.get("nuisance_cap_per_hour") != null else 0)
		var recent: int = nuisance.filter(func(x: float) -> bool: return t - x < 3600.0).size()
		if str(persona.get("social_role", "none")) != "saboteur" or recent >= cap:
			return -9.0
	if o.get("break", false):
		if exploits_found.has(key):
			return -9.0
		s += (_drive("break") - 0.5) * 1.6
	s += rng.randfn(0.0, 0.05 + _skill("mistake_rate", 0.08))
	return s


## Renvoie {"option": Dictionary (vide si rien), "delay": secondes de réaction}.
func decide(options: Array, t: float) -> Dictionary:
	if options.is_empty():
		return {"option": {}, "delay": 0.0}
	var chosen: Dictionary
	var best: float = -INF
	if rng.randf() < _skill("mistake_rate", 0.08):
		chosen = options[rng.randi_range(0, options.size() - 1)]
		best = NAN
	else:
		for o: Dictionary in options:
			var sc := score(o, t)
			if sc > best:
				best = sc
				chosen = o
		if best <= -9.0:
			return {"option": {}, "delay": 0.0}
	var id := str(chosen.get("id", ""))
	repeat = repeat + 1 if id == last_option else 0
	last_option = id
	last_verb = str(chosen.get("verb", ""))
	tried[id] = int(tried.get(id, 0)) + 1
	chosen["_context"] = context
	if chosen.get("disrupt", false):
		nuisance.append(t)
	event.emit("intent", {"bot": bot, "option": id, "score": null if is_nan(best) else snappedf(best, 0.001), "area": chosen.get("area")})
	var rms: float = _skill("reaction_ms", 350.0)
	return {"option": chosen, "delay": maxf(0.05, rng.randfn(rms, rms * 0.2) / 1000.0)}


## Après le geste : apprendre, s'ennuyer, s'agacer. reward : ce que le joueur perçoit (-1..1).
func feedback(o: Dictionary, ok: bool, reward: float, t: float, dt: float, novel_result: bool = false) -> void:
	var lr: float = _skill("learning_rate", 0.5) * 0.5
	var key := "%s|%s" % [o.get("verb", ""), o.get("area", "")]
	var value: float = reward if ok else -0.5
	learned[key] = (1.0 - lr) * float(learned.get(key, 0.0)) + lr * value
	var ctx := str(o.get("_context", ""))
	if ctx != "":
		learned[key + "#" + ctx] = (1.0 - lr) * float(learned.get(key + "#" + ctx, 0.0)) + lr * value
	if ok:
		fail_streak = 0
		frustration = maxf(0.0, frustration - 0.15)
	else:
		fail_streak += 1
		frustration += (0.25 + 0.1 * fail_streak) * (1.2 - _p("frustration_tolerance"))
	if frustration >= 1.0:
		frustration_episodes += 1
		event.emit("frustrated", {"bot": bot, "streak": fail_streak, "area": o.get("area")})
		frustration = 0.4
		if frustration_episodes > 2 + 8 * _p("frustration_tolerance"):
			quit_reason = "frustrated"
	var interest: float = reward + (0.5 if novel_result else 0.0)
	if interest < 0.15:
		boredom += dt / 60.0 * (1.1 - _p("boredom_tolerance")) * 0.6
	else:
		boredom = maxf(0.0, boredom - interest * 0.5)
	if boredom >= 1.0:
		bored_episodes += 1
		event.emit("bored", {"bot": bot, "duration": snappedf(60.0 * (1.2 - _p("boredom_tolerance")), 0.1), "area": o.get("area")})
		boredom = 0.3
		if bored_episodes > 2 + 6 * _p("boredom_tolerance"):
			quit_reason = "bored"


## Un signal perçu ; s'il précède souvent une conséquence, il est compris. Renvoie vrai s'il est compris.
func see_cue(cue: String, t: float, then_hurt: bool = false) -> bool:
	if cues_learned.has(cue):
		return true
	if not cue_seen.has(cue):
		cue_seen[cue] = [t, 0, 0]
	var seen: Array = cue_seen[cue]
	seen[1] = int(seen[1]) + 1
	if then_hurt:
		seen[2] = int(seen[2]) + 1
	var need: int = maxi(1, roundi(6.0 * (1.1 - _skill("learning_rate", 0.5))))
	if int(seen[2]) >= need:
		cues_learned[cue] = true
		event.emit("learn", {"bot": bot, "cue": cue, "after": snappedf(t - float(seen[0]), 0.1), "essais": seen[1]})
		return true
	return false


## Le fouineur reproduit une faille une fois, la signale, n'y revient plus.
func found_exploit(o: Dictionary, what: String, steps: Array) -> void:
	var key := "%s|%s" % [o.get("verb", ""), o.get("area", "")]
	if exploits_found.has(key):
		return
	exploits_found[key] = true
	event.emit("exploit", {"bot": bot, "what": what, "steps": steps, "area": o.get("area")})


func wants_to_leave(play_s: float) -> String:
	if quit_reason != "":
		return quit_reason
	if play_s >= session_s:
		return "session_end"
	return ""
