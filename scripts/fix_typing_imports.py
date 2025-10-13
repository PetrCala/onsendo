#!/usr/bin/env python3
"""
Script to replace deprecated typing module aliases with Python 3.12+ built-in generics.

Replacements:
- List[X] -> list[X]
- Dict[K, V] -> dict[K, V]
- Tuple[X, Y] -> tuple[X, Y]
- Set[X] -> set[X]

Keeps: Optional, Any, Union, Callable, TypeVar, etc.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def fix_typing_in_file(file_path: Path) -> Tuple[bool, Dict[str, int]]:
    """
    Fix typing imports in a single file.

    Returns:
        Tuple of (modified, replacements_count)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False, {}

    original_content = content
    replacements = {'List': 0, 'Dict': 0, 'Tuple': 0, 'Set': 0}

    # Replace type annotations in code
    # List[X] -> list[X]
    content, list_count = re.subn(r'\bList\[', 'list[', content)
    replacements['List'] = list_count

    # Dict[K, V] -> dict[K, V]
    content, dict_count = re.subn(r'\bDict\[', 'dict[', content)
    replacements['Dict'] = dict_count

    # Tuple[X, Y] -> tuple[X, Y]
    content, tuple_count = re.subn(r'\bTuple\[', 'tuple[', content)
    replacements['Tuple'] = tuple_count

    # Set[X] -> set[X]
    content, set_count = re.subn(r'\bSet\[', 'set[', content)
    replacements['Set'] = set_count

    # Fix import statements - remove unused deprecated types
    if any(replacements.values()):
        content = fix_import_statements(content, replacements)

    # Only write if changes were made
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, replacements
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False, {}

    return False, {}


def fix_import_statements(content: str, replacements: Dict[str, int]) -> str:
    """
    Fix import statements by removing deprecated types that are no longer needed.
    """
    lines = content.split('\n')
    modified_lines = []

    for line in lines:
        # Match: from typing import ...
        if line.strip().startswith('from typing import'):
            # Extract the imports
            match = re.match(r'(from typing import\s+)(.*)', line)
            if match:
                prefix = match.group(1)
                imports_str = match.group(2)

                # Parse imports (handle both single line and parenthesized)
                imports = []
                if '(' in imports_str:
                    # Multi-line import
                    modified_lines.append(line)
                    continue
                else:
                    # Single line import
                    imports = [imp.strip() for imp in imports_str.split(',')]

                # Remove deprecated types that were replaced
                types_to_remove = []
                for type_name, count in replacements.items():
                    if count > 0:
                        types_to_remove.append(type_name)

                # Filter out deprecated types
                remaining_imports = [imp for imp in imports if imp not in types_to_remove]

                # Reconstruct the import line
                if remaining_imports:
                    new_line = prefix + ', '.join(remaining_imports)
                    modified_lines.append(new_line)
                else:
                    # Skip the line if no imports remain
                    continue
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    return '\n'.join(modified_lines)


def process_directory(directory: Path, extensions: Set[str] = {'.py'}) -> Tuple[int, Dict[str, int], List[str]]:
    """
    Process all Python files in a directory recursively.

    Returns:
        Tuple of (files_modified, total_replacements, errors)
    """
    files_modified = 0
    total_replacements = {'List': 0, 'Dict': 0, 'Tuple': 0, 'Set': 0}
    errors = []

    for file_path in directory.rglob('*'):
        if file_path.suffix in extensions and file_path.is_file():
            # Skip __pycache__ and other irrelevant directories
            if '__pycache__' in file_path.parts or '.venv' in file_path.parts:
                continue

            modified, replacements = fix_typing_in_file(file_path)

            if modified:
                files_modified += 1
                for key in total_replacements:
                    total_replacements[key] += replacements[key]

                # Print what was changed
                changes = [f"{k}→{v}" for k, v in replacements.items() if v > 0]
                if changes:
                    print(f"✓ {file_path.relative_to(directory)}: {', '.join(changes)}")

    return files_modified, total_replacements, errors


def main():
    """Main entry point."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print("=" * 70)
    print("Replacing deprecated typing aliases with Python 3.12+ built-in generics")
    print("=" * 70)
    print()

    # Process src directory
    src_dir = project_root / 'src'
    if src_dir.exists():
        print(f"Processing {src_dir}...")
        src_modified, src_replacements, src_errors = process_directory(src_dir)
        print(f"\nSrc directory: {src_modified} files modified")
        for type_name, count in src_replacements.items():
            if count > 0:
                print(f"  - {type_name}: {count} replacements")
    else:
        print(f"Warning: {src_dir} not found")
        src_modified = 0
        src_replacements = {}

    print()

    # Process tests directory
    tests_dir = project_root / 'tests'
    if tests_dir.exists():
        print(f"Processing {tests_dir}...")
        tests_modified, tests_replacements, tests_errors = process_directory(tests_dir)
        print(f"\nTests directory: {tests_modified} files modified")
        for type_name, count in tests_replacements.items():
            if count > 0:
                print(f"  - {type_name}: {count} replacements")
    else:
        print(f"Warning: {tests_dir} not found")
        tests_modified = 0
        tests_replacements = {}

    # Print summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files modified: {src_modified + tests_modified}")
    print()
    print("Total replacements by type:")
    total_all = {}
    for key in ['List', 'Dict', 'Tuple', 'Set']:
        total_all[key] = src_replacements.get(key, 0) + tests_replacements.get(key, 0)
        if total_all[key] > 0:
            print(f"  - {key}: {total_all[key]}")
    print()
    print("✓ All deprecated typing aliases have been replaced!")
    print("=" * 70)


if __name__ == '__main__':
    main()
