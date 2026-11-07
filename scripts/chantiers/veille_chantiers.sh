#!/usr/bin/env bash
# Veille de l'orchestrateur (guide : guides/orchestrer-des-chantiers.md § L'orchestrateur). Lancée en arrière-plan, elle rend la main
# (en sortant) dès qu'un chantier change d'état ou qu'une session se ferme (CHANGEMENT), quand aucun fichier n'a bougé depuis 30 min
# (CALME : session figée, limite d'usage ?), ou au bout de 45 min (POINT). L'orchestrateur agit, puis la relance.
# Né sur Guardians of the Seal (2026-11-07) : trois sessions sont restées figées une demi-journée sans que personne le voie.
# Usage : sh veille_chantiers.sh [racine du projet] [dossier des fiches, défaut docs/chantiers] [dossiers à surveiller, défaut « . »]
ICI="$(cd "$(dirname "$0")" && pwd)"
RACINE="${1:-.}"; FICHES="${2:-docs/chantiers}"; SURVEILLER="${3:-.}"
cd "$RACINE" || exit 1
signature() {
  sh "$ICI/chantiers_etat.sh" . "$FICHES" "$SURVEILLER" 2>/dev/null | grep -E "^== [a-z]|état :" | sed -E 's/fiche touchée il y a [0-9]+ min//'
}
avant=$(signature); debut=$(date +%s)
while true; do
  sleep 120
  apres=$(signature)
  if [ "$apres" != "$avant" ]; then echo "CHANGEMENT"; diff <(echo "$avant") <(echo "$apres"); exit 0; fi
  recent=$(find $SURVEILLER -type f -mmin -30 2>/dev/null | grep -vE '\.godot/|/\.git/|node_modules' | head -1)
  [ -z "$recent" ] && { echo "CALME : aucun fichier changé depuis 30 min"; echo "$apres"; exit 0; }
  [ $(( $(date +%s) - debut )) -ge 2700 ] && { echo "POINT : 45 min"; echo "$apres"; exit 0; }
done
