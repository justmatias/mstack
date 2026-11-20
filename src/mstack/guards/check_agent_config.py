import argparse
import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from mstack.guards.check_no_domain_leak import SECRETS
from mstack.install.render import RuleFormatError, split_frontmatter

logger = logging.getLogger(__name__)

FOLDER_README = "README.md"
PLACEHOLDER = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")
SENSITIVE_KEY = re.compile(
    r"(?i)(token|secret|password|passwd|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"credential|authorization|auth)"
)
BEARER = re.compile(r"(?i)\b(bearer|basic)\s+(?!\$\{)\S{8,}")
MACHINE_PATH = re.compile(r"(/home/[^/\s$~]+/|/Users/[^/\s$~]+/|[A-Za-z]:\\Users\\)")
SERVER_KEYS = ("command", "url")


def content_files(folder: Path, suffix: str) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        path for path in folder.glob(f"*{suffix}") if path.name != FOLDER_README
    )


def string_values(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from string_values(nested, (*path, str(key)))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from string_values(nested, (*path, str(index)))
    elif isinstance(value, str):
        yield ".".join(path), value


def is_literal_secret(key: str, value: str) -> bool:
    if any(secret.search(value) for secret in SECRETS) or BEARER.search(value):
        return True
    last_key = key.rsplit(".", 1)[-1]
    if not SENSITIVE_KEY.search(last_key) or not value.strip():
        return False
    return not PLACEHOLDER.search(value)


def text_problems(location: str, text: str) -> list[str]:
    if MACHINE_PATH.search(text):
        return [f"{location}: machine-specific path, use ~ or ${{HOME}}"]
    return []


def json_value_problems(location: str, data: Any) -> list[str]:
    problems: list[str] = []
    for key, value in string_values(data):
        if is_literal_secret(key, value):
            problems.append(
                f"{location}: '{key}' holds a literal secret, use a ${{VAR}} placeholder"
            )
        problems.extend(text_problems(f"{location}: '{key}'", value))
    return problems


def load_json_problems(path: Path) -> tuple[Any, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"{path}: invalid JSON ({error})"]
    if not isinstance(data, dict):
        return None, [f"{path}: must be a JSON object"]
    return data, json_value_problems(str(path), data)


def agent_problems(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    try:
        metadata, _ = split_frontmatter(text)
    except RuleFormatError as error:
        return [f"{path}: {error}"]
    problems = text_problems(str(path), text)
    if metadata.get("name") != path.stem:
        problems.append(
            f"{path}: frontmatter name {metadata.get('name')!r} must be {path.stem!r}"
        )
    if not metadata.get("description"):
        problems.append(f"{path}: frontmatter needs a description")
    return problems


def mcp_problems(path: Path) -> list[str]:
    data, problems = load_json_problems(path)
    if data is not None and not any(key in data for key in SERVER_KEYS):
        problems.append(
            f"{path}: an MCP server entry needs a 'command' or a 'url' "
            "(the mcpServers entry format, without the server name)"
        )
    return problems


def collect_problems(root: Path) -> list[str]:
    problems: list[str] = []
    for path in content_files(root / "agents", ".md"):
        problems.extend(agent_problems(path))
    for path in content_files(root / "mcp", ".json"):
        problems.extend(mcp_problems(path))
    for path in content_files(root / "settings", ".json"):
        problems.extend(load_json_problems(path)[1])
    for path in content_files(root / "instructions", ".md"):
        problems.extend(text_problems(str(path), path.read_text(encoding="utf-8")))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack config-check",
        description=(
            "Validate agents/, mcp/, settings/ and instructions/: agent frontmatter, "
            "valid JSON, no literal secrets, no machine-specific paths."
        ),
    )
    parser.add_argument(
        "--root", type=Path, default=Path(), help="The repo root (default: .)."
    )
    arguments = parser.parse_args(argv)
    problems = collect_problems(arguments.root)
    for problem in problems:
        logger.error("%s", problem)
    if problems:
        logger.error("check_agent_config: %d problem(s)", len(problems))
        return 1
    logger.info("check_agent_config: OK")
    return 0
