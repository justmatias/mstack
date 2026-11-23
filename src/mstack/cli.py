import argparse
import importlib
import logging
import sys

logger = logging.getLogger(__name__)

COMMANDS = {
    "cleanup": "mstack.cleanup",
    "commit-msg": "mstack.guards.check_commit_msg",
    "config": "mstack.config",
    "coverage": "mstack.guards.check_rule_coverage",
    "doctor": "mstack.doctor",
    "exceptions": "mstack.guards.check_exceptions",
    "hook": "mstack.hooks",
    "init": "mstack.init",
    "domain-check": "mstack.guards.check_domain",
    "lint": "mstack.lint",
    "packs": "mstack.packs",
    "platform": "mstack.platform",
    "render-rule": "mstack.render",
    "skills-check": "mstack.guards.check_skills",
}


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if arguments[:1] == ["hook"]:
        command = importlib.import_module(COMMANDS["hook"])
        return int(command.main(arguments[1:]))
    metadata = importlib.import_module("importlib.metadata")
    parser = argparse.ArgumentParser(
        prog="mstack",
        description=(
            "Keep prose rules and their automated checks in sync, and check that "
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
    config = importlib.import_module("mstack.config")
    try:
        return int(command.main(arguments[1:]))
    except config.ConfigError as error:
        logger.error("mstack: %s", error)
        return 2
