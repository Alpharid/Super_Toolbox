class_name HyperboleVirtualPad
extends RefCounted
## La manette d'un Einherjar : les MÊMES actions que le joueur (InputMap), mais propres à ce bot (l'Input global est
## partagé par tout le processus, donc inutilisable pour plusieurs bots dans une chambre).
## Le contrôleur du personnage lit « source.is_action_pressed(...) » où source = Input pour un humain, ce pad pour un bot :
##     var source: Variant = pad if pad != null else Input
## Ainsi le bot ne peut faire que ce qu'un joueur fait : appuyer sur des actions, pousser des axes, viser.

var _held: Dictionary = {}     # action -> secondes restantes (INF = maintenu)
var _just: Dictionary = {}     # action -> true pendant une image
var _axes: Dictionary = {}     # nom -> float
var aim: Vector2 = Vector2.ZERO  # regard (souris/stick droit), en radians ou pixels selon le jeu


func press(action: StringName, seconds: float = 0.1) -> void:
	if not _held.has(action):
		_just[action] = true
	_held[action] = seconds


func hold(action: StringName) -> void:
	press(action, INF)


func release(action: StringName) -> void:
	_held.erase(action)


func set_axis(axis: StringName, value: float) -> void:
	_axes[axis] = clampf(value, -1.0, 1.0)


func release_all() -> void:
	_held.clear()
	_axes.clear()


## À appeler une fois par image physique (HyperboleEinherjar le fait).
func tick(delta: float) -> void:
	_just.clear()
	for a: Variant in _held.keys():
		_held[a] = float(_held[a]) - delta
		if float(_held[a]) <= 0.0:
			_held.erase(a)


# --- même API que Input ---
func is_action_pressed(action: StringName, _exact: bool = false) -> bool:
	return _held.has(action)


func is_action_just_pressed(action: StringName, _exact: bool = false) -> bool:
	return _just.has(action)


func get_action_strength(action: StringName, _exact: bool = false) -> float:
	return 1.0 if _held.has(action) else 0.0


func get_axis(negative: StringName, positive: StringName) -> float:
	return get_action_strength(positive) - get_action_strength(negative)


func get_vector(neg_x: StringName, pos_x: StringName, neg_y: StringName, pos_y: StringName, _deadzone: float = -1.0) -> Vector2:
	var v := Vector2(get_axis(neg_x, pos_x), get_axis(neg_y, pos_y))
	if _axes.has(&"move_x") or _axes.has(&"move_y"):
		v = Vector2(float(_axes.get(&"move_x", 0.0)), float(_axes.get(&"move_y", 0.0)))
	return v.limit_length(1.0)
