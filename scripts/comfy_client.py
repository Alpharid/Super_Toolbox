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

    def envoyer(self, attente=900):
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
    """Envoie une image locale dans le dossier input de ComfyUI ; renvoie son nom."""
    import mimetypes
    import os
    nom = os.path.basename(chemin)
    limite = uuid.uuid4().hex
    corps = (f"--{limite}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{nom}\"\r\n"
             f"Content-Type: {mimetypes.guess_type(nom)[0] or 'image/png'}\r\n\r\n").encode()
    corps += open(chemin, "rb").read() + f"\r\n--{limite}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{limite}--\r\n".encode()
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
                   controle=None, force_controle=0.7, fin_controle=1.0):
    """Z-Image (Apache-2.0). turbo : 8 pas, cfg 1. controle : image locale (profondeur, contours…)."""
    g = Graphe()
    model, clip, vae = _zimage_base(g, turbo)
    if controle:
        img = g.n("LoadImage", image=televerser(controle))
        patch = g.n("ModelPatchLoader", name="Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors")
        model = g.n("ZImageFunControlnet", model=(model, 0), model_patch=(patch, 0), vae=(vae, 0),
                    strength=force_controle, image=(img, 0), start_percent=0.0, end_percent=fin_controle)
    pos = g.n("CLIPTextEncode", clip=(clip, 0), text=prompt)
    neg = g.n("CLIPTextEncode", clip=(clip, 0), text=negatif)
    lat = g.n("EmptySD3LatentImage", width=largeur, height=hauteur, batch_size=lot)
    ks = g.n("KSampler", model=(model, 0), seed=seed, steps=9 if turbo else 30, cfg=1.0 if turbo else 4.0,
             sampler_name="res_multistep", scheduler="simple", positive=(pos, 0), negative=(neg, 0),
             latent_image=(lat, 0), denoise=1.0)
    dec = g.n("VAEDecode", samples=(ks, 0), vae=(vae, 0))
    g.n("SaveImage", images=(dec, 0), filename_prefix="guardians")
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
    g.n("SaveImage", images=(dec, 0), filename_prefix="guardians_edit")
    return g.envoyer(attente=1800)
