# SGEO — Unified SEO + GEO Master Audit Skill
# Uninstall script for Windows (PowerShell)

$ErrorActionPreference = "Stop"

$SkillName = "sgeo"
$ClaudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$LinkPath = Join-Path $ClaudeSkillsDir $SkillName

function Write-Info  { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Ok    { param($msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "+==============================================+"
Write-Host "|  SGEO - Uninstaller (Windows)                |"
Write-Host "+==============================================+"
Write-Host ""

if (Test-Path $LinkPath) {
    $item = Get-Item $LinkPath -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Info "Removing link: $LinkPath"
        Remove-Item $LinkPath -Force
        Write-Ok "Link removed"
    } else {
        Write-Warn "$LinkPath exists but is not a junction/symlink. Remove manually."
    }
} else {
    Write-Info "Link not found (already removed or never installed)"
}

Write-Host ""
Write-Host "================================================"
Write-Host "Uninstall complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: This script only removes the Claude CLI link."
Write-Host "The skill directory remains at its original location."
Write-Host "To fully remove, delete the skill directory manually."
Write-Host "================================================"
