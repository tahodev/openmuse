import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = Path(__file__).parent / "snapshots"


def run_example(name: str, *arguments: str, cwd: Path) -> str:
    completed = subprocess.run(
        [sys.executable, ROOT / "examples" / name, *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def normalized_example_outputs(tmp_path: Path) -> dict[str, str]:
    demo_workspace = tmp_path / "approval-demo"
    demo = run_example("e2e_demo.py", "--auto-approve", "--workspace", str(demo_workspace), cwd=tmp_path)
    verifier = run_example("verify_audit.py", str(demo_workspace / "audit.jsonl"), cwd=tmp_path)
    memory = run_example("memory_demo.py", cwd=tmp_path)
    scheduler = run_example("scheduler_demo.py", cwd=tmp_path)
    worker = run_example("isolated_worker_demo.py", "--workspace", str(tmp_path / "worker"), cwd=tmp_path)

    demo = re.sub(r"(?<=sha256: )[0-9a-f]{16}(?=\.\.\.)", "<ACTION_HASH>", demo)
    verifier = re.sub(r"(?<=sha256: )[0-9a-f]{16}(?=\.\.\.)", "<ACTION_HASH>", verifier)
    verifier = re.sub(r"\([0-9a-f]{16}\.\.\.\)", "(<ACTION_HASH>...)", verifier)
    demo = demo.replace("path: plan.md", "path: <PATH>")
    demo = demo.replace("Audit proof saved: .openmuse-demo/audit.jsonl", "Audit proof saved: <PATH>")
    worker_output = json.loads(worker)
    worker_output["child_pid"] = "<PID>"
    worker_output["cwd_name"] = "<WORKSPACE>"
    worker = json.dumps(worker_output, sort_keys=True) + "\n"

    return {
        "approval.txt": demo,
        "audit-verification.txt": verifier,
        "memory.txt": memory,
        "scheduler.txt": scheduler,
        "isolated-worker.json": worker,
    }


def test_credential_free_example_output_matches_snapshots(tmp_path, request):
    update_snapshots = request.config.getoption("--update-example-snapshots")
    for name, actual in normalized_example_outputs(tmp_path).items():
        snapshot = SNAPSHOTS / name
        if update_snapshots:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(actual, encoding="utf-8")
            continue

        assert snapshot.is_file(), f"Missing snapshot {snapshot}; run pytest with --update-example-snapshots"
        assert actual == snapshot.read_text(encoding="utf-8"), f"Example output changed: {snapshot.name}"
