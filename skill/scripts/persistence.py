"""Local staging only; the agent publishes snapshots with host CopyArtifact.
Never invokes tools, hooks, network requests or durable writes from Python.
"""
import json
import os
import tempfile
from pathlib import Path

USER_ROOT = Path('/mnt/user-config')
DATA_REL = Path('data/cowork-roi-report')
# Hook subprocesses may have a different cwd; bind staging to this task workspace.
STAGING = Path('/mnt/workspace/working/cowork-roi-state')


def state_path(filename):
    """Prefer the published data namespace, then legacy read-only logs."""
    if Path(filename).name != filename:
        raise ValueError('state filename must be a basename')
    canonical = USER_ROOT / DATA_REL / filename
    legacy = USER_ROOT / '.claude' / filename
    return str(canonical if canonical.exists() or not legacy.exists() else legacy)


def scratch_path(filename):
    return str(STAGING / Path(filename).name)


def writable_path(path):
    """Reject mount writes, including symlinks, before creating any directories."""
    target = Path(path).resolve()
    if target == USER_ROOT or USER_ROOT in target.parents:
        raise ValueError('user mount is read-only; stage under working/ and publish with CopyArtifact(surface="user")')
    output = Path('/mnt/workspace/output')
    if target == output or output in target.parents:
        raise ValueError('output is a publish surface; stage under working/ instead')
    return target


def read_dict(path):
    """Absent is a first run; corrupt or unexpected data must not be overwritten."""
    if not Path(path).exists():
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError('state must be a JSON object')
    return data


def atomic_stage(path, data):
    target = writable_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=target.name + '.', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def upsert_log(source, destination, key, record):
    """Retain the source ledger and accumulate a session's pending local records.
    Single writer only: the agent must coordinate/rebase before publication.
    """
    writable_path(destination)
    data = read_dict(source)
    if Path(destination).exists() and Path(destination).resolve() != Path(source).resolve():
        data.update(read_dict(destination))
    data[key] = record
    atomic_stage(destination, data)
    return len(data)
