import argparse
import ast
import builtins
import importlib.metadata
import logging
import re
import sys
import tomllib
from pathlib import Path

from mstack.config import resolve_config

logger = logging.getLogger(__name__)

GENERIC_NAMES_FILE = Path(__file__).with_name("generic_names.txt")
SKIPPED_DIRECTORIES = {
    "node_modules",
    "site-packages",
    "__pycache__",
    "venv",
    "build",
    "dist",
}
TEXT_SUFFIXES = {
    ".yml",
    ".yaml",
    ".mdc",
    ".md",
    ".py",
    ".txt",
    ".json",
    ".toml",
    ".sh",
    "",
}
MINIMUM_STRING_LENGTH = 16

URL = re.compile(
    r"\b[a-z][a-z0-9+.-]*://(?P<host>[^/\s\"'`)>]+)[^\s\"'`)>]*", re.IGNORECASE
)
HOST = re.compile(
    r"(?<![\w./@-])(?P<host>(?:[a-z0-9-]+\.)+"
    r"(?:com|net|org|io|dev|ai|co|app|cloud|internal|local|corp|lan))\b",
    re.IGNORECASE,
)
IP_ADDRESS = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
SECRETS = (
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def load_generic_names() -> tuple[set[str], set[str]]:
    names: set[str] = set()
    hosts: set[str] = set()
    for line in GENERIC_NAMES_FILE.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            (hosts if "." in entry else names).add(entry)
    return names, hosts


def known_external_names() -> set[str]:
    names = set(sys.stdlib_module_names) | set(dir(builtins))
    for top_level, distributions in importlib.metadata.packages_distributions().items():
        names.add(top_level)
        for distribution in distributions:
            names.add(distribution)
            names.add(distribution.replace("-", "_"))
    return names


def is_compound(name: str) -> bool:
    stripped = name.strip("_")
    return "_" in stripped or bool(re.search(r"[a-z][A-Z]", stripped))


def is_skipped(path: Path, repository: Path, excluded_directories: list[Path]) -> bool:
    parts = path.relative_to(repository).parts[:-1]
    return any(
        part.startswith(".") or part in SKIPPED_DIRECTORIES for part in parts
    ) or any(path.is_relative_to(directory) for directory in excluded_directories)


def project_name_identifiers(repository: Path) -> dict[str, str]:
    pyproject = repository / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    project_name = (
        tomllib
        .loads(pyproject.read_text(encoding="utf-8"))
        .get("project", {})
        .get("name")
    )
    if not project_name:
        return {}
    return {
        project_name: "project name",
        project_name.replace("-", "_"): "project name",
    }


def node_identifiers(node: ast.AST, relative: Path) -> dict[str, str]:
    if isinstance(node, ast.ClassDef):
        identifiers = {node.name: f"class in {relative}:{node.lineno}"}
        for statement in node.body:
            if (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and is_compound(statement.target.id)
            ):
                identifiers.setdefault(
                    statement.target.id, f"field in {relative}:{statement.lineno}"
                )
        return identifiers
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_compound(
        node.name
    ):
        return {node.name: f"function in {relative}:{node.lineno}"}
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and len(node.value.strip()) >= MINIMUM_STRING_LENGTH
    ):
        return {node.value.strip(): f"string literal in {relative}:{node.lineno}"}
    return {}


def collect_repository_identifiers(
    repository: Path, excluded: set[Path], excluded_directories: list[Path]
) -> dict[str, str]:
    identifiers = project_name_identifiers(repository)
    for path in sorted(repository.rglob("*.py")):
        if (
            is_skipped(path, repository, excluded_directories)
            or path.resolve() in excluded
        ):
            continue
        relative = path.relative_to(repository)
        for part in relative.parent.parts:
            identifiers.setdefault(part, f"package in {relative}")
        if path.stem != "__init__":
            identifiers.setdefault(path.stem, f"module {relative}")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            for name, origin in node_identifiers(node, relative).items():
                identifiers.setdefault(name, origin)
    return identifiers


def generated_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file()
                and candidate.suffix in TEXT_SUFFIXES
                and "__pycache__" not in candidate.parts
            )
        elif path.is_file():
            files.append(path)
    return files


def identifier_findings(
    location: str,
    line: str,
    word_pattern: re.Pattern[str] | None,
    words: dict[str, str],
    literals: dict[str, str],
) -> list[str]:
    findings: list[str] = []
    if word_pattern:
        findings.extend(
            f"{location}: repo identifier '{match[1]}' ({words[match[1]]})"
            for match in word_pattern.finditer(line)
        )
    findings.extend(
        f"{location}: repo string copied verbatim ({origin})"
        for literal, origin in literals.items()
        if literal in line
    )
    return findings


def pattern_findings(location: str, line: str, allowed_hosts: set[str]) -> list[str]:
    findings: list[str] = []
    for match in URL.finditer(line):
        host = match["host"].split("@")[-1].split(":")[0].lower()
        if host not in allowed_hosts:
            findings.append(f"{location}: URL '{match[0]}'")
    line_without_urls = URL.sub(" ", line)
    findings.extend(
        f"{location}: host '{match['host']}'"
        for match in HOST.finditer(line_without_urls)
        if match["host"].lower() not in allowed_hosts
    )
    findings.extend(
        f"{location}: IP address '{match[0]}'"
        for match in IP_ADDRESS.finditer(line_without_urls)
    )
    findings.extend(
        f"{location}: email '{match[0]}'" for match in EMAIL.finditer(line_without_urls)
    )
    if any(secret.search(line) for secret in SECRETS):
        findings.append(f"{location}: looks like a secret")
    return findings


def relevant_identifiers(
    files: list[Path],
    repository: Path,
    excluded_directories: list[Path],
    generic_names: set[str],
) -> dict[str, str]:
    external = known_external_names()
    excluded = {path.resolve() for path in files}
    return {
        name: origin
        for name, origin in collect_repository_identifiers(
            repository, excluded, excluded_directories
        ).items()
        if name not in generic_names
        and name not in external
        and not (name.startswith("__") and name.endswith("__"))
        and len(name) >= 3
    }


def build_word_pattern(words: dict[str, str]) -> re.Pattern[str] | None:
    if not words:
        return None
    escaped_words = [re.escape(word) for word in sorted(words, key=len, reverse=True)]
    return re.compile(r"(?<![\w-])(" + "|".join(escaped_words) + r")(?![\w-])")


def find_leaks(
    files: list[Path], repository: Path, excluded_directories: list[Path]
) -> list[str]:
    generic_names, allowed_hosts = load_generic_names()
    identifiers = relevant_identifiers(
        files, repository, excluded_directories, generic_names
    )
    words = {
        name: origin
        for name, origin in identifiers.items()
        if re.fullmatch(r"\w+", name)
    }
    word_pattern = build_word_pattern(words)
    literals = {
        name: origin for name, origin in identifiers.items() if name not in words
    }

    findings: list[str] = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            location = f"{path}:{line_number}"
            findings.extend(
                identifier_findings(location, line, word_pattern, words, literals)
            )
            findings.extend(pattern_findings(location, line, allowed_hosts))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack leak-check",
        description=(
            "Flag domain information (repo identifiers, URLs, emails, secrets) "
            "in generated files."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Generated files or folders to check (default: [leak_check].paths).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="The repo the files were generated from (default: the git root).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help=(
            "Repo folder (relative to --repo) whose code is tooling, not the "
            "analyzed project. Repeatable (default: [leak_check].exclude)."
        ),
    )
    arguments = parser.parse_args(argv)
    config = resolve_config({"leak_check.paths": arguments.paths or None})

    repository = (
        arguments.repo.expanduser().resolve()
        if arguments.repo
        else config.git_root or config.root
    )
    excluded_directories = (
        [repository / directory for directory in arguments.exclude]
        if arguments.exclude
        else config.values.leak_check.exclude
    )
    findings = find_leaks(
        generated_files(config.values.leak_check.paths),
        repository,
        excluded_directories,
    )
    for finding in findings:
        logger.error("%s", finding)
    if findings:
        logger.error(
            "check_no_domain_leak: %d finding(s). Rewrite them as generic practices "
            "or drop them as domain-dependent.",
            len(findings),
        )
        return 1
    logger.info("check_no_domain_leak: OK")
    return 0
