import pytest

VALID_HEADER = (
    '# rule-exception: reason="third-party legacy API" expires=2999-12-31 '
    "approved-by=@reviewer\n"
)


def test_justified_exception_passes(run_script, exception_file):
    completed = run_script("check_exceptions.py", str(exception_file(VALID_HEADER)))

    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("header", "expected_problem"),
    [
        ("", "needs a '# rule-exception:'"),
        (
            '# rule-exception: reason="legacy" expires=2000-01-01 approved-by=@reviewer\n',
            "expired on 2000-01-01",
        ),
        (
            '# rule-exception: reason="legacy" expires=2999-12-31\n',
            "missing approved-by",
        ),
        (
            "# rule-exception: expires=2999-12-31 approved-by=@reviewer\n",
            "missing reason",
        ),
        (
            '# rule-exception: reason="legacy" expires=someday approved-by=@reviewer\n',
            "not a YYYY-MM-DD date",
        ),
    ],
    ids=["no-justification", "expired", "no-approval", "no-reason", "bad-date"],
)
def test_unjustified_exception_fails(
    run_script, exception_file, header: str, expected_problem: str
):
    completed = run_script("check_exceptions.py", str(exception_file(header)))

    assert completed.returncode == 1
    assert expected_problem in completed.stderr
