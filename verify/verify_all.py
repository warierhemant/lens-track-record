"""Check the Lens Stage 9 sealed result end to end, from the files in this repository.

Run from the repository root, with numpy and scipy installed (verify/requirements.txt):

    python3 verify/verify_all.py                    # every check, about 6 minutes
    python3 verify/verify_all.py --skip-analysis    # every check except the full re-run

It prints one line per check and ends with a count. Exit code 0 means every check passed.
It writes nothing inside the repository. The re-run's output goes to a temporary folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

HASHES = ROOT / "docs/track-record/HASHES.md"
SUBSET = ROOT / "verify/PREREG_PUBLIC_SUBSET.md"
LARGE = ROOT / "verify/LARGE_FILES.sha256"
PKG = {"stage9-holdout-v1": "research/accuracy/PREREG_PACKAGE_v1.md",
       "stage9-holdout-v2": "research/accuracy/PREREG_PACKAGE_v2.md"}
CONFIG = {"stage9-holdout-v1": "engine/experiments/stage9/_archive/2026-10-23_first_seal/FROZEN_CONFIG_v1.json",
          "stage9-holdout-v2": "engine/experiments/stage9/FROZEN_CONFIG.json"}
LEDGER = {"stage9-holdout-v1": "engine/experiments/stage9/_archive/2026-10-23_first_seal/stage9_ledger.sqlite",
          "stage9-holdout-v2": "engine/experiments/stage9/ledger.sqlite",
          "stack-gate": "engine/experiments/stack_gate/ledger.sqlite",
          "stack-gate refit_nf4r": "engine/experiments/stack_gate/refit_nf4r/ledger.sqlite",
          "stage9 gpu pass": "engine/experiments/stage9/gpu_pass/ledger.sqlite",
          "stage9-f1-openai-addendum": "engine/experiments/stage9/f1_openai/ledger.sqlite"}
PREREG_FILE = {"stage9-f1-openai-addendum": "research/stage9/F1_OPENAI_ADDENDUM_PREREG.md"}
RESULTS_FILE = {"stage9-f1-openai-addendum": "research/stage9/results_f1_openai.json"}
ARXIV399 = {"arxiv399-prereg": "research/stage9/ARXIV399_PREREG.md",
            "arxiv399-prereg-head": "engine/experiments/stage9/arxiv399/ledger.sqlite"}
MIROFISH = {"mirofish-prereg": "research/stage9/MIROFISH_PREREG.md",
            "mirofish-prereg-head": "engine/experiments/stage9/mirofish/ledger.sqlite"}
RESULTS = "research/stage9/results.json"
REPORT = "research/stage9/REPORT.md"
ADDENDUM = "research/stage9/REPORT_F1_ADDENDUM.md"
RESULTS_SHA = "d6c863ba520661b29e95804b696f29037b61702b2440d033267697b6ee6b9d6e"  # from the addendum
FENCE = re.compile(r"```json prereg-manifest\n(.*?)\n```", re.S)

passed: list[str] = []
failed: list[str] = []


def check(ok: bool, what: str) -> bool:
    (passed if ok else failed).append(what)
    print(f"{'PASS' if ok else 'FAIL'}  {what}")
    return ok


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ro(path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{ROOT / path}?mode=ro", uri=True)


def hash_rows() -> list[dict]:
    rows = []
    for line in HASHES.read_text().splitlines():
        m = re.match(r"\|\s*(\d{4}-\d\d-\d\d \d\d:\d\d)\s*\|\s*([^|]+?)\s*\|\s*([a-z0-9-]+)\s*\|"
                     r"\s*`([0-9a-f]{64})`\s*\|", line)
        if m:
            rows.append({"date": m[1], "run": m[2], "type": m[3], "sha": m[4]})
    return rows


def step0_files() -> None:
    print("\n0. Every large ledger is present and is the exact file that was published")
    for line in LARGE.read_text().splitlines():
        if not line.strip():
            continue
        want, rel = line.split(maxsplit=1)
        p = ROOT / rel
        if not p.exists():
            check(False, f"{rel} is missing (download it from the release, see README step 2)")
            continue
        check(sha256(p) == want, f"{rel} sha256 {want[:12]}...")
    s4 = json.loads((ROOT / "engine/experiments/stack_gate/refit_nf4r/s4_extended.json").read_text())
    refit = ROOT / LEDGER["stack-gate refit_nf4r"]
    check(refit.exists() and sha256(refit) == s4["ledger_sha256"],
          "the refit ledger's sha256 equals ledger_sha256 in the sealed s4_extended.json")


def step1_published_hashes() -> None:
    print("\n1. Every published hash matches the file or ledger entry it names")
    rows = hash_rows()
    check(len(rows) >= 12, f"{len(rows)} published lines read from docs/track-record/HASHES.md")
    for r in rows:
        run, typ, want = r["run"], r["type"], r["sha"]
        label = f"{r['date']} {run} {typ} {want[:12]}..."
        if typ == "package":
            check(sha256(ROOT / PKG[run]) == want, f"{label} = sha256 of {PKG[run]}")
        elif typ == "f1-openai-prereg":
            check(sha256(ROOT / PREREG_FILE[run]) == want, f"{label} = sha256 of {PREREG_FILE[run]}")
        elif typ == "f1-openai-prereg-head":
            con = ro(LEDGER[run])
            row = con.execute("SELECT hash, ref, payload FROM ledger WHERE seq = 1").fetchone()
            con.close()
            check(bool(row) and row[0] == want and row[1] == "f1oa:PREREG"
                  and json.loads(row[2]).get("prereg_sha256") == sha256(ROOT / PREREG_FILE[run]),
                  f"{label} is entry 1 (f1oa:PREREG) of {LEDGER[run]} and seals {PREREG_FILE[run]}")
        elif typ == "f1-openai-final-head":
            con = ro(LEDGER[run])
            row = con.execute("SELECT hash, ref, payload FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()
            con.close()
            check(bool(row) and row[0] == want and row[1] == "f1oa:RESULTS"
                  and json.loads(row[2]).get("results_sha256") == sha256(ROOT / RESULTS_FILE[run]),
                  f"{label} is the last entry (f1oa:RESULTS) of {LEDGER[run]} and seals {RESULTS_FILE[run]}")
        elif typ == "config":
            check(sha256(ROOT / CONFIG[run]) == want, f"{label} = sha256 of {CONFIG[run]}")
        elif typ in ("predictions-head", "final-head", "stack-gate-prereg", "stack-gate-final-head"):
            path = LEDGER[run if run in LEDGER else "stack-gate"]
            if not (ROOT / path).exists():
                check(False, f"{label}: {path} is missing")
                continue
            con = ro(path)
            hit = con.execute("SELECT seq, ref FROM ledger WHERE hash = ?", (want,)).fetchone()
            last = con.execute("SELECT max(seq) FROM ledger").fetchone()[0]
            con.close()
            if typ == "predictions-head":
                check(bool(hit) and hit[1] == "stage9:PREDICTIONS",
                      f"{label} is entry {hit[0] if hit else '?'} of {path}, the sealed predictions manifest")
            elif typ == "stack-gate-prereg":
                check(bool(hit) and hit[0] == 1, f"{label} is entry 1 of {path}")
            else:
                check(bool(hit) and hit[0] == last, f"{label} is the last entry (head) of {path}")
        elif typ in ("arxiv399-prereg", "arxiv399-prereg-head"):
            f = ROOT / ARXIV399[typ]
            if f.exists():
                if typ == "arxiv399-prereg":
                    check(sha256(f) == want, f"{label} = sha256 of {ARXIV399[typ]}")
                else:
                    con = ro(ARXIV399[typ])
                    row = con.execute("SELECT hash, ref FROM ledger WHERE seq = 1").fetchone()
                    con.close()
                    check(bool(row) and row[0] == want and row[1] == "ax399:PREREG",
                          f"{label} is entry 1 (ax399:PREREG) of {ARXIV399[typ]}")
            else:
                print(f"NOTE  {label}: hash only for now, {ARXIV399[typ]} is published with the results")
        elif typ in ("mirofish-prereg", "mirofish-prereg-head"):
            f = ROOT / MIROFISH[typ]
            if f.exists():
                if typ == "mirofish-prereg":
                    check(sha256(f) == want, f"{label} = sha256 of {MIROFISH[typ]}")
                else:
                    con = ro(MIROFISH[typ])
                    row = con.execute("SELECT hash, ref FROM ledger WHERE seq = 1").fetchone()
                    con.close()
                    check(bool(row) and row[0] == want and row[1] == "mirofish:PREREG",
                          f"{label} is entry 1 (mirofish:PREREG) of {MIROFISH[typ]}")
            else:
                print(f"NOTE  {label}: hash only for now, {MIROFISH[typ]} is published with the results")
        else:
            check(False, f"{label}: unknown line type")


def step2_order() -> None:
    print("\n2. The config and package were sealed first, and every prediction before any outcome")
    for run in ("stage9-holdout-v1", "stage9-holdout-v2"):
        con = ro(LEDGER[run])
        first = con.execute("SELECT seq, ref, payload FROM ledger ORDER BY seq LIMIT 1").fetchone()
        pl = json.loads(first[2])
        check(first[1] == "stage9:FROZEN" and pl["config_sha256"] == sha256(ROOT / CONFIG[run])
              and pl["package_sha256"] == sha256(ROOT / PKG[run]) and pl["config_id"] == run,
              f"{run}: entry 1 is stage9:FROZEN and records this config's and this package's sha256")
        if run.endswith("v2"):
            man = con.execute("SELECT seq FROM ledger WHERE ref = 'stage9:PREDICTIONS'").fetchone()[0]
            last_pred = con.execute("SELECT max(seq) FROM ledger WHERE kind = 'prediction'").fetchone()[0]
            first_out = con.execute("SELECT min(seq) FROM ledger WHERE kind = 'outcome'").fetchone()[0]
            n = con.execute("SELECT kind, count(*) FROM ledger GROUP BY kind").fetchall()
            check(last_pred == man and first_out == man + 1,
                  f"{run}: the predictions manifest is entry {man}, the last prediction. "
                  f"The first outcome is entry {first_out}. Counts {dict(n)}")
            gp = json.loads(con.execute("SELECT payload FROM ledger WHERE seq = ?", (man,)).fetchone()[0])["gpu_pass_head"]
            g = ro(LEDGER["stage9 gpu pass"])
            ghead = g.execute("SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()[0]
            g.close()
            check(gp == ghead, f"{run}: the manifest's gpu_pass_head {gp[:12]}... is the head of "
                               f"{LEDGER['stage9 gpu pass']}")
        con.close()


def step3_prereg() -> None:
    print("\n3. The pre-registration check passes on the published subset of the v2 manifest")
    full = json.loads(FENCE.findall((ROOT / PKG["stage9-holdout-v2"]).read_text())[0])
    sub = json.loads(FENCE.findall(SUBSET.read_text())[0])
    for sec in ("files", "ledgers"):
        ok = all(e in full[sec] for e in sub[sec])
        check(ok, f"every {sec} entry of verify/PREREG_PUBLIC_SUBSET.md is copied unchanged "
                  f"from PREREG_PACKAGE_v2.md ({len(sub[sec])} of {len(full[sec])})")
    import importlib.util
    spec = importlib.util.spec_from_file_location("prereg_check", ROOT / "engine/scripts/prereg_check.py")
    pc = importlib.util.module_from_spec(spec)
    sys.modules["prereg_check"] = pc
    spec.loader.exec_module(pc)
    checks = pc.run(ROOT, SUBSET, strict=True)
    for c in checks:
        check(c.status == "PASS", f"prereg_check --strict {c.id}: {c.detail[:110]}")


def step4_ledgers() -> None:
    print("\n4. Every ledger's hash chain is intact (lens_engine.harness.ledger.verify)")
    from lens_engine.harness.ledger import verify
    for run, path in LEDGER.items():
        if not (ROOT / path).exists():
            check(False, f"{path} is missing")
            continue
        con = ro(path)
        head = con.execute("SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()[0]
        v = verify(con, expected_head=head)
        con.close()
        check(v.ok, f"{path} verifies to head {head[:12]}..."
              + ("" if v.ok else " PROBLEMS: " + "; ".join(v.problems[:3])))


def diff(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{path}/{k}: only on one side" for k in set(a) ^ set(b)]
        for k in set(a) & set(b):
            out += diff(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} vs {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")]
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
        return []
    return [] if a == b else [f"{path}: {a!r} vs {b!r}"]


def step5_analysis(published: dict) -> None:
    print("\n5. A fresh run of engine/scripts/stage9_analysis.py gives every published number")
    head = next(r["sha"] for r in hash_rows() if r["type"] == "final-head")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "results_rerun.json"
        cmd = [sys.executable, str(ROOT / "engine/scripts/stage9_analysis.py"),
               "--config", str(ROOT / CONFIG["stage9-holdout-v2"]), "--expected-head", head,
               "--root", str(ROOT), "--package", str(SUBSET), "--out", str(out)]
        print("      running:", " ".join(Path(c).name if "/" in c else c for c in cmd[1:]))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not check(r.returncode == 0 and out.exists(),
                     f"stage9_analysis.py exited {r.returncode}" + (f": {r.stderr[-300:]}" if r.returncode else "")):
            return
        res = json.loads(out.read_text())
    con = ro(LEDGER["stage9-holdout-v2"])
    man = json.loads(con.execute(
        "SELECT payload FROM ledger WHERE ref = 'stage9:PREDICTIONS'").fetchone()[0])
    con.close()
    nt, failed_nt = res.pop("null_tests"), res.pop("null_tests_failed")
    cfg = json.loads((ROOT / CONFIG["stage9-holdout-v2"]).read_text())
    # the same wrapping as lens_engine.stage9.runner.evaluate (its code-hash check is the one
    # step this repository cannot repeat, see README)
    rebuilt = {"schema": "lens.stage9.results/2", "config_id": cfg["config_id"],
               "config_sha256": sha256(ROOT / CONFIG["stage9-holdout-v2"]), "ledger_head": head,
               "synthetic": False, "internal_benchmark": cfg["internal_benchmark"],
               "model": man.get("model"), "arm_score_method": man.get("arm_score_method"),
               "arm_set": man.get("arm_set"), "null_tests": nt, "null_tests_failed": failed_nt,
               "accuracy_shown": not failed_nt, "analysis": res}
    # One value differs by design: meta.prereg_checks_passed counts the pre-registration checks
    # that passed before the run. The private run checked the full manifest. This repository checks
    # the public subset. Both must be "all of them".
    sub_n = len(json.loads(FENCE.findall(SUBSET.read_text())[0])["files"]) + len(
        json.loads(FENCE.findall(SUBSET.read_text())[0])["ledgers"])
    meta = rebuilt["analysis"]["meta"]
    check(meta["prereg_checks_passed"] == sub_n,
          f"the re-run passed all {sub_n} subset checks first. The published run passed all "
          f"{published['analysis']['meta']['prereg_checks_passed']} checks of the full manifest")
    meta["prereg_checks_passed"] = published["analysis"]["meta"]["prereg_checks_passed"]
    d = diff(published["analysis"], rebuilt["analysis"])
    check(not d, f"every other value under 'analysis' in {RESULTS} matches the re-run"
          + ("" if not d else f" ({len(d)} differ, first: {d[0]})"))
    d = diff(published, rebuilt)
    check(not d, f"the whole of {RESULTS} matches the re-run, null tests included"
          + ("" if not d else f" ({len(d)} differ, first: {d[0]})"))


def step6_report(published: dict) -> None:
    print("\n6. The published report and addendum are exactly what the results file renders")
    check(sha256(ROOT / RESULTS) == RESULTS_SHA, f"{RESULTS} sha256 = {RESULTS_SHA[:12]}... (named in the addendum)")
    from lens_engine.stage9 import report
    f1 = report.frontier_lines(published["analysis"]["F1"])
    text = report.render(published)
    block = "\n" + "\n".join([""] + f1)
    same = text.replace(block, "", 1) == (ROOT / REPORT).read_text()
    check(block in text and same, f"{REPORT} = report.render(results.json) byte for byte, "
          "without the F1 block it left out")
    check("\n".join(f1) in (ROOT / ADDENDUM).read_text(),
          f"the F1 block of {ADDENDUM} = report.frontier_lines(results.json analysis.F1)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-analysis", action="store_true", help="skip step 5 (the 6 minute re-run)")
    a = ap.parse_args()
    published = json.loads((ROOT / RESULTS).read_text())
    step0_files()
    step1_published_hashes()
    step2_order()
    step3_prereg()
    step4_ledgers()
    if a.skip_analysis:
        print("\n5. skipped (--skip-analysis)")
    else:
        step5_analysis(published)
    step6_report(published)
    print(f"\n{len(passed)} pass, {len(failed)} fail")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
