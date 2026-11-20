"""`mstack doctor`: whether this machine is set up like the others.

Every check is a function from a `Context` to a list of `Result`s, registered in
`CHECKS`. Adding a check means adding one function. Doctor only reports: each
problem comes with the command or step that fixes it.
"""

import argparse
import importlib.metadata
import json
import logging
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from mstack.doctor.cli import check_cli
from mstack.doctor.drift import check_drift
from mstack.doctor.model import Check, Context, Result
from mstack.doctor.platform import check_platform
from mstack.doctor.rules import check_rules
from mstack.doctor.skills import check_skills_installed
from mstack.doctor.source import check_source
from mstack.doctor.tools import check_tools
from mstack.doctor.version import check_version
from mstack.install.item_kinds import Tool

logger = logging.getLogger(__name__)

CHECKS: list[Check] = [
    check_tools,
    check_cli,
    check_source,
    check_skills_installed,
    check_rules,
    check_drift,
    check_platform,
    check_version,
]
SYMBOLS = {"ok": "ok", "warn": "WARN", "error": "ERROR"}


def installed_checkout() -> Path | None:
    """The folder mstack was installed from: an editable or local install."""
    try:
        direct_url = importlib.metadata.distribution("mstack").read_text(
            "direct_url.json"
        )
    except importlib.metadata.PackageNotFoundError:
        direct_url = None
    if direct_url:
        url = urllib.parse.urlparse(json.loads(direct_url).get("url", ""))
        if url.scheme == "file":
            return Path(urllib.request.url2pathname(url.path))
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file() and (candidate / "skills").is_dir():
        return candidate
    return None


def default_tool(home: Path) -> Tool:
    claude = (home / ".claude").is_dir()
    cursor = (home / ".cursor").is_dir()
    if claude and cursor:
        return "both"
    return "cursor" if cursor else "claude"


def run_checks(context: Context, checks: list[Check] | None = None) -> list[Result]:
    return [result for check in checks or CHECKS for result in check(context)]


def report(results: list[Result]) -> None:
    for result in results:
        line = f"{SYMBOLS[result.status]:<5} {result.group:<9} {result.check:<14} {result.detail}"
        if result.status == "ok":
            logger.info("%s", line)
        else:
            logger.warning("%s", line)
        if result.fix and result.status != "ok":
            logger.warning("%s fix: %s", " " * 30, result.fix)


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mstack doctor",
        description=(
            "Check that this machine has the mstack stack: tools, CLI, checkout, "
            "skills, rules and drift from the checkout. Reports only; prints the "
            "fix for each problem. Exit 1 if any check is an error."
        ),
    )
    parser.add_argument(
        "--tool",
        choices=["claude", "cursor", "both"],
        help="Which tool's folders to check (default: the ones that exist).",
    )
    parser.add_argument(
        "--checkout",
        type=Path,
        help="The mstack checkout (default: the one this CLI was installed from).",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Also compare with the latest release tag (git ls-remote on origin).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the full report as JSON."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    home = Path.home()
    context = Context(
        home=home,
        tool=arguments.tool or default_tool(home),
        checkout=(
            arguments.checkout.expanduser().resolve()
            if arguments.checkout
            else installed_checkout()
        ),
        online=arguments.online,
    )
    results = run_checks(context)
    report(results)
    errors = sum(result.status == "error" for result in results)
    warnings = sum(result.status == "warn" for result in results)
    if arguments.json:
        payload = {
            "ok": errors == 0,
            "tool": context.tool,
            "checkout": str(context.checkout) if context.checkout else None,
            "results": [result.model_dump() for result in results],
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    logger.info(
        "doctor: %d errors, %d warnings (tool: %s)", errors, warnings, context.tool
    )
    return 1 if errors else 0
