# Hyperbole pour Godot 4.7

L'addon `addons/hyperbole/` (aucune compilation, GDScript typé). L'exemple `exemple/` (« Les Plaines ») montre une
intégration complète : `python ../hyperbole.py lancer exemple/mission.json --ouvrir` depuis ce dossier.

## Les pièces

| Classe | Rôle | Le jeu… |
|---|---|---|
| `HyperboleChamber` (Node) | lit le contrat (`--hyperbole=<chamber.json>`), règle le temps, fait apparaître les Einherjar, mesure la perf, obéit au fichier stop | l'ajoute à la scène de chambre et crée les personnages (`_spawn_einherjar` ou signal `einherjar_requested`) |
| `HyperboleEinherjar` (Node) | relie Tête + Sens + Corps + journal ; détecte seul les blocages | l'ajoute au personnage, appelle `setup()` ; signale `death()`, `progress()`, `gain()`, `encounter()`, `moment()`, `exploit()` |
| `HyperboleSenses` | **la seule porte** vers le jeu : `options()`, `perceive()`, `position()`, `area()` ; aides `can_see_3d/2d` (cône + rayon), `hears()` | en fait une sous-classe |
| `HyperboleBody` | option → **entrées** sur `pad` (`perform`, `update`, `finish`) | en fait une sous-classe |
| `HyperboleVirtualPad` | une manette par bot, même API que `Input` (`is_action_pressed`, `get_vector`…) | son contrôleur lit `source` (= `Input` pour un humain, le pad pour un bot) |
| `HyperboleHead` | la Tête (utility AI, profil, apprentissage, ennui, frustration, lobby) | rien : ne pas la modifier par jeu (régler les profils) |
| `HyperboleJournal` | écrit le JSONL | rien |

## Brancher son jeu (4 étapes)

1. **Une source d'entrées par personnage.** Là où le contrôleur lit `Input`, lire une variable :
   ```gdscript
   var source: Variant = Input   # le bot remplace par son HyperboleVirtualPad
   func _physics_process(_d):
       var dir: Vector2 = source.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
       if source.is_action_just_pressed(&"grab"): _grab()
   ```
   C'est ce qui garantit « sans triche » : un bot ne peut faire que ce que les touches font.
2. **Une scène de chambre** (`res://hyperbole/chambre.tscn`) : le niveau + un `HyperboleChamber` dont `_spawn_einherjar`
   crée le personnage, ajoute un `HyperboleEinherjar`, appelle `e.setup(chamber, entry, MesSens.new(perso), MonCorps.new(perso))`
   et branche `perso.source = body.pad`. Renseigner `milestones` (les étapes du jeu).
3. **Les Sens** : `options()` liste ce qu'un joueur peut faire d'où il est, avec ce qu'il en perçoit (`risk` estimé de
   l'écran, `hint` si un texte y pousse, `wiki` pour ce qu'un joueur informé saurait). `perceive()` donne les signaux
   (`cues`) que sa caméra et ses oreilles captent. **Tout accès au jeu se fait ici**, avec les aides de perception honnête.
4. **Le Corps** : `perform()` commence le geste avec le pad (pousser le stick vers un point, viser, appuyer),
   `update()` le poursuit, `finish(ok, reward, novel, reason)` le termine. Raté sans effet : `reason = "no_effect"`.

Puis la mission (`missions/modele-godot.json`) :

```json
"cmd": ["C:/Godot/Godot_v4.7.2-stable_win64_console.exe", "--headless", "--fixed-fps", "60",
        "--path", "..", "res://hyperbole/chambre.tscn", "--", "--hyperbole={chamber_json}"]
```

`--fixed-fps 60` : chaque image avance de 1/60 s de jeu, et les images ne sont plus bridées : c'est l'accélération
(x90 à x200 mesurés sur l'exemple). Sans lui, la chambre tourne en temps réel (elle le signale). `lint` dans la mission :
`"fichiers": ["hyperbole/tete/**/*.gd"]`, `"autorises": ["*senses*.gd", "*body*.gd"]`.

## Pièges

- `Input` est global au processus : plusieurs bots dans une chambre = un pad chacun, jamais `Input.action_press`.
- Le hasard du jeu doit suivre la graine (la chambre appelle `seed()` ; les `RandomNumberGenerator` du jeu aussi, sinon
  `rejouer` ne rejoue pas la même partie).
- Les Sens ne renvoient que du perceptible : pas de `get_tree().get_nodes_in_group("ennemis")` dans la Tête (le lint
  le refuse), seulement dans les Sens, filtré par `can_see_3d`.
- Réseau : la voie `reel` (x1) avec un processus par client ; ne pas conclure d'un bug réseau vu en accéléré.
