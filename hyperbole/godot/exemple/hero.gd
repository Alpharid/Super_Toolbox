extends CharacterBody2D
## Le personnage : il lit SA source d'entrées (Input pour un humain, la manette virtuelle pour un Einherjar).

var source: Variant = Input
var einherjar: HyperboleEinherjar = null
var visited: Dictionary = {}


func _ready() -> void:
	var c := CollisionShape2D.new()
	var s := CircleShape2D.new()
	s.radius = 8.0
	c.shape = s
	add_child(c)


func _physics_process(_delta: float) -> void:
	var dir: Vector2 = source.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
	velocity = dir * 140.0
	move_and_slide()
