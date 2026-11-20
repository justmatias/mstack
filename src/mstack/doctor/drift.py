from mstack.doctor.model import SETUP_FIX, Context, Result
from mstack.install.manifest import (
    ManifestError,
    compute_status,
    load_manifest,
    manifest_path,
)


def check_drift(context: Context) -> list[Result]:
    """Only when the manifest exists: without it there is nothing to compare."""
    path = manifest_path()
    if context.checkout is None or not path.is_file():
        return []
    try:
        rows = compute_status(context.checkout, context.tool, load_manifest(path))
    except ManifestError as error:
        return [
            Result(group="drift", check="manifest", status="error", detail=str(error))
        ]
    drifted = [row for row in rows if row.state != "identical"]
    if not drifted:
        return [
            Result(
                group="drift",
                check="manifest",
                status="ok",
                detail=f"{len(rows)} items identical to the checkout",
            )
        ]
    return [
        Result(
            group="drift",
            check=f"{row.kind} {row.name}",
            status="warn",
            detail=f"{row.state} at {row.target} ({row.action})",
            fix=SETUP_FIX,
        )
        for row in drifted
    ]
