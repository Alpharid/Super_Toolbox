#!/usr/bin/env bash
# Vérifie une page HTML de décisions (ou toute page faite à la main) avant de l'ouvrir au propriétaire. Guide : guides/pages-de-decisions.md
#   sh verifier_page.sh page.html [autre.html …]
# 1. chaque <script> en ligne passe `node --check` (une apostrophe non échappée dans un texte casse toute la page : bouton mort) ;
# 2. la page a un fond sombre déclaré (body ou :root) ; 3. elle a un bouton « Copier » ; 4. les images locales citées existent.
code=0
for page in "$@"; do
  [ -f "$page" ] || { echo "ERREUR: $page introuvable"; code=1; continue; }
  dossier=$(dirname "$page"); tmp=$(mktemp -d)
  python - "$page" "$tmp" <<'PY'
import re, sys, os
src = open(sys.argv[1], encoding="utf-8").read()
for i, m in enumerate(re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)):
    open(os.path.join(sys.argv[2], f"s{i}.js"), "w", encoding="utf-8").write(m.group(1))
PY
  for js in "$tmp"/*.js; do
    [ -f "$js" ] || continue
    if ! node --check "$js" 2>"$tmp/err"; then echo "ERREUR: $page : script invalide"; sed -n 1,6p "$tmp/err"; code=1; fi
  done
  grep -qiE 'color-scheme:\s*dark|--fond:\s*#[0-2]|background:\s*#[0-2][0-9a-f]{2}' "$page" || { echo "ATTENTION: $page : pas de fond sombre repéré"; code=1; }
  grep -qi 'copier' "$page" || echo "ATTENTION: $page : pas de bouton Copier"
  for img in $(grep -oE "src=[\"'][^\"':]+\.(png|jpe?g|webp|gif|svg)" "$page" | sed -E "s/src=[\"']//" | sort -u); do
    [ -f "$dossier/$img" ] || echo "ATTENTION: $page : image absente : $img"
  done
  rm -rf "$tmp"
  [ $code -eq 0 ] && echo "OK: $page"
done
exit $code
