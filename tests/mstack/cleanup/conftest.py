import pytest


@pytest.fixture(autouse=True)
def _isolate_tool_folders(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-profile"))
    monkeypatch.setenv("MSTACK_PLATFORM", "linux")
    monkeypatch.setattr(
        "mstack.cleanup.run_quiet",
        lambda command: str(tmp_path / ("bin" if "--bin" in command else "uv-tools")),
    )
