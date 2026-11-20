# OpenMuse examples

Every example runs locally. Start with the approval demo, then pick the boundary you want to inspect.

| Example | What it shows | Credentials | Command |
|---|---|---|---|
| `openmuse-chat` | Browser chat with the agent; writes pause for exact-action approval in the page | None (optional model key) | `openmuse-chat --workspace .` |
| [`approval_app.py`](approval_app.py) | Local UI for inspecting and approving or denying one exact persisted action | None | `python examples/approval_app.py` |
| [`e2e_demo.py`](e2e_demo.py) | Exact-action approval, a durable task, and an HMAC-keyed hash-chained audit | None | `python examples/e2e_demo.py` |
| [`verify_audit.py`](verify_audit.py) | Independent verification of the demo's audit chain and executed action | None | `python examples/verify_audit.py` |
| [`isolated_worker_demo.py`](isolated_worker_demo.py) | A JSON job in a fresh, resource-limited process | None | `python examples/isolated_worker_demo.py` |
| [`memory_demo.py`](memory_demo.py) | Curated memory with provenance, search, verification, edit, and forget | None | `python examples/memory_demo.py` |
| [`scheduler_demo.py`](scheduler_demo.py) | A persisted cron job claimed atomically by one worker | None | `python examples/scheduler_demo.py` |
| [`typed_tool.py`](typed_tool.py) | Agent-registered typed tool with closed bounded arguments and read-only risk | None | `python examples/typed_tool.py` |
| [`local_planner.py`](local_planner.py) | The smallest deterministic planner loop | None | `python examples/local_planner.py` |

The Google Calendar and Gmail connectors need host-managed OAuth credentials. Their deterministic, credential-free boundary examples live in [`tests/test_google_calendar_connector.py`](../tests/test_google_calendar_connector.py), [`tests/test_google_mail_connector.py`](../tests/test_google_mail_connector.py), and [`tests/test_google_oauth.py`](../tests/test_google_oauth.py). Do not use sensitive production accounts while OpenMuse is alpha.

`approval_app.py` binds to localhost and is a reference demo, not a production approval surface. Production hosts must add TLS, authenticated identity, CSRF protection, and secure cookies.

## Review example output changes

The five credential-free approval, audit verification, memory, scheduler, and
isolated-worker walkthroughs have whole-output snapshots in `tests/snapshots/`.
The tests execute the current scripts in fresh temporary directories, then compare
their output with readable pytest diffs. They mask only the two displayed digest
prefixes and the worker process ID. Timestamps, temporary paths, and credentials
are not part of the expected output; unexpected new output is not filtered away.

Run the contracts after installing the development dependencies:

```bash
python -m pytest -q tests/test_example_snapshots.py
```

For an intentional wording or output change, regenerate and review every changed
snapshot before committing it:

```bash
OPENMUSE_UPDATE_SNAPSHOTS=1 python -m pytest -q tests/test_example_snapshots.py
git diff -- tests/snapshots/
python -m pytest -q tests/test_example_snapshots.py
```

The update command does not approve the changed output for you. Do not use it to
hide a regression. These tests need no live accounts and do not change the runtime
trust boundary. Worker execution retains the existing POSIX platform requirement.
