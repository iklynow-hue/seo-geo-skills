#!/usr/bin/env python3
"""Post-edit schema validation helper.

Validates JSON-LD schema after file edits. Returns exit code 2 to block
if critical validation errors found.

Example usage:
  python3 schema_validator.py path/to/file.html
  python3 schema_validator.py path/to/file.html --json
"""

import argparse
import json
import re
import sys
import os
from typing import List


def validate_jsonld(content: str) -> List[str]:
    """Validate JSON-LD blocks in HTML content."""
    errors = []
    pattern = r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>'
    blocks = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    if not blocks:
        return []  # No schema found — not an error

    for i, block in enumerate(blocks, 1):
        block = block.strip()
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            errors.append(f"Block {i}: Invalid JSON — {e}")
            continue

        if isinstance(data, list):
            for item in data:
                errors.extend(_validate_schema_object(item, i))
        elif isinstance(data, dict):
            errors.extend(_validate_schema_object(data, i))

    return errors


def _validate_schema_object(obj: dict, block_num: int) -> List[str]:
    """Validate a single schema object."""
    errors = []
    prefix = f"Block {block_num}"

    # Check @context
    if "@context" not in obj:
        errors.append(f"{prefix}: Missing @context")
    elif obj["@context"] not in ("https://schema.org", "http://schema.org"):
        errors.append(f"{prefix}: @context should be 'https://schema.org'")

    # Check @type
    if "@type" not in obj:
        errors.append(f"{prefix}: Missing @type")

    # Check for placeholder text
    placeholders = [
        "[Business Name]",
        "[City]",
        "[State]",
        "[Phone]",
        "[Address]",
        "[Your",
        "[INSERT",
        "REPLACE",
        "[URL]",
        "[Email]",
    ]
    text = json.dumps(obj)
    for p in placeholders:
        if p.lower() in text.lower():
            errors.append(f"{prefix}: Contains placeholder text: {p}")

    # Check for deprecated types
    schema_type = obj.get("@type", "")
    deprecated = {
        "HowTo": "deprecated September 2023",
        "SpecialAnnouncement": "deprecated July 31, 2025",
        "CourseInfo": "retired June 2025",
        "EstimatedSalary": "retired June 2025",
        "LearningVideo": "retired June 2025",
        "ClaimReview": "retired June 2025 — fact-check rich results discontinued",
        "VehicleListing": "retired June 2025 — vehicle listing structured data discontinued",
        "PracticeProblem": "retired late 2025 — rich results discontinued",
        "Dataset": "retired late 2025 — rich results discontinued",
    }
    if schema_type in deprecated:
        errors.append(f"{prefix}: @type '{schema_type}' is {deprecated[schema_type]}")

    # Check for FAQPage (informational note - keep for GEO benefits)
    if schema_type == "FAQPage":
        # Note: FAQPage restricted for Google rich results but valuable for AI search
        errors.append(f"{prefix}: ℹ️ FAQPage restricted for Google rich results (gov/healthcare only) but recommended for AI search engines (ChatGPT, Perplexity, Claude). Keep for GEO benefits.")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate JSON-LD schema in HTML files")
    parser.add_argument("filepath", help="Path to HTML file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not os.path.isfile(args.filepath):
        if args.json:
            print(json.dumps({"error": "File not found", "score": 0}))
        sys.exit(0)

    # Only validate HTML-like files
    valid_extensions = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".php", ".ejs")
    if not args.filepath.endswith(valid_extensions):
        if args.json:
            print(json.dumps({"score": 100, "issues": [], "schemas_found": 0}))
        sys.exit(0)

    try:
        with open(args.filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (OSError, IOError) as e:
        if args.json:
            print(json.dumps({"error": str(e), "score": 0}))
        sys.exit(0)

    errors = validate_jsonld(content)

    # Count schemas
    pattern = r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>'
    schemas_found = len(re.findall(pattern, content, re.DOTALL | re.IGNORECASE))

    if not errors:
        if args.json:
            print(json.dumps({"score": 100, "issues": [], "schemas_found": schemas_found}))
        sys.exit(0)

    # Categorize errors
    critical_keywords = ["placeholder", "deprecated", "retired"]
    informational_keywords = ["ℹ️", "informational", "keep for geo"]

    critical = [e for e in errors if any(kw in e.lower() for kw in critical_keywords)]
    informational = [e for e in errors if any(kw in e.lower() for kw in informational_keywords)]
    warnings = [e for e in errors if e not in critical and e not in informational]

    # Calculate score (100 - 10 per critical, -5 per warning, -0 per informational)
    score = 100 - (len(critical) * 10) - (len(warnings) * 5)
    score = max(0, min(100, score))

    if args.json:
        output = {
            "score": score,
            "schemas_found": schemas_found,
            "issues": [
                {"severity": "critical", "message": e} for e in critical
            ] + [
                {"severity": "warning", "message": e} for e in warnings
            ] + [
                {"severity": "info", "message": e} for e in informational
            ],
            "summary": {
                "critical": len(critical),
                "warnings": len(warnings),
                "informational": len(informational)
            }
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Text output mode
    if informational:
        print("ℹ️  Schema validation info:")
        for i in informational:
            print(f"  - {i}")

    if warnings:
        print("⚠️  Schema validation warnings:")
        for w in warnings:
            print(f"  - {w}")

    if critical:
        print("🛑 Schema validation ERRORS (blocking):")
        for e in critical:
            print(f"  - {e}")
        sys.exit(2)  # Block the edit

    if warnings:
        sys.exit(1)  # Warnings only — proceed

    sys.exit(0)  # Informational only — success


if __name__ == "__main__":
    main()
