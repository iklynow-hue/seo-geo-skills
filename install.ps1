# SGEO — Unified SEO + GEO Master Audit Skill
# Install script for Windows (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillName = "sgeo"
$ClaudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$Requirements = @("requests", "beautifulsoup4", "lxml")

function Write-Info  { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Ok    { param($msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "+==============================================+"
Write-Host "|  SGEO - Unified SEO + GEO Master Audit       |"
Write-Host "|  Installer v1.0 (Windows)                    |"
Write-Host "+==============================================+"
Write-Host ""

# --- 1. Check Python ---
Write-Info "Checking Python..."
$PY = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PY = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PY = "python"
} else {
    Write-Fail "Python 3.8+ is required. Install from https://python.org"
}

$PyVersion = & $PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$PyMajor = & $PY -c "import sys; print(sys.version_info.major)"
$PyMinor = & $PY -c "import sys; print(sys.version_info.minor)"

if ([int]$PyMajor -lt 3 -or ([int]$PyMajor -eq 3 -and [int]$PyMinor -lt 8)) {
    Write-Fail "Python 3.8+ required. Found: $PyVersion"
}
Write-Ok "Python $PyVersion found"

# --- 2. Check pip ---
Write-Info "Checking pip..."
try {
    & $PY -m pip --version 2>&1 | Out-Null
} catch {
    Write-Warn "pip not found. Attempting to install..."
    & $PY -m ensurepip --default-pip 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Fail "Cannot install pip. Install manually." }
}
Write-Ok "pip available"

# --- 3. Install Python dependencies ---
Write-Info "Installing Python dependencies..."
& $PY -m pip install --quiet --upgrade $Requirements
Write-Ok "Dependencies installed: $($Requirements -join ', ')"

# --- 4. Optional: Playwright ---
$playwrightInstalled = & $PY -c "import playwright" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Playwright already installed (optional)"
} else {
    Write-Warn "Playwright not installed (optional - needed for screenshots)"
    Write-Host "    To install: pip install playwright && playwright install chromium"
}

# --- 5. Create Claude skills directory and junction ---
Write-Info "Setting up Claude CLI skill link..."
if (-not (Test-Path $ClaudeSkillsDir)) {
    New-Item -ItemType Directory -Path $ClaudeSkillsDir -Force | Out-Null
}

$LinkPath = Join-Path $ClaudeSkillsDir $SkillName

if (Test-Path $LinkPath) {
    $item = Get-Item $LinkPath -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        $existingTarget = (Get-Item $LinkPath).Target
        if ($existingTarget -eq $ScriptDir) {
            Write-Ok "Link already exists and points to correct location"
        } else {
            Write-Warn "Link exists but points to: $existingTarget"
            Write-Warn "Updating to: $ScriptDir"
            Remove-Item $LinkPath -Force
            New-Item -ItemType Junction -Path $LinkPath -Target $ScriptDir | Out-Null
            Write-Ok "Link updated"
        }
    } else {
        Write-Fail "$LinkPath exists but is not a junction/symlink. Remove it manually."
    }
} else {
    New-Item -ItemType Junction -Path $LinkPath -Target $ScriptDir | Out-Null
    Write-Ok "Junction created: $LinkPath -> $ScriptDir"
}

# --- 6. Verify installation ---
Write-Info "Verifying installation..."

$Errors = 0

# Check SKILL.md exists
if (Test-Path (Join-Path $ScriptDir "SKILL.md")) {
    Write-Ok "SKILL.md found"
} else {
    Write-Warn "SKILL.md not found"
    $Errors++
}

# Check key scripts exist
$scripts = @("fetch_page.py", "parse_html.py", "robots_checker.py", "citability_scorer.py", "schema_validator.py", "generate_report.py")
foreach ($script in $scripts) {
    $path = Join-Path $ScriptDir "scripts\$script"
    if (Test-Path $path) {
        Write-Ok "scripts/$script found"
    } else {
        Write-Warn "scripts/$script missing"
        $Errors++
    }
}

# Check references exist
$refs = @("mece-framework.md", "dual-scoring-methodology.md", "faqpage-guidance.md", "quality-gates.md")
foreach ($ref in $refs) {
    $path = Join-Path $ScriptDir "resources\references\$ref"
    if (Test-Path $path) {
        Write-Ok "resources/references/$ref found"
    } else {
        Write-Warn "resources/references/$ref missing"
        $Errors++
    }
}

# Check link resolves
if (Test-Path $LinkPath) {
    Write-Ok "Skill accessible at: $LinkPath"
} else {
    Write-Warn "Link not resolving correctly"
    $Errors++
}

Write-Host ""
Write-Host "================================================"
if ($Errors -eq 0) {
    Write-Host "Installation complete!" -ForegroundColor Green
} else {
    Write-Host "Installation complete with $Errors warnings." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Usage with Claude CLI:"
Write-Host '  claude> sgeo audit https://example.com'
Write-Host '  claude> sgeo seo https://example.com'
Write-Host '  claude> sgeo geo https://example.com'
Write-Host ""
Write-Host "Skill location: $ScriptDir"
Write-Host "Link: $LinkPath"
Write-Host "================================================"
