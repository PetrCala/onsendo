"""CLI command to clear recommendation caches."""

import argparse
from typing import Optional

from src.lib.cache import CacheNamespace, clear_recommendation_cache


_NAMESPACE_MAP = {
    "distance": CacheNamespace.DISTANCE,
    "milestones": CacheNamespace.MILESTONES,
}


def clear_cache(args: argparse.Namespace) -> None:
    """Clear persisted recommendation caches."""

    namespace_arg: Optional[str] = args.namespace
    if namespace_arg:
        namespace_arg = namespace_arg.lower()
        if namespace_arg not in _NAMESPACE_MAP and namespace_arg != "all":
            print(
                "Unknown namespace. Use 'distance', 'milestones', or 'all'."
            )
            return

    if not namespace_arg or namespace_arg == "all":
        clear_recommendation_cache()
        print("Cleared all recommendation caches.")
        return

    clear_recommendation_cache(_NAMESPACE_MAP[namespace_arg])
    print(f"Cleared {namespace_arg} cache.")
