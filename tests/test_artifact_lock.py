"""Real OS-lock, inherited-descriptor and pre-collection custody regressions."""

from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

import pytest

from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, ArtifactLeaseCustodyError, artifact_lease

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROBE = """
import os
import sys
from orchestration.artifact_lock import (
    ARTIFACT_LEASE_ENV, ArtifactLeaseBusy, ArtifactLeaseError, artifact_lease,
)
try:
    with artifact_lease(sys.argv[1], inherited=os.environ.get(ARTIFACT_LEASE_ENV)):
        print('ACQUIRED', flush=True)
except ArtifactLeaseError as exc:
    print(type(exc).__name__ + ': ' + str(exc), flush=True)
    raise SystemExit(2 if isinstance(exc, ArtifactLeaseBusy) else 3)
"""
_HOLDER = """
import os
import sys
from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, artifact_lease
with artifact_lease(sys.argv[1], inherited=os.environ.get(ARTIFACT_LEASE_ENV)):
    print('LEASE_READY', flush=True)
    assert sys.stdin.readline().strip() == 'release'
"""


def _child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    result = dict(os.environ if env is None else env)
    if env is None:
        result.pop(ARTIFACT_LEASE_ENV, None)
    result.pop("PYTEST_ADDOPTS", None)
    result["PYTHONPATH"] = os.pathsep.join((str(PROJECT_ROOT / "src"), str(PROJECT_ROOT / "tests")))
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    result["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return result


def _probe(root: Path, *, env: dict[str, str] | None = None, pass_fds: tuple[int, ...] = ()):
    return subprocess.run(
        [sys.executable, "-B", "-c", _PROBE, str(root)],
        cwd=root,
        env=_child_env(env),
        pass_fds=pass_fds,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _await_ready(process: subprocess.Popen[str], marker: str) -> None:
    assert process.stdout is not None
    deadline = time.monotonic() + 30
    output = b""
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while marker.encode() not in output:
            remaining = deadline - time.monotonic()
            assert remaining > 0 and selector.select(remaining), output.decode(errors="replace")
            chunk = os.read(process.stdout.fileno(), 65536)
            assert chunk, output.decode(errors="replace")
            output += chunk


@contextmanager
def _running_reader(
    root: Path,
    argv: list[str],
    marker: str,
    *,
    env: dict[str, str] | None = None,
    pass_fds: tuple[int, ...] = (),
) -> Iterator[subprocess.Popen[str]]:
    process = subprocess.Popen(
        argv,
        cwd=root,
        env=_child_env(env),
        pass_fds=pass_fds,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _await_ready(process, marker)
        yield process
    finally:
        try:
            stdout, stderr = process.communicate("release\n", timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        assert process.returncode == 0, stdout + stderr


def _pytest_project(root: Path, *, wait_during_collection: bool = False) -> None:
    (root / "tests").mkdir()
    (root / "scripts").mkdir()
    (root / "docs" / "manuscript").mkdir(parents=True)
    (root / "output" / "data").mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / "conftest.py", root / "conftest.py")
    shutil.copyfile(PROJECT_ROOT / "scripts" / "run_full_chain.py", root / "scripts" / "run_full_chain.py")
    shutil.copyfile(PROJECT_ROOT / "docs" / "manuscript" / "config.yaml", root / "docs" / "manuscript" / "config.yaml")
    (root / "output" / "data" / "finite.json").write_text('{"observations": [0, 1, 2]}\n', encoding="utf-8")
    reader = """
import json
import sys
from pathlib import Path
payload = json.loads((Path(__file__).resolve().parents[1] / 'output/data/finite.json').read_text())
assert payload == {'observations': [0, 1, 2]}
"""
    if wait_during_collection:
        reader += "print('COLLECTION_READY', flush=True)\nassert sys.stdin.readline().strip() == 'release'\n"
    reader += "\ndef test_finite_artifact_reader():\n    assert sum(payload['observations']) == 3\n"
    (root / "tests" / "test_finite_reader.py").write_text(reader, encoding="utf-8")


def test_nested_physical_root_lease_does_not_deadlock_or_release_early(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with artifact_lease(root) as outer:
        with artifact_lease(alias) as inner:
            assert inner.root == outer.root == root.resolve()
            assert inner.fileno() == outer.fileno()
            assert _probe(root).returncode == 2
        assert _probe(root).returncode == 2
        with pytest.raises(ArtifactLeaseCustodyError, match="already exited"):
            inner.handoff()
    assert _probe(root).returncode == 0


def test_independent_physical_roots_do_not_contend(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with artifact_lease(first):
        assert _probe(first).returncode == 2
        assert _probe(second).returncode == 0


def test_explicit_inherited_child_succeeds_and_parent_stays_locked(tmp_path: Path) -> None:
    with artifact_lease(tmp_path) as parent:
        handoff = parent.handoff()
        child = _probe(tmp_path, env=handoff.env, pass_fds=handoff.pass_fds)
        assert child.returncode == 0, child.stdout + child.stderr
        assert child.stdout.strip() == "ACQUIRED"
        # A borrowed child's context exit and process exit must not LOCK_UN the
        # shared description, even though it successfully used the lease.
        assert _probe(tmp_path).returncode == 2
    assert _probe(tmp_path).returncode == 0


def test_parent_close_keeps_custody_until_inherited_child_finishes(tmp_path: Path) -> None:
    with ExitStack() as children:
        with artifact_lease(tmp_path) as parent:
            handoff = parent.handoff()
            children.enter_context(
                _running_reader(
                    tmp_path,
                    [sys.executable, "-B", "-c", _HOLDER, str(tmp_path)],
                    "LEASE_READY",
                    env=handoff.env,
                    pass_fds=handoff.pass_fds,
                )
            )
        # Parent has closed its descriptor, but a real inherited reference still
        # holds the same OS lock. Owner exit must also avoid explicit LOCK_UN.
        assert _probe(tmp_path).returncode == 2
    assert _probe(tmp_path).returncode == 0


def test_environment_without_inherited_descriptor_is_rejected(tmp_path: Path) -> None:
    with artifact_lease(tmp_path) as parent:
        child = _probe(tmp_path, env=parent.handoff().env)
        assert child.returncode == 3, child.stdout + child.stderr
        assert "ArtifactLeaseCustodyError" in child.stdout
        assert _probe(tmp_path).returncode == 2


@pytest.mark.parametrize("descriptor", [-1, 1000000])
def test_invalid_inherited_descriptor_is_rejected(tmp_path: Path, descriptor: int) -> None:
    with artifact_lease(tmp_path) as parent:
        handoff = parent.handoff()
        handle = json.loads(handoff.env[ARTIFACT_LEASE_ENV])
        handle["fd"] = descriptor
        env = {**handoff.env, ARTIFACT_LEASE_ENV: json.dumps(handle)}
        child = _probe(tmp_path, env=env, pass_fds=handoff.pass_fds)
        assert child.returncode == 3, child.stdout + child.stderr
        assert _probe(tmp_path).returncode == 2


def test_inherited_custody_cannot_authorize_a_different_root(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with artifact_lease(first) as parent:
        handoff = parent.handoff()
        child = _probe(second, env=handoff.env, pass_fds=handoff.pass_fds)
        assert child.returncode == 3, child.stdout + child.stderr
        assert "different physical root" in child.stdout
        assert not (second / "output").exists()
        assert _probe(first).returncode == 2


def test_forged_root_metadata_cannot_rebind_a_real_descriptor(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with artifact_lease(second):
        pass
    with artifact_lease(first) as parent:
        handoff = parent.handoff()
        handle = json.loads(handoff.env[ARTIFACT_LEASE_ENV])
        info = second.stat()
        handle.update(root=str(second.resolve()), root_device=info.st_dev, root_inode=info.st_ino)
        env = {**handoff.env, ARTIFACT_LEASE_ENV: json.dumps(handle)}
        child = _probe(second, env=env, pass_fds=handoff.pass_fds)
        assert child.returncode == 3, child.stdout + child.stderr
        assert "lock inode" in child.stdout
        assert _probe(first).returncode == 2


def test_same_inode_unrelated_open_description_cannot_borrow_custody(tmp_path: Path) -> None:
    with artifact_lease(tmp_path) as parent:
        handoff = parent.handoff()
        unrelated = os.open(tmp_path / "output" / ".artifact.lock", os.O_RDWR)
        try:
            handle = json.loads(handoff.env[ARTIFACT_LEASE_ENV])
            handle["fd"] = unrelated
            env = {**handoff.env, ARTIFACT_LEASE_ENV: json.dumps(handle)}
            child = _probe(tmp_path, env=env, pass_fds=(unrelated,))
            assert child.returncode == 3, child.stdout + child.stderr
            assert "does not hold artifact custody" in child.stdout
            assert _probe(tmp_path).returncode == 2
        finally:
            os.close(unrelated)


def test_unlocked_descriptor_and_metadata_cannot_create_borrowed_custody(tmp_path: Path) -> None:
    with artifact_lease(tmp_path) as parent:
        handoff = parent.handoff()
    unlocked = os.open(tmp_path / "output" / ".artifact.lock", os.O_RDWR)
    try:
        handle = json.loads(handoff.env[ARTIFACT_LEASE_ENV])
        handle["fd"] = unlocked
        env = {**handoff.env, ARTIFACT_LEASE_ENV: json.dumps(handle)}
        child = _probe(tmp_path, env=env, pass_fds=(unlocked,))
        assert child.returncode == 3, child.stdout + child.stderr
        assert "not exclusively locked" in child.stdout
    finally:
        os.close(unlocked)
    assert _probe(tmp_path).returncode == 0


def test_root_lock_symlink_is_rejected_without_touching_its_target(tmp_path: Path) -> None:
    target = tmp_path / "external.lock"
    target.write_bytes(b"preserve these bytes\n")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / ".artifact.lock").symlink_to(target)
    with pytest.raises(ArtifactLeaseCustodyError, match="unsafe"):
        with artifact_lease(tmp_path):
            pytest.fail("symlink lock unexpectedly admitted")
    assert target.read_bytes() == b"preserve these bytes\n"


@pytest.mark.parametrize("chain_args", [("--max-passes", "0"), ("--dry-run",)])
def test_relative_pytest_excludes_full_chain_before_artifact_mutation(
    tmp_path: Path, chain_args: tuple[str, ...]
) -> None:
    _pytest_project(tmp_path, wait_during_collection=True)
    finite = tmp_path / "output" / "data" / "finite.json"
    expected = finite.read_bytes()
    with _running_reader(
        tmp_path,
        [sys.executable, "-B", "-m", "pytest", "tests/test_finite_reader.py", "-q", "-s", "-p", "no:cacheprovider"],
        "COLLECTION_READY",
    ):
        # Neither relative pytest argv nor this historically trusted environment
        # flag may let an unrelated writer bypass actual OS custody.
        env = {**_child_env(), "PYTEST_CURRENT_TEST": "forged::test_owner (call)"}
        chain = subprocess.run(
            [sys.executable, "-B", "scripts/run_full_chain.py", *chain_args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert chain.returncode == 2, chain.stdout + chain.stderr
        assert "artifact custody is already held" in chain.stderr
        assert "exit " not in chain.stdout
        assert finite.read_bytes() == expected
        assert not (tmp_path / "output" / "reports").exists()
    assert _probe(tmp_path).returncode == 0


def test_writer_excludes_pytest_before_collection_or_bootstrap(tmp_path: Path) -> None:
    _pytest_project(tmp_path)
    entered = tmp_path / "collection-entered"
    (tmp_path / "tests" / "test_finite_reader.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(entered)!r}).write_text('collection was entered')\n"
        "def test_finite_values():\n    assert sum([0, 1, 2]) == 3\n",
        encoding="utf-8",
    )
    with artifact_lease(tmp_path):
        child = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "tests/test_finite_reader.py", "--collect-only", "-q"],
            cwd=tmp_path,
            env=_child_env(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert child.returncode == 4, child.stdout + child.stderr
        assert "cannot collect tests without artifact custody" in child.stderr
        assert not entered.exists()


def test_explicit_inherited_pytest_reads_real_finite_artifact(tmp_path: Path) -> None:
    _pytest_project(tmp_path)
    with artifact_lease(tmp_path) as parent:
        handoff = parent.handoff()
        child = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "tests/test_finite_reader.py", "-q", "-p", "no:cacheprovider"],
            cwd=tmp_path,
            env=_child_env(handoff.env),
            pass_fds=handoff.pass_fds,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert child.returncode == 0, child.stdout + child.stderr
        assert "1 passed" in child.stdout
        assert _probe(tmp_path).returncode == 2
    assert _probe(tmp_path).returncode == 0


@pytest.mark.parametrize("entrypoint", ["ensure_gate_artifacts", "refresh_generated_gate_artifacts"])
def test_bootstrap_entrypoints_refuse_without_custody_before_shared_access(tmp_path: Path, entrypoint: str) -> None:
    code = """
import sys
from pathlib import Path
from orchestration.artifact_lock import ArtifactLeaseBusy
import gate_support
try:
    getattr(gate_support, sys.argv[2])(Path(sys.argv[1]))
except ArtifactLeaseBusy:
    raise SystemExit(2)
raise SystemExit('bootstrap incorrectly admitted')
"""
    with artifact_lease(tmp_path):
        child = subprocess.run(
            [sys.executable, "-B", "-c", code, str(tmp_path), entrypoint],
            cwd=tmp_path,
            env=_child_env(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert child.returncode == 2, child.stdout + child.stderr
        assert sorted(path.name for path in (tmp_path / "output").iterdir()) == [".artifact.lock"]
