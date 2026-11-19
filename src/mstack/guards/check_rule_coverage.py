import argparse
import configparser
import json
import logging
import re
import sys
from pathlib import Path

import yaml

from mstack.guards.conventions_inventory import read_convention

logger = logging.getLogger(__name__)

CHECKS_HEADING = re.compile(r"^##\s+Checks\s*$")
ENFORCED_BY = re.compile(r"^\s*-\s*enforced-by:\s*(?P<check_id>\S+)\s*$")
LLM_REVIEW = re.compile(r"^\s*-\s*enforcement:\s*llm-review\s*$")
IMPORT_LINTER_CONTRACT = re.compile(r"^importlinter:contract:(?P<contract_id>.+)$")


def parse_checks_section(mdc_path: Path) -> dict | None:
    lines = mdc_path.read_text(encoding="utf-8").splitlines()
    start = next(
        (index for index, line in enumerate(lines) if CHECKS_HEADING.match(line)), None
    )
    if start is None:
        return None
    enforced_by: dict[str, int] = {}
    llm_review = False
    for line_number, line in enumerate(lines[start + 1 :], start=start + 2):
        if line.startswith("#"):
            break
        if match := ENFORCED_BY.match(line):
            enforced_by[match["check_id"]] = line_number
        elif LLM_REVIEW.match(line):
            llm_review = True
    return {"enforced_by": enforced_by, "llm_review": llm_review}


def mdc_frontmatter(mdc_path: Path) -> dict:
    text = mdc_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        return yaml.safe_load(text.split("---", 2)[1]) or {}
    except yaml.YAMLError:
        return {}


def derived_issues(mdc_path: Path, root: Path) -> list[dict]:
    frontmatter = mdc_frontmatter(mdc_path)
    source = frontmatter.get("derived-from")
    if not source:
        return []
    location = display(mdc_path, root)
    source_path = Path(str(source)).expanduser()
    if not source_path.is_file():
        return [
            {
                "kind": "orphan",
                "file": location,
                "detail": f"derived-from '{source}' no longer exists",
            }
        ]
    try:
        current = read_convention(source_path)["sha256"]
    except ValueError as error:
        return [
            {
                "kind": "stale",
                "file": location,
                "detail": f"derived-from '{source}' is malformed ({error})",
            }
        ]
    if current != str(frontmatter.get("derived-sha256", "")):
        return [
            {
                "kind": "stale",
                "file": location,
                "detail": f"'{source}' changed since this rule was derived",
            }
        ]
    return []


def load_ast_grep_rules(config_path: Path) -> dict[str, dict]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    rules: dict[str, dict] = {}
    for rule_directory in config.get("ruleDirs", []):
        for rule_path in sorted((config_path.parent / rule_directory).glob("*.y*ml")):
            for document in yaml.safe_load_all(rule_path.read_text(encoding="utf-8")):
                if document and "id" in document:
                    rules[document["id"]] = {
                        "path": rule_path,
                        "source": (document.get("metadata") or {}).get("source"),
                        "severity": document.get("severity", "hint"),
                    }
    return rules


def load_import_linter_contracts(importlinter_path: Path) -> set[str]:
    if not importlinter_path.is_file():
        return set()
    parser = configparser.ConfigParser()
    parser.read(importlinter_path, encoding="utf-8")
    return {
        match["contract_id"]
        for section in parser.sections()
        if (match := IMPORT_LINTER_CONTRACT.match(section))
    }


def resolve_source(source: str, root: Path) -> Path:
    path = Path(source).expanduser()
    return path if path.is_absolute() else root / path


def display(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def prose_rule_issues(
    rules_dir: Path, known_checks: set[str], root: Path, pattern: str = "*.mdc"
) -> tuple[list[dict], list[dict], dict[Path, set[str]]]:
    issues: list[dict] = []
    rules: list[dict] = []
    listed_by_mdc: dict[Path, set[str]] = {}
    for mdc_path in sorted(rules_dir.rglob(pattern)):
        issues.extend(derived_issues(mdc_path, root))
        section = parse_checks_section(mdc_path)
        entry = {"mdc": display(mdc_path, root), "checks": [], "llm_review": False}
        rules.append(entry)
        if section is None or not (section["enforced_by"] or section["llm_review"]):
            issues.append({
                "kind": "missing-checks-section",
                "file": display(mdc_path, root),
                "detail": (
                    "no '## Checks' section with 'enforced-by:' or "
                    "'enforcement: llm-review'"
                ),
            })
            continue
        entry["checks"] = sorted(section["enforced_by"])
        entry["llm_review"] = section["llm_review"]
        listed_by_mdc[mdc_path.resolve()] = set(section["enforced_by"])
        issues.extend(
            {
                "kind": "unknown-check",
                "file": f"{display(mdc_path, root)}:{line_number}",
                "check": check_id,
                "detail": (
                    f"'enforced-by: {check_id}' has no YAML rule and no "
                    "import-linter contract"
                ),
            }
            for check_id, line_number in section["enforced_by"].items()
            if check_id not in known_checks
        )
    return rules, issues, listed_by_mdc


def check_source_issues(
    ast_grep_rules: dict, listed_by_mdc: dict[Path, set[str]], root: Path
) -> list[dict]:
    issues: list[dict] = []
    for check_id, rule in sorted(ast_grep_rules.items()):
        rule_file = display(rule["path"], root)
        if not rule["source"]:
            issues.append({
                "kind": "orphan",
                "file": rule_file,
                "check": check_id,
                "detail": "the YAML has no metadata.source",
            })
            continue
        source_path = resolve_source(rule["source"], root)
        if not source_path.is_file():
            issues.append({
                "kind": "missing-source",
                "file": rule_file,
                "check": check_id,
                "detail": f"metadata.source '{rule['source']}' does not exist",
            })
        elif check_id not in listed_by_mdc.get(source_path.resolve(), set()):
            issues.append({
                "kind": "unlisted-check",
                "file": rule_file,
                "check": check_id,
                "detail": (
                    f"'{rule['source']}' does not list 'enforced-by: {check_id}'"
                ),
            })
    return issues


def compute_drift(
    rules_dir: Path,
    config: Path,
    importlinter: Path,
    root: Path,
    pattern: str = "*.mdc",
) -> dict:
    ast_grep_rules = load_ast_grep_rules(config)
    contracts = load_import_linter_contracts(importlinter)
    known_checks = set(ast_grep_rules) | contracts
    rules, issues, listed_by_mdc = prose_rule_issues(
        rules_dir, known_checks, root, pattern
    )
    issues.extend(check_source_issues(ast_grep_rules, listed_by_mdc, root))
    return {"ok": not issues, "rules": rules, "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack coverage",
        description="Check that every prose rule and every check point to each other.",
    )
    parser.add_argument("--rules-dir", type=Path, default=Path(".cursor/rules"))
    parser.add_argument("--config", type=Path, default=Path("lint-rules/sgconfig.yml"))
    parser.add_argument("--importlinter", type=Path, default=Path(".importlinter"))
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Directory that relative metadata.source paths resolve against.",
    )
    parser.add_argument(
        "--glob",
        default="*.mdc",
        help="Which .mdc files in --rules-dir to check (personal set: 'my-*.mdc').",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the drift report as JSON."
    )
    arguments = parser.parse_args(argv)

    report = compute_drift(
        arguments.rules_dir.expanduser(),
        arguments.config.expanduser(),
        arguments.importlinter.expanduser(),
        arguments.root.expanduser(),
        arguments.glob,
    )
    if arguments.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        for issue in report["issues"]:
            logger.error("%s: [%s] %s", issue["file"], issue["kind"], issue["detail"])
        if report["ok"]:
            logger.info("check_rule_coverage: OK (%d rules)", len(report["rules"]))
    return 0 if report["ok"] else 1
