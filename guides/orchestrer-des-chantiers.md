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
| `scripts/chantiers/veille_chantiers.sh` | Pour l'orchestrateur, en arrière-plan : rend la main dès qu'un chantier change d'état, que tout est calme depuis 30 min (blocage ?), ou toutes les 45 min. |
| `scripts/chantiers/verrou_gpu.sh` | File d'attente du GPU et des tâches lourdes, partagée par toutes les sessions (ticket par étape, ordre d'arrivée). |
| `scripts/verifier_page.sh` + `guides/pages-de-decisions.md` | Quand un chantier attend une décision du propriétaire : une page à cocher, vérifiée. |

```powershell
# depuis la racine du projet
powershell -ExecutionPolicy Bypass -File D:\Super_Toolbox\scripts\chantiers\chantier.ps1 -Nom onglets-chat [-SansAutorisation]
sh D:/Super_Toolbox/scripts/chantiers/chantiers_etat.sh . docs/chantiers "art tools client server docs"
sh D:/Super_Toolbox/scripts/chantiers/veille_chantiers.sh . docs/chantiers "art tools client server docs"   # en arrière-plan
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
Fiche à jour (« FINI » en tête), commits de tes seuls fichiers (voir les pièges de git plus bas), pas de push (c'est l'orchestrateur).
```
États reconnus en tête : `REPRENDRE ICI`, `EN COURS`, `EN ATTENTE` (du propriétaire, sa page est ouverte), `INTERROMPU … REPRENDRE ICI`,
`FINI` / `CLOS`. Les réponses du propriétaire arrivent dans la fiche sous un titre qui contient `À TRAITER` (voir L'orchestrateur). Une session interrompue (limite, nuit) écrit **avant de partir** quels fichiers non commités sont à elle.

## L'orchestrateur

La session où parle le propriétaire. Elle ne fabrique rien elle-même : elle écrit les fiches, ouvre et ferme les terminaux, porte les
réponses, surveille et publie. Sa difficulté : **elle ne peut pas écrire dans le terminal d'une autre session** (pas de messagerie
entre sessions), et une session qui attend, ou qui s'est figée sur une erreur d'API, reste plantée des heures sans que personne le
voie (vu deux fois : 4 h, puis trois sessions une demi-journée). D'où le cycle suivant.

**1. Les sessions ne s'arrêtent jamais pour attendre.** La consigne que `chantier.ps1` leur donne au démarrage :
> Lis ta fiche et fais ce qu'elle demande, rien d'autre. Mets la fiche à jour au fil de l'eau (état en tête). Ne t'arrête jamais pour
> attendre : si une décision du propriétaire manque, fais sa page (sombre, Copier), ouvre-la, et continue tout ce qui n'en dépend
> pas. Quand il ne reste rien à faire sans lui, ne pose pas de question dans ce terminal : surveille ta fiche (en arrière-plan :
> `until grep -qE '^#+ .*À TRAITER' <fiche>; do sleep 120; done`) ; traite ce qui y arrive, remplace « À TRAITER » par « traitées », et continue.
>
> La boucle cherche un **titre** (`^#+ .*À TRAITER`), pas le mot n'importe où : une fiche qui cite « À TRAITER » dans son texte (en
> décrivant la méthode, par exemple) déclencherait la session pour rien (vu le 2026-11-07).

**2. Les réponses passent par la fiche.** Le propriétaire coche sa page, copie ses réponses et les colle chez l'orchestrateur. Celui-ci
les recopie dans la fiche du chantier, sous un titre qui contient **« À TRAITER »** (`## Réponses du propriétaire à <page>_v2 (date) :
À TRAITER`). La boucle de surveillance de la session se déclenche ; la session traite et écrit « traitées ».

**3. L'orchestrateur veille.** `veille_chantiers.sh` tourne en arrière-plan et lui rend la main sur un **changement** (une fiche change
d'état, une session se ferme), sur un **calme** (aucun fichier touché depuis 30 min : blocage, limite d'usage ?) ou à un **point**
régulier (45 min). Il agit, puis la relance. À chaque message du propriétaire, il lance aussi `chantiers_etat.sh`.

**4. Relancer une session figée.** Pas d'activité depuis plus de 30 min et aucune page en attente : écrire l'état dans sa fiche (ce qui
reste, sous « À TRAITER »), tuer son `claude.exe` (le processus dont la ligne de commande contient « Chantier <nom> »), puis rouvrir
`chantier.ps1 <nom>` : la session neuve repart de sa fiche. Une fiche bien tenue est ce qui rend la relance gratuite.

**5. Fermer.** Une fiche « FINI » : vérifier que tout est commité, fermer le terminal, et le dire au propriétaire.

## Règles de l'orchestrateur
- **4 ou 5 sessions à la fois au plus** (jetons, GPU, et le propriétaire doit pouvoir suivre).
- **Un seul publie** : une fiche (ou l'orchestrateur) tient HANDOVER, README, la branche principale et les mises en ligne ; les
  autres commitent leurs chemins et s'arrêtent là.
- **Vérifier avant d'affirmer** : `chantiers_etat.sh` avant de dire « rien n'est bloqué ». Une session ne relit pas sa fiche toute
  seule : **réponses déposées dans sa fiche par un autre = la relancer** (lui écrire « relis ta fiche »).
- Fermer les terminaux des sessions finies (après avoir vérifié que tout est commité).
- **Outils maison** : un chantier qui crée ou change un outil maison met à jour son guide dans `guides/`, sa ligne dans
  [notre-methode.md](notre-methode.md) et dans la vitrine (`guides/vitrine/notre-methode.html`), et `INDEX.md`. Une leçon tirée d'un
  incident va dans « Faiblesses et pistes » de `notre-methode.md`.

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
