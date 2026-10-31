from __future__ import annotations

import hashlib
import io
import os
import subprocess
import tarfile
from pathlib import Path

import pytest

from tests.release import test_smoke_distribution as smoke


def _write_sdist(path: Path, lock: bytes, *, kind: str = "regular") -> None:
    with tarfile.open(path, "w:gz") as archive:
        if kind == "missing":
            return
        member = tarfile.TarInfo("pixipix-0.2.0/uv.lock")
        member.size = len(lock)
        if kind == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "/outside/uv.lock"
        elif kind == "hardlink":
            member.type = tarfile.LNKTYPE
            member.linkname = "pixipix-0.2.0/other"
        archive.addfile(member, io.BytesIO(lock))
        if kind == "duplicate":
            archive.addfile(member, io.BytesIO(lock))


@pytest.fixture
def candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for variable in os.environ:
        if variable.startswith("GIT_"):
            monkeypatch.delenv(variable)
    empty_git_directory = tmp_path / "empty-git-configuration"
    empty_git_directory.mkdir()
    for variable, value in {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TEMPLATE_DIR": str(empty_git_directory),
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(empty_git_directory),
        "GIT_CONFIG_KEY_1": "core.attributesFile",
        "GIT_CONFIG_VALUE_1": os.devnull,
    }.items():
        monkeypatch.setenv(variable, value)
    source = tmp_path / "source"
    source.mkdir()
    (source / "uv.lock").write_bytes(b"current candidate lock\n")
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    sdist = artifacts / "pixipix-0.2.0.tar.gz"
    _write_sdist(sdist, (source / "uv.lock").read_bytes())
    (artifacts / "pixipix-0.2.0-py3-none-any.whl").write_bytes(b"synthetic wheel")
    monkeypatch.setattr(smoke, "PROJECT_ROOT", source)
    for variable in (
        smoke.DEVELOPMENT_SOURCE_COMMIT_ENV,
        smoke.RELEASE_SOURCE_COMMIT_ENV,
        smoke.RELEASE_AUTHORITY_VERSION_ENV,
        smoke.EXTERNAL_RELEASE_CANDIDATE_ENV,
    ):
        monkeypatch.delenv(variable, raising=False)
    return sdist


def _commit_source() -> str:
    commands = (
        ["git", "init", "-q"],
        ["git", "add", "uv.lock"],
        [
            "git",
            "-c",
            "user.name=Synthetic Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "synthetic lock fixture",
        ],
    )
    for command in commands:
        subprocess.run(command, cwd=smoke.PROJECT_ROOT, check=True, capture_output=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=smoke.PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_temporary_source_ignores_caller_git_hooks_and_templates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    template = tmp_path / "caller-template"
    hooks = template / "hooks"
    hooks.mkdir(parents=True)
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 86\n", encoding="utf-8")
    hook.chmod(0o755)
    config = tmp_path / "caller-gitconfig"
    config.write_text(f'[core]\n hooksPath = "{hooks.as_posix()}"\n', encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_TEMPLATE_DIR", str(template))

    request.getfixturevalue("candidate")
    commit = _commit_source()

    assert len(commit) == 40
    assert not (smoke.PROJECT_ROOT / ".git" / "hooks" / "pre-commit").exists()


def test_local_development_candidate_records_actual_lock(candidate: Path) -> None:
    actual = smoke._development_candidate_lock_sha256(candidate)
    assert actual == hashlib.sha256(b"current candidate lock\n").hexdigest()


def test_external_development_candidate_binds_commit_checkout_and_sdist(
    candidate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = _commit_source()
    monkeypatch.setenv(smoke.EXTERNAL_RELEASE_CANDIDATE_ENV, str(candidate.parent))
    monkeypatch.setenv(smoke.DEVELOPMENT_SOURCE_COMMIT_ENV, commit)
    assert (
        smoke._development_candidate_lock_sha256(candidate)
        == hashlib.sha256(b"current candidate lock\n").hexdigest()
    )


def test_external_development_candidate_requires_source_commit(
    candidate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(smoke.EXTERNAL_RELEASE_CANDIDATE_ENV, str(candidate.parent))
    with pytest.raises(AssertionError, match="required for an external development candidate"):
        smoke._development_candidate_lock_sha256(candidate)


@pytest.mark.parametrize("commit", ["", "HEAD", "a" * 39, "A" * 40])
def test_development_source_commit_must_be_an_exact_identity(
    candidate: Path, monkeypatch: pytest.MonkeyPatch, commit: str
) -> None:
    monkeypatch.setenv(smoke.DEVELOPMENT_SOURCE_COMMIT_ENV, commit)
    with pytest.raises(AssertionError, match="full lowercase commit SHA"):
        smoke._development_candidate_lock_sha256(candidate)


def test_development_source_rejects_another_checkout(
    candidate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous_commit = _commit_source()
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Synthetic Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-qm",
            "another source commit with the same lock",
        ],
        cwd=smoke.PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv(smoke.DEVELOPMENT_SOURCE_COMMIT_ENV, previous_commit)
    with pytest.raises(AssertionError, match="checkout must match the candidate source commit"):
        smoke._development_candidate_lock_sha256(candidate)


def test_development_source_rejects_uncommitted_lock_drift(
    candidate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(smoke.DEVELOPMENT_SOURCE_COMMIT_ENV, _commit_source())
    (smoke.PROJECT_ROOT / "uv.lock").write_bytes(b"different checkout lock\n")
    _write_sdist(candidate, b"different checkout lock\n")
    with pytest.raises(
        AssertionError, match="checkout lock must match the candidate source commit"
    ):
        smoke._development_candidate_lock_sha256(candidate)


def test_development_sdist_rejects_another_lock(candidate: Path) -> None:
    _write_sdist(candidate, b"different artifact lock\n")
    with pytest.raises(AssertionError, match="sdist lock must match the checkout lock"):
        smoke._development_candidate_lock_sha256(candidate)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "symlink", "hardlink"])
def test_development_sdist_requires_one_regular_lock(candidate: Path, kind: str) -> None:
    _write_sdist(candidate, b"current candidate lock\n", kind=kind)
    with pytest.raises(AssertionError, match=r"exactly one regular uv\.lock"):
        smoke._development_candidate_lock_sha256(candidate)


@pytest.mark.parametrize(
    "variable", [smoke.RELEASE_SOURCE_COMMIT_ENV, smoke.RELEASE_AUTHORITY_VERSION_ENV]
)
def test_development_refuses_mixed_release_identity(
    candidate: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv(variable, "")
    with pytest.raises(AssertionError, match="development qualification must not select a release"):
        smoke._development_candidate_lock_sha256(candidate)
