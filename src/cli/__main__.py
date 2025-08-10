import argparse
from typing import Dict
from src import config
from .cmd_list import CLI_COMMANDS, CommandConfig, get_argument_kwargs


def create_command_group_parser(
    subparsers: argparse._SubParsersAction,
    group_name: str,
    help_text: str,
) -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:
    """Create a command group parser with subparsers."""
    group_parser = subparsers.add_parser(group_name, help=help_text)
    subparsers_name = f"{group_name}_subparsers"
    subparsers_obj = group_parser.add_subparsers(
        dest=f"{group_name}_command",
        help=f"{group_name.title()} subcommands",
        required=False,
    )
    return group_parser, subparsers_obj


def get_command_group_config() -> Dict[str, str]:
    """Get configuration for all command groups."""
    return {
        "location": "Location management commands",
        "visit": "Visit management commands",
        "onsen": "Onsen management commands",
        "system": "System management commands",
        "database": "Database management commands",
    }


def get_command_group_mapping() -> Dict[str, str]:
    """Get mapping of command prefixes to their group names."""
    return {
        "location-": "location",
        "visit-": "visit",
        "onsen-": "onsen",
        "database-": "database",
    }


def add_subcommands_to_group(
    subparsers_obj: argparse._SubParsersAction,
    command_name: str,
    command_config: CommandConfig,
    group_prefix: str,
) -> argparse.ArgumentParser:
    """Add a subcommand to the appropriate group."""
    subcommand = command_name.replace(group_prefix, "")
    parser_command = subparsers_obj.add_parser(subcommand, help=command_config.help)

    # Add arguments to the command
    for arg_name, arg_config in command_config.args.items():
        kwargs = get_argument_kwargs(arg_config)

        if hasattr(arg_config, "short") and arg_config.short:
            parser_command.add_argument(
                f"--{arg_name}", f"-{arg_config.short}", **kwargs
            )
        else:
            # Add only long form
            if arg_config.positional:
                parser_command.add_argument(arg_name, **kwargs)
            else:
                parser_command.add_argument(f"--{arg_name}", **kwargs)

    parser_command.set_defaults(func=command_config.func)
    return parser_command


def show_command_group_help(
    command_group: str, group_parsers: Dict[str, argparse.ArgumentParser]
) -> None:
    """Show help for a specific command group."""
    if command_group in group_parsers:
        group_parsers[command_group].print_help()


def main() -> None:
    """
    Main function for the CLI.
    """
    parser = argparse.ArgumentParser(description=f"{config.CLI_NAME}")
    subparsers = parser.add_subparsers(dest="command_group", help="Command groups")

    # Get command group configuration
    group_config = get_command_group_config()
    group_mapping = get_command_group_mapping()

    # Create command groups and store parsers
    group_parsers = {}
    group_subparsers = {}

    for group_name, help_text in group_config.items():
        group_parser, group_subparser = create_command_group_parser(
            subparsers, group_name, help_text
        )
        group_parsers[group_name] = group_parser
        group_subparsers[group_name] = group_subparser

    # Add subcommands to each group
    for command_name, command_config in CLI_COMMANDS.items():
        # Find which group this command belongs to
        target_group = None
        for prefix, group_name in group_mapping.items():
            if command_name.startswith(prefix):
                target_group = group_name
                break

        if target_group:
            # Add to the appropriate group
            add_subcommands_to_group(
                group_subparsers[target_group],
                command_name,
                command_config,
                f"{target_group}-",
            )
        else:
            # System commands (no prefix)
            add_subcommands_to_group(
                group_subparsers["system"], command_name, command_config, ""
            )

    args = parser.parse_args()

    # Check if a command group was specified but no subcommand
    if hasattr(args, "command_group") and args.command_group:
        # Check if any subcommand was actually provided
        subcommand_attr = f"{args.command_group}_command"
        has_subcommand = getattr(args, subcommand_attr) is not None

        # If no subcommand was provided, show help for the command group
        if not has_subcommand:
            show_command_group_help(args.command_group, group_parsers)
            return

    # Execute the command if a function is specified
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
