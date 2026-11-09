# Un serveur Discord de jeu, construit par script

Né sur Guardians of the Seal (2026-11-09, `communaute/discord/` du projet) ; **essayé sur un vrai serveur** le jour même : construit,
relancé deux fois sans rien changer. Outil : **`scripts/discord/construire.py`** et le
gabarit **`scripts/discord/modele_serveur.yaml`** ; tests : `python -m unittest discover -s tests` (un faux Discord en mémoire).

## L'idée
Le serveur entier (rôles, catégories, salons, droits, accueil natif, AutoMod, textes fixes) tient dans **un fichier relisible**.
Le script compare le fichier au serveur et **ne fait que le plan** ; `--appliquer` crée ce qui manque et corrige ce qui a changé ;
il **ne supprime jamais** sans `--elaguer` (il liste ce qui est en trop). On l'essaie sur un serveur d'essai, puis on le passe sur
le vrai. Chaque salon et chaque rôle a une **phase** (1 l'identité en ligne, 2 l'annonce, 3 l'accès anticipé) : `--phase 2` ajoute
la suite sans rien casser.

## Démarrer
1. Copier `modele_serveur.yaml` dans le projet, remplir les textes `<…>`, `python construire.py --fichier … --verifier`.
2. Le propriétaire crée le serveur d'essai, l'application et son bot (portail des développeurs), invite le bot avec `bot`,
   `applications.commands` et **Administrator** le temps de la construction ; le jeton et l'identifiant du serveur dans un
   `.env` hors git (`DISCORD_JETON=…`, `DISCORD_SERVEUR=…`). **Jamais un jeton dans la boîte.**
3. `construire.py --env … ` (le plan), puis `--appliquer --phase 1`.

## Ce qu'on a appris (pièges)
- **L'ordre compte** : les salons d'annonces, les forums et la scène exigent le **mode Communauté**, qui exige un salon de règles et
  un salon pour les avis de Discord : le script crée d'abord les salons simples, active la Communauté, puis crée le reste.
- **L'accueil natif** (Onboarding) veut au moins 7 salons par défaut, dont 5 où l'on peut écrire (règle vue dans les fils de
  Discord, pas dans la doc) ; les identifiants des questions neuves sont des flocons fabriqués par le script.
- **Le rôle du bot** doit être au-dessus des rôles qu'il donne. Les rôles neufs naissent tous à la position 1, le bot compris ;
  Discord accepte pourtant de monter le rôle du bot **s'il est dans la même requête que les autres, en tête** (vu sur un vrai
  serveur, 2026-11-09). Si Discord refuse, le script demande au propriétaire de le glisser à la main.
- **L'ordre des salons** : la requête d'ordre ne doit pas changer de parent (« Only one channel can have a parent_id modified at a
  time ») : le parent se pose à la création, l'ordre ne porte que les positions, et rien n'est envoyé si l'ordre est déjà bon.
- **L'accueil** : le relire (`GET /onboarding`) et comparer sans les identifiants des questions, sinon chaque passage le renvoie ;
  de même, Discord rend les rôles exemptés de l'AutoMod dans un autre ordre : comparer triés.
- **Le compte personnel, jamais** : piloter un compte utilisateur par un script (« self-bot ») est interdit et peut le faire
  bannir. Le propriétaire crée l'application et colle son jeton (Guardians : `preparer_essai.bat` trouve seul le serveur).
- **2FA obligatoire pour la modération** : seul le propriétaire peut l'activer (pas l'API).
- **Les notifications** : serveur réglé sur « mentions seulement », un rôle d'alerte choisi par le membre (« Alerte Alpha »), que
  seuls le studio et le bot mentionnent ; jamais `@everyone`.
- **Les liens et pièces jointes** fermés par défaut, ouverts salon par salon : la première défense contre les arnaques aux liens.
- **Discord renvoie plus de champs qu'on n'en écrit** : comparer seulement ce que le fichier fixe (`contient()`), sinon chaque
  passage « corrige » tout.
- **Débit** : lire `X-RateLimit-*`, attendre `retry_after` sur un 429 ; 10 000 requêtes refusées en 10 min = adresse bannie.
- **Un message par langue, chacun complet** (`message: [bienvenue, welcome]`) : une langue résumée sous l'autre se voit (le
  propriétaire de Guardians l'a relevé : les anglophones seront peut-être la majorité) ; et 2000 caractères au plus par message.
  Les boutons vont sous le dernier. `#salon` dans un texte devient un lien cliquable (`<#id>`) quand le salon existe.
- **Ne pas interdire de sujets** aux membres : le respect et « pas d'attaque » suffisent, la modération traite chaque débat
  comme les autres (une règle « pas de religion ni de politique » a été jugée infantilisante).
- **Les salons vocaux des membres** (« Créer un vocal ») : entrer dans un salon-porte fait ouvrir par le bot un salon à soi,
  ouvert à tous, éteint quand il est vide. Pièges : marquer la catégorie `vocaux_libres`, sinon `--elaguer` supprime des salons
  pleins ; **Discord ne laisse renommer un salon que deux fois en dix minutes** (le bot le dit au lieu d'échouer en silence) ;
  copier les droits de la catégorie à la création (l'API ne les recopie pas seule) ; garder les identifiants pour éteindre au
  redémarrage ceux restés vides ; un salon par membre, une attente entre deux, un plafond. Modèle : `bot/` de Guardians (`/feu`).
- **Les guildes reconnues** : section `guildes:` (une entrée = un rôle « Guilde · <nom> » et un salon dans sa catégorie ;
  `visible: tous` = tout le monde lit, la guilde écrit).
- **Un bot qui publie ne publie rien seul** : il dépose un brouillon dans un salon privé avec « Publier / Ne pas publier » (règle
  Alpharium : rien ne part dehors sans un clic du propriétaire). Modèle : le bot de Guardians (`communaute/discord/bot/` du projet :
  état du serveur de jeu, notes de version, rôles au choix, liste d'attente de l'accès anticipé, discord.py 2.7.1).

## Sources
Discord : https://docs.discord.com/developers/resources/auto-moderation · https://docs.discord.com/developers/topics/rate-limits ·
https://discord.com/blog/the-game-developer-playbook-part-two-early-access-and-pre-launch ·
https://discord.com/safety/360043653152-four-steps-to-a-super-safe-server
