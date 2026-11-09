# La musique et les sons d'un jeu, en local, triés avant l'écoute

> Né sur Guardians of the Seal (octobre-novembre 2026). Toute la génération tourne sur le PC (ACE-Step 1.5 XL dans ComfyUI,
> MOSS-SoundEffect), le tri aussi (sur CPU). Ce guide donne **l'ordre des étapes et les règles** ; les détails techniques (juge,
> peigne du décodeur, pièce écrite, sons sans paroles) sont dans [creer-des-assets.md § Chaînes éprouvées](creer-des-assets.md#chaînes-éprouvées-guardians-of-the-seal-octobre-novembre-2026).
> Code de référence : `tools/musique/` et `tools/sons/` du dépôt de Guardians (privé).

## Les règles (toutes nées d'un retour du propriétaire)

1. **Un contexte précis par morceau**, écrit sur la page d'écoute : la scène exacte (quand il joue, ce qu'on voit, combien de temps),
   ce qu'on vise, l'inspiration, et à quoi on reconnaît un raté. Sans ça, l'auditeur ne sait pas si un choix est voulu ou raté. Une
   recette par usage, pas une recette générale.
2. **Le mode imposé** : un mode non occidental écrit dans les tags ne suffit pas, tout sort pentatonique (mesuré : sur onze morceaux, 5
   degrés font 86 à 99 % des notes, aucune seconde augmentée). On écrit un **squelette** synthétique dans le mode et ACE-Step le reprend.
3. **Les combats démarrent vifs dès la première seconde** : un combat dure quelques échanges, une intro lente ne sera jamais entendue.
4. **Trier avant de soumettre** : rien sur une page d'écoute sans le tri automatique, et **1 ou 2 propositions par usage**, les
   meilleures du tri. (Un lot soumis sans tri l'a mis en colère : « fais des tests avant de me les soumettre ».)
5. **Les rejets s'archivent** (dossier d'archives hors git), ils ne se suppriment pas ; les morceaux excellents mais pas joués vont
   dans les archives du site (le « Conservatoire »).
6. **Des voix, ce sont de vraies voix audibles** (fredonnement, chœur en syllabes), jamais de paroles. Un « no lyrics » sans syllabes
   écrites donne de l'instrumental : écrire des lignes de syllabes (mmm, ah, oh). Vérifier la présence de voix avant de présenter.
7. **Les bruits d'interface sont des matières** du monde (parchemin, cuir, bois, cuivre, argile), jamais des bips. Un bus par usage,
   chacun réglable et coupable.

## La chaîne, dans l'ordre

| Étape | Outil (Guardians) | Ce qu'il faut savoir |
|---|---|---|
| Squelette dans le mode | `squelette.py --mode hijaz --tonique 62 --bpm 86 --duree 120` | Cordes pincées Karplus-Strong, souffle de flûte, bendir ; 3 min calculées en 1 s. Modes : hijaz, nahawand, kurd, penta mineure. |
| Reprise par ACE-Step | `generer.py`, `essais.py <recette> <graine> sft scrag a2a:0.6 squelette:auto` | Audio→audio, débruitage 0,5 à 0,8. **SFT (50 pas) + décodeur ScragVAE** : 0 bouffée de grésillement, contre 53 en Turbo. Turbo pour explorer, SFT pour finir. |
| Creuser le peigne | `raies.py <entree> <sortie> --lufs -14` | Le décodeur laisse des raies fines aux multiples de 1 500 Hz (« effet synthétique »). À faire **avant** toute reprise, sinon elle les recopie ; une source trop faible fait grésiller la reprise. |
| Vérifier le mode | `modes.py <fichier>` | Profil des hauteurs au quart de ton : le mode est-il vraiment joué ? |
| Nettoyer un morceau gardé | `nettoyer.py <entree> <sortie>` | Ne retouche que la bande 2,5-16 kHz dans les bouffées repérées ; jamais sur un combat. |
| **Trier** | `tri.py <dossier> [--combat]` | Sonie, écrêtage, silences, grésillement, sifflements, peigne, attaque des combats, et le juge **Audiobox Aesthetics** (CPU, ~15 s le morceau). Étalonné sur 59 verdicts du propriétaire : 17 de ses 21 rejets recalés. |
| Page d'écoute | `page_ecoute.py <plan>`, `ecoute.py` | Sombre ; un serveur local qui **enregistre les avis de chaque auditeur** et sert les téléchargements (FLAC, pistes séparées, recette). Partagée par un tunnel `cloudflared` : le service de pages de claude.ai refuse les gros fichiers. L'adresse du tunnel change à chaque lancement : ne jamais l'écrire dans un dépôt public. |
| Mise en jeu | `en_jeu.py` | Ogg, sonie commune, un bus de son par usage (musique, ambiance, effets, interface). |

**L'autre voie : la pièce écrite** (`ecrite.py`) : la musique écrite note à note (MIDI) et jouée avec de vrais échantillons CC0 (VCSL,
VSCO 2 CE). Rien de généré, donc aucun artefact : au juge, ce sont les meilleures notes du projet (CE 7,5 à 7,8). Détail dans
[creer-des-assets.md](creer-des-assets.md).

**Refaire un morceau déjà en jeu sans le dénaturer** (`lot6.py` de Guardians) : deux voies, à présenter côte à côte avec l'actuelle
(avant / après), tout passé au tri, l'avant compris : la **nettoyée seule** (`raies.py` puis `nettoyer.py` : aucune génération, rien
d'autre ne bouge) et la **reprise proche** (la recette d'origine plus un négatif contre le synthétique ; source = le fichier du jeu aux
raies creusées ; débruitage 0,35 à 0,5). Trier une **copie** du fichier du jeu : le tri écrit son rapport à côté du fichier.

**De vraies voix libres (Freesound)** (`freesound.py`) : la recherche se fait avec la clé d'API, mais l'original (WAV) ne se
télécharge que par **OAuth2** au nom d'un compte ; les aperçus publics (MP3 128 kb/s) sont trop pauvres pour des voix tenues jouées en
notes. Une page locale (jamais derrière un tunnel) où l'on colle la clé et clique « Autoriser » ; secrets dans un `.env` hors git ;
filtre `license:"Creative Commons 0"` à la recherche, licence revérifiée au téléchargement, chaque source notée (id, auteur, page).
Pour **jouer une vraie voix en notes** (`voix.py banque`) : chercher une **série d'un même chanteur** (une note tenue par fichier :
« single note » ; mieux qu'un assortiment de voix), mesurer la hauteur de chaque prise (autocorrélation au **premier pic** proche du
maximum : l'argmax saute d'octave ; lissage sur 7 trames contre le vibrato), départager par le nom donné quand la mesure tombe entre
deux notes, **remettre chaque note juste** (rééchantillonnage de quelques dizaines de cents), puis l'échantillonneur transpose au plus
d'un demi-ton. Whisper invente des mots sur une syllabe tenue (« daaa » → « Done. ») : n'écarter qu'une prise où il entend une phrase.
Poser la voix sur un morceau déjà gardé (même tempo) plutôt que la faire reprendre au modèle : il la rendrait synthétique.

**Rejouer un morceau généré avec de vrais instruments** (`reecrire.py` de Guardians) : quand un rendu a « un mood à lui » mais un
timbre synthétique, on garde ses notes et on change le son. Demucs `htdemucs_6s` (6 pistes) → **Basic Pitch** (Spotify, Apache-2.0 :
audio → notes et MIDI ; son modèle **ONNX** tourne sans TensorFlow : venv Python 3.12, `uv pip install --no-deps basic-pitch` puis
onnxruntime, librosa, pretty_midi, resampy, scikit-learn, mir_eval) → l'échantillonneur de la pièce écrite, piste par piste (basse
→ contrebasse en pizz, notes tenues → flûte ou violon, notes brèves → harpe). Jeu humain gardé (aucune quantification). Pièges : une
piste **presque vide** se transcrit quand même en centaines de notes fantômes (ignorer une piste sous 1 % de l'énergie, la batterie
sous 2 %) ; des cordes de métal pincées font compter leurs attaques comme du « grésillement » au tri. Leçons du premier essai (refusé à l'oreille : « un bordel », « pourquoi un piano ? ») : la harpe aux notes serrées sonne
piano ; la transcription relève aussi harmoniques et échos : **une seule note à la fois par instrument** (la plus forte) et
**trois instruments au plus**, tous du monde du jeu (1 380 notes → 368). Un juge qui préfère le rendu ne suffit pas : l'oreille tranche.

**Un « grésillement » sans nom peut être de l'écrêtage** : la source collée à 0 dBFS (des milliers d'échantillons) garde ses crêtes
coupées même une fois normalisée pour le jeu. Mesurer l'écrêtage **de la source** ; `ffmpeg -af adeclip,volume=-6dB` redessine
chaque crête d'après ce qui l'entoure (puis raies et bouffées). Sur Guardians : 45 bouffées → 2.

**La musique de combat qui ne coupe pas** (Godot, `sons.gd` de Guardians) : mesurer les écarts réels entre deux combats (les joueurs
IA : 80 % ≤ 10 s, 90 % ≤ 19 s, 98 % ≤ 60 s), tenir la musique ~15 s après le dernier coup, l'éteindre en ~10 s (un coup pendant le
fondu la fait remonter), et **reprendre le même morceau là où il était** si un combat revient dans la minute ; la zone reprend aussi le
sien. Sans cela, le joueur n'entend que des débuts de morceaux. Vérifier par un script Godot sans fenêtre qui étend le vrai script
avec un faux état de jeu.

**Toujours un champ « notes libres »** en bas d'une page de choix, en plus de la remarque de chaque question.

## Les bruitages

- **MOSS-SoundEffect v2** (Apache-2.0, GPU) : 6 candidats par son, 30 s au plus pour une ambiance ; 44 bruitages faits pour Guardians.
  Libérer d'abord la mémoire de ComfyUI (`POST :8188/free`) : ComfyUI inactif garde 20 Go de VRAM et MOSS passe de 1,2 à 40 s par pas.
- `trier.py` écarte par **Whisper** (CPU) les candidats où l'on entend des mots ; une page d'écoute ; `poser.py <son> <graine>` pose le
  choix en Ogg à la bonne sonie (ambiance −26, effets −18, interface −23 LUFS).
- Sons sans paroles (chuchotements « qui ne disent rien ») : de vrais enregistrements CC0, à l'envers ou en grains, vérifiés par
  Whisper et AST → [creer-des-assets.md](creer-des-assets.md).

## Les pièges

- **Ne pas se fier à une mesure sans l'avoir vérifiée à l'oreille** : le chiffre « secondes de voix » (énergie de la piste voix de
  Demucs) donnait 74 s de chant à un morceau qui n'en a aucun ; Demucs range la flûte et les cordes frottées avec la voix. Whisper
  seul sur le mélange ne repère pas le chant non plus.
- Le juge ne mesure pas le goût : un rejet pour ses voix ou son ambiance peut passer le tri. Le tri écarte le raté, l'oreille choisit.
- **GPU partagé** : un ticket de la file par rendu (8 min au plus) ; un rendu de 1 à 2 min en prend 6 ou 7 quand d'autres chantiers
  tournent. Un rendu tué reste dans la file de ComfyUI : le retirer (`essais.py --interrompre`).
- Un verrou du GPU orphelin bloque toute la file (voir [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md)).
