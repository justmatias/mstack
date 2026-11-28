import argparse
import configparser
import json
import logging
import re
import sys
from pathlib import Path

import yaml

from mstack.guards.config import ConfigError, GuardConfig, absolute, resolve_config
from mstack.guards.credit import credit_problems
from mstack.render import FrontmatterError, split_frontmatter

logger = logging.getLogger(__name__)

CHECKS_HEADING = re.compile(r"^##\s+Checks\s*$")
ENFORCED_BY = re.compile(r"^\s*-\s*enforced-by:\s*(?P<check_id>\S+)\s*$")
ENFORCED_BY_HOOK = re.compile(r"^\s*-\s*enforced-by-hook:\s*(?P<hook_id>\S+)\s*$")
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
    hooks: dict[str, int] = {}
    llm_review = False
    for line_number, line in enumerate(lines[start + 1 :], start=start + 2):
        if line.startswith("#"):
            break
        if match := ENFORCED_BY.match(line):
            enforced_by[match["check_id"]] = line_number
        elif match := ENFORCED_BY_HOOK.match(line):
            hooks[match["hook_id"]] = line_number
        elif LLM_REVIEW.match(line):
            llm_review = True
    return {"enforced_by": enforced_by, "hooks": hooks, "llm_review": llm_review}


def load_ast_grep_rules(config_path: Path) -> dict[str, dict]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    paths = [
        path
        for directory in config.get("ruleDirs", [])
        for path in sorted((config_path.parent / directory).glob("*.y*ml"))
    ]
    return load_ast_grep_rule_files(paths)


def load_ast_grep_rule_files(paths: list[Path]) -> dict[str, dict]:
    rules: dict[str, dict] = {}
    for rule_path in paths:
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


def load_pre_commit_hooks(config_path: Path) -> set[str] | None:
    """Every hook id in every repo of the config, `local` ones included.

    None when the file is missing, so every `enforced-by-hook` is unknown.
    """
    if not config_path.is_file():
        return None
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    repos = config.get("repos") if isinstance(config, dict) else None
    return {
        hook["id"]
        for repo in repos or []
        if isinstance(repo, dict)
        for hook in repo.get("hooks") or []
        if isinstance(hook, dict) and "id" in hook
    }


def unknown_hook_issues(
    mdc: str, hooks: dict[str, int], configured: set[str] | None, config_name: str
) -> list[dict]:
    reason = (
        f"there is no {config_name}"
        if configured is None
        else f"no hook with this id in {config_name}"
    )
    return [
        {
            "kind": "unknown-hook",
            "file": f"{mdc}:{line_number}",
            "check": hook_id,
            "detail": f"'enforced-by-hook: {hook_id}': {reason}",
        }
        for hook_id, line_number in hooks.items()
        if configured is None or hook_id not in configured
    ]


def frontmatter_issues(mdc_path: Path, mdc: str) -> list[dict]:
    try:
        frontmatter, _ = split_frontmatter(mdc_path.read_text(encoding="utf-8"))
    except FrontmatterError as error:
        return [{"kind": "invalid-frontmatter", "file": mdc, "detail": str(error)}]
    return [
        {"kind": "credit", "file": mdc, "detail": problem}
        for problem in credit_problems(frontmatter)
    ]


def display(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def prose_rule_issues(
    prose_paths: list[Path],
    known_checks: set[str],
    root: Path,
    pre_commit_config: Path,
) -> tuple[list[dict], list[dict], dict[Path, set[str]]]:
    configured_hooks = load_pre_commit_hooks(pre_commit_config)
    issues: list[dict] = []
    rules: list[dict] = []
    listed_by_mdc: dict[Path, set[str]] = {}
    for mdc_path in sorted(prose_paths):
        section = parse_checks_section(mdc_path)
        mdc = display(mdc_path, root)
        entry = {"mdc": mdc, "checks": [], "hooks": [], "llm_review": False}
        rules.append(entry)
        issues.extend(frontmatter_issues(mdc_path, mdc))
        if section is None or not (
            section["enforced_by"] or section["hooks"] or section["llm_review"]
        ):
            issues.append({
                "kind": "missing-checks-section",
                "file": mdc,
                "detail": (
                    "no '## Checks' section with 'enforced-by:', "
                    "'enforced-by-hook:' or 'enforcement: llm-review'"
                ),
            })
            continue
        entry["checks"] = sorted(section["enforced_by"])
        entry["hooks"] = sorted(section["hooks"])
        entry["llm_review"] = section["llm_review"]
        issues.extend(
            unknown_hook_issues(
                mdc, section["hooks"], configured_hooks, pre_commit_config.name
            )
        )
        listed_by_mdc[mdc_path.resolve()] = set(section["enforced_by"])
        issues.extend(
            {
                "kind": "unknown-check",
                "file": f"{mdc}:{line_number}",
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
        source = rule["source"]
        if source is None:
            continue
        rule_file = display(rule["path"], root)
        source_path = absolute(Path(source), root) if isinstance(source, str) else None
        if source_path is None or not source_path.is_file():
            issues.append({
                "kind": "missing-source",
                "file": rule_file,
                "check": check_id,
                "detail": f"metadata.source {source!r} must point to an existing prose rule",
            })
        elif check_id not in listed_by_mdc.get(source_path.resolve(), set()):
            issues.append({
                "kind": "unlisted-check",
                "file": rule_file,
                "check": check_id,
                "detail": f"{source!r} does not list 'enforced-by: {check_id}'",
            })
    return issues


def compute_drift(settings: GuardConfig, root: Path) -> dict:
    if not settings.sgconfig.is_file():
        raise ConfigError(
            f"no ast-grep config at {settings.sgconfig} "
            "(set sgconfig in .rulepack.toml or pass --config)"
        )

    ast_grep_rules = load_ast_grep_rules(settings.sgconfig)
    known_checks = set(ast_grep_rules) | load_import_linter_contracts(
        settings.importlinter
    )

    rules, issues, listed_by_mdc = prose_rule_issues(
        list(settings.rules_dir.rglob("*.mdc")),
        known_checks,
        root,
        settings.pre_commit_config,
    )
    issues.extend(check_source_issues(ast_grep_rules, listed_by_mdc, root))
    return {"ok": not issues, "rules": rules, "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack coverage",
        description="Validate check references in prose and any declared ast-grep source links.",
    )
    parser.add_argument(
        "--rules-dir", type=Path, help="Prose rules folder (default: from config)."
    )
    parser.add_argument(
        "--config", type=Path, help="ast-grep sgconfig.yml (default: from config)."
    )
    parser.add_argument(
        "--importlinter", type=Path, help="import-linter file (default: from config)."
    )
    parser.add_argument(
        "--pre-commit-config",
        type=Path,
        help="pre-commit config whose hook ids count as checks (default: from config).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Directory that relative metadata.source paths resolve against "
            "(default: the config file's folder)."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the drift report as JSON."
    )
    arguments = parser.parse_args(argv)
    flag_paths = {
        "rules_dir": arguments.rules_dir,
        "sgconfig": arguments.config,
        "importlinter": arguments.importlinter,
        "pre_commit_config": arguments.pre_commit_config,
    }
    config = resolve_config().model_copy(
        update={key: path.resolve() for key, path in flag_paths.items() if path}
    )

    root = arguments.root.expanduser() if arguments.root else config.root
    report = compute_drift(config, root)
    if arguments.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        for issue in report["issues"]:
            logger.error("%s: [%s] %s", issue["file"], issue["kind"], issue["detail"])
        if report["ok"]:
            logger.info("coverage: OK (%d rules)", len(report["rules"]))
    return 0 if report["ok"] else 1
