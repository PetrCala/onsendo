import argparse
from src import config
from .commands import COMMANDS, get_argument_kwargs


def main() -> None:
    """
    Main function for the CLI.

    Usage:
    ```bash
    python -m src.cli --help
    python -m src.cli add-onsen --help
    python -m src.cli add-visit --help
    ```
    """
    parser = argparse.ArgumentParser(description=f"{config.CLI_NAME}")
    subparsers = parser.add_subparsers(help="Sub-commands")

    for command_name, command_config in COMMANDS.items():
        parser_command = subparsers.add_parser(command_name, help=command_config.help)
        for arg_name, arg_config in command_config.args.items():
            kwargs = get_argument_kwargs(arg_config)
            parser_command.add_argument(f"--{arg_name}", **kwargs)
        parser_command.set_defaults(func=command_config.func)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
