import subprocess

from mstack.doctor.model import Context, Result, install_fix


def check_source(context: Context) -> list[Result]:
    checkout = context.checkout
    if checkout is None or not checkout.is_dir():
        return [
            Result(
                group="source",
                check="checkout",
                status="error",
                detail=(
                    "the mstack checkout this CLI was installed from was not found"
                    + (f" ({checkout})" if checkout else "")
                ),
                fix=install_fix(context),
            )
        ]
    status = subprocess.run(
        ["git", "-C", str(checkout), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode != 0:
        return [
            Result(
                group="source",
                check="checkout",
                status="error",
                detail=f"{checkout} is not a git repository",
            )
        ]
    results = [
        Result(group="source", check="checkout", status="ok", detail=str(checkout))
    ]
    if status.stdout.strip():
        results.append(
            Result(
                group="source",
                check="uncommitted",
                status="warn",
                detail=f"{checkout} has uncommitted changes",
            )
        )
    return results
