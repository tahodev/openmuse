"""Property-style tests for host-issued approval tokens."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from openmuse.approvals import ApprovalAuthority
from openmuse.models import Action


def approval_action(**overrides):
    arguments = {"path": "notes.txt", "content": "approved"}
    arguments.update(overrides.pop("arguments", {}))
    tool = overrides.pop("tool", "write_file")
    return Action(tool, arguments, **overrides)


def test_expired_approval_is_rejected(monkeypatch):
    now = 1_000
    monkeypatch.setattr("openmuse.approvals.time.time", lambda: now)
    authority = ApprovalAuthority(b"s" * 32)
    token = authority.issue(approval_action(), ttl_seconds=1)

    monkeypatch.setattr("openmuse.approvals.time.time", lambda: now + 2)

    assert authority.verify(approval_action(), token) is False


def test_approval_is_bound_to_exact_action():
    authority = ApprovalAuthority(b"s" * 32)
    action = approval_action()
    token = authority.issue(action)

    variants = [
        approval_action(arguments={"path": "other.txt", "content": "approved"}),
        approval_action(arguments={"path": "notes.txt", "content": "tampered"}),
        approval_action(tool="delete_file"),
        approval_action(id="different-action"),
    ]

    assert all(authority.verify(variant, token) is False for variant in variants)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda token: token[:-1],
        lambda token: "not-a-token",
        lambda token: token.replace(".", ".", 1) + ".extra",
        lambda token: "zz." + token.split(".", 1)[1],
        lambda token: token.split(".", 1)[0] + ".zzzz",
    ],
)
def test_malformed_or_tampered_tokens_fail_closed(mutate):
    authority = ApprovalAuthority(b"s" * 32)
    action = approval_action()
    token = authority.issue(action)

    assert authority.verify(action, mutate(token)) is False


def test_replay_is_rejected_even_for_identical_action():
    authority = ApprovalAuthority(b"s" * 32)
    action = approval_action()
    token = authority.issue(action)

    assert authority.verify(action, token) is True
    assert authority.verify(deepcopy(action), token) is False


def test_concurrent_verification_consumes_approval_once():
    authority = ApprovalAuthority(b"s" * 32)
    action = approval_action()
    token = authority.issue(action)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: authority.verify(action, token), range(32)))

    assert results.count(True) == 1
    assert results.count(False) == 31
