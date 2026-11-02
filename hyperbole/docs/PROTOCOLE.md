# Hyperbole — le contrat entre Mr. Popo et un jeu

Ce document suffit pour brancher **n'importe quel jeu** (Godot, C#, Unreal, Electron, Python…). Le jeu n'a que trois
choses à faire : lire le contrat d'une chambre, écrire un journal JSONL, obéir au fichier `stop`.

## 1. La chambre

Mr. Popo lance la commande `jeu.cmd` de la mission, une fois par chambre. Il y remplace :

| Gabarit | Valeur |
|---|---|
| `{chamber_json}` | chemin du contrat de cette chambre (aussi dans la variable d'environnement `HYPERBOLE_CHAMBER`) |
| `{seed}` `{world}` `{speed}` `{mode}` `{out_dir}` `{bots}` | raccourcis des champs du contrat |
| `{port}` | seulement avec `hyperbole.py pont` : le port TCP des têtes Python (§4) |

Le contrat (`chamber.json`) :

```json
{
  "hyperbole": 1, "run": "stryder_2026-11-05_041200", "world": "c1-l2", "cycle": 1,
  "seed": 1573429662, "mode": "chambre", "speed": "max",
  "wall_seconds": 900, "game_seconds_max": 14400,
  "variant": null, "params": {"difficulte": 1.0}, "twin_of": null,
  "journal": ".../chambres/c1-l2/journal.jsonl", "stop_file": ".../chambres/c1-l2/stop", "out_dir": ".../chambres/c1-l2",
  "lobby": [{"bot": "E201-tryhard", "persona_id": "tryhard", "persona": { "...profil complet résolu..." }}],
  "lobby_knowledge": {"E201-tryhard": "tryhard", "E202-saboteur": "saboteur"}
}
```

- **mode** : `chambre` (accélérée, pour l'équilibre, le fun et les bugs au long cours) ou `reel` (x1, pour le réseau).
  Un jeu en réseau ne s'accélère pas honnêtement (Guardians à x20 : des centaines de faux refus). Le mode `mixte` de
  la mission joue chaque lobby dans les deux voies, et le rapport signale ce qui n'apparaît qu'en accéléré.
- **speed** : `"max"` = aussi vite que le CPU le permet, avec un pas de temps fixe (Godot : `--fixed-fps 60`).
  Un nombre = multiple fixe du temps réel. La vitesse **mesurée** (t_game / t_wall) est dans le rapport ; on ne la promet pas.
- **seed** : tout le hasard du jeu doit en dépendre. Rejouer une chambre (`hyperbole.py rejouer`), c'est relancer avec la
  même graine, le même lobby et les mêmes params.
- **lobby_knowledge** : chaque Einherjar connaît le profil des autres (des amis savent qui est le troll du groupe).
  Il ne connaît rien d'autre : ni leur état, ni leur position hors de sa vue.
- **Fin** : le jeu s'arrête de lui-même à `wall_seconds` réelles ou `game_seconds_max` de jeu, ou dès que le fichier
  `stop_file` existe. Sinon Mr. Popo le tue après `grace_s`. Un journal immobile pendant `heartbeat_s` = chambre figée (tuée, signalée).

## 2. Le journal (JSONL)

Un objet JSON par ligne, un seul écrivain par fichier. Champs communs : `t_game` (secondes de jeu depuis l'ouverture de
la chambre), `t_wall` (secondes réelles), `world`, `kind`. La plupart ont aussi `bot`. `pos` = `[x, y]` ou `[x, y, z]`
(en 3D, la carte utilise x/z). Écrivains prêts à l'emploi : `popo/journal.py`, `godot/addons/hyperbole/hyperbole_journal.gd`,
`csharp/HyperboleJournal.cs`. Contrôle : `python hyperbole.py valider journal.jsonl`.

| kind | champs exigés | champs utiles | sert à |
|---|---|---|---|
| `chamber_start` | seed, mode | speed, engine, lobby, params, **milestones** (liste des étapes du jeu) | contexte ; les étapes que personne n'atteint |
| `chamber_end` | reason | | |
| `bot_join` | bot, persona | session_planned_s | rétention, abandons précoces |
| `bot_leave` | bot, reason | `bored` / `frustrated` / `quit` = abandon ; `session_end` / `fin_de_chambre` = non | rétention |
| `intent` | bot, option | score, area | ce que la Tête a voulu (écrit par la Tête) |
| `act` | bot, verb | area, pos, inputs, target | variété, couverture, mécaniques, repro |
| `fail` | bot, verb | reason (`rate`, `refus`, `no_effect`, `bloque`, `timeout`…), blame | ergonomie, frustration, gestes sans effet |
| `stuck` | bot | pos, intent, area, duration | carte des blocages |
| `learn` | bot, cue | after (s depuis le 1er signal) | apprentissage sans UI |
| `progress` | bot, milestone | | étapes, temps par profil |
| `gain` / `spend` | bot, resource, amount | source / sink, total | économie, exploits, ressource négative |
| `encounter` | bot, threat, outcome (`win`/`lose`/…) | pos | défi par menace et par profil |
| `death` | bot, cause | doing, pos, area, blame | équilibre, morts/h |
| `run_end` | bot, duration | cause, score | jeux à « runs » (rogue-lite, Stryder) |
| `moment` | bot, what | intensity | fun : moments à montrer (streamer) |
| `bored` / `frustrated` | bot | duration / streak, area | fun (écrits par la Tête) |
| `social` | bot, with, what | | entraide, vols, groupe |
| `say` | bot, text | | chat (Esprit) |
| `exploit` | bot, what | steps (marche à suivre) | failles du fouineur |
| `refusal` | bot, what | | refus du serveur inattendus (jeux en ligne) |
| `need` | bot, need, value | total | besoins (faim, froid…) |
| `error` | text | level | erreurs du moteur (Mr. Popo les prend aussi sur la sortie standard) |
| `anomaly` | what | gravite, domaine | NaN, objet sous le monde, désync… |
| `perf` | | fps, proc_ms, phys_ms, mem_*_mb, nodes, objects, orphans, resources, bots… | perf, fuites |

**blame** : tout événement qu'un saboteur cause à un autre porte `blame: <bot du saboteur>`. Le rapport compare alors le
lobby avec son **jumeau** (même graine, sans saboteur ni meneur).

Mr. Popo ajoute `popo.jsonl` (crash, gel, lignes d'erreur de la sortie) et les **oracles** génériques ajoutent leurs
`anomaly` à l'analyse : téléportation, hors bornes, ressource négative, valeur non finie, geste sans effet, progression
figée, oscillation (`popo/oracles.py`, réglages dans `seuils`).

## 3. La règle d'or : sans triche

- Un Einherjar **n'agit que par des entrées de joueur** : la manette virtuelle (`HyperboleVirtualPad`, mêmes actions
  que l'InputMap) ou le protocole client d'un jeu en ligne (serveur autoritaire). Jamais d'écriture directe dans l'état du jeu.
- Il **ne sait que ce qu'un joueur perçoit** : la façade `Senses` (caméra : cône + ligne de vue ; sons entendus ; HUD ;
  son propre corps). Le savoir des règles vient du profil (`knowledge` : `none` / `partial` / `wiki`, ou l'outil `wiki`) ou de l'expérience.
- **Contrôle automatique** : `python hyperbole.py lint mission.json` grep les fichiers de la tête (`lint.fichiers`) ;
  seuls les fichiers `lint.autorises` (Senses, Body) peuvent toucher le jeu. Préréglages `godot`, `csharp`, `python`
  + interdits propres au jeu (`lint.interdits` : tables de butin, chances, recettes cachées…). `lancer` refuse de
  partir si le contrôle échoue.
- Le **fouineur** cherche les failles avec les seuls moyens d'un joueur, la reproduit une fois, la signale (`exploit`
  avec `steps`) et n'y revient plus. Mondes de test seulement.

## 4. Le pont : des têtes Python pour un autre moteur

Pour un jeu qui ne veut pas porter la Tête (Unreal, C#, Electron) :

```
"cmd": ["python", "D:/Super_Toolbox/hyperbole/hyperbole.py", "pont", "{chamber_json}", "--", "MonJeu.exe", "-hyperbole={chamber_json}", "-hyperbole-port={port}"]
```

Le jeu se connecte en TCP sur `127.0.0.1:{port}` ; une ligne JSON par message (forme PettingZoo : une observation et
une action par agent) :

```
jeu -> pont : {"type":"senses","bot":"E1-01","t":12.5,"senses":{"cues":["lueur_rouge"]},"options":[{"id":"aller:mine","verb":"aller","area":"mine","tags":{"explore":0.6},"risk":0.4}]}
pont -> jeu : {"type":"act","bot":"E1-01","option":"aller:mine","delay":0.42,"leave":null}
jeu -> pont : {"type":"outcome","bot":"E1-01","t":20.1,"option":"aller:mine","ok":true,"reward":0.3,"novel":true,"dt":7.6,"cues":[{"cue":"lueur_rouge","hurt":true}],"exploit":null}
jeu -> pont : {"type":"bye"}
```

`leave` non nul = le bot quitte la partie (le jeu écrit `bot_leave`). Le jeu écrit son `journal.jsonl` ; le pont écrit
`tete.jsonl` (intent, learn, bored, frustrated, exploit) ; l'analyse lit les deux.

## 5. Les options (ce que la Tête choisit)

Une option est ce qu'un joueur pourrait faire **maintenant**, vu de son écran :

| champ | sens |
|---|---|
| `id` | unique, stable (`aller:mine`, `forger`, `aider:E1-02`) |
| `verb` | le geste (`aller`, `recolter`, `chasser`…) : la variété et les mécaniques se mesurent par verbe |
| `tags` | `{envie: poids}` parmi `progress mastery explore collect create social help show break disrupt lead rest survive` (+ les tags propres au jeu, notés par `goals` du profil) |
| `area` | le lieu visé / concerné |
| `risk` | danger **perçu** (0-1) : ce que le joueur peut estimer de son écran |
| `wiki` | `{value}` : ce qu'un joueur informé saurait (visible seulement des profils `knowledge: wiki`) |
| `hint` | un texte affiché qui y pousse (lu selon `reads_text`) |
| `target` | le bot visé (aide, vol…) ; la Tête évite le saboteur qu'elle connaît |
| `group` | jeu en groupe (les moins sûrs suivent le meneur) |
| `break` | cas limite (rafale, ordre des gestes, déconnexion) : n'attire que les fouineurs |
| `disrupt` | nuisance : seulement le saboteur, sous son plafond horaire |
