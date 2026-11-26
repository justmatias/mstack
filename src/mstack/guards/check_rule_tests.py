import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_SGCONFIG = Path("lint/sgconfig.yml")

IssueKind = Literal[
    "duplicate-rule-id",
    "untested-rule",
    "unknown-rule-test",
    "missing-valid-cases",
    "missing-invalid-cases",
]


class RuleTestsConfigError(ValueError):
    """The sgconfig or a rule file cannot be read."""


class AstGrepTestConfig(BaseModel):
    test_dir: Path = Field(alias="testDir")


class AstGrepConfig(BaseModel):
    """The keys of an sgconfig.yml that say where rules and their tests live."""

    rule_dirs: list[Path] = Field(default=[], alias="ruleDirs")
    test_configs: list[AstGrepTestConfig] = Field(default=[], alias="testConfigs")


class Rule(BaseModel):
    rule_id: str
    path: Path


class RuleTest(BaseModel):
    rule_id: str
    path: Path
    valid_cases: int
    invalid_cases: int


class CoverageIssue(BaseModel):
    kind: IssueKind
    file: str
    rule: str
    detail: str


class CoverageReport(BaseModel):
    rules: list[str]
    issues: list[CoverageIssue]


def read_yaml_documents(path: Path) -> list[dict[str, Any]]:
    try:
        documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    except yaml.YAMLError as error:
        raise RuleTestsConfigError(f"{path}: invalid YAML ({error})") from error
    return [document for document in documents if isinstance(document, dict)]


def find_yaml_files(directories: list[Path]) -> list[Path]:
    """Every YAML file under the directories, nested ones included, as ast-grep loads them."""
    return sorted(
        path
        for directory in directories
        for pattern in ("*.yml", "*.yaml")
        for path in directory.rglob(pattern)
    )


def load_ast_grep_config(path: Path) -> AstGrepConfig:
    documents = read_yaml_documents(path)
    try:
        return AstGrepConfig.model_validate(documents[0] if documents else {})
    except ValidationError as error:
        raise RuleTestsConfigError(f"{path}: {error}") from error


def load_rules(rule_dirs: list[Path]) -> list[Rule]:
    return [
        Rule(rule_id=str(document["id"]), path=path)
        for path in find_yaml_files(rule_dirs)
        for document in read_yaml_documents(path)
        if "id" in document
    ]


def load_rule_tests(test_dirs: list[Path]) -> list[RuleTest]:
    return [
        RuleTest(
            rule_id=str(document["id"]),
            path=path,
            valid_cases=len(document.get("valid") or []),
            invalid_cases=len(document.get("invalid") or []),
        )
        for path in find_yaml_files(test_dirs)
        for document in read_yaml_documents(path)
        if "id" in document
    ]


def display_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def find_rule_issues(
    rules: list[Rule], tested_ids: set[str], root: Path
) -> list[CoverageIssue]:
    paths_by_id: dict[str, list[Path]] = defaultdict(list)
    for rule in rules:
        paths_by_id[rule.rule_id].append(rule.path)
    issues: list[CoverageIssue] = []
    for rule_id, paths in sorted(paths_by_id.items()):
        first_path, *duplicate_paths = paths
        issues.extend(
            CoverageIssue(
                kind="duplicate-rule-id",
                file=display_path(path, root),
                rule=rule_id,
                detail=f"'{rule_id}' is also declared in {display_path(first_path, root)}",
            )
            for path in duplicate_paths
        )
        if rule_id not in tested_ids:
            issues.append(
                CoverageIssue(
                    kind="untested-rule",
                    file=display_path(first_path, root),
                    rule=rule_id,
                    detail=f"no rule test in testConfigs has 'id: {rule_id}'",
                )
            )
    return issues


def find_rule_test_issue(
    rule_test: RuleTest, rule_ids: set[str], root: Path
) -> CoverageIssue | None:
    file = display_path(rule_test.path, root)
    if rule_test.rule_id not in rule_ids:
        return CoverageIssue(
            kind="unknown-rule-test",
            file=file,
            rule=rule_test.rule_id,
            detail=f"no rule in ruleDirs has 'id: {rule_test.rule_id}'",
        )
    if not rule_test.valid_cases:
        return CoverageIssue(
            kind="missing-valid-cases",
            file=file,
            rule=rule_test.rule_id,
            detail="add a 'valid' case: code the rule must not flag",
        )
    if not rule_test.invalid_cases:
        return CoverageIssue(
            kind="missing-invalid-cases",
            file=file,
            rule=rule_test.rule_id,
            detail="add an 'invalid' case: code the rule must flag",
        )
    return None


def build_coverage_report(sgconfig: Path, root: Path) -> CoverageReport:
    if not sgconfig.is_file():
        raise RuleTestsConfigError(
            f"no ast-grep config at {sgconfig} (pass --sgconfig)"
        )
    ast_grep_config = load_ast_grep_config(sgconfig)
    base = sgconfig.parent
    rules = load_rules([base / directory for directory in ast_grep_config.rule_dirs])
    rule_tests = load_rule_tests([
        base / test_config.test_dir for test_config in ast_grep_config.test_configs
    ])
    rule_ids = {rule.rule_id for rule in rules}
    test_issues = (
        find_rule_test_issue(rule_test, rule_ids, root) for rule_test in rule_tests
    )
    return CoverageReport(
        rules=sorted(rule_ids),
        issues=[
            *find_rule_issues(rules, {test.rule_id for test in rule_tests}, root),
            *(issue for issue in test_issues if issue),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack rule-tests-check",
        description=(
            "Check that every ast-grep rule has a rule test with valid and invalid "
            "cases, that every rule test names a rule, and that rule ids are unique."
        ),
    )
    parser.add_argument(
        "--sgconfig",
        type=Path,
        default=DEFAULT_SGCONFIG,
        help=f"ast-grep sgconfig.yml (default: {DEFAULT_SGCONFIG}).",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    arguments = parser.parse_args(argv)

    try:
        report = build_coverage_report(arguments.sgconfig, Path.cwd())
    except RuleTestsConfigError as error:
        logger.error("mstack rule-tests-check: %s", error)
        return 2
    if arguments.json:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
    else:
        for issue in report.issues:
            logger.error("%s: [%s] %s", issue.file, issue.kind, issue.detail)
        if not report.issues:
            logger.info(
                "rule-tests-check: OK (%d rules, each tested)", len(report.rules)
            )
    return 1 if report.issues else 0
