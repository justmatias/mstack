import importlib.metadata
import re
import subprocess

from mstack.doctor.model import SETUP_FIX, Context, Result

RELEASE_TAG = re.compile(r"refs/tags/v(?P<version>\d+\.\d+\.\d+)$")


def parse(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def display(version: tuple[int, ...]) -> str:
    return "v" + ".".join(str(part) for part in version)


def latest_release(context: Context) -> tuple[int, ...] | None:
    if context.checkout is None:
        return None
    completed = subprocess.run(
        ["git", "-C", str(context.checkout), "ls-remote", "--tags", "origin"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    versions = [
        parse(match["version"])
        for line in completed.stdout.splitlines()
        if (match := RELEASE_TAG.search(line))
    ]
    return max(versions, default=None)


def check_version(context: Context) -> list[Result]:
    """Only with --online: the one check that uses the network."""
    if not context.online:
        return []
    latest = latest_release(context)
    if latest is None:
        return [
            Result(
                group="version",
                check="latest",
                status="warn",
                detail="could not read the release tags from the checkout's origin",
            )
        ]
    installed = parse(importlib.metadata.version("mstack"))
    if latest > installed:
        return [
            Result(
                group="version",
                check="latest",
                status="warn",
                detail=f"{display(latest)} is out; this is {display(installed)}",
                fix=f"git pull in the checkout, then {SETUP_FIX}",
            )
        ]
    return [
        Result(
            group="version",
            check="latest",
            status="ok",
            detail=f"{display(latest)} is the latest release",
        )
    ]
