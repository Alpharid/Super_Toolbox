# Orchestrer plusieurs chantiers en parallèle (un terminal Claude par chantier)

> Né sur Guardians of the Seal (novembre 2026) : une seule session Claude qui porte cinq sujets finit saturée (contexte, images,
> journaux) et perd le fil. La méthode : **un chantier = une fiche = une session**, et une session « orchestrateur » qui écrit les
> fiches, ouvre les terminaux, surveille, ferme et publie. Outils : `scripts/chantiers/`.

## Les pièces

| Pièce | Rôle |
|---|---|
| `docs/chantiers/<nom>.md` (dans le projet) | **La fiche** : le seul contexte de la session. Écrite par l'orchestrateur, tenue à jour par la session. |
| `scripts/chantiers/chantier.ps1` | Ouvre un onglet Windows Terminal et y lance `claude` avec la consigne « lis la fiche, fais-la, mets-la à jour, dis quand c'est fini ». |
| `scripts/chantiers/chantiers_etat.sh` | Pour l'orchestrateur : sessions ouvertes, état en tête de chaque fiche, âge, alertes (réponses non vues, fini à fermer). |
| `scripts/chantiers/verrou_gpu.sh` | File d'attente du GPU et des tâches lourdes, partagée par toutes les sessions (ticket par étape, ordre d'arrivée). |
| `scripts/verifier_page.sh` + `guides/pages-de-decisions.md` | Quand un chantier attend une décision du propriétaire : une page à cocher, vérifiée. |

```powershell
# depuis la racine du projet
powershell -ExecutionPolicy Bypass -File D:\Super_Toolbox\scripts\chantiers\chantier.ps1 -Nom onglets-chat [-SansAutorisation]
sh D:/Super_Toolbox/scripts/chantiers/chantiers_etat.sh . docs/chantiers "art tools client server docs"
GPU_FILE=art/.file_gpu sh D:/Super_Toolbox/scripts/chantiers/verrou_gpu.sh rendu_tuiles blender -b --python rendu.py
```
Un projet peut garder sa propre copie de ces scripts (adaptée à ses dossiers) : c'est le cas de Guardians (`tools/chantier.ps1`).

## La fiche (gabarit)

```markdown
# Chantier : <sujet> : <date>
Fiche de reprise : une session neuve lit HANDOVER puis ce fichier. Un chantier par session.
## État : À FAIRE : REPRENDRE ICI          ← la 1re ligne « ## État » est lue par chantiers_etat.sh
## Chantiers qui tournent en même temps (ne pas toucher leurs fichiers, ne jamais commiter leur travail)
<qui touche quoi ; QUI SEUL publie, pousse, touche HANDOVER / main>
## 1. … 2. … (ce qu'il faut faire, avec chemins, critères d'acceptation, ce qui est interdit)
## Fin
Fiche à jour (« FINI » en tête), commits `git commit -- <chemins>`, pas de push (c'est l'orchestrateur).
```
États reconnus en tête : `REPRENDRE ICI`, `EN ATTENTE` (du propriétaire, sa page est ouverte), `INTERROMPU … REPRENDRE ICI`,
`FINI` / `CLOS`. Une session interrompue (limite, nuit) écrit **avant de partir** quels fichiers non commités sont à elle.

## Règles de l'orchestrateur
- **4 ou 5 sessions à la fois au plus** (jetons, GPU, et le propriétaire doit pouvoir suivre).
- **Un seul publie** : une fiche (ou l'orchestrateur) tient HANDOVER, README, la branche principale et les mises en ligne ; les
  autres commitent leurs chemins et s'arrêtent là.
- **Vérifier avant d'affirmer** : `chantiers_etat.sh` avant de dire « rien n'est bloqué ». Une session ne relit pas sa fiche toute
  seule : **réponses déposées dans sa fiche par un autre = la relancer** (lui écrire « relis ta fiche »).
- Fermer les terminaux des sessions finies (après avoir vérifié que tout est commité).

## Pièges vus (tous réels)
- **`git add` laissé dans l'index** par une session part dans le commit d'une autre : toujours `git commit -- <chemins>`.
- **`git commit -- <chemin>` commite le fichier tel qu'il est sur le disque**, avec le travail en cours des autres sessions dans ce
  même fichier. Pour un seul morceau d'un fichier partagé : passer par l'index (`git add -p`, ou `git hash-object -w` +
  `git update-index --cacheinfo`), vérifier `git diff --cached`, puis `git commit` **sans** chemin.
- **Scripts jetables** dans `%TEMP%` sous un nom banal (`h2.py`) : une autre session les importe par erreur. Chaque session écrit
  dans **son** scratchpad.
- Un fichier à moitié écrit par une session peut empêcher **tout le projet** de compiler (client Godot, solution .NET) : prévenir
  dans les fiches qui compile quoi, et ne lancer les vérifications globales qu'aux moments calmes.
- Les scénarios d'essai qui tournent sur le PC du propriétaire écrivent dans **ses** réglages (`user://`, config) : remettre la
  valeur d'avant en sortant.
- Une tâche GPU longue d'une session bloque les autres : un ticket **par étape** (8 min au plus), jamais une boucle entière sous un ticket.
- `wt` ne trouve pas `claude.cmd` et abîme les accents de la consigne : d'où les deux temps de `chantier.ps1` (wt → powershell → claude),
  fichier en **UTF-8 avec BOM** pour PowerShell 5.1.
