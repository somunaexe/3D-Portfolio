import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import check_setup  # noqa: E402

PY = sys.executable


@pytest.mark.parametrize(
    "code, expected",
    [
        (0xC0000005, "access violation"),
        (3221225477, "access violation"),                 # the same code as Python reports it on Windows
        (-1073741819, "access violation"),                # ...and as a signed number
        (0xC000001D, "illegal instruction"),
        (0xC0000135, "DLL was not found"),
        (-11, "signal 11"),                               # POSIX: killed by SIGSEGV
        (7, "exit code 7"),
    ],
)
def test_exit_codes_are_explained_in_words(code, expected):
    assert expected in check_setup.describe_exit(code)


def test_a_normal_success_is_ok():
    assert check_setup.run_isolated([PY, "-c", "print('fine')"], timeout=30) == ("ok", "fine")


def test_a_normal_python_error_is_reported_as_a_failure_with_its_message():
    status, text = check_setup.run_isolated([PY, "-c", "print('ValueError: nope'); raise SystemExit(1)"], timeout=30)
    assert (status, text) == ("fail", "ValueError: nope")


def test_a_hard_crash_is_reported_not_swallowed():
    """The case that made the old script silently stop: the process dies without any Python error."""
    status, text = check_setup.run_isolated([PY, "-c", "import os; os._exit(5)"], timeout=30)   # 5: portable, any code but 0/1
    assert status == "crash" and "exit code 5" in text


def test_a_hang_times_out():
    status, text = check_setup.run_isolated([PY, "-c", "import time; time.sleep(30)"], timeout=1)
    assert status == "timeout" and "1 seconds" in text


def test_a_crash_in_one_step_does_not_stop_the_steps_after_it(tmp_path):
    """Run the real script, with a step list where one step crashes: later steps must still report."""
    script = tmp_path / "run.py"
    script.write_text(
        "import os, sys\n"
        f"sys.path.insert(0, {str(Path(check_setup.ME).parent)!r})\n"
        "import check_setup\n"
        "check_setup.STEPS.clear()\n"
        "@check_setup.step('first step', 'hint1')\n"
        "def _(): return 'fine'\n"
        "@check_setup.step('crashing step', 'hint2')\n"
        "def _(): os._exit(5)\n"
        "@check_setup.step('last step', 'hint3')\n"
        "def _(): return 'still ran'\n"
        "if len(sys.argv) == 3 and sys.argv[1] == '--run': sys.exit(check_setup.run_child(int(sys.argv[2])))\n"
        "check_setup.ME = os.path.abspath(__file__)\n"
        "sys.exit(check_setup.main())\n"
    )
    import subprocess
    done = subprocess.run([PY, str(script)], capture_output=True, text=True, timeout=120)
    out = done.stdout
    assert "[OK  ] first step: fine" in out
    assert "[FAIL] crashing step: crashed: exit code 5" in out
    assert "[OK  ] last step: still ran" in out
    assert "Needs attention: crashing step" in out and done.returncode == 1


@pytest.mark.parametrize(
    "prefix, warns",
    [
        (r"C:\Users\ADMIN\anaconda3", True),
        (r"C:\Users\me\miniconda3\envs\x", True),
        ("/opt/conda", True),
        (r"C:\Users\ADMIN\AppData\Local\Programs\Python\Python312", False),
        ("/usr", False),
    ],
)
def test_it_warns_when_python_comes_from_conda(prefix, warns):
    assert (check_setup.conda_warning(prefix) is not None) is warns
