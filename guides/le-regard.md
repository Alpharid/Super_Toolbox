# Le regard : un juge visuel par l'API, avant l'œil du propriétaire

> Né sur Guardians of the Seal (novembre 2026). Un modèle de l'API Claude regarde des rendus (sprites, icônes, pièces d'interface,
> blocs de carte) et liste ce qui cloche. **Il signale, il ne valide pas** : le propriétaire reste le seul juge. **Le moteur est dans
> cette boîte** : [`scripts/regard/regard.py`](../scripts/regard/regard.py), générique ; tout ce qui est propre à un projet est en
> données, dans son fichier `regard.json` (modèle : `scripts/regard/regard.exemple.json`). Vue d'ensemble : [notre-methode.md](notre-methode.md).

## À quoi il sert

- **Filtrer avant une page de choix** : sur 3 visuels neufs ou plus, le regard passe d'abord ; les défauts nets sont corrigés avant
  que le propriétaire ne voie quoi que ce soit.
- **Auditer un lot entier** (tous les sprites, toutes les icônes) pour remplir la liste des défauts à corriger.
- Il ne sert **pas** à dire « c'est beau » ni à trancher un goût.

## Comment il marche

1. **Une liste de défauts connus** (un fichier Markdown : mains fondues, débris flottants, teinte qui vire, look « mascotte »…). Le
   regard cherche d'abord ceux-là (`connu = vrai`), puis tout autre défaut net (`connu = faux`).
2. **Une sortie imposée** par schéma JSON, une entrée par défaut : `quoi`, `ou` (précis : « main gauche, 3e silhouette »),
   `gravite` (`à corriger` / `à regarder` / `détail`), `connu` ; plus un résumé d'une ou deux phrases. Liste vide si l'image est propre.
3. **Le contexte de chaque image**, ajouté automatiquement quand c'est une entité : sa fiche (ce qu'elle est, son inspiration), son
   histoire dans le journal de l'atelier (concepts retenus, essais refusés, tronquée à 2 500 caractères), et **ce que le propriétaire a
   dit voulu** (fichier `voulus` : une ligne par entité).
4. **Des images préparées** : réduites à 1 568 px de côté, en JPEG de haute qualité au-delà de 1,2 Mo (les gros PNG ne passaient pas
   sur une connexion montante modeste). Pour un audit : une seule direction par entité, des **planches contact** pour les icônes et
   l'interface, la carte en blocs qui se chevauchent.

```
python D:/Super_Toolbox/scripts/regard/regard.py --config <projet>/regard.json <images…> [--contexte "…"] [--sortie rapport.md]
python D:/Super_Toolbox/scripts/regard/regard.py --config <projet>/regard.json --etalon   # se mesurer sur des défauts connus
```
Le fichier du projet (`regard.json`) donne : `projet` (son nom dans la liste blanche du client de l'API : un projet absent est
refusé), `presentation` (deux phrases sur le jeu et son style), `defauts` (le Markdown des défauts déjà relevés), `voulus` (une
ligne `- **<nom>** : …` par entité), `fiches` (les documents où chercher la section `### <nom>` d'une entité, avec un titre, une
longueur maximale et s'il faut passer par les `alias`), `entites` (comment reconnaître une entité dans un chemin : préfixe du
fichier ou dossier parent), `etalon`, `sorties`, `modele`, `effort`. Dans un script : `Config.lire(…)`, `regarder(conf, image,
contexte)`, `demande_lot(conf, id, image, contexte)` pour la Batch API, `rapport_md(…)`.

Sur Guardians, `tools/claude_api/regard/regard.py` garde les mêmes commandes et ajoute l'**audit** propre à ses assets
(`--audit <familles|tout> --lot` : une direction par entité, planches contact, carte en blocs) ; vérifié le 2026-11-08 :
consignes et contextes identiques à l'ancien code sur 38 images.

## Ce qu'il coûte et ce qu'il vaut

- Modèle : le plus grand (Opus), réflexion moyenne. **Environ 0,03 $ l'image** (étalon : 0,14 $ pour 5 images) ; l'audit de 65 images
  (en lot) : **0,91 $**. Règle retenue : 0,50 $ au plus pour le filtre d'une page ; les audits complets restent rares.
- **Étalon** avant de s'en servir : on lui donne des images dont on connaît les défauts. Sur Guardians il a retrouvé 6 défauts sur 6,
  et n'a rien inventé sur l'image témoin.

## Ce qui a raté (et la règle qui en sort)

- **Faux défauts faute de contexte** : il voyait des « cheveux » sur une créature qui s'appelle l'Ombre, un serpent « trop rond », des
  « grands yeux de mascotte » que le propriétaire avait validés, une « croix » qui était un encrier. → **Toujours lui donner la fiche
  de l'entité et la liste de ce qui est voulu**, et ajouter une ligne au fichier `voulus` à chaque retour de ce genre.
- **Trop d'un coup** : 283 défauts signalés sur 65 images ; le propriétaire en a jugé 58 puis a lâché. → **Ne jamais lui soumettre la
  liste brute.** Claude trie d'abord (doublons, déjà connus, évidents), regroupe en points (47 au lieu de 118 défauts), coche son avis,
  et le propriétaire ne corrige que là où il n'est pas d'accord (il a changé l'avis de Claude 9 fois sur 47).
- Il reste un œil de plus, pas un juge : un défaut qu'il ne signale pas n'est pas une preuve que l'image est bonne.

## Pour un autre projet

Ce qu'il faut : l'accord du propriétaire pour y mettre du crédit (le projet entre alors dans la liste blanche), un `regard.json`
copié du modèle, une liste de défauts connus propre au projet, un fichier « voulu » par entité, une fiche par entité qu'on puisse
retrouver par son nom (client de l'API : [economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md) §3), et une
page de tri ([pages-de-decisions.md](pages-de-decisions.md)) où l'avis de Claude est coché d'avance.
