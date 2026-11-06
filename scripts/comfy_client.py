"""Client minimal de ComfyUI (Atelier IA, http://127.0.0.1:8188) : construit un graphe, l'envoie, récupère les images.

Lancer ComfyUI d'abord : C:\\Atelier_IA\\lancer_comfyui.bat

    from comfy import Graphe, zimage_txt2img
    imgs = zimage_txt2img("prompt", seed=1, largeur=1024, hauteur=1024)
"""
import json
import time
import urllib.parse
import urllib.request
import uuid

SERVEUR = "http://127.0.0.1:8188"

NEGATIF_DEFAUT = ("cute, chibi, cartoon, kawaii, big eyes, mascot, 3d render, plastic, clean vector, smooth gradient, "
                  "glossy, toy, pixar, disney, anime, text, watermark, signature, logo, frame, border")


class Graphe:
    """Graphe au format API de ComfyUI : g.n("Classe", entree=valeur ou (noeud, sortie))."""

    def __init__(self):
        self.noeuds = {}

    def n(self, classe, **entrees):
        nid = str(len(self.noeuds) + 1)
        self.noeuds[nid] = {"class_type": classe,
                            "inputs": {k: (list(v) if isinstance(v, tuple) else v) for k, v in entrees.items()}}
        return nid

    def envoyer(self, attente=3600):  # la file peut être occupée par un long TRELLIS
        cid = uuid.uuid4().hex
        data = json.dumps({"prompt": self.noeuds, "client_id": cid}).encode()
        req = urllib.request.Request(f"{SERVEUR}/prompt", data=data, headers={"Content-Type": "application/json"})
        try:
            pid = json.load(urllib.request.urlopen(req))["prompt_id"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(e.read().decode()) from e
        t0 = time.time()
        while time.time() - t0 < attente:
            h = json.load(urllib.request.urlopen(f"{SERVEUR}/history/{pid}"))
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    raise RuntimeError(json.dumps(st.get("messages", [])[-1:], ensure_ascii=False)[:2000])
                return self._images(h[pid]["outputs"])
            time.sleep(1.0)
        raise TimeoutError(pid)

    @staticmethod
    def _images(outputs):
        out = []
        for o in outputs.values():
            for im in o.get("images", []):
                q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im["subfolder"],
                                            "type": im["type"]})
                out.append(urllib.request.urlopen(f"{SERVEUR}/view?{q}").read())
        return out


def televerser(chemin):
    """Envoie une image locale dans le dossier input de ComfyUI ; renvoie son nom.
    Le nom porte l'empreinte du contenu : deux images de même nom (a/fiche_0.png, b/fiche_0.png) en file en même temps
    s'écrasaient, et le second travail lisait l'image du premier (vu sur Guardians of the Seal : un modèle 3D fait d'après la
    mauvaise fiche)."""
    import hashlib
    import mimetypes
    import os
    donnees = open(chemin, "rb").read()
    base, ext = os.path.splitext(os.path.basename(chemin))
    nom = f"{base}_{hashlib.sha1(donnees).hexdigest()[:12]}{ext}"
    limite = uuid.uuid4().hex
    corps = (f"--{limite}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{nom}\"\r\n"
             f"Content-Type: {mimetypes.guess_type(nom)[0] or 'image/png'}\r\n\r\n").encode()
    corps += donnees + f"\r\n--{limite}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{limite}--\r\n".encode()
    req = urllib.request.Request(f"{SERVEUR}/upload/image", data=corps,
                                 headers={"Content-Type": f"multipart/form-data; boundary={limite}"})
    return json.load(urllib.request.urlopen(req))["name"]


def _zimage_base(g, turbo=True):
    unet = g.n("UNETLoader", unet_name="z_image_turbo_bf16.safetensors" if turbo else "z_image_bf16.safetensors",
               weight_dtype="default")
    clip = g.n("CLIPLoader", clip_name="qwen_3_4b.safetensors", type="lumina2", device="default")
    vae = g.n("VAELoader", vae_name="ae.safetensors")
    model = g.n("ModelSamplingAuraFlow", model=(unet, 0), shift=3.0)
    return model, clip, vae


def zimage_txt2img(prompt, seed=0, largeur=1024, hauteur=1024, negatif=NEGATIF_DEFAUT, turbo=True, lot=1,
                   controle=None, force_controle=0.7, fin_controle=1.0, image_depart=None, denoise=1.0, lora=None):
    """Z-Image (Apache-2.0). turbo : 8 pas, cfg 1. controle : image locale (profondeur, contours…).

    lora : (fichier, force), ex. ("mon_style_v1.safetensors", 1.3)."""
    g = Graphe()
    model, clip, vae = _zimage_base(g, turbo)
    if lora:
        model = g.n("LoraLoaderModelOnly", model=(model, 0), lora_name=lora[0], strength_model=lora[1])
    if controle:
        img = g.n("LoadImage", image=televerser(controle))
        patch = g.n("ModelPatchLoader", name="Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors")
        model = g.n("ZImageFunControlnet", model=(model, 0), model_patch=(patch, 0), vae=(vae, 0),
                    strength=force_controle, image=(img, 0), start_percent=0.0, end_percent=fin_controle)
    pos = g.n("CLIPTextEncode", clip=(clip, 0), text=prompt)
    neg = g.n("CLIPTextEncode", clip=(clip, 0), text=negatif)
    if image_depart:  # image → image : garde la composition, repeint la matière
        src = g.n("LoadImage", image=televerser(image_depart))
        lat = g.n("VAEEncode", pixels=(src, 0), vae=(vae, 0))
    else:
        lat = g.n("EmptySD3LatentImage", width=largeur, height=hauteur, batch_size=lot)
    ks = g.n("KSampler", model=(model, 0), seed=seed, steps=9 if turbo else 30, cfg=1.0 if turbo else 4.0,
             sampler_name="res_multistep", scheduler="simple", positive=(pos, 0), negative=(neg, 0),
             latent_image=(lat, 0), denoise=denoise)
    dec = g.n("VAEDecode", samples=(ks, 0), vae=(vae, 0))
    g.n("SaveImage", images=(dec, 0), filename_prefix="atelier")
    return g.envoyer()


def qwen_edit(prompt, images, seed=0, pas=30, cfg=4.0, megapixels=1.0, lora_angles=None, negatif=" "):
    """Qwen-Image-Edit-2511 (Apache-2.0) : modifie/réinterprète 1 à 3 images de référence locales.

    lora_angles : force (ex. 0.9) pour la LoRA « Multiple Angles » (vues sous d'autres angles)."""
    g = Graphe()
    unet = g.n("UNETLoader", unet_name="qwen_image_edit_2511_fp8mixed.safetensors", weight_dtype="default")
    clip = g.n("CLIPLoader", clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors", type="qwen_image", device="default")
    vae = g.n("VAELoader", vae_name="qwen_image_vae.safetensors")
    model = unet
    if lora_angles:
        model = g.n("LoraLoaderModelOnly", model=(model, 0),
                    lora_name="qwen-image-edit-2511-multiple-angles-lora.safetensors", strength_model=lora_angles)
    model = g.n("ModelSamplingAuraFlow", model=(model, 0), shift=3.1)
    refs = {}
    premier = None
    for i, chemin in enumerate(images[:3]):
        im = g.n("LoadImage", image=televerser(chemin))
        sc = g.n("ImageScaleToTotalPixels", image=(im, 0), upscale_method="lanczos", megapixels=megapixels,
                 resolution_steps=8)
        refs[f"image{i + 1}"] = (sc, 0)
        premier = premier or sc
    pos = g.n("TextEncodeQwenImageEditPlus", clip=(clip, 0), prompt=prompt, vae=(vae, 0), **refs)
    neg = g.n("TextEncodeQwenImageEditPlus", clip=(clip, 0), prompt=negatif, vae=(vae, 0), **refs)
    lat = g.n("VAEEncode", pixels=(premier, 0), vae=(vae, 0))
    ks = g.n("KSampler", model=(model, 0), seed=seed, steps=pas, cfg=cfg, sampler_name="euler", scheduler="simple",
             positive=(pos, 0), negative=(neg, 0), latent_image=(lat, 0), denoise=1.0)
    dec = g.n("VAEDecode", samples=(ks, 0), vae=(vae, 0))
    g.n("SaveImage", images=(dec, 0), filename_prefix="atelier_edit")
    return g.envoyer(attente=1800)


def trellis_3d(image, sortie_prefixe="atelier_3d", seed=42, texture=2048, cible_faces=None):
    """TRELLIS.2 (MIT, nœuds natifs ComfyUI) : image locale → modèle 3D texturé (GLB dans output/3d/).

    Renvoie le chemin relatif du GLB dans le dossier output de ComfyUI."""
    g = Graphe()
    img = g.n("LoadImage", image=televerser(image))
    bg = g.n("LoadBackgroundRemovalModel", bg_removal_name="birefnet.safetensors")
    masque = g.n("RemoveBackground", bg_removal_model=(bg, 0), image=(img, 0))
    crop = g.n("ImageCropToMask", images=(img, 0), masks=(masque, 0), width=1024, height=1024, pad_factor=1.1,
               grow_mask=0, background="#000000")
    cv = g.n("CLIPVisionLoader", clip_name="dino_v3_vit_l.safetensors")
    cond = g.n("Trellis2Conditioning", clip_vision_model=(cv, 0), image=(crop, 0))
    unet = g.n("UNETLoader", unet_name="trellis_2_bf16.safetensors", weight_dtype="default")
    vshape = g.n("VAELoader", vae_name="trellis_2_shape_vae_bf16.safetensors")
    vtex = g.n("VAELoader", vae_name="trellis_2_texture_vae_bf16.safetensors")
    # structure
    m_s = g.n("ModelSamplingSD3", model=(g.n("RescaleCFG", model=(g.n("CFGOverride", model=(unet, 0), cfg=1.0,
              start_percent=0.667, end_percent=1.0), 0), multiplier=0.7), 0), shift=5.0)
    vide = g.n("EmptyTrellis2LatentStructure", batch_size=1)
    k_s = g.n("KSampler", model=(m_s, 0), seed=seed, steps=12, cfg=7.5, sampler_name="euler", scheduler="normal",
              positive=(cond, 0), negative=(cond, 1), latent_image=(vide, 0), denoise=1.0)
    vox = g.n("VaeDecodeStructureTrellis2", samples=(k_s, 0), vae=(vshape, 0), resolution="32")
    # forme
    m_f = g.n("RescaleCFG", model=(g.n("CFGOverride", model=(unet, 0), cfg=1.0, start_percent=0.769,
              end_percent=1.0), 0), multiplier=0.5)
    st = g.n("Trellis2ShapeStage", positive=(cond, 0), negative=(cond, 1), voxel=(vox, 0))
    k_f = g.n("KSampler", model=(m_f, 0), seed=seed, steps=20, cfg=7.5, sampler_name="euler", scheduler="normal",
              positive=(st, 0), negative=(st, 1), latent_image=(st, 2), denoise=1.0)
    up = g.n("Trellis2UpsampleStage", positive=(st, 0), negative=(st, 1), shape_latent=(k_f, 0), vae=(vshape, 0),
             target_resolution=1536)
    k_u = g.n("KSampler", model=(m_f, 0), seed=seed, steps=12, cfg=7.5, sampler_name="euler", scheduler="simple",
              positive=(up, 0), negative=(up, 1), latent_image=(up, 2), denoise=1.0)
    forme = g.n("VaeDecodeShapeTrellis", samples=(k_u, 0), vae=(vshape, 0))
    # texture
    tx = g.n("Trellis2TextureStage", positive=(up, 0), negative=(up, 1), shape_latent=(k_u, 0))
    k_t = g.n("KSampler", model=(unet, 0), seed=seed + 1, steps=12, cfg=1.0, sampler_name="euler", scheduler="normal",
              positive=(tx, 0), negative=(tx, 1), latent_image=(tx, 2), denoise=1.0)
    couleurs = g.n("VaeDecodeTextureTrellis", samples=(k_t, 0), vae=(vtex, 0), shape_subdivides=(forme, 1))
    # cible_faces : décime avant l'unwrap (l'unwrap de 8 M de faces prend ~25 min sur le CPU) ; la texture est cuite
    # depuis le maillage complet (reference_mesh), donc sans trous. Sans décimation : unwrap ~25 min et cuisson à court de VRAM ; 1,5 M de faces : ~6-10 min, GLB ~45 Mo.
    base = g.n("DecimateMesh", mesh=(forme, 0), target_face_count=cible_faces, placement_mode="midpoint") if cible_faces else forme
    mesh = g.n("MeshSmoothNormals", mesh=(base, 0), crease_angle=180.0)
    uv = g.n("UnwrapMesh", mesh=(mesh, 0), segmenter="pec", resolution=texture, padding=1, weld_distance=0.0002)
    bake = g.n("BakeTextureFromVoxel", mesh=(uv, 0), voxel_colors=(couleurs, 0), texture_size=texture,
               reference_mesh=(forme, 0))
    tex = g.n("ApplyTextureToMesh", mesh=(uv, 0), base_color=(bake, 0), metallic=(bake, 1), roughness=(bake, 2))
    g.n("SaveGLB", mesh=(tex, 0), filename_prefix=f"3d/{sortie_prefixe}")
    g.envoyer(attente=3600)
    return sortie_prefixe
