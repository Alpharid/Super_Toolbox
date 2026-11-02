class_name HyperboleSenses
extends RefCounted
## La façade « ce qu'un joueur peut savoir » : SEULE porte entre un Einherjar et le jeu (avec son Corps).
## Le jeu en fait une sous-classe et remplit options() et perceive() avec ce que le joueur VOIT et ENTEND :
## ce que sa caméra montre (cône + ligne de vue), les sons qu'il entend (distance, occlusion), le HUD, son propre corps.
## Jamais : l'état interne des autres, les tables cachées, les positions hors de vue. `hyperbole lint` vérifie que la
## Tête ne passe que par ici (les fichiers *senses*.gd et *body*.gd sont les seuls autorisés à toucher le jeu).

var me: Node = null  ## le personnage contrôlé par ce bot


func _init(my_character: Node = null) -> void:
	me = my_character


## Ce que le joueur pourrait faire maintenant, en options pour la Tête (voir hyperbole_head.gd pour les champs).
func options() -> Array[Dictionary]:
	return []


## Ce que le bot perçoit à cet instant : {"cues": ["lueur_rouge", ...], "hp": 0.4 (ressenti), ...}.
func perceive() -> Dictionary:
	return {}


## Sa propre position (pour le journal : blocages, couverture, téléportation).
func position() -> Variant:
	if me is Node3D:
		return (me as Node3D).global_position
	if me is Node2D:
		return (me as Node2D).global_position
	return null


## Le lieu (zone nommée) où il se trouve, s'il est affiché au joueur.
func area() -> String:
	return ""


# ---------- aides de perception honnête ----------

## Vrai si la cible est dans le cône de vue et que rien ne la cache (rayon physique).
static func can_see_3d(eye: Node3D, target: Vector3, cone_deg: float = 90.0, max_range: float = 60.0, exclude: Array[RID] = []) -> bool:
	var to := target - eye.global_position
	if to.length() > max_range:
		return false
	var fwd := -eye.global_transform.basis.z
	if fwd.angle_to(to) > deg_to_rad(cone_deg * 0.5):
		return false
	var q := PhysicsRayQueryParameters3D.create(eye.global_position, target)
	q.exclude = exclude
	var hit := eye.get_world_3d().direct_space_state.intersect_ray(q)
	return hit.is_empty() or (hit["position"] as Vector3).distance_to(target) < 0.5


static func can_see_2d(eye: Node2D, target: Vector2, cone_deg: float = 360.0, max_range: float = 800.0, exclude: Array[RID] = []) -> bool:
	var to := target - eye.global_position
	if to.length() > max_range:
		return false
	if cone_deg < 360.0 and absf(Vector2.RIGHT.rotated(eye.global_rotation).angle_to(to)) > deg_to_rad(cone_deg * 0.5):
		return false
	var q := PhysicsRayQueryParameters2D.create(eye.global_position, target)
	q.exclude = exclude
	var hit := eye.get_world_2d().direct_space_state.intersect_ray(q)
	return hit.is_empty() or (hit["position"] as Vector2).distance_to(target) < 4.0


## Intensité perçue d'un son (0 = inaudible) selon la distance ; le jeu ajoute son occlusion s'il en a une.
static func hears(listener: Vector3, source: Vector3, loudness: float = 1.0, reach: float = 40.0) -> float:
	var d := listener.distance_to(source)
	return clampf(loudness * (1.0 - d / reach), 0.0, 1.0)
