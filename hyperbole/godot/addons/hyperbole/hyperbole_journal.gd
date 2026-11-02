class_name HyperboleJournal
extends RefCounted
## Le journal d'une chambre : un événement JSON par ligne (contrat : Super_Toolbox/hyperbole/docs/PROTOCOLE.md).
## Un seul écrivain par fichier. t_game vient de la chambre (secondes de jeu), t_wall de l'horloge réelle.

var world: String = ""
var _file: FileAccess
var _t0_usec: int = 0
var _clock: Callable
var _since_flush: int = 0


func _init(path: String, world_id: String, clock: Callable) -> void:
	world = world_id
	_clock = clock
	_t0_usec = Time.get_ticks_usec()
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	_file = FileAccess.open(path, FileAccess.READ_WRITE) if FileAccess.file_exists(path) else FileAccess.open(path, FileAccess.WRITE)
	if _file == null:
		push_error("Hyperbole : journal impossible à ouvrir : %s" % path)
		return
	_file.seek_end()


func t_wall() -> float:
	return float(Time.get_ticks_usec() - _t0_usec) / 1000000.0


func write(kind: String, data: Dictionary = {}) -> void:
	if _file == null:
		return
	var ev: Dictionary = {"t_game": snappedf(float(_clock.call()), 0.001), "t_wall": snappedf(t_wall(), 0.001), "world": world, "kind": kind}
	for k: Variant in data:
		if data[k] != null:
			ev[k] = data[k]
	_file.store_line(JSON.stringify(ev))
	_since_flush += 1
	if _since_flush >= 64:
		flush()


func flush() -> void:
	if _file != null:
		_file.flush()
		_since_flush = 0


func close() -> void:
	if _file != null:
		_file.flush()
		_file.close()
		_file = null


## Une position Vector2/Vector3 en tableau JSON arrondi (le champ « pos » du contrat).
static func pos(v: Variant) -> Array:
	if v is Vector3:
		return [snappedf(v.x, 0.01), snappedf(v.y, 0.01), snappedf(v.z, 0.01)]
	if v is Vector2:
		return [snappedf(v.x, 0.01), snappedf(v.y, 0.01)]
	return []
