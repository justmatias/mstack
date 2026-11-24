from pathlib import Path


def create_backup_batch(parent: Path, timestamp: str) -> Path:
    batch = parent / ".mstack-backups" / timestamp
    batch.mkdir(parents=True)
    (batch / "item").write_bytes(b"content")
    return batch
