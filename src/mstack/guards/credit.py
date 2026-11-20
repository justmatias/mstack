import re

SHA = re.compile(r"^[0-9a-f]{40}$")


def credit_problems(frontmatter: dict) -> list[str]:
    """Problems with the upstream credit in a skill's or a rule's frontmatter.

    `license` and `metadata.adapted-from` go together, and every
    `adapted-from[-<label>]` has an `upstream-commit[-<label>]` set to a full sha.
    """
    metadata = frontmatter.get("metadata") or {}
    if not isinstance(metadata, dict):
        return ["'metadata' is not a mapping"]
    problems: list[str] = []
    if "license" in frontmatter and "adapted-from" not in metadata:
        problems.append("'license' without 'adapted-from'")
    if "adapted-from" in metadata and "license" not in frontmatter:
        problems.append("'adapted-from' without 'license'")
    for key in metadata:
        if not str(key).startswith("adapted-from"):
            continue
        commit_key = str(key).replace("adapted-from", "upstream-commit", 1)
        if not SHA.match(str(metadata.get(commit_key, ""))):
            problems.append(f"'{key}' needs a '{commit_key}' set to a 40-character sha")
    return problems
