from __future__ import annotations

from argparse import REMAINDER as ARG_REMAINDER
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, TypedDict

    class CmdMetaDataDict(TypedDict):
        add_argument: dict[str, dict[str, Any]]
        argument: str
        description: str


def create_argument(help_text: str, **kwargs: Any) -> dict[str, Any]:
    return {"help": help_text, **kwargs}


def create_boolean_argument(help_text: str, action: str = "store_true") -> dict[str, Any]:
    return {"action": action, "help": help_text}


def create_path_argument(help_text: str, metavar: str) -> dict[str, Any]:
    return {"type": Path, "help": help_text, "metavar": metavar}


def create_choice_argument(help_text: str, choices: list[str], default: str) -> dict[str, Any]:
    return {"choices": choices, "default": default, "help": help_text}


BUBBLEJAIL_CMD: dict[str, CmdMetaDataDict] = {
    "run": {
        "add_argument": {
            "--debug-shell": create_boolean_argument(
                "Opens a shell inside the sandbox instead of running program. Useful for debugging."
            ),
            "--dry-run": create_boolean_argument(
                "Prints the bwrap and xdg-desktop-entry arguments instead of running."
            ),
            "--debug-helper-script": create_path_argument(
                "Use the specified helper script. This is mainly a development command.",
                "script_path"
            ),
            "--debug-log-dbus": create_boolean_argument("Enables D-Bus proxy logging."),
            "--wait": create_boolean_argument(
                "Wait on the command inserted into the sandbox and get the output."
            ),
            "--debug-bwrap-args": {
                "action": "append",
                "nargs": "+",
                "help": "Add extra option to bwrap. First argument will be prefixed with `--`.",
                "metavar": ("bwrap_option", "bwrap_option_args"),
            },
            "instance_name": create_argument("Instance to run."),
            "args_to_instance": {
                "nargs": ARG_REMAINDER,
                "help": "Command and its arguments to run inside instance.",
            },
        },
        "argument": "instance",
        "description": "Launch instance or run command inside.",
    },
    "create": {
        "add_argument": {
            "--profile": create_argument("Bubblejail profile to use.", metavar="profile"),
            "--no-desktop-entry": create_boolean_argument("Do not create desktop entry", "store_false"),
            "new_instance_name": create_argument("New instance name."),
        },
        "argument": "any",
        "description": "Create new bubblejail instance.",
    },
    "list": {
        "add_argument": {
            "list_what": create_choice_argument(
                "Type of entity to list.",
                ["instances", "profiles", "services"],
                "instances"
            ),
        },
        "argument": "any",
        "description": "List certain bubblejail entities.",
    },
    "edit": {
        "add_argument": {
            "instance_name": create_argument("Instance to edit config."),
        },
        "argument": "instance",
        "description": "Open instance config in $EDITOR.",
    },
    "generate-desktop-entry": {
        "add_argument": {
            "--profile": create_argument("Use desktop entry specified in profile.", metavar="profile"),
            "--desktop-entry": create_argument("Desktop entry name or path to use.", metavar="name_or_path"),
            "instance_name": create_argument("Instance to generate desktop entry for"),
        },
        "argument": "instance",
        "description": "Generate XDG desktop entry for an instance.",
    },
}
