"""Hash-chained, append-only prediction ledger in SQLite (spec 3.4, 7.10, 4.7 tamper test).

Every entry stores: seq (contiguous from 1), ts (UTC ISO, non-decreasing), kind, the
payload as canonical JSON, prev_hash and hash, where
    hash = sha256(prev_hash || canonical_json({seq, ts, kind, payload})).
Kinds:
  prediction  sealed BEFORE its outcome exists in the ledger
  outcome     joined later; must reference an earlier sealed prediction
  root        daily root: sha256 over the ordered hashes of that UTC day's entries,
              appended once per day; publish it outside the ledger as an anchor
SQLite triggers refuse UPDATE and DELETE; the verifier is the real control and
catches edits, inserts, deletes, re-orders and back-dating even if the triggers are
dropped. Truncation of the newest entries is caught when an anchor (a published
daily root or head hash) is supplied.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field

GENESIS = "0" * 64

SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger (
    seq INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('prediction','outcome','root')),
    ref TEXT,
    payload TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS ledger_ref ON ledger(kind, ref);
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
"""


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def entry_hash(prev_hash: str, seq: int, ts: str, kind: str, payload: dict) -> str:
    body = canonical_json({"seq": seq, "ts": ts, "kind": kind, "payload": payload})
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


def day_root(hashes: list[str]) -> str:
    return hashlib.sha256("".join(hashes).encode()).hexdigest()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


class LedgerError(RuntimeError):
    pass


class Ledger:
    def __init__(self, path: str = ":memory:", clock=_now):
        self.con = sqlite3.connect(path, isolation_level=None)
        self.con.executescript(SCHEMA)
        self.clock = clock

    # ---------------------------------------------------------------- writing
    def _head(self):
        row = self.con.execute("SELECT seq, ts, hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()
        return row if row else (0, "", GENESIS)

    def head_hash(self) -> str:
        return self._head()[2]

    def _append(self, kind: str, ref: str | None, payload: dict) -> str:
        seq, last_ts, prev = self._head()
        ts = self.clock()
        if last_ts and ts < last_ts:
            raise LedgerError("clock went backwards")
        last_day = last_ts[:10]
        if kind != "root" and last_ts and ts[:10] > last_day and not self._has_root(last_day):
            self.close_day(last_day)  # seal the previous day before writing into a new one
            seq, last_ts, prev = self._head()
            ts = self.clock()
            if ts < last_ts:
                raise LedgerError("clock went backwards")
        h = entry_hash(prev, seq + 1, ts, kind, payload)
        self.con.execute(
            "INSERT INTO ledger(seq, ts, kind, ref, payload, prev_hash, hash) VALUES (?,?,?,?,?,?,?)",
            (seq + 1, ts, kind, ref, canonical_json(payload), prev, h))
        return h

    def _has_root(self, day: str) -> bool:
        return self.con.execute(
            "SELECT 1 FROM ledger WHERE kind='root' AND ref=?", (day,)).fetchone() is not None

    def seal_prediction(self, pred_id: str, payload: dict) -> str:
        if self.con.execute("SELECT 1 FROM ledger WHERE kind='prediction' AND ref=?",
                            (pred_id,)).fetchone():
            raise LedgerError(f"prediction {pred_id} already sealed")
        if self.con.execute("SELECT 1 FROM ledger WHERE kind='outcome' AND ref=?",
                            (pred_id,)).fetchone():
            raise LedgerError(f"outcome for {pred_id} already revealed; cannot seal after reveal")
        return self._append("prediction", pred_id, {"pred_id": pred_id, **payload})

    def join_outcome(self, pred_id: str, outcome: dict) -> str:
        if not self.con.execute("SELECT 1 FROM ledger WHERE kind='prediction' AND ref=?",
                                (pred_id,)).fetchone():
            raise LedgerError(f"no sealed prediction {pred_id}: outcome refused")
        if self.con.execute("SELECT 1 FROM ledger WHERE kind='outcome' AND ref=?",
                            (pred_id,)).fetchone():
            raise LedgerError(f"outcome for {pred_id} already joined")
        return self._append("outcome", pred_id, {"pred_id": pred_id, **outcome})

    def close_day(self, day: str | None = None) -> str:
        """Append the daily root for `day` (UTC YYYY-MM-DD; default: the head's day)."""
        day = day or self._head()[1][:10]
        if self._has_root(day):
            raise LedgerError(f"day {day} already closed")
        hashes = [r[0] for r in self.con.execute(
            "SELECT hash FROM ledger WHERE kind!='root' AND substr(ts,1,10)=? ORDER BY seq", (day,))]
        root = day_root(hashes)
        self._append("root", day, {"day": day, "n_entries": len(hashes), "root": root})
        return root

    def roots(self) -> dict[str, str]:
        return {json.loads(p)["day"]: json.loads(p)["root"] for (p,) in self.con.execute(
            "SELECT payload FROM ledger WHERE kind='root' ORDER BY seq")}

    # ---------------------------------------------------------------- reading
    def rows(self):
        return self.con.execute(
            "SELECT seq, ts, kind, ref, payload, prev_hash, hash FROM ledger ORDER BY seq").fetchall()

    def joined(self) -> list[dict]:
        """Predictions with their outcomes, only for outcomes joined after the seal."""
        preds, outs = {}, {}
        for seq, ts, kind, ref, payload, *_ in self.rows():
            if kind == "prediction":
                preds[ref] = (seq, json.loads(payload))
            elif kind == "outcome":
                outs[ref] = (seq, json.loads(payload))
        out = []
        for ref, (oseq, o) in outs.items():
            pseq, p = preds[ref]
            assert pseq < oseq
            out.append({"prediction": p, "outcome": o})
        return out


@dataclass
class VerifyResult:
    ok: bool
    problems: list[str] = field(default_factory=list)


def verify(con_or_ledger, anchors: dict[str, str] | None = None,
           expected_head: str | None = None) -> VerifyResult:
    """Recompute the chain. anchors: published {day: root}; expected_head: published head."""
    con = con_or_ledger.con if isinstance(con_or_ledger, Ledger) else con_or_ledger
    rows = con.execute(
        "SELECT seq, ts, kind, ref, payload, prev_hash, hash FROM ledger ORDER BY seq").fetchall()
    probs: list[str] = []
    prev, last_ts = GENESIS, ""
    sealed: dict[str, int] = {}
    revealed: set[str] = set()
    day_hashes: dict[str, list[str]] = {}
    roots: dict[str, str] = {}
    closed_days: set[str] = set()
    for i, (seq, ts, kind, ref, payload, prev_hash, h) in enumerate(rows, start=1):
        if seq != i:
            probs.append(f"seq gap or insert at position {i} (seq {seq})")
        if prev_hash != prev:
            probs.append(f"seq {seq}: prev_hash does not link to the previous entry")
        try:
            pl = json.loads(payload)
        except ValueError:
            probs.append(f"seq {seq}: payload is not JSON")
            pl = {}
        if canonical_json(pl) != payload:
            probs.append(f"seq {seq}: payload not in canonical form")
        if entry_hash(prev_hash, seq, ts, kind, pl) != h:
            probs.append(f"seq {seq}: hash mismatch (entry edited)")
        if ts < last_ts:
            probs.append(f"seq {seq}: timestamp earlier than the previous entry (back-dated)")
        day = ts[:10]
        if kind != "root" and day in closed_days:
            probs.append(f"seq {seq}: entry dated {day} after that day's root (back-dated)")
        if kind == "prediction":
            if ref in revealed:
                probs.append(f"seq {seq}: prediction {ref} sealed after its outcome")
            sealed[ref] = seq
        elif kind == "outcome":
            if ref not in sealed:
                probs.append(f"seq {seq}: outcome {ref} has no earlier sealed prediction")
            revealed.add(ref)
        if kind == "root":
            d = pl.get("day")
            want = day_root(day_hashes.get(d, []))
            if pl.get("root") != want or pl.get("n_entries") != len(day_hashes.get(d, [])):
                probs.append(f"seq {seq}: daily root for {d} does not match its entries")
            roots[d] = pl.get("root")
            closed_days.add(d)
        else:
            day_hashes.setdefault(day, []).append(h)
        prev, last_ts = h, max(last_ts, ts)
    for d, r in (anchors or {}).items():
        if roots.get(d) != r:
            probs.append(f"published root for {d} missing or different (truncated or rewritten)")
    if expected_head is not None and prev != expected_head:
        probs.append("head hash differs from the published head (truncated or extended)")
    return VerifyResult(ok=not probs, problems=probs)
