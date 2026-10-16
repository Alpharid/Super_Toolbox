# Heimdall — le veilleur de la Super_Toolbox

> Dans la mythologie nordique, Heimdall est le gardien qui voit et entend tout l'univers depuis son pont.
> Ici, c'est le **cœur intelligent** de la toolbox : il se tient au courant de ce qui sort dans la tech
> utile aux projets de l'utilisateur, et il garde la toolbox à jour.

Heimdall n'est pas un démon qui tourne tout seul : c'est **un workflow suivi par Claude**, outillé par
`heimdall.ps1` (la partie mécanique) et deux fichiers de données. L'intelligence — lire le web, juger ce qui
est pertinent — est faite par le modèle ; le script dit **où regarder** et range les résultats.

## Les 3 pièces

| Fichier | Rôle |
|---|---|
| `sources.json` | Les **6 domaines** de veille et leurs **sources** (blogs, releases, listes, topics GitHub, forums). C'est la carte « où regarder ». |
| `projects.json` | La carte **projet → domaines → outils du kit + manques + pistes**. C'est ce qu'on lit en RÉFLEXE quand on touche un projet. |
| `reports/AAAA-MM-JJ.md` | Les **digests datés** produits à chaque passe de veille. L'historique de ce qui est sorti. |

Les 6 domaines : `godot` · `physique-netcode` · `modding-re` · `ia-agents` · `secu-reseau` · `devtools`.

## Les 2 déclics (la veille se lance ainsi)

**1. Réflexe projet (à chaque fois qu'on ouvre/lance un projet de l'utilisateur).**
Avant de travailler, lire l'index puis l'entrée du projet :
```
powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 project -Name <Projet>
```
→ ça dit quels **outils du kit** s'appliquent (à proposer) et quels **manques** restent. Si un besoin du
projet n'est couvert par rien dans la toolbox → **déclencher une passe de veille ciblée** sur le(s) domaine(s)
concerné(s) (voir ci-dessous), proposer les trouvailles, et ajouter les bonnes au kit.

**2. Digest planifié (1×/semaine, agent cloud).**
Un agent programmé (routine Claude Code) fait une passe de veille large sur les 6 domaines, écrit un digest
daté, met à jour `../INDEX.md` (section « Dernières nouveautés ») et pousse. Voir `../scripts/` et la routine
schedulée. C'est l'équilibre fraîcheur / tokens choisi par l'utilisateur.

## Faire une passe de veille (la recette)

1. `heimdall.ps1 brief [-Domain <id>]` → imprime les sources + mots-clés à couvrir (et quoi éviter).
2. `..\scripts\kit.ps1 check` → nouveautés des dépôts déjà intégrés (subtrees).
3. Pour chaque domaine visé : chercher sur le web (releases récentes, GitHub trending/topics, awesome lists,
   forums) ce qui est **nouveau ou notablement mis à jour**, **maintenu**, **licence correcte**, **pertinent**
   pour au moins un projet. Écarter ce qui est déjà dans `INDEX.md` / `upstream/`.
4. `heimdall.ps1 report` → crée `reports/AAAA-MM-JJ.md` (squelette par domaine). Le remplir.
5. Décider pour chaque trouvaille : **lien** (dans INDEX + CATALOGUE) ou **subtree** (`kit.ps1 add …`, si
   copie raisonnable < ~50 Mo et licence permissive). Mettre à jour `INDEX.md` (contenu + « Dernières nouveautés »).
6. Commit + push. Une ligne dans `../HANDOVER.md` § Historique.

## Critères de pertinence (ce que Heimdall retient)

- Utile à **au moins un projet** de `projects.json` (ou au fil rouge : panels Godot en code, agents IA, audit réseau).
- **Maintenu** (commits/releases récents) ; pas de projet mort.
- **Licence** : permissive (MIT/Apache/BSD) pour une copie en subtree ; sinon simple **lien**. Jamais embarquer du
  code sans licence ou en CC-BY-NC-ND dans un subtree (lien seulement).
- **Taille** raisonnable pour un subtree (< ~50 Mo de fichiers) ; au-delà → lien vers la release.
- Pas de doublon avec ce qui est déjà dans la toolbox.

## Étendre Heimdall

- **Nouvelle source** : l'ajouter au bon domaine dans `sources.json`.
- **Nouveau projet** : ajouter une entrée dans `projects.json` (chemin, domaines, outils_kit, manques, pistes) — à faire
  dès qu'un projet naît, c'est ce qui rend le réflexe utile.
- **Nouvelle piste** : trouvé un outil qui irait bien à un projet précis ? L'ajouter à `pistes` de ce projet dans
  `projects.json`. `heimdall.ps1 project -Name <P>` les affiche → au prochain passage, on les propose ou on les utilise.
- **Nouveau domaine** : l'ajouter dans `sources.json` (il apparaît automatiquement dans `domains`, `brief`, `report`).
