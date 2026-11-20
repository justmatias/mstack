import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Write to a temporary file in the same folder, then rename it over the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}-", delete=False
    ) as temporary:
        temporary.write(text)
    try:
        os.replace(temporary.name, path)
    except OSError:
        Path(temporary.name).unlink(missing_ok=True)
        raise
