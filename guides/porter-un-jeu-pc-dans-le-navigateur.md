# Faire tourner un vieux jeu PC dans un navigateur

Cas réel : **MM2_Web** (`C:\MM2_Web`, dépôt privé `Alpharid/MM2_Web`), Midtown Madness 2 (2000) jouable en ligne avec les fichiers du CD, à 240 FPS dans Chrome. Ce guide donne l'ordre des options et les pièges rencontrés.

> Si l'utilisateur dit « une version web de tel jeu », il veut **le jeu tel quel**, pas un remake. Chercher d'abord un moyen de faire tourner l'original.

## 1. Choisir la voie (de la meilleure à la pire)

| Voie | Quand | Outils |
|---|---|---|
| **Réimplémentation / source port libre** compilé en WebAssembly | Il existe un moteur libre qui lit les données originales (cas de MM2 : OpenMM2). Résultat natif, rapide. | [Emscripten](https://emscripten.org) (`emscripten/emsdk` dans Docker), SDL2/SDL3 (cible Emscripten intégrée) |
| **Décompilation** (projet « decomp ») | Le code décompilé recompile ; même chemin qu'au-dessus. | listes : [awesome-decomp-games](https://github.com/myuu-151/awesome-decomp-games), [recompsoftware.com/games](https://recompsoftware.com/games/) |
| **Jeu DOS** | Tout jeu DOS. | [js-dos](https://js-dos.com) / DOSBox en WASM ; Abandonware France a une rubrique « Dans le navigateur » |
| **Console** | Jeux console. | EmulatorJS (cœurs RetroArch en WASM) |
| **Émulation Windows** | Dernier recours : appli 2D ou très légère. Lent (~25 % de la vitesse native), la 3D fixed-function passe mal en WebGL. | [Boxedwine](https://github.com/danoon2/Boxedwine) (Wine + CPU émulé), [v86](https://github.com/copy/v86) (PC x86 entier, Win98) |

Pour trouver un moteur libre : chercher « `<jeu>` decompilation OR reimplementation OR source port github ». Pour MM2 : [OpenMM2](https://github.com/lowlevelmetal/OpenMM2) (MM2, GPL-3.0), [Open1560](https://github.com/0x1F9F1/Open1560) (MM1), [mm2hook](https://github.com/Fireboyd78/mm2hook) (doc seulement, sans licence).

## 2. Porter un moteur C/C++ avec Emscripten : la check-list

1. **Build dans Docker** : `FROM emscripten/emsdk:<version>` (+ `pip install cmake ninja` si le projet veut un CMake récent). `emcmake cmake …`, désactiver Vulkan, les tests, les outils, le réseau.
2. **Boucle principale** : le navigateur la possède. Découper `while(!quit){…}` en une fonction appelée par `emscripten_set_main_loop_arg(fn, state, 0, true)`. Mettre tout l'état sur le tas (le `true` abandonne la pile de l'appelant). Aucun `sleep` dans une image.
3. **Threads** : les pthreads exigent l'isolation cross-origin (en-têtes COOP/COEP), impossible sur la plupart des hébergements simples. Remplacer chaque thread par un `pump()` appelé à chaque image (musique, décodage vidéo, chargements). Tout `std::thread` restant fait planter le jeu au moment où il démarre.
4. **OpenGL 3.3 → WebGL 2 (GLES 3.0)** : contexte `SDL_GL_CONTEXT_PROFILE_ES` 3.0, prélude `#version 300 es` + `precision highp float; precision highp int;`, `glDepthRangef` / `glClearDepthf`, pas de `glDrawElementsBaseVertex` (ajouter `baseVertex × stride` aux offsets des attributs).
5. **Fichiers** : les données vont dans MEMFS (`FS.createDataFile(…, canOwn=true)` évite une copie), les sauvegardes dans IDBFS (`FS.mount(IDBFS, {}, "/home/web_user")`, `FS.syncfs` toutes les 15 s et sur `visibilitychange`).
6. **Page** : `-sINVOKE_RUN=0`, monter les fichiers dans `preRun`, puis `callMain` après un **clic** (sinon pas de son : la politique autoplay bloque l'AudioContext). Canvas plein page : `SDL_WINDOW_FILL_DOCUMENT` (SDL ≥ 3.4).

## 3. Les pièges WebGL qui ont coûté le plus cher

- **`glGetError` par image = synchro GPU complète.** 95 % du temps CPU dans MM2. N'appeler qu'en mode debug.
- **Chrome/Edge sous Windows passent par ANGLE → Direct3D 11.** Un `glBindBufferRange` d'UBO par objet dessiné y est catastrophique (5 FPS, contre 56 avec `--use-angle=gl`). Passer les constantes par objet en **uniforms simples** (`uniform struct DrawBlockT {…} draw;`), en n'envoyant que les champs qui changent : 240 FPS. Toujours mesurer avec le backend D3D11, c'est celui des joueurs.
- **WebGL 2 type un buffer à sa première liaison** : lié une fois à `COPY_WRITE_BUFFER` (ou à `ARRAY_BUFFER`), il ne pourra plus jamais servir de tampon d'indices. Envoyer les indices via `GL_ELEMENT_ARRAY_BUFFER` avec le VAO 0 lié.
- **Fragment shader** : sans `precision highp int`, les blocs partagés entre les deux étages ne correspondent pas.

## 4. Héberger

| Où | Limites | Pour |
|---|---|---|
| **Cloudflare Pages** (`wrangler pages deploy dist`) | 25 Mio par fichier, 20 000 fichiers, bande passante illimitée, gratuit | Choisi pour MM2 (~345 Mo). Découper les données en morceaux de 14 Mo gzip. Nom de projet aléatoire pour une URL non devinable ; Cloudflare Access si l'accès doit être restreint. |
| Artifact claude.ai | 16 Mo par page, 15 Mo par fichier binaire, **256 Mo par version** | Petits jeux ; CSP stricte (aucune requête vers un autre hôte). |
| GitHub Pages | 1 Go le site, 100 Mo par fichier, dépôt public (sauf offre payante) | Jeux libres seulement : jamais de données propriétaires sur un dépôt public. |
| PC ou Pi + Tailscale Funnel / Cloudflare Tunnel | La machine doit rester allumée | Test, accès ponctuel. |

Côté page : un `manifest.json` (non mis en cache) liste les morceaux sous un dossier versionné (`data/<hash>/`, cache `immutable`). Les morceaux sont stockés dans **IndexedDB** après le premier téléchargement : 2ᵉ lancement en ~1 s. Inflater avec `DecompressionStream("gzip")`, seulement si les octets commencent par `1f 8b` (au cas où le serveur aurait déjà décodé).

## 5. Tester sans écran (Claude)

`puppeteer-core` + le Chrome installé (`C:/Program Files/Google/Chrome/Application/chrome.exe`), arguments `--use-angle=d3d11 --enable-gpu --ignore-gpu-blocklist`. Le mode headless rend en logiciel (FPS faux) : mesurer en `headless: false`. Clics et touches avec `delay: 90` (le jeu lit l'état une fois par image). Profil CPU : CDP `Profiler.start/stop`, en compilant avec `--profiling-funcs` pour avoir les noms C++. Scripts prêts : `C:\MM2_Web\tools\browser\` (`drive.mjs`, `fps.mjs`, `prof.mjs`).

## 6. Données d'un CD

- Image CloneCD/BIN 2352 octets → ISO : garder les octets 16 à 2064 de chaque secteur MODE1 jusqu'au début de la piste audio (`C:\MM2_Web\tools\img2iso.py`), puis 7-Zip.
- Ne mettre **aucune donnée du jeu dans git** ; les garder dans `local/` (ignoré).
