# Ouvre un terminal Claude Code dédié à UN chantier (une fiche = une session). Guide : guides/orchestrer-des-chantiers.md
# Usage (depuis la racine d'un projet, ou -Racine) :
#   powershell -ExecutionPolicy Bypass -File D:\Super_Toolbox\scripts\chantiers\chantier.ps1 -Nom onglets-chat [-Racine C:\MonProjet]
# La session lit le CLAUDE.md du projet (chargé d'office) puis <Racine>\docs\chantiers\<Nom>.md, fait le chantier, met la fiche à jour
# et dit quand c'est fini (l'orchestrateur ferme alors le terminal).
#
# Deux temps : sans -Session, ouvre un onglet de Windows Terminal qui relance ce script avec -Session ; avec -Session, lance claude.
# Pourquoi : claude est un claude.cmd (npm) que wt ne trouve pas sans extension (erreur 0x80070002), et la consigne (espaces,
# apostrophes, accents) passe mal à travers wt ; dans PowerShell, `claude` se résout et la consigne reste intacte.
# Ce fichier est en UTF-8 AVEC BOM : sans BOM, PowerShell 5.1 le lit en ANSI et abîme les accents de la consigne.
# -SansAutorisation : lance claude avec --dangerously-skip-permissions (seulement si le propriétaire l'a décidé pour ce projet).
param([Parameter(Mandatory = $true)][string]$Nom, [string]$Racine = (Get-Location).Path, [string]$Fiches = "docs\chantiers",
      [switch]$SansAutorisation, [switch]$Session)
$fiche = Join-Path $Racine (Join-Path $Fiches "$Nom.md")
if (-not (Test-Path $fiche)) { Write-Error "Pas de fiche : $fiche"; exit 1 }
if ($Session) {
    Set-Location $Racine
    $rel = ($Fiches -replace '\', '/') + "/$Nom.md"
    # La session ne s'arrête jamais pour attendre : l'orchestrateur ne peut pas écrire dans ce terminal, il dépose les réponses du
    # propriétaire dans la fiche sous un titre qui contient « À TRAITER » (guide § L'orchestrateur ; Guardians, 2026-11-07).
    $consigne = "Chantier $Nom. Lis $rel et fais ce qu'elle demande, rien d'autre. Mets la fiche à jour au fil de l'eau (état en tête). " +
        "Ne t'arrête jamais pour attendre : si une décision du propriétaire manque, fais sa page de décision (sombre, Copier), ouvre-la, " +
        "et continue tout ce qui n'en dépend pas. Quand il ne reste rien à faire sans lui, ne pose pas de question dans ce terminal : surveille ta fiche " +
        "(en arrière-plan : until grep -q 'À TRAITER' $rel; do sleep 120; done), l'orchestrateur y dépose ses réponses sous un titre " +
        "« À TRAITER » ; traite-les, remplace « À TRAITER » par « traitées », et continue. Si le chantier est entièrement fini, dis-le en quelques lignes."
    if ($SansAutorisation) { claude --dangerously-skip-permissions $consigne } else { claude $consigne }
    exit
}
$args2 = @('-NoExit', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Nom', $Nom, '-Racine', $Racine, '-Fiches', $Fiches, '-Session')
if ($SansAutorisation) { $args2 += '-SansAutorisation' }
wt -w 0 nt -d $Racine --title "$(Split-Path -Leaf $Racine) : $Nom" powershell @args2
