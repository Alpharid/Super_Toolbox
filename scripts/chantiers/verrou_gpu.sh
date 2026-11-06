#!/bin/sh
# File d'attente du GPU (et des tâches lourdes) partagée par plusieurs sessions ou agents d'un même projet. Guide : guides/orchestrer-des-chantiers.md
#
#   sh verrou_gpu.sh <nom> <commande…>     # attend son tour, lance la commande, rend la main
#   sh verrou_gpu.sh --etat                # qui tient le verrou, qui attend
#
# Chacun prend un ticket horodaté dans $GPU_FILE (défaut .file_gpu/ dans le dossier courant) ; on passe dans l'ordre d'arrivée, pas de
# resquille, même pour un script qui enchaîne plusieurs tâches (un ticket par étape : rendre la main entre deux étapes laisse passer
# les autres). La prise est atomique (mkdir). Les tickets de processus morts sont retirés : la file ne reste jamais bloquée.
# Mettre .file_gpu/, .verrou_gpu et .verrou_gpu.d/ dans le .gitignore du projet.
FILE="${GPU_FILE:-.file_gpu}"
VERROU="${FILE%/}/../.verrou_gpu"
DOSSIER="${FILE%/}/../.verrou_gpu.d"
mkdir -p "$FILE"

if [ "$1" = "--etat" ]; then
  [ -f "$VERROU" ] && echo "tenu par : $(cat "$VERROU")" || echo "libre"
  ls "$FILE" 2>/dev/null | sed 's/^/en file : /'
  exit 0
fi

NOM="$1"; shift
[ -n "$NOM" ] && [ $# -gt 0 ] || { echo "usage : verrou_gpu.sh <nom> <commande…>"; exit 2; }
TICKET="$FILE/$(date +%s%N)_$(echo "$NOM" | tr -c 'A-Za-z0-9_-' '_')"
echo $$ > "$TICKET"
rendre() {
  rm -f "$TICKET"
  if [ -f "$DOSSIER/ticket" ] && [ "$(cat "$DOSSIER/ticket")" = "$TICKET" ]; then
    rm -f "$VERROU"; rm -rf "$DOSSIER"
  fi
}
trap rendre EXIT INT TERM

vivant() { [ -n "$1" ] && kill -0 "$1" 2>/dev/null; }
while :; do
  for t in "$FILE"/*; do
    [ -f "$t" ] && [ "$t" != "$TICKET" ] && ! vivant "$(cat "$t" 2>/dev/null)" && rm -f "$t"
  done
  if [ -d "$DOSSIER" ] && [ ! -f "$(cat "$DOSSIER/ticket" 2>/dev/null)" ]; then rm -f "$VERROU"; rm -rf "$DOSSIER"; fi
  PREMIER="$FILE/$(ls "$FILE" | sort | head -1)"
  if [ "$PREMIER" = "$TICKET" ] && [ ! -f "$VERROU" ] && mkdir "$DOSSIER" 2>/dev/null; then
    echo "$TICKET" > "$DOSSIER/ticket"
    echo "$NOM $(date +%H:%M)" > "$VERROU"
    break
  fi
  sleep 2
done

"$@"
