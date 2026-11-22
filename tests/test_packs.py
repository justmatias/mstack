from collections import Counter

from mstack.packs import load_manifest, load_packs, pack_root


def test_each_shared_rule_has_one_pack_when_all_packs_are_selected():
    root = pack_root()
    packs = load_packs(list(load_manifest(root)))
    expected = Counter((root / "rules").glob("*.mdc"))

    assert Counter(path for pack in packs for path in pack.rules) == expected


def test_each_shared_check_has_one_pack_when_all_packs_are_selected():
    root = pack_root()
    packs = load_packs(list(load_manifest(root)))
    expected = Counter((root / "lint" / "rules").glob("*.yml"))

    assert Counter(path for pack in packs for path in pack.checks) == expected
