import argparse
import logging
import sys
from collections.abc import Callable

from mstack import config
from mstack.guards import check_exceptions, check_no_domain_leak, check_rule_coverage
from mstack.install import manifest, render

logger = logging.getLogger(__name__)

COMMANDS: dict[str, Callable[[list[str]], int]] = {
    "config": config.main,
    "coverage": check_rule_coverage.main,
    "exceptions": check_exceptions.main,
    "leak-check": check_no_domain_leak.main,
    "manifest": manifest.main,
    "render-rule": render.main,
}


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="mstack",
        description=(
            "Keep prose rules and their automated checks in sync, and track what "
            "mstack installed."
        ),
        epilog="Run 'mstack <command> --help' for what each command does.",
    )
    parser.add_argument("command", choices=COMMANDS)
    parsed = parser.parse_args(arguments[:1])
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        return COMMANDS[parsed.command](arguments[1:])
    except config.ConfigError as error:
        logger.error("mstack: %s", error)
        return 2
