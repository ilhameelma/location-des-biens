# ============================================================
# SmartRent — Sauvegarde PostgreSQL chiffrée (local Windows)
# ============================================================
# Usage :
#   .\backup_smartrent.ps1
#
# Prérequis :
#   - Docker Desktop lancé, conteneur smartrent_postgres actif
#   - age.exe présent dans .\age\age.exe (voir README pour l'installation)
#   - AGE_PUBLIC_KEY renseignée ci-dessous (jamais la clé privée ici)
# ============================================================

$ErrorActionPreference = "Stop"

# --- Configuration ---
$PgContainer   = "smartrent_postgres"
$PgUser        = "smartrent"
$PgDatabase    = "smartrent_db"
$BackupDir     = ".\backups"
$AgeExe        = "age.exe"
# Remplace par TA clé publique générée avec age-keygen (celle-ci est un exemple) :
$AgePublicKey  = "age1x7lrl6ll77auzstpqgn4ptrzxcpnrna4e22mzfx2cd705atfwf2q2mtmym"
$RetentionDays = 14   # sauvegardes plus anciennes que ça sont supprimées automatiquement

# --- Préparation ---
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}
# age.exe est dans le PATH utilisateur (pas un chemin relatif) -> on vérifie via Get-Command
if (-not (Get-Command $AgeExe -ErrorAction SilentlyContinue)) {
    Write-Error "age.exe introuvable dans le PATH — vérifie l'installation (age --version doit fonctionner)."
}
if ($AgePublicKey -eq "age1REMPLACE_PAR_TA_CLE_PUBLIQUE") {
    Write-Error "Renseigne ta vraie clé publique age dans la variable `$AgePublicKey avant de continuer."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutFile   = Join-Path $BackupDir "smartrent_backup_$Timestamp.sql.age"

Write-Host "Sauvegarde de la base '$PgDatabase' en cours..." -ForegroundColor Cyan

# --- Dump + chiffrement en un seul pipeline (le SQL en clair ne touche jamais le disque) ---
docker exec $PgContainer pg_dump -U $PgUser $PgDatabase | & $AgeExe -r $AgePublicKey -o $OutFile

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $OutFile)) {
    Write-Error "Échec de la sauvegarde — vérifie que le conteneur '$PgContainer' est bien lancé (docker compose ps)."
}

$Size = (Get-Item $OutFile).Length / 1KB
Write-Host "OK : $OutFile ($([math]::Round($Size, 1)) Ko)" -ForegroundColor Green

# --- Purge des sauvegardes trop anciennes ---
$CutoffDate = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $BackupDir -Filter "smartrent_backup_*.sql.age" |
    Where-Object { $_.LastWriteTime -lt $CutoffDate } |
    ForEach-Object {
        Write-Host "Suppression de l'ancienne sauvegarde : $($_.Name)" -ForegroundColor Yellow
        Remove-Item $_.FullName
    }

Write-Host "Terminé." -ForegroundColor Cyan
