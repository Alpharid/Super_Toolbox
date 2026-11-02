class_name HyperboleChamber
extends Node
## La chambre côté Godot : lit le contrat de Mr. Popo (chamber.json), règle le temps, fait apparaître les Einherjar,
## mesure la perf, obéit au fichier stop et quitte proprement. Sans contrat (--hyperbole=… absent), elle ne fait rien :
## on peut la laisser dans la scène, le jeu tourne normalement.
##
## Lancer en chambre accélérée (le plus rapide possible, pas de temps fixe perdu) :
##   godot --headless --fixed-fps 60 --path <projet> res://hyperbole/chambre.tscn -- --hyperbole=<chamber.json>
## --fixed-fps donne un delta fixe (1/60 s de jeu par image) et débride les images : la vitesse = ce que le CPU tient.
## Vitesse fixe (vitesse: 4 dans la mission) : Engine.time_scale, et plus de pas physiques par seconde.
##
## Le jeu fait une sous-classe (ou se connecte au signal) pour créer le personnage de chaque Einherjar :
##   func _spawn_einherjar(entry: Dictionary) -> void:
##       var hero := HERO.instantiate(); add_child(hero)
##       var e := HyperboleEinherjar.new(); hero.add_child(e)
##       e.setup(self, entry, MySenses.new(hero), MyBody.new(hero)); hero.input_source = e.pad()

signal einherjar_requested(entry: Dictionary)
signal finished(reason: String)

@export var perf_every_s: float = 30.0  ## une ligne « perf » toutes les N secondes de jeu
@export var stagger_s: float = 5.0  ## arrivées étalées (secondes de jeu entre deux Einherjar)
@export var milestones: PackedStringArray = []  ## étapes du jeu : le rapport montre aussi celles que personne n'atteint

var active: bool = false
var contract: Dictionary = {}
var journal: HyperboleJournal
var rng := RandomNumberGenerator.new()
var t_game: float = 0.0
var einherjar: Array[HyperboleEinherjar] = []

var _to_spawn: Array = []
var _next_spawn: float = 0.0
var _next_perf: float = 0.0
var _wall_check: float = 0.0
var _done: bool = false
var _speed_checked: bool = false


func _ready() -> void:
	var path := ""
	for a: String in OS.get_cmdline_user_args():
		if a.begins_with("--hyperbole="):
			path = a.trim_prefix("--hyperbole=")
	if path == "":
		path = OS.get_environment("HYPERBOLE_CHAMBER")
	if path == "" or not FileAccess.file_exists(path):
		return
	contract = JSON.parse_string(FileAccess.get_file_as_string(path))
	active = true
	rng.seed = int(contract.get("seed", 1))
	seed(int(contract.get("seed", 1)))  # le hasard global du jeu suit la graine (rejouer = même partie)
	process_mode = Node.PROCESS_MODE_ALWAYS
	var speed: Variant = contract.get("speed")
	Engine.max_fps = 0
	if speed is float or speed is int:
		Engine.time_scale = float(speed)
		Engine.physics_ticks_per_second = int(ProjectSettings.get_setting("physics/common/physics_ticks_per_second", 60))
		Engine.max_physics_steps_per_frame = maxi(8, int(ceil(float(speed))) * 2)
	journal = HyperboleJournal.new(str(contract["journal"]), str(contract["world"]), func() -> float: return t_game)
	journal.write("chamber_start", {"seed": int(contract.get("seed", 1)), "mode": contract.get("mode"), "speed": speed,
		"engine": "godot %s" % Engine.get_version_info()["string"], "params": contract.get("params", {}),
		"lobby": (contract.get("lobby", []) as Array).map(func(b: Dictionary) -> String: return str(b["persona_id"])),
		"milestones": Array(milestones) if not milestones.is_empty() else null})
	_to_spawn = (contract.get("lobby", []) as Array).duplicate()


func _physics_process(delta: float) -> void:
	if not active or _done:
		return
	t_game += delta
	while not _to_spawn.is_empty() and t_game >= _next_spawn:
		var entry: Dictionary = _to_spawn.pop_front()
		_spawn_einherjar(entry)
		_next_spawn = t_game + stagger_s
	if t_game >= _next_perf:
		_next_perf = t_game + perf_every_s
		_perf()
	_wall_check += delta
	if not _speed_checked and t_game > 10.0:
		_speed_checked = true  # « max » sans --fixed-fps sur la ligne de commande = temps réel : le dire
		if str(contract.get("speed")) == "max" and t_game / maxf(journal.t_wall(), 0.001) < 1.5:
			push_warning("Hyperbole : vitesse « max » mais la chambre tourne en temps réel : ajouter --fixed-fps 60 à la commande.")
	if _wall_check >= 1.0:
		_wall_check = 0.0
		if FileAccess.file_exists(str(contract["stop_file"])):
			finish("stop")
		elif journal.t_wall() > float(contract.get("wall_seconds", 600)):
			finish("durée réelle")
		elif contract.get("game_seconds_max") != null and t_game > float(contract["game_seconds_max"]):
			finish("durée de jeu")
		elif _to_spawn.is_empty() and not einherjar.is_empty() and einherjar.all(func(e: HyperboleEinherjar) -> bool: return e.gone):
			finish("tous partis")
		journal.flush()


## À surcharger (ou se connecter à einherjar_requested). Doit créer le personnage, un HyperboleEinherjar et l'enregistrer.
func _spawn_einherjar(entry: Dictionary) -> void:
	einherjar_requested.emit(entry)


func register(e: HyperboleEinherjar) -> void:
	einherjar.append(e)


func _perf() -> void:
	journal.write("perf", {
		"fps": Performance.get_monitor(Performance.TIME_FPS),
		"proc_ms": snappedf(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, 0.01),
		"phys_ms": snappedf(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0, 0.01),
		"mem_static_mb": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.01),
		"objects": Performance.get_monitor(Performance.OBJECT_COUNT),
		"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"orphans": Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
		"resources": Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
		"bots": einherjar.filter(func(e: HyperboleEinherjar) -> bool: return not e.gone).size()})


func finish(reason: String) -> void:
	if _done:
		return
	_done = true
	for e: HyperboleEinherjar in einherjar:
		if not e.gone:
			e.leave_game("fin_de_chambre")
	journal.write("chamber_end", {"reason": reason})
	journal.close()
	finished.emit(reason)
	get_tree().quit()
