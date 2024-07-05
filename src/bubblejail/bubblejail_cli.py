from __future__ import annotations

from argparse import ArgumentParser
from asyncio import run as async_run
from pathlib import Path
from sys import argv, stderr, stdout
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Iterator

# Mocking necessary imports for standalone code
BUBBLEJAIL_CMD = {
    "run": {"add_argument": {}, "description": "Run an instance"},
    "create": {"add_argument": {}, "description": "Create a new instance"},
    "list": {"add_argument": {"list_what": {"choices": {"instances", "profiles", "services", "subcommands"}}}, "description": "List items"},
    "edit": {"add_argument": {}, "description": "Edit an instance"},
    "generate-desktop-entry": {"add_argument": {}, "description": "Generate desktop entry"},
}

SERVICES_CLASSES = [type("MockService", (object,), {"name": "service1"})]

class BubblejailDirectories:
    @staticmethod
    def iter_instances_path() -> Generator[Path, None, None]:
        yield Path("instance1")

    @staticmethod
    def instance_get(instance_name: str) -> 'BubblejailInstance':
        return BubblejailInstance(instance_name)

    @staticmethod
    def iter_profile_names() -> Generator[str, None, None]:
        yield "profile1"

    @staticmethod
    def create_new_instance(new_name: str, profile_name: Optional[str], create_dot_desktop: bool, print_import_tips: bool) -> None:
        pass

    @staticmethod
    def overwrite_desktop_entry_for_profile(instance_name: str, profile_name: Optional[str], desktop_entry_name: Optional[str]) -> None:
        pass

class BubblejailInstance:
    def __init__(self, name: str):
        self.name = name

    def is_running(self) -> bool:
        return False

    async def send_run_rpc(self, args_to_run: list[str], wait_for_response: bool) -> Optional[str]:
        return "response"

    async def async_run_init(self, args_to_run: list[str], debug_shell: bool, debug_helper_script: Optional[Path], debug_log_dbus: bool, dry_run: bool, extra_bwrap_args: Optional[list[str]]) -> None:
        pass

    async def edit_config_in_editor(self) -> None:
        pass

class BubblejailSettings:
    VERSION = "1.0"

def iter_instance_names() -> Generator[str, None, None]:
    for instance_directory in BubblejailDirectories.iter_instances_path():
        yield instance_directory.name

def iter_subcommands() -> Generator[str, None, None]:
    yield from BUBBLEJAIL_CMD.keys()

def iter_subcommand_options(subcommand_text: str) -> Generator[str, None, None]:
    yield from (x for x in BUBBLEJAIL_CMD[subcommand_text]["add_argument"] if x.startswith("--"))

def iter_list_choices() -> Iterable[str]:
    choices = BUBBLEJAIL_CMD["list"]["add_argument"]["list_what"]["choices"]
    assert isinstance(choices, set)
    return choices

def _extra_args_converter(command_sequence: list[str]) -> Generator[str, None, None]:
    command_iter = iter(command_sequence)
    try:
        argword = next(command_iter)
    except StopIteration:
        raise ValueError("Expected at least one argument")
    yield f"--{argword}"
    yield from command_iter

def run_bjail(instance_name: str, args_to_instance: list[str], wait: bool, dry_run: bool, debug_bwrap_args: list[list[str]], debug_shell: bool, debug_log_dbus: bool, debug_helper_script: Optional[Path]) -> None:
    try:
        instance = BubblejailDirectories.instance_get(instance_name)
        if instance.is_running():
            if dry_run:
                print("Found helper socket.", file=stderr)
                print("Args would be be sent: ", args_to_instance, file=stderr)
                return
            else:
                print("Instance already running.", file=stderr)
                print("Sending command to the instance: ", args_to_instance, file=stderr)
            command_return_text = async_run(instance.send_run_rpc(args_to_instance, wait))
            if wait and command_return_text is not None:
                stdout.write(command_return_text)
        else:
            extra_bwrap_args = [] if debug_bwrap_args else None
            if extra_bwrap_args is not None:
                for x in debug_bwrap_args:
                    extra_bwrap_args.extend(_extra_args_converter(x))
            async_run(instance.async_run_init(args_to_instance, debug_shell, debug_helper_script, debug_log_dbus, dry_run, extra_bwrap_args))
    except Exception:
        from os import isatty
        if not isatty(stderr.fileno()):
            from subprocess import run as subprocess_run
            from traceback import format_exc
            try:
                subprocess_run(("notify-send", "--urgency", "critical", "--icon", "bubblejail-config", f"Failed to run instance: {instance_name}", f"Exception: {format_exc(0)}"))
            except FileNotFoundError:
                pass
        raise

def bjail_list(list_what: str) -> None:
    str_iterator: Iterator[str]
    if list_what == "instances":
        str_iterator = iter_instance_names()
    elif list_what == "profiles":
        str_iterator = BubblejailDirectories.iter_profile_names()
    elif list_what == "services":
        str_iterator = (x.name for x in SERVICES_CLASSES)
    elif list_what == "subcommands":
        str_iterator = iter_subcommands()
    for string in str_iterator:
        print(string, file=stdout)

def bjail_create(new_instance_name: str, profile: Optional[str], no_desktop_entry: bool) -> None:
    BubblejailDirectories.create_new_instance(new_instance_name, profile, not no_desktop_entry, True)

def bjail_edit(instance_name: str) -> None:
    instance = BubblejailDirectories.instance_get(instance_name)
    async_run(instance.edit_config_in_editor())

def bjail_create_desktop_entry(instance_name: str, profile: Optional[str], desktop_entry: Optional[str]) -> None:
    BubblejailDirectories.overwrite_desktop_entry_for_profile(instance_name, profile, desktop_entry)

COMMANDS_FUNCS: dict[str, Callable[..., None]] = {
    "run": run_bjail,
    "create": bjail_create,
    "list": bjail_list,
    "edit": bjail_edit,
    "generate-desktop-entry": bjail_create_desktop_entry,
}

def create_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Bubblejail is a bubblewrap based sandboxing utility.")
    subparsers = parser.add_subparsers(required=True, description="Available subcommands.")
    for subcommand_name, subcommand_data in BUBBLEJAIL_CMD.items():
        subfunction = COMMANDS_FUNCS[subcommand_name]
        description = subcommand_data["description"]
        subcommand_add_argument = subcommand_data["add_argument"]
        subparser = subparsers.add_parser(subcommand_name, description=description)
        subparser.set_defaults(func=subfunction)
        for arg_name, arg_options in subcommand_add_argument.items():
            subparser.add_argument(arg_name, **arg_options)
    return parser

def bubblejail_main(arg_list: Optional[list[str]] = None) -> None:
    if len(argv) > 1 and argv[1] == "auto-complete":
        from .bubblejail_cli_autocomplete import run_autocomplete
        run_autocomplete()
        return

    parser = create_arg_parser()
    parser.add_argument("--version", action="version", version=BubblejailSettings.VERSION)
    args_dict = vars(parser.parse_args(arg_list))
    func = args_dict.pop("func")
    func(**args_dict)

if __name__ == "__main__":
    bubblejail_main()
