#!/usr/bin/env bash
# État des chantiers ouverts (un terminal Claude par fiche : chantier.ps1). Pour l'orchestrateur, AVANT de dire « tout tourne » :
# pour chaque session ouverte, l'état écrit en tête de sa fiche, l'âge de la fiche, et des alertes. Guide : guides/orchestrer-des-chantiers.md
# Leçon d'origine : une session a attendu 4 h des réponses recopiées dans sa fiche par une AUTRE session (une session ne relit pas sa
# fiche toute seule : réponses déposées par un autre = relancer la session).
# Usage : sh chantiers_etat.sh [racine du projet] [dossier des fiches, défaut docs/chantiers] [dossiers à surveiller, défaut « . »]
cd "${1:-.}" || exit 1
FICHES="${2:-docs/chantiers}"
SURVEILLER="${3:-.}"
maintenant=$(date +%s)
ouverts=$(powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'powershell.exe' -and \$_.CommandLine -match '-File \S*chantier\.ps1 -Nom \S+ .*-Session' } | ForEach-Object { (\$_.CommandLine -replace '.*-Nom\s+(\S+).*','\$1') + ' ' + \$_.CreationDate.ToString('HH:mm') }" | tr -d '\r')
[ -z "$ouverts" ] && { echo "Aucune session de chantier ouverte."; exit 0; }
echo "$ouverts" | while read -r nom debut; do
  fiche="$FICHES/$nom.md"
  [ -f "$fiche" ] || { echo "== $nom : PAS DE FICHE ICI ($fiche)"; continue; }
  age_fiche=$(( (maintenant - $(stat -c %Y "$fiche")) / 60 ))
  etat=$(grep -m1 -E "^## .*REPRENDRE ICI" "$fiche" | cut -c4-170)
  [ -z "$etat" ] && etat=$(grep -m1 -iE "^## .*(attente|fini|clos|interrompu|en cours)" "$fiche" | cut -c4-170)
  echo "== $nom (session ouverte à $debut) : fiche touchée il y a ${age_fiche} min"
  echo "   état : ${etat:-(aucun en-tête d'état)}"
  if echo "$etat" | grep -qiE "Réponses.*REPRENDRE|REPRENDRE.*Réponses"; then
    [ "$age_fiche" -ge 20 ] && echo "   !! des réponses attendent depuis ${age_fiche} min : la session les a-t-elle vues ? (sinon la relancer)"
  fi
  # réponses déposées par l'orchestrateur sous un titre « À TRAITER » (la session les remplace par « traitées » une fois faites)
  if grep -qE "^#+ .*À TRAITER" "$fiche" && [ "$age_fiche" -ge 20 ]; then
    echo "   !! « À TRAITER » dans la fiche depuis ${age_fiche} min sans qu'elle bouge : la session surveille-t-elle sa fiche ? (sinon la relancer)"
  fi
  echo "$etat" | grep -qiE "FINI|CLOS" && echo "   -> fini : fermer son terminal (après avoir vérifié que tout est commité)"
  echo "$etat" | grep -qiE "attente" && echo "   -> attend le propriétaire : sa page est-elle ouverte, sombre, avec un bouton Copier qui marche ?"
done
echo "== activité (fichiers changés depuis 20 min, par dossier)"
find $SURVEILLER -mmin -20 -type f -not -path '*/.git/*' 2>/dev/null | grep -vE '\.import$|/\.godot/|node_modules' \
  | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -10
