# IA locale rapide et fiable sur une carte 24 Go (état oct. 2026)

> Pour **Alphred_AI** et tout projet qui fait tourner un LLM, un agent ou une voix en local (RTX 3090 Ti 24 Go,
> 64 Go RAM, Windows 11). Veille Heimdall du 2026-10-19 → `heimdall/reports/2026-10-19-alphred.md`.
> Dépôts, licences et versions **vérifiés** ; les gains chiffrés viennent de blogs → **à mesurer chez nous** (A/B,
> on garde l'existant tant que le nouveau n'a pas gagné).

## 1. Moteur et modèle (vitesse + intelligence)

- **Ollama 0.40.6** (16/10/2026, stable ; 0.40.7 en rc). Correctifs utiles déjà acquis depuis 0.33 : cache KV qui
  n'est plus cassé par le compteur de tokens de Claude Code, 500 sur appel d'outil mal parsé, cache de préfill.
  Encore ouvert : [ollama#18913](https://github.com/ollama/ollama/issues/18913) (appels d'outils aux arguments vides).
- **Qwen3.8-27B** (Qwen, 05/08/2026, Apache-2.0) : successeur dense de Qwen3.6-27B, 262k de contexte, **tête MTP**
  (décodage spéculatif intégré). Sur Ollama : `qwen3.8:27b`, `qwen3.8:27b-mtp-q4_…`, `-mtp-q8_0`.
  - Vitesse : ~2× mesuré sur 4090 (47,7 → 95,5 tok/s) ; llama.cpp sur 3090 : 41,5 → 66 tok/s. Attendu chez nous : ~60-70 tok/s.
  - Qualité (chiffres constructeur) : SWE-bench Pro 61,7 vs 53,5, Terminal-Bench 2.1 73,0 vs 63,4. Français : pas de mesure trouvée.
  - VRAM : Q4_K_M ≈ 18 Go (+1 Go vs 3.6) → 128k de contexte risque de ne plus tenir : tester 96k.
  - Réglage du nombre de tokens spéculés (`draft_num_predict`) : via `/api/chat`, pas via `/v1`.
- **Templates de chat corrigés** : [froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates)
  (Apache-2.0, v22.5) — blocs de réflexion vides qui coupent les appels d'outils, boucles de répétition, cache KV
  invalidé, arguments d'outils en chaîne JSON. Ollama : à mettre en `TEMPLATE` dans le Modelfile (à tester) ;
  llama.cpp : `--jinja --chat-template-file`.
- **llama.cpp direct** ([ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp), MIT, MTP fusionné le 16/05/2026) :
  plan B si Ollama coince ; sert aussi à isoler « problème du modèle » vs « problème d'Ollama ».
- **Cache KV** : q8_0 reste bon pour Qwen (KL 0,024 au banc [localbench](https://localbench.substack.com/p/kv-cache-quantization-benchmark)) ;
  Gemma 4 se dégrade nettement en q8_0 → pas un bon remplaçant ici.
- Réflexion : `reasoning_effort` par défaut très haut → coupe-la (`"think": false`) pour la voix et les petites actions.

## 2. Agent (boucles, contexte perdu, appels d'outils ratés)

| Harnais | Licence / version | Pourquoi l'essayer |
|---|---|---|
| **[Pi](https://github.com/earendil-works/pi)** | MIT · v1.3.0 (15/10) | 4 outils, prompt système minuscule (idéal petit contexte), sessions en arbre, installeur PowerShell, `ollama launch pi`, plugin mem0. **1er candidat.** |
| [OpenCode](https://github.com/anomalyco/opencode) | MIT · v1.19 | compaction réglable (`auto`/`prune`/`reserved`), Windows OK |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | MIT · v0.22 | mémoire + skills qui s'améliorent, MCP, Windows natif ; le plus lourd |
| Qwen Code / Goose | Apache-2.0 | corrects, non évalués |

Protocole : mêmes 3 tâches > 50k tokens, même modèle, Claude Code vs Pi → compter boucles, appels ratés, réussite.
Aider stagne (dernier push mai 2026) ; Crush = licence FSL (pas libre).

## 3. Voix (Sonnette) — sans prendre de VRAM au LLM

| Brique | Outil | Gain | Coût |
|---|---|---|---|
| Voix | **[Pocket TTS](https://github.com/kyutai-labs/pocket-tts)** (Kyutai, code MIT, poids CC-BY-4.0, v3.3) | français (+ variante `french_24l` meilleure), streaming ~200 ms, **clonage depuis un wav** (avec consentement) | CPU, 0 Go VRAM |
| Fin de tour | **[Smart Turn v3.2](https://github.com/pipecat-ai/smart-turn)** (BSD-2) | détecte la fin de phrase à l'intonation, pas au silence seul : moins de coupures | 8 Mo, CPU, 10-65 ms |
| Mot d'éveil | **[livekit-wakeword](https://github.com/livekit/livekit-wakeword)** (Apache-2.0) | modèle « Hey Alphred » entraîné en données synthétiques ; libère whisper de l'écoute permanente | CPU, quasi nul |
| Timbre | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) VoiceDesign (Apache-2.0) | créer UNE fois la voix « majordome » depuis une description, puis la cloner avec Pocket TTS | GPU ponctuel |
| Voix haut de gamme | [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) (MIT) | plus expressif | ~6 Go VRAM → phrases pré-générées seulement |

À savoir : Piper (rhasspy) est **archivé** depuis 08/2025, son successeur `piper1-gpl` est GPL-3.0 ; Kokoro n'a qu'une
voix FR moyenne ; Voxtral TTS et F5-TTS = poids non commerciaux ; les modèles pré-entraînés d'openWakeWord = CC-BY-NC-SA.
STT : faster-whisper large-v3-turbo reste un bon choix ; Parakeet v3 / Voxtral Realtime = gain faible pour plus de VRAM.

## 4. Mémoire, web, outils

- **Mémoire** : [mem0](https://github.com/mem0ai/mem0) (Apache-2.0, v2.2.1, déjà copié) avec Qdrant local + embedder
  Ollama ; extraction en fin de session (sinon il se bat pour le GPU). Open WebUI a une mémoire native par modèle.
- **Recherche web locale** : [SearXNG](https://github.com/searxng/searxng) (AGPL, Docker) + [mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng)
  (MIT) ; lecture de pages → [crawl4ai](https://github.com/unclecode/crawl4ai) (Apache-2.0). Remplace le scraping Bing/DDG maison.
- **Open WebUI 0.12.3** (16/10) : MCP natif (streamable HTTP), Skills importables, compaction pendant les longues séries
  d'outils, automations ; [Open Terminal](https://github.com/open-webui/open-terminal) (MIT).
- **Contrôle du PC** : [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) (MIT) — derrière la confirmation vocale « Je confirme ».
- **Domotique** : serveur MCP officiel de [Home Assistant](https://www.home-assistant.io/integrations/mcp_server/) (`/api/mcp`).
- **Tokens** : [RTK](https://github.com/rtk-ai/rtk) (Apache-2.0, Rust) et [Caveman](https://github.com/JuliusBrussee/caveman)
  (Apache-2.0) compressent les sorties de commandes avant que le modèle les lise.

## 5. Ordre conseillé (quick wins)

1. Ollama 0.40.6 + `qwen3.8:27b` MTP en **A/B** contre le modèle actuel (vitesse, 10 appels d'outils types, français).
2. Voix : Pocket TTS fr + Smart Turn (CPU, 0 VRAM) contre Piper `gilles-low`.
3. Agent : Pi vs Claude Code sur 3 tâches longues ; SearXNG + mcp-searxng à la place de `tools/web.py`.
