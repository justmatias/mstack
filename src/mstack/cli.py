import argparse
import logging
import sys
from collections.abc import Callable

from mstack.guards import (
    check_exceptions,
    check_no_domain_leak,
    check_rule_coverage,
    check_skills,
)

COMMANDS: dict[str, Callable[[list[str]], int]] = {
    "coverage": check_rule_coverage.main,
    "exceptions": check_exceptions.main,
    "leak-check": check_no_domain_leak.main,
    "skills-check": check_skills.main,
}


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="mstack",
        description="Keep prose rules and their automated checks in sync.",
        epilog="Run 'mstack <command> --help' for what each command does.",
    )
    parser.add_argument("command", choices=COMMANDS)
    parsed = parser.parse_args(arguments[:1])
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return COMMANDS[parsed.command](arguments[1:])
