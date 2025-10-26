"""
Print the current Onsendo rules, formatted.
"""

import argparse
from src.lib.rule_manager import RuleParser
from src.paths import PATHS


def print_rules(args: argparse.Namespace) -> None:
    """
    Print the current rules to the console.

    Args:
        args: Command-line arguments containing:
            - section: Optional section number to print (default: all)
            - raw: Whether to output raw markdown (default: False)
            - version: Optional version number to print rules at that revision
    """
    parser = RuleParser(PATHS.RULES_FILE)

    try:
        if hasattr(args, "version") and args.version is not None:
            # Print rules from a specific revision
            print_rules_at_version(args.version, args)
            return

        if hasattr(args, "section") and args.section:
            # Print specific section
            section = parser.get_section(args.section)
            if not section:
                print(f"Error: Section {args.section} not found.")
                return

            if hasattr(args, "raw") and args.raw:
                # Raw markdown output
                print(f"## {section.section_number}. {section.section_title}\n")
                print(section.content)
            else:
                # Formatted output
                print("=" * 80)
                print(f"SECTION {section.section_number}: {section.section_title.upper()}")
                print("=" * 80)
                print()
                print(section.content)
                print()
        else:
            # Print all rules
            full_content = parser.get_full_content()

            if hasattr(args, "raw") and args.raw:
                # Raw markdown output
                print(full_content)
            else:
                # Formatted output
                print("=" * 80)
                print("ONSENDO CHALLENGE RULESET")
                print("=" * 80)
                print()
                print(full_content)
                print()

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error printing rules: {e}")


def print_rules_at_version(version_number: int, args: argparse.Namespace) -> None:
    """
    Print rules as they were at a specific revision.

    Args:
        version_number: The version number to retrieve
        args: Command-line arguments
    """
    from src.db.conn import get_db
    from src.db.models import RuleRevision
    from src.config import get_database_config
    import os

# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        revision = (
            db.query(RuleRevision)
            .filter(RuleRevision.version_number == version_number)
            .first()
        )

        if not revision:
            print(f"Error: Version {version_number} not found.")
            return

        # Check if the markdown file exists
        if not revision.markdown_file_path or not os.path.exists(
            revision.markdown_file_path
        ):
            print(f"Error: Revision markdown file not found for version {version_number}.")
            return

        # Read and print the revision markdown
        with open(revision.markdown_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if hasattr(args, "raw") and args.raw:
            print(content)
        else:
            print("=" * 80)
            print(f"RULES AT VERSION {version_number}")
            print(f"Revision Date: {revision.revision_date.strftime('%Y-%m-%d')}")
            print("=" * 80)
            print()
            print(content)
            print()
