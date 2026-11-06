# Pages de décisions (faire trancher le propriétaire sans perdre le fil)

> Méthode préférée du propriétaire : quand plusieurs décisions attendent, **une page HTML locale** (ouverte aussitôt dans son
> navigateur) plutôt qu'une liste dans le terminal, où il perd le fil. Gabarit : `guides/modeles/page-de-decisions.html`.

## Ce que la page contient
1. Un titre court et versionné (`boussole_v7`, `emplacements_v2`) et, en deux lignes, d'où viennent les questions.
2. **Une question par bloc**, avec de quoi juger sur pièce (images à la taille réelle **et** en zoom, extraits audio, captures en jeu).
3. Des réponses à cocher ; **la préférence de l'agent marquée « mon choix » et cochée d'avance** (le propriétaire n'a plus qu'à
   corriger ce qui ne lui va pas) ; un champ « autre / remarque » par question ; des notes libres en bas.
4. Un bouton **« Copier mes réponses »** qui compose un texte numéroté à recoller dans la conversation (repli `prompt()` si le
   presse-papiers est refusé, en `file://` notamment).

## Règles
- **Toujours sombre** (la page s'ouvre souvent la nuit ; une page claire a « flashbang » le propriétaire).
- **Vérifier avant d'ouvrir** : `sh D:/Super_Toolbox/scripts/verifier_page.sh page.html` : `node --check` de chaque script (une
  apostrophe non échappée dans un texte casse tout et le bouton ne copie plus rien : vu), fond sombre, bouton Copier, images présentes.
- Ouvrir la page tout de suite sur l'écran du propriétaire (son navigateur, pas celui par défaut si ce n'est pas le même) et la noter
  dans la fiche du chantier (« EN ATTENTE : page X ouverte »).
- Ses réponses arrivent recopiées : les consigner **dans la doc du projet** (décisions datées), puis seulement les appliquer.
- Pas de page pour une seule question évidente : une ligne dans la conversation suffit. Pas de page « pour lire » déguisée en page
  de décisions.
- Audio lourd : le service de pages de claude.ai refuse les gros fichiers ; servir la page en local (`python -m http.server`) et
  la partager par un tunnel (`cloudflared tunnel --url http://127.0.0.1:<port>`) si quelqu'un d'autre doit écouter.
