import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

# rulepack's config: the guards read the paths rulepack also checks.
RULEPACK_CONFIG_FILE_NAME = ".rulepack.toml"
# The guards' own settings, which rulepack does not accept.
CONFIG_FILE_NAME = ".mstack.toml"


class ConfigError(Exception):
    pass


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RulepackScanSettings(BaseModel):
    exclude: list[str] = []


class RulepackSettings(BaseModel):
    """The keys of .rulepack.toml the guards read. Others belong to rulepack alone."""

    sgconfig: Path = Path("lint/sgconfig.yml")
    importlinter: Path = Path(".importlinter")
    scan: RulepackScanSettings = RulepackScanSettings()


class DomainCheckSettings(StrictModel):
    paths: list[Path] = [Path("lint"), Path(".cursor/rules")]
    exclude: list[Path] = []


class CommitsSettings(StrictModel):
    # The Conventional Commits types `mstack commit-msg` accepts.
    types: list[str] = [
        "build",
        "chore",
        "ci",
        "docs",
        "feat",
        "fix",
        "perf",
        "refactor",
        "style",
        "test",
    ]


class GuardSettings(StrictModel):
    rules_dir: Path = Path(".cursor/rules")
    pre_commit_config: Path = Path(".pre-commit-config.yaml")
    domain_check: DomainCheckSettings = DomainCheckSettings()
    commits: CommitsSettings = CommitsSettings()


class GuardConfig(BaseModel):
    """Both files resolved. Every path is absolute."""

    root: Path
    git_root: Path | None
    rules_dir: Path
    sgconfig: Path
    importlinter: Path
    pre_commit_config: Path
    scan_exclude: list[str]
    # The folder scan_exclude globs are relative to.
    scan_root: Path
    domain_check: DomainCheckSettings
    commit_types: list[str]


def find_git_root(start: Path) -> Path | None:
    return next(
        (
            directory
            for directory in (start, *start.parents)
            if (directory / ".git").exists()
        ),
        None,
    )


def find_config_path(start: Path, git_root: Path | None, name: str) -> Path | None:
    """Find the nearest config file without looking above the git root."""
    directories = [start]
    if git_root is not None:
        directories.extend(
            parent for parent in start.parents if parent.is_relative_to(git_root)
        )
    return next(
        (directory / name for directory in directories if (directory / name).is_file()),
        None,
    )


def read_toml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: invalid TOML ({error})") from error


def validate_settings[Settings: BaseModel](
    model: type[Settings], path: Path | None
) -> Settings:
    try:
        return model.model_validate(read_toml(path))
    except ValidationError as error:
        raise ConfigError(f"{path}: {error}") from error


def absolute(path: Path, base: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else base / path


def resolve_config(start: Path | None = None) -> GuardConfig:
    """Read .mstack.toml and .rulepack.toml, each relative to its own folder."""
    start = (start or Path.cwd()).resolve()
    git_root = find_git_root(start)
    guard_file = find_config_path(start, git_root, CONFIG_FILE_NAME)
    rulepack_file = find_config_path(start, git_root, RULEPACK_CONFIG_FILE_NAME)
    guard_settings = validate_settings(GuardSettings, guard_file)
    rulepack_settings = validate_settings(RulepackSettings, rulepack_file)
    fallback_root = git_root or start
    guard_root = guard_file.parent if guard_file else fallback_root
    rulepack_root = rulepack_file.parent if rulepack_file else fallback_root
    domain_check = guard_settings.domain_check
    return GuardConfig(
        root=guard_root,
        git_root=git_root,
        rules_dir=absolute(guard_settings.rules_dir, guard_root),
        sgconfig=absolute(rulepack_settings.sgconfig, rulepack_root),
        importlinter=absolute(rulepack_settings.importlinter, rulepack_root),
        pre_commit_config=absolute(guard_settings.pre_commit_config, guard_root),
        scan_exclude=rulepack_settings.scan.exclude,
        scan_root=rulepack_root,
        domain_check=DomainCheckSettings(
            paths=[absolute(path, guard_root) for path in domain_check.paths],
            exclude=[absolute(path, guard_root) for path in domain_check.exclude],
        ),
        commit_types=guard_settings.commits.types,
    )
