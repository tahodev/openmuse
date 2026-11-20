"""Whole-output contracts for the credential-free walkthroughs.

Run with OPENMUSE_UPDATE_SNAPSHOTS=1 only when intentionally reviewing output
changes. Each snapshot still comes from a fresh execution of the example.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = Path(__file__).with_name("snapshots")
EXAMPLES = (
    "e2e_demo",
    "verify_audit",
    pytest.param("memory_demo", marks=pytest.mark.skipif(os.name == "nt", reason="memory privacy needs POSIX")),
    "scheduler_demo",
    pytest.param(
        "isolated_worker_demo",
        marks=pytest.mark.skipif(sys.platform == "win32", reason="worker resource limits need POSIX"),
    ),
)


def normalize_output(name: str, output: str) -> str:
    """Mask only fields that are intentionally different between executions."""
    output = output.replace("\r\n", "\n")
    if name == "e2e_demo":
        output = re.sub(
            r"(?m)^(   action sha256: )[0-9a-f]{16}(\.\.\.)$",
            r"\1<DIGEST>\2",
            output,
        )
    elif name == "verify_audit":
        output = re.sub(
            r"(?m)^(VERIFIED: approved action == executed action \()[0-9a-f]{16}(\.\.\.\))$",
            r"\1<DIGEST>\2",
            output,
        )
    elif name == "isolated_worker_demo":
        result = json.loads(output)
        assert isinstance(result["child_pid"], int) and result["child_pid"] > 0
        result["child_pid"] = "<PID>"
        output = json.dumps(result, sort_keys=True) + "\n"
    return output


def run_example(name: str, work: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(work / "examples" / f"{name}.py")]
        + (["--auto-approve"] if name == "e2e_demo" else []),
        cwd=work,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not result.stderr, result.stderr
    return result.stdout


@pytest.mark.parametrize("name", EXAMPLES)
def test_example_output_snapshot(name, tmp_path):
    # Copy scripts, not output: all paths, temporary stores and worker files stay
    # in this test's directory rather than changing the checkout or another test.
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    if name == "verify_audit":
        run_example("e2e_demo", tmp_path)
    actual = normalize_output(name, run_example(name, tmp_path))
    snapshot = SNAPSHOTS / f"{name}.txt"
    if os.environ.get("OPENMUSE_UPDATE_SNAPSHOTS") == "1":
        snapshot.parent.mkdir(exist_ok=True)
        snapshot.write_text(actual, encoding="utf-8")
    assert actual == snapshot.read_text(encoding="utf-8")


def test_normalization_keeps_unexpected_output():
    output = "   action sha256: 0123456789abcdef...\nunexpected line\n"
    assert normalize_output("e2e_demo", output) == "   action sha256: <DIGEST>...\nunexpected line\n"
    assert normalize_output("memory_demo", "unexpected timestamp 2026-01-01\n") == "unexpected timestamp 2026-01-01\n"


def test_worker_normalization_keeps_payload_and_rejects_missing_process():
    output = '{"child_pid": 123, "message": "visible payload", "extra": true}\n'
    assert json.loads(normalize_output("isolated_worker_demo", output)) == {
        "child_pid": "<PID>", "message": "visible payload", "extra": True,
    }
    with pytest.raises(AssertionError):
        normalize_output("isolated_worker_demo", '{"child_pid": 0}\n')
