import argparse
import sys
from typing import Callable, Dict, Optional, Sequence

from .core import CLICommandFn, fetch_cli_arg_type


class PydanticCLIApp(object):
    """Tree of commands.

    You can nest commands like a tree. Where the root is the `PydanticCLIApp`
    that you end up calling.

    Examples:
        >>> class Args(BaseCLIArguments):
        ...    count: int
        ...
        >>> def command(args: Args):
        ...   print(args)
        ...
        >>> app = PydanticCLIApp()
        >>> a_app = PydanticCLIApp("a")
        >>> b_app = PydanticCLIApp("b")
        >>> a_app.add_command(command, name="command")
        >>> b_app.add_command(command, name="command")
        >>> app.add_application(a_app)
        >>> app.add_application(b_app)
        >>> app(["a", "--count", "1"])


    Args:
        name: CLI application name. If left blank, pydantic uses the package 
            name. Defaults "".
        base_parser: Parent argument parser. Defaults None.
    """

    def __init__(
        self,
        name: str = "",
        base_parser: Optional[argparse.ArgumentParser] = None,
    ) -> None:
        self.name = name or __name__.split(".")[0]
        self.base_parser = base_parser or argparse.ArgumentParser()
        self.subparsers = self.base_parser.add_subparsers(
            dest=f"{self.name}_subcommand",
            required=True,
        )
        self._command_handlers: Dict[
            str, Callable[[argparse.Namespace], None]
        ] = {}

    def add_application(self, app: "PydanticCLIApp") -> None:
        parser = self.subparsers.add_parser(app.name)
        app.base_parser._actions = app.base_parser._actions[1:]
        parser._add_container_actions(app.base_parser)
        self._command_handlers[app.name] = app._run_command

    def add_command(self, fn: CLICommandFn, name: str) -> None:
        name = name or fn.__name__.replace("_", "-")
        parser = self.subparsers.add_parser(name)
        cli_cls = fetch_cli_arg_type(fn)
        cli_cls.to_parser(parser)

        def parse_and_run(args: argparse.Namespace) -> None:
            fn(cli_cls.from_args(args))

        self._command_handlers[name] = parse_and_run

    def command(self, name: str = "") -> CLICommandFn:
        def decorator(fn: CLICommandFn) -> CLICommandFn:
            self.add_command(fn, name=name)
            return fn

        return decorator

    def __call__(self, argv: Sequence[str] = None) -> None:
        if not self._command_handlers:
            raise ValueError("No commands or sub-applications registered.")

        args = self.base_parser.parse_args(argv)
        self._run_command(args)

    def _run_command(self, args: argparse.Namespace) -> None:
        self._command_handlers[getattr(args, f"{self.name}_subcommand")](args)
        sys.exit(0)
