# Heimdall — le veilleur de la Super_Toolbox.
# Partie MÉCANIQUE de la veille (données, squelettes, raccourcis). L'intelligence — lire le web, juger
# ce qui est pertinent — est faite par Claude en suivant heimdall\README.md. Ici : où regarder, quoi nourrir.
#
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 domains
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 sources  [-Domain godot]
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 projects
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 project  -Name Stryder_Symbiosis
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 brief    [-Domain godot]   # ce qu'il faut donner à Claude pour la veille
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 report                     # crée reports\AAAA-MM-JJ.md (squelette)
#   powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 log                        # liste les digests passés
# Sortie : lignes « OK: … » / « ERREUR: … ». Le dépôt local est le dossier parent de heimdall\.
param(
    [Parameter(Position = 0)][ValidateSet("domains", "sources", "projects", "project", "brief", "report", "log")][string]$Action = "domains",
    [string]$Domain,
    [string]$Name
)
$ErrorActionPreference = "Stop"
$heimdall = $PSScriptRoot
$racine = Split-Path $heimdall -Parent
$fSources = Join-Path $heimdall "sources.json"
$fProjects = Join-Path $heimdall "projects.json"
$dirReports = Join-Path $heimdall "reports"

function Lire($f) { Get-Content -LiteralPath $f -Raw -Encoding UTF8 | ConvertFrom-Json }
function Domaines() { (Lire $fSources).domaines }
function Projets() { (Lire $fProjects).projets }
function NomsDomaines($d) { $d.PSObject.Properties.Name }

switch ($Action) {
    "domains" {
        $d = Domaines
        foreach ($id in NomsDomaines $d) {
            $n = ($d.$id.sources | Measure-Object).Count
            Write-Output ("OK: {0,-18} {1}  ({2} sources)" -f $id, $d.$id.nom, $n)
        }
    }
    "sources" {
        $d = Domaines
        $ids = if ($Domain) { @($Domain) } else { NomsDomaines $d }
        foreach ($id in $ids) {
            if (-not $d.$id) { Write-Output "ERREUR: domaine inconnu : $id"; continue }
            Write-Output "== $id — $($d.$id.nom) =="
            foreach ($s in $d.$id.sources) { Write-Output ("OK: [{0,-9}] {1}  ->  {2}" -f $s.type, $s.nom, $s.url) }
        }
    }
    "projects" {
        $p = Projets
        foreach ($n in $p.PSObject.Properties.Name) {
            Write-Output ("OK: {0,-20} [{1}]  {2}" -f $n, ($p.$n.domaines -join ","), $p.$n.resume)
        }
    }
    "project" {
        if (-not $Name) { throw "ERREUR: -Name requis (ex. -Name Stryder_Symbiosis)" }
        $p = Projets
        if (-not $p.$Name) { throw "ERREUR: projet inconnu : $Name (voir : heimdall.ps1 projects)" }
        $x = $p.$Name
        Write-Output "== $Name — $($x.resume) =="
        Write-Output ("OK: chemin   : {0}" -f $x.chemin)
        Write-Output ("OK: domaines : {0}" -f ($x.domaines -join ", "))
        Write-Output ("OK: outils kit: {0}" -f (($x.outils_kit -join ", ") -replace '^$', '(aucun pour l''instant)'))
        if ($x.guide) { Write-Output ("OK: guide    : {0}" -f $x.guide) }
        if ($x.manques) { foreach ($m in $x.manques) { Write-Output ("OK: manque -> {0}" -f $m) } }
        if ($x.pistes) { Write-Output "-- PISTES repérées (à proposer ou utiliser) --"; foreach ($p in $x.pistes) { Write-Output ("OK: piste -> {0}" -f $p) } }
        if ($x.ligne_rouge) { Write-Output ("OK: LIGNE ROUGE : {0}" -f $x.ligne_rouge) }
    }
    "brief" {
        # Ce qu'on donne à Claude pour une passe de veille : domaines, sources, et outils du kit déjà présents (pour ne pas redoubler).
        $d = Domaines
        $ids = if ($Domain) { @($Domain) } else { NomsDomaines $d }
        Write-Output "== BRIEF DE VEILLE ($(Get-Date -Format yyyy-MM-dd)) =="
        foreach ($id in $ids) {
            if (-not $d.$id) { Write-Output "ERREUR: domaine inconnu : $id"; continue }
            Write-Output ""
            Write-Output "### $id — $($d.$id.nom)"
            Write-Output ("mots-clés : {0}" -f ($d.$id.mots_cles -join ", "))
            Write-Output "sources :"
            foreach ($s in $d.$id.sources) { Write-Output ("  - [{0}] {1} : {2}" -f $s.type, $s.nom, $s.url) }
        }
        Write-Output ""
        Write-Output "Consigne : pour chaque domaine, repérer les nouveautés/MAJ pertinentes, écarter ce qui est déjà"
        Write-Output "dans INDEX.md / upstream\, puis consigner dans reports\AAAA-MM-JJ.md (voir heimdall\README.md)."
    }
    "report" {
        if (-not (Test-Path $dirReports)) { New-Item -ItemType Directory -Path $dirReports | Out-Null }
        $stamp = Get-Date -Format "yyyy-MM-dd"
        $f = Join-Path $dirReports "$stamp.md"
        if (Test-Path $f) { Write-Output "OK: le digest du jour existe déjà : heimdall\reports\$stamp.md"; break }
        $d = Domaines
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.AppendLine("# Digest Heimdall — $stamp")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("> Veille de la Super_Toolbox. Pour chaque domaine : nouveautés/MAJ repérées, et ce qui mérite d'être ajouté (lien ou subtree) ou mis à jour. Format d'une trouvaille : **Nom** — ``owner/repo`` · licence · une phrase + pourquoi c'est pertinent.")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## À retenir (résumé)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("- _(à remplir : 3-5 points saillants)_")
        [void]$sb.AppendLine("")
        foreach ($id in NomsDomaines $d) {
            [void]$sb.AppendLine("## $($d.$id.nom)  [$id]")
            [void]$sb.AppendLine("")
            [void]$sb.AppendLine("- _(trouvailles)_")
            [void]$sb.AppendLine("")
        }
        [void]$sb.AppendLine("## Propositions d'ajout à la toolbox")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("| Outil | Domaine | Licence | Lien ou subtree ? | Pourquoi |")
        [void]$sb.AppendLine("|---|---|---|---|---|")
        [void]$sb.AppendLine("")
        [IO.File]::WriteAllText($f, $sb.ToString(), (New-Object Text.UTF8Encoding $false))
        Write-Output "OK: squelette créé : heimdall\reports\$stamp.md"
    }
    "log" {
        if (-not (Test-Path $dirReports)) { Write-Output "OK: aucun digest pour l'instant"; break }
        Get-ChildItem $dirReports -Filter *.md | Sort-Object Name -Descending | ForEach-Object {
            Write-Output ("OK: {0}" -f $_.Name)
        }
    }
}
