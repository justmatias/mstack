# Read-only inventory of the local conventions store (the store behind Helix
# recall/remember). Never writes to the store.
import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

FRONTMATTER = re.compile(
    r"\A---\n(?P<frontmatter>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL
)
SECTION = re.compile(r"^(?P<label>Why|How to apply):\s*", re.MULTILINE)


def default_directory() -> Path:
    return Path(
        os.environ.get("CONVENTIONS_HOME", "~/.dev_brain/conventions")
    ).expanduser()


def body_sha256(body: str) -> str:
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def split_body(body: str) -> dict[str, str]:
    sections = {"rule": "", "why": "", "how_to_apply": ""}
    keys = {"Why": "why", "How to apply": "how_to_apply"}
    current = "rule"
    position = 0
    for match in SECTION.finditer(body):
        sections[current] += body[position : match.start()]
        current = keys[match["label"]]
        position = match.end()
    sections[current] += body[position:]
    return {key: value.strip() for key, value in sections.items()}


def read_convention(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("no YAML frontmatter")
    frontmatter = yaml.safe_load(match["frontmatter"]) or {}
    if not isinstance(frontmatter, dict) or not frontmatter.get("name"):
        raise ValueError("frontmatter has no 'name'")
    body = match["body"]
    if not body.strip():
        raise ValueError("empty body")
    tags = frontmatter.get("tags") or []
    return {
        "name": str(frontmatter["name"]),
        "tags": [str(tag) for tag in tags] if isinstance(tags, list) else [str(tags)],
        "path": str(path),
        "sha256": body_sha256(body),
        **split_body(body),
    }


def inventory(directory: Path) -> dict:
    conventions: list[dict] = []
    malformed: list[dict] = []
    for path in sorted(directory.glob("*.md")):
        try:
            conventions.append(read_convention(path))
        except (ValueError, yaml.YAMLError) as error:
            malformed.append({"path": str(path), "error": str(error)})
    return {
        "directory": str(directory),
        "conventions": conventions,
        "malformed": malformed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack conventions",
        description="List the conventions store as JSON. Read-only.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Conventions folder (default $CONVENTIONS_HOME).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the inventory as JSON (default: a summary).",
    )
    arguments = parser.parse_args(argv)

    directory = (arguments.dir or default_directory()).expanduser()
    if not directory.is_dir():
        logger.error("conventions_inventory: %s does not exist", directory)
        return 1
    report = inventory(directory)
    for problem in report["malformed"]:
        logger.warning("%s: skipped (%s)", problem["path"], problem["error"])
    if arguments.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        for convention in report["conventions"]:
            sys.stdout.write(f"{convention['name']}: {', '.join(convention['tags'])}\n")
    return 0
