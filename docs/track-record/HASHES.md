# Lens track record: published hashes

Each line below is a SHA-256 that Lens made public at the time shown, while the run was in progress. Together they fix what was decided before any outcome was read.

The lines were first published on those dates in the project's own records. This public repository opened on 2026-10-27 with all nine lines copied as they were. From now on, every new line is added here by its own dated commit, in the order a run produces it. A line is never edited or removed. A correction is a new line that names the line it corrects.

`python3 verify/verify_all.py` checks every line against the file or ledger entry in the last column.

| Date (IST) | Run | What | SHA-256 | Where to check it |
|---|---|---|---|---|
| 2026-10-23 07:22 | stage9-holdout-v1 | package | `cd5c6a8cfe7d92267a28e7d00e809466a3a514a25beb842d684e84ebca20cf78` | sha256 of research/accuracy/PREREG_PACKAGE_v1.md |
| 2026-10-23 07:45 | stage9-holdout-v1 | config | `b755abe15e295c7179f03a4ecdb3f19e952107ab56f820dae12e36163594f38f` | sha256 of the v1 config in engine/experiments/stage9/_archive/2026-10-23_first_seal/ |
| 2026-10-23 18:04 | stage9-holdout-v2 | package | `9ffcd70a04f8b0d48619efe67618b469b7195c572a43ed61ef257691c6861435` | sha256 of research/accuracy/PREREG_PACKAGE_v2.md |
| 2026-10-23 18:44 | stage9-holdout-v2 | config | `53933780bf8f695821c3fee2613f04299f2a2cf86550295c5d326e22e9e7a993` | sha256 of engine/experiments/stage9/FROZEN_CONFIG.json |
| 2026-10-23 22:16 | stage9-holdout-v2 | predictions-head | `6cb99dec7e891bd62e57aa4a59b1b8a29d6b2641f329dbae0c5d140bacbe3fe3` | entry 27087 of engine/experiments/stage9/ledger.sqlite |
| 2026-10-23 22:53 | stage9-holdout-v2 | final-head | `593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f` | last entry of engine/experiments/stage9/ledger.sqlite |
| 2026-10-23 22:55 | stack-gate | stack-gate-prereg | `a8d1e17f6bf21fc4a46744ec03fdbc085adfb8e4385302a61b7d6d4515ae939e` | entry 1 of engine/experiments/stack_gate/ledger.sqlite |
| 2026-10-23 22:55 | stack-gate | stack-gate-final-head | `55a8701c7e2105aa8e84ee35fa16220c8957598f596f1887367683cc1a07e6a7` | last entry of engine/experiments/stack_gate/ledger.sqlite |
| 2026-10-23 22:55 | stack-gate refit_nf4r | stack-gate-final-head | `7035e628eaa8dfe37dc35feb2ad8a4f7cb1973dbc7a0f2ba476e45fef057101e` | last entry of engine/experiments/stack_gate/refit_nf4r/ledger.sqlite |

**Superseded on 2026-10-23.** The two `stage9-holdout-v1` lines were sealed and then superseded the same day, before any paid call and before any outcome was read. The spending cap in package v1 was set on the worst case, and that cap blocked the text-only collection step. The owner chose to cap spending by actual spend instead, which is section 0c of package v2. The v1 package, config and ledger are kept here so that the v1 lines stay checkable. The run continued as `stage9-holdout-v2`, and every result in this repository comes from v2.

## What each line type means

- `package`: the pre-registration package, signed and published before the config was sealed. The config cannot carry this hash because the package lists the config's values. So the hash sits in this table and also in entry 1 of the run's ledger (`package_sha256`).
- `config`: the frozen config, published right after it was sealed as entry 1 of the run's ledger and before any prediction.
- `predictions-head`: the ledger head after every prediction was sealed and before any outcome was joined.
- `final-head`: the ledger head after the outcomes were joined.
- `stack-gate-prereg` and `stack-gate-final-head`: the sealed start and end of the earlier stack gate run that chose the model, and of its refit (`refit_nf4r`), which is the model Stage 9 used.
