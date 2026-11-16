"""Exclusive artifact custody shared by producers and pytest readers.

The persistent lock file is never truncated or unlinked. Subprocess custody needs
both the metadata from ``lease.handoff().env`` and its ``pass_fds``; copied
environment variables alone cannot authorize entry. Closing a lease never calls
LOCK_UN: a child shares the parent's open file description, so unlocking it would
also unlock the parent. The OS releases custody after the last descriptor closes.
"""

from __future__ import annotations

import fcntl
import json
import os
import stat
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ARTIFACT_LEASE_ENV = "OPD_ARTIFACT_LEASE"
_LOCK_PATH = Path("output") / ".artifact.lock"
_HANDLE_FIELDS = {"version", "root", "root_device", "root_inode", "lock_device", "lock_inode", "fd"}


class ArtifactLeaseError(RuntimeError):
    """Artifact custody could not be established."""


class ArtifactLeaseBusy(ArtifactLeaseError):
    """Another open file description already holds artifact custody."""


class ArtifactLeaseCustodyError(ArtifactLeaseError):
    """A supplied handle does not identify real custody of this physical root."""


@dataclass(frozen=True)
class ArtifactLeaseHandoff:
    """Use both fields as subprocess keyword arguments while the lease is open."""

    env: dict[str, str]
    pass_fds: tuple[int, ...]


@dataclass
class _LeaseState:
    root: Path
    root_identity: tuple[int, int]
    lock_identity: tuple[int, int]
    fd: int
    pid: int
    entries: int = 1


_ACTIVE: dict[tuple[int, int, int], _LeaseState] = {}
_ACTIVE_GUARD = threading.RLock()


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _physical_root(project_root: Path | str) -> tuple[Path, tuple[int, int]]:
    try:
        root = Path(project_root).resolve(strict=True)
        info = root.stat()
    except OSError as exc:
        raise ArtifactLeaseCustodyError("artifact root is unavailable") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise ArtifactLeaseCustodyError("artifact root must be a directory")
    return root, _identity(info)


def _open_lock(root: Path, *, create: bool) -> int:
    flags = os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW
    if create:
        flags |= os.O_CREAT
    try:
        directory = root / "output"
        if create:
            directory.mkdir(exist_ok=True)
        if not stat.S_ISDIR(directory.lstat().st_mode):
            raise ArtifactLeaseCustodyError("artifact lock directory must not be a symlink")
        fd = os.open(root / _LOCK_PATH, flags, 0o600)
    except OSError as exc:
        raise ArtifactLeaseCustodyError("artifact lock file is unavailable or unsafe") from exc
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise ArtifactLeaseCustodyError("artifact lock must be an ordinary, unaliased file")
    return fd


def _check_binding(state: _LeaseState) -> None:
    try:
        valid = (
            state.pid == os.getpid()
            and state.root_identity == _identity(state.root.stat())
            and stat.S_ISDIR((state.root / "output").lstat().st_mode)
            and state.lock_identity == _identity((state.root / _LOCK_PATH).lstat())
            and state.lock_identity == _identity(os.fstat(state.fd))
        )
    except OSError as exc:
        raise ArtifactLeaseCustodyError("artifact lease binding is no longer available") from exc
    if not valid:
        raise ArtifactLeaseCustodyError("artifact lease physical root or lock inode changed")


def _validate_inherited(root: Path, root_identity: tuple[int, int], inherited: str) -> int:
    try:
        handle = json.loads(inherited)
    except (TypeError, ValueError) as exc:
        raise ArtifactLeaseCustodyError("invalid artifact lease handle metadata") from exc
    if not isinstance(handle, dict) or set(handle) != _HANDLE_FIELDS:
        raise ArtifactLeaseCustodyError("invalid artifact lease handle fields")
    numeric = ("version", "root_device", "root_inode", "lock_device", "lock_inode", "fd")
    if any(type(handle[key]) is not int for key in numeric) or handle["version"] != 1 or handle["fd"] < 0:
        raise ArtifactLeaseCustodyError("invalid artifact lease descriptor metadata")
    if handle["root"] != str(root) or (handle["root_device"], handle["root_inode"]) != root_identity:
        raise ArtifactLeaseCustodyError("inherited artifact lease belongs to a different physical root")

    fd = handle["fd"]
    try:
        info = os.fstat(fd)
        access = fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE
    except OSError as exc:
        raise ArtifactLeaseCustodyError("inherited artifact lease descriptor is not open") from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or access != os.O_RDWR
        or _identity(info) != (handle["lock_device"], handle["lock_inode"])
    ):
        raise ArtifactLeaseCustodyError("inherited artifact lease descriptor identity is invalid")

    probe = _open_lock(root, create=False)
    try:
        if _identity(os.fstat(probe)) != _identity(info):
            raise ArtifactLeaseCustodyError("inherited artifact lease lock inode does not match this root")
        # A separate description must fail even a shared lock: this proves that
        # exclusive custody already exists, rather than acquiring it from env.
        try:
            fcntl.flock(probe, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ArtifactLeaseCustodyError("inherited artifact lease descriptor is not exclusively locked")
        # Reaffirming EX succeeds only for the description that holds custody;
        # an unrelated open descriptor for the same inode cannot borrow it.
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ArtifactLeaseCustodyError("inherited descriptor does not hold artifact custody") from exc
    finally:
        os.close(probe)
    return fd


class ArtifactLease:
    """An active root lease; create it with :func:`artifact_lease`."""

    def __init__(self, state: _LeaseState):
        self._state = state
        self._closed = False

    @property
    def root(self) -> Path:
        return self._state.root

    def fileno(self) -> int:
        if self._closed:
            raise ArtifactLeaseCustodyError("artifact lease context has already exited")
        _check_binding(self._state)
        return self._state.fd

    def handoff(self) -> ArtifactLeaseHandoff:
        """Prepare explicit environment AND descriptor inheritance for a child."""
        fd = self.fileno()
        handle = {
            "version": 1,
            "root": str(self.root),
            "root_device": self._state.root_identity[0],
            "root_inode": self._state.root_identity[1],
            "lock_device": self._state.lock_identity[0],
            "lock_inode": self._state.lock_identity[1],
            "fd": fd,
        }
        inherited = json.dumps(handle, sort_keys=True, separators=(",", ":"))
        _validate_inherited(self.root, self._state.root_identity, inherited)
        env = os.environ.copy()
        env[ARTIFACT_LEASE_ENV] = inherited
        return ArtifactLeaseHandoff(env=env, pass_fds=(fd,))


@contextmanager
def artifact_lease(project_root: Path | str, *, inherited: str | None = None) -> Iterator[ArtifactLease]:
    """Enter nonblocking, process-reentrant exclusive artifact custody.

    ``inherited`` is explicit serialized handoff metadata, never a bypass token.
    A borrowed child duplicates and closes its own descriptor, without unlocking
    or closing the caller's descriptor. Physical aliases share one lease; distinct
    roots have independent locks. Hold this context across all shared reads/writes
    and across the lifetime of any subprocess to which custody is handed.
    """
    root, root_identity = _physical_root(project_root)
    pid = os.getpid()
    key = (pid, *root_identity)
    with _ACTIVE_GUARD:
        inherited_fd = None if inherited is None else _validate_inherited(root, root_identity, inherited)
        state = _ACTIVE.get(key)
        if state is not None:
            _check_binding(state)
            state.entries += 1
        else:
            fd = os.dup(inherited_fd) if inherited_fd is not None else _open_lock(root, create=True)
            try:
                if inherited_fd is None:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError as exc:
                        raise ArtifactLeaseBusy(f"artifact custody is already held for {root}") from exc
                state = _LeaseState(root, root_identity, _identity(os.fstat(fd)), fd, pid)
                _check_binding(state)
            except BaseException:
                os.close(fd)
                raise
            _ACTIVE[key] = state
    lease = ArtifactLease(state)
    try:
        yield lease
    finally:
        with _ACTIVE_GUARD:
            lease._closed = True
            state.entries -= 1
            if state.entries == 0:
                del _ACTIVE[key]
                os.close(state.fd)
