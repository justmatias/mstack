import argparse
import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

FRONTMATTER_DELIMITER = "---"
CHECKS_HEADING = "## Checks"


class RuleFormatError(ValueError):
    """The .mdc file cannot be converted into a Claude Code rule."""


def split_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            try:
                metadata = yaml.safe_load("\n".join(lines[1:index])) or {}
            except yaml.YAMLError as error:
                raise RuleFormatError(f"invalid frontmatter: {error}") from error
            if not isinstance(metadata, dict):
                raise RuleFormatError("the frontmatter is not a mapping")
            return metadata, "\n".join(lines[index + 1 :])
    raise RuleFormatError("the frontmatter has no closing '---'")


def drop_checks_section(body: str) -> str:
    kept: list[str] = []
    in_checks = False
    for line in body.splitlines():
        if line.startswith("## "):
            in_checks = line.strip() == CHECKS_HEADING
        if not in_checks:
            kept.append(line)
    return "\n".join(kept)


def globs_text(globs: object) -> str:
    if isinstance(globs, list):
        return ", ".join(f"`{glob}`" for glob in globs)
    return f"`{globs}`"


def credit_lines(frontmatter: dict) -> list[str]:
    """The upstream credit, kept in the body because the frontmatter is dropped."""
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return []
    lines = []
    for key, value in metadata.items():
        name = str(key)
        if name.startswith("adapted-from"):
            license_key = name.replace("adapted-from", "upstream-license", 1)
            license_text = metadata.get(license_key) or frontmatter.get("license")
            suffix = f" License: {license_text}." if license_text else ""
            lines.append(f"Adapted from {value}{suffix}")
        elif name.startswith("inspired-by"):
            lines.append(f"Inspired by {value}")
    return lines


def render_rule(mdc_text: str) -> str:
    """Convert an .mdc rule into the text installed at ~/.claude/rules/<name>.md."""
    metadata, body = split_frontmatter(mdc_text)
    body = drop_checks_section(body).strip()
    globs = metadata.get("globs")
    if globs:
        body = f"Applies to files matching {globs_text(globs)}.\n\n{body}"
    credit = credit_lines(metadata)
    if credit:
        body = body + "\n\n" + "\n".join(credit)
    return body + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack render-rule",
        description="Print an .mdc rule converted into a Claude Code user rule.",
    )
    parser.add_argument("mdc", type=Path, help="The .mdc rule to convert.")
    arguments = parser.parse_args(argv)
    try:
        rendered = render_rule(arguments.mdc.read_text(encoding="utf-8"))
    except (OSError, RuleFormatError) as error:
        logger.error("render-rule: %s: %s", arguments.mdc, error)
        return 1
    sys.stdout.write(rendered)
    return 0
