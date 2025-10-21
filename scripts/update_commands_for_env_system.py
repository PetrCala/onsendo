#!/usr/bin/env python3
"""Batch update CLI commands to use new database environment system.

This script updates all CLI command files to use the new database configuration
system with environment awareness.

Changes applied:
1. Replace `from src.const import CONST` with `from src.config import get_database_config`
2. Replace `with get_db(url=CONST.DATABASE_URL)` with config-based URL
3. Add `from src.lib.cli_display import show_database_banner` for destructive operations
4. Add config resolution and banner display before database operations

IMPORTANT: Only run this script once during the migration!
"""

import os
import re
from pathlib import Path


# Define which commands are destructive (need banners)
DESTRUCTIVE_OPERATIONS = {
    "add", "modify", "delete", "drop", "insert",
    "import", "batch", "create", "remove", "update"
}

# Define which commands should block production (e.g., mock data)
BLOCK_PROD_OPERATIONS = {
    "insert-mock", "insert_mock"
}


def is_destructive_operation(filepath: str) -> bool:
    """Check if a command file represents a destructive operation."""
    filename = os.path.basename(filepath).lower()
    return any(op in filename for op in DESTRUCTIVE_OPERATIONS)


def should_block_prod(filepath: str) -> bool:
    """Check if a command should block production database access."""
    filename = os.path.basename(filepath).lower()
    return any(op in filename for op in BLOCK_PROD_OPERATIONS)


def update_command_file(filepath: str, dry_run: bool = False) -> bool:
    """Update a single command file to use new config system.

    Args:
        filepath: Path to command file
        dry_run: If True, only print what would be changed

    Returns:
        True if file was modified (or would be in dry run)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    modified = False

    # Check if file uses DATABASE_URL
    if "CONST.DATABASE_URL" not in content:
        return False

    print(f"\nProcessing: {filepath}")

    # Step 1: Update imports
    if "from src.const import CONST" in content:
        content = content.replace(
            "from src.const import CONST",
            "from src.config import get_database_config"
        )
        print("  ✓ Updated imports: CONST → get_database_config")
        modified = True

    # Step 2: Add cli_display import for destructive operations
    if is_destructive_operation(filepath) and "show_database_banner" not in content:
        # Find the last import line and add after it
        import_pattern = r"(from src\.[^\n]+\n)"
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = (
                content[:insert_pos]
                + "from src.lib.cli_display import show_database_banner\n"
                + content[insert_pos:]
            )
            print("  ✓ Added cli_display import")
            modified = True

    # Step 3: Replace database connection pattern
    # Pattern: with get_db(url=CONST.DATABASE_URL) as db:
    old_pattern = r"with get_db\(url=CONST\.DATABASE_URL\) as (\w+):"

    def replacement(match):
        db_var = match.group(1)
        is_destructive = is_destructive_operation(filepath)
        block_prod = should_block_prod(filepath)

        # Build replacement code
        lines = []
        lines.append("# Get database configuration")

        if block_prod:
            lines.append("config = get_database_config(")
            lines.append("    env_override=getattr(args, 'env', None),")
            lines.append("    path_override=getattr(args, 'database', None),")
            lines.append("    allow_prod=False  # Block production for mock data")
            lines.append(")")
        else:
            lines.append("config = get_database_config(")
            lines.append("    env_override=getattr(args, 'env', None),")
            lines.append("    path_override=getattr(args, 'database', None)")
            lines.append(")")

        if is_destructive:
            # Extract operation name from filename
            filename = os.path.basename(filepath).replace(".py", "").replace("_", " ").title()
            lines.append("")
            lines.append("# Show banner for destructive operation")
            lines.append(f"show_database_banner(config, operation=\"{filename}\")")

        lines.append("")
        lines.append(f"with get_db(url=config.url) as {db_var}:")

        # Maintain proper indentation (assume 4 spaces)
        return "\n    ".join(lines)

    if re.search(old_pattern, content):
        content = re.sub(old_pattern, replacement, content)
        print("  ✓ Updated database connection pattern")
        modified = True

    # Write changes
    if modified:
        if dry_run:
            print(f"  [DRY RUN] Would update: {filepath}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ Saved: {filepath}")

    return modified


def main():
    """Main function to update all command files."""
    # Find all Python files in src/cli/commands
    commands_dir = Path("/Users/petr/code/onsendo/src/cli/commands")
    python_files = list(commands_dir.rglob("*.py"))

    print("=" * 70)
    print("DATABASE ENVIRONMENT SYSTEM - COMMAND UPDATE SCRIPT")
    print("=" * 70)
    print(f"\nFound {len(python_files)} Python files in commands directory")

    # Filter to only files that need updating
    files_to_update = []
    for filepath in python_files:
        with open(filepath, "r", encoding="utf-8") as f:
            if "CONST.DATABASE_URL" in f.read():
                files_to_update.append(str(filepath))

    print(f"Files needing update: {len(files_to_update)}")

    if not files_to_update:
        print("\n✓ No files need updating!")
        return

    # Confirm with user
    print("\nFiles to update:")
    for f in files_to_update:
        rel_path = f.replace("/Users/petr/code/onsendo/", "")
        print(f"  • {rel_path}")

    response = input("\nProceed with updates? [yes/no]: ").strip().lower()
    if response != "yes":
        print("Cancelled by user")
        return

    # Update files
    print("\n" + "-" * 70)
    print("Updating files...")
    print("-" * 70)

    updated_count = 0
    for filepath in files_to_update:
        if update_command_file(filepath, dry_run=False):
            updated_count += 1

    print("\n" + "=" * 70)
    print(f"✓ Updated {updated_count} files successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
