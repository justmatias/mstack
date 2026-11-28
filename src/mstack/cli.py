import argparse
import importlib
import logging
import sys

from mstack.guards.config import ConfigError

logger = logging.getLogger(__name__)

COMMANDS = {
    "cleanup": "mstack.cleanup",
    "coverage": "mstack.guards.coverage",
    "doctor": "mstack.doctor",
    "platform": "mstack.platform",
    "render-rule": "mstack.render",
    "rule-tests-check": "mstack.guards.check_rule_tests",
    "skills-check": "mstack.guards.check_skills",
}


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    metadata = importlib.import_module("importlib.metadata")
    parser = argparse.ArgumentParser(
        prog="mstack",
        description=(
            "Install mstack's skills and rules, and check that "
            "this machine has the mstack stack."
        ),
        epilog="Run 'mstack <command> --help' for what each command does.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mstack {metadata.version('mstack')}",
    )
    parser.add_argument("command", choices=COMMANDS)
    parsed = parser.parse_args(arguments[:1])
    command = importlib.import_module(COMMANDS[parsed.command])
    try:
        return int(command.main(arguments[1:]))
    except ConfigError as error:
        logger.error("mstack: %s", error)
        return 2
