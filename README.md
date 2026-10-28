# Lens track record

Lens predicts which version of a piece of copy will win an A/B test. This repository holds the sealed record of its Stage 9 accuracy test, and everything an outsider needs to check that record without trusting us. It holds no product code, no model and no serving code.

## What was tested

Stage 9 asked one question. Given the headlines of an Upworthy A/B test and nothing else, can Lens tell which headline got the most clicks?

- **The data.** The holdout part of the Upworthy Research Archive: 2,110 tests with 9,324 headlines between them. Lens never trained on these tests.
- **The model.** One frozen model, `lens-ens10-STACK` version `94ed011ee886`, chosen by an earlier sealed run (the stack gate) before Stage 9 started.
- **The order of events.** Every rule, threshold and pass mark was written into a pre-registration package and a frozen config first. Their hashes were published. Then the config was sealed as entry 1 of a hash-chained ledger. Then every prediction was sealed into that ledger, and its head was published. Only after that were the real outcomes read and joined. The final head was published too. Nothing was tuned on the results.
- **The scoring.** Endpoints are checked in a fixed order. Once one fails, the later ones are still computed and shown, but none of them counts as a claim.

## The result

All nine null tests passed. These check the test machinery itself. Example: a model that knows nothing scores like chance, shuffled outcomes give no signal, and every edited or deleted ledger entry is caught.

| Endpoint | Verdict | The numbers |
|---|---|---|
| **P.** Lens finds the best headline more often than chance | **Pass** | Lift 0.330 (95% CI 0.302 to 0.359) on 2,110 tests. Lens picked the best headline 49.9% of the time where chance is 25.2%. The bar was a CI lower end of at least 0.171. |
| **S1.** The text learner beats simple guesses (position, length, newer arm, familiarity, recognition) | **Pass** | It beats each one by at least 35 points. |
| **S2.** The panel "describe" call adds to the text learner | **Fail** | Gain 0.0011 nats per pair (95% CI -0.0024 to 0.0046). The describe call is dropped. The fixed order stops here. |
| **S3.** Lens's probabilities mean what they say (calibration) | Fail, not claimed | Slope 1.13 (95% CI 1.01 to 1.27), outside the bar. |
| **S4.** The can't-tell rule stays quiet on tests with no real difference | Pass, not claimed | Called 4.0% of 5,191 null pairs. The bar was 5%. |
| **C98.** When Lens is confident, it is right at least 98% of the time | **Fail**, not claimed | Right on 98.7% of its confident calls, covering 72.1% of decided pairs. The 95% CI runs from 97.9% to 99.3%. A pass needed the lower end at 98% or more, so this missed. |
| **S5.** Lens picks the winner of decided pairs often enough | Pass, not claimed | Right on 92.8% of 1,664 decided pairs. The target was 86.1%. Always keeping the control gets 57.4%. |
| **S6.** A sequential test against the strongest naive rule | Pass, not claimed | Edge shown at the first look (40 calls), one-sided p = 9.5e-07. |

Every result here carries the label **provisional**. It stays provisional until there are at least 100 decided pairs from tests that ended after the training cutoff of Opus 5.5 (June 2026). At sealing there were fewer.

So the claims that stand are P and S1. The describe call (S2) failed and was dropped. The 98% confident-call promise (C98) was missed on its pre-set rule. Everything after S2 is shown for completeness and claims nothing.

An addendum written on 2026-10-24 adds a block the report left out: two frontier models given the same tests with no training. Lens picked the best headline 49.9% of the time. Opus 5.5 did so 35.7% of the time and Sonnet 5.5 34.5%. This block sits after the fixed order and is never gated. It was rendered from the unchanged published results file.

A second addendum, run on 2026-10-27 and 2026-10-28, adds three OpenAI models on the same tests with the same prompts. It was pre-registered and sealed in its own ledger before any OpenAI call. GPT-6.1 Terra picked the best headline 36.8% of the time, GPT-6.1 Sol 37.3% and GPT-6 Astra 37.8%. Lens beats each of them, with the 95% CI of the gap above zero in every case. The full text is in [`research/stage9/REPORT_F1_OPENAI_ADDENDUM.md`](research/stage9/REPORT_F1_OPENAI_ADDENDUM.md).

The full text is in [`research/stage9/REPORT.md`](research/stage9/REPORT.md) and [`research/stage9/REPORT_F1_ADDENDUM.md`](research/stage9/REPORT_F1_ADDENDUM.md). The published hashes are in [`docs/track-record/HASHES.md`](docs/track-record/HASHES.md). Every file in this repository is listed in [`MANIFEST.md`](MANIFEST.md) with its hash and the reason it is here.

## How to verify it

You need git, Python 3 (tested with 3.14.5), about 3 GB of free disk and about 10 minutes. The steps work on macOS and Linux.

**1. Get the repository.**

```sh
git clone https://github.com/warierhemant/lens-track-record.git
cd lens-track-record
```

**2. Get the two large ledgers.** The stack gate ledgers are about 1 GB each, too large for git, so they are attached to the release `ledgers-2026-10-23`.

```sh
BASE=https://github.com/warierhemant/lens-track-record/releases/download/ledgers-2026-10-23
curl -L -O "$BASE/stack_gate_ledger.sqlite.gz"
curl -L -O "$BASE/stack_gate_refit_nf4r_ledger.sqlite.gz"
gunzip -c stack_gate_ledger.sqlite.gz > engine/experiments/stack_gate/ledger.sqlite
gunzip -c stack_gate_refit_nf4r_ledger.sqlite.gz > engine/experiments/stack_gate/refit_nf4r/ledger.sqlite
shasum -a 256 -c verify/LARGE_FILES.sha256
```

The last command must print `OK` for all five ledgers. On Linux, `sha256sum -c` does the same.

**3. Make a clean Python environment.**

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r verify/requirements.txt
```

**4. Run every check.**

```sh
python3 verify/verify_all.py
```

It takes about 6 minutes and must end with `0 fail`. It checks these things in turn.

1. Each ledger is the exact file that was published.
2. Each line in `docs/track-record/HASHES.md` matches its file or ledger entry. The package and config lines are file hashes. The head lines are entries of the run's ledger.
3. Entry 1 of the Stage 9 ledger is the frozen config, and it records the hashes of this config and this package. The predictions manifest (the published predictions head) is the last prediction, and the first outcome comes right after it.
4. `engine/scripts/prereg_check.py --strict` passes with 0 FAIL on `verify/PREREG_PUBLIC_SUBSET.md`. The script first proves that every entry in that file is copied unchanged from the manifest in `PREREG_PACKAGE_v2.md`.
5. Every ledger's hash chain is intact.
6. `engine/scripts/stage9_analysis.py` runs from scratch on the ledger and gives back every value in `research/stage9/results.json`, null tests included. One value differs by design. It counts the pre-registration checks the run passed before it started: 147 for the full manifest in the private run, 10 for the public subset here. The script checks that each run passed all of its own.
7. The published report and addendum are exactly what that results file renders.

**5. Or check the main points by hand.** Each command below is independent of the verify script.

```sh
# The package and config hashes in HASHES.md
shasum -a 256 research/accuracy/PREREG_PACKAGE_v2.md engine/experiments/stage9/FROZEN_CONFIG.json

# Entry 1 of the ledger seals that config and that package
sqlite3 -readonly engine/experiments/stage9/ledger.sqlite "SELECT seq, ts, payload FROM ledger WHERE seq = 1"

# The published predictions head is the sealed manifest, and the final head is the last entry
sqlite3 -readonly engine/experiments/stage9/ledger.sqlite \
  "SELECT seq, kind, ref FROM ledger WHERE hash IN ('6cb99dec7e891bd62e57aa4a59b1b8a29d6b2641f329dbae0c5d140bacbe3fe3', '593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f')"
sqlite3 -readonly engine/experiments/stage9/ledger.sqlite "SELECT min(seq) FROM ledger WHERE kind = 'outcome'"

# The pre-registration check
python3 engine/scripts/prereg_check.py --strict --package verify/PREREG_PUBLIC_SUBSET.md

# The full analysis, then compare its output with research/stage9/results.json
python3 engine/scripts/stage9_analysis.py --config engine/experiments/stage9/FROZEN_CONFIG.json \
  --expected-head 593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f \
  --package verify/PREREG_PUBLIC_SUBSET.md --out /tmp/stage9_rerun.json

# The addendum's frontier block, rendered from the published results
cd engine && python3 -c "import json; from lens_engine.stage9 import report; print('\n'.join(report.frontier_lines(json.load(open('../research/stage9/results.json'))['analysis']['F1'])))"
```

## What you can and cannot check here

You can check that the rules were fixed and published before the run, that every prediction was sealed before any outcome, that the ledger was never edited, and that every published number follows from the sealed predictions and outcomes.

Some things stay outside this repository, and we would rather say so plainly.

- **The predictions cannot be re-run.** That needs the model, which is not published. The ledger proves the predictions were fixed before the outcomes were read. It cannot show how good the model would be on other data.
- **The outcomes can be checked against the public archive, with some work.** Each ledger entry names its Upworthy test id and arm. The rule that turns the archive's rows into arms is in `research/stage9/AMEND_text_only_precollection.json`. The verify script does not do this step.
- **The code hash in ledger entry 1 cannot be recomputed here.** It covers the whole Stage 9 code package, which includes the code that calls the model. This repository holds only the analysis script and the modules it runs. They are byte for byte the versions in the private project, and step 6 shows they reproduce every number.
- **The publication times come from the private project's records.** This repository opened on 2026-10-27 with the nine lines from 2026-10-23. The ledger's own timestamps agree with them. Example: entry 1 of the Stage 9 ledger is stamped 13:14 UTC, which is 18:44 IST, the time of the config line.
- **A few pre-registration values are not checkable here.** The full manifest in the package also covers plans and code from earlier stages, the app, and two hashes kept inside the sealed holdout folder. `MANIFEST.md` lists each one left out and why. One of them is the stack gate's plan file. It contains a private note that has nothing to do with the result, so it is withheld. Its hash (`ac003b8e...a60b`) is still sealed in entry 1 of both stack gate ledgers.

## Future entries

Every future sealed result will be added to this repository as new dated commits, in the order the run produces its hashes. Published lines and files are never edited or removed. A correction is always a new line that names the one it corrects.

## Credit

The test data is the **Upworthy Research Archive** by J. Nathan Matias, Kevin Munger, Marianne Aubin Le Quere and Charles Ebersole ("The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media", *Scientific Data* 8, 195, 2021, [doi:10.1038/s41597-021-00934-7](https://doi.org/10.1038/s41597-021-00934-7)). It is published on OSF at [osf.io/jd64p](https://osf.io/jd64p/) under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licence. This repository links to the archive at that address and holds only the values derived from it that the analysis needs: Upworthy test and arm ids, outcome labels computed from the archive's clicks and impressions, and model scores. No headline text is included. These derived files are shared under CC BY 4.0 as well.
