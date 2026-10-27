# Public subset of the Stage 9 pre-registration manifest

This file holds a subset of the `prereg-manifest` block in `research/accuracy/PREREG_PACKAGE_v2.md`. Every entry below is copied from that block without any change. `verify/verify_all.py` checks this before it uses the file.

It exists because the full manifest also lists files that this repository does not publish: plans and code from earlier stages, the training and serving code, the app, and two hashes kept inside the sealed holdout folder. Those entries are listed by id in `MANIFEST.md`, with the reason each one is left out.

```json prereg-manifest
{
 "version": 1,
 "files": [
  {
   "id": "stage9:bridge_set",
   "path": "research/stage9/bridge_set.json",
   "expected_sha256": "ee0f60589b98227766a1f21803291da97ac263c6e2e1d8d1a47c3a917953d538",
   "source": "B5 (O3): drawn 2026-10-21 by engine/scripts/draw_bridge_set.py (package 2.5 rule); config bridge_set.sha256"
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
   "expected_sha256": "53933780bf8f695821c3fee2613f04299f2a2cf86550295c5d326e22e9e7a993",
   "source": "B9 2026-10-23 (fill-holdout-sha256), revised 2026-10-23 for option A (0c; the first value b755abe1...f38f is superseded); copy of research/stage9/FROZEN_CONFIG_DRAFT.json; sealed by seal-config as stage9:FROZEN"
  },
  {
   "id": "stage9:AMEND_text_only_precollection",
   "path": "research/stage9/AMEND_text_only_precollection.json",
   "expected_sha256": "c404390fcc83ce829846bfbf28b94e45fc01af0b52e13129723a859ca7c320c3",
   "source": "B4 re-approved 2026-10-23 for option A (0c, 2.7; approved_to_run true, tool 20b91892...3b67); the first approval a4c7fdef...154b is superseded"
  }
 ],
 "ledgers": [
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
  }
 ]
}
```
