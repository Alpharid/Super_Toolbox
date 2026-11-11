# Économiser les tokens, les crédits de l'API et le GPU

> Comment on fait beaucoup avec un abonnement Claude, un crédit d'API mensuel et une seule carte graphique (24 Go) partagée entre
> plusieurs projets. Né sur Guardians of the Seal (octobre-novembre 2026). Vue d'ensemble : [notre-methode.md](notre-methode.md).
> Résultat mesuré : en une semaine d'usage de l'API (regard, gazette, traduction, joueurs IA qui parlent), **232 appels pour 3,21 $**.

## 1. Où tourne quoi

La règle : **le PC fait tout ce qu'il sait faire ; l'API sert quand elle est nettement meilleure, et on l'a mesuré.**

| Travail | Où | Pourquoi |
|---|---|---|
| Joueurs IA (corps et tête), Hyperbole | PC (CPU) | Des heures de jeu sans un token. |
| Faire parler les joueurs IA | API, petit modèle ; modèle local en secours | Essai à l'aveugle : l'API préférée 17 fois sur 20. |
| Images, 3D, sprites, carte | PC (GPU : ComfyUI, Blender, TRELLIS) | Rien ne sort de la machine, pas de coût à l'image. |
| Musique, bruitages | PC (GPU) | Idem. |
| Tri de la musique et des sons | PC (**CPU**) | Laisse le GPU aux rendus. |
| Regarder des rendus (le regard) | API, grand modèle | Aucun modèle local ne voit aussi juste. |
| Lire des rapports (la gazette) | API, modèle moyen | Quelques centimes par jour. |
| Traduire le jeu | API, grand modèle, en lot | Qualité d'un traducteur, glossaire tenu. |
| Assistant local (Alphred) | PC | Ce qui n'a pas besoin de Claude ; son dernier recours. → [ia-locale-performante.md](ia-locale-performante.md) |

**Jamais d'entraînement d'un modèle local sur des sorties de Claude** (la politique d'usage d'Anthropic interdit la distillation sans
accord). Un modèle local s'améliore par l'ingénierie : contexte, réglages, mémoire.

## 2. Les tokens des sessions Claude Code

- **Un terminal par chantier** : une session courte qui ne lit que sa fiche coûte moins qu'une longue session qui traîne cinq sujets,
  leurs images et leurs journaux, et qui finit en erreurs. → [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md)
- **Un document de reprise court**, chargé à chaque session : l'état présent et le mode d'emploi. L'historique complet vit à part et ne
  se lit que pour chercher le pourquoi d'une décision.
- **Un index léger** avant tout (`INDEX.md` de cette boîte) ; puis Grep, puis lecture des seules lignes utiles. Les listes se greppent,
  elles ne se lisent pas.
- **Peu d'images** : un recadrage réduit, une planche plutôt que dix vues. **Jamais de long journal** : `tail`, `grep`.
- **Des sous-agents pour les balayages larges** (lire vingt fichiers pour en tirer une conclusion) : on garde leur conclusion, pas les
  fichiers. 4 ou 5 à la fois au plus, comptes rendus courts, détail écrit dans un fichier.
- **Ne pas dépenser de tokens pour ce qu'une machine teste** : les joueurs IA et Hyperbole jouent sur le PC ; les scénarios d'essai
  prennent les captures ; les scripts de vérification (`verifier_page.sh`, tests) disent oui ou non.
- **Garder une marge** avant la limite d'usage : finir proprement (fiche à jour, commits) plutôt que couper au milieu.
- **Écrire moins de code** (gain mesuré modeste, ~10 %, mais moins à relire ensuite), dosé selon le projet → [code-sobre.md](code-sobre.md).
- Le bon moment pour `/clear` se dit au propriétaire (fin de chantier, contexte qui s'alourdit).

## 3. Les crédits de l'API : le petit client maison

**D'abord, la permission.** Le crédit de l'API est payé pour des projets précis : avant de l'utiliser sur un projet, **demander au
propriétaire, au moins une fois par projet** (« certains ne méritent pas qu'on y mette des dollars d'API »). Aujourd'hui seul
Guardians of the Seal est autorisé. Le client de cette boîte tient une **liste blanche** des projets
(`scripts/claude_api/projets_autorises.json`) et **refuse tout projet qui n'y est pas** (`ProjetNonAutorise`, dès la construction
du client). Ajouter un projet = son accord d'abord, puis une entrée avec la date de cet accord (`autorise_le`).

Le client : **`scripts/claude_api/claude_api.py`** (né sur Guardians, porté le 2026-11-08 ; Guardians l'utilise par un
branchement de quelques lignes qui garde ses anciens noms).

```python
import sys; sys.path.insert(0, r"D:\Super_Toolbox\scripts\claude_api")
from claude_api import Client, HAIKU
api = Client("Mon_Projet")                     # refusé si le projet n'est pas dans la liste blanche
rep = api.appeler(HAIKU, "…", systeme="…", usage="essai", max_tokens=400, effort="low", cache_systeme=True)
lot = api.lancer_lot([{"id": "a1", "modele": HAIKU, "contenu": "…"}], usage="audit"); res = api.attendre_lot(lot, usage="audit")
```
```
python scripts/claude_api/claude_api.py projets      # la liste blanche et d'où vient la clé (jamais la clé)
python scripts/claude_api/claude_api.py depenses     # le cycle en cours, par projet, usage et modèle
python scripts/claude_api/claude_api.py verifier X   # autorisé ou refusé, sans appel
```

Ce qu'il fait :

- **La clé dans un fichier hors git** du projet, lue explicitement. **Jamais dans une variable d'environnement** : Claude Code la
  prendrait et dépenserait le crédit de l'API au lieu de l'abonnement.
- **Un journal de chaque appel** (date, modèle, usage, jetons, coût calculé) et un script qui totalise par usage et par modèle sur le
  cycle de facturation. La page de coût de la Console fait foi ; le journal sert à décider.
- **Un plafond d'arrêt commun** : à 90 $ dépensés sur les 100 $ du cycle (tous projets ensemble, compté depuis le jour où le crédit
  se renouvelle, `jour_du_cycle`), plus aucun appel ne part. Un journal par projet, chaque ligne marquée de son projet.
- **Un cache des réponses** (facultatif, `memoriser=True`) : la même demande déjà payée revient du disque, pour rien (utile pour
  relancer une page ou un rapport sans repayer).
- **La Batch API** (moitié prix) pour tout ce qui n'est pas pressé : audits, traductions, rapports. 19 lots, 132 appels sur 232.
- **Le cache des consignes** : les consignes longues (règles du projet, glossaire, liste des défauts) sont mises en cache ; les appels
  suivants les relisent pour une fraction du prix.
- **Une sortie imposée par schéma JSON** : pas de réponse à reprendre, pas d'appel perdu.
- **Le modèle selon la tâche** : le petit pour parler (Esprit des joueurs IA, réflexion basse), le moyen pour lire (gazette), le grand
  pour regarder et traduire. Réflexion basse ou moyenne par défaut.
- **Estimer avant d'automatiser** : la gazette a une commande `estimer` qui calcule le coût d'une journée sans appel.
- **Un plafond par usage** : 300 appels par séance de joueurs IA (environ 0,10 $) ; 0,50 $ pour le regard avant une page.
- Images réduites à 1 568 px, planches contact plutôt qu'une image par objet.

Répartition réelle (au 7 novembre 2026 ; la vitrine de la méthode tient les chiffres à jour, `scripts/recompter_vitrine.py`) :
regard 1,13 $, traduction et relecture 1,83 $, gazette et rapports 0,23 $, joueurs IA qui
parlent 0,03 $.

## 4. Le GPU partagé

- **Une file à tickets** (`scripts/chantiers/verrou_gpu.sh <nom> <commande>`) : chaque tâche lourde prend un ticket, servie dans l'ordre
  d'arrivée ; la prise est atomique (`mkdir`), les tickets d'un processus mort sont nettoyés. Partagée par toutes les sessions et entre
  projets.
- **Un ticket par étape, 8 minutes au plus** : jamais une boucle entière sous un seul ticket (elle bloquerait les autres sessions des
  heures). Les scripts de lot prennent un ticket par rendu.
- **Un projet peut être prioritaire** et demander une pause des tâches lourdes des autres. Pendant la pause, on ne reste pas les bras
  croisés : audit, ménage, documentation, tout ce qui est léger.
- **Libérer la mémoire** d'un serveur de modèles inactif avant d'en lancer un autre (ComfyUI inactif garde 20 Go ; on lui demande
  `POST /free`).
- **Le CPU pour ce qui peut** : juges audio, Whisper, tri.
- **Essayer petit avant les lots** (2 ou 3 morceaux montrés), puis les lots longs la nuit, enchaînés par un script.
- **Rien ne tourne pour rien** : on ferme serveurs, clients et modèles après usage.
- Windows : passer le délai TDR à 60 s (les longs calculs du GPU faisaient planter le pilote sans message).
