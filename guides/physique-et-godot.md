# Physique avancée et Godot 4 — guide (écrit pour Stryder_Symbiosis)

Contexte visé : Godot **4.7**, GDScript, moteur physique **Jolt** (intégré à Godot depuis 4.4 ; `3d/physics_engine="Jolt Physics"`),
jeu « tout est physique » : cordes qui se tendent et cassent selon leur matière, structures qui cèdent sous le poids, eau qui
fait tourner une roue, joueurs bousculés sur le dos d'une créature géante qui marche, coop en ligne.

> Les chemins sont relatifs à `D:\Super_Toolbox\`. Ce qui est marqué **(à vérifier)** n'a pas été testé dans Godot 4.7 :
> le prouver par un petit prototype avant de bâtir dessus.

## 1. Comprendre Jolt (le moteur sous Godot) — `upstream/JoltPhysics/`

`Docs/Architecture.md` (≈ 1 000 lignes, lire par sections — `grep -n "^#" upstream/JoltPhysics/Docs/Architecture.md`) :

| Sujet Stryder | Section (ligne) | À retenir |
|---|---|---|
| Structures / cordes qui **cassent** | « Breakable Constraints » (~555) | Jolt n'a pas de casse automatique : on lit l'impulsion de la contrainte (`GetTotalLambdaPosition()` etc., voir `Jolt/Physics/Constraints/Constraint.h:149`) et on la **désactive** au-delà d'un seuil. Côté Godot : vérifier ce que `Joint3D`/Jolt exposent en 4.7 **(à vérifier)** ; à défaut, mesurer en GDScript l'étirement / l'écart entre les deux corps et supprimer le joint. |
| Ressorts, cordes élastiques | « Constraint Motors », « Stiffness and Damping », « Frequency and Damping » (~493-555) | Régler une contrainte en fréquence (Hz) + amortissement est plus stable que des raideurs brutes. |
| Personnage sur une surface qui bouge | « Character Controllers » (~701) | + l'exemple `Samples/Tests/Character/CharacterSpaceShipTest.cpp` : un personnage qui marche sur un vaisseau rapide qui accélère (c'est le problème du Symbiote sur le Strider ; cf. ADR 0001 de Stryder). |
| Monde très grand / précision | « Big Worlds » (~750) | Complète l'ADR « le Strider reste à l'origine ». |
| Coop / rollback | « Deterministic Simulation », « Rolling Back a Simulation » (~785-850) | Le déterminisme de Jolt suppose les mêmes binaires et le même ordre d'opérations. |
| Tissus, cordes souples, chair | « Soft Bodies » (~423) | Corps mous, skinning sur un squelette. |

**Exemples C++ à lire** (`Samples/Tests/`, un `.h` + un `.cpp` par démo, ~100-300 lignes) :
- Cordes : `Constraints/DistanceConstraintTest` et `Constraints/PointConstraintTest` (chaînes de 15 maillons), `SoftBody/SoftBodyCosseratRodConstraintTest` (tige/corde souple), `Hair/` (mèches = cordes très fines).
- Grue / poulies / mécanismes : `Constraints/PulleyConstraintTest`, `GearConstraintTest`, `RackAndPinionConstraintTest`, `PoweredHingeConstraintTest` (roue à aube motorisée), `SliderConstraintTest`, `SpringTest`.
- Eau / flottaison : `Water/BoatTest`, `Water/WaterShapeTest` (poussée d'Archimède par volume immergé).
- Ragdolls et créatures : `Rig/SoftKeyframedRigTest` (corps **dynamiques** forcés à suivre une animation : ils bousculent ce qu'ils touchent — piste pour le Strider), `Rig/PoweredRigTest` (moteurs qui amènent un ragdoll vers une pose), `Rig/KinematicRigTest` (version cinématique).
- Chaînes de corps liés (passerelles, structures) : `Constraints/ConstraintPriorityTest` (l'ordre de résolution rend la chaîne plus ou moins raide). Pas d'exemple de « résistance des matériaux » tout fait : la combiner avec la casse ci-dessus.

## 2. Briques Godot du kit

| Besoin | Dossier | Notes |
|---|---|---|
| Pattes / bras d'une créature (IK) | `upstream/GodotIK/` | IK 3D (FABRIK) pour Godot 4.3+, GDExtension (`GodotIK/src`, projet de démo `GodotIK/godot_project`). Godot 4.3+ a aussi `SkeletonModifier3D` en natif. |
| Destruction (casser un objet en morceaux) | `upstream/godot-destruction-plugin/` | Remplace un mesh par ses fragments en corps rigides (fragments préparés dans Blender). Godot 4 : addon depuis les *releases*. Base simple, pas de calcul de contraintes. |
| IA des Parasites / vautours | `upstream/limboai/` (behavior trees + machines à états, éditeur visuel, GDExtension ; démo `limboai/demo/`) ou `upstream/beehave/` (pur GDScript, plus simple à lire) | Choisir l'un des deux. |
| Coop en ligne | `upstream/netfox/` | Doc : `netfox/docs/` (concepts, guides, FAQ), exemples : `netfox/examples/` (multiplayer-simple, rollback-fps, multiplayer-state-machine…). |

### Point d'architecture pour la coop (important)
`upstream/netfox/docs/netfox.extras/guides/physics.md` : les versions officielles de Godot **ne permettent pas de faire avancer la
physique à la main** (pas de *stepping*), donc le **rollback de `RigidBody`** demande soit un Godot recompilé avec la PR de stepping,
soit l'addon **Rapier** (qui l'expose), soit le fork Blazium. Et `netfox/docs/faq.md` (~154) : le rollback n'exige pas une physique
déterministe, seulement *cohérente*. Pour un jeu où tout est physique, la voie simple est souvent **l'hôte fait la physique, les
autres reçoivent l'état** (pas de rollback des corps rigides) — à trancher tôt (ADR), car ça conditionne tout le reste.

## 3. Hors kit (liens, trop gros ou sans licence)

- **Godot Rapier Physics** — https://github.com/appsinacup/godot-rapier-physics (MIT, ~75 Mo) : autre moteur physique 2D/3D pour
  Godot, avec **stepping manuel** (rollback) et **simulation de fluides** (eau). Alternative sérieuse à Jolt si l'eau et le rollback
  deviennent centraux ; coût : changer de moteur.
- **Ten Minute Physics** (Matthias Müller) — https://matthias-research.github.io/pages/ (sources : github.com/matthias-research/pages,
  sans licence → ne pas copier le code) : cours courts et démos JS sur **XPBD** (cordes, tissus, corps mous, fluides, casse) —
  la meilleure base pour écrire ses propres cordes à matériaux (tension, rupture).
- **Corde verlet 3D façon Half-Life 2** — https://github.com/2nafish117/godot-verlet-rope (MIT, Godot 4).
- **Phantom Camera** (caméras façon Cinemachine) — https://github.com/ramokz/phantom-camera.
- **Terrain3D** (terrains) — https://github.com/TokisanGames/Terrain3D · **godot_voxel** (voxels, terrain destructible) — https://github.com/Zylann/godot_voxel.
- **Steam** (GodotSteam, a quitté GitHub) — https://codeberg.org/godotsteam/godotsteam · https://godotsteam.com.
- **Tests** : GUT — https://github.com/bitwes/Gut · gdUnit4 — https://github.com/godot-gdunit-labs/gdUnit4.
- **Debug en jeu** (FPS, mesures) — https://github.com/godot-extended-libraries/godot-debug-menu.
- **Doc officielle Godot** — https://docs.godotengine.org (sources : github.com/godotengine/godot-docs, 645 Mo).
- Plus de plugins : `upstream/awesome-godot/README.md` (Grep « physics », « rope », « water », « network »).

## 4. Licences — jeu destiné à Steam (commercial)

On peut **embarquer dans le jeu** : MIT (Jolt, netfox, LimboAI, beehave, GodotIK, destruction, Rapier), Apache-2.0, BSD — en
gardant leur fichier de licence dans les crédits / un `THIRD_PARTY_NOTICES`. On **ne peut pas** embarquer : du code sans licence
(Ten Minute Physics : s'en inspirer, réécrire), du CC BY-NC-ND (`awesome-claude-code`), et attention au GPL (contamine le jeu).
Les addons s'installent dans le projet du jeu depuis **leurs releases officielles** (`addons/`), pas en copiant `upstream/`.
