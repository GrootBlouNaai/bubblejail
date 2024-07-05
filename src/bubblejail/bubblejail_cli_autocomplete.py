from __future__ import annotations

from argparse import ArgumentParser
from shlex import split as shlex_split
from typing import TYPE_CHECKING, Iterable

from .bubblejail_cli import (
    iter_instance_names,
    iter_list_choices,
    iter_subcommand_options,
    iter_subcommands,
)
from .bubblejail_directories import BubblejailDirectories

if TYPE_CHECKING:
    from collections.abc import Iterable


class AutoCompleteParser:
    def __init__(self) -> None:
        self.last_auto_complete: Iterable[str] = []

    def auto_complete_parser(self, current_cmd: str) -> None:
        words = shlex_split(current_cmd)
        self.last_auto_complete = iter_subcommands()

        if current_cmd[-1].isspace():
            words.append("")

        want_instance_set = {"edit", "run", "generate-desktop-entry"}
        base_options = {"--help", "--version"}

        enumer_words = enumerate(words)
        next(enumer_words)  # Skip 'bubblejail'

        try:
            index, token = next(enumer_words)
            while token.startswith("-"):
                self.last_auto_complete = base_options
                index, token = next(enumer_words)
            subcommand = token

            subcommand_options = tuple(iter_subcommand_options(subcommand))
        except KeyError:
            try:
                next(enumer_words)
            except StopIteration:
                return
            self.last_auto_complete = tuple()
            return
        except StopIteration:
            return

        subject_set = False

        try:
            while True:
                index, token = next(enumer_words)

                if subject_set:
                    self.last_auto_complete = tuple()
                    return

                if token.startswith("-"):
                    self.last_auto_complete = subcommand_options
                    continue

                if subcommand == "list":
                    self.last_auto_complete = iter_list_choices()
                    subject_set = True
                    continue

                if words[index - 1] == "--profile":
                    self.last_auto_complete = BubblejailDirectories.iter_profile_names()
                    continue

                if subcommand in want_instance_set:
                    self.last_auto_complete = iter_instance_names()
                    subject_set = True
                    continue

                self.last_auto_complete = tuple()
        except StopIteration:
            return

    def auto_complete(self, current_cmd: str) -> Iterable[str]:
        try:
            self.auto_complete_parser(current_cmd)
        except StopIteration:
            pass

        yield from self.last_auto_complete


def run_autocomplete() -> None:
    parser = ArgumentParser()
    parser.add_argument("auto_complete")
    parser.add_argument("current_cmd")
    args = parser.parse_args()

    for x in AutoCompleteParser().auto_complete(args.current_cmd):
        print(x)
