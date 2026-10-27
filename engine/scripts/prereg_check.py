"""Stage 8.13 pre-registration check: recompute every recorded hash and compare.

Run on the Mac (the machine that holds the ledgers), from the repo root:

    python3 engine/scripts/prereg_check.py                 # human-readable report
    python3 engine/scripts/prereg_check.py --strict        # a missing ledger counts as FAIL
    python3 engine/scripts/prereg_check.py --json          # machine-readable report

What it reads. The fenced ```json prereg-manifest block in
research/accuracy/PREREG_PACKAGE_DRAFT.md lists every value the package freezes. For each entry:

  files      SHA-256 of the file's bytes (every PLAN.json, ANALYSIS_PLAN.json, CANDIDATES.json and
             other sealed inputs) must equal `expected_sha256`. If the entry names a sidecar
             (PLAN.sha256), its first token must match too. If the entry carries `resume`, that
             abbreviated value must still appear verbatim in RESUME.md and must abbreviate the
             expected hash.
  canonical  SHA-256 of canonical JSON (sorted keys, no spaces, as lens_engine.harness.ledger) of
             the object at `pointer` inside a JSON file (the grading plans demo-obf-v1 and
             customer-v1 are hashed this way when sealed).
  contains   the file must contain `text` (a seal embedded in a committed replay file).
  ledgers    the hash chain of a ledger.sqlite is recomputed from genesis (prev-hash links, entry
             hashes, canonical payloads) and the recorded hash (a head or entry hash, possibly
             abbreviated as abc123...def456) must be one of its entries, at or before which the
             chain is intact. Ledgers are not in git: a missing file is SKIP (FAIL with --strict).
  pending    a plan written as an unsealed DRAFT (no hash exists yet; the Mac seals it later). The
             file must exist and the entry must carry no hash. Reported as SKIP ("PENDING"), and as
             FAIL with --strict: the package cannot be sealed while a plan it lists is unsealed.
  holdout    only data/sealed/HOLDOUT_SHA256.txt is read and its first token compared with the
             recorded value. holdout_ids.txt is never opened.
  holdout_text_hashes
             the holdout text-fingerprint amendment: the amendment file and the tool must hash
             to the recorded values (both are in git). Until the tool has run, output_sha256 is
             null: SKIP ("PENDING"), FAIL with --strict. After it, the hash-only output file in
             data/sealed/manifests is hashed (SKIP where data/sealed is absent, FAIL --strict).

RESUME.md convention. A checksum that is not a pre-registration value (a downloaded data file,
say) is written in RESUME.md as `data-sha256 <hex>`; resume_hash_prefixes() skips it, so the test
that every hash RESUME.md records is in the manifest does not ask for it.

Standard library only, so it runs in any Python >= 3.10 with no engine venv. Exit code 0 when
nothing FAILs, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path("research/accuracy/PREREG_PACKAGE_DRAFT.md")
RESUME = Path("RESUME.md")
GENESIS = "0" * 64
MANIFEST_FENCE = re.compile(r"```json prereg-manifest\n(.*?)\n```", re.S)
HEX = re.compile(r"^[0-9a-f]+$")


@dataclass
class Check:
    section: str
    id: str
    status: str  # PASS, FAIL or SKIP
    detail: str


# ---------------------------------------------------------------- helpers
def canonical_json(obj) -> str:
    """Same as lens_engine.harness.ledger.canonical_json (kept here so the script needs no venv)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def entry_hash(prev_hash: str, seq: int, ts: str, kind: str, payload: dict) -> str:
    body = canonical_json({"seq": seq, "ts": ts, "kind": kind, "payload": payload})
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def split_abbrev(abbrev: str) -> tuple[str, str]:
    """'abc123...def' or 'abc123…def' -> ('abc123', 'def'); 'abc123' -> ('abc123', '')."""
    a = abbrev.strip().replace("…", "...")
    prefix, _, suffix = a.partition("...")
    for part in (prefix, suffix):
        if part and not HEX.match(part):
            raise ValueError(f"not a hex abbreviation: {abbrev!r}")
    if len(prefix) < 6:
        raise ValueError(f"abbreviation needs at least 6 leading hex characters: {abbrev!r}")
    return prefix, suffix


def matches(abbrev: str, full: str) -> bool:
    """True if `abbrev` (full hash, prefix, or prefix...suffix) abbreviates `full`."""
    prefix, suffix = split_abbrev(abbrev)
    return full.startswith(prefix) and full.endswith(suffix)


# `data-sha256 18491f45…`: a data-file checksum, not a prereg hash (see the module docstring)
DATA_SHA = re.compile(r"data-sha256[: ]\s*[0-9a-f]+(?:(?:…|\.\.\.)[0-9a-f]*)?")


def resume_hash_prefixes(text: str) -> set[str]:
    """The 8-hex-character hash prefixes RESUME.md records, minus data-sha256 checksums."""
    text = DATA_SHA.sub("", text)
    found = set(re.findall(r"(?<![0-9A-Za-z_])([0-9a-f]{8})(?=[^0-9A-Za-z_]|$)", text))
    found |= set(re.findall(r"(?<![0-9A-Za-z_])([0-9a-f]{8})(?=…|\.\.\.)", text))
    return found


def extract_manifest(text: str) -> dict:
    found = MANIFEST_FENCE.findall(text)
    if len(found) != 1:
        raise ValueError(f"expected exactly one ```json prereg-manifest block, found {len(found)}")
    return json.loads(found[0])


# ---------------------------------------------------------------- checks
def check_file(root: Path, e: dict, resume_text: str | None) -> list[Check]:
    p = root / e["path"]
    if not p.exists():
        return [Check("files", e["id"], "FAIL", f"missing: {e['path']}")]
    got = sha256_file(p)
    out = [Check("files", e["id"], "PASS" if got == e["expected_sha256"] else "FAIL",
                 f"{e['path']} sha256 {got}" + ("" if got == e["expected_sha256"]
                                                else f" != expected {e['expected_sha256']}"))]
    if e.get("sidecar"):
        sp = root / e["sidecar"]
        if not sp.exists():
            out.append(Check("files", e["id"] + ":sidecar", "FAIL", f"missing: {e['sidecar']}"))
        else:
            tok = sp.read_text().split()[0]
            ok = tok == e["expected_sha256"]
            out.append(Check("files", e["id"] + ":sidecar", "PASS" if ok else "FAIL",
                             f"{e['sidecar']} says {tok}"))
    if e.get("resume"):
        ab = e["resume"]
        ok_abbrev = matches(ab, e["expected_sha256"])
        in_resume = resume_text is not None and ab in resume_text
        if resume_text is None:
            st, why = "SKIP", "RESUME.md not found"
        else:
            st = "PASS" if ok_abbrev and in_resume else "FAIL"
            why = (f"RESUME.md records {ab}" + ("" if in_resume else " (NOT FOUND in RESUME.md)")
                   + ("" if ok_abbrev else " (does not abbreviate the expected hash)"))
        out.append(Check("files", e["id"] + ":resume", st, why))
    return out


def check_canonical(root: Path, e: dict) -> list[Check]:
    p = root / e["path"]
    if not p.exists():
        return [Check("canonical", e["id"], "FAIL", f"missing: {e['path']}")]
    obj = json.loads(p.read_text())
    for key in e["pointer"]:
        obj = obj[key]
    got = hashlib.sha256(canonical_json(obj).encode()).hexdigest()
    ok = got == e["expected_sha256"]
    return [Check("canonical", e["id"], "PASS" if ok else "FAIL",
                  f"{e['path']}:{'/'.join(e['pointer'])} canonical sha256 {got}"
                  + ("" if ok else f" != expected {e['expected_sha256']}"))]


def check_contains(root: Path, e: dict) -> list[Check]:
    p = root / e["path"]
    if not p.exists():
        return [Check("contains", e["id"], "FAIL", f"missing: {e['path']}")]
    ok = e["text"] in p.read_text()
    return [Check("contains", e["id"], "PASS" if ok else "FAIL",
                  f"{e['path']} {'contains' if ok else 'does NOT contain'} {e['text'][:80]}")]


def check_pending(root: Path, e: dict, strict: bool) -> list[Check]:
    if "expected_sha256" in e:
        return [Check("pending", e["id"], "FAIL", "a pending entry carries a hash: move it to files")]
    if not (root / e["path"]).exists():
        return [Check("pending", e["id"], "FAIL", f"missing: {e['path']}")]
    return [Check("pending", e["id"], "FAIL" if strict else "SKIP",
                  f"PENDING: {e['path']} is an unsealed draft, no hash recorded yet")]


def walk_ledger(path: Path) -> tuple[list[str], int | None, str]:
    """Recompute the chain. Returns (entry hashes in seq order, seq of first break or None, note)."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT seq, ts, kind, payload, prev_hash, hash FROM ledger ORDER BY seq").fetchall()
    finally:
        con.close()
    hashes: list[str] = []
    prev, last_ts = GENESIS, ""
    for i, (seq, ts, kind, payload, prev_hash, h) in enumerate(rows, start=1):
        why = None
        if seq != i:
            why = f"seq gap at position {i}"
        elif prev_hash != prev:
            why = "prev_hash does not link"
        elif ts < last_ts:
            why = "timestamp goes backwards"
        else:
            try:
                pl = json.loads(payload)
            except ValueError:
                pl, why = None, "payload is not JSON"
            if why is None and canonical_json(pl) != payload:
                why = "payload not canonical"
            if why is None and entry_hash(prev_hash, seq, ts, kind, pl) != h:
                why = "entry hash mismatch"
        if why:
            return hashes, seq, why
        hashes.append(h)
        prev, last_ts = h, ts
    return hashes, None, ""


def check_ledger(root: Path, e: dict, strict: bool) -> list[Check]:
    p = root / e["path"]
    if not p.exists():
        return [Check("ledgers", e["id"], "FAIL" if strict else "SKIP",
                      f"{e['path']} not on this machine (ledgers stay on the Mac)")]
    try:
        hashes, broken_at, why = walk_ledger(p)
    except sqlite3.Error as exc:
        return [Check("ledgers", e["id"], "FAIL", f"{e['path']}: cannot read ({exc})")]
    hits = [i for i, h in enumerate(hashes, start=1) if matches(e["recorded"], h)]
    head = hashes[-1] if hashes else GENESIS
    if len(hits) == 1:
        tail = (f"; chain breaks later at seq {broken_at} ({why})" if broken_at else
                f"; chain intact to head seq {len(hashes)} {head[:12]}...")
        st = "FAIL" if broken_at else "PASS"
        return [Check("ledgers", e["id"], st, f"{e['recorded']} = entry seq {hits[0]}{tail}")]
    if len(hits) > 1:
        return [Check("ledgers", e["id"], "FAIL", f"{e['recorded']} is ambiguous ({len(hits)} entries)")]
    if broken_at:
        return [Check("ledgers", e["id"], "FAIL",
                      f"chain breaks at seq {broken_at} ({why}) before {e['recorded']} was found")]
    return [Check("ledgers", e["id"], "FAIL",
                  f"{e['recorded']} is not an entry of {e['path']} (head seq {len(hashes)} {head[:12]}...)")]


def check_holdout(root: Path, e: dict, strict: bool) -> list[Check]:
    p = root / e["hash_file"]
    if not p.exists():
        return [Check("holdout", "holdout_hash", "FAIL" if strict else "SKIP",
                      f"{e['hash_file']} not on this machine")]
    tok = p.read_text().split()[0]
    ok = matches(e["recorded"], tok)
    return [Check("holdout", "holdout_hash", "PASS" if ok else "FAIL",
                  f"{e['hash_file']} = {tok[:12]}...{tok[-4:]} vs recorded {e['recorded']}")]


def check_holdout_text(root: Path, e: dict, strict: bool) -> list[Check]:
    out = []
    for key, path in (("amendment", e["amendment"]), ("tool", e["tool"])):
        p, want = root / path, e[f"{key}_sha256"]
        if not p.exists():
            out.append(Check("holdout_text", key, "FAIL", f"missing: {path}"))
            continue
        got = sha256_file(p)
        out.append(Check("holdout_text", key, "PASS" if got == want else "FAIL",
                         f"{path} sha256 {got}" + ("" if got == want else f" != expected {want}")))
    want, p = e.get("output_sha256"), root / e["output"]
    if want is None:
        out.append(Check("holdout_text", "output", "FAIL" if strict else "SKIP",
                         f"PENDING: {e['output']} not generated yet (tool not run)"))
    elif not p.exists():
        out.append(Check("holdout_text", "output", "FAIL" if strict else "SKIP",
                         f"{e['output']} not on this machine"))
    else:
        got = sha256_file(p)
        out.append(Check("holdout_text", "output", "PASS" if got == want else "FAIL",
                         f"{e['output']} sha256 {got}" + ("" if got == want else f" != {want}")))
    return out


def run(root: Path = ROOT, package: Path = PACKAGE, strict: bool = False) -> list[Check]:
    pkg = package if package.is_absolute() else root / package
    manifest = extract_manifest(pkg.read_text())
    rp = root / RESUME
    resume_text = rp.read_text() if rp.exists() else None
    out: list[Check] = []
    for e in manifest.get("files", []):
        out += check_file(root, e, resume_text)
    for e in manifest.get("canonical", []):
        out += check_canonical(root, e)
    for e in manifest.get("contains", []):
        out += check_contains(root, e)
    for e in manifest.get("pending", []):
        out += check_pending(root, e, strict)
    for e in manifest.get("ledgers", []):
        out += check_ledger(root, e, strict)
    if manifest.get("holdout"):
        out += check_holdout(root, manifest["holdout"], strict)
    if manifest.get("holdout_text_hashes"):
        out += check_holdout_text(root, manifest["holdout_text_hashes"], strict)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this checkout)")
    ap.add_argument("--package", type=Path, default=PACKAGE, help="package markdown file")
    ap.add_argument("--strict", action="store_true", help="missing ledgers / holdout hash = FAIL")
    ap.add_argument("--json", action="store_true", help="print a JSON report")
    a = ap.parse_args(argv)
    checks = run(a.root, a.package, a.strict)
    n = {s: sum(c.status == s for c in checks) for s in ("PASS", "FAIL", "SKIP")}
    if a.json:
        print(json.dumps({"counts": n, "checks": [asdict(c) for c in checks]}, indent=1))
    else:
        for c in checks:
            print(f"{c.status:4}  {c.section:9}  {c.id:28}  {c.detail}")
        print(f"\n{n['PASS']} pass, {n['FAIL']} fail, {n['SKIP']} skip")
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
