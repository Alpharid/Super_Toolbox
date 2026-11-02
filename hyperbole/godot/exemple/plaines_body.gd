extends HyperboleBody
## Le Corps des Plaines : « aller » pousse le stick vers le lieu jusqu'à y être ; « fouiller » appuie sur l'action.

var target := Vector2.ZERO
var verb := ""
var until := 0.0


func perform(option: Dictionary, t: float) -> void:
	verb = str(option.get("verb"))
	max_s = 20.0
	if verb == "aller":
		target = (me.get_parent() as Node).ZONES[str(option["area"])]
	elif verb == "fouiller":
		pad.press(&"interact", 0.2)
		until = t + 3.0
	else:
		until = t + 5.0


func update(t: float, _delta: float) -> void:
	if verb == "aller":
		var to: Vector2 = target - (me as Node2D).global_position
		if to.length() < 30.0:
			var hero: Node = me
			var first: bool = not hero.visited.has(target)
			hero.visited[target] = true
			for z: String in hero.get_parent().ZONES:
				if hero.get_parent().ZONES[z] == target and first and z != "camp":
					hero.einherjar.progress(z)
			finish(true, 0.3, first)
			return
		pad.set_axis(&"move_x", to.normalized().x)
		pad.set_axis(&"move_y", to.normalized().y)
	elif t >= until:
		if verb == "fouiller":
			var ok: bool = randf() < 0.7
			if ok:
				me.einherjar.gain("trouvaille", 1, "fouille")
			finish(ok, 0.25 if ok else 0.0, false, "" if ok else "rate")
		else:
			finish(true, 0.05)


func wants_to_move() -> bool:
	return verb == "aller" and running
