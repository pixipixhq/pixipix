from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "main-ci.yml"
ACTION_REFERENCE = re.compile(
    r"(?m)^\s*uses:\s+(?P<action>[^@\s]+)@(?P<sha>[0-9a-f]{40})\s+#\s+(?P<version>v\S+)\s*$"
)


def _top_level_block(text: str, name: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(name)}:\n(?P<body>.*?)(?=^\S|\Z)", text)
    assert match is not None, f"missing workflow block {name!r}"
    return match.group("body").strip()


def test_main_ci_only_accepts_main_branch_pushes() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert _top_level_block(text, "on") == "push:\n    branches: [main]"
    job = _top_level_block(text, "jobs")
    condition = re.search(r"(?ms)^    if: >-\n(?P<body>.*?)(?=^    \S)", job)
    assert condition is not None
    assert " ".join(condition.group("body").split()) == (
        "github.event_name == 'push' && "
        "github.ref_type == 'branch' && "
        "github.ref == 'refs/heads/main' && "
        "github.event.deleted == false"
    )


def test_main_ci_has_read_only_permissions_and_no_release_delegation() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert _top_level_block(text, "permissions") == "contents: read"
    assert len(re.findall(r"(?m)^\s*permissions:", text)) == 1
    assert "id-token" not in text
    assert "secrets." not in text
    assert re.search(r"(?m)^\s*(?:environment|password|username|api-token|token):", text) is None
    assert "write-all" not in text
    assert "publish.yml" not in text
    assert "gh workflow" not in text
    assert "workflow_dispatch" not in text
    assert "continue-on-error" not in text


def test_main_ci_uses_only_pinned_verification_actions() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    references = [
        (match.group("action"), match.group("sha"), match.group("version"))
        for match in ACTION_REFERENCE.finditer(text)
    ]

    assert len(references) == len(re.findall(r"(?m)^\s*uses:", text))
    assert references
    assert len(references) == 3
    assert set(references) == {
        ("actions/checkout", "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0", "v7.0.0"),
        ("actions/setup-python", "a309ff8b426b58ec0e2a45f0f869d46889d02405", "v6.2.0"),
        ("astral-sh/setup-uv", "11f9893b081a58869d3b5fccaea48c9e9e46f990", "v8.3.2"),
    }
    assert text.count("actions/checkout@") == 1
    assert "ref: ${{ github.sha }}" in text
    assert "persist-credentials: false" in text
    assert len(re.findall(r"(?m)^\s*ref:", text)) == 1
    assert len(re.findall(r"(?m)^\s*persist-credentials:", text)) == 1


def test_main_ci_is_one_linux_job_with_separate_latest_tip_concurrency() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    jobs = _top_level_block(text, "jobs")

    assert re.findall(r"(?m)^(?:  )?([\w-]+):$", jobs) == ["verify"]
    assert len(re.findall(r"(?m)^\s*runs-on:", jobs)) == 1
    assert "runs-on: ubuntu-latest" in jobs
    assert "strategy:" not in jobs
    assert "matrix" not in jobs
    assert "timeout-minutes: 30" in jobs
    assert _top_level_block(text, "concurrency") == (
        "group: main-ci-${{ github.ref }}\n  cancel-in-progress: true"
    )
    assert len(re.findall(r"(?m)^\s*concurrency:", text)) == 1


def test_main_ci_runs_the_agreed_portable_verification_contract() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert 'python-version: "3.12.12"' in text
    assert 'version: "0.11.29"' in text
    assert "fetch-depth: 0" in text
    assert re.findall(r"(?m)^\s*run: (.+)$", text) == [
        "uv sync --locked --all-groups --python 3.12.12",
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run mypy src tests",
        'uv run pytest -m "not canonical"',
    ]
    assert len(re.findall(r"(?m)^\s*run:", text)) == 5
    assert len(re.findall(r"(?m)^\s*if:", text)) == 1
    assert re.search(r"(?m)^\s*shell:", text) is None
