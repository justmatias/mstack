import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

RULEPACK_CONFIG_FILE_NAME = ".rulepack.toml"
# Where the prose rules and the pre-commit config live, relative to the root.
# rulepack does not accept these keys, so a repo that moves them passes a flag.
DEFAULT_RULES_DIR = Path(".cursor/rules")
DEFAULT_PRE_COMMIT_CONFIG = Path(".pre-commit-config.yaml")


class ConfigError(Exception):
    pass


class RulepackSettings(BaseModel):
    """The keys of .rulepack.toml the guards read. Others belong to rulepack alone."""

    sgconfig: Path = Path("lint/sgconfig.yml")
    importlinter: Path = Path(".importlinter")


class GuardConfig(BaseModel):
    """The resolved paths. Every path is absolute."""

    root: Path
    rules_dir: Path
    sgconfig: Path
    importlinter: Path
    pre_commit_config: Path


def find_git_root(start: Path) -> Path | None:
    return next(
        (
            directory
            for directory in (start, *start.parents)
            if (directory / ".git").exists()
        ),
        None,
    )


def find_config_path(start: Path, git_root: Path | None) -> Path | None:
    """Find the nearest .rulepack.toml without looking above the git root."""
    directories = [start]
    if git_root is not None:
        directories.extend(
            parent for parent in start.parents if parent.is_relative_to(git_root)
        )
    return next(
        (
            directory / RULEPACK_CONFIG_FILE_NAME
            for directory in directories
            if (directory / RULEPACK_CONFIG_FILE_NAME).is_file()
        ),
        None,
    )


def read_toml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: invalid TOML ({error})") from error


def absolute(path: Path, base: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else base / path


def resolve_config(start: Path | None = None) -> GuardConfig:
    """Read .rulepack.toml; its paths and the defaults resolve against its folder."""
    start = (start or Path.cwd()).resolve()
    git_root = find_git_root(start)
    config_file = find_config_path(start, git_root)
    try:
        settings = RulepackSettings.model_validate(read_toml(config_file))
    except ValidationError as error:
        raise ConfigError(f"{config_file}: {error}") from error
    root = config_file.parent if config_file else git_root or start
    return GuardConfig(
        root=root,
        rules_dir=root / DEFAULT_RULES_DIR,
        sgconfig=absolute(settings.sgconfig, root),
        importlinter=absolute(settings.importlinter, root),
        pre_commit_config=root / DEFAULT_PRE_COMMIT_CONFIG,
    )
