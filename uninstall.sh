#!/usr/bin/env bash
set -euo pipefail

# SGEO — Unified SEO + GEO Master Audit Skill
# Uninstall script

SKILL_NAME="sgeo"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
SYMLINK_PATH="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

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
echo "║  SGEO — Uninstaller                          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check if symlink exists
if [ -L "$SYMLINK_PATH" ]; then
    info "Removing symlink: $SYMLINK_PATH"
    rm "$SYMLINK_PATH"
    ok "Symlink removed"
elif [ -e "$SYMLINK_PATH" ]; then
    warn "$SYMLINK_PATH exists but is not a symlink. Remove manually."
else
    info "Symlink not found (already removed or never installed)"
fi

echo ""
echo "════════════════════════════════════════════════"
echo -e "${GREEN}Uninstall complete!${NC}"
echo ""
echo "Note: This script only removes the Claude CLI symlink."
echo "The skill directory remains at its original location."
echo "To fully remove, delete the skill directory manually."
echo "════════════════════════════════════════════════"
