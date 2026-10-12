# Gestion des dépôts tiers du kit (git subtree --squash), liste dans upstreams.json.
#   powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 list
#   powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check  [-Name rea]        # nouveautés en amont (rien n'est modifié)
#   powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 verify                    # santé du kit : dossiers, synchro, patches locaux
#   powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 update -Name rea [-Push]  # intègre la dernière version (commit local)
#   powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 add -Name x -Url https://github.com/a/x [-Branch main] [-Category listes] [-Role "..."] [-Push]
#   Catégories : modding (outils de mod / RE), physique (moteurs, contraintes, IK, destruction), godot (addons Godot 4),
#   dev (bibliothèques et outils de création), listes (listes de ressources).
# Sortie : lignes « OK: … » / « ERREUR: … ». Le dépôt local est le dossier parent de scripts\.
param(
    [Parameter(Position = 0)][ValidateSet("list", "check", "update", "add", "verify")][string]$Action = "list",
    [string]$Name,
    [string]$Url,
    [string]$Branch,
    [string]$Role = "",
    [string]$Category = "dev",
    [int]$Max = 25,
    [switch]$Push
)
$ErrorActionPreference = "Stop"
$racine = Split-Path $PSScriptRoot -Parent
$fichier = Join-Path $racine "upstreams.json"
Set-Location -LiteralPath $racine

function Lire { Get-Content -LiteralPath $fichier -Raw -Encoding UTF8 | ConvertFrom-Json }
function Ecrire($cfg) {
    $json = $cfg | ConvertTo-Json -Depth 5
    [IO.File]::WriteAllText($fichier, $json + "`n", (New-Object Text.UTF8Encoding $false))
}
# git écrit ses messages normaux sur stderr : en PowerShell 5.1 il ne faut pas les traiter comme des erreurs.
function Invoke-Git {
    $ErrorActionPreference = "Continue"
    $out = & git.exe @args 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') : $($out -join ' ')" }
    $out | Where-Object { $_ -notmatch '^(From |remote: |warning: )' -and $_ -notmatch '^\s+\S+\.\.\S+\s' -and $_ -notmatch '^ \* ' }
}
function Distant($r) {
    $nom = "up-" + $r.name
    if (-not ((& git.exe remote) -contains $nom)) { Invoke-Git remote add $nom $r.url | Out-Null }
    Invoke-Git fetch -q $nom $r.branch | Out-Null
    return "$nom/$($r.branch)"
}
function Choisir($cfg) {
    if (-not $Name) { return $cfg.repos }
    $r = @($cfg.repos | Where-Object { $_.name -eq $Name })
    if (-not $r) { throw "dépôt inconnu : $Name (voir : kit.ps1 list)" }
    return $r
}
function Propre {
    if (& git.exe status --porcelain) { throw "le dépôt a des modifications non commitées : commite-les ou annule-les d'abord." }
}

try {
    $cfg = Lire
    switch ($Action) {
        "list" {
            foreach ($r in $cfg.repos) {
                "{0,-20} [{1}] {2}  (synchro {3} le {4})" -f $r.name, $r.category, $r.prefix, $r.synced_commit, $r.synced_on
                "{0,-20} {1}" -f "", $r.role
            }
        }
        "check" {
            foreach ($r in (Choisir $cfg)) {
                $ref = Distant $r
                $tete = (Invoke-Git rev-parse --short=8 $ref).Trim()
                $n = [int](Invoke-Git rev-list --count "$($r.synced_commit)..$ref")
                if ($n -eq 0) { "OK: $($r.name) est à jour ($tete)."; continue }
                "OK: $($r.name) : $n nouveau(x) commit(s) en amont ($($r.synced_commit) -> $tete). Les plus récents :"
                Invoke-Git log --no-merges --date=short --format="   %ad %h %s" -n $Max "$($r.synced_commit)..$ref"
                "   Fichiers : " + ((Invoke-Git diff --stat "$($r.synced_commit)" $ref | Select-Object -Last 1) -join "").Trim()
                "   Détail d'un commit : git show --stat <hash>   ·   Intégrer : kit.ps1 update -Name $($r.name)"
            }
        }
        "update" {
            if (-not $Name) { throw "précise -Name (une mise à jour à la fois, après avoir lu kit.ps1 check)." }
            Propre
            $r = (Choisir $cfg)[0]
            $ref = Distant $r
            $tete = (Invoke-Git rev-parse --short=8 $ref).Trim()
            if ($tete -eq $r.synced_commit) { "OK: $($r.name) déjà à jour ($tete)."; break }
            Invoke-Git subtree pull --prefix=$($r.prefix) "up-$($r.name)" $r.branch --squash -m "MAJ $($r.name) : $($r.synced_commit) -> $tete" | Out-Null
            $r.synced_commit = $tete
            $r.synced_on = (Get-Date -Format "yyyy-MM-dd")
            Ecrire $cfg
            Invoke-Git add upstreams.json | Out-Null
            Invoke-Git commit -q -m "upstreams.json : $($r.name) synchronisé sur $tete" | Out-Null
            "OK: $($r.name) mis à jour ($tete). Pense à noter les changements utiles dans HANDOVER.md (Historique)."
            if ($Push) { Invoke-Git push -q origin main | Out-Null; "OK: poussé sur GitHub." }
        }
        "verify" {
            # Pour chaque dépôt : dossier présent, dernier squash du subtree = commit noté, commits locaux qui touchent upstream/<nom>.
            $problemes = 0
            foreach ($r in $cfg.repos) {
                $dir = Join-Path $racine $r.prefix
                if (-not (Test-Path -LiteralPath $dir)) { "ERREUR: $($r.name) : dossier $($r.prefix) absent."; $problemes++; continue }
                $msg = (& git.exe log -n 1 --format=%B --grep="git-subtree-dir: $($r.prefix)$" 2>$null) -join "`n"
                if ($msg -notmatch "git-subtree-split: ([0-9a-f]{7,40})") { "ERREUR: $($r.name) : aucun commit subtree trouvé (dossier déplacé ou copié à la main ?)."; $problemes++; continue }
                $split = $Matches[1]
                if (-not $split.StartsWith($r.synced_commit)) { "ERREUR: $($r.name) : upstreams.json dit $($r.synced_commit), le subtree est sur $($split.Substring(0,8))."; $problemes++ }
                $locaux = @(& git.exe log --format="%h %s" -- $r.prefix 2>$null | Where-Object { $_ -notmatch "^\w+ (Squashed '|Ajout de |MAJ |Merge commit )" })
                if ($locaux) { "ATTENTION: $($r.name) : $($locaux.Count) commit(s) local(aux) dans $($r.prefix) (patch à documenter au §8 de HANDOVER.md) : $($locaux -join ' | ')" }
            }
            $orphelins = Get-ChildItem -LiteralPath (Join-Path $racine "upstream") -Directory | Where-Object { $n = $_.Name; -not ($cfg.repos | Where-Object { $_.prefix -eq "upstream/$n" }) }
            foreach ($o in $orphelins) { "ERREUR: upstream/$($o.Name) n'est pas dans upstreams.json."; $problemes++ }
            if ($problemes -eq 0) { "OK: $(@($cfg.repos).Count) dépôts vérifiés, kit cohérent." } else { throw "$problemes problème(s)." }
        }
        "add" {
            if (-not $Name -or -not $Url) { throw "précise -Name et -Url." }
            if ($cfg.repos | Where-Object { $_.name -eq $Name }) { throw "$Name existe déjà." }
            Propre
            if (-not $Branch) {
                $sym = & git.exe ls-remote --symref $Url HEAD 2>$null | Select-Object -First 1
                $Branch = if ($sym -match "refs/heads/(\S+)") { $Matches[1] } else { "main" }
            }
            $r = [pscustomobject]@{ name = $Name; url = $Url; branch = $Branch; prefix = "upstream/$Name"; license = "?"; category = $Category; role = $Role; synced_commit = ""; synced_on = "" }
            $ref = Distant $r
            Invoke-Git subtree add --prefix=$($r.prefix) "up-$Name" $Branch --squash -m "Ajout de $Name en subtree" | Out-Null
            $r.synced_commit = (Invoke-Git rev-parse --short=8 $ref).Trim()
            $r.synced_on = (Get-Date -Format "yyyy-MM-dd")
            # Licence : identifiant SPDX donné par GitHub, sinon 1re ligne du fichier LICENSE
            if ($Url -match 'github\.com[/:]([^/]+)/([^/.]+)') {
                $spdx = & gh api "repos/$($Matches[1])/$($Matches[2])/license" --jq .license.spdx_id 2>$null
                if ($LASTEXITCODE -eq 0 -and $spdx -and $spdx -ne "NOASSERTION") { $r.license = "$spdx".Trim() }
            }
            $lic = Get-ChildItem -LiteralPath (Join-Path $racine $r.prefix) -Filter "LICENSE*" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($r.license -eq "?" -and $lic) { $r.license = ((Get-Content -LiteralPath $lic.FullName -TotalCount 1 -Encoding UTF8) -join "").Trim() }
            if ($r.license -eq "?") { Write-Host "ATTENTION : pas de licence trouvée pour $Name (tous droits réservés ?) : vérifier avant de le garder." -ForegroundColor Yellow }
            $cfg.repos += $r
            Ecrire $cfg
            Invoke-Git add upstreams.json | Out-Null
            Invoke-Git commit -q -m "upstreams.json : ajout de $Name" | Out-Null
            "OK: $Name ajouté dans $($r.prefix) ($($r.synced_commit), licence : $($r.license)). Documente-le dans HANDOVER.md et CATALOGUE.md."
            if ($Push) { Invoke-Git push -q origin main | Out-Null; "OK: poussé sur GitHub." }
        }
    }
}
catch {
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
