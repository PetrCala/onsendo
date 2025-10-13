#!/usr/bin/env python3
"""
Fix remaining deprecated typing imports in import statements.
"""

import re
from pathlib import Path


def fix_import_line(line: str) -> str:
    """Fix a single import line by removing deprecated types."""
    # If it's not a typing import, return as-is
    if 'from typing import' not in line:
        return line

    # Extract the imports part
    match = re.match(r'(from typing import\s+)(.*)', line)
    if not match:
        return line

    prefix = match.group(1)
    imports_str = match.group(2)

    # Don't process multi-line imports (with parentheses)
    if '(' in imports_str:
        return line

    # Split by comma
    imports = [imp.strip() for imp in imports_str.split(',')]

    # Remove deprecated types
    deprecated = {'List', 'Dict', 'Tuple', 'Set'}
    remaining = [imp for imp in imports if imp not in deprecated]

    # If no imports remain, return empty (will be filtered out)
    if not remaining:
        return ''

    # Reconstruct the line
    return prefix + ', '.join(remaining) + '\n'


def fix_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    modified = False
    new_lines = []

    for line in lines:
        if 'from typing import' in line and any(t in line for t in ['List', 'Dict', 'Tuple', 'Set']):
            fixed_line = fix_import_line(line)
            if fixed_line != line:
                modified = True
                if fixed_line:  # Only add if not empty
                    new_lines.append(fixed_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False

    return False


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Files with remaining deprecated imports
    files_to_fix = [
        'src/analysis/interactive_maps.py',
        'src/analysis/econometrics.py',
        'src/analysis/insight_discovery.py',
        'src/cli/commands/analysis/run_analysis.py',
        'src/cli/commands/onsen/scrape_data/scraper.py',
        'src/testing/mocks/mock_heart_rate_data.py',
        'src/testing/mocks/mock_visit_data.py',
        'src/testing/mocks/scenario_builder.py',
        'src/testing/mocks/integrated_scenario.py',
        'src/testing/testutils/fixtures.py',
        'src/lib/milestone_calculator.py',
        'src/lib/heart_rate_manager.py',
    ]

    fixed_count = 0
    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_file(file_path):
                print(f"✓ Fixed: {file_path_str}")
                fixed_count += 1
        else:
            print(f"✗ Not found: {file_path_str}")

    print(f"\n✓ Fixed {fixed_count} files")


if __name__ == '__main__':
    main()
