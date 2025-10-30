"""
Deprecation notice for exercise command group.

The exercise command group has been deprecated in favor of the unified
Activity system with Strava integration.
"""


def print_deprecation_warning():
    """Print deprecation warning for exercise commands."""
    print("\n" + "=" * 70)
    print("⚠️  DEPRECATION WARNING")
    print("=" * 70)
    print("The 'exercise' command group is deprecated and will be removed")
    print("in a future version.")
    print()
    print("Please use the unified Activity system via Strava integration:")
    print("  - Import all activities: poetry run onsendo strava sync")
    print("  - Interactive tagging:   poetry run onsendo strava sync --interactive")
    print("  - Auto-tag pattern:      poetry run onsendo strava sync --auto-tag-pattern 'onsen'")
    print()
    print("The new system:")
    print("  ✓ Single source of truth (Strava)")
    print("  ✓ Tag activities as onsen monitoring")
    print("  ✓ Link only onsen activities to visits")
    print("  ✓ Track all exercises without redundancy")
    print("=" * 70 + "\n")
