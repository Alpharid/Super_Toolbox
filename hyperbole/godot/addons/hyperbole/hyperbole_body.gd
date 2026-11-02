class_name HyperboleBody
extends RefCounted
## Le Corps : transforme l'option choisie par la Tête en ENTRÉES DE JOUEUR sur la manette virtuelle du bot.
## Le jeu en fait une sous-classe : perform() commence le geste (appuie sur des actions, pousse des axes, vise),
## update() le poursuit image par image (se diriger vers un point…), finish() le termine avec son résultat.
## Il ne modifie jamais l'état du jeu directement : il n'a que la manette, comme un joueur.

var pad := HyperboleVirtualPad.new()
var me: Node = null
var max_s: float = 30.0  ## un geste qui n'a pas fini après ce temps (s de jeu) est raté (« timeout »)
var done: Variant = null  ## null pendant le geste ; {ok, reward, novel, reason} à la fin
var running: bool = false
var started_t: float = 0.0


func _init(my_character: Node = null) -> void:
	me = my_character


## Commence le geste. À surcharger. Appeler finish() tout de suite pour un geste instantané.
func perform(_option: Dictionary, _t: float) -> void:
	finish(true)


## Poursuit le geste à chaque image physique. À surcharger pour les gestes qui durent (se déplacer, viser…).
func update(_t: float, _delta: float) -> void:
	pass


func begin(t: float) -> void:
	running = true
	done = null
	started_t = t


func finish(ok: bool, reward: float = 0.0, novel: bool = false, reason: String = "") -> void:
	running = false
	pad.release_all()
	done = {"ok": ok, "reward": reward, "novel": novel, "reason": reason}


## Le geste vise un déplacement (pour repérer les blocages : il veut avancer et ne bouge pas).
func wants_to_move() -> bool:
	return pad.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back") != Vector2.ZERO
