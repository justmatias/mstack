import argparse
import sys
import tomllib
from pathlib import Path

from mstack.config import ConfigError, StrictModel


class Pack(StrictModel):
    name: str
    rules_dir: Path
    checks_dir: Path
    tests_dir: Path
    rules: list[Path]
    checks: list[Path]
    tests: list[Path]


def pack_root() -> Path:
    package = Path(__file__).resolve().parent
    bundled = package / "pack_data"
    if (bundled / "packs.toml").is_file():
        return bundled
    checkout = package.parents[1]
    if (checkout / "packs.toml").is_file():
        return checkout
    raise ConfigError("shared rule pack assets are missing; reinstall mstack")


class ManifestEntry(StrictModel):
    rules: list[str]
    checks: list[str]


def load_manifest(root: Path) -> dict[str, ManifestEntry]:
    data = tomllib.loads((root / "packs.toml").read_text(encoding="utf-8"))
    return {
        name: ManifestEntry.model_validate(entry)
        for name, entry in data["packs"].items()
    }


def load_packs(names: list[str]) -> list[Pack]:
    if not names:
        return []
    root = pack_root()
    manifest = load_manifest(root)
    unknown = sorted(set(names) - manifest.keys())
    if unknown:
        raise ConfigError(f"unknown rule pack(s): {', '.join(unknown)}")
    return [build_pack(root, name, manifest[name]) for name in dict.fromkeys(names)]


def build_pack(root: Path, name: str, entry: ManifestEntry) -> Pack:
    rules_dir = root / "rules"
    checks_dir = root / "lint" / "rules"
    tests_dir = root / "lint" / "rule-tests"
    rules = [rules_dir / f"{rule}.mdc" for rule in entry.rules]
    checks = [checks_dir / f"{check}.yml" for check in entry.checks]
    tests = [tests_dir / f"{check}-test.yml" for check in entry.checks]
    for path in (*rules, *checks, *tests):
        if not path.is_file():
            raise ConfigError(f"pack {name!r} is missing {path.relative_to(root)}")
    return Pack(
        name=name,
        rules_dir=rules_dir,
        checks_dir=checks_dir,
        tests_dir=tests_dir,
        rules=rules,
        checks=checks,
        tests=tests,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="mstack packs")
    parser.add_argument("command", choices=["list"])
    parser.parse_args(argv)
    names = list(load_manifest(pack_root()))
    for pack in load_packs(names):
        rules = ", ".join(path.stem for path in pack.rules)
        checks = ", ".join(path.stem for path in pack.checks)
        sys.stdout.write(
            f"{pack.name}\n  Rules: {rules}\n  Checks: {checks or '(none)'}\n"
        )
    return 0
