# Jouer en réseau, par Internet, à un vieux jeu PC « LAN » (IPX / DirectPlay)

> Pour les jeux PC 1995-2005 dont le multijoueur passe par **IPX** ou **DirectPlay ≤ 7** (réseau local, MSN Gaming
> Zone, modem…). But : que des amis jouent ensemble **par Internet, chacun chez soi, sans VPN, sans droits admin,
> sans rien régler**, avec le jeu d'origine. Exemple réussi : **MCM_Online** (Motocross Madness 1 & 2, 8 joueurs,
> 2026-10-27). Pour un jeu dans le navigateur, voir plutôt [porter-un-jeu-pc-dans-le-navigateur.md](porter-un-jeu-pc-dans-le-navigateur.md).

## 1. Diagnostiquer le multi du jeu (10 minutes)

- Imports de l'exe (`pefile`) : `DPLAYX.dll` (ordinal 1 = `DirectPlayCreate`, 4 = `DirectPlayLobbyCreateA`) → DirectPlay ;
  `WSOCK32.dll` + chaînes « IPX » → IPX direct (Winsock 1).
- Chaînes (ASCII **et** UTF-16, plus les `STRINGTABLE` des DLL de langue) : « IPX », « LAN », « 8 joueurs »,
  `ConnectUsingLobby`, `LaunchedFromLobby` (le jeu accepte d'être lancé par un lobby DirectPlay).
- **Le mode IPX est souvent celui à 8 joueurs** (ex. MCM1 : « Connexion IPX (8 joueurs) » contre « Internet TCP/IP
  (4 joueurs) »). Les modes de course sont les mêmes ; seuls les classements en ligne de l'époque sont perdus.

## 2. La recette qui marche : IPX encapsulé vers un relais

```
jeu ─ DirectPlay/Winsock IPX ─ IPXWrapper (DLL à côté de l'exe) ─ UDP ─► relais « serveur IPX DOSBox » ─► autres joueurs
```

- **[IPXWrapper](https://github.com/solemnwarning/ipxwrapper)** (GPL-2, 0.7.2 en 2025) : 4 DLL (`wsock32`, `mswsock`,
  `dpwsockx`, `ipxwrapper`) à côté de l'exe + un `ipxwrapper.ini` à côté aussi (prioritaire sur le registre) :
  `dosbox server address = <hôte>` / `dosbox server port = <port>`. Le jeu se croit sur un LAN ; **la diffusion marche**
  (la liste des parties s'affiche toute seule), ce que Tailscale (pas de broadcast) ne fait pas. Pas de SPX (DirectPlay n'en a pas besoin).
- **Relais = protocole du serveur IPX de DOSBox** (`ipxnet startserver`), ~150 lignes de Python asyncio :
  en-tête IPX de 30 octets ; inscription = paquet vers socket 2 avec nœud nul → réponse dont le nœud de destination est
  l'**IP+port du client vu par le relais** ; nœud destination `FF FF FF FF …` = diffusion à tous sauf l'émetteur, sinon
  envoi au client dont le nœud correspond. À ajouter au protocole d'origine : anti-usurpation (nœud source = expéditeur),
  suivi d'un changement de port NAT pour la même IP, oubli des muets, limite de débit par client, et une requête d'état
  dont la réponse est plus petite que la requête (pas d'amplification). Voir `C:\MCM_Online\relay\mcm_relay.py`.
- Hébergement : une machine allumée en permanence (Raspberry Pi) + **un seul port UDP** redirigé sur la box.
  Freebox en IPv4 partagée : seuls les ports 32768-49151 sont redirigeables. Le retour en boucle (« hairpin ») marche
  sur Freebox : les joueurs de la maison peuvent viser l'IP publique.

## 3. DirectPlay sur Windows 10/11 sans droits admin

- DirectPlay est un **composant facultatif** : `fondue.exe /enable-feature:DirectPlay` ouvre la fenêtre officielle
  « Installer cette fonctionnalité ». Vérifier : `SysWOW64\dplayx.dll` + clé `HKLM\…\DirectPlay\Service Providers` (vue 32 bits).
- Le fournisseur IPX doit être déclaré dans HKLM (`Service Providers\IPX Connection For DirectPlay` + `Services\{5146ab8c…}`,
  valeurs dans `dplay-setup.c` d'IPXWrapper). **La virtualisation UAC (VirtualStore) ne s'applique pas ici**, et les jeux
  Microsoft Games lisent aussi leurs clés d'installation dans HKLM.
- **Astuce zéro admin** : une DLL relais posée dans le dossier du jeu, sur une DLL qu'il importe et qui n'est **pas** une
  KnownDLL (ex. `dinput.dll`), qui pose des crochets **MinHook** sur `RegOpenKey*/RegCreateKey*` d'advapi32 et redirige
  `HKLM\Software\Microsoft\DirectPlay\…` et les clés du jeu vers `HKCU\Software\<Projet>\HKLM\…` (rempli par le lanceur).
  Ça couvre aussi les lectures faites par `dplayx.dll` lui-même. Penser à `LoadLibraryW(L"advapi32.dll")` avant
  `MH_CreateHookApi`, sinon aucun crochet dans un programme qui ne l'importe pas encore. Sous Wine, inutile (pas d'UAC).
- Recopier dans HKCU les fournisseurs du système (TCP/IP…) : le nom « Internet TCP/IP Connection For DirectPlay »
  contient un « / » que `New-Item` PowerShell prend pour un séparateur → passer par l'API .NET.

## 4. Faire tourner le jeu lui-même sur Windows 10/11 (pièges vus)

| Symptôme | Cause | Remède |
|---|---|---|
| Le jeu quitte sur sa vidéo d'intro ; journal « décodeurs Indeo IV50 nécessaires » | Indeo retiré de Windows | Réencoder les AVI en **Cinepak** (`ffmpeg -c:v cinepak -max_extra_cb_iterations 0 -c:a copy`), lu par Windows ET Wine. Encodeur lent et mono-thread : un fichier par cœur, et un cache |
| « Erreur d'installation, réinstallez » | clés HKLM absentes | reprendre le `[Registry]` de l'installeur (Inno : `innounp -x setup.exe install_script.iss`) |
| Test de CD refusé malgré les clés | chemins absolus | l'installeur d'origine mettait `.\` (relatif au dossier du jeu) |
| Le jeu quitte (code 1) au lancement par script | DirectInput `DIERR_OTHERAPPHASPRIO` : fenêtre sans focus | lancer depuis un processus au premier plan (lanceur, double-clic) |
| DLL `d3drm.dll` manquante | Direct3D Retained Mode retiré depuis Vista | livrer celui de XP à côté de l'exe |
| Musique CD → MP3 (`_inmm.dll`) : « Registry information is invalid » | réglages d'_inmm absents | `HKCU\Software\irori\_inmm.dll` (+ `\Player`) |
| Affichage | DirectDraw / D3D 5-7 | dgVoodoo2 (déjà dans les « versions automatiques » d'Abandonware France) |

## 5. Tester le réseau SANS le jeu (et sans voler l'écran de quelqu'un)

`tools/dptool.c` des sources d'IPXWrapper = petit client DirectPlay en ligne de commande (`create_session`,
`list_sessions`, `join_session`, `send_message`). Compilable avec MSVC 32 bits + `dplay.h` d'IPXWrapper
(`/DDUMMYUNIONNAME1=`). Deux processus, chacun dans un dossier avec les DLL d'IPXWrapper : l'un crée, l'autre voit,
rejoint, et le message passe par le **vrai** relais. Script : `C:\MCM_Online\native\test\dp_relay_test.py`.

## 6. Tracer ce que fait un vieux jeu (Frida, sans débogueur)

`pip install frida` puis lancer le jeu suspendu (`device.spawn`) et poser des `Interceptor.attach` sur :
`RegOpenKeyExA/W` + `RegQueryValueExA` (clés lues), `ntdll!NtOpenKeyEx/NtQueryValueKey` (le vrai chemin, après
redirections), `kernel32!OutputDebugStringA` (les jeux y écrivent leurs erreurs DirectX !), `ExitProcess` /
`TerminateProcess` avec `Thread.backtrace`, et `Process.setExceptionHandler`. Exemples : `C:\MCM_Online\tools\`
(`run_redirected.py` sert aussi de redirection de registre « à chaud » pour tester avant d'écrire la DLL).

## 7. Distribuer à la famille (un lien, zéro réglage)

- Page + données sur **Cloudflare Pages** (gratuit, sans limite de trafic) : **25 Mio max par fichier** → zip
  déterministe découpé en morceaux de 24 Mio + `manifest.json` (tailles, SHA-256). R2 demande d'activer la facturation.
- Lanceur Windows **.NET Framework 4.8** (présent sur tout Windows 10/11), un seul exe : s'installe dans
  `%LOCALAPPDATA%`, télécharge et vérifie les morceaux, règle le registre, lance le jeu. Adresse du site gravée au build
  (`AssemblyMetadata`). Exe non signé → prévenir pour SmartScreen (« Informations complémentaires » → « Exécuter quand même »).
- **Mac** : builds Wine officiels WineHQ de Gcenx (`Gcenx/macOS_Wine_builds`, `wine-stable-11.0_1`, 32 bits OK via
  WoW64) + script `curl … | bash` (rien n'est mis en quarantaine) qui crée une vraie `.app`. JSON lu avec JavaScript for
  Automation (`osascript -l JavaScript`) car python3 n'est plus livré. DLL d'IPXWrapper forcées en natif par jeu
  (`HKCU\Software\Wine\AppDefaults\<exe>\DllOverrides`).
- Envoi vers Cloudflare : forcer l'IPv4 (`node --dns-result-order=ipv4first …wrangler… pages deploy`) si l'IPv6 est bridé.

## Alternatives écartées (et pourquoi)

- **VPN maillé** (Tailscale, ZeroTier) : à installer partout avec droits admin, compte ou clé partagée ; Tailscale ne
  transporte pas la diffusion (pas de liste de parties) ; mode TCP/IP de DirectPlay souvent limité à 4 joueurs.
- **Jeu dans le navigateur** (Boxedwine, v86) : trop lent pour un jeu 3D de cette époque, et pas d'UDP dans un navigateur.
- **Lobby DirectPlay** (`IDirectPlayLobby::RunApplication`) : possible si le jeu est « lobbyable », mais inutile quand
  la liste IPX marche ; à garder pour un futur bouton « Rejoindre » direct.
