import tomllib
from collections import Counter

from tests.conftest import REPOSITORY_ROOT

MANIFEST = tomllib.loads((REPOSITORY_ROOT / "packs.toml").read_text(encoding="utf-8"))
CHECKS = REPOSITORY_ROOT / "lint" / "rules"


def test_every_check_is_in_one_pack_when_all_packs_are_listed():
    listed = Counter(
        check for pack in MANIFEST["packs"].values() for check in pack["checks"]
    )

    assert listed == Counter(path.stem for path in CHECKS.glob("*.yml"))
