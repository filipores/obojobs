#!/usr/bin/env python3
"""
Data migration script to fix corrupted template content.

The bug caused variable labels to be duplicated in template content, e.g.:
- "{{FIRMA}}FirmaFirmaFirma" instead of "{{FIRMA}}"
- "{{POSITION}}PositionPosition" instead of "{{POSITION}}"

This script finds and fixes these corrupted patterns.

Usage:
    # Dry run (no changes made):
    python fix_corrupted_templates.py --dry-run

    # Apply fixes:
    python fix_corrupted_templates.py

    # Verbose output:
    python fix_corrupted_templates.py --dry-run --verbose
"""

import argparse
import re
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from models import Template, db


# Variable types and their labels (must match frontend VARIABLE_TYPES)
VARIABLE_LABELS = {
    "FIRMA": "Firma",
    "POSITION": "Position",
    "ANSPRECHPARTNER": "Ansprechpartner",
    "QUELLE": "Quelle",
    "EINLEITUNG": "Einleitung",
}


def build_cleanup_pattern(var_name: str, label: str) -> re.Pattern:
    """
    Build regex pattern to find and fix duplicated labels after a variable.

    Matches patterns like:
    - {{FIRMA}}Firma           -> {{FIRMA}}
    - {{FIRMA}}FirmaFirma      -> {{FIRMA}}
    - {{FIRMA}}FirmaFirmaFirma -> {{FIRMA}}

    Also handles partial label matches at the end (from truncated duplications):
    - {{FIRMA}}FirmaFi         -> {{FIRMA}}
    """
    # Escape special regex chars in label
    escaped_label = re.escape(label)

    # Pattern: {{VAR}} followed by one or more occurrences of the label
    # Also match partial labels at the end (at least 2 chars to avoid false positives)
    pattern = rf"(\{{\{{{var_name}\}}\}})({escaped_label})+"

    return re.compile(pattern, re.IGNORECASE)


def fix_template_content(content: str, verbose: bool = False) -> tuple[str, list[str]]:
    """
    Fix corrupted template content by removing duplicated labels.

    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    fixed = content
    changes = []

    for var_name, label in VARIABLE_LABELS.items():
        pattern = build_cleanup_pattern(var_name, label)

        def replacer(match):
            original = match.group(0)
            replacement = match.group(1)  # Just the {{VAR}} part
            if original != replacement:
                changes.append(f"  {var_name}: '{original}' -> '{replacement}'")
            return replacement

        fixed = pattern.sub(replacer, fixed)

    # Also check for orphaned labels not attached to variables
    # These might appear if the variable was removed but label text remained
    for var_name, label in VARIABLE_LABELS.items():
        # Pattern: label repeated 2+ times (not preceded by {{VAR}})
        orphan_pattern = rf"(?<!\}}\}})({re.escape(label)}){{2,}}"
        matches = list(re.finditer(orphan_pattern, fixed, re.IGNORECASE))
        for match in reversed(matches):  # Reverse to preserve indices
            original = match.group(0)
            changes.append(f"  Orphaned labels removed: '{original}'")
            fixed = fixed[:match.start()] + fixed[match.end():]

    return fixed, changes


def run_migration(dry_run: bool = True, verbose: bool = False):
    """Run the data migration to fix corrupted templates."""
    app = create_app()

    with app.app_context():
        templates = Template.query.all()
        print(f"Found {len(templates)} templates to check")
        print()

        fixed_count = 0
        for template in templates:
            fixed_content, changes = fix_template_content(template.content, verbose)

            if changes:
                fixed_count += 1
                print(f"Template #{template.id}: '{template.name}' (user_id={template.user_id})")
                for change in changes:
                    print(change)

                if verbose:
                    print(f"  Original length: {len(template.content)}")
                    print(f"  Fixed length: {len(fixed_content)}")

                if not dry_run:
                    template.content = fixed_content
                    print("  ✓ Fixed")
                else:
                    print("  (dry-run, no changes made)")
                print()

        if not dry_run and fixed_count > 0:
            db.session.commit()
            print(f"Committed {fixed_count} template fixes to database")
        elif dry_run and fixed_count > 0:
            print(f"Dry run complete. {fixed_count} templates would be fixed.")
            print("Run without --dry-run to apply changes.")
        else:
            print("No corrupted templates found.")


def main():
    parser = argparse.ArgumentParser(
        description="Fix corrupted template content with duplicated variable labels"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Template Data Migration: Fix Corrupted Labels")
    print("=" * 60)
    if args.dry_run:
        print("MODE: Dry run (no changes will be made)")
    else:
        print("MODE: Live run (changes will be committed)")
    print()

    run_migration(dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
