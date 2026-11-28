from pathlib import Path


def test_exceptions_pass_when_exception_is_justified(
    run_mstack, justified_exception_file: Path
):
    completed = run_mstack("exceptions", str(justified_exception_file))

    assert completed.returncode == 0, completed.stderr


def test_exceptions_fail_when_exception_is_unjustified(
    run_mstack, unjustified_exception: tuple[Path, str]
):
    path, problem = unjustified_exception

    completed = run_mstack("exceptions", str(path))

    assert completed.returncode == 1
    assert problem in completed.stderr


def test_exceptions_check_files_when_folder_is_given(run_mstack, exception_file):
    path = exception_file("")

    completed = run_mstack("exceptions", str(path.parent))

    assert completed.returncode == 1
    assert path.name in completed.stderr
