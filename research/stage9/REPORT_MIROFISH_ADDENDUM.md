# Stage 9 addendum: MiroFish swarm arm

**This is a post-publication addendum, and every number in it is provisional.** Its label in the results file is "post-publication addendum, provisional, after the Stage 9 hierarchy, never gated". It was run from 29 October to 1 November 2026 under `research/stage9/MIROFISH_PREREG.md`, which was sealed in its own ledger before any MiroFish call on a holdout test. The published Stage 9 v2 report, `research/stage9/results.json`, both Stage 9 ledgers and the F1 OpenAI addendum were only read. Every number below is rendered by a script from `research/stage9/results_mirofish.json`. The run log counts come from the harness's run log, which stays private because it holds raw replies. The script, a counts-only summary of that log and the exploratory checks (`render_mirofish_addendum.py`, `mirofish_run_summary.json`, `mirofish_sensitivity.py` and `mirofish_sensitivity.json`) are in the private Lens project.

- Pre-registration sha256: `c4b50da92d989a1c8e87fd9f7b4f9c5c60a0161050ce6b67512658604ae70b37`
- Ledger final head (the `mirofish:RESULTS` entry): `794cdb281a335a82ff2456281d0eae9dadc756d053ce716df498770f65913548`
- Ledger head the results were scored at (the `mirofish:PREDICTIONS` entry): `9b3c71f436dc258e8fc6643348daf56a2a743aaddc17274ed1265d060f7384a6`
- `research/stage9/results_mirofish.json` sha256: `73c65947fb85b1d36d31b01c0b517983e0b9846b88ff99a4700b148adb810fbb`
- Predictions file sha256, sealed in the ledger: `bd37103d8a6732140781eb177f7dfa5cca87cd98fe617092bcfec2fdb469f98b`
- Stage 9 final head the arms were scored against: `593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f`
- Harness sha256: `2c7d90be004bd0d2fa8c3da26a541377ff18af7f4b611120cb9f209fd254a1fd`
- MiroFish commit, unmodified: `7657031ac01184afe2cb220f5ee3545573b5e843`

## The result

MiroFish picked the best headline on 43 of 150 tests, a pick rate of 28.7% (95% CI 22.0% to 36.0%). Chance on these tests is 27.7%, and the lift L is +0.013 (95% CI -0.081 to +0.112). The interval on the pick rate includes chance and the interval on L includes zero, so this sample doesn't show that this setup did better than chance. The interval also leaves room for a lift of up to +0.112.

On the same tests, Lens minus MiroFish is +24.7 pts (95% CI +14.0 pts to +34.7 pts), and GPT-6 Astra minus MiroFish is +10.3 pts (95% CI +0.7 pts to +19.3 pts). Both intervals are above zero. The other four frontier comparisons have intervals that include zero, so no difference is claimed for them.

## All arms on the same 150 tests

| Arm | Model | Picked the best version (95% CI) | Chance | L (95% CI) | Arm minus MiroFish (95% CI) | Comparison |
|---|---|---|---|---|---|---|
| MiroFish | `gpt-4o-mini` | 28.7% (22.0% to 36.0%) | 27.7% | +0.013 (-0.081 to +0.112) | | |
| Lens | Stage 9 stack | 53.3% (44.7% to 60.7%) | 27.7% | +0.354 (+0.238 to +0.459) | +24.7 pts (+14.0 pts to +34.7 pts) | primary |
| GPT-6 Astra | `gpt-6-astra` | 39.0% (32.3% to 45.7%) | 27.7% | +0.156 (+0.064 to +0.245) | +10.3 pts (+0.7 pts to +19.3 pts) | primary |
| GPT-6.1 Sol | `gpt-6.1-sol` | 38.3% (31.7% to 44.7%) | 27.7% | +0.147 (+0.057 to +0.234) | +9.7 pts (-0.3 pts to +18.7 pts) | secondary |
| GPT-6.1 Terra | `gpt-6.1-terra` | 36.7% (29.3% to 43.3%) | 27.7% | +0.124 (+0.027 to +0.217) | +8.0 pts (-2.0 pts to +17.3 pts) | secondary |
| Opus 5.5 | `claude-opus-5-5` | 37.0% (30.0% to 43.7%) | 27.7% | +0.128 (+0.033 to +0.221) | +8.3 pts (-1.7 pts to +18.0 pts) | secondary |
| Sonnet 5.5 | `claude-sonnet-5-5` | 32.8% (26.3% to 39.5%) | 27.7% | +0.070 (-0.023 to +0.160) | +4.1 pts (-6.0 pts to +13.6 pts) | secondary |

L is (pick rate minus chance) divided by (1 minus chance). Intervals are 95% percentile bootstrap, with 2,000 resamples clustered by test and seed 9000.

Three differences apply to every comparison above:

- MiroFish saw one fixed order per test and its pick scores 1 or 0. The frontier arms saw two orders and scored 0.5 per order.
- A MiroFish test with no valid pick scores 0, and a frontier arm with no valid pick gets chance credit, because the Stage 9 best-of-k rule splits a tie among the kept arms.
- A valid MiroFish pick of an arm the Stage 9 outcome read dropped scores 0, where a frontier arm gets chance credit. This happened 0 times here.

A fourth difference applies to Lens. It scores each version on its own, so it has no presentation order, and a tie in its scores splits credit under the Stage 9 best-of-k rule.

Before any MiroFish number was computed, the scoring step re-scored the five frontier arms on all 2,110 tests and matched the published F1 numbers: GPT-6 Astra 37.8%, GPT-6.1 Sol 37.3%, GPT-6.1 Terra 36.8%, Opus 5.5 35.7%, Sonnet 5.5 34.5%, against Lens at 49.9% and chance at 25.2%. The chance line is higher on this sample because tests with more than 5 versions are left out, so rates on the 150 tests shouldn't be read against the 2,110-test rates.

## Parse counts and spend

| Item | Value |
|---|---|
| Tests scored | 150 of 150 |
| Valid picks | 147 |
| Cannot tell | 0 |
| Invalid replies | 1 |
| Failed tests | 2 (1 in ontology, 1 in report) |
| Tests not run | 0 |
| Picks of a dropped arm | 0 |
| Pick rate among answered tests (secondary) | 29.3% of 147 |
| Mean agents per test (secondary) | 6.2 |
| Mean rounds run (secondary) | 23.7, see the setup limit below |
| Mean spend per test (secondary) | 0.065 USD |
| Actual OpenAI spend | 9.79 USD against a 15 USD cap |

47 of the 10,841 metered calls failed on the network, and the sealed rule charged them their worst case, 0.15 USD in all. Cached input was also charged at the full input price, so the spend figure can only run high. Zep Cloud usage sits outside this figure.

As read from the Zep dashboard on 1 November 2026, project `lens-mirofish-test` is on the Free plan with a 10,000 credit limit, and the Free plan carries no charge. Monthly usage shows 2,211 credits, labelled "this month". The last 7 days show about 1.8K episodes added (shown rounded), 160 graphs created, 0 still processing and an error rate of 4.45%. These are account-level dashboard totals, so they may include the practice runs and they don't split by run. The 1.8K figure is rounded, and the dashboard doesn't say what window "this month" uses. They can't be attributed precisely to the full run, and this report claims no cause for the error rate.

## Limits

- **The sample.** These are 150 tests with 5 or fewer versions, drawn by a fixed hash order from the 2,110 holdout tests: 18 with 2 versions, 12 with 3 versions, 92 with 4 versions, 28 with 5 versions. 454 tests were left out for having more than 5 versions, which left 1,656 eligible.
- **The setup.** MiroFish ran as one configuration: `gpt-4o-mini`, the Reddit platform only, 24 simulation rounds configured per test, a mean of 6.2 agents. The recorded figure of 23.7 rounds is the status reading when the harness stopped polling. This measures that setup on headline clicks and doesn't measure MiroFish in general.
- **The model.** `gpt-4o-mini` is MiroFish's own default, and the frontier arms ran on other, newer models. A second MiroFish arm on `gpt-6.1-terra` was not run in this addendum, by the owner's decision on 29 October. So this addendum can't separate what the swarm adds from what the model adds.
- **The training.** Lens was fitted on Upworthy tests outside the holdout. MiroFish and the frontier arms received no such training, and MiroFish was given a neutral audience description with no source name.
- **The orders.** MiroFish saw one fixed order per test where the frontier arms saw two.
- **Failures count as misses.** 2 failed tests and 1 invalid reply score 0. The pre-registration forbids asking again or reading a reply to recover a pick.
- **The score can't be re-derived from the public files.** The predictions file holds raw replies, so it stays private. The ledger seals its sha256.
- **The label.** Like every Upworthy number, these results are provisional and sit after the Stage 9 hierarchy. They are never gated and prove no endpoint.

## What happened in the run

The run started at 20:29 on 29 October IST. The macOS power log shows the Mac on battery with lid-closed sleep from 01:10 on 30 October IST, a low-power sleep at 08:06 on 30 October and a wake at 16:53 on 30 October, when mains power was attached. The harness held an idle-sleep block, and closing the lid on battery still puts the Mac to sleep.

The sleep cost 5 attempts on 4 tests, with 37,485 seconds of sleep recorded in the attempt records. Each one failed under the sealed rule that treats a slept test as a pipeline failure.

| Test | Attempt | Stage | Sleep recorded in that attempt | Final outcome of the test |
|---|---|---|---|---|
| A | 1 | close_env | 1,717 s | a pick on its re-run |
| B | 1 | close_env | 59 s | a miss, counted as failed |
| B | 2 | ontology | 601 s | a miss, counted as failed |
| C | 1 | simulate | 3,521 s | a miss, counted as failed |
| D | 1 | prepare | 31,587 s | a pick on its re-run |

The last metered call before the cut-off was at 16:55 on 30 October IST, while the harness was waiting for the network to come back, and the process ended there. The run log doesn't record why it ended. That call was a leftover from attempt 1's prepare stage on test D: MiroFish's preparation job was still running after the harness had timed it out. 27 such calls, from 16:54 to 16:55 IST, cost 0.086 USD at worst case. 26 of them, 0.083 USD, came after that attempt's record closed, which is why mean spend times 150 gives 9.71 USD against the 9.79 USD total. The harness had announced the re-run of test D and was waiting for the network before starting it. It sent no request for that re-run and recorded no start, so the test's single re-run was still unused when the run resumed.

The run resumed at 04:45 on 1 November IST under the same locked rules, in the same folder (`full-20261029T145928Z`), with the same harness and the same 15 USD cap. Spend carried over at 5.98 USD. It finished all 150 tests with no stop reason, and the ingest step accepted it. No test that finished had a sleep on its last attempt.

**Which final failures involved sleep.** Both failed tests did, and the invalid reply did not.

- Test B lost both attempts to sleep, and its final failure is in the ontology stage.
- Test C lost its first attempt to sleep. A further 435 s of sleep fell between the announcement of this re-run and its start, and it isn't in the attempt record. It's the same window, handled the same way, before any cut-off. The re-run then recorded no sleep and failed in the report stage.
- The invalid reply came on 1 November with no sleep recorded.

**A separate failure.** MiroFish's report task returned a failed status with the error text `'name'` on 15 attempts, one each on 15 tests. 14 of those tests finished on their single re-run. The other is test C. This report doesn't claim a cause. In all, 18 tests used a re-run across 168 attempts.

## Sensitivity

**This line is only an upper bound.** If the 2 failed tests and the 1 invalid reply had all been hits, MiroFish would have 46 of 150, a pick rate of 30.7% and L of +0.041. That is the most those 3 tests can change the score. Lens would still lead by +22.7 pts as a plain difference, with no interval computed. This bound assumes every one of those tests was a hit, which nothing in the run supports.

**Strict-reading check (exploratory, computed after the seal).** The pre-registration says "An attempt that was cut off counts as a failed attempt." The console announced attempt 2 of test D before the cut-off. A literal counter-reading is that a cut-off there is a second failure and so a miss. That reading is weaker but arguable. The re-run was treated as valid because the pre-registration places the network wait before the test ("Before each test the harness waits for api.openai.com"), and the sealed harness calls `wait_for_openai` before `event("start")`, so `close_interrupted` treats only attempts with a start event as cut off. No request was sent for that attempt and no start was recorded.

Under the strict reading, re-scored with the frozen bootstrap, MiroFish has 42 of 150, 28.0% (21.3% to 35.3%), L +0.004 (-0.089 to +0.103), with 3 failed tests and 146 answered. Arm minus MiroFish becomes: Lens +25.3 pts (+14.7 pts to +35.3 pts), GPT-6 Astra +11.0 pts (+1.7 pts to +20.0 pts), GPT-6.1 Sol +10.3 pts (+0.7 pts to +19.3 pts), GPT-6.1 Terra +8.7 pts (-1.3 pts to +18.0 pts), Opus 5.5 +9.0 pts (-1.0 pts to +18.3 pts), Sonnet 5.5 +4.8 pts (-5.2 pts to +14.5 pts). The GPT-6.1 Sol interval, which is secondary, then clears zero. The reported reading is the kinder one to MiroFish, because that re-run produced a hit, and both primary conclusions are unchanged. The sealed result stays as reported.

## Multiple comparisons

The pre-registration names two primary comparisons: Lens minus MiroFish and the best frontier arm minus MiroFish. The best frontier arm is GPT-6 Astra, chosen before the run for its pick rate on all 2,110 tests. The other four are reported as secondary. That makes six paired comparisons, and the pre-registration applies no correction for multiplicity, so none is applied here.

The GPT-6 Astra interval starts at +0.7 pts, which is about 1 test of 150. That margin is thin. The Lens interval starts at +14.0 pts.

**Two-comparison correction (exploratory, computed after the seal).** With 97.5% intervals, 20,000 resamples and seed 9000, GPT-6 Astra minus MiroFish is -0.7 pts to +21.3 pts and Lens minus MiroFish is +12.7 pts to +36.7 pts.

## To check it

The public record at https://github.com/warierhemant/lens-track-record checks the pre-registration, the results file and the ledger with `python3 verify/verify_all.py`, including the ledger chain through `lens_engine.harness.ledger.verify`. In the private Lens project, `python3 research/stage9/render_mirofish_addendum.py check` confirms this page equals a fresh render.
