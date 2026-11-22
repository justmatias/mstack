import argparse
import contextlib
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field

from mstack.changed_files import ChangedFilesError, changed_files
from mstack.config import ConfigError, ResolvedConfig, StrictModel, resolve_config
from mstack.guards import check_domain, check_exceptions, check_rule_coverage
from mstack.packs import load_packs

logger = logging.getLogger(__name__)

STEPS = ("test", "scan", "imports", "coverage", "exceptions", "domain-check")
Mode = Literal["full", "changed", "files"]


class LintError(Exception):
    pass


class StepResult(StrictModel):
    ok: bool
    skipped: str | None = None
    findings: list[Any] = Field(default_factory=list)


class LintRun(StrictModel):
    """What one `mstack lint` invocation scans and how it reports."""

    config: ResolvedConfig
    mode: Mode = "full"
    files: list[Path] = Field(default_factory=list)
    json_output: bool = False
    scan_config: Path | None = None


def find_tool(name: str) -> str:
    """The tool installed with mstack wins over whatever is on PATH."""
    directories = [Path(sysconfig.get_path("scripts")), Path(sys.executable).parent]
    for directory in directories:
        for candidate in (directory / name, directory / f"{name}.exe"):
            if candidate.is_file():
                return str(candidate)
    if found := shutil.which(name):
        return found
    raise LintError(
        f"'{name}' was not found next to {sys.executable} or on PATH; "
        "reinstall mstack (uv tool install --editable <checkout>)"
    )


def run_tool(
    command: list[str], run: LintRun, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    logger.debug("lint: %s", " ".join(command))
    return subprocess.run(
        command,
        cwd=run.config.root,
        capture_output=run.json_output,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )


def output_lines(completed: subprocess.CompletedProcess) -> list[str]:
    return [
        line
        for line in f"{completed.stdout or ''}{completed.stderr or ''}".splitlines()
        if line.strip()
    ]


def tool_result(completed: subprocess.CompletedProcess) -> StepResult:
    ok = completed.returncode == 0
    return StepResult(ok=ok, findings=[] if ok else output_lines(completed))


def sgconfig_path(run: LintRun) -> Path:
    path = run.scan_config or run.config.values.sgconfig
    if not path.is_file():
        raise LintError(f"no ast-grep config at {path} (set sgconfig in .mstack.toml)")
    return path


def local_config(config: ResolvedConfig) -> dict:
    path = config.values.sgconfig
    if not path.is_file():
        if config.sources["sgconfig"] != "default":
            raise LintError(f"no ast-grep config at {path}")
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key in ("ruleDirs", "utilDirs"):
        if key in data:
            data[key] = [str(path.parent / directory) for directory in data[key]]
    for entry in data.get("testConfigs") or []:
        entry["testDir"] = str(path.parent / entry["testDir"])
    for entry in (data.get("customLanguages") or {}).values():
        entry["libraryPath"] = str(path.parent / entry["libraryPath"])
    return data


def pack_rules(config: ResolvedConfig) -> tuple[dict, set[Path]]:
    rules: dict = {}
    tests: set[Path] = set()
    for pack in load_packs(config.values.packs):
        for path in pack.checks:
            for document in yaml.safe_load_all(path.read_text(encoding="utf-8")):
                if document:
                    rules[document["id"]] = document
        tests.update(pack.tests)
    return rules, tests


def local_rule_ids(data: dict) -> set[str]:
    return {
        entry["id"]
        for directory in data.get("ruleDirs", [])
        for path in Path(directory).rglob("*.y*ml")
        for entry in yaml.safe_load_all(path.read_text(encoding="utf-8"))
        if entry and "id" in entry
    }


def write_pack_tests(directory: Path, tests: set[Path], selected: set[str]) -> None:
    for index, path in enumerate(sorted(tests)):
        cases = [
            case
            for case in yaml.safe_load_all(path.read_text(encoding="utf-8"))
            if case and case.get("id") in selected
        ]
        if cases:
            (directory / f"{index}.yml").write_text(
                yaml.safe_dump_all(cases), encoding="utf-8"
            )


def write_pack_files(root: Path, config: ResolvedConfig, data: dict) -> None:
    rules, tests = pack_rules(config)
    overrides = config.values.pack_overrides
    if unknown := (set(overrides.disable) | overrides.severity.keys()) - rules.keys():
        raise ConfigError(
            f"pack_overrides: unknown checks: {', '.join(sorted(unknown))}"
        )
    local_ids = local_rule_ids(data)
    for check_id in sorted(local_ids & rules.keys()):
        logger.info("lint: local check %s overrides the shared pack check", check_id)
    selected = rules.keys() - local_ids - set(overrides.disable)
    rules_dir = root / "rules"
    tests_dir = root / "tests"
    rules_dir.mkdir()
    tests_dir.mkdir()
    for index, check_id in enumerate(sorted(selected)):
        document = rules[check_id]
        if check_id in overrides.severity:
            document["severity"] = overrides.severity[check_id]
        (rules_dir / f"{index}.yml").write_text(
            yaml.safe_dump(document), encoding="utf-8"
        )
    write_pack_tests(tests_dir, tests, selected)
    data.setdefault("ruleDirs", []).append(str(rules_dir))
    data.setdefault("testConfigs", []).append({"testDir": str(tests_dir)})


@contextlib.contextmanager
def packed_run(run: LintRun, steps: list[str]) -> Generator[LintRun, None, None]:
    if not run.config.values.packs or not {"scan", "test"}.intersection(steps):
        yield run
        return
    with tempfile.TemporaryDirectory(prefix="mstack-packs-") as directory:
        root = Path(directory)
        data = local_config(run.config)
        write_pack_files(root, run.config, data)
        path = root / "sgconfig.yml"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        yield run.model_copy(update={"scan_config": path})


def has_rule_tests(sgconfig: Path) -> bool:
    data = yaml.safe_load(sgconfig.read_text(encoding="utf-8")) or {}
    test_directories = [
        sgconfig.parent / entry["testDir"]
        for entry in data.get("testConfigs") or []
        if isinstance(entry, dict) and entry.get("testDir")
    ]
    return any(
        any(directory.glob("*.y*ml"))
        for directory in test_directories
        if directory.is_dir()
    )


def step_test(run: LintRun) -> StepResult:
    sgconfig = sgconfig_path(run)
    if not has_rule_tests(sgconfig):
        return StepResult(ok=True, skipped="the sgconfig has no rule tests")
    command = [find_tool("ast-grep"), "test", "-c", str(sgconfig)]
    return tool_result(run_tool([*command, "--skip-snapshot-tests"], run))


def scan_finding(line: str) -> dict[str, Any]:
    match = json.loads(line)
    return {
        "file": match.get("file"),
        "line": match.get("range", {}).get("start", {}).get("line", 0) + 1,
        "rule": match.get("ruleId"),
        "severity": match.get("severity"),
        "message": match.get("message"),
    }


def scan_targets(run: LintRun) -> list[str]:
    if run.mode == "full":
        excludes = [f"!{pattern}" for pattern in run.config.values.scan.exclude]
        return [argument for glob in excludes for argument in ("--globs", glob)] + ["."]
    return [
        "--error",
        *[os.path.relpath(path, run.config.root) for path in run.files],
    ]


def step_scan(run: LintRun) -> StepResult:
    sgconfig = sgconfig_path(run)
    if run.mode != "full" and not run.files:
        return StepResult(ok=True, skipped="no changed files to scan")
    command = [find_tool("ast-grep"), "scan", "-c", str(sgconfig)]
    if run.json_output:
        command.append("--json=stream")
    completed = run_tool([*command, *scan_targets(run)], run)
    if not run.json_output:
        return StepResult(ok=completed.returncode == 0)
    findings = [scan_finding(line) for line in completed.stdout.splitlines() if line]
    return StepResult(ok=completed.returncode == 0, findings=findings)


def project_lint_imports(root: Path) -> list[str] | None:
    """The repo's own lint-imports, when its uv environment provides one."""
    lock_file = root / "uv.lock"
    uv = shutil.which("uv")
    if (
        uv
        and lock_file.is_file()
        and 'name = "import-linter"' in lock_file.read_text(encoding="utf-8")
    ):
        return [uv, "run", "--frozen", "lint-imports"]
    return None


def step_imports(run: LintRun) -> StepResult:
    importlinter = run.config.values.importlinter
    if not importlinter.is_file():
        return StepResult(ok=True, skipped=f"no {importlinter.name}")
    root = run.config.root
    command = project_lint_imports(root)
    env = None
    if command:
        logger.info("lint: imports uses the project's lint-imports (uv run)")
    else:
        logger.info("lint: imports uses the lint-imports bundled with mstack")
        command = [find_tool("lint-imports")]
        python_path = [str(root), str(root / "src"), os.environ.get("PYTHONPATH", "")]
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join(path for path in python_path if path),
        }
    if importlinter.resolve() != (root / ".importlinter").resolve():
        command += ["--config", str(importlinter)]
    return tool_result(run_tool(command, run, env))


class ErrorCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def run_guard(main: Callable[[list[str]], int]) -> StepResult:
    """Call a guard in process; its error messages become the step's findings."""
    collector = ErrorCollector()
    root_logger = logging.getLogger()
    root_logger.addHandler(collector)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = main([])
    finally:
        root_logger.removeHandler(collector)
    return StepResult(ok=exit_code == 0, findings=collector.messages)


def step_coverage(run: LintRun) -> StepResult:
    rules_dir = run.config.values.rules_dir
    if (
        not run.config.values.packs
        and not rules_dir.is_dir()
        and not run.config.values.sgconfig.is_file()
    ):
        return StepResult(ok=True, skipped=f"no rules folder at {rules_dir}")
    return run_guard(
        lambda arguments: check_rule_coverage.main(arguments, resolved=run.config)
    )


def step_exceptions(_run: LintRun) -> StepResult:
    return run_guard(check_exceptions.main)


def step_domain_check(run: LintRun) -> StepResult:
    if not any(path.exists() for path in run.config.values.domain_check.paths):
        return StepResult(ok=True, skipped="none of [domain_check].paths exist")
    return run_guard(check_domain.main)


STEP_FUNCTIONS: dict[str, Callable[[LintRun], StepResult]] = {
    "test": step_test,
    "scan": step_scan,
    "imports": step_imports,
    "coverage": step_coverage,
    "exceptions": step_exceptions,
    "domain-check": step_domain_check,
}


def run_step(name: str, run: LintRun) -> StepResult:
    logger.info("lint: running %s", name)
    try:
        return STEP_FUNCTIONS[name](run)
    except (LintError, ConfigError, subprocess.CalledProcessError) as error:
        logger.error("lint: %s: %s", name, error)
        return StepResult(ok=False, findings=[str(error)])


def run_lint(steps: list[str], run: LintRun) -> dict[str, StepResult]:
    return {name: run_step(name, run) for name in steps}


def selected_steps(only: list[str] | None, skip: list[str] | None) -> list[str]:
    return [
        step
        for step in STEPS
        if (not only or step in only) and step not in (skip or [])
    ]


def selected_files(config: ResolvedConfig, names: list[str]) -> list[Path]:
    """The given files that exist, have a scanned extension and are not excluded."""
    extensions = config.values.scan.extensions
    files = {Path(name).resolve() for name in names}
    return sorted(
        path
        for path in files
        if path.is_file()
        and path.suffix in extensions
        and not check_exceptions.is_excluded(
            path, config.root.resolve(), config.values.scan.exclude
        )
    )


def build_run(arguments: argparse.Namespace) -> LintRun:
    config = resolve_config({"packs": arguments.packs})
    if arguments.files is not None:
        return LintRun(
            config=config,
            mode="files",
            files=selected_files(config, arguments.files),
            json_output=arguments.json,
        )
    if not arguments.changed:
        return LintRun(config=config, json_output=arguments.json)
    if config.git_root is None:
        raise LintError("--changed needs a git repository")
    changed = changed_files(
        config.git_root,
        base_ref=arguments.base_ref,
        default_base_ref=config.values.changed.base_ref,
        staged=arguments.staged,
        extensions=config.values.scan.extensions,
    )
    return LintRun(
        config=config,
        mode="changed",
        files=selected_files(config, [str(path) for path in changed]),
        json_output=arguments.json,
    )


def report(results: dict[str, StepResult], json_output: bool) -> None:
    for name, result in results.items():
        if result.skipped:
            logger.info("lint: %s skipped (%s)", name, result.skipped)
        elif result.ok:
            logger.info("lint: %s OK", name)
        else:
            logger.error("lint: %s FAILED", name)
    if json_output:
        sys.stdout.write(
            json.dumps(
                {name: result.model_dump() for name, result in results.items()},
                indent=2,
            )
            + "\n"
        )


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mstack lint",
        description=(
            "Run every check in order: ast-grep rule tests, the ast-grep scan, "
            "import-linter, and the coverage, exceptions and domain-check guards. "
            "All steps run; the exit code is 1 if any failed."
        ),
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--changed",
        action="store_true",
        help=(
            "Scan only the files changed against the base ref, and fail on "
            "warnings too."
        ),
    )
    selection.add_argument(
        "--files",
        nargs="+",
        metavar="FILE",
        help="Scan exactly these files, and fail on warnings too (for pre-commit).",
    )
    parser.add_argument(
        "--base-ref",
        help="With --changed: compare against this ref (default: [changed].base_ref).",
    )
    parser.add_argument(
        "--staged", action="store_true", help="With --changed: only the staged files."
    )
    parser.add_argument("--only", nargs="+", choices=STEPS, metavar="STEP")
    parser.add_argument("--skip", nargs="+", choices=STEPS, metavar="STEP")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print {step: {ok, skipped, findings}} as JSON.",
    )
    parser.add_argument(
        "--packs",
        nargs="*",
        help="Select packs explicitly, replacing repo or host defaults.",
    )
    arguments = parser.parse_args(argv)
    if (arguments.base_ref or arguments.staged) and not arguments.changed:
        parser.error("--base-ref and --staged need --changed")
    return arguments


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        run = build_run(arguments)
        steps = selected_steps(arguments.only, arguments.skip)
        with packed_run(run, steps) as prepared:
            results = run_lint(steps, prepared)
    except (LintError, ConfigError, ChangedFilesError, yaml.YAMLError) as error:
        logger.error("mstack lint: %s", error)
        return 2
    report(results, run.json_output)
    return 0 if all(result.ok for result in results.values()) else 1
