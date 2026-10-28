# Des joueurs IA dans un jeu en ligne (qui jouent vraiment)

Faire vivre un monde en ligne avec des personnages joués par des IA : ils farment, craftent, échangent, discutent,
se groupent et se fâchent, **sans tricher** et **sans comportement scripté**. Ils servent aussi de testeurs
(équilibre, bugs bloquants, exploits). Méthode tirée de la conception des « Descellés » d'un MMO maison (oct. 2026).

## 1. La règle d'or : un bot est un client

- Le bot se connecte par **le même protocole que le jeu** et reçoit la même vue que le joueur. Il ne peut pas tricher
  si le serveur est **autoritaire** (il décide de tout et refuse ce qui est illégal). Sans serveur autoritaire, commencer par là.
- Côté serveur, un drapeau sur le compte sert **uniquement** à compter (humains / bots) et à observer. Aucune règle du
  monde ne le lit (règle de revue + test d'architecture).
- Côté bot, la décision passe par une façade « ce qu'un joueur peut savoir ». Pas de tables de butin ni d'apparitions :
  il **apprend** en jouant et par la rumeur du chat.
- Le plus simple : réutiliser le **noyau du client** (réseau + état local, sans moteur graphique) s'il existe.

## 2. Trois couches, le LLM seulement en haut

| Couche | Rôle | Techno | Coût |
|---|---|---|---|
| Corps | se déplacer, combattre, ramasser, fuir | code classique (A*, réflexes) | ~nul, des milliers de bots |
| Tête | quoi faire maintenant : lieu, quête, craft, build, se déconnecter | utility AI / GOAP : chaque option reçoit un score selon envies, personnalité, expérience | très faible |
| Esprit | parler, se souvenir, aimer, détester, se fixer des buts | LLM, sortie JSON, **appelé sur événement** | c'est là que ça coûte |

L'Esprit ne pilote jamais un geste : il change des buts et des relations, la Tête en tient compte.
Déclencheurs : on lui parle, événement marquant (mort, niveau, butin rare, insulte, cadeau), début de session (plan),
fin de session (résumé), réflexion lente toutes les 10-20 min.

## 3. Ce qui les fait vivre (paramètres, pas scripts)

- **Personnalité chiffrée avec des défauts** (radin, vantard, rancunier, menteur…) : sans défauts, un LLM est trop
  gentil et il ne se passe rien.
- **Une vie hors jeu** → agenda bruité, sessions de durée variable, AFK, absences, départs et arrivées. Avec des
  horaires réalistes, environ un quart des bots sont en ligne au pic.
- **Apprendre au lieu de savoir** : estimation par lieu (XP/min, gain, risque) mise à jour par l'expérience
  (explorer un peu, exploiter beaucoup) → personne ne reste dans une zone trop facile ni ne meurt dans une zone trop dure,
  sans règle « niveau X = zone X ». Builds essayés, mesurés, gardés → une méta émerge. Rumeurs pondérées par la confiance.
- **Mémoire** : souvenirs datés avec importance, résumés de session, compactage des vieux souvenirs (contre la dérive),
  **graphe de relations** (affinité, confiance, rancune, dette) mis à jour par les événements. Outil possible : `mem0` (dans la boîte).
- **Chat crédible** : vitesse de frappe, fautes, silences, tout le monde ne répond pas à tout. RP : IC par défaut, OOC
  entre `(( ))` de temps en temps.
- **Filtre avant envoi** (liste + vérification) pour les interdits du jeu ; une ligne refusée est régénérée ou le bot se tait.

## 4. Être honnête avec les joueurs

Mélanger des bots à des joueurs sans le dire, c'est de la population truquée (des MMO l'ont payé cher). Les **assumer** :
une faction dans le lore, un compteur qui donne le détail humains / bots au survol, et à « t'es un bot ? » une
pirouette qui ne ment pas franchement.

## 5. Le modèle (local de préférence)

- Un modèle d'instruction moyen (8-14B), réflexion coupée, JSON, requêtes en parallèle (`OLLAMA_NUM_PARALLEL`, ou
  `llama-server -np N`). Voir [ia-locale-performante.md](ia-locale-performante.md).
- GPU partagé : si le modèle n'est pas là, l'Esprit dort et les bots jouent en silence (Corps + Tête suffisent).
- Aucun bot en ligne → décharger le modèle (`keep_alive: 0`).
- Une API (Claude…) seulement pour les moments rares et importants : sinon le coût récurrent grimpe vite.

## 6. Les bots testeurs

Chaque bot note ce qu'il voit, un orchestrateur agrège (JSONL + résumé Markdown lisible par une IA) :
`blocage` (position figée, quête qui ne valide pas), `anomalie` (résultat hors des bornes des règles partagées),
`refus` inattendu, `exploit` (gains aberrants vs la distribution : duplication, faille), `equilibre` (XP/h par lieu,
temps de kill, builds dominants). Des bots « fouineurs » qui cherchent la faille (actions hors portée, déconnexion au pire
moment, rafales) **uniquement sur un monde de test**.

## 7. Démarrer petit

1. Serveur : drapeau + compteur + création des comptes bots par l'admin.
2. 5-10 bots Corps + Tête, sans LLM : ils doivent finir le tutoriel et farmer au bon endroit.
3. Esprit : chat, mémoire, relations.
4. Horaires, observatoire (graphe social + « gazette » quotidienne), puis on monte en nombre en mesurant.

## Références

- *Generative Agents* (Park et al., 2023) — `joonspk-research/generative_agents` : mémoire, réflexion, plans (25 agents).
- *Project Sid* (Altera, 2024, arXiv 2411.00114) : 1000+ agents dans Minecraft, rôles, règles, cultures.
- *Voyager* (2023) — `MineDojo/Voyager` : agent qui apprend Minecraft seul (bibliothèque de compétences).
- *Mineflayer* — `PrismarineJS/mineflayer` : bots Minecraft en JS, si on veut expérimenter sur Minecraft d'abord.
