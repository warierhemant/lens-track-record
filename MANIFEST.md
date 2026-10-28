# Manifest

Every file in this repository, with the reason it is here. Hashes are SHA-256. Files marked *copied* are byte for byte the files in the private Lens project at commit `74f4f35` (2026-10-27). The v1 config comes from the private commit `fe1c535` (2026-10-23), the one that published its line. The ledgers are the same bytes as the sealed originals, which the private project keeps outside git.

## Files in git

| File | SHA-256 | Why it is here |
|---|---|---|
| `.gitignore` | (written for this repository) | Keeps the two large ledgers and the venv out of git. |
| `README.md` | (written for this repository) | Plain-English summary and the verification steps. |
| `docs/track-record/HASHES.md` | (written for this repository) | The published-hash table. New lines are appended by dated commits. |
| `engine/experiments/stack_gate/refit_nf4r/ensemble.json` *copied* | `94ed011ee8860333...` | The frozen stack (manifest entry). Its sha256 prefix is the model version 94ed011ee886. |
| `engine/experiments/stack_gate/refit_nf4r/results_oof_ensemble_t98.json` *copied* | `6f2708de0aba0e7f...` | The sealed C98 threshold fit on non-holdout predictions (manifest entry). The analysis re-hashes and refits it. Derived from Upworthy. |
| `engine/experiments/stack_gate/refit_nf4r/s4_extended.json` *copied* | `c9a68292e2d22710...` | The sealed S4 threshold fit (manifest entry). |
| `engine/experiments/stage9/FROZEN_CONFIG.json` *copied* | `53933780bf8f6958...` | The frozen Stage 9 v2 config. |
| `engine/experiments/stage9/_archive/2026-10-23_first_seal/FROZEN_CONFIG_v1.json` *copied* | `b755abe15e295c71...` | The superseded v1 config, so the v1 config line stays checkable. |
| `engine/experiments/stage9/_archive/2026-10-23_first_seal/stage9_ledger.sqlite` *copied* | `e5a7dcd2114f2fbe...` | The superseded v1 ledger (one entry, the v1 config seal). |
| `engine/experiments/stage9/f1_openai/ledger.sqlite` *copied* | `3bcbe48d67e10cb7...` | The OpenAI F1 addendum's own ledger: the pre-registration seal, every batch decision and spend, every parsed answer, and the results seal. |
| `engine/experiments/stage9/gpu_pass/ledger.sqlite` *copied* | `50608c99023aa0c1...` | The Stage 9 GPU pass ledger (a manifest entry). Its head is named in the predictions manifest. |
| `engine/experiments/stage9/ledger.sqlite` *copied* | `1c6e8f218f4615b8...` | The Stage 9 v2 ledger: config seal, every prediction, the manifest, every outcome. |
| `engine/lens_engine/__init__.py` *copied* | `a7baa3e41b660b67...` | Empty package marker. |
| `engine/lens_engine/harness/__init__.py` *copied* | `e3b0c44298fc1c14...` | Empty package marker. |
| `engine/lens_engine/harness/ledger.py` *copied* | `a7031d90c9086207...` | The ledger format and lens_engine.harness.ledger.verify. |
| `engine/lens_engine/harness/metrics.py` *copied* | `8884c2b1be5f8fc1...` | Statistics used by the analysis (bootstrap, kappa, calibration). |
| `engine/lens_engine/paths.py` *copied* | `20f99dfcdb5b7adc...` | Path constants imported by the config module. |
| `engine/lens_engine/r0/__init__.py` *copied* | `1670f5942ade6afe...` | Empty package marker. |
| `engine/lens_engine/r0/decision.py` *copied* | `542402d0b357d3aa...` | Decision statistics used by the analysis. |
| `engine/lens_engine/stage9/__init__.py` *copied* | `8bcef1bb1f75f772...` | Empty package marker. |
| `engine/lens_engine/stage9/analysis.py` *copied* | `4376c23c7166dda5...` | Loads engine/scripts/stage9_analysis.py as a module. |
| `engine/lens_engine/stage9/config.py` *copied* | `81cd6044c0bb038a...` | Config helpers used by the runner and the synthetic config. |
| `engine/lens_engine/stage9/learner.py` *copied* | `a5cf4324e9e78ebc...` | Adapter hash checks imported by the config module. No training code. |
| `engine/lens_engine/stage9/mocks.py` *copied* | `46f3b2c1d1315bc2...` | Mock predictors for the null tests. No model, no network. |
| `engine/lens_engine/stage9/models.py` *copied* | `03d41e07d7aa7f67...` | Predictor interfaces the runner imports. It has a thin adapter class for the forecast service, and that service is left out. |
| `engine/lens_engine/stage9/nulls.py` *copied* | `1b3d4677fb7da49d...` | The outcome-side null tests the analysis runs. |
| `engine/lens_engine/stage9/publication.py` *copied* | `6f516b4eefa573cd...` | Reads published lines (imported by the runner). |
| `engine/lens_engine/stage9/report.py` *copied* | `ef7695e84dd844b3...` | Renders the report from results.json. Used by step 7 and the addendum command. |
| `engine/lens_engine/stage9/runner.py` *copied* | `2b45e6546e6f4aa2...` | Imported by the mock-harness null test, which runs a synthetic seal, predict and join with mock predictors. |
| `engine/lens_engine/stage9/sources.py` *copied* | `066524e5d763652e...` | Synthetic and blind data sources the runner imports. The real holdout source paths import modules that are left out. |
| `engine/scripts/prereg_check.py` *copied* | `82fbcfe3edb1221c...` | Recomputes every hash in a manifest. Standard library only. |
| `engine/scripts/stage9_analysis.py` *copied* | `934d9c8e627c3cf9...` | The Stage 9 analysis. Reads the ledger read-only and never opens the holdout. |
| `research/accuracy/PREREG_PACKAGE_v1.md` *copied* | `cd5c6a8cfe7d9226...` | Signed pre-registration package v1 (superseded the same day, kept so its published line stays checkable). |
| `research/accuracy/PREREG_PACKAGE_v2.md` *copied* | `9ffcd70a04f8b0d4...` | Signed pre-registration package v2. Its manifest block is the source of verify/PREREG_PUBLIC_SUBSET.md. |
| `research/stage9/AMEND_text_only_precollection.json` *copied* | `c404390fcc83ce82...` | Sealed amendment with the arm rule and spend rule (a manifest entry). |
| `research/stage9/F1_OPENAI_ADDENDUM_PREREG.md` *copied* | `ec1b8a119c87fa80...` | Pre-registration of the post-publication OpenAI F1 addendum, published before any OpenAI call. |
| `research/stage9/REPORT_F1_OPENAI_ADDENDUM.md` *copied* | `3a70ac4fe0a5af6c...` | The OpenAI F1 addendum report, rendered from results_f1_openai.json. |
| `research/stage9/REPORT.md` *copied* | `061e3ac13ecf3bb3...` | The published Stage 9 report. |
| `research/stage9/REPORT_F1_ADDENDUM.md` *copied* | `66cc2ad921e013ef...` | The 2026-10-24 addendum with the frontier-model block. |
| `research/stage9/bridge_set.json` *copied* | `ee0f60589b982277...` | Sealed list of non-holdout pair ids for the model-change bridge set (a manifest entry). Derived from Upworthy. |
| `research/stage9/results.json` *copied* | `d6c863ba520661b2...` | The published results file the report renders from. |
| `research/stage9/results_f1_openai.json` *copied* | `4cc07be2c37a8fdc...` | The OpenAI F1 addendum results, sealed by the addendum ledger's last entry. |
| `verify/LARGE_FILES.sha256` | (written for this repository) | sha256 of every ledger, for `shasum -a 256 -c`. |
| `verify/PREREG_PUBLIC_SUBSET.md` | (written for this repository) | The manifest entries this repository can check, copied unchanged from package v2. |
| `verify/requirements.txt` | (written for this repository) | numpy and scipy, pinned to the versions the run used. |
| `verify/verify_all.py` | (written for this repository) | Runs every check in the README, written for this repository. |

## Files attached to the release `ledgers-2026-10-23`

These are too large for git. Each is gzip-compressed. The SHA-256 below is of the uncompressed file and is also in `verify/LARGE_FILES.sha256`.

| File | SHA-256 | Why it is here |
|---|---|---|
| `engine/experiments/stack_gate/ledger.sqlite` (as `stack_gate_ledger.sqlite.gz`) | `9c983e6fb98e3094...` | The stack gate ledger. Entry 1 and the head are published lines. |
| `engine/experiments/stack_gate/refit_nf4r/ledger.sqlite` (as `stack_gate_refit_nf4r_ledger.sqlite.gz`) | `867db4fb2d1a2b45...` | The refit ledger that produced the Stage 9 model. Its head is a published line, and its sha256 is sealed in `s4_extended.json`. |

## Pre-registration entries left out

The manifest in `PREREG_PACKAGE_v2.md` has 109 file, canonical, contains and ledger entries plus two holdout entries. This repository checks 10 of them. The rest are left out for these reasons.

- **Earlier stages.** Plans, candidates, kernels and ledgers of the experiments before Stage 9 (8.1 to 8.12, the bakeoff, the R-0 runs, the survey, scaling and embedding tests, Stage 10). They are separate studies, and many of them are training or model code.
- **The app.** Grading plans and replay files used by the product.
- **The stack gate plan** (`stack_gate:PLAN`, `engine/experiments/stack_gate/PLAN.json`). It contains a private note that has nothing to do with the result. Its sha256 `ac003b8e2b6a6c04bb49f18c6f7453358f4ce367840f5753965d0cf7fa4ba60b` is sealed in entry 1 of both stack gate ledgers and in `ensemble.json`.
- **The holdout hash and the holdout text fingerprints** (`holdout` and `holdout_text_hashes`). Both live inside the sealed holdout folder, which stays closed.

Every entry left out, by id:

| Section | Id | Path |
|---|---|---|
| files | `8_1:CANDIDATES` | `engine/experiments/8_1/CANDIDATES.json` |
| files | `8_1b:CANDIDATES` | `engine/experiments/8_1b/CANDIDATES.json` |
| files | `8_1b:zeroshot_kernel` | `engine/experiments/8_1b/kaggle/zeroshot/lens_8_1b_zeroshot.py` |
| files | `8_5:PLAN` | `engine/experiments/8_5/PLAN.json` |
| files | `8_5_v2:PLAN` | `engine/experiments/8_5_v2/PLAN.json` |
| files | `r0_v2:PLAN` | `engine/experiments/r0_v2/PLAN.json` |
| files | `tpu_spike:PLAN` | `engine/experiments/tpu_spike/PLAN.json` |
| files | `tpu_spike:kernel_amendment` | `engine/experiments/tpu_spike/kaggle/kernel/lens_tpu_spike.py` |
| files | `8_6:ANALYSIS_PLAN` | `engine/experiments/8_6/ANALYSIS_PLAN.json` |
| files | `8_6:recognition_AMENDMENT` | `engine/experiments/8_6/recognition/AMENDMENT.json` |
| files | `8_7:PLAN` | `engine/experiments/8_7/PLAN.json` |
| files | `8_7:PREREG_describe_only` | `engine/experiments/8_7/PREREG_describe_only.json` |
| files | `8_10:PLAN` | `engine/experiments/8_10/PLAN.json` |
| files | `8_11:ANALYSIS_PLAN` | `engine/experiments/8_11/ANALYSIS_PLAN.json` |
| files | `8_12:PLAN` | `engine/experiments/8_12/PLAN.json` |
| files | `8_12:refit` | `engine/experiments/8_12/refit.json` |
| files | `bakeoff:PLAN` | `engine/experiments/bakeoff/PLAN.json` |
| files | `describe_ext:PLAN` | `engine/experiments/describe_ext/PLAN.json` |
| files | `r0_claude:PLAN` | `engine/experiments/r0_claude/PLAN.json` |
| files | `r0_opus:PLAN` | `engine/experiments/r0_opus/PLAN.json` |
| files | `r0_paraphrase:PLAN` | `engine/experiments/r0_paraphrase/PLAN.json` |
| files | `survey:PLAN` | `engine/experiments/survey/PLAN.json` |
| files | `grading:plans_file` | `app/src/lib/replay/sequential-plan.json` |
| files | `8_1c:PLAN` | `engine/experiments/8_1c/PLAN.json` |
| files | `8_1c:kernel_body` | `engine/experiments/8_1c/kernel/lens_8_1c.py` |
| files | `8_1c:AMEND_gemma_4_31b_base` | `engine/experiments/8_1c/AMEND_gemma_4_31b_base.json` |
| files | `8_1c:kernel_body_gemma31` | `engine/experiments/8_1c/kernel/lens_8_1c_gemma31.py` |
| files | `8_1c:AMEND_gemma_modal_l40s` | `engine/experiments/8_1c/AMEND_gemma_modal_l40s.json` |
| files | `8_1c:AMEND_origin_rule_removed` | `engine/experiments/8_1c/AMEND_origin_rule_removed.json` |
| files | `ruling:R-2026-10-19-origin-irrelevant` | `research/accuracy/rulings/R-2026-10-19-origin-irrelevant.md` |
| files | `scaling:PLAN` | `engine/experiments/scaling/PLAN.json` |
| files | `scaling:driver` | `engine/experiments/scaling/scaling.py` |
| files | `scaling:amend_qwen3_8b_base` | `engine/experiments/scaling/amend_qwen3_8b_base.json` |
| files | `scaling:amend_gemma_4_31b_base` | `engine/experiments/scaling/amend_gemma_4_31b_base.json` |
| files | `voyage_test:PLAN` | `engine/experiments/voyage_test/PLAN.json` |
| files | `voyage_test:voyage_embed` | `engine/experiments/voyage_test/voyage_embed.py` |
| files | `stage10:PLAN` | `research/stage10/PLAN_v1.md` |
| files | `stage10:stimuli_MANIFEST` | `research/stage10/stimuli/MANIFEST.json` |
| files | `stage10:plan.py` | `engine/lens_engine/stage10/plan.py` |
| files | `stage10:prompts.py` | `engine/lens_engine/stage10/prompts.py` |
| files | `stage10:aggregate.py` | `engine/lens_engine/stage10/aggregate.py` |
| files | `stage10:report.py` | `engine/lens_engine/stage10/report.py` |
| files | `stage10:AMENDMENT_01` | `research/stage10/AMENDMENT_01.md` |
| files | `stage10:panel-rule.ts` | `app/src/lib/panel-rule.ts` |
| files | `stage10:persona_p01` | `research/stage10/personas/p01.json` |
| files | `stage10:persona_p02` | `research/stage10/personas/p02.json` |
| files | `stage10:persona_p03` | `research/stage10/personas/p03.json` |
| files | `stage10:persona_p04` | `research/stage10/personas/p04.json` |
| files | `stage10:persona_p05` | `research/stage10/personas/p05.json` |
| files | `stage10:persona_p06` | `research/stage10/personas/p06.json` |
| files | `stage10:persona_p07` | `research/stage10/personas/p07.json` |
| files | `stage10:persona_p08` | `research/stage10/personas/p08.json` |
| files | `stage10:persona_p09` | `research/stage10/personas/p09.json` |
| files | `stage10:persona_p10` | `research/stage10/personas/p10.json` |
| files | `stage10:persona_p11` | `research/stage10/personas/p11.json` |
| files | `stage10:persona_p12` | `research/stage10/personas/p12.json` |
| files | `stage10:persona_p13` | `research/stage10/personas/p13.json` |
| files | `stage10:persona_p14` | `research/stage10/personas/p14.json` |
| files | `stage10:persona_p15` | `research/stage10/personas/p15.json` |
| files | `stage10:persona_p16` | `research/stage10/personas/p16.json` |
| files | `stage10:persona_p17` | `research/stage10/personas/p17.json` |
| files | `stage10:persona_p18` | `research/stage10/personas/p18.json` |
| files | `stage10:persona_p19` | `research/stage10/personas/p19.json` |
| files | `stage10:persona_p20` | `research/stage10/personas/p20.json` |
| files | `stage10:persona_p21` | `research/stage10/personas/p21.json` |
| files | `stage10:persona_p22` | `research/stage10/personas/p22.json` |
| files | `stage10:persona_p23` | `research/stage10/personas/p23.json` |
| files | `stage10:persona_p24` | `research/stage10/personas/p24.json` |
| files | `stack_gate:PLAN` | `engine/experiments/stack_gate/PLAN.json` |
| canonical | `grading:demo-obf-v1` | `app/src/lib/replay/sequential-plan.json` |
| canonical | `grading:customer-v1` | `app/src/lib/replay/sequential-plan.json` |
| contains | `8_3:demo-120:checkpoint_plan` | `app/src/data/replay/upworthy-demo-120.json` |
| contains | `8_3:demo-300:checkpoint_plan` | `app/src/data/replay/upworthy-demo-300.json` |
| contains | `8_3:demo-600:checkpoint_plan` | `app/src/data/replay/upworthy-demo-600.json` |
| ledgers | `8_1:head` | `engine/experiments/8_1/ledger.sqlite` |
| ledgers | `8_1b:head_6_splits` | `engine/experiments/8_1b/ledger.sqlite` |
| ledgers | `8_1b:amendment_seq_287197` | `engine/experiments/8_1b/ledger.sqlite` |
| ledgers | `8_1b:head_9_splits` | `engine/experiments/8_1b/ledger.sqlite` |
| ledgers | `8_6:head` | `engine/experiments/8_6/ledger.sqlite` |
| ledgers | `8_7:describe_alone_FROZEN` | `engine/experiments/8_7/ledger.sqlite` |
| ledgers | `8_10:test_seal` | `engine/experiments/8_10/ledger.sqlite` |
| ledgers | `8_11:head` | `engine/experiments/8_11/ledger.sqlite` |
| ledgers | `describe_ext:head` | `engine/experiments/describe_ext/ledger.sqlite` |
| ledgers | `bakeoff:head` | `engine/experiments/bakeoff/ledger.sqlite` |
| ledgers | `r0_claude:head` | `engine/experiments/r0_claude/ledger.sqlite` |
| ledgers | `r0_opus:head` | `engine/experiments/r0_opus/ledger.sqlite` |
| ledgers | `survey:head` | `engine/experiments/survey/ledger.sqlite` |
| ledgers | `8_12:head_btos` | `engine/experiments/8_12/ledger.sqlite` |
| ledgers | `8_1c:gemma_head` | `engine/experiments/8_1c/ledger_gemma_4_31b_base.sqlite` |
| ledgers | `8_1c:qwen_origin_amend_head` | `engine/experiments/8_1c/ledger_qwen3_14b_base.sqlite` |
| ledgers | `8_1c:gemma_origin_amend_head` | `engine/experiments/8_1c/ledger_gemma_4_31b_base.sqlite` |
| ledgers | `8_1c:mistral_origin_amend_head` | `engine/experiments/8_1c/ledger_mistral_small_24b_base.sqlite` |
| ledgers | `8_5:head` | `engine/experiments/8_5/ledger.sqlite` |
| ledgers | `8_5_v2:head` | `engine/experiments/8_5_v2/ledger.sqlite` |
| ledgers | `8_7:head` | `engine/experiments/8_7/ledger.sqlite` |
| ledgers | `8_1b:head_final` | `engine/experiments/8_1b/ledger.sqlite` |
| ledgers | `bakeoff:head_final` | `engine/experiments/bakeoff/ledger.sqlite` |
| ledgers | `stage10:prereg` | `engine/experiments/stage10/ledger.sqlite` |
| ledgers | `8_1c_nf4r:head` | `engine/experiments/8_1c/ledger_gemma_4_31b_base_nf4_retrain.sqlite` |
| holdout | `holdout_hash` | `data/sealed/HOLDOUT_SHA256.txt` |
| holdout_text_hashes | `amendment`, `tool`, `output` | `research/stage9/AMEND_holdout_text_fingerprint.json`, `engine/lens_engine/stage9/fingerprint.py`, `data/sealed/manifests/holdout_text_sha256.txt` |
