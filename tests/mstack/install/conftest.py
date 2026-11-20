import shutil
from pathlib import Path

import pytest

from mstack.install import manifest
from mstack.install.render import render_rule


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home_directory = tmp_path / "home"
    home_directory.mkdir()
    # Path.home() reads USERPROFILE on Windows, and the manifest LOCALAPPDATA.
    monkeypatch.setenv("HOME", str(home_directory))
    monkeypatch.setenv("USERPROFILE", str(home_directory))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "state"))
    return home_directory


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    skill = root / "skills" / "demo-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo-skill\n---\n\n# Demo\n")
    (skill / "references" / "notes.md").write_text("Some notes.\n")
    (root / "skills" / "setup-mstack").mkdir()
    (root / "skills" / "setup-mstack" / "SKILL.md").write_text("# Setup\n")
    (root / "rules").mkdir()
    (root / "rules" / "demo.mdc").write_text(
        '---\ndescription: Demo rule\nglobs: "**/*.py"\nalwaysApply: false\n---\n\n'
        "# Demo\n\n- Do the thing.\n\n## Checks\n- enforcement: llm-review\n"
    )
    return root


@pytest.fixture
def install(checkout: Path, home: Path):
    """Copy the demo skill and rule the way setup-mstack does, then record them."""

    def run(*, record: bool = True) -> tuple[Path, Path]:
        skill_target = home / ".claude" / "skills" / "demo-skill"
        rule_target = home / ".claude" / "rules" / "demo.md"
        shutil.copytree(checkout / "skills" / "demo-skill", skill_target)
        rule_target.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_rule((checkout / "rules" / "demo.mdc").read_text())
        rule_target.write_text(rendered)
        if record:
            for kind, name, target in (
                ("skill", "demo-skill", skill_target),
                ("rule", "demo", rule_target),
            ):
                manifest.main([
                    "record",
                    kind,
                    name,
                    str(target),
                    "--checkout",
                    str(checkout),
                ])
        return skill_target, rule_target

    return run


@pytest.fixture
def states(checkout: Path):
    def run(tool: manifest.Tool = "claude") -> dict[str, str]:
        loaded = manifest.load_manifest(manifest.manifest_path())
        return {
            f"{row.kind}:{row.name}": row.state
            for row in manifest.compute_status(checkout, tool, loaded)
        }

    return run
