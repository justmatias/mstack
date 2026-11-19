import argparse
import datetime
import io
import json
import re
import shlex
import subprocess
import sys
import tokenize
from pathlib import Path

IGNORE_COMMENT = re.compile(r"^#\s*ast-grep-ignore\b(?::\s*(?P<rule_ids>.*))?$")
EXCEPTION_COMMENT = re.compile(r"^#\s*rule-exception:\s*(?P<fields>.*)$")
REQUIRED_FIELDS = ("reason", "expires", "approved-by")


def python_files(paths: list[Path]) -> list[Path]:
    if not paths:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        return [Path(name) for name in listed if Path(name).is_file()]
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return files


def comments_by_line(source: str) -> dict[int, str]:
    comments: dict[int, str] = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                comments[token.start[0]] = token.string.strip()
    except (tokenize.TokenError, SyntaxError):
        pass
    return comments


def parse_exception_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in shlex.split(text):
        key, separator, value = part.partition("=")
        if separator:
            fields[key] = value
    return fields


def validate_exception_fields(
    location: str, fields_text: str, today: datetime.date
) -> tuple[dict[str, str], str | None]:
    try:
        fields = parse_exception_fields(fields_text)
    except ValueError as error:
        return {}, f"{location}: malformed rule-exception ({error})"
    missing = [field for field in REQUIRED_FIELDS if not fields.get(field)]
    if missing:
        return fields, f"{location}: rule-exception is missing {', '.join(missing)}"
    try:
        expires = datetime.date.fromisoformat(fields["expires"])
    except ValueError:
        return fields, (
            f"{location}: expires={fields['expires']} is not a YYYY-MM-DD date"
        )
    if expires < today:
        return fields, f"{location}: rule-exception expired on {expires}"
    if not fields["approved-by"].startswith("@"):
        return fields, f"{location}: approved-by must be a @handle"
    return fields, None


def ignored_rule_ids(rule_ids_text: str | None) -> list[str]:
    return [
        rule_id.strip()
        for rule_id in (rule_ids_text or "").split(",")
        if rule_id.strip()
    ]


def missing_exception_problem(location: str, line: str) -> str:
    is_trailing = not line.lstrip().startswith("#")
    where = "the line above the code" if is_trailing else "the line directly above"
    return f"{location}: 'ast-grep-ignore' needs a '# rule-exception:' on {where}"


def file_exceptions(path: Path, today: datetime.date) -> tuple[list[dict], list[str]]:
    exceptions: list[dict] = []
    problems: list[str] = []
    source = path.read_text(encoding="utf-8")
    comments = comments_by_line(source)
    lines = source.splitlines()
    for line_number, comment in sorted(comments.items()):
        ignore = IGNORE_COMMENT.match(comment)
        if not ignore:
            continue
        location = f"{path}:{line_number}"
        rule_ids = ignored_rule_ids(ignore["rule_ids"])
        if not rule_ids:
            problems.append(
                f"{location}: 'ast-grep-ignore' must name the rule ids it suppresses"
            )
        exception = EXCEPTION_COMMENT.match(comments.get(line_number - 1, ""))
        if not exception:
            problems.append(missing_exception_problem(location, lines[line_number - 1]))
            continue
        fields, problem = validate_exception_fields(
            f"{path}:{line_number - 1}", exception["fields"], today
        )
        if problem:
            problems.append(problem)
            continue
        exceptions.extend(
            {
                "rule": rule_id,
                "file": str(path),
                "line": line_number,
                "reason": fields["reason"],
                "expires": fields["expires"],
                "approved_by": fields["approved-by"],
            }
            for rule_id in rule_ids
        )
    return exceptions, problems


def collect_exceptions(
    files: list[Path], today: datetime.date
) -> tuple[list[dict], list[str]]:
    exceptions: list[dict] = []
    problems: list[str] = []
    for path in files:
        found, invalid = file_exceptions(path, today)
        exceptions.extend(found)
        problems.extend(invalid)
    return exceptions, problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Every ast-grep-ignore must carry a rule-exception with reason, "
            "expiry and approval."
        )
    )
    parser.add_argument(
        "paths", nargs="*", type=Path, help="Files or folders (default: git files)."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print active exceptions as JSON."
    )
    parser.add_argument(
        "--today", type=datetime.date.fromisoformat, default=datetime.date.today()
    )
    arguments = parser.parse_args()

    exceptions, problems = collect_exceptions(
        python_files(arguments.paths), arguments.today
    )
    if arguments.json:
        print(json.dumps({"exceptions": exceptions, "problems": problems}, indent=2))
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems and not arguments.json:
        print(f"check_exceptions: OK ({len(exceptions)} active exceptions)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
