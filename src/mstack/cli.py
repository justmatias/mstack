import argparse
import importlib.metadata
import logging
import sys
from collections.abc import Callable

from mstack import config, doctor, init, lint, platform
from mstack.guards import (
    check_agent_config,
    check_commit_msg,
    check_exceptions,
    check_no_domain_leak,
    check_rule_coverage,
    check_skills,
)
from mstack.install import manifest, merge, render

logger = logging.getLogger(__name__)

COMMANDS: dict[str, Callable[[list[str]], int]] = {
    "commit-msg": check_commit_msg.main,
    "config": config.main,
    "config-check": check_agent_config.main,
    "coverage": check_rule_coverage.main,
    "doctor": doctor.main,
    "exceptions": check_exceptions.main,
    "init": init.main,
    "leak-check": check_no_domain_leak.main,
    "lint": lint.main,
    "manifest": manifest.main,
    "merge-block": merge.merge_block_main,
    "merge-settings": merge.merge_settings_main,
    "platform": platform.main,
    "render-rule": render.main,
    "skills-check": check_skills.main,
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
    parser.add_argument(
        "--version",
        action="version",
        version=f"mstack {importlib.metadata.version('mstack')}",
    )
    parser.add_argument("command", choices=COMMANDS)
    parsed = parser.parse_args(arguments[:1])
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        return COMMANDS[parsed.command](arguments[1:])
    except config.ConfigError as error:
        logger.error("mstack: %s", error)
        return 2
