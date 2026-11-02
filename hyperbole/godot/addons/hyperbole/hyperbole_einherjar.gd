class_name HyperboleEinherjar
extends Node
## Un Einherjar dans une chambre : relie sa Tête (décide), ses Sens (perçoit), son Corps (entrées) et le journal.
## Le jeu l'ajoute comme enfant de son personnage (ou n'importe où), puis appelle report() quand le résultat d'un geste
## est connu, et les aides (death, progress, gain…) quand le jeu le constate. Tout part dans le journal de la chambre.

var chamber: HyperboleChamber
var entry: Dictionary
var bot: String = ""
var persona_id: String = ""
var head: HyperboleHead
var senses: HyperboleSenses
var body: HyperboleBody
var gone: bool = false

var stuck_after_s: float = 6.0   ## veut bouger mais n'a pas bougé de stuck_epsilon pendant ce temps -> « stuck »
var stuck_epsilon: float = 0.3

var _joined_t: float = 0.0
var _pending: Dictionary = {}
var _perform_at: float = -1.0
var _current: Dictionary = {}
var _current_t: float = 0.0
var _last_pos: Variant = null
var _still_since: float = -1.0
var _stuck_logged: bool = false
var _rest_until: float = 0.0


func setup(chamber_node: HyperboleChamber, lobby_entry: Dictionary, my_senses: HyperboleSenses, my_body: HyperboleBody) -> void:
	chamber = chamber_node
	entry = lobby_entry
	bot = str(entry["bot"])
	persona_id = str(entry["persona_id"])
	senses = my_senses
	body = my_body
	head = HyperboleHead.new(bot, entry["persona"], chamber.rng.randi(), chamber.contract.get("lobby_knowledge", {}))
	head.event.connect(func(kind: String, data: Dictionary) -> void: chamber.journal.write(kind, data))
	_joined_t = chamber.t_game
	chamber.register(self)
	log_event("bot_join", {"persona": persona_id, "session_planned_s": roundi(head.session_s)})


func pad() -> HyperboleVirtualPad:
	return body.pad


func _physics_process(delta: float) -> void:
	if gone or chamber == null:
		return
	body.pad.tick(delta)
	var t: float = chamber.t_game
	var leave := head.wants_to_leave(t - _joined_t)
	if leave != "":
		leave_game(leave)
		return
	_watch_stuck(t)
	if body.running:
		body.update(t, delta)
		if body.running and t - body.started_t > body.max_s:
			body.finish(false, -0.2, false, "timeout")
	if body.done != null:
		var d: Dictionary = body.done
		body.done = null
		report(bool(d["ok"]), float(d["reward"]), bool(d["novel"]), str(d["reason"]))
		_rest_until = t + 0.05
		return
	if body.running or t < _rest_until:
		return
	if _perform_at >= 0.0:
		if t >= _perform_at:
			_perform_at = -1.0
			_current = _pending
			_current_t = t
			log_event("act", {"verb": _current.get("verb"), "area": _current.get("area", senses.area()), "inputs": _current.get("id"),
				"pos": HyperboleJournal.pos(senses.position())})
			body.begin(t)
			body.perform(_current, t)
		return
	_think(t)


func _think(t: float) -> void:
	var p: Dictionary = senses.perceive()
	for cue: Variant in p.get("cues", []):
		head.see_cue(str(cue), t)
	var d: Dictionary = head.decide(senses.options(), t)
	var o: Dictionary = d["option"]
	if o.is_empty():
		_rest_until = t + 1.0
		return
	_pending = o
	_perform_at = t + float(d["delay"])


## Le jeu dit ce qu'a donné le geste en cours : réussi ou non, ce que le joueur y gagne (-1..1), un résultat nouveau.
## reason (si raté) : « rate », « refus », « no_effect » (geste sans effet), « bloque »…
func report(ok: bool, reward: float = 0.0, novel: bool = false, reason: String = "", cues_hurt: Array = []) -> void:
	var t: float = chamber.t_game
	if not ok:
		log_event("fail", {"verb": _current.get("verb"), "area": _current.get("area"), "reason": reason if reason != "" else null})
	for cue: Variant in cues_hurt:
		head.see_cue(str(cue), t, true)
	head.feedback(_current, ok, reward, t, maxf(0.1, t - _current_t), novel)


func _watch_stuck(t: float) -> void:
	var p: Variant = senses.position()
	if p == null:
		return
	if _last_pos != null and body.wants_to_move() and (p - _last_pos).length() < stuck_epsilon * get_physics_process_delta_time() * 60.0:
		if _still_since < 0.0:
			_still_since = t
		elif t - _still_since > stuck_after_s and not _stuck_logged:
			_stuck_logged = true
			log_event("stuck", {"pos": HyperboleJournal.pos(p), "intent": _current.get("id"), "area": senses.area(),
				"duration": snappedf(t - _still_since, 0.1)})
	else:
		_still_since = -1.0
		_stuck_logged = false
	_last_pos = p


# ---------- aides : ce que le jeu constate ----------
func log_event(kind: String, data: Dictionary = {}) -> void:
	var d := data.duplicate()
	d["bot"] = bot
	chamber.journal.write(kind, d)


func death(cause: String, doing: String = "", blame: String = "") -> void:
	log_event("death", {"cause": cause, "doing": doing if doing != "" else _current.get("verb"), "pos": HyperboleJournal.pos(senses.position()),
		"area": senses.area(), "blame": blame if blame != "" else null})


func progress(milestone: String) -> void:
	log_event("progress", {"milestone": milestone})


func gain(resource: String, amount: float, source: String = "", total: Variant = null) -> void:
	log_event("gain", {"resource": resource, "amount": amount, "source": source, "total": total})


func spend(resource: String, amount: float, sink: String = "", total: Variant = null) -> void:
	log_event("spend", {"resource": resource, "amount": amount, "sink": sink, "total": total})


func encounter(threat: String, outcome: String) -> void:
	log_event("encounter", {"threat": threat, "outcome": outcome, "pos": HyperboleJournal.pos(senses.position())})


func moment(what: String, intensity: float = 0.5) -> void:
	log_event("moment", {"what": what, "intensity": intensity, "pos": HyperboleJournal.pos(senses.position())})


func exploit(what: String, steps: Array) -> void:
	head.found_exploit(_current, what, steps)


func leave_game(reason: String) -> void:
	if gone:
		return
	gone = true
	body.pad.release_all()
	log_event("bot_leave", {"reason": reason})
