# Task Completion Checklist

## When Adding New Scripts
1. Place script in `scripts/` directory
2. Make executable: `chmod +x scripts/new_script.py`
3. Add shebang: `#!/usr/bin/env python3`
4. Support `--json` flag for structured output
5. Update SKILL.md if script adds new audit capability
6. Test script standalone before integration

## When Modifying Audit Logic
1. Ensure MECE compliance (no category overlap)
2. Update dual scoring weights if needed (SEO vs GEO)
3. Verify confidence labels (Confirmed, Likely, Hypothesis)
4. Test with sample URLs
5. Update reference docs in resources/references/ if framework changes

## Before Committing
1. No linting required (no explicit linter configured)
2. No formatting required (no explicit formatter configured)
3. No automated tests (no test suite present)
4. Manual verification: Run install.sh to verify symlink creation
5. Test key commands: `sgeo audit <url>` via Claude CLI

## Quality Standards
- Scripts must handle network failures gracefully
- Always produce markdown reports even with partial data
- Use LLM-first approach, script-verified when possible
- Never block on script failure — continue with available evidence
- Bound retries: max 1 retry per failed check

## Git Workflow
- Main branch: `main`
- Standard git commands for version control
- No pre-commit hooks configured
