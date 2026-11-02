extends Node2D
## « Les Plaines » : trois lieux (camp, puits, ruines), des héros qui s'y déplacent avec une manette.
## Un mur invisible planté devant les ruines (BUG voulu) : les Einherjar doivent le signaler en « stuck ».

const ZONES := {"camp": Vector2(100, 300), "puits": Vector2(500, 120), "ruines": Vector2(820, 420)}
const HERO := preload("res://exemple/hero.gd")
const SENSES := preload("res://exemple/plaines_senses.gd")
const BODY := preload("res://exemple/plaines_body.gd")

var chamber: HyperboleChamber


func _ready() -> void:
	_wall(Rect2(0, -20, 960, 20)); _wall(Rect2(0, 600, 960, 20)); _wall(Rect2(-20, 0, 20, 600)); _wall(Rect2(960, 0, 20, 600))
	_wall(Rect2(700, 300, 16, 220))  # le mur invisible planté sur le chemin des ruines
	chamber = HyperboleChamber.new()
	chamber.stagger_s = 2.0
	chamber.milestones = PackedStringArray(["puits", "ruines"])
	chamber.einherjar_requested.connect(_spawn)
	add_child(chamber)


func _wall(r: Rect2) -> void:
	var b := StaticBody2D.new()
	var c := CollisionShape2D.new()
	var s := RectangleShape2D.new()
	s.size = r.size
	c.shape = s
	b.position = r.position + r.size / 2
	b.add_child(c)
	add_child(b)


func _spawn(entry: Dictionary) -> void:
	var hero: CharacterBody2D = HERO.new()
	hero.position = ZONES["camp"] + Vector2(randf_range(-20, 20), randf_range(-20, 20))
	add_child(hero)
	var e := HyperboleEinherjar.new()
	hero.add_child(e)
	var body: HyperboleBody = BODY.new(hero)
	e.setup(chamber, entry, SENSES.new(hero, ZONES), body)
	hero.source = body.pad
	hero.einherjar = e
