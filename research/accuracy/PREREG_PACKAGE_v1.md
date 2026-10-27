# Stage 9 pre-registration package (step 8.13), FINAL DRAFT FOR SEALING

First drafted 2026-10-15. **Rewritten 2026-10-20** (cloud session, branch `cloud/s9-prereg-v2`) for the production stack chosen since then: the Gemma 4 31B base scorer selected in 8.1c, the voyage-4 embedding learner and, if the stack gate keeps it, one Opus describe call, ridge-stacked. The rewrite encodes Emily's nine decisions of 2026-10-20 (listed in section 0) and resolves O1-O13 one by one (section 7). **Revised 2026-10-21** (branch `cloud/s9-blockers`, PR #101) for Emily's six rulings of 2026-10-21 (section 0b): the learner decision tree, the S4 extended grid, the E2E GPU text route, the credit check before the holdout text read, the M5 mapping and the 98% display rule, and the credit note. **Refreshed 2026-10-21** (branch `cloud/s9-gaps-b`, runbook gaps G4, G8 and G9) against the merged refit config (PR #112/#114): t_S4 0.4905, S5 target 0.8611, the refit stack `94ed011e...c3bc` and its ledger heads, 12 post-cutoff decided pairs (PR #110), Emily's B1 d confirmation, her display ruling on the 98% phrase (C98 must pass in the hierarchy), the `package` track-record line (G8) and the independent refit re-run (G9, `research/stage9/B7b_REFIT_RERUN.md`).

Status: **DRAFT, NOT SEALED.** Nothing here may be hashed into a ledger until every blocker in section 7.2 is closed and Emily has signed off. When it is sealed, this file is copied to `PREREG_PACKAGE_v1.md` and that copy is hashed. This draft is never edited into the sealed version in place.

Sources read for the rewrite: `research/stage9/READINESS_2026-10-20.md` (PR #86); `research/market/COMPETITORS_2026-10-20.md` section 8 ("What Stage 9 must prove") and its "Lens's own evidence" notes; `engine/experiments/8_1c/SELECTION_REPORT.md`; the stack gate draft `engine/experiments/stack_gate/PLAN.json` (PR #59); the Stage 9 runner `engine/lens_engine/stage9/` (PR #50) and `engine/scripts/stage9_analysis.py`. Earlier sources, unchanged: `RESUME.md`; `ACCURACY_ENGINE_SPEC_v3.md` (row 8.13, sections 2, 4.1-4.8, 9); every `engine/experiments/*/PLAN.json`; the rulings `R-2026-10-13-chance-line` and `R-2026-10-14-grade-vs-base-rate`.

Checker: `python3 engine/scripts/prereg_check.py` recomputes every hash listed here and compares it (section 8). Frozen config draft: `research/stage9/FROZEN_CONFIG_DRAFT.json` (the runner's config, section 2.10).

---

## 0. Emily's decisions of 2026-10-20, and where each is encoded

| # | Decision | Encoded in |
|---|---|---|
| 1 | **Learner.** Stage 9 scores the GATED 10-split Gemma ensemble (Path 2), not a fresh final adapter | 2.1; config `model.design` |
| 2 | **Frontier arms.** Opus 5.5 zero-shot best-of-k and Sonnet 5.5 zero-shot run head to head on every holdout test. The Sonnet 8-persona x 2-order panel is dropped. Dry-run cost about $6 combined | 2.3; endpoint F1 in 5.4; config `frontier_arms` |
| 3 | **Stack gate.** Opus describe runs on a CAPPED budget of $65 (about half the pairs), on a deterministic seeded sample. Pairs without a describe enter through a missing-feature indicator. The gate decides whether describe stays in the frozen stack | 2.2; `stack_gate/PLAN.json` `describe`, `stacker`, `describe_decision`; `run_stack_gate.py` |
| 4 | **Credit reserve.** Stage 9 never starts with less credit than its worst-case cost. Reserve: $70 | 2.7; config `credit`; runner `_gate_credit` |
| 5 | **Extra metrics.** Kappa at matched coverage, a reliability curve with a monotonicity test, confidence AUROC and ECE, null-pair call rate under 5%, open evaluation code | 5.5 and S4; `stage9_analysis.extra_metrics`; 2.9 |
| 6 | **B2B evidence.** A separately sealed B2B set (own-site tests plus connector replay), results "pending" until it reaches its pre-registered n | 2.8 |
| 7 | **Label.** Results are "provisional" while the post-Opus-cutoff (June 2026) set has fewer than 100 decided pairs. Today: 12 (PR #110) | 1, 2.6; analysis `label` |
| 8 | **Web-presence baseline (O13).** Dropped unless a free licensed index exists. None was found; the drop is disclosed | section 5, draft change 5.2; `S1_BASELINES` |
| 9 | **Publication.** Config hash and ledger heads are published in this repo under `docs/track-record/` | 2.9; `docs/track-record/README.md` |

## 0b. Emily's rulings of 2026-10-21, and where each is encoded

| # | Ruling | Encoded in |
|---|---|---|
| 1 | **Learner = the gate-adopted 10-split Gemma ensemble, with saved adapters.** The 8.1c NF4 adapters were never saved. If the bf16 8.1c gate (PR #99, job g81c, which now saves all 10 adapters to the Mac) meets its sealed adoption rule, the learner is the bf16 ensemble from those adapters; otherwise an NF4 retrain of the 10 per-split adapters on E2E with the sealed 8.1c recipe and seeds, accepted only if every split's tune log-loss replays the sealed NF4 value within 0.011088638914821092 (the sealed noise margin, 2 x pooled seed SD). Either way the stack is re-fit only by the sealed stack gate procedure, and the config pins the adapter sha256 list | 2.1a; config `model.learner_rule`, `model.adapters` (route nf4_retrain, 10 pins, filled 2026-10-21), `model.stack_sha256` (`94ed011e...c3bc`, the refit stack, filled 2026-10-21); `stage9/learner.py`; `config.validate` |
| 2 | **S4 extended grid.** The LTT grid is extended upward (p >= 0.9999 down to 0.9901 in 0.0001 steps, then the sealed grid), on non-holdout cross-fitted predictions only. Lowest threshold under 5%; if none, S4 fails honestly. The 5% is not loosened | 2.1 S4 row, 5; config `s4`; `stack_gate/s4_extended.py` -> `s4_extended.json`. **Result on the refit (B1 d, the value in the config): PASS at t_S4 = 0.4905 (p >= 0.9905): null call rate 4.80% (1,268 of 26,442), coverage 30.1% of decided pairs, right on 99.8% of them.** On the gate's own readouts it was 0.4913 (1,270 of 26,442, coverage 30.0%) |
| 3 | **GPU pass on holdout text on E2E only** (familiarity and recognition under the Gemma base; owner's prepaid account): text only, no labels; a fresh instance, deleted after; the text sha256 list logged before upload; score files hash-checked on return | 2.1 data flow; amendment `gpu_pass`; `stage9/gpu_pass.py`; `stage9/familiarity.py` pinned in config `baselines.familiarity.implementation_sha256`. **Readouts:** Emily ruled the same day that the 10 per-split adapter readouts of holdout pairs ride the same route (`stage9/readout.py`, config `model.readout`). Launcher built 2026-10-21 (`stage9/e2e_gpu_pass.py`, B3). The non-holdout `test_part` pass ran 2026-10-21 (Stage 9 GPU ledger entry `ffbf0d63...2a06`, the refit's readouts); the holdout pass runs after `seal-config` (runbook step I) |
| 4 | **B4 approved in substance:** the credit check moves to before the holdout text is read; the amendment stays unsealed | section 4 step 2; `precollect.gate_credit` (build); `runner._gate_paid`; amendment `credit_check` |
| 5 | **Upworthy = M5. The 98% display rule is confirmed:** every "about 98% when confident" shows its coverage and its null-pair call rate next to it | config `datasets[0].product_use_case`, `emily_confirmed`; `stage9/report.py confident_claim`; `stack_gate/report_stack_gate.py` (RESULTS.md regenerated); `app/src/config/forecast-use-cases.ts confidentClaim` |
| 5b | **Display ruling (later the same day).** "About 98% when confident" may appear only when **C98 passes in the endpoint hierarchy** (its own bar, CI lower bound >= 98%, and gated). Ruling 5's thresholds (97.5%, CI lower bound 96%) stay as extra conditions. When C98 fails or is not gated, the report shows the measured accuracy with its CI lower bound, its coverage and its null-call rate, without the phrase. Prompted by the runbook's 1,500-test dry run, which printed the phrase while C98 had failed | section 5 C98 row; config `emily_confirmed.display_rule_98`; `stage9/report.py display_98_allowed`, `confident_claim` (tests `test_display_98_ruling.py`); `app/src/config/forecast-use-cases.ts display98Allowed`, `formatAccuracy` (`c98Passed`) |
| B1 d | **Re-derive after the re-fit: confirmed.** t98, t_S4 and the S5 target are re-derived with the same pinned code from the re-fit predictions, before any holdout read (the RESUME.md log on the Mac main tree, entry 2026-10-21 ~05:40 IST: "EMILY CONFIRMS: (a) after re-fit re-derive t98/t_S4/S5 target with same pinned code pre-holdout"; repeated in its ~07:00 entry, "Emily already confirmed B1d re-derivation") | 2.1a step 4; `scripts/stage9_refit.py`; config `c98.fit`, `s4`, `s5` (filled from the refit) |
| 6 | **Credit:** about $70.26 of promo credit left (unverified); Stage 9's worst case is $68, so nothing else may use Opus before Stage 9 | 2.7; config `credit` |

## 1. What Stage 9 is

Stage 9 runs the frozen Lens forecaster once on the **sealed Upworthy holdout**: 2,110 tests, 15% of test ids, stratified by start date, drawn and hashed in 8.0 before any split existed. Holdout id-list SHA-256 `1c62e0c5...ce77` (RESUME.md, verified by Emily 10-13). Every Stage 8 step excluded it, and the loader guard refuses it outside `lens_engine/stage9`. Reading any holdout outcome before this package is sealed voids the holdout (spec R11). The holdout text fingerprint (section 3.3) read headline text only, through the guard, and no outcome column.

Post-cutoff public tests, B2B sets and customer archives are scored **prospectively**, each in its own sealed config and ledger: only tests that end after that config's hash is published count.

**Label (decision 7).** Every Stage 9 number is labelled **provisional**. Upworthy is pre-cutoff for every model used, Opus 5.5 included. The label stays until a set of tests that **ended after the Opus 5.5 training cutoff (June 2026)** holds at least **100 decided pairs**. Today that set holds **12 decided pairs** (25 post-cutoff pairs: 8.7's 18 pairs with 9 decided, plus the 2026-10-21 growth sweep's 7 pairs with 3 decided, `research/accuracy/POSTCUTOFF_GROWTH_2026-10-21.md`, PR #110; 10 decided if the 2 TEST-ONLY NextAfter pairs are left out). The count is retrospective (the outcomes were read during curation), and config `label.post_cutoff_decided_pairs_at_sealing` records 12. The plan for growing it is in section 2.6. The label is lifted only by a separate report from that set's own ledger, never by editing Stage 9 results.

## 2. Frozen configuration (proposed)

"Proposed" means this is the configuration the evidence and Emily's decisions point to. It is frozen when the config draft (2.10) has no TODO left and is sealed as `stage9:FROZEN`. Where a value is still to come, the line names the step that fills it.

### 2.1 A/B winner forecaster: the Gemma 4 31B stack (the headline product number)

| Component | Frozen choice | Evidence | Fills it / open item |
|---|---|---|---|
| What Stage 9 scores | **The gated 10-split ensemble (Path 2, decision 1), read out with the adapters of the learner tree in 2.1a (ruling 1).** For a holdout pair (a, b): z = mean over splits s = 0..9 of z_s(b over a), where z_s is split s's frozen stacker applied to split s's own components. p = sigmoid(z). Arm scores for best-of-k = Bradley-Terry strengths of the within-test round robin of z (`pairwise_lm.arm_strengths`, the 8.1b aggregation). **No fresh final adapter is scored.** The final adapter, trained on the final training mixture `data/mixtures/lens-final-mixture-2026.10.20-4` (`final_manifest.json` SHA-256 `49182f6a2c5c49b990219486913a4d7b39386c78c5cab44a143da03e52f2b0fc`; on the Mac only), ships after Stage 9, as a model change through the 600-pair bridge test (2.5) | READINESS D3: the final adapter is never gated itself and leaves no out-of-fold logits for the stacker or the thresholds; the ensemble is exactly what the stack gate validates, split by split | stack gate (O12) |
| Scorer | **Gemma 4 31B base** (`google/gemma-4-31B` @ `5bbc2fb1c1b2c611d06e3d9f23c170ba21659d89`), pairwise Bradley-Terry LoRA per split at its tune-selected checkpoint, both-order readout `s = (d_ab - d_ba)/2`, tune pair scale. The 8.1c NF4 per-split adapters (Modal L40S) were never saved, so the adapters are those of 2.1a: the bf16 gate's (route bf16) or an NF4 retrain (route nf4_retrain), sha256-pinned in config `model.adapters` | 8.1c: PASS on 10 of 10 splits; mean L **0.304** [0.294, 0.314] vs Qwen3-14B 0.282, OSim-8B 0.244; G3 min margins B5 +17.0, B6 +9.6, B7 +10.5 pts; G4 pass on all five leakage baselines | none (selected, PR #79) |
| Embedding learner | The 8.1 text learner on **voyage-4** vectors, per split (voyage_test endpoint a, sealed there) | voyage_test: L 0.171 -> 0.242; stack +0.038 nats | none |
| Describe feature | **One Opus 5.5 describe call per pair** (`r0_opus` `requests_for`, the `-d` request; `claude-opus-5-5`, effort low, max_tokens 1024, Batch API), **only if the stack gate keeps it** (2.2). If kept, every holdout pair gets one call, collected in a sealed text-only pre-collection phase (section 4, phase 2b) | 8.6 KEEP (Opus +0.067 nats); describe alone carries the gain (post hoc, now tested by the stack gate's pre-registered describe decision) | stack gate `describe_decision` |
| Stacker = calibration | Ridge logistic by IRLS (`lens_engine/r0/stack.py`), fitted on the **symmetrised** fit set (each pair as oriented and reversed), so the intercept is exactly 0 and the stack is order-invariant. lambda 1.0 per pair. Design: `scorer_logit, emb_logit, desc_opus, scorer_logit_x_nodesc, emb_logit_x_nodesc` (STACK) or `scorer_logit, emb_logit` (STACK_no_describe), whichever the stack gate freezes. Cross-fitted per split on decided R-0 selection pairs of the split's train and tune parts, features from each pair's home split | `stack_gate/PLAN.json` `stacker` | stack gate (O5, O12) |
| Pairs without a describe | Missing-feature indicator m (1 = no usable describe). m enters only as `m x scorer_logit` and `m x emb_logit`, so the two learners are re-weighted when the describe is absent. m alone cannot enter an intercept-free antisymmetric stack (its coefficient is exactly 0). At Stage 9, m = 1 only on a failed or invalid call | `stack_gate/PLAN.json` `describe.missing_feature` | none |
| Can't-tell rule (S4) | Call a pair only when abs(p - 0.5) >= t_S4. t_S4 by Learn-then-Test on the non-significant null pairs of the stack gate's pooled test-part predictions of the frozen design (H0: null call rate >= 0.05, delta 0.10, fixed sequence from the top of the grid down). **Grid (ruling 2, 2026-10-21):** t = 0.4999 down to 0.4901 in 0.0001 steps (p >= 0.9999 ... p >= 0.9901), then the sealed 0.49 down to 0.01 in 0.01 steps. t_S4 = the lowest t rejected before the first failure. If the top of the grid already fails, S4 fails honestly (t_S4 = 0.5), Stage 9 reports it, and the product shows the null call rate beside every confident call. The 5% is not loosened. Panel decline reasons are not used (spec 4.6 bar not met) | 8.8 method; voyage_test b: one stacked configuration called 22% of null pairs at its 98% threshold, which is why S4 has its own threshold. The sealed grid stopped at 0.49 (p >= 0.99), where the stack still calls 5.4% of null pairs, so it returned "never call" | **t_S4 = 0.4905** (p >= 0.9905), re-derived on the refit (B1 d, 2.1a): null call rate 4.80% (1,268 of 26,442; Wilson 95% CI 4.54% to 5.06%; LTT p = 0.065; the next step, 0.4904, gives p = 0.120 and stops the sequence); coverage 30.1% of decided pairs (2,606 of 8,664), right on 99.8%; identical pairs called 0. `stack_gate/refit_nf4r/s4_extended.json` (sha256 `c9a68292e2d2271024d83485be23105f8dad6d3d313a90de71c0cc98768638e6`), code `s4_extended.py` (`affd66db...e97b`), read from the refit ledger (head `7035e628...101e`). The gate's own value, on the 8.1c Modal readouts, was 0.4913 (1,270 of 26,442, coverage 30.0%; `stack_gate/s4_extended.json` `5c63cb99...dc85`) |
| 98% when confident (C98) | t98 = the r0_v2 rule 4b on the stack gate's pooled test-part decided predictions of the frozen design (each pair predicted by the split whose test part holds it; a pair in several test parts takes the mean z), for the full and the text-only design. The file and its hash go in config `c98.fit`; the analysis refits and refuses a mismatch | r0_v2 plan `dbadebd0` rule 4b; stack gate `confident_98` | **t98 = 0.41** (full and text-only), re-derived on the refit (B1 d), the same as the gate's: `stack_gate/refit_nf4r/results_oof_ensemble_t98.json` (sha256 `6f2708de0aba0e7f4295924666e3c035556e4efc009a13d070c2585e124fb97f`). Refit 98% rule pooled: coverage 67.5% at 98.1% |
| Threshold transfer | Thresholds are fitted on single-split out-of-fold predictions and applied to the 10-split ensemble. Averaging z over splits shrinks extreme values, so the ensemble calls fewer pairs at the same t. Stated before sealing; S4 and C98 are measured on the holdout either way | | none |
| Effect-size head | Not frozen; no effect-size claim | 8.6 secondary 3: NOT RUN | none (conceded) |
| Fallback | None inside this package. If neither STACK nor STACK_no_describe passes the stack gate, this package cannot be sealed on a stack and a new draft is written | | |

**Data flow: where holdout text goes.** Holdout text leaves the machine three ways, all public Upworthy headlines with no outcome and no label: to **Anthropic** (describe, kept; frontier arms; Batch API, in the text-only pre-collection), to **Voyage** (voyage-4 embeddings of holdout headlines, and of the 200 paraphrase null texts, for the embedding learner; runbook gap G3: `engine/lens_engine/stage9/holdout_emb.py`, sha256 `cce87a01...c752`, under the text-only amendment's `voyage` section: one text-only read, the text sha256 list sealed in `stage9_emb:UPLOAD` before the call, free tier, the pinned `voyage_embed.py` client; the per-split learners are refitted exactly as voyage_test a_fit on non-holdout data only, as the amendment says they must be since they were never saved, and must reproduce the gate's sealed learner output before any holdout score is written), and (ruling 3, 2026-10-21) to **an E2E Networks GPU instance** on the owner's prepaid account, for familiarity and recognition under the Gemma 4 31B base. The E2E route runs only on these conditions, each enforced by `engine/lens_engine/stage9/gpu_pass.py` (sha256 `06d90ace...cde2`; launcher `e2e_gpu_pass.py` `47c11254...da9a`, instance job `gpu_job.py` `3a0e6c30...f4e8`, re-pinned 2026-10-21 for the v2 launcher and again for runbook gap G5, the 200 paraphrase null pairs staged with the holdout set): (1) text only, no labels: the upload holds `{text_sha256, text}` rows and nothing else; (2) a fresh instance, deleted after the pass: the instance is named in the sealed upload entry and refused if used before, and scores seal only with the deletion confirmed; (3) the text sha256 list is sealed in `engine/experiments/stage9/gpu_pass/ledger.sqlite` before upload, and every score file must match the sha256 computed on the instance, hold exactly one finite score per uploaded text and come from the pinned scorer code. The scorers are `stage9/familiarity.py` (pinned in config `baselines.familiarity.implementation_sha256`, `ecd5935f...86dd`) and `stage9/recognition.py` (`dab4f30f...e450`, re-pinned 2026-10-21 for the degenerate-text rule in 5.1). **Text-only reads (2026-10-21, runbook):** exactly four reads of the holdout source with the planned two-pass GPU run (pre-collection build, one per GPU stage command, the voyage stage), three with a single GPU pass, each logged in `UNSEAL_LOG.txt` and each sealed (amendment `data_flow`). The non-holdout `test_part` pass ran on 2026-10-21 (GPU ledger entry `ffbf0d63...2a06`); the holdout pass runs once, after `seal-config`. The per-split adapter readouts of holdout pairs ride the same route (Emily's ruling of 2026-10-21, "same route"; amendment `gpu_pass.resolved`). The web-presence index (a route in the 10-15 draft) is dropped (5.1).

### 2.1a Learner decision tree (ruling 1, 2026-10-21)

The 8.1c NF4 per-split adapters were never saved (the Modal runs had no Volume; only readouts came back), so they cannot score the holdout. Fixed before any holdout read (`engine/lens_engine/stage9/learner.py` `decide`, sha256 `a5cf4324...1bc0`, tested):

1. **bf16 gate.** The bf16 8.1c gate (PR #99, job g81c on E2E; sealed amendment `engine/experiments/8_1c/AMEND_gemma_bf16_gate_e2e.json`, `83f63951...ddf0`) saves all 10 adapters to the Mac. If its sealed `gate_adoption_rule` gives **ADOPT_BF16** (`adoption_gemma_4_31b_base_bf16.json`), route = **bf16**: the Stage 9 learner is the bf16 10-split ensemble from those adapters.
2. **NF4 retrain** (verdict NF4_STAYS or NO_ADOPTION). Route = **nf4_retrain**: the 10 per-split adapters retrained in NF4 on E2E with the sealed 8.1c recipe and seeds (`8_1c/PLAN.json` + `AMEND_gemma_4_31b_base.json`, SEED_LORA = 81200 + split). Accepted only if **every** split's tune log-loss (selected checkpoint, after the fitted pair scale) replays the sealed NF4 value in `results_gemma_4_31b_base.json` (`5b864276...b332a`, `selection.<s>.LEARNER_selected.tune.logloss`) within **0.011088638914821092**, stated now: the sealed noise margin, 2 x pooled seed SD (`scaling/amend_gemma_4_31b_base.json` `measured_seed_spread.two_x`; per-model seed SD 0.0017 to 0.0087). Sealed values, splits 0-9: 0.22434, 0.20648, 0.22839, 0.23077, 0.24863, 0.20829, 0.24318, 0.21296, 0.21309, 0.22233. Any split outside: no admissible learner, and this package cannot be sealed on a stack (a new draft).
3. **Either way**, the stack (describe KEEP, frozen design STACK) is re-fit only as the sealed stack gate procedure specifies (`stack_gate/PLAN.json` `stacker`, the same code) on the new readouts; **Where the new TEST-part readouts come from (route nf4_retrain):** the GPU pass's non-holdout `test_part` set (`stage9/e2e_gpu_pass.py`, 2026-10-21): for each split k, split k's TEST-part pairs of the sealed 8.1b split files (`s<k>/test_jobs.jsonl`, sha256 = the 8.1c kernel's `data_manifest`; 204,762 pairs over the 10 splits), both orders, read with split k's g81n adapter in NF4 by `readout.py`, in the kernel's own order and orientation (one ordered pair file per split, duplicates kept), so the result is exactly what the sealed kernel's TEST scoring would give (CPU dry run: max abs diff 0.0 against the kernel's TEST path). Adapter pins come from g81n's ledger (`8_1c_nf4r:s<k>:retrain`, chain recomputed); staging refuses until g81n is finished and its replay rule passes. Outputs are sealed into the Stage 9 GPU ledger, all or nothing. Estimate (H200, measured scoring rates): central 1.19 h = INR 706 on-demand / INR 124 spot; slow 3.68 h = INR 2,182 / INR 382, incl. GST. `ensemble.build_frozen` rebuilds `ensemble.json`, whose sha256 fills `model.stack_sha256` (the gate's value is kept as `model.gate_stack_sha256`, `0d87a15f...6faa`). The frozen config pins the adapter sha256 list (`model.adapters.sha256`, 10 entries in split order, `learner.adapter_sha256`), and `learner.check_adapters` checks the files against it before any holdout readout. `config.validate(strict=True)` refuses a config without the route and the 10 pins.
4. **Thresholds after the re-fit (B1 d, confirmed by Emily 2026-10-21):** t98, t_S4 and the S5 target were derived from the gate's NF4 readouts, so they are re-derived with the same pinned code (`stage9_values.py`, `s4_extended.py`) from the re-fit pooled test-part predictions, before any holdout read. The familiarity scale would be refitted only if route = bf16; the route is nf4_retrain, so it stays 0.4747.

**Done 2026-10-21 (PR #112 chain, results PR #114; `research/stage9/REFIT_RESULTS_2026-10-21.md`).** g81n (route **nf4_retrain**) replayed every split's tune log-loss within the margin (max |diff| 0.009698 against 0.011089), and its 10 adapters are pinned in `model.adapters.sha256`. `engine/scripts/stage9_refit.py run` re-ran the sealed stack gate code on the g81n `test_part` readouts into a new refit ledger: **PASS_full** 10 of 10 (mean L 0.315 [0.308, 0.323]), describe **KEEP** (+0.0045 [+0.0021, +0.0071]), every predictor that does not read the scorer identical to the gate on all 23,932 entries. Re-derived values, now in the config: **t98 0.41** (unchanged), **t_S4 0.4905** (was 0.4913), **S5 target 0.8611** (was 0.8631). The refit stack is `stack_gate/refit_nf4r/ensemble.json`, **`model.stack_sha256` = `94ed011ee886033333188e917b437cf6994e4b9829d6c8b080a5c942d8e5c3bc`** (self replay: 173 per-split predictions, max abs diff 0.0). Ledger heads:

| Ledger | Head (entry) | Where |
|---|---|---|
| Refit stack gate ledger, after evaluate (seq 813711; file sha256 `867db4fb2d1a2b45ec873942991eee64769b3716cf1730331351fe55ff4c903c`) | `7035e628eaa8dfe37dc35feb2ad8a4f7cb1973dbc7a0f2ba476e45fef057101e` | `engine/experiments/stack_gate/refit_nf4r/ledger.sqlite` (git-ignored, 1 GB; written on the Mac in the `s9-run` worktree) |
| Stage 9 GPU ledger, after the `test_part` readouts (entry seq 12) | `ffbf0d634bf7a43a88e452322fd51eceb2e72fad549380dd63186483b5fb2a06` | `engine/experiments/stage9/gpu_pass/ledger.sqlite` |
| g81n NF4-retrain ledger (seq 24, all 10 splits sealed and joined) | `9277f7d265bdf7e6fcf1f04b8a5571ad8f5798cf6e17e6d89d4b37e120c3f731` | `engine/experiments/8_1c/ledger_gemma_4_31b_base_nf4_retrain.sqlite` |

Each head was checked on 2026-10-21 against a read-only copy with `prereg_check.check_ledger` (chain recomputed, entry found). The independent re-run of the refit is G9 (`research/stage9/B7b_REFIT_RERUN.md`, 7.2 B7b).

### 2.1b Arm-set rule (2026-10-23, fixed before any holdout read)

**The gap.** The text-only rebuild of the holdout arms (pre-collection, both GPU holdout stages, the voyage stage) uses **all** packages. The single outcome read (`upworthy.load_packages`) drops packages with zero impressions and exact duplicates. If every package of a holdout headline had zero impressions, that arm (and, if it leaves fewer than 2 arms, its test) is missing at the outcome read, and the `test_id:arm_idx` ids of the later arms in that test shift (a dropped first package can also re-order arms). Keyed by those ids, `sealed-run` would then fail closed **after** the one irreversible outcome read and waste Stage 9.

**The rule (`precollect.ARM_SET_RULE`, `lens.stage9.arm_set/1`; amendment `arm_set_rule`; config `datasets[0].arm_set_rule`).** An arm is identified on both sides by **(test id, sha256 of its headline_key text)**, never by its index. `runner.predict` binds the pre-collection's `{(test id, text sha256): arm id}` index to the holdout source **before** the read (`runner._bind_precollection`; a real holdout run without it refuses). At the read, every `load_packages` arm is re-keyed to the pre-collection arm id with the same key (`precollect.reconcile`, inside `sources.UpworthyHoldoutSource.items`), so every pair id, arm id and arm ref is the pre-collection's and every table built from the text-only rebuild covers it. Then, mechanically and with no dependence on any outcome:

1. Pre-collection arms the outcome read lacks (all packages zero impressions) and tests it lacks (fewer than 2 arms left) are **excluded by rule**: no pair, no arm record, no outcome. Their counts are sealed in `stage9:PREDICTIONS` (`arm_set`: pre / outcome / excluded tests and arms, arms re-keyed) and printed in the report beside the joined n, and every n of every endpoint counts the kept arms only.
2. The text-only side is a superset by construction (same eligible tests, same `headline_key`, a subset of the packages), so coverage always holds. An outcome arm with **no** pre-collection arm of the same key still refuses (fail closed), as does any arm without its table rows.
3. Kept arms keep every pre-collection value: frontier picks and scores (the picks were made among all k text-only arms; a pick of an excluded arm gives no vote to the kept arms, as an invalid pick does, which can only add ties and split credit to F1; not rescored, Emily's ruling 2 of 2026-10-23: F1 is provisional and never gated, the disclosure stays), the recognition probe (a probe answer naming an excluded arm leaves that test out of the probe rows; an 'N' answer stays a not-recognised row), describes, readouts and embedding scores (each holdout arm's voyage score was computed inside its full text-only test). Arm order within a test (`order_a`/`order_b`: the position and always-newer baselines, `b_is_later`) stays the `load_packages` `arm_idx`, as on the non-holdout data the baseline scales were fitted on. The pair id, and so the A/B slot coin, is built from the sorted pre-collection ids.
4. The spec 4.7 constructed null pairs are the staged ones (`null_pairs.jsonl`, `nulls.null_specs` on the **pre-collection** text set), loaded before the read by `frozen_models.FrozenStack.null_items` with their texts from the voyage stage's `texts.jsonl` (sha256 = the sealed `stage9_emb:UPLOAD`); they are never rebuilt from the outcome-side texts, which differ once an arm is excluded. Reading that `texts.jsonl` is a named non-source access (amendment `data_flow.non_source_accesses`, Emily's ruling 3 of 2026-10-23): a sealed-file access checked against its sha256, not a read of the holdout source, so the count of holdout-source reads stays exactly four (three with one GPU pass).

**Non-holdout rehearsal (2026-10-23, `engine/lens_engine/stage9/armset_rehearsal.py`, counts in `research/stage9/ARMSET_REHEARSAL_2026-10-23.json`; guarded loaders, `allow_holdout` never passed).** Text-only rebuild 53,181 arms in 11,969 tests; `load_packages` path 53,181 arms, 11,969 tests, 102,386 pairs; under the rule all 53,181 map to the same arms (0 excluded, 0 re-keyed) and `check_items` passes on all 102,386 items. Neither filter drops anything on non-holdout data: 0 zero-impression and 0 duplicate packages among all 140,822 non-holdout packages (the archive is its deployed tests). A synthetic holdout with a zero-impression arm, a test left with one arm and a duplicate package runs through predict and join on the frozen table stack without failing closed, and a test re-ordered by a dropped first package, with a probe answer and frontier votes on an excluded arm, runs through predict and join too (`stage9/tests/test_armset_rule.py`).

### 2.2 Stack gate (decision 3, O12)

The stack gate (`engine/experiments/stack_gate/PLAN.json`, PENDING, section 3.2) gates the stack on all 10 splits (G1-G4 of R-2026-10-13) before Stage 9 is sealed. Revised 2026-10-20, still unsealed and before any stack prediction:

- **Scorer pick:** `gemma_4_31b_base` (8.1c selection; equal to `selection.json`, so no override).
- **Capped describe budget: $65.** The union of the 10 splits' scored pairs (86,000-91,800) is sorted and permuted once with `numpy default_rng(97300)`. The **describe sample** is the longest prefix of that permutation whose new calls cost at most $65 at the expected per-pair cost ($0.001561, describe_ext `COST.json`): about 41,600 new calls, about 45-48% of the scored pairs. A prefix of a uniform permutation is a uniform random sample. The sample is written to `describe/sample.json` by `describe-jobs`, frozen, and sealed with the plan.
- **Hard cap at submission:** the driver submits in job order, in chunks of at most 5,000, and calls `chunk_allowed(measured spend, chunk size, worst per-pair cost $0.003008)` before each chunk. A chunk whose worst case would take the measured spend over $65 is not submitted. If the driver stops early, it writes `describe/stop.json`. The effective sample is then the prefix up to that point, and every later pair has m = 1.
- **Describe presence depends on the seed, to first order.** A describe that exists for a scored pair outside the sample (the r0_opus and describe_ext selection pairs) is ignored. describe_ext described decided pairs only, so using those calls would make "has a describe" carry outcome class. Two second-order residuals remain and are accepted, as the cross-fitting leak is: (i) inside the sample a pre-existing describe costs nothing, so the prefix length counts how many such (decided) pairs fall in it, and one pair's own status can move the sample boundary by at most one pair; (ii) inside the sample, m = 1 arises only from a failed new call, and the pairs that need a new call exclude the pre-existing (decided) ones, so in-sample m = 1 is slightly enriched for non-decided pairs. The 95% in-sample coverage rule bounds (ii), and the per-split in-sample coverage is reported. These residuals are stated here only: PLAN.json was sealed (`ac003b8e`) at 21:19 IST on 10-20, before the review edit that added them to it, so the sealed plan keeps its sealed bytes. In the run every new call was valid (41,221 of 41,221), so (ii) did not occur.
- **Missing-feature design:** as in 2.1. In each split's fit set, each pair keeps its describe with probability q = sample share (`default_rng(97200 + split)`), so the interaction coefficients are learnt from the same mix.
- **Describe decision (pre-registered):** gain = log-loss(STACK_no_describe) - log-loss(STACK) on decided gate items whose pair carries a usable describe, pooled, cluster bootstrap by test id (2,000, seed 9810). **KEEP** describe if STACK holds PASS_full and the gain's 95% CI lower bound is above 0. Otherwise **DROP**: the frozen design is STACK_no_describe if it holds PASS_full (the same sealed gate code, `gate_for`). If neither passes, no stack is admissible.
- **If describe is dropped,** Stage 9 sends no describe calls (row A of 2.7 becomes $0), and S2 reads "not tested: describe dropped by the stack gate".
- Collection reads no outcome and needs Hemant's yes on its figure ($65 cap) before submission.

### 2.3 Frontier arms (decision 2)

Two head-to-head arms run on **every holdout test**, sealed with the Lens predictions before any outcome is read:

| Arm | Model | Design | Expected / worst |
|---|---|---|---|
| F-Opus | `claude-opus-5-5` | zero-shot best-of-k letter pick, both orders per test (the 8.1 `frontier_arm.py` PROMPT, sha256 `1a50b6346ee8012ab83dcd6a33345d4336f60c060c5af5327132128d5e8fcdbe`), arm score = mean of the two picks; plus the 300-test recognition probe (RECOG). max_tokens 512 (Opus thinks on every choice call; disabled thinking is rejected), effort low, Batch | $5 / $9 |
| F-Sonnet | `claude-sonnet-5-5` | the same requests (the 8.1 B7 design, for continuity with dev G3) | $1 / $5 |

Endpoint F1 (5.4): paired best-of-k accuracy, Lens minus each arm. "Lens beats Opus 5.5" is said only if the 95% CI lower bound is above 0. Both arms are labelled provisional like every Upworthy number, and an arm's recognition-probe hit rate is printed beside it (a frontier model that recognises the test is an upper bound, never a fair rival).

**Dropped:** the Sonnet 8-persona x 2-order panel "comparison arm" (about $90). It adds nothing to any endpoint: S2 tests describe only. GPT-6 Astra is not an arm (it needs an OpenAI account and a card: owner's call; if added, it is added before sealing, never after).

### 2.4 Grading plans (letter-style claims)

The edge test is a one-sided exact McNemar of Lens against the strongest naive baseline (always-control, always-challenger, running base rate) on the same called tests. It runs **only** at 40, 80, 160, 320 and 640 decided calls. No look after 640 exists in either plan, and a later look needs a new sealed plan.

| Plan | Applies to | Spending | Thresholds at 40 / 80 / 160 / 320 / 640 | Canonical-JSON SHA-256 |
|---|---|---|---|---|
| `demo-obf-v1` (sealed 2026-10-14) | the three public demo sets only | Lan-DeMets O'Brien-Fleming, t = n/640, one-sided 0.05 | 4.51e-15 / 2.96e-08 / 8.85e-05 / 0.00549 / 0.04443; first realistic at 160 | `c8a05006ff91644d67c2d2a0ce595324e05916283eef979ca2e5517357fc8700` (sealed as `checkpoint_plan` in each demo ledger) |
| `customer-v1` (sealed 2026-10-14) | every non-demo replay and live account, **including Stage 9 and the B2B set** | Pocock-type, 0.05/5 = 0.01 per look | 0.01 at each; first realistic at 80 | `d0884d21345afa5cd11c86044e316c62dc42a0aef2622afe21dcd4ebdce9ffae` |

Both plans live in `app/src/lib/replay/sequential-plan.json` (file SHA-256 `bd7487ca5fb4bc6715035a8f0d2e567a9a36ea7520c5583e5d35dc7bc25d3d3f`), generated from `engine/lens_engine/replay/sequential.py`. A test already checks the two are identical. The hash is `sha256(canonical_json(plan_document(plan_id)))`, as `replay/timemachine.py` seals it. The `customer-v1` hash is carried in the frozen config (`s6.plan_sha256`), so sealing the config seals it (O7).

### 2.5 Model-change bridge set

600 pairs drawn from the 8.6 R-0 tier-1 decided pairs (already scored on the current models, never from the holdout). Rule, fixed now: sort the tier-1 decided pair ids, permute with `numpy default_rng(8130)`, take the first 600. TOST on paired log-loss, margin plus or minus 0.02 nats, 90% CI. Needed before the final adapter (or any other model) replaces the gated ensemble. **Drawn 2026-10-21 (B5)** by `engine/scripts/draw_bridge_set.py` on the Mac main tree's data: 600 of the 4,095 tier-1 decided pairs of `r0_claude/selection.jsonl` (sha256 `4b090a8e...ff1b`), every drawn pair's test checked to be a non-holdout test of the guarded `loaders.load_pairs()` (no holdout or sealed file read directly). Ids in `research/stage9/bridge_set.json` (file sha256 `ee0f60589b98227766a1f21803291da97ac263c6e2e1d8d1a47c3a917953d538`, ids_sha256 `4ebbc283bdaa2a85ec43d61f6a9b64182a88af9fc1222f25af72ce834ccd18a5`), recorded in config `bridge_set` and the manifest.

### 2.6 Post-cutoff set: growing it to 100 decided pairs (decision 7)

"Post-cutoff" means a test that **ended after June 2026** (the Opus 5.5 training cutoff, the latest of any model in the stack or the arms) **and** after the hash of its own sealed config is published. Today: **12 decided pairs** (8.7's 9 plus 3 from the 2026-10-21 growth sweep, PR #110; at the free public rate of about 4 a month, 100 is roughly 22 months away). Sources, in order of expected yield:

1. **Own-site tests** (ruling 1, 2026-10-13): headline and subject-line A/B tests on Lens's own site and newsletter, each registered in the prospective ledger before it starts.
2. **Design-partner archives**: tests that ended after June 2026, replayed through the connectors (2.8).
3. **Public archives** published after June 2026, each licence-checked (TRAIN-OK or TEST-ONLY) and registered before its outcomes are read.

Each source runs in its own config and ledger (`internal_benchmark: true` for TEST-ONLY sets). The count is reported monthly in RESUME.md. The label is lifted when the pooled prospective ledger holds 100 decided pairs; the 8.7 describe-only test (`8_7/PREREG_describe_only.json`) runs then too.

### 2.7 Credit reserve (decision 4)

Stage 9 never starts with less API credit in hand than its worst-case cost: the holdout is read once, and a run that runs out of credit halfway is lost after the read.

| Row (READINESS section 2) | Expected | Worst |
|---|---|---|
| A. Opus describe on every holdout pair, Batch (only if the stack gate keeps describe) | $28 | $54 |
| B. F-Opus | $5 | $9 |
| C. F-Sonnet | $1 | $5 |
| **Stage 9 total** | **$34** | **$68** |

**Reserve: $70.** The pre-collection build refuses unless `--credit-in-hand-usd` (read from the console just before the run) is at least the reserve of 70 USD, and it checks this **before it reads any holdout text** (ruling 4; `precollect.gate_credit`, tested; the value is sealed in `stage9_pre:BUILD`). A holdout predict makes no paid call and checks that sealed value and the pre-collection head instead (`runner._gate_paid`, tested); a prospective `pair_files` config without a pre-collection keeps the check at predict (`runner._gate_credit`).

**Credit left (ruling 6, 2026-10-21).** About **$70.26** of the promo credit is left (**unverified**: the estimated $134.60 before the stack gate, less its measured $64.34; the credit expires 2026-11-16 UTC). Stage 9's worst case is **$68**. So **nothing else may use Opus (or any other paid call on this credit) before Stage 9's pre-collection has run**: not the 8.12 BTOS describe calls, not any review or test. Any other spend needs a top-up first. The spend itself still needs Hemant's yes on the figure (O10), and the console figure read just before the build is what the gate checks.

### 2.8 B2B evidence: a separately sealed set (decision 6)

Stage 9 is consumer news headlines and says nothing about B2B buyers. B2B evidence comes from its own sealed set, never pooled with Upworthy:

- **Sources:** (a) own-site B2B tests: messages aimed at B2B buyers on Lens's site, newsletter and outbound copy, registered before each test starts; (b) **connector replay**: design partners' past VWO, Optimizely, AB Tasty or Statsig tests read through the connectors (sandbox accounts needed), graded by each customer's own recorded results. A replayed test counts as prospective only if it ended after the B2B config hash is published; earlier tests are reported separately as retrospective, flagged.
- **Config and ledger:** `stage9-b2b-v1`, its own frozen config and `engine/experiments/stage9_b2b/ledger.sqlite`, with the same model hash as Stage 9 and the same runner.
- **Pre-registered n:** at least **100 decided pairs from at least 20 tests and at least 3 accounts or sources**. Until then every B2B result reads **"pending"**, and Lens says "no B2B evidence yet".
- **Endpoints, in order:** decided-pair accuracy vs always-control (Wilson CI), with kappa; null-pair call rate under 5%; calibration slope (descriptive below 1,500 decided pairs); best-of-k L where k >= 3; letter claims only at the `customer-v1` checkpoints.
- Objection recall (8.5) stays hypothesis-only: it failed (-0.156), and no coder validated v2.

### 2.9 Publication and open evaluation code (decisions 5 and 9)

- **Where:** `docs/track-record/` in this repo, as dated commits: **the v1 package SHA-256 first** (a `package` line, after Emily's sign-off and before `seal-config`, runbook G8: the config cannot carry the package hash because the package lists the config's), then the config SHA-256 right after `seal-config` (before any prediction), the predictions head after phase 4, the final head after the join, and the stack gate's prereg hash and final head (and the refit head `7035e628...101e`). Format in `docs/track-record/README.md`. `sealed-run` waits for the typed head, which the owner pastes after the commit, and `stage9.cli publication-lines` prints every line, the `package` line included, from the files on disk.
- **Open evaluation code:** the code that turns the ledger into numbers is in this repo: `engine/scripts/stage9_analysis.py`, `engine/lens_engine/stage9/`, `engine/scripts/prereg_check.py` and `engine/lens_engine/harness/`. Its hash (`config.code_sha256()`) is sealed with `stage9:FROZEN`. Pre-set rule: the publication commit must contain exactly that code (hash match), or no Stage 9 number is published.

### 2.10 The frozen config draft

`research/stage9/FROZEN_CONFIG_DRAFT.json` is the runner's config (`stage9.cli template`, schema `lens.stage9.config/1`) with every value decided here filled in. It loads with `config.validate(strict=False)`. As of 2026-10-21 (after Emily's rulings and the refit) filled: `model.frozen_design` STACK, `s4.threshold` 0.4905 (ruling 2, re-derived on the refit, B1 d; the gate's value was 0.4913), `c98.fit` (refit, t98 0.41), `s5.target_accuracy` 0.8611 (refit; the gate's was 0.8631), `model.adapters` (route nf4_retrain, 10 pins from g81n), `model.stack_sha256` (`94ed011e...c3bc`, the refit stack), `label.post_cutoff_decided_pairs_at_sealing` 12, all five baseline scales (recognition 2026-10-21 from the sealed `recog_scale` table, B3), `baselines.familiarity.implementation_sha256` (the Stage 9 familiarity scorer, ruling 3), `frontier_arms.implementation_sha256` (`731a757c...cd3a`, the pre-collection with the credit check before its read; re-pinned 2026-10-23 for the arm-set rule, 2.1b), the M5 mapping and the confirmed 98% display rule (`emily_confirmed`), the credit note (ruling 6), and (2026-10-21, branch `cloud/s9-b356`) `bridge_set` (B5) and `model.readout.implementation_sha256` (the readout the GPU pass runs). TODOs left (1): `baselines.recognition.scale` (GPU Min-K% pass, B3; PR #115) and `datasets[0].holdout_sha256` (B9). No other string in the config carries "TODO" or "DRAFT" (cleared 2026-10-21, G4; tested by `test_frozen_config_draft_has_no_stale_draft_or_todo_strings`), because the config is sealed as written. `seal-config` refuses while any TODO remains, and `config.validate(strict=True)` also refuses a config without the route and 10 adapter pins.

### 2.11 Survey share, attention, conceded items (unchanged)

- **Survey share** is a separate prospective track, already sealed: `8_12/PLAN.json` (`274861dc...`), router = last wave if the question recurs from a TRAIN-OK source, else tabular if library cosine >= 0.90, else LLM blend (w = 0.5). 213 items over 6 releases; verdict once, after Edelman 2027 (about 2027-01-17 to 01-19). BTOS describe deadlines (10-21, 11-04, 11-18, 12-02) in `build/notes/s8-12.md`.
- **Attention:** 8.10 PASS on UEyes test (CC 0.660 vs 0.433, +0.226 [0.208, 0.246]); ships as `--backbone random` (also PASS) unless counsel clears the ImageNet start. No Stage 9 attention claim.
- **Conceded or hypothesis-only:** objection recall (8.5 FAIL), sycophancy (v2 gap 0.028 [-0.014, 0.069]; a raw panel verdict is never shown as a prediction), purchase intent.


## 3. Every plan hash and ledger head recorded in RESUME.md

These values are copied exactly as RESUME.md writes them (some are abbreviated there). The full value is what this repo's file hashes to today.

| What | RESUME.md says | Full value | Where |
|---|---|---|---|
| 8.11 analysis plan | `4057be4f` (line 3) | `4057be4f9a5621bdce3d18e5a5235e4dec5df47795fadbd5af9fcf0b402b5cb2` | `engine/experiments/8_11/ANALYSIS_PLAN.json` |
| 8.6 analysis plan (R-0 + 8.8) | `2c4bb8d3` (line 12) | `2c4bb8d30431ec2ad0b4ca19261580a4e9e9c3364780de4f6371211fc2f6130c` | `engine/experiments/8_6/ANALYSIS_PLAN.json` |
| Bake-off plan | `432ebf73…298c` (line 132) | `432ebf73f7bc2b997624492871b4e6ba0aa19824020d1289ba40845e5659298c` | `engine/experiments/bakeoff/PLAN.json` |
| 8.10 plan | `07076ddf…5998` (lines 134, 141) | `07076ddf1b58ad8b805ff717385de72d73caf21093060d7c402d047bc5745998` | `engine/experiments/8_10/PLAN.json` |
| 8.5 plan | `154f78c2…c848` (line 134) | `154f78c2c4bded3d26f1359803aa34a8286a2e5b12647491c1addfafd81dc848` | `engine/experiments/8_5/PLAN.json` |
| 8.5 v2 plan | `d5c508b4…` (line 146) | `d5c508b4fdde419ec653dbc3fc2d44f1af742abde63dfcbb55e5bc57bb1af662` | `engine/experiments/8_5_v2/PLAN.json` |
| 8.12 plan | `274861dc…` (line 152) | `274861dc35c47c79f4b5789e43a3e7c62c789c9ce532ded6c95453e32ad65eb2` | `engine/experiments/8_12/PLAN.json` |
| 8.1b zero-shot kernel (amendment seq 287197) | `e418179e…b54b` (line 137) | `e418179e2c8197a6ef36c0002e84e9cec09f985ded8322e4eb994013c986b54b` | `engine/experiments/8_1b/kaggle/zeroshot/lens_8_1b_zeroshot.py` |
| 8.1c plan | `7b42b577…5871` (2026-10-15 ~12:45 IST, 8.1c PREP DONE) | `7b42b577c604c242fd2140b8076eb924f5f0458c2e5f5fec4ae3812814d75871` | `engine/experiments/8_1c/PLAN.json` (prereg:8_1c, entry 1 of each 8.1c ledger) |
| 8.1c kernel body (`RUN = None`) | `fb256abd…` (same line) | `fb256abdac81718cac3e8b17318cac68cf5063c0fca267aa34da18d021a87709` | `engine/experiments/8_1c/kernel/lens_8_1c.py` (8_1c PLAN `sealed_files`) |
| Voyage test plan | `018e445f` (2026-10-15 ~13:30 IST, VOYAGE TEST) | `018e445f63f87fb0d1b2321214be96e8f92f3965f00a1c3a84ce3fc91f7a7903` | `engine/experiments/voyage_test/PLAN.json` (voyage_test ledger seq 1 `plan_sha256`) |
| 8.12 ledger head after the BTOS describe baselines (seq 936) | `a0f7ad81…` (2026-10-15, 8.12 BTOS SEALED) | `a0f7ad81c7b9374d8514d388c5e028d94382841c4a54cc9c24908ab455318bca` (verified on the Mac 2026-10-16: verify ok, 936 entries) | `engine/experiments/8_12/ledger.sqlite` |
| 8.1c amendment: Gemma-4-31B-Base second candidate | `6aca4f23…` (2026-10-15 ~18:55 IST, 8.1c AMENDED) | `6aca4f23ee39a09367017a1c203f9a3c8df092d493c45f52b6f7213fedd06085` | `engine/experiments/8_1c/AMEND_gemma_4_31b_base.json` (amend_sha256 in 8_1c ledger_qwen3_14b_base seq 3 and ledger_mistral_small_24b_base seq 3, sha256 in ledger_gemma_4_31b_base seq 3) |
| 8.1c Gemma kernel body (`RUN = None`) | `55e70363…` (same line; 2026-10-15 21:15 IST) | `55e70363bb9c71eb41ffe0f456c70ddf5ec426d88c63236fa1c169d50d58d094` | `engine/experiments/8_1c/kernel/lens_8_1c_gemma31.py` (kernel_body_sha256 in ledger_gemma_4_31b_base seq 3 and 4) |
| 8.1c amendment: Gemma venue Modal L40S | `9eb24878…` (2026-10-15 21:15 IST, 8.1c GEMMA on Modal L40S) | `9eb2487884d41a1547ebba27b8b8de56c69932b7950117cd5974cb40ad7a816e` | `engine/experiments/8_1c/AMEND_gemma_modal_l40s.json` (ledger_gemma_4_31b_base seq 4) |
| 8.1c Gemma ledger head, all 10 splits + familiarity sealed (seq 311140) | `10bafc7f…44f1` (2026-10-15 22:45 IST, 8.1c GEMMA ALL 10 SPLITS) | `10bafc7fbdb510f0169f6b61bfe73f2acf37b79288241da92c08b3c6a86444f1` (verified on the Mac 2026-10-18: verify ok, 311140 entries, opened read-only) | `engine/experiments/8_1c/ledger_gemma_4_31b_base.sqlite` |
| 8.1c amendment: origin rule removed (R-2026-10-19) | `c5e10d04…5bac` (2026-10-19, 8.1c select, PR #79) | `c5e10d04b7845d781620b578351732e4aea75c4261452fd73572d54f375d5bac` | `engine/experiments/8_1c/AMEND_origin_rule_removed.json` (sha256 in every 8.1c ledger at `amendment:8_1c:origin-rule-removed:2026-10-19`: qwen seq 311135, gemma seq 311142, mistral seq 5) |
| Ruling R-2026-10-19 (origin irrelevant) | `2ce5e63a…d20e` (same) | `2ce5e63ac4a1b442f4d7ee3e3aa2cb0762db5df5b1e4f295fdaaad319a27d20e` | `research/accuracy/rulings/R-2026-10-19-origin-irrelevant.md` (ruling_sha256 in the amendment above) |
| 8.1c ledger heads right after the origin amendment (before any join) | qwen `8e37dc66…`, gemma `048badae…`, mistral `44d338a4…` (2026-10-19, PR #79) | qwen seq 311135 `8e37dc66923d0c1fd3485cfc25f3e1c0d5382c784a0c9fa70f7cd04e44a242c8`; gemma seq 311142 `048badae7511a39456bad8d5e2bbfc98b491e1521d84c597175ebe6e523de4e7`; mistral seq 5 `44d338a406ab1a823ce303fe7d4e95f05701c439e729207a8e2a01b91567e482` | `engine/experiments/8_1c/ledger_<model>.sqlite` |
| Sealed holdout id list | `1c62e0c5...ce77` (line 35) | on the Mac only | `data/sealed/HOLDOUT_SHA256.txt` |
| R-0 Claude ledger head | `bb0bbce0...3dbc0e` (line 56) | on the Mac only | `engine/experiments/r0_claude/ledger.sqlite` |
| R-0 Opus ledger head | `0c66bb4f` (line 56) | on the Mac only | `engine/experiments/r0_opus/ledger.sqlite` |
| Bake-off ledger head (2 entries) | `c714b103…b2ca` (line 132) | on the Mac only | `engine/experiments/bakeoff/ledger.sqlite` |
| 8.1b head at 6 of 10 splits | `dd1c4d65…` (line 136, "results.json head") | on the Mac only | `engine/experiments/8_1b/ledger.sqlite` (assumed: RESUME calls it the results.json head; if the checker cannot find it in the ledger, check whether it was a results.json field) |
| 8.1b modal amendment | seq `287198` (line 142), no hash given | on the Mac only | `engine/experiments/8_1b/ledger.sqlite` |

Not a hash: `af33feca` (line 132) is an agent id. Not a prereg hash: the LMArena WebDev data file sha (2026-10-15 ~20:10 IST) is a download checksum; RESUME.md writes it as `data-sha256 18491f45…`, a marker `prereg_check.resume_hash_prefixes` skips.

### 3.1 Other sealed values (from RESULTS.md, sidecars and plans, not in RESUME.md)

| What | Value | Source |
|---|---|---|
| 8.1 candidates | `8e70ceabd49fdcbffd86f22e95ead2324b9bd998ba872230e8f196d0fd1879a2` | 8_1/RESULTS.md, CANDIDATES.sha256 |
| 8.1b candidates | `d4630a71a8aece5887b45cf007936dc4a96b53b6153967737c6ddfcfb3dca995` | 8_1b/CANDIDATES.sha256 |
| 8.6 recognition amendment | `c00917b15fb9c726514c34197f4d809a860b64291a5b6392cb078b5d9fc5da31` | this package |
| 8.7 plan | `a661e310ffe4800795755ba092ea82b3ed569a0a286a1a00231bb7951b90250f` | 8_7/PLAN.sha256 |
| 8.7 describe-only pre-registration | `461e18794ddb6477b2d11b207e4d4e99549191c1024845ce019259f56b1157c8` | 8_7/PLAN.json |
| 8.12 refit | `ea1b7e4672e2cd362af94f7524865804b20985327daa70233a728176fe61faa4` | 8_12/PLAN.json |
| describe_ext plan | `4bbbc2b2c106934e48036518031fce8d4b826cbfba5811b03eb87e5f012beb62` | describe_ext/PLAN.sha256 |
| R-0 Claude plan | `9b0a5cc9432602bfedcff5b0a2100f1241d8431cde0afc85ceebc6bc0daa1ecf` | r0_claude/PLAN.sha256 |
| R-0 Opus plan | `ac3a57218e0df4bbdef1603bf75575b484950824ae20822174b31365a18d3ab2` | r0_opus/PLAN.sha256 |
| R-0 paraphrase plan | `df23576a3622499ebae5d8791a728f6791324fd02dac1fed85b89a15c83e508d` | r0_paraphrase/PLAN.sha256 |
| Survey retrospective plan | `66cd06ba63f34956e6f752ba698d20ee409d1cf58225b0441ba6389e669f4f48` | survey/RESULTS.md |
| Grading plans file | `bd7487ca5fb4bc6715035a8f0d2e567a9a36ea7520c5583e5d35dc7bc25d3d3f` | this package |
| 8.1 ledger head | `0f1c5b21...acea` | 8_1/RESULTS.md |
| 8.1b ledger head, 9 splits | `0ef83ba755e4c0691e46abdb9c673b9c768040b3ceec2ad82d64fbef5bbf5d1d` | 8_1b/results.json |
| 8.1b amendment seq 287197 entry | `0793173d5255dc8e4d4943f278a399ec3c9dff1241e6f6e3976d1598d68df5e4` | build/notes/s8-1b-lora.md |
| 8.6 ledger head | `171cbfcc2a5fc82cab36955845a9bb62993833cef879e05a25f5653ab0098897` | 8_6/RESULTS.md |
| 8.7 describe-alone FROZEN entry | `7392a2d5…` | 8_7/DESCRIBE_ALONE_RESULT.md |
| 8.10 test-prediction seal (seq 5) | `19fa7315` | 8_10/RESULTS.md |
| 8.11 ledger head | `d1ae84b1bee98f1e2cd0f4ef909cef7e37c23c2e6670990aa3a08b53bd68b8e8` | 8_11/RESULTS.md |
| describe_ext ledger head | `f27d7db0e1035e0f4b2e1d73b9abd5b9c9a8344550fc9ce7687d0cfe86d48c78` | RESUME.md 2026-10-15 describe_ext DONE (head given there only as `f27d7db0…`; full value from the manifest) |
| R-0 v2 PLAN.json | `dbadebd0b3f581a8c9e3dc3bda89ce5f085763a377eface99927bdcc30e6928c` | r0_v2/PLAN.json, RESUME.md 2026-10-15 |
| TPU spike PLAN.json | `3dfff8f46647b78dffc9ada925ae1faa090bf71df34e2543b2513eef18caa79e` | tpu_spike/PLAN.json |
| TPU spike kernel (amendment) | `ed1d402c95fa609881faf9fa17fdaa9670a306e01e7912cf6a1cb1e3c25be3fb` | tpu_spike ledger entry 2 |
| Survey ledger head | `af559f4fec142000ba3ad7be0284e8fbccfffb13b0c5c24b7a3a5c1abadc5dca` | survey/results.json |
| Scaling plan | `c0c13f5d680ecbf012e1d39d425775b681d8b169dda6a2d3106ed5f3efe714dc` | scaling/PLAN.sha256; scaling ledger seq 1 (prereg:scaling) |
| Scaling driver `scaling.py` | `48f42101cc83e1baaf93a396d34a9df82693fc3786b2d79561141d6867cf6332` | scaling ledger seq 1 `driver_sha256` |
| Scaling amendment: Qwen3-8B-Base control | `4f99a4a6875db7d67cae7d915917b035a3b1f9d4e599b1198e30966989ada11b` | `scaling/amend_qwen3_8b_base.json`; scaling ledger seq 9 |
| Scaling amendment: Gemma-4-31B-Base screen | `1d551d6d2443781583e12fed8c018a66d7e39341e521a900bda5d1e113482242` | `scaling/amend_gemma_4_31b_base.json`; scaling ledger seq 18 |
| Voyage embed driver `voyage_embed.py` (after amendment 2) | `4ffd4c61354821f5d706872551caee472bf0af10ada79126f9d07a95238b87f2` | voyage_test ledger seq 3 (`vt:AMENDMENT:2:empty-headline`) |
| 8.5 ledger head (seq 5, `8_5:RESULTS`; B6) | `c8e02af7a7504ee2781045ab71b31eb3dd4b0890d17b8820463f737699310775` | copied 2026-10-21 from the Mac's `engine/experiments/8_5/ledger.sqlite` (opened read-only; chain recomputed from genesis: 5 entries, intact) |
| 8.5 v2 ledger head (seq 14; B6) | `1eacbcadf7dcbee824ea53585ce6c92ebc84ca7eda2d255ef7c7d66dbf412574` | copied 2026-10-21 from `engine/experiments/8_5_v2/ledger.sqlite` (read-only; 14 entries, intact) |
| 8.7 ledger head (seq 619, the describe-alone outcome after the FROZEN entry seq 618; B6) | `10e23f3ec37c459c765334cd8546d67e6357720c18139ff9a4059f337436a274` | copied 2026-10-21 from `engine/experiments/8_7/ledger.sqlite` (read-only; 619 entries, intact) |
| 8.1b final ledger head (seq 531329, after the last outcome join; B6) | `32bcf66ee5d68a4f459c4d11934df8470c2118462c67838326d6d3325e036544` | copied 2026-10-21 from `engine/experiments/8_1b/ledger.sqlite` (read-only; 531,329 entries, intact; the 6-split, amendment and 9-split values above are entries 287196, 287197 and 473894 of the same chain) |
| Bake-off final ledger head (seq 39; B6) | `70dc77b13c93c0ee969571f8e1dbe3549620aa6240e3733ce6f4a290b47df74e` | copied 2026-10-21 from `engine/experiments/bakeoff/ledger.sqlite` (read-only; 39 entries, intact; RESUME's `c714b103…b2ca` is entry 2) |
| Stage 9 bridge set (B5, O3; 600 pair ids, `default_rng(8130)`) | `ee0f60589b98227766a1f21803291da97ac263c6e2e1d8d1a47c3a917953d538` | `research/stage9/bridge_set.json` (drawn 2026-10-21 by `engine/scripts/draw_bridge_set.py`; ids_sha256 `4ebbc283bdaa2a85ec43d61f6a9b64182a88af9fc1222f25af72ce834ccd18a5`; config `bridge_set`) |
| Stage 10 sealed plan `research/stage10/PLAN_v1.md` | `8ae8d938145c7872f9d4260d3197c60c457c48513009d1a9d4871792ced4008c` | `research/stage10/PLAN_v1.sha256`; stage10 ledger seq 1 (`prereg:stage10`, entry hash `55326f7224316ae3de2a9e25084612dc24cc3bf7cd375e518e346b44bc8682da`), with the stimuli `MANIFEST.json` (`4d0281b76e33637bc1b9f60f6b02ef2d8e07c9ad98aff7b2398c9138e9e854b3`), the 24 persona cards and the analysis code (`plan.py`, `prompts.py`, `aggregate.py`, `report.py`, `panel-rule.ts`), each also a `files` entry below |

All PLAN.json files in the repo hash to the values above today, and every `PLAN.sha256` sidecar agrees (checked 2026-10-15 in this session). The 8.5, 8.5 v2, 8.7, final 8.1b and final bake-off heads (O8) were copied on 2026-10-21 from the Mac's ledgers, opened read-only, each chain recomputed from genesis and intact (rows above, manifest `ledgers`; B6 closed). The 8.12 head above is the head after the BTOS baselines; later 8.12 entries do not change it.

The 8.1c, scaling and voyage_test rows were added 2026-10-16 (the 8.1c Gemma kernel body and Gemma ledger head 2026-10-18) from the files in this repo, each checked against its ledger entry on the Mac (`lens_engine.harness.ledger.verify` ok on every ledger named, opened read-only).

Stage 10 sealed inputs (added 2026-10-19 when `research/stage10/PLAN_v1.md` was sealed as entry 1 of `engine/experiments/stage10/ledger.sqlite`; the ledger was verified on the Mac, 1 entry, chain intact). The plan and its stimuli manifest are the Stage 10 row of the table above; the analysis code and the persona cards it seals are:

| File | SHA-256 |
|---|---|
| `engine/lens_engine/stage10/plan.py` | `167c1a688c285ce18d48596ddf6898a3108fc6327511173f9d4c55a04e5cff41` |
| `engine/lens_engine/stage10/prompts.py` | `964ed85a02f285e880480aed95bda3a34680f5dbf12648a207181e6b8afa0c07` |
| `engine/lens_engine/stage10/aggregate.py` (after amendment 1; `dbab0719...f236` in PLAN_v1) | `3e461fd40da08fc7feb5b2954f2526b4e75364ccd78d48a4de5e1cf259e3b279` |
| `engine/lens_engine/stage10/report.py` (after amendment 1; `722b7186...d90a` in PLAN_v1) | `a4fd862054149cfb2c085f73bbac0476cc7f20a5c0cca56764041eba3d228ea7` |
| `research/stage10/AMENDMENT_01.md` (amendment 1, written 2026-10-19 before any Stage 10 request was sent; to be sealed as `prereg:stage10:amendment-01` by `seal_stage10.py amend` before the pilot) | `d07a1efd6eb2dc4f8c4eeeb7809107aa34c82239044da9df5aada450f06867db` |
| `app/src/lib/panel-rule.ts` | `777a8d74fce8f6addd258e2e87bb77b795ca33e2780004a38007a3a26fc2b2f1` |
| `research/stage10/personas/p01.json` | `c5ef3bb3a4e2fd28683afe47a770dda6265aaf72f071eb787a4469a524256c92` |
| `research/stage10/personas/p02.json` | `c7eb94de9f4edd7a3a10307f5beddb55231c8c5d48a034bcf178472849d445c0` |
| `research/stage10/personas/p03.json` | `2c628ff1f0ab11b6381e62eba82e79d6fa58f589596a9a6b19a6de9bd212e297` |
| `research/stage10/personas/p04.json` | `4f3b33f574ab44262fa044e056b99bc5f3efad9e7e59cb6d6260a686ed7d4c3b` |
| `research/stage10/personas/p05.json` | `c2bd6e8174feca6973fcaa440d94f5622c41726e6a4fa7098fd21aed8c4401de` |
| `research/stage10/personas/p06.json` | `41fdbb03bc0951e0eab3500e08b82699c16122c68b845cc120e5b68766f437e8` |
| `research/stage10/personas/p07.json` | `a737f94f1fda537173bb244af7092b8d70bbfb1bca45e8eedf1207bd27ba9f9b` |
| `research/stage10/personas/p08.json` | `6f0ca3dcc6819418beb8fdf170a5d7599fb8a2ac515ef30480f8022e961aeb6b` |
| `research/stage10/personas/p09.json` | `e810dee26549371bd665cfbbde8471df59daf5198ac8548f0a3de5d56b3476f2` |
| `research/stage10/personas/p10.json` | `478f2a24f533d47cc02dc6ab07a01b693e01f4281030405d8a04b66518453089` |
| `research/stage10/personas/p11.json` | `80f52f589486fe032f1d8ab7a71805862dd452cdf741758bbff0e71270fed0c8` |
| `research/stage10/personas/p12.json` | `cee63d2f448275233081bb3a436fb35bc5144588d0c77a202c2d1407702f916b` |
| `research/stage10/personas/p13.json` | `2907e23abb9f3907d3c8198e20113b1f332560cd70f9026af71e72c952ef04f9` |
| `research/stage10/personas/p14.json` | `13833b3b39c7092aa6df33a156b8845d3784f6d0b6fbe3a25b90052092412504` |
| `research/stage10/personas/p15.json` | `5a33309f5f140cdf70a75d3c260c0059f4a3cfa2b89cf3e220e066fa6f9a8cfe` |
| `research/stage10/personas/p16.json` | `377f469de4d042c812cba5a41ed289cdb31ba2eec33b1a2a19d9412ba7669686` |
| `research/stage10/personas/p17.json` | `37de2c13a99ca13ec54ab7836cdc59ccf694f70d3c23e1629ec55da339af4033` |
| `research/stage10/personas/p18.json` | `22637b5d43dcad6096012386eb9ac56c714ede9f21d92da8688cf0530abd67e6` |
| `research/stage10/personas/p19.json` | `f420b658f87365fec53376328fe4c65e659107293708a622eec20ed68d717f74` |
| `research/stage10/personas/p20.json` | `c2d40e98ad2a2b93a170ef99f86b22406b9348ca47b6527b8418cffec7f5536f` |
| `research/stage10/personas/p21.json` | `6ae6409d04b982c81afcf6c6f191f088f5fca48c5b78b6c132e4f409c6aa8b42` |
| `research/stage10/personas/p22.json` | `8f5f935b7007083ad1e34841ec10b617cee767134bf67b99cb3ae29211cca909` |
| `research/stage10/personas/p23.json` | `dc72b19135287fb437b179ba3bee203ed18310161171d9432a83ec520fb074a9` |
| `research/stage10/personas/p24.json` | `683a04105993872e2eaed91cfce5edac04dbf0de79cb5bc66a37a94d5e326f9c` |

### 3.2 Pending plans (unsealed drafts, no hash yet)

A pending plan is listed so the checker knows it exists, but it has **no hash** until the Mac seals it. `prereg_check.py` reports it as SKIP ("PENDING"), and as FAIL with `--strict`, so this package cannot be sealed while one is pending. When the Mac seals it, its entry moves from `pending` to `files` with the sealed SHA-256, and a row is added to section 3.

| What | Status | Where |
|---|---|---|
| Stack gate plan: full 10-split G1-G4 gate of the production stack | **SEALED** 2026-10-20 21:19 IST, before any paid call: `ac003b8e2b6a6c04bb49f18c6f7453358f4ce367840f5753965d0cf7fa4ba60b` (prereg:stack_gate; re-sealed unchanged at 22:26 IST after the first run's folder was deleted, see `recover_2026_10_20.py`). Prereg head `a8d1e17f6bf21fc4a46744ec03fdbc085adfb8e4385302a61b7d6d4515ae939e`, final head after join `55a8701c7e2105aa8e84ee35fa16220c8957598f596f1887367683cc1a07e6a7`. Result: PASS_full 10 of 10, describe KEEP (RESULTS.md) | `engine/experiments/stack_gate/PLAN.json` |
| Stage 9 frozen config (the runner's config, section 2.10) | **RECORDED** 2026-10-23 (runbook step B, B9: `fill-holdout-sha256` filled `datasets[0].holdout_sha256`; no TODO left): `b755abe15e295c7179f03a4ecdb3f19e952107ab56f820dae12e36163594f38f` (stage9:FROZEN_CONFIG; moved from `pending` to `files` in step C). `seal-config` seals this file as `stage9:FROZEN` (entry 1 of `engine/experiments/stage9/ledger.sqlite`) | `engine/experiments/stage9/FROZEN_CONFIG.json` (byte-identical copy of `research/stage9/FROZEN_CONFIG_DRAFT.json`) |
| Text-only pre-collection amendment (phase 2b and the E2E GPU route, B4) | **APPROVED** 2026-10-23 (B4: Hemant, owner, in chat; `approved_to_run` true, committed): `a4c7fdef6a5a45a8b17d1e12db5e13239569013860440a241df9bf62650b154b` (stage9:AMEND_text_only_precollection; moved from `pending` to `files` in step C) | `research/stage9/AMEND_text_only_precollection.json` |

### 3.3 Holdout text fingerprint (amendment 2026-10-20; run once, output recorded)

The final training mixture (PR #83; current version `data/mixtures/lens-final-mixture-2026.10.20-4` (`final_manifest.json` SHA-256 `49182f6a2c5c49b990219486913a4d7b39386c78c5cab44a143da03e52f2b0fc`; on the Mac only)) can claim it excludes the Stage 9 holdout only if its leakage guard holds a text-hash list of the holdout headlines. Only `lens_engine.stage9` may read holdout rows, so the list is written by a Stage 9 tool under its own amendment. Owner approval 2026-10-19 (relayed). The tool reads no outcome column, prints counts only and writes hashes only. It refuses to run until `approved_to_run` below is set to true by the reviewer, and it runs once.

| What | Value | Where |
|---|---|---|
| Amendment | `27faf9f6b7880a70e706ca14d56995e1564826cda23997aa78b4226160d7b224` | `research/stage9/AMEND_holdout_text_fingerprint.json` |
| Tool | `ccb58ed739da100f21a6952a0d38ab553609aa34247766d996fbe6a4516ccbed` | `engine/lens_engine/stage9/fingerprint.py` |
| Output (hashes only) | c5956ea51b88a554037ffd39c00399de032da4b0a726522bb39b2359e180705a | `data/sealed/manifests/holdout_text_sha256.txt` (on the Mac only; the tool's `--record` fills this cell and the manifest) |

Run, from `engine/` on the Mac: `python -I -m lens_engine.stage9.fingerprint check`, then `python -I -m lens_engine.stage9.fingerprint run --confirm-holdout-fingerprint --record`. Changing the tool or the amendment changes these hashes, and the checker and the tool's own tests then fail until both are updated here.

## 4. Stage 9 run: phases and safeguards

The runner is `engine/lens_engine/stage9/` (the only package the guard lets unseal); the analysis is `engine/scripts/stage9_analysis.py`. Each phase refuses to start unless the previous phase's ledger entry exists. Every safeguard of the 10-15 draft is kept: the **single holdout read** (prediction and join in one `sealed-run` process; one release per source), the **sealed-run process** (config hash published before real data opens; `--confirm-stage9`; typed head before the join), and the **guard** (`guard.check_access` admits frames under `lens_engine.stage9` only and logs to `data/sealed/UNSEAL_LOG.txt`; `allow_holdout` is passed nowhere else).

1. **preflight** (no holdout read). `prereg_check.py --strict`: every hash in this package matches, every ledger verifies, no pending entry is left. `HOLDOUT_SHA256.txt` against the published value. The v1 package hash is published first as a `package` line under `docs/track-record/` (G8). `seal-config --package research/accuracy/PREREG_PACKAGE_v1.md` seals the frozen config as `stage9:FROZEN`, the first entry of a **new** ledger `engine/experiments/stage9/ledger.sqlite`, with the code hash and the package hash (`package_sha256`). It refuses the holdout config without the signed v1 package or with an unpublished package hash (`runner.seal_config`, `stage9/publication.py`, tests `test_publication.py`). The config hash is published under `docs/track-record/` (2.9).
2. **credit check (moved by ruling 4, 2026-10-21; built).** `--credit-in-hand-usd` >= $70 (2.7), checked by the pre-collection build **before its holdout text read** (`precollect.gate_credit`; the value is sealed in `stage9_pre:BUILD`). Phase 2b makes every paid call, so `predict` (which then makes no paid call) checks the pre-collection head and that sealed credit value instead of a new figure (`runner._gate_paid`). Otherwise a run that spent up to $68 in 2b would be refused at predict, or would need a second top-up.
2b. **text-only pre-collection** (needed if describe is kept, and for the frontier arms). Built like the fingerprint tool: a Stage 9 module reads headline text through the guard with `with_outcomes=False`, builds the describe and frontier requests, sends them by the Batch API and seals every parsed result in its own ledger. Its head is recorded in the `stage9:PREDICTIONS` manifest, and `sealed-run` fails closed if any result is missing. Arms are matched to the outcome read by the arm-set rule (2.1b), never by index. This reads no outcome, so R11 is not touched. It needs its own sealed amendment (READINESS 3.1; `AMEND_text_only_precollection.json`, approved in substance 2026-10-21, kept unsealed) and Hemant's yes on its figure. The same amendment carries the E2E GPU pass on holdout text (familiarity and recognition, ruling 3; 2.1 data flow): its tables go in through `familiarity.TableFamiliarity` and `recognition.TableRecognition`, and the GPU ledger head is recorded beside the pre-collection head. **Built 2026-10-21 (runbook gaps G1, G2, G3, G5, G6, G7, branch `cloud/s9-gaps-a`):** `cli assemble-tables` (`stage9/tables.py`) writes the stack's table folder from the sealed GPU tables, the sealed pre-collection and the sealed voyage route only, and the folder's manifest records the GPU pass head, the pre-collection head and the voyage head; `stage9/frozen_models.py` holds the zero-argument factories `sealed-run` takes (`frozen_models:stack`, `:familiarity`, `:recognition`, `:probe`), each refusing before the holdout read unless every table, `ensemble.json` and the ledgers match; `runner.predict` runs the coverage check (`tables.coverage`, also `cli rehearse`) before the read and seals `gpu_pass_head` and `tables_manifest_sha256` in `stage9:PREDICTIONS`. The spec 4.7 constructed null pairs carry their own arm ids and table rows (the 200 paraphrase pairs are read out on the GPU route; identical pairs have readout 0 by construction). The scrambled-instruction probe is deterministic word counting (`frozen_models.WordCountProbe`, `str.split`, no model call: the package names no model and predict makes no paid call), so that row checks the harness, not a model; Emily's ruling 2 (2026-10-22) keeps it as spec 4.7 defines it and the report labels the row a harness check. Emily's rulings 1 and 3 (2026-10-22): each null pair is scored as its own two-arm test (a failure of the paraphrase row on that is reported as a finding), and the voyage learners are refitted under an exact-reproduction check (same pick, same pair scale, test-part scores within 1e-9 of the gate's staged pickle) that runs on all 10 splits before any holdout embedding is scored.
3. **predict** (`stage9.cli sealed-run` -> `UpworthyHoldoutSource.items()` -> `stage9.access.holdout_pairs()` -> `loaders.load_pairs(allow_holdout=True)`). Outcome columns are split off at once and held back; predictors see blind items only. The ensemble, familiarity and recognition scorers and the probe run; frontier picks are read from the pre-collection ledger. One prediction is sealed per pair (p, p_text, baselines, familiarity gap) and per arm, then the manifest with the prediction-side null tests. The head is published.
4. **join** (same process): outcomes released once, after the typed head equals the sealed head. A second join is refused.
5. **evaluate**: every number from `ledger.joined()` after `verify()`; spec 4.7 null tests first (no endpoint exists unless all pass); endpoints in the fixed order of section 5; cluster bootstrap by test id, 2,000 resamples, seed 9000.
6. **report**: `RESULTS.md`, `results.json`, `REPORT.md`; final head published under `docs/track-record/`.
7. **independent re-run** (spec row 8.13, O9). Before the holdout is touched, a second reviewer (nina or an isolated agent) (a) re-runs `run_stack_gate.py evaluate` and `report_stack_gate.py` from the sealed stack gate ledger and gets identical numbers, and (b) runs the Stage 9 ensemble implementation on 200 non-holdout scored pairs drawn with `default_rng(9200)` and matches the stack gate's sealed per-split predictions to 1e-9 (per split) and their mean (ensemble). The holdout run uses the same code hash.

### 4.1 Reproducibility: pinned environment (from the B7 re-run, 2026-10-21)

`engine/pyproject.toml` leaves its dependencies unpinned. The B7 re-run (`research/stage9/B7_INDEPENDENT_RERUN.md`) reproduced every stack gate number byte for byte with the environment below. A later re-run of the stack gate or of Stage 9 should pin it. These are the same Python, numpy, scipy and pandas versions as the main tree's venv that produced the original outputs.

Platform: macOS 27.0.1 (build 26A434), arm64, CPU only, Python 3.14.5. Venv: `python3 -m venv .venv && .venv/bin/pip install -r requirements-b7.txt && .venv/bin/pip install --no-deps -e .` (from `engine/`), with `requirements-b7.txt` holding:

```
cffi==2.1.1
cloudpickle==3.1.2
cryptography==50.0.2
iniconfig==2.3.1
joblib==1.6.0
narwhals==2.27.1
numpy==2.5.4
packaging==26.3
pandas==3.0.6
pluggy==1.7.0
pyarrow==26.0.0
pycparser==3.11
Pygments==2.21.0
pytest==9.1.1
python-dateutil==2.9.0.post0
scikit-learn==1.9.1
scipy==1.18.1
six==1.17.0
threadpoolctl==3.7.0
```

Output of `pip freeze --exclude-editable` in the B7 venv. The numbers depend directly on numpy, scipy, pandas, scikit-learn and pyarrow. The rest are their dependencies plus pytest.

## 5. Published bars (fixed before Stage 9; one primary, secondaries in order)

| # | Endpoint on the sealed holdout | Bar | Source |
|---|---|---|---|
| **P** | Best-of-k normalised lift L = (acc - chance)/(1 - chance), chance = mean 1/k on the holdout | **L >= 0.171 on the 95% CI lower bound** (`pass_rule: ci_lower`). Parity with LOLA claimed only if the CI lower bound is >= 0.198. Quoted with our chance line beside it, never an absolute % next to LOLA's | R-2026-10-13-chance-line |
| S1 | Learner (p_text) beats position, length, always-newer, familiarity and **recognition** baselines | paired cluster-bootstrap CI > 0 for each | spec 4.3, 4.7; draft changes 5.1, 5.2 |
| S2 | Panel gain: log-loss(text) - log-loss(text + describe), decided pairs | KEEP if CI lower > 0; DROP if CI upper < 0.0075 nats; else undetermined. If the stack gate dropped describe: "not tested". S2 is then skipped in the fixed sequence: it is not claimed and does not stop the hierarchy, and S3 onward are tested in order (the skip is fixed by `model.frozen_design` in the sealed config before any holdout read, so the error control is unchanged; `stage9_analysis.apply_hierarchy`, tested) | spec 4.4 |
| S3 | Calibration on holdout decided pairs | slope 95% CI inside [0.8, 1.25], then intercept CI contains 0, then Spiegelhalter not rejected at 0.05 | spec 4.5 |
| S4 | Can't-tell rule at t_S4 (0.4905 from the ruling-2 extended grid on the refit, 2.1) | non-significant nulls called **under 5%** (strictly below 0.05, Wilson CI reported); identical pairs "ahead" <= 5%; selective accuracy and coverage reported, plus the share of calls on nulls at the Upworthy decided base rate (24.8%) | spec 4.6, 4.7; decision 5; ruling 2 |
| C98 | Accuracy when confident at t98 (full design), with coverage | selective accuracy >= 0.98 on its 95% CI lower bound (`ci_lower`); text-only design reported. **Display rule (Emily's display ruling 2026-10-21, on top of ruling 5):** "about 98% when confident" is written only if **C98 passes in the endpoint hierarchy** (this bar met and gated), and then only if, as extra conditions, accuracy when confident >= 97.5% with its CI lower bound >= 96%; always with its coverage and its null-pair call rate next to it (`report.display_98_allowed`, `report.confident_claim`). When C98 fails or is not gated, the report gives the measured accuracy with its CI lower bound, its coverage and its null-pair call rate, and not the phrase. At the gate, t98 called 28.2% of non-significant null pairs (refit 28.4%), which is why the null rate travels with every figure | r0_v2 rule 4b; ruling 5 |
| S5 | Decided-pair accuracy vs the usual winner (always-control) | target from the stack gate's test parts (O6 rule below), frozen in the config before sealing; reported with kappa | spec 2.1 target 2 |
| S6 | Letter-style claim | `customer-v1` checkpoints only | R-2026-10-14-grade-vs-base-rate, Addendum 2 |
| Report | Familiarity regression slope and below-median-familiarity accuracy | reported, never gated | spec 3.2 |

**S5 target rule (O6).** target = the 95% CI lower bound of the frozen design's pooled decided-pair accuracy on the stack gate's test parts, minus 0.05 for the shift from dev to holdout, and never below always-control on those test parts + 0.05. Computed once from the stack gate results and written into `s5.target_accuracy` before sealing.

**Draft change 5.1 (2026-10-18; unsealed, so a change to the draft, not an amendment).** A **recognition** baseline joins S1 and the spec 4.7 `baselines_full_system` null test: per text, a membership score of the exact text under the frozen base model; guess = the arm the model recognises more. Method fixed 2026-10-20: **Min-K% Prob, k = 20%, under `google/gemma-4-31B` @ `5bbc2fb1` without the adapter**. Scale fitted on non-holdout decided pairs before sealing, like the other baselines; the implementation (a `models.Recognition`) is pinned by `baselines.recognition.implementation_sha256` in the frozen config (O13). **Degenerate texts (rule pre-set 2026-10-21, before any recognition score existed).** Every text is scored after a BOS token, with the log-softmax in fp32, so any text with at least one token has at least one scored log-probability. A text with no scored token (under the Gemma 4 tokenizer only the empty string: 1 of the 45,017 non-holdout headlines, which crashed the first `recog_scale` run) or with a non-finite token log-probability is **degenerate**: its table row holds the finite sentinel score 0.0 with `degenerate: true` (no NaN in the file); it is **excluded from the scale fit**; at Stage 9 it scores the **median** of the table's non-degenerate scores, so the recognition guess has no systematic lean for or against that arm.

**Draft change 5.2 (2026-10-20, decision 8): web-presence baseline DROPPED.** The 10-18 draft also added a web-presence baseline (log(1 + exact-phrase hits) in a web index frozen before the model cutoff). Emily's rule: keep it only if a free, licensed index exists. None was found. Common Crawl is free but has no exact-phrase index: building one means processing the WET files, which is not free. The infini-gram API counts exact n-grams over training corpora (Dolma, RedPajama, C4, the Pile), not the web. Its terms for commercial use could not be verified, and using it would send holdout text to another third party. So web presence is removed from `S1_BASELINES` (analysis), the config template, the runner and the CLI. The disclosure is printed in every Stage 9 report ("What this does not show"). The recognition and familiarity baselines remain the leakage checks. Re-adding web presence after sealing is impossible; before sealing it needs a new draft change naming the index, its licence and its `index_as_of` date.

### 5.4 Frontier endpoint (decision 2; after the hierarchy, provisional)

| # | Endpoint | Rule |
|---|---|---|
| F1 | Paired best-of-k accuracy, Lens minus F-Opus, and Lens minus F-Sonnet, on the same holdout tests (the arms kept by the arm-set rule, 2.1b) | cluster bootstrap by test id (2,000, seed 9000). "Lens beats <arm>" only if the 95% CI lower bound > 0. Each arm's L, its chance line and its recognition-probe hit rate are printed beside it |

### 5.5 Extra metrics (decision 5; after the hierarchy, never gated)

All on holdout decided pairs, cluster bootstrap by test id with the frozen n_boot and seed. Computed by `stage9_analysis.extra_metrics` (tested) into `results["extra"]`.

| Metric | Definition | Pre-set rule or label |
|---|---|---|
| Kappa at matched coverage | Cohen's kappa on the 49% most confident decided pairs (by abs(p - 0.5)) | Lens is said to exceed Squoosh's **0.31 at 49%** (arXiv 2608.07517) only if the 95% CI lower bound is above 0.31. The external figure is another vendor's data set, never placed in the same row as an Upworthy number |
| Reliability curve | 10 equal-count bins of confidence vs accuracy of the chosen side | printed in full |
| Monotonicity test | Kendall tau-b between abs(p - 0.5) and the hit | "accuracy rises with confidence" only if the 95% CI lower bound is above 0 |
| Confidence AUROC | AUROC of abs(p - 0.5) for a correct call | **descriptive** |
| ECE | debiased ECE (spec 4.5) | **descriptive**; withheld below 1,500 decided pairs (the holdout is expected to have far more) |
| Null-pair call rate | S4 | **under 5%** (S4 bar) |
| Open evaluation code | 2.9 | publication commit must hold the sealed code hash |

External bars, never placed in the same row as an Upworthy number: Squoosh kappa 0.31 on the 49% its vote gate answers; LOLA prompted GPT-4 37.85-39.96% best-of-k on 3,263 tests; human CRO experts kappa about 0; Aaru confidence AUROC 0.845 (survey track); Attention Insight MIT300 AUC 0.864 (no comparable Lens number exists).

Stage 8 dev numbers, for reference only (contaminated-flagged, provisional): 8.1c Gemma best-of-k 47.9% vs chance about 25.2% (L 0.304); text + Opus 81.2% decided-pair accuracy vs always-control 62.5% (8.6, on the 8.1 learner).

## 6. What may not change after sealing

The frozen config bytes and hash (which carry the ensemble's artefact hashes, the frozen design and coefficients, t_S4, t98, the describe and frontier prompts and model ids, the baseline scales, the credit reserve, the bars and their order, the extra-metric rules, the bootstrap seeds and the `customer-v1` hash), the bridge set (`bridge_set.json`, sha256 `ee0f6058...d538`) and the analysis code hash. A crash fix that changes no number goes in as a sealed amendment with the new code hash, before the affected phase runs.

## 7. O1-O13, resolved one by one, and what still blocks sealing

### 7.1 Decision per open item

| # | Item (10-15 draft) | Decision 2026-10-20 | State |
|---|---|---|---|
| O1 | Full 10-split 8.1b gate (split 0) | **Superseded.** The learner is no longer the 8.1b OSim adapter. 8.1c re-gated OSim-8B, Qwen3-14B and Gemma 4 31B on all 10 splits: all PASS_full | Closed |
| O2 | Bake-off winner | **Superseded** by the 8.1c selection: Gemma 4 31B, most accurate full-gate passer (accuracy-only rule, R-2026-10-19). The bake-off plan stays listed in the manifest, unused | Closed |
| O3 | 600-pair bridge set | **Kept**, rule fixed in 2.5 (`default_rng(8130)` over sorted tier-1 decided pair ids). Needed before the final adapter replaces the ensemble | **Closed 2026-10-21** (B5): drawn, `bridge_set.json` `ee0f6058...d538` (2.5) |
| O4 | Describe-only vs full panel | **Decided:** describe-only; the full panel is dropped (decision 2). The post hoc basis is replaced by the stack gate's pre-registered describe decision (2.2). `8_7/PREREG_describe_only.json` still runs at 100 post-cutoff pairs | Closed (design) |
| O5 | Stacker and threshold on the chosen learner | **Decided:** per-split symmetrised stackers and t98 from the stack gate; t_S4 by LTT on its pooled test-part predictions (extended grid, ruling 2: 0.4913); ensemble transfer rule in 2.1; stack re-fit on the adopted learner's readouts (ruling 1, 2.1a) | **Closed 2026-10-21:** re-derived on the refit (B1 d, confirmed): t98 0.41, t_S4 0.4905 |
| O6 | S5 target | **Decided:** rule in section 5 (stack gate test parts, CI lower bound - 0.05, floor always-control + 0.05) | **Closed 2026-10-21:** 0.8611 on the refit (B1 d; the gate's 0.8631) |
| O7 | `customer-v1` seal | **Decided:** its hash `d0884d21...` is carried in the frozen config (`s6.plan_sha256`), so `stage9:FROZEN` seals it. The Mac still looks for an earlier ledger seal and records it if found | Closed (design) |
| O8 | Ledger heads not recorded (8.5, 8.5 v2, 8.7, final 8.1b, bake-off) | **Kept:** copied into the manifest on the Mac and checked with `--strict`; the stack gate heads join them | **Closed 2026-10-21** (B6): the five heads copied read-only from the Mac's ledgers (3.1) |
| O9 | Analysis script and independent dev re-run | Runner and analysis exist and are tested (PR #50; extra metrics, credit gate and the web-presence drop added here). **Decided:** the re-run is the two-part check of section 4 step 7 | Open (B4); B7 **closed 2026-10-21** (re-run MATCH, `research/stage9/B7_INDEPENDENT_RERUN.md`) |
| O10 | Stage 9 spend | **Decided:** reserve $70 enforced by the runner; expected $34, worst $68 | **Deferred: Hemant's yes on the figure at run time** (B8) |
| O11 | Post-cutoff confirmation | **Decided:** label rule (section 1), growth plan (2.6). Not a sealing blocker: Stage 9 reports "provisional" until it is met | Open, label only |
| O12 | Stack gate | **Decided:** plan revised (pick, $65 cap, seeded sample, missing-feature design, describe decision); runner and tests updated | Open (B1) |
| O13 | Recognition and web-presence scorers | **Web presence dropped** (draft change 5.2, disclosed). **Recognition** method fixed (Min-K% 20%, Gemma base); recognition and familiarity scorers built and pinned; GPU route E2E (ruling 3); launcher built (B3); recognition scale fitted 2026-10-21 (0.1532, B3) | Decided |

### 7.2 What still blocks sealing

| # | Blocker | Who / where | Fills |
|---|---|---|---|
| B1 | **Stack gate run: DONE 2026-10-21.** Collection: 41,221 Opus describes, $64.34 measured. Gate: **PASS_full** on 10 of 10 (mean L 0.318 [0.310, 0.325]); describe **KEEP** (gain +0.0045 nats [+0.0021, +0.0070]); 98% rule pooled coverage 67.0% at 98.1% [97.7, 98.5]. **Closed by Emily's rulings 2026-10-21:** (a) S4: the extended grid (ruling 2) gives t_S4 = 0.4913 on the gate (null call rate 4.80%, coverage 30.0%), so S4 is no longer "never call"; (b) Upworthy = M5 and the 98% display rule with coverage and null rate beside it (ruling 5), encoded, and since the display ruling gated on C98 passing in the hierarchy (0b 5b); (c) the independent re-run: B7 (gate) and B7b (refit, G9); (d) **confirmed by Emily 2026-10-21** and done: after the ruling-1 re-fit, t98 (0.41), t_S4 (**0.4905**) and the S5 target (**0.8611**) were re-derived by the same pinned code from the re-fit predictions (2.1a point 4) | Emily, nina | refit values (filled) |
| B2 | **Learner adapters (ruling 1).** `EnsembleStack` is built (`stage9/ensemble.py`, tests `test_ensemble.py`). The decision tree is encoded (`stage9/learner.py`, 2.1a): bf16 adapters if the bf16 8.1c gate (PR #99, job g81c) adopts, else an NF4 retrain on E2E accepted within the sealed noise margin 0.011088638914821092 per split. **Closed 2026-10-21:** (a) route **nf4_retrain** (g81n, every split inside the margin, max |diff| 0.009698); (b) `model.adapters` (route + 10 sha256), the stack re-fit by the sealed procedure (`stage9_refit.py`, PASS_full, describe KEEP) and `model.stack_sha256` `94ed011e...c3bc` are in the config (2.1a); (c) **resolved 2026-10-21:** Emily ruled the 10 per-split adapter readouts ride the same E2E route (amendment `gpu_pass.resolved`); `stage9/readout.py` (the sealed kernel's readout, equal to its `Runner.score` on a tiny model, max abs diff 0.0) and the launcher (B3) are built; the holdout readouts run in the holdout pass (runbook step I) | GPU (E2E) | `model.adapters`, `model.stack_sha256` (filled) |
| B3 | **Recognition scale: DONE 2026-10-21.** The `recog_scale` v2 pass (E2E H200, instance `lens-e2e-s9gpu-20261021-220512`, deleted) sealed the Min-K% 20% table of the 45,017 non-holdout headlines under Gemma 4 31B bf16 (`engine/experiments/stage9/gpu_pass/ledger.sqlite` seq 14, ref `stage9_gpu:SCORES:recog_scale:recognition`, table sha256 `165c5944...2dfc`, scorer `dab4f30f...e450`). Before the fit the fetched table's sha256 was checked against the sealed entry, `gpu_pass.check_scores` was re-run against the sealed upload's sha256 list and the ledger chain verified. **1 degenerate row** (the empty string, `e3b0c442...b855`), excluded by the 5.1 rule; no decided pair contains it. `baseline_scales.py` (`34777896...fa53`, the same fit as the other four scales) gives **`baselines.recognition.scale` = 0.15316481430828632** on 9,746 non-holdout decided pairs (0 dropped); the other four scales reproduce bit for bit. Fit file `research/stage9/baseline_scales.json` (sha256 in config `baselines.fit.sha256`). **Recognition and familiarity scorers: BOTH BUILT and pinned.** Recognition: `stage9/recognition.py` (Min-K% 20%, `dab4f30f...e450`; re-pinned 2026-10-21: the first `recog_scale` run crashed on the one empty headline, fixed by the degenerate-text rule of 5.1). Familiarity: `stage9/familiarity.py` (8.1b mean token log-prob, Gemma base, precision of the adopted learner; `ecd5935f...86dd`, in config). The E2E route (ruling 3) is built as bookkeeping (`stage9/gpu_pass.py`: text-only upload, sha256 list sealed before upload, fresh instance, hash-checked score files, deletion confirmed; extended 2026-10-21 to the readouts: canonical `{a_sha256, b_sha256}` pair file, 10 adapter pins sealed before upload, per-split readout tables). **Launcher built 2026-10-21** (branch `cloud/s9-b356`): `stage9/e2e_gpu_pass.py` (sets `recog_scale` = Min-K% of the 45,017 distinct non-holdout headlines; `holdout` = familiarity + recognition of the holdout texts and the 10 readouts of every within-test holdout pair, staged only through the approved text-only procedure; refuses while any other E2E session or unconfirmed create is recorded, and while the 8.1c bf16 gate (g81c) is unfinished, also between its sessions (review of PR #102: its ledger has session 1 sealed and 0 of 10 splits on 2026-10-21); every check of `seal_scores` made for all tables before the first is sealed, sealed only after a deletion the pass itself confirmed; `readout.py` batches exactly as the kernel, so the dry run's readouts equal `Runner.score` bit for bit; outputs to the main tree), the instance job `stage9/gpu_job.py` + `gpu_job.sh` (sealed lane install), tests with fake TIR clients (`stage9/tests/test_e2e_gpu_pass.py`) and a CPU dry run with a tiny Gemma 4 (`experiments/stage9_gpu/dryrun_cpu.py`: 12 tables sealed after the delete). **Cost estimate (unmeasured throughput):** `recog_scale` H200 spot INR 62 central / 197 slow, on-demand INR 356 / 1,127; `holdout` full (7,891 texts, ~18,049 pairs x 10 adapters) spot INR 240 / 624, on-demand INR 1,370 / 3,564 (slow case 6.0 h: stage it as two passes, e.g. familiarity + recognition + readouts s0-4, then s5-9; each part seals only its own tables). **Still blocked (not a config value):** the `holdout` GPU run: the owner's go on the figure and the amendment's seal (B4) | GPU (E2E), Hemant (go), Emily (B4 seal) | `baselines.recognition.scale` (filled 2026-10-21) |
| B4 | **DONE 2026-10-23.** Amendment approved (`approved_to_run` true) after Hemant's explicit go in chat on 2026-10-23; its sha256 is in the manifest files list. **Text-only pre-collection: amendment approved in substance (ruling 4), kept unsealed.** The credit check now runs before the holdout text read (`precollect.gate_credit` in build; sealed in `stage9_pre:BUILD`), and a holdout predict checks the pre-collection head and its sealed credit instead (`runner._gate_paid`); tool hash `731a757c...cd3a` (re-pinned 2026-10-23 for the arm-set rule, 2.1b) in the amendment and the config. The amendment also carries the E2E GPU route (`gpu_pass`). **Open:** sealing it (`approved_to_run: true`) once Emily or her reviewer confirms the hashes; ruling 6 holds until it runs: nothing else may use Opus | Emily (seal), then Mac | `frontier_arms.implementation_sha256` (filled) |
| B5 | **Bridge set drawn (O3): DONE 2026-10-21** (2.5): `research/stage9/bridge_set.json` sha256 `ee0f6058...d538`, ids_sha256 `4ebbc283...18a5`, in config `bridge_set` and the manifest (`stage9:bridge_set`) | Mac | manifest entry (filled) |
| B6 | **Missing ledger heads copied (O8): DONE 2026-10-21** (branch `cloud/s9-b356`). 8.5 seq 5 `c8e02af7...0775`, 8.5 v2 seq 14 `1eacbcad...2574`, 8.7 seq 619 `10e23f3e...a274`, 8.1b final seq 531329 `32bcf66e...6544`, bake-off final seq 39 `70dc77b1...f74e`, each read from the Mac's ledger opened read-only with its chain recomputed from genesis (intact). `prereg_check.py` run from the worktree only (no ledgers there: SKIP); `--strict` on the Mac main tree confirms them at sealing | Mac | manifest entries (filled) |
| B7 | **Independent re-run matches (O9): DONE 2026-10-21, accepted by Emily.** B7: independent re-run MATCH 2026-10-21 (research/stage9/B7_INDEPENDENT_RERUN.md); 7a byte-identical outputs from ledger head `55a8701c...e6a7`; 7b 173 of 173 split predictions at max abs diff 0.0, tol 1e-9. Clean checkout of origin/main `0af4ce7`, fresh venv (pinned in 4.1), copied ledgers; no holdout read, no API call, nothing sealed | isolated agent (accepted by Emily) | sign-off line (filled) |
| B7b | **Independent re-run of the refit ensemble (runbook G9).** Section 4 step 7 asks for a re-run of the stack Stage 9 scores, which is now the refit `94ed011e...c3bc`, not the gate's. **MATCH 2026-10-21, with one step not re-run** (`research/stage9/B7b_REFIT_RERUN.md`): from the refit ledger head `7035e628...101e`, `results.json`, the no-describe arm, `RESULTS.md`, `s4_extended.json`, `results_oof_ensemble_t98.json` and `ensemble.json` (`94ed011e...c3bc`) reproduce byte for byte, and the 200-pair replay matches 173 of 173 split predictions at max abs diff 0.0. The re-staging from the sealed gate inputs and the GPU tables, the invariants against the gate (23,932 entries) and every config value also reproduce. The stacker fit itself (`fit-seal`) was not re-run: the guarded loaders read the holdout exclusion list in `data/sealed`, which this agent may not open. Clean checkout `c8e01b4`, fresh venv (pinned list of 4.1), APFS-clone copies; no holdout read, no spend, nothing sealed in a real ledger. **Open:** Emily accepts it, or has nina (or a run on the Mac main tree) re-run `fit-seal` from data | isolated agent (done); Emily accepts | sign-off line |
| B8 | **DONE 2026-10-23.** Hemant's yes on 2026-10-21 and again on 2026-10-23; console credit read 2026-10-23: US$70.25 promotional, US$0 purchased, no card on file. Hemant's yes on the Stage 9 figure, credit >= $70 in hand at the pre-collection build (about $70.26 left, unverified, ruling 6), and a top-up if any other Opus spend lands first (2.7) | Hemant | build-time flag |
| B9 | **DONE 2026-10-23.** `holdout_sha256` filled with `fill-holdout-sha256` (matches the recorded value); config copied to `engine/experiments/stage9/FROZEN_CONFIG.json`, in the manifest files list. `holdout_sha256` written into the config from `data/sealed/HOLDOUT_SHA256.txt`; the frozen config moves from pending to sealed (`seal-config`) | Mac | `datasets[0].holdout_sha256` |
| B10 | **DONE 2026-10-23.** Signed off: see the sign-off line below. Emily's sign-off on this package; copy to `PREREG_PACKAGE_v1.md`, hash it, and publish the hash as a dated `package` line in `docs/track-record/README.md` before `seal-config` (G8; `stage9.cli publication-lines --package research/accuracy/PREREG_PACKAGE_v1.md` prints it) | Emily, then Mac | the seal |

**Sign-off (B10), 2026-10-23:** Emily (CTO) signs off this package for sealing. Every 7.2 blocker is closed; `prereg_check --strict` gave 147 pass, 0 fail, 0 skip on the draft. This draft is copied unchanged to `PREREG_PACKAGE_v1.md`, and v1 is never edited.

Not blocking: the post-cutoff count (label only; 12 decided pairs), the B2B set (its own config, results "pending"), the final mixture adapter (mixture `lens-final-mixture-2026.10.20-4`, manifest `49182f6a...f0fc`; ships after Stage 9 through the bridge test, never scored by Stage 9).


## 8. Running the checker

```
python3 engine/scripts/prereg_check.py            # on the Mac, from the repo root
python3 engine/scripts/prereg_check.py --strict   # before sealing: missing ledgers count as FAIL
```

In a checkout without data (cloud, CI), the file and canonical checks run and pass. Ledger and holdout checks report SKIP, and so do pending plans (FAIL with `--strict`). The checker reads only the holdout **hash** file, never `holdout_ids.txt`. Unit tests: `engine/tests/test_prereg_check.py` (no data needed).

The block below is the machine-readable manifest the checker reads. Every value in it also appears in sections 2-3. A unit test fails if they drift apart, or if a `PLAN.json` / `ANALYSIS_PLAN.json` is added under `engine/experiments/` without being listed here.

```json prereg-manifest
{
 "version": 1,
 "files": [
  {
   "id": "8_1:CANDIDATES",
   "path": "engine/experiments/8_1/CANDIDATES.json",
   "expected_sha256": "8e70ceabd49fdcbffd86f22e95ead2324b9bd998ba872230e8f196d0fd1879a2",
   "source": "8_1/RESULTS.md",
   "sidecar": "engine/experiments/8_1/CANDIDATES.sha256"
  },
  {
   "id": "8_1b:CANDIDATES",
   "path": "engine/experiments/8_1b/CANDIDATES.json",
   "expected_sha256": "d4630a71a8aece5887b45cf007936dc4a96b53b6153967737c6ddfcfb3dca995",
   "source": "sidecar",
   "sidecar": "engine/experiments/8_1b/CANDIDATES.sha256"
  },
  {
   "id": "8_1b:zeroshot_kernel",
   "path": "engine/experiments/8_1b/kaggle/zeroshot/lens_8_1b_zeroshot.py",
   "expected_sha256": "e418179e2c8197a6ef36c0002e84e9cec09f985ded8322e4eb994013c986b54b",
   "source": "RESUME.md line 137",
   "resume": "e418179e…b54b"
  },
  {
   "id": "8_5:PLAN",
   "path": "engine/experiments/8_5/PLAN.json",
   "expected_sha256": "154f78c2c4bded3d26f1359803aa34a8286a2e5b12647491c1addfafd81dc848",
   "source": "RESUME.md line 134",
   "sidecar": "engine/experiments/8_5/PLAN.sha256",
   "resume": "154f78c2…c848"
  },
  {
   "id": "8_5_v2:PLAN",
   "path": "engine/experiments/8_5_v2/PLAN.json",
   "expected_sha256": "d5c508b4fdde419ec653dbc3fc2d44f1af742abde63dfcbb55e5bc57bb1af662",
   "source": "RESUME.md line 146",
   "sidecar": "engine/experiments/8_5_v2/PLAN.sha256",
   "resume": "d5c508b4…"
  },
  {
   "id": "r0_v2:PLAN",
   "path": "engine/experiments/r0_v2/PLAN.json",
   "expected_sha256": "dbadebd0b3f581a8c9e3dc3bda89ce5f085763a377eface99927bdcc30e6928c",
   "source": "RESUME.md 2026-10-15 R-0 v2",
   "sidecar": "engine/experiments/r0_v2/PLAN.sha256",
   "resume": "dbadebd0"
  },
  {
   "id": "tpu_spike:PLAN",
   "path": "engine/experiments/tpu_spike/PLAN.json",
   "expected_sha256": "3dfff8f46647b78dffc9ada925ae1faa090bf71df34e2543b2513eef18caa79e",
   "source": "RESUME.md 2026-10-15 TPU spike",
   "sidecar": "engine/experiments/tpu_spike/PLAN.sha256",
   "resume": "3dfff8f4"
  },
  {
   "id": "tpu_spike:kernel_amendment",
   "path": "engine/experiments/tpu_spike/kaggle/kernel/lens_tpu_spike.py",
   "expected_sha256": "ed1d402c95fa609881faf9fa17fdaa9670a306e01e7912cf6a1cb1e3c25be3fb",
   "source": "RESUME.md 2026-10-15 TPU spike (runtime-only amendment, ledger entry 2)",
   "resume": "ed1d402c"
  },
  {
   "id": "8_6:ANALYSIS_PLAN",
   "path": "engine/experiments/8_6/ANALYSIS_PLAN.json",
   "expected_sha256": "2c4bb8d30431ec2ad0b4ca19261580a4e9e9c3364780de4f6371211fc2f6130c",
   "source": "RESUME.md line 12",
   "sidecar": "engine/experiments/8_6/PLAN.sha256",
   "resume": "2c4bb8d3"
  },
  {
   "id": "8_6:recognition_AMENDMENT",
   "path": "engine/experiments/8_6/recognition/AMENDMENT.json",
   "expected_sha256": "c00917b15fb9c726514c34197f4d809a860b64291a5b6392cb078b5d9fc5da31",
   "source": "this package"
  },
  {
   "id": "8_7:PLAN",
   "path": "engine/experiments/8_7/PLAN.json",
   "expected_sha256": "a661e310ffe4800795755ba092ea82b3ed569a0a286a1a00231bb7951b90250f",
   "source": "sidecar",
   "sidecar": "engine/experiments/8_7/PLAN.sha256"
  },
  {
   "id": "8_7:PREREG_describe_only",
   "path": "engine/experiments/8_7/PREREG_describe_only.json",
   "expected_sha256": "461e18794ddb6477b2d11b207e4d4e99549191c1024845ce019259f56b1157c8",
   "source": "8_7/PLAN.json prereg.sha256"
  },
  {
   "id": "8_10:PLAN",
   "path": "engine/experiments/8_10/PLAN.json",
   "expected_sha256": "07076ddf1b58ad8b805ff717385de72d73caf21093060d7c402d047bc5745998",
   "source": "RESUME.md line 134",
   "sidecar": "engine/experiments/8_10/PLAN.sha256",
   "resume": "07076ddf…5998"
  },
  {
   "id": "8_11:ANALYSIS_PLAN",
   "path": "engine/experiments/8_11/ANALYSIS_PLAN.json",
   "expected_sha256": "4057be4f9a5621bdce3d18e5a5235e4dec5df47795fadbd5af9fcf0b402b5cb2",
   "source": "RESUME.md line 3",
   "sidecar": "engine/experiments/8_11/PLAN.sha256",
   "resume": "4057be4f"
  },
  {
   "id": "8_12:PLAN",
   "path": "engine/experiments/8_12/PLAN.json",
   "expected_sha256": "274861dc35c47c79f4b5789e43a3e7c62c789c9ce532ded6c95453e32ad65eb2",
   "source": "RESUME.md line 152",
   "resume": "274861dc…"
  },
  {
   "id": "8_12:refit",
   "path": "engine/experiments/8_12/refit.json",
   "expected_sha256": "ea1b7e4672e2cd362af94f7524865804b20985327daa70233a728176fe61faa4",
   "source": "8_12/PLAN.json refit.sha256"
  },
  {
   "id": "bakeoff:PLAN",
   "path": "engine/experiments/bakeoff/PLAN.json",
   "expected_sha256": "432ebf73f7bc2b997624492871b4e6ba0aa19824020d1289ba40845e5659298c",
   "source": "RESUME.md line 132",
   "sidecar": "engine/experiments/bakeoff/PLAN.sha256",
   "resume": "432ebf73…298c"
  },
  {
   "id": "describe_ext:PLAN",
   "path": "engine/experiments/describe_ext/PLAN.json",
   "expected_sha256": "4bbbc2b2c106934e48036518031fce8d4b826cbfba5811b03eb87e5f012beb62",
   "source": "sidecar",
   "sidecar": "engine/experiments/describe_ext/PLAN.sha256"
  },
  {
   "id": "r0_claude:PLAN",
   "path": "engine/experiments/r0_claude/PLAN.json",
   "expected_sha256": "9b0a5cc9432602bfedcff5b0a2100f1241d8431cde0afc85ceebc6bc0daa1ecf",
   "source": "sidecar; r0_opus and r0_paraphrase plans",
   "sidecar": "engine/experiments/r0_claude/PLAN.sha256"
  },
  {
   "id": "r0_opus:PLAN",
   "path": "engine/experiments/r0_opus/PLAN.json",
   "expected_sha256": "ac3a57218e0df4bbdef1603bf75575b484950824ae20822174b31365a18d3ab2",
   "source": "sidecar; describe_ext plan",
   "sidecar": "engine/experiments/r0_opus/PLAN.sha256"
  },
  {
   "id": "r0_paraphrase:PLAN",
   "path": "engine/experiments/r0_paraphrase/PLAN.json",
   "expected_sha256": "df23576a3622499ebae5d8791a728f6791324fd02dac1fed85b89a15c83e508d",
   "source": "sidecar",
   "sidecar": "engine/experiments/r0_paraphrase/PLAN.sha256"
  },
  {
   "id": "survey:PLAN",
   "path": "engine/experiments/survey/PLAN.json",
   "expected_sha256": "66cd06ba63f34956e6f752ba698d20ee409d1cf58225b0441ba6389e669f4f48",
   "source": "survey/RESULTS.md"
  },
  {
   "id": "grading:plans_file",
   "path": "app/src/lib/replay/sequential-plan.json",
   "expected_sha256": "bd7487ca5fb4bc6715035a8f0d2e567a9a36ea7520c5583e5d35dc7bc25d3d3f",
   "source": "this package"
  },
  {
   "id": "8_1c:PLAN",
   "path": "engine/experiments/8_1c/PLAN.json",
   "expected_sha256": "7b42b577c604c242fd2140b8076eb924f5f0458c2e5f5fec4ae3812814d75871",
   "source": "RESUME.md 2026-10-15 8.1c PREP DONE; prereg:8_1c in every 8_1c ledger",
   "sidecar": "engine/experiments/8_1c/PLAN.sha256",
   "resume": "7b42b577…5871"
  },
  {
   "id": "8_1c:kernel_body",
   "path": "engine/experiments/8_1c/kernel/lens_8_1c.py",
   "expected_sha256": "fb256abdac81718cac3e8b17318cac68cf5063c0fca267aa34da18d021a87709",
   "source": "8_1c/PLAN.json sealed_files (body, RUN = None)",
   "resume": "fb256abd…"
  },
  {
   "id": "8_1c:AMEND_gemma_4_31b_base",
   "path": "engine/experiments/8_1c/AMEND_gemma_4_31b_base.json",
   "expected_sha256": "6aca4f23ee39a09367017a1c203f9a3c8df092d493c45f52b6f7213fedd06085",
   "source": "8_1c ledgers seq 3 (amend_sha256 / sha256)"
  },
  {
   "id": "8_1c:kernel_body_gemma31",
   "path": "engine/experiments/8_1c/kernel/lens_8_1c_gemma31.py",
   "expected_sha256": "55e70363bb9c71eb41ffe0f456c70ddf5ec426d88c63236fa1c169d50d58d094",
   "source": "8_1c/AMEND_gemma_4_31b_base.json sealed_files (body, RUN = None); kernel_body_sha256 in ledger_gemma_4_31b_base seq 3 and 4"
  },
  {
   "id": "8_1c:AMEND_gemma_modal_l40s",
   "path": "engine/experiments/8_1c/AMEND_gemma_modal_l40s.json",
   "expected_sha256": "9eb2487884d41a1547ebba27b8b8de56c69932b7950117cd5974cb40ad7a816e",
   "source": "8_1c ledger_gemma_4_31b_base seq 4"
  },
  {
   "id": "8_1c:AMEND_origin_rule_removed",
   "path": "engine/experiments/8_1c/AMEND_origin_rule_removed.json",
   "expected_sha256": "c5e10d04b7845d781620b578351732e4aea75c4261452fd73572d54f375d5bac",
   "source": "every 8_1c ledger, amendment:8_1c:origin-rule-removed:2026-10-19 (qwen seq 311135, gemma seq 311142, mistral seq 5)"
  },
  {
   "id": "ruling:R-2026-10-19-origin-irrelevant",
   "path": "research/accuracy/rulings/R-2026-10-19-origin-irrelevant.md",
   "expected_sha256": "2ce5e63ac4a1b442f4d7ee3e3aa2cb0762db5df5b1e4f295fdaaad319a27d20e",
   "source": "AMEND_origin_rule_removed.json ruling_sha256"
  },
  {
   "id": "scaling:PLAN",
   "path": "engine/experiments/scaling/PLAN.json",
   "expected_sha256": "c0c13f5d680ecbf012e1d39d425775b681d8b169dda6a2d3106ed5f3efe714dc",
   "source": "scaling ledger seq 1 (prereg:scaling)",
   "sidecar": "engine/experiments/scaling/PLAN.sha256"
  },
  {
   "id": "scaling:driver",
   "path": "engine/experiments/scaling/scaling.py",
   "expected_sha256": "48f42101cc83e1baaf93a396d34a9df82693fc3786b2d79561141d6867cf6332",
   "source": "scaling ledger seq 1 driver_sha256"
  },
  {
   "id": "scaling:amend_qwen3_8b_base",
   "path": "engine/experiments/scaling/amend_qwen3_8b_base.json",
   "expected_sha256": "4f99a4a6875db7d67cae7d915917b035a3b1f9d4e599b1198e30966989ada11b",
   "source": "scaling ledger seq 9 amendment_file_sha256"
  },
  {
   "id": "scaling:amend_gemma_4_31b_base",
   "path": "engine/experiments/scaling/amend_gemma_4_31b_base.json",
   "expected_sha256": "1d551d6d2443781583e12fed8c018a66d7e39341e521a900bda5d1e113482242",
   "source": "scaling ledger seq 18 amendment_file_sha256"
  },
  {
   "id": "voyage_test:PLAN",
   "path": "engine/experiments/voyage_test/PLAN.json",
   "expected_sha256": "018e445f63f87fb0d1b2321214be96e8f92f3965f00a1c3a84ce3fc91f7a7903",
   "source": "RESUME.md 2026-10-15 VOYAGE TEST; voyage_test ledger seq 1 plan_sha256",
   "sidecar": "engine/experiments/voyage_test/PLAN.sha256",
   "resume": "018e445f"
  },
  {
   "id": "voyage_test:voyage_embed",
   "path": "engine/experiments/voyage_test/voyage_embed.py",
   "expected_sha256": "4ffd4c61354821f5d706872551caee472bf0af10ada79126f9d07a95238b87f2",
   "source": "voyage_test ledger seq 3 (amendment 2) code_sha256"
  },
  {
   "id": "stage10:PLAN",
   "path": "research/stage10/PLAN_v1.md",
   "expected_sha256": "8ae8d938145c7872f9d4260d3197c60c457c48513009d1a9d4871792ced4008c",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19",
   "sidecar": "research/stage10/PLAN_v1.sha256"
  },
  {
   "id": "stage10:stimuli_MANIFEST",
   "path": "research/stage10/stimuli/MANIFEST.json",
   "expected_sha256": "4d0281b76e33637bc1b9f60f6b02ef2d8e07c9ad98aff7b2398c9138e9e854b3",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `stimuli_manifest_sha256`"
  },
  {
   "id": "stage10:plan.py",
   "path": "engine/lens_engine/stage10/plan.py",
   "expected_sha256": "167c1a688c285ce18d48596ddf6898a3108fc6327511173f9d4c55a04e5cff41",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `sealed_files`"
  },
  {
   "id": "stage10:prompts.py",
   "path": "engine/lens_engine/stage10/prompts.py",
   "expected_sha256": "964ed85a02f285e880480aed95bda3a34680f5dbf12648a207181e6b8afa0c07",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `sealed_files`"
  },
  {
   "id": "stage10:aggregate.py",
   "path": "engine/lens_engine/stage10/aggregate.py",
   "expected_sha256": "3e461fd40da08fc7feb5b2954f2526b4e75364ccd78d48a4de5e1cf259e3b279",
   "source": "research/stage10/AMENDMENT_01.md (stage10 amendment 1, `prereg:stage10:amendment-01` `changed_sealed_files`, to be sealed before the pilot)"
  },
  {
   "id": "stage10:report.py",
   "path": "engine/lens_engine/stage10/report.py",
   "expected_sha256": "a4fd862054149cfb2c085f73bbac0476cc7f20a5c0cca56764041eba3d228ea7",
   "source": "research/stage10/AMENDMENT_01.md (stage10 amendment 1, `prereg:stage10:amendment-01` `changed_sealed_files`, to be sealed before the pilot)"
  },
  {
   "id": "stage10:AMENDMENT_01",
   "path": "research/stage10/AMENDMENT_01.md",
   "expected_sha256": "d07a1efd6eb2dc4f8c4eeeb7809107aa34c82239044da9df5aada450f06867db",
   "source": "stage10 amendment 1, written 2026-10-19 before any Stage 10 request was sent; its sha256 goes in `prereg:stage10:amendment-01` when seal_stage10.py amend seals it"
  },
  {
   "id": "stage10:panel-rule.ts",
   "path": "app/src/lib/panel-rule.ts",
   "expected_sha256": "777a8d74fce8f6addd258e2e87bb77b795ca33e2780004a38007a3a26fc2b2f1",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `sealed_files`"
  },
  {
   "id": "stage10:persona_p01",
   "path": "research/stage10/personas/p01.json",
   "expected_sha256": "c5ef3bb3a4e2fd28683afe47a770dda6265aaf72f071eb787a4469a524256c92",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p02",
   "path": "research/stage10/personas/p02.json",
   "expected_sha256": "c7eb94de9f4edd7a3a10307f5beddb55231c8c5d48a034bcf178472849d445c0",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p03",
   "path": "research/stage10/personas/p03.json",
   "expected_sha256": "2c628ff1f0ab11b6381e62eba82e79d6fa58f589596a9a6b19a6de9bd212e297",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p04",
   "path": "research/stage10/personas/p04.json",
   "expected_sha256": "4f3b33f574ab44262fa044e056b99bc5f3efad9e7e59cb6d6260a686ed7d4c3b",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p05",
   "path": "research/stage10/personas/p05.json",
   "expected_sha256": "c2bd6e8174feca6973fcaa440d94f5622c41726e6a4fa7098fd21aed8c4401de",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p06",
   "path": "research/stage10/personas/p06.json",
   "expected_sha256": "41fdbb03bc0951e0eab3500e08b82699c16122c68b845cc120e5b68766f437e8",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p07",
   "path": "research/stage10/personas/p07.json",
   "expected_sha256": "a737f94f1fda537173bb244af7092b8d70bbfb1bca45e8eedf1207bd27ba9f9b",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p08",
   "path": "research/stage10/personas/p08.json",
   "expected_sha256": "6f0ca3dcc6819418beb8fdf170a5d7599fb8a2ac515ef30480f8022e961aeb6b",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p09",
   "path": "research/stage10/personas/p09.json",
   "expected_sha256": "e810dee26549371bd665cfbbde8471df59daf5198ac8548f0a3de5d56b3476f2",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p10",
   "path": "research/stage10/personas/p10.json",
   "expected_sha256": "478f2a24f533d47cc02dc6ab07a01b693e01f4281030405d8a04b66518453089",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p11",
   "path": "research/stage10/personas/p11.json",
   "expected_sha256": "80f52f589486fe032f1d8ab7a71805862dd452cdf741758bbff0e71270fed0c8",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p12",
   "path": "research/stage10/personas/p12.json",
   "expected_sha256": "cee63d2f448275233081bb3a436fb35bc5144588d0c77a202c2d1407702f916b",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p13",
   "path": "research/stage10/personas/p13.json",
   "expected_sha256": "2907e23abb9f3907d3c8198e20113b1f332560cd70f9026af71e72c952ef04f9",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p14",
   "path": "research/stage10/personas/p14.json",
   "expected_sha256": "13833b3b39c7092aa6df33a156b8845d3784f6d0b6fbe3a25b90052092412504",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p15",
   "path": "research/stage10/personas/p15.json",
   "expected_sha256": "5a33309f5f140cdf70a75d3c260c0059f4a3cfa2b89cf3e220e066fa6f9a8cfe",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p16",
   "path": "research/stage10/personas/p16.json",
   "expected_sha256": "377f469de4d042c812cba5a41ed289cdb31ba2eec33b1a2a19d9412ba7669686",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p17",
   "path": "research/stage10/personas/p17.json",
   "expected_sha256": "37de2c13a99ca13ec54ab7836cdc59ccf694f70d3c23e1629ec55da339af4033",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p18",
   "path": "research/stage10/personas/p18.json",
   "expected_sha256": "22637b5d43dcad6096012386eb9ac56c714ede9f21d92da8688cf0530abd67e6",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p19",
   "path": "research/stage10/personas/p19.json",
   "expected_sha256": "f420b658f87365fec53376328fe4c65e659107293708a622eec20ed68d717f74",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p20",
   "path": "research/stage10/personas/p20.json",
   "expected_sha256": "c2d40e98ad2a2b93a170ef99f86b22406b9348ca47b6527b8418cffec7f5536f",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p21",
   "path": "research/stage10/personas/p21.json",
   "expected_sha256": "6ae6409d04b982c81afcf6c6f191f088f5fca48c5b78b6c132e4f409c6aa8b42",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p22",
   "path": "research/stage10/personas/p22.json",
   "expected_sha256": "8f5f935b7007083ad1e34841ec10b617cee767134bf67b99cb3ae29211cca909",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p23",
   "path": "research/stage10/personas/p23.json",
   "expected_sha256": "dc72b19135287fb437b179ba3bee203ed18310161171d9432a83ec520fb074a9",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage10:persona_p24",
   "path": "research/stage10/personas/p24.json",
   "expected_sha256": "683a04105993872e2eaed91cfce5edac04dbf0de79cb5bc66a37a94d5e326f9c",
   "source": "stage10 ledger seq 1 (prereg:stage10), sealed 2026-10-19 `persona_files`"
  },
  {
   "id": "stage9:bridge_set",
   "path": "research/stage9/bridge_set.json",
   "expected_sha256": "ee0f60589b98227766a1f21803291da97ac263c6e2e1d8d1a47c3a917953d538",
   "source": "B5 (O3): drawn 2026-10-21 by engine/scripts/draw_bridge_set.py (package 2.5 rule); config bridge_set.sha256"
  },
  {
   "id": "stack_gate:PLAN",
   "path": "engine/experiments/stack_gate/PLAN.json",
   "expected_sha256": "ac003b8e2b6a6c04bb49f18c6f7453358f4ce367840f5753965d0cf7fa4ba60b",
   "source": "prereg:stack_gate, sealed 2026-10-20 21:19 IST before any paid call (commit 7d922a1); re-sealed unchanged 22:26 IST after the first ledger was lost (stack_gate:recovery)",
   "sidecar": "engine/experiments/stack_gate/PLAN.sha256"
  },
  {
   "id": "stack_gate:refit_nf4r:ensemble",
   "path": "engine/experiments/stack_gate/refit_nf4r/ensemble.json",
   "expected_sha256": "94ed011ee886033333188e917b437cf6994e4b9829d6c8b080a5c942d8e5c3bc",
   "source": "stage9_refit.py run 2026-10-21 (PR #112/#114): the refit stack; config model.stack_sha256; rebuilt byte for byte by B7b"
  },
  {
   "id": "stack_gate:refit_nf4r:s4_extended",
   "path": "engine/experiments/stack_gate/refit_nf4r/s4_extended.json",
   "expected_sha256": "c9a68292e2d2271024d83485be23105f8dad6d3d313a90de71c0cc98768638e6",
   "source": "config s4.fit.file_sha256 (t_S4 0.4905, B1 d); reproduced by B7b"
  },
  {
   "id": "stack_gate:refit_nf4r:c98_fit",
   "path": "engine/experiments/stack_gate/refit_nf4r/results_oof_ensemble_t98.json",
   "expected_sha256": "6f2708de0aba0e7f4295924666e3c035556e4efc009a13d070c2585e124fb97f",
   "source": "config c98.fit.sha256 (t98 0.41, B1 d); reproduced by B7b"
  },
  {
   "id": "stage9:FROZEN_CONFIG",
   "path": "engine/experiments/stage9/FROZEN_CONFIG.json",
   "expected_sha256": "b755abe15e295c7179f03a4ecdb3f19e952107ab56f820dae12e36163594f38f",
   "source": "B9 2026-10-23 (fill-holdout-sha256); copy of research/stage9/FROZEN_CONFIG_DRAFT.json; sealed by seal-config as stage9:FROZEN"
  },
  {
   "id": "stage9:AMEND_text_only_precollection",
   "path": "research/stage9/AMEND_text_only_precollection.json",
   "expected_sha256": "a4c7fdef6a5a45a8b17d1e12db5e13239569013860440a241df9bf62650b154b",
   "source": "B4 approved 2026-10-23 (approved_to_run true)"
  }
 ],
 "canonical": [
  {
   "id": "grading:demo-obf-v1",
   "path": "app/src/lib/replay/sequential-plan.json",
   "pointer": [
    "plans",
    "demo-obf-v1"
   ],
   "expected_sha256": "c8a05006ff91644d67c2d2a0ce595324e05916283eef979ca2e5517357fc8700",
   "source": "checkpoint_plan seal in the demo replay ledgers"
  },
  {
   "id": "grading:customer-v1",
   "path": "app/src/lib/replay/sequential-plan.json",
   "pointer": [
    "plans",
    "customer-v1"
   ],
   "expected_sha256": "d0884d21345afa5cd11c86044e316c62dc42a0aef2622afe21dcd4ebdce9ffae",
   "source": "this package (no ledger seal found in the repo)"
  }
 ],
 "contains": [
  {
   "id": "8_3:demo-120:checkpoint_plan",
   "path": "app/src/data/replay/upworthy-demo-120.json",
   "text": "c8a05006ff91644d67c2d2a0ce595324e05916283eef979ca2e5517357fc8700"
  },
  {
   "id": "8_3:demo-300:checkpoint_plan",
   "path": "app/src/data/replay/upworthy-demo-300.json",
   "text": "c8a05006ff91644d67c2d2a0ce595324e05916283eef979ca2e5517357fc8700"
  },
  {
   "id": "8_3:demo-600:checkpoint_plan",
   "path": "app/src/data/replay/upworthy-demo-600.json",
   "text": "c8a05006ff91644d67c2d2a0ce595324e05916283eef979ca2e5517357fc8700"
  }
 ],
 "pending": [],
 "ledgers": [
  {
   "id": "8_1:head",
   "path": "engine/experiments/8_1/ledger.sqlite",
   "recorded": "0f1c5b21...acea",
   "source": "8_1/RESULTS.md"
  },
  {
   "id": "8_1b:head_6_splits",
   "path": "engine/experiments/8_1b/ledger.sqlite",
   "recorded": "dd1c4d65…",
   "source": "RESUME.md line 136"
  },
  {
   "id": "8_1b:amendment_seq_287197",
   "path": "engine/experiments/8_1b/ledger.sqlite",
   "recorded": "0793173d5255dc8e4d4943f278a399ec3c9dff1241e6f6e3976d1598d68df5e4",
   "source": "build/notes/s8-1b-lora.md (RESUME.md line 137: seq 287197)"
  },
  {
   "id": "8_1b:head_9_splits",
   "path": "engine/experiments/8_1b/ledger.sqlite",
   "recorded": "0ef83ba755e4c0691e46abdb9c673b9c768040b3ceec2ad82d64fbef5bbf5d1d",
   "source": "8_1b/results.json"
  },
  {
   "id": "8_6:head",
   "path": "engine/experiments/8_6/ledger.sqlite",
   "recorded": "171cbfcc2a5fc82cab36955845a9bb62993833cef879e05a25f5653ab0098897",
   "source": "8_6/RESULTS.md, recognition AMENDMENT.json"
  },
  {
   "id": "8_7:describe_alone_FROZEN",
   "path": "engine/experiments/8_7/ledger.sqlite",
   "recorded": "7392a2d5…",
   "source": "8_7/DESCRIBE_ALONE_RESULT.md"
  },
  {
   "id": "8_10:test_seal",
   "path": "engine/experiments/8_10/ledger.sqlite",
   "recorded": "19fa7315",
   "source": "8_10/RESULTS.md (seq 5)"
  },
  {
   "id": "8_11:head",
   "path": "engine/experiments/8_11/ledger.sqlite",
   "recorded": "d1ae84b1bee98f1e2cd0f4ef909cef7e37c23c2e6670990aa3a08b53bd68b8e8",
   "source": "8_11/RESULTS.md"
  },
  {
   "id": "describe_ext:head",
   "path": "engine/experiments/describe_ext/ledger.sqlite",
   "recorded": "f27d7db0e1035e0f4b2e1d73b9abd5b9c9a8344550fc9ce7687d0cfe86d48c78",
   "source": "RESUME.md 2026-10-15 describe_ext DONE"
  },
  {
   "id": "bakeoff:head",
   "path": "engine/experiments/bakeoff/ledger.sqlite",
   "recorded": "c714b103…b2ca",
   "source": "RESUME.md line 132"
  },
  {
   "id": "r0_claude:head",
   "path": "engine/experiments/r0_claude/ledger.sqlite",
   "recorded": "bb0bbce0...3dbc0e",
   "source": "RESUME.md line 56"
  },
  {
   "id": "r0_opus:head",
   "path": "engine/experiments/r0_opus/ledger.sqlite",
   "recorded": "0c66bb4f",
   "source": "RESUME.md line 56"
  },
  {
   "id": "survey:head",
   "path": "engine/experiments/survey/ledger.sqlite",
   "recorded": "af559f4fec142000ba3ad7be0284e8fbccfffb13b0c5c24b7a3a5c1abadc5dca",
   "source": "survey/results.json"
  },
  {
   "id": "8_12:head_btos",
   "path": "engine/experiments/8_12/ledger.sqlite",
   "recorded": "a0f7ad81c7b9374d8514d388c5e028d94382841c4a54cc9c24908ab455318bca",
   "source": "RESUME.md 2026-10-15 8.12 BTOS describe baselines SEALED (head a0f7ad81…, seq 936)"
  },
  {
   "id": "8_1c:gemma_head",
   "path": "engine/experiments/8_1c/ledger_gemma_4_31b_base.sqlite",
   "recorded": "10bafc7fbdb510f0169f6b61bfe73f2acf37b79288241da92c08b3c6a86444f1",
   "source": "RESUME.md 2026-10-15 22:45 IST 8.1c GEMMA ALL 10 SPLITS + familiarity SEALED (head 10bafc7f…44f1, seq 311140)"
  },
  {
   "id": "8_1c:qwen_origin_amend_head",
   "path": "engine/experiments/8_1c/ledger_qwen3_14b_base.sqlite",
   "recorded": "8e37dc66923d0c1fd3485cfc25f3e1c0d5382c784a0c9fa70f7cd04e44a242c8",
   "source": "amend_origin_8_1c.py seal 2026-10-19 (seq 311135, head before any 8.1c outcome join); build/notes/s8-1c.md"
  },
  {
   "id": "8_1c:gemma_origin_amend_head",
   "path": "engine/experiments/8_1c/ledger_gemma_4_31b_base.sqlite",
   "recorded": "048badae7511a39456bad8d5e2bbfc98b491e1521d84c597175ebe6e523de4e7",
   "source": "amend_origin_8_1c.py seal 2026-10-19 (seq 311142, head before any 8.1c outcome join); build/notes/s8-1c.md"
  },
  {
   "id": "8_1c:mistral_origin_amend_head",
   "path": "engine/experiments/8_1c/ledger_mistral_small_24b_base.sqlite",
   "recorded": "44d338a406ab1a823ce303fe7d4e95f05701c439e729207a8e2a01b91567e482",
   "source": "amend_origin_8_1c.py seal 2026-10-19 (seq 5, head before any 8.1c outcome join); build/notes/s8-1c.md"
  },
  {
   "id": "8_5:head",
   "path": "engine/experiments/8_5/ledger.sqlite",
   "recorded": "c8e02af7a7504ee2781045ab71b31eb3dd4b0890d17b8820463f737699310775",
   "source": "B6 (O8): copied 2026-10-21 from the Mac ledger opened read-only (seq 5, 8_5:RESULTS; chain intact)"
  },
  {
   "id": "8_5_v2:head",
   "path": "engine/experiments/8_5_v2/ledger.sqlite",
   "recorded": "1eacbcadf7dcbee824ea53585ce6c92ebc84ca7eda2d255ef7c7d66dbf412574",
   "source": "B6 (O8): copied 2026-10-21 from the Mac ledger opened read-only (seq 14; chain intact)"
  },
  {
   "id": "8_7:head",
   "path": "engine/experiments/8_7/ledger.sqlite",
   "recorded": "10e23f3ec37c459c765334cd8546d67e6357720c18139ff9a4059f337436a274",
   "source": "B6 (O8): copied 2026-10-21 from the Mac ledger opened read-only (seq 619, the describe-alone outcome; chain intact)"
  },
  {
   "id": "8_1b:head_final",
   "path": "engine/experiments/8_1b/ledger.sqlite",
   "recorded": "32bcf66ee5d68a4f459c4d11934df8470c2118462c67838326d6d3325e036544",
   "source": "B6 (O8): copied 2026-10-21 from the Mac ledger opened read-only (seq 531329, last outcome join; chain intact)"
  },
  {
   "id": "bakeoff:head_final",
   "path": "engine/experiments/bakeoff/ledger.sqlite",
   "recorded": "70dc77b13c93c0ee969571f8e1dbe3549620aa6240e3733ce6f4a290b47df74e",
   "source": "B6 (O8): copied 2026-10-21 from the Mac ledger opened read-only (seq 39; chain intact)"
  },
  {
   "id": "stage10:prereg",
   "path": "engine/experiments/stage10/ledger.sqlite",
   "recorded": "55326f7224316ae3de2a9e25084612dc24cc3bf7cd375e518e346b44bc8682da",
   "source": "seal_stage10.py prereg 2026-10-19 (entry 1, head at sealing)"
  },
  {
   "id": "stack_gate:prereg",
   "path": "engine/experiments/stack_gate/ledger.sqlite",
   "recorded": "a8d1e17f6bf21fc4a46744ec03fdbc085adfb8e4385302a61b7d6d4515ae939e",
   "source": "run_stack_gate.py prereg 2026-10-20 22:26 IST (entry 1, re-sealed after the recovery; the ledger lives in the main tree on the Mac)"
  },
  {
   "id": "stack_gate:final",
   "path": "engine/experiments/stack_gate/ledger.sqlite",
   "recorded": "55a8701c7e2105aa8e84ee35fa16220c8957598f596f1887367683cc1a07e6a7",
   "source": "run_stack_gate.py join 2026-10-21 03:05 IST: head after all 10 splits sealed and joined (verify ok)"
  },
  {
   "id": "stack_gate:refit_nf4r:final",
   "path": "engine/experiments/stack_gate/refit_nf4r/ledger.sqlite",
   "recorded": "7035e628eaa8dfe37dc35feb2ad8a4f7cb1973dbc7a0f2ba476e45fef057101e",
   "source": "stage9_refit.py run 2026-10-21: refit ledger head after evaluate (seq 813711); config model.stack_artifact.stack_gate_ledger_head_after_evaluate. Written in the s9-run worktree: copy the ledger (1 GB, git-ignored) into the main tree before --strict"
  },
  {
   "id": "stage9_gpu:test_part",
   "path": "engine/experiments/stage9/gpu_pass/ledger.sqlite",
   "recorded": "ffbf0d634bf7a43a88e452322fd51eceb2e72fad549380dd63186483b5fb2a06",
   "source": "the test_part readouts the refit used (entry seq 12; refit_report.json gpu_pass_ledger_head)"
  },
  {
   "id": "8_1c_nf4r:head",
   "path": "engine/experiments/8_1c/ledger_gemma_4_31b_base_nf4_retrain.sqlite",
   "recorded": "9277f7d265bdf7e6fcf1f04b8a5571ad8f5798cf6e17e6d89d4b37e120c3f731",
   "source": "g81n: all 10 splits sealed and joined (seq 24); config model.adapters.fills"
  }
 ],
 "holdout": {
  "hash_file": "data/sealed/HOLDOUT_SHA256.txt",
  "recorded": "1c62e0c5...ce77",
  "source": "RESUME.md line 35"
 },
 "holdout_text_hashes": {
  "amendment": "research/stage9/AMEND_holdout_text_fingerprint.json",
  "amendment_sha256": "27faf9f6b7880a70e706ca14d56995e1564826cda23997aa78b4226160d7b224",
  "tool": "engine/lens_engine/stage9/fingerprint.py",
  "tool_sha256": "ccb58ed739da100f21a6952a0d38ab553609aa34247766d996fbe6a4516ccbed",
  "output": "data/sealed/manifests/holdout_text_sha256.txt",
  "output_sha256": "c5956ea51b88a554037ffd39c00399de032da4b0a726522bb39b2359e180705a",
  "output_counts": {
   "n_empty_headlines": 0,
   "n_hashes": 15878,
   "n_headlines_distinct": 7891,
   "n_packages": 9995,
   "n_sealed_ids": 2110,
   "n_tests": 2110
  },
  "approved_to_run": true,
  "source": "section 3.3; owner approval 2026-10-19 relayed by the coordinator 2026-10-20"
 }
}
```
