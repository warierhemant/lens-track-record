"""Track-record publication lines (package section 2.9; runbook gap G8).

`docs/track-record/README.md` holds one table row per published hash, each added by its own dated
commit, in run order. The first line of a Stage 9 run is the `package` line: the SHA-256 of the
signed package copy `research/accuracy/PREREG_PACKAGE_v<N>.md` (v1 for the first seal of
2026-10-23; v2 for the option A re-seal, package section 0c), published after Emily's sign-off and
before `seal-config`. A signed copy is never edited, so a re-seal signs the next number. The config
cannot carry the package hash (the package lists the config's values), so the package hash is
anchored twice: in this public line, and in the `stage9:FROZEN` ledger entry, because
`runner.seal_config` records `package_sha256` there and refuses a real holdout config unless the
package line is already published and the package is not one the text-only amendment lists as
superseded (`require_published`).

This module only reads files and formats rows. It writes nothing; the owner commits each line.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

TRACK_RECORD_REL = "docs/track-record/README.md"
V1_PACKAGE_NAME = "PREREG_PACKAGE_v1.md"
# a signed copy is PREREG_PACKAGE_v<N>.md, never the draft; a copy is never edited, so a re-seal
# (2026-10-23, option A: the first seal superseded before any paid call) signs the next number
SIGNED_PACKAGE = re.compile(r"PREREG_PACKAGE_v[1-9][0-9]*\.md")
# run order (README "Line types")
LINE_TYPES = ("package", "config", "predictions-head", "final-head", "stack-gate-prereg",
              "stack-gate-final-head")
_SHA = re.compile(r"\b[0-9a-f]{64}\b")


class PublicationError(RuntimeError):
    """A refusal: the hash is not published where the run needs it."""


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row(date: str, run: str, what: str, sha256: str) -> str:
    """One table row for the README, ready to paste (the commit column is filled after the commit)."""
    if what not in LINE_TYPES:
        raise PublicationError(f"unknown line type {what!r}; expected one of {', '.join(LINE_TYPES)}")
    if not _SHA.fullmatch(sha256):
        raise PublicationError("a published line carries a full 64-character lowercase SHA-256")
    return f"| {date} | {run} | {what} | `{sha256}` | |"


def published_lines(readme: Path) -> list[dict]:
    """The README's published rows as {date, run, what, sha256}; rows without a full hash are skipped."""
    out = []
    if not Path(readme).is_file():
        return out
    for line in Path(readme).read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[2] not in LINE_TYPES:
            continue
        m = _SHA.search(cells[3])
        if m:
            out.append({"date": cells[0], "run": cells[1], "what": cells[2], "sha256": m.group(0)})
    return out


def is_published(root, what: str, sha256: str) -> bool:
    return any(r["what"] == what and r["sha256"] == sha256
               for r in published_lines(Path(root) / TRACK_RECORD_REL))


def package_record(root, package) -> dict:
    """{package_path, package_sha256} for the FROZEN entry (path relative to root when inside it)."""
    p = Path(package)
    p = p if p.is_absolute() else Path(root) / p
    if not p.is_file():
        raise PublicationError(f"package {p} does not exist")
    try:
        rel = str(p.resolve().relative_to(Path(root).resolve()))
    except ValueError:
        rel = str(p)
    return {"package_path": rel, "package_sha256": sha256_file(p)}


AMEND_REL = "research/stage9/AMEND_text_only_precollection.json"   # = precollect.AMEND_REL


def superseded_package_hashes(root) -> set[str]:
    """Every 64-hex hash in the text-only amendment's `supersedes.package` (option A, 2026-10-23:
    the v1 package cd5c6a8c...cf78). An absent amendment or section lists none."""
    import json
    f = Path(root) / AMEND_REL
    if not f.is_file():
        return set()
    sup = (json.loads(f.read_text()).get("supersedes") or {}).get("package") or ""
    return set(_SHA.findall(str(sup)))


def require_published(root, package) -> dict:
    """The G8 gate for a real holdout config: the package must be a signed copy
    PREREG_PACKAGE_v<N>.md (never the draft), not a package the amendment lists as superseded, and
    its hash must already be a `package` line in docs/track-record/README.md."""
    rec = package_record(root, package)
    if not SIGNED_PACKAGE.fullmatch(Path(rec["package_path"]).name):
        raise PublicationError(f"the Stage 9 holdout config seals against a signed copy "
                               f"PREREG_PACKAGE_v<N>.md ({V1_PACKAGE_NAME}, then v2 ...), "
                               f"not {Path(rec['package_path']).name}")
    if rec["package_sha256"] in superseded_package_hashes(root):
        raise PublicationError(f"the package hash {rec['package_sha256']} belongs to a superseded seal (the "
                               f"text-only amendment's `supersedes`): seal against the current signed copy")
    if not is_published(root, "package", rec["package_sha256"]):
        raise PublicationError(f"the package hash {rec['package_sha256']} is not published: add a `package` line "
                               f"to {TRACK_RECORD_REL} in its own dated commit before seal-config (runbook G8)")
    return rec
