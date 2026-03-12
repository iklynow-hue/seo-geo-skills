#!/usr/bin/env bash
set -euo pipefail

# SGEO — Unified SEO + GEO Master Audit Skill
# Install script for Claude CLI / Codex CLI integration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="sgeo"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
REQUIREMENTS="requests beautifulsoup4 lxml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  SGEO — Unified SEO + GEO Master Audit      ║"
echo "║  Installer v1.0                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# --- 1. Check Python ---
info "Checking Python..."
if command -v python3 &>/dev/null; then
    PY="python3"
elif command -v python &>/dev/null; then
    PY="python"
else
    fail "Python 3.8+ is required. Install from https://python.org"
fi

PY_VERSION=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PY -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PY -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
    fail "Python 3.8+ required. Found: $PY_VERSION"
fi
ok "Python $PY_VERSION found"

# --- 2. Check pip ---
info "Checking pip..."
if ! $PY -m pip --version &>/dev/null; then
    warn "pip not found. Attempting to install..."
    $PY -m ensurepip --default-pip 2>/dev/null || fail "Cannot install pip. Install manually."
fi
ok "pip available"

# --- 3. Install Python dependencies ---
info "Installing Python dependencies..."
$PY -m pip install --quiet --upgrade $REQUIREMENTS
ok "Dependencies installed: $REQUIREMENTS"

# --- 4. Optional: Playwright ---
if $PY -c "import playwright" 2>/dev/null; then
    ok "Playwright already installed (optional)"
else
    warn "Playwright not installed (optional — needed for screenshots)"
    echo "    To install: pip install playwright && playwright install chromium"
fi

# --- 5. Create Claude skills directory ---
info "Setting up Claude CLI skill symlink..."
mkdir -p "$CLAUDE_SKILLS_DIR"

SYMLINK_PATH="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

if [ -L "$SYMLINK_PATH" ]; then
    EXISTING_TARGET=$(readlink "$SYMLINK_PATH")
    if [ "$EXISTING_TARGET" = "$SCRIPT_DIR" ]; then
        ok "Symlink already exists and points to correct location"
    else
        warn "Symlink exists but points to: $EXISTING_TARGET"
        warn "Updating to: $SCRIPT_DIR"
        rm "$SYMLINK_PATH"
        ln -s "$SCRIPT_DIR" "$SYMLINK_PATH"
        ok "Symlink updated"
    fi
elif [ -e "$SYMLINK_PATH" ]; then
    fail "$SYMLINK_PATH exists but is not a symlink. Remove it manually."
else
    ln -s "$SCRIPT_DIR" "$SYMLINK_PATH"
    ok "Symlink created: $SYMLINK_PATH → $SCRIPT_DIR"
fi

# --- 6. Verify scripts are executable ---
info "Making scripts executable..."
chmod +x "$SCRIPT_DIR/scripts/"*.py 2>/dev/null || true
ok "Scripts are executable"

# --- 7. Verify installation ---
info "Verifying installation..."

ERRORS=0

# Check SKILL.md exists
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    ok "SKILL.md found"
else
    warn "SKILL.md not found"
    ERRORS=$((ERRORS + 1))
fi

# Check key scripts exist
for script in fetch_page.py parse_html.py robots_checker.py citability_scorer.py schema_validator.py generate_report.py; do
    if [ -f "$SCRIPT_DIR/scripts/$script" ]; then
        ok "scripts/$script found"
    else
        warn "scripts/$script missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check references exist
for ref in mece-framework.md dual-scoring-methodology.md faqpage-guidance.md quality-gates.md; do
    if [ -f "$SCRIPT_DIR/resources/references/$ref" ]; then
        ok "resources/references/$ref found"
    else
        warn "resources/references/$ref missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check symlink resolves
if [ -d "$SYMLINK_PATH" ]; then
    ok "Skill accessible at: $SYMLINK_PATH"
else
    warn "Symlink not resolving correctly"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "════════════════════════════════════════════════"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}Installation complete!${NC}"
else
    echo -e "${YELLOW}Installation complete with $ERRORS warnings.${NC}"
fi
echo ""
echo "Usage with Claude CLI:"
echo "  claude> sgeo audit https://example.com"
echo "  claude> sgeo seo https://example.com"
echo "  claude> sgeo geo https://example.com"
echo ""
echo "Skill location: $SCRIPT_DIR"
echo "Symlink: $SYMLINK_PATH"
echo "════════════════════════════════════════════════"
