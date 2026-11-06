# Execute from the OpenD578 root in Windows PowerShell 5+ or PowerShell 7.
# Private archives are stored OUTSIDE the Git repository by default.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path (Split-Path -Parent $root) 'OpenD578_archives_privees'
Write-Host "Destination privee: $dest"
py -3 (Join-Path $PSScriptRoot 'archive_sources_privees.py') --destination $dest --sites f1dmg theweeks vk7zja_v74 vk7zja_mirror vk7zja_authorised_mirror oz1dgq --wayback --max-pages 300 --max-assets 2500
if ($LASTEXITCODE -ne 0) { Write-Warning "Certains sites n'ont pas repondu. Examiner les fichiers manifest.json et INDEX.md." }
