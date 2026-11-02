extends HyperboleSenses
## Ce qu'un joueur des Plaines sait : où il est (la zone affichée), les lieux sur la carte, son sac.

var zones: Dictionary


func _init(hero: Node, zone_map: Dictionary) -> void:
	super(hero)
	zones = zone_map


func area() -> String:
	for z: String in zones:
		if (me as Node2D).global_position.distance_to(zones[z]) < 60.0:
			return z
	return "chemin"


func options() -> Array[Dictionary]:
	var here := area()
	var out: Array[Dictionary] = []
	for z: String in zones:
		if z != here:
			out.append({"id": "aller:" + z, "verb": "aller", "area": z, "tags": {"explore": 0.8, "progress": 0.6 if z != "camp" else 0.0}})
	if here != "chemin":
		out.append({"id": "fouiller:" + here, "verb": "fouiller", "area": here, "tags": {"collect": 1.0, "explore": 0.2}})
	out.append({"id": "se_reposer", "verb": "repos", "area": here, "tags": {"rest": 0.6}})
	return out
