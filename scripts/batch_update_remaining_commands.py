#!/usr/bin/env python3
"""Batch update remaining CLI commands to use database environment system.

This script is simpler than the previous attempt - it only does import replacement
and simple pattern matching without trying to be too smart about indentation.
"""

import os
import re
from pathlib import Path


# Commands that should block production (mock data generation)
BLOCK_PROD_COMMANDS = {
    'mock_data.py',
    'generate_realistic_data.py',
}

# Commands that are destructive (need banners, already done for visit/)
DESTRUCTIVE_COMMANDS = {
    'add.py', 'modify.py', 'delete.py', 'drop', 'import', 'batch',
    'create.py', 'update_artifacts.py',
}


def should_add_banner(filepath: str) -> bool:
    """Check if file needs banner/confirmation (destructive operation)."""
    filename = os.path.basename(filepath)
    return any(pattern in filename for pattern in DESTRUCTIVE_COMMANDS)


def is_mock_data_command(filepath: str) -> bool:
    """Check if command generates mock data."""
    filename = os.path.basename(filepath)
    return filename in BLOCK_PROD_COMMANDS


def update_file(filepath: str) -> bool:
    """Update a single file with simple replacements."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'CONST.DATABASE_URL' not in content:
        return False

    original = content

    # Step 1: Update import
    content = content.replace(
        'from src.const import CONST',
        'from src.config import get_database_config'
    )

    # Step 2: Add banner import if needed (destructive ops only)
    if should_add_banner(filepath) and 'show_database_banner' not in content:
        # Find first src import and add after it
        import_match = re.search(r'(from src\.[^\n]+\n)', content)
        if import_match:
            insert_pos = import_match.end()
            content = (
                content[:insert_pos] +
                "from src.lib.cli_display import show_database_banner\n" +
                content[insert_pos:]
            )

    # Step 3: Replace database connection - simple pattern
    # Pattern: "with get_db(url=CONST.DATABASE_URL) as db:"

    # Build replacement based on file type
    is_mock = is_mock_data_command(filepath)

    if is_mock:
        # Mock data - block production
        replacement = '''# Get database configuration - BLOCK PRODUCTION ACCESS
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None),
        allow_prod=False  # Mock data should never touch production
    )

    with get_db(url=config.url) as db:'''
    else:
        # Regular command - allow production
        replacement = '''# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:'''

    # Only replace if there's a match
    pattern = r'    with get_db\(url=CONST\.DATABASE_URL\) as db:'
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)

    # Write if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def main():
    """Update all remaining command files."""
    # Files already done (skip these)
    skip_files = {
        'init_db.py',  # Already done
        'migrate_to_envs.py',  # Already done
        'add.py',  # Visit commands already done
        'list.py',
        'modify.py',
        'delete.py',
        'interactive.py',
    }

    # Find all command files that still need updating
    commands_dir = Path('/Users/petr/code/onsendo/src/cli/commands')

    files_to_update = []
    for filepath in commands_dir.rglob('*.py'):
        filename = filepath.name

        # Skip if already done
        if filename in skip_files or filename == '__init__.py':
            continue

        # Check if needs update
        with open(filepath, 'r', encoding='utf-8') as f:
            if 'CONST.DATABASE_URL' in f.read():
                files_to_update.append(str(filepath))

    print(f"Found {len(files_to_update)} files to update\n")

    updated = 0
    for filepath in files_to_update:
        rel_path = filepath.replace('/Users/petr/code/onsendo/', '')
        if update_file(filepath):
            print(f"✓ {rel_path}")
            updated += 1
        else:
            print(f"- {rel_path} (no changes)")

    print(f"\n✓ Updated {updated} files")


if __name__ == '__main__':
    main()
