import argparse
from src import config
from .cmd_list import CLI_COMMANDS, get_argument_kwargs


def main() -> None:
    """
    Main function for the CLI.

    Usage:
    ```bash
    python -m src.cli --help
    python -m src.cli location add --help
    python -m src.cli visit add --help
    python -m src.cli onsen add --help
    ```
    """
    parser = argparse.ArgumentParser(description=f"{config.CLI_NAME}")
    subparsers = parser.add_subparsers(dest="command_group", help="Command groups")

    # Create command groups
    location_parser = subparsers.add_parser(
        "location", help="Location management commands"
    )
    location_subparsers = location_parser.add_subparsers(
        dest="location_command", help="Location subcommands", required=False
    )

    visit_parser = subparsers.add_parser("visit", help="Visit management commands")
    visit_subparsers = visit_parser.add_subparsers(
        dest="visit_command", help="Visit subcommands", required=False
    )

    onsen_parser = subparsers.add_parser("onsen", help="Onsen management commands")
    onsen_subparsers = onsen_parser.add_subparsers(
        dest="onsen_command", help="Onsen subcommands", required=False
    )

    system_parser = subparsers.add_parser("system", help="System management commands")
    system_subparsers = system_parser.add_subparsers(
        dest="system_command", help="System subcommands", required=False
    )

    # Add subcommands to each group
    for command_name, command_config in CLI_COMMANDS.items():
        if command_name.startswith("location-"):
            subcommand = command_name.replace("location-", "")
            parser_command = location_subparsers.add_parser(
                subcommand, help=command_config.help
            )
        elif command_name.startswith("visit-"):
            subcommand = command_name.replace("visit-", "")
            parser_command = visit_subparsers.add_parser(
                subcommand, help=command_config.help
            )
        elif command_name.startswith("onsen-"):
            subcommand = command_name.replace("onsen-", "")
            parser_command = onsen_subparsers.add_parser(
                subcommand, help=command_config.help
            )
        else:
            # System commands
            parser_command = system_subparsers.add_parser(
                command_name, help=command_config.help
            )

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

    args = parser.parse_args()

    # Check if a command group was specified but no subcommand
    if hasattr(args, "command_group") and args.command_group:
        # Check if any subcommand was actually provided
        has_subcommand = False
        if args.command_group == "location":
            has_subcommand = args.location_command is not None
        elif args.command_group == "visit":
            has_subcommand = args.visit_command is not None
        elif args.command_group == "onsen":
            has_subcommand = args.onsen_command is not None
        elif args.command_group == "system":
            has_subcommand = args.system_command is not None

        # If no subcommand was provided, show help for the command group
        if not has_subcommand:
            if args.command_group == "location":
                location_parser.print_help()
            elif args.command_group == "visit":
                visit_parser.print_help()
            elif args.command_group == "onsen":
                onsen_parser.print_help()
            elif args.command_group == "system":
                system_parser.print_help()
            return

    # Execute the command if a function is specified
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
