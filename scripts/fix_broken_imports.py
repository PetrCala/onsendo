#!/usr/bin/env python3
"""Fix broken import statements in command files."""

import re
from pathlib import Path

def fix_file(filepath):
    """Fix broken imports in a file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Pattern: find "from X import (\nfrom src.lib.cli_display..."
    # This happens when the banner import got inserted inside a multi-line import
    pattern = r'(from src\.lib\.[a-z_]+ import \()\n(from src\.lib\.cli_display import show_database_banner)\n'

    def replacement(match):
        return match.group(1) + '\n'

    content = re.sub(pattern, replacement, content)

    # If we removed it, add it back at the end of imports
    if content != original and 'from src.lib.cli_display import show_database_banner' not in content:
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i

        # Insert after last import
        lines.insert(last_import_idx + 1, 'from src.lib.cli_display import show_database_banner')
        content = '\n'.join(lines)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Find all files
commands_dir = Path('/Users/petr/code/onsendo/src/cli/commands')
files = list(commands_dir.rglob('*.py'))

fixed = 0
for filepath in files:
    if fix_file(filepath):
        print(f"Fixed: {filepath}")
        fixed += 1

print(f"\nFixed {fixed} files")
