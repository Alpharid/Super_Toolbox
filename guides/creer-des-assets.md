# Créer des assets (images, 3D, sprites, audio) en local

> Pour tout projet qui a besoin d'art : concept, décors, personnages, sprites isométriques, icônes, UI, musique.
> L'atelier tourne **en local** sur le PC (RTX 3090 Ti 24 Go) : pas d'abonnement, pas d'envoi de données.
> Recherche et licences vérifiées le 2026-10-18 (projet Guardians of the Seal).

## Règle d'or : pas de « look IA par défaut »
1. **D'abord un moodboard** de références d'**artistes humains** (ArtStation, Pinterest, peintres du domaine public), avec des mots-clés de style.
2. Puis les outils ci-dessous.
3. **Repeindre ou retoucher à la main** (Krita) ce qui sera livré.

Une sortie 100 % IA paraît générique, et elle est difficile à protéger par le droit d'auteur dans l'UE. Steam exige aussi de déclarer les assets IA livrés (depuis le 16/01/2026).

## L'atelier : `C:\Atelier_IA`

| Élément | Où | Rôle |
|---|---|---|
| ComfyUI portable v0.41 (Python 3.13, torch cu130) | `C:\Atelier_IA\ComfyUI_windows_portable` | moteur de génération ; lancer `C:\Atelier_IA\lancer_comfyui.bat` (http://127.0.0.1:8188) |
| Modèles partagés | `C:\Atelier_IA\modeles\<type>\` | lus par ComfyUI via `extra_model_paths.yaml` (et donc par Krita) |
| Téléchargement des modèles | `C:\Atelier_IA\telecharger_modeles.sh` | `bash telecharger_modeles.sh` : reprise possible, saute ce qui est déjà là |
| Nœuds ajoutés | `custom_nodes/` : comfyui-tooling-nodes, comfyui-inpaint-nodes, comfyui_controlnet_aux, ComfyUI_IPAdapter_plus | ce qu'il faut à Krita AI Diffusion |
| Krita 5.3 + **krita-ai-diffusion** 1.53 | winget `KDE.Krita` ; extension dans `%APPDATA%\krita\pykrita` | peindre par-dessus, inpainting, sélection → génération. Dans Krita : Réglages > Docker « AI Image Generation », serveur personnalisé `127.0.0.1:8188` |
| Client Python | `scripts/comfy_client.py` (ce dépôt) | piloter ComfyUI depuis un script : `zimage_txt2img`, `qwen_edit`, `televerser` |
| ffmpeg, 7-Zip, Audacity, Surge XT, uv | winget | vidéo et son, archives, synthé (accordage microtonal Scala pour les maqâms), Python isolés |

## Modèles installés et licences (UE + commercial)

| Modèle | Fichiers | Licence | Usage |
|---|---|---|---|
| **Z-Image Turbo** (6B) | `z_image_turbo_bf16` + `qwen_3_4b` (CLIPLoader type `lumina2`) + `ae` | Apache-2.0 ✅ | concept rapide : 9 pas, cfg 1, `res_multistep`, ModelSamplingAuraFlow shift 3. Environ 15 s par image en 1024² |
| Z-Image (base, non distillé) | `z_image_bf16` | Apache-2.0 ✅ | base pour entraîner une **LoRA de style** |
| Z-Image Fun ControlNet Union 2.1 | `model_patches/Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps` | Apache-2.0 ✅ | conditionner par profondeur, contours ou pose (rendus Blender → peinture), nœud `ZImageFunControlnet` |
| **Qwen-Image-2512** (20B fp8) | `qwen_image_2512_fp8_e4m3fn` + `qwen_2.5_vl_7b_fp8_scaled` (type `qwen_image`) + `qwen_image_vae` | Apache-2.0 ✅ | meilleure qualité et meilleure compréhension du texte du prompt ; lent |
| **Qwen-Image-Edit-2511** (fp8mixed) | `qwen_image_edit_2511_fp8mixed` | Apache-2.0 ✅ | **réinterpréter une image** (même personnage, autre pose, fond neutre…) ; plusieurs minutes par image |
| LoRA Multiple-Angles (fal) | `loras/qwen-image-edit-2511-multiple-angles-lora` | Apache-2.0 ✅ | vues à 45° près : feuilles de personnage |
| InstantX ControlNet Union (Qwen) | `controlnet/Qwen-Image-InstantX-ControlNet-Union` | Apache-2.0 ✅ | profondeur, contours, pose pour Qwen-Image |
| **TRELLIS.2** (4B) | `trellis_2_bf16` + VAE shape/texture + `clip_vision/dino_v3_vit_l` | MIT ✅ | **image → 3D texturée** (GLB). Nœuds **natifs** ComfyUI (`Trellis2*`), sans nvdiffrast (dont la licence est non commerciale) |
| BiRefNet | `background_removal/birefnet` | MIT ✅ | détourage (nœud `RemoveBackground`) |

**À ne pas prendre**
- **Tencent Hunyuan** (3D, Motion) : licence qui **exclut l'UE**. Pixal3D (Tencent ARC) : licence non vérifiée.
- **Non commerciaux** : FLUX.2 dev, FLUX.1 Kontext dev, Qwen-Image-2.1, MusicGen, YuE2 ; checkpoints Civitai fusionnés avec NoobAI.
- **Seuil de 1 M$ de CA** (Stability Community License) : SD 3.5, Stable Fast 3D, Stable Audio Open.
- Une LoRA hérite de la licence de son modèle de base.

## Recettes

- **Concept / moodboard → croquis** : `zimage_txt2img` en lots (variantes de prompt plutôt que de seed : Turbo varie peu d'une seed à l'autre). Ajouter un négatif anti-mignon (`cute, chibi, big eyes, 3d render, plastic…`, déjà dans le client). Écrire le style en mots de peintre : *rough oil painting, visible brushstrokes, muted palette, single warm light*.
- **Garder un design et changer la pose ou le fond** : `qwen_edit("Redraw this exact same creature… plain grey background…", [concept.png])`.
- **Image → 3D** : image propre sur fond neutre → `RemoveBackground` → `ImageCropToMask` (1024, pad 1.1) → `Trellis2Conditioning` → structure (KSampler 12 pas, cfg 7.5, ModelSamplingSD3 shift 5) → shape (20 pas) → `Trellis2UpsampleStage` 1536 → texture (12 pas, cfg 1) → `VaeDecodeShapeTrellis` / `VaeDecodeTextureTrellis` → `UnwrapMesh` → `BakeTextureFromVoxel` → `ApplyTextureToMesh` → `MeshToFile3D` + `Save3DAdvanced`. Modèle de départ : template `3d_pixal3d_trellis2_image_to_model.json` des templates de ComfyUI, branche TRELLIS.2.
- **3D → sprites isométriques 8 directions** : `um render3d … --preset iso8` (universal-modder, `upstream/universal-modder/skills/asset-pipeline/SKILL.md`) ou script Blender maison. Caméra ortho à 30° = 2:1 exact des TileMaps isométriques Godot. Pour un rendu peint : EEVEE + Shader-to-RGB + nœud **Kuwahara** au compositing.
- **Rendu Blender → peinture cohérente** : passe de profondeur → `zimage_txt2img(…, controle="depth.png", force_controle=0.6)`.
- **Fumée, feu, sable vivants** : effets en temps réel dans le moteur (Godot GPUParticles2D + shaders) par-dessus le sprite, pas d'images fixes.

## Pas encore installé (pistes vérifiées)
- **ai-toolkit** (ostris, MIT) ou musubi-tuner (Apache-2.0) : LoRA de style sur 24 Go (Z-Image base ou Qwen-Image).
- **ACE-Step 1.5 / XL** (MIT, usage commercial des sorties explicitement permis) : musique ; version portable Windows. HeartMuLa 3B (Apache-2.0) en alternative.
- **NVIDIA Kimodo** (texte → mouvement ; poids SOMA/G1 sous NVIDIA Open Model License, éviter la variante SMPL-X) ; Mixamo (libre de droits dans un jeu) ; Rigify / AccuRIG 2 pour le rig.
- **Wan 2.2 VACE / Fun Control** (Apache-2.0) : repeindre une séquence animée à partir de la profondeur Blender (il reste un peu de scintillement).
- Audio libre : Sonniss GDC bundles, Kenney (CC0), Freesound filtré CC0, darbuka Coyotus. Pas de bonne banque libre d'oud ou de qanûn : celles qui valent le coup sont payantes (Sonokinetic, Sonuscore).

## Pièges
- **ComfyUI meurt sans erreur dans son journal** (Windows : événement 153 de `nvlddmkm` dans le journal Système). Le GPU qui gère l'affichage est réinitialisé dès qu'un calcul dépasse 2 s (TDR). Correctif standard : `HKLM\System\CurrentControlSet\Control\GraphicsDrivers` → `TdrDelay` et `TdrDdiDelay` = 60 (DWORD, admin, **redémarrage**). Fait sur ce PC le 2026-10-18. En attendant le redémarrage : images ≤ 1 MP avec Qwen.
- **Lancer ComfyUI détaché** (il survit à la console) : `Start-Process python_embeded\python.exe -ArgumentList '-s','ComfyUI\main.py','--windows-standalone-build','--listen','127.0.0.1','--port','8188' -WorkingDirectory C:\Atelier_IA\ComfyUI_windows_portable -WindowStyle Minimized`.
- **Qwen-Image 20B sur 24 Go** : fp8 + déchargement automatique, environ 5 min par image en édition. Z-Image Turbo pour itérer, Qwen pour finaliser.
- **Archive ComfyUI portable** : filtre BCJ2, que **py7zr ne sait pas lire**. Utiliser 7-Zip ou `7zr.exe` (7-zip.org, autonome).
- **Nouveau dossier de modèles** (ex. `background_removal`) : l'ajouter dans `extra_model_paths.yaml` **et redémarrer** ComfyUI.
- **winget en silencieux** : 7-Zip, Audacity et Krita demandent une validation UAC à l'écran. Prévenir l'utilisateur.
