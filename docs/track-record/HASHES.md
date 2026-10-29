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
| 2026-10-27 10:41 | stage9-f1-openai-addendum | f1-openai-prereg | `ec1b8a119c87fa80829a6565666020e185b1e6998d7805c62b6e24ad49b28aa7` | sha256 of research/stage9/F1_OPENAI_ADDENDUM_PREREG.md |
| 2026-10-27 10:41 | stage9-f1-openai-addendum | f1-openai-prereg-head | `4eb9b89b54ac327292f49d8c856342460e1ff94f3af6f0e7c8e5d5260000aa0f` | entry 1 of engine/experiments/stage9/f1_openai/ledger.sqlite |
| 2026-10-28 06:10 | stage9-f1-openai-addendum | f1-openai-final-head | `dfd57e615ece4accb05ef5f3bd2db68910b7bf896fa60fdcdf3d1dbb4f6c0572` | last entry of engine/experiments/stage9/f1_openai/ledger.sqlite |
| 2026-10-29 04:21 | stage9-arxiv399-addendum | arxiv399-prereg | `93443b467bb36e7b1397fb99d37dc961f3f85c9101e997836494d3ca70a7b1be` | sha256 of research/stage9/ARXIV399_PREREG.md (published with the results) |
| 2026-10-29 04:21 | stage9-arxiv399-addendum | arxiv399-prereg-head | `cce940aec5e5cb904385584e62df311837a62cf9d2fd2730e3caba850db99e51` | entry 1 of engine/experiments/stage9/arxiv399/ledger.sqlite (published with the results) |
| 2026-10-29 19:25 | stage9-mirofish-addendum | mirofish-prereg | `c4b50da92d989a1c8e87fd9f7b4f9c5c60a0161050ce6b67512658604ae70b37` | sha256 of research/stage9/MIROFISH_PREREG.md (published with the results) |
| 2026-10-29 19:25 | stage9-mirofish-addendum | mirofish-prereg-head | `f68beec4cd13256973e90f1a8939040d8b4bd8687b12f2e564d456b1619d05e2` | entry 1 of engine/experiments/stage9/mirofish/ledger.sqlite (published with the results) |

**Superseded on 2026-10-23.** The two `stage9-holdout-v1` lines were sealed and then superseded the same day, before any paid call and before any outcome was read. The spending cap in package v1 was set on the worst case, and that cap blocked the text-only collection step. The owner chose to cap spending by actual spend instead, which is section 0c of package v2. The v1 package, config and ledger are kept here so that the v1 lines stay checkable. The run continued as `stage9-holdout-v2`, and every result in this repository comes from v2.

## What each line type means

- `package`: the pre-registration package, signed and published before the config was sealed. The config cannot carry this hash because the package lists the config's values. So the hash sits in this table and also in entry 1 of the run's ledger (`package_sha256`).
- `config`: the frozen config, published right after it was sealed as entry 1 of the run's ledger and before any prediction.
- `predictions-head`: the ledger head after every prediction was sealed and before any outcome was joined.
- `final-head`: the ledger head after the outcomes were joined.
- `f1-openai-prereg` and `f1-openai-prereg-head`: a post-publication addendum that adds three OpenAI models as frontier arms on the same Stage 9 tests. The first is the sha256 of its pre-registration. The second is entry 1 of its own ledger, which seals that pre-registration. Both were published before any OpenAI call. The published Stage 9 files are only read by it.
- `f1-openai-final-head`: the addendum ledger's head after scoring. That last entry, `f1oa:RESULTS`, seals the sha256 of research/stage9/results_f1_openai.json.
- `arxiv399-prereg` and `arxiv399-prereg-head`: a post-publication addendum that scores Lens on the 399 Upworthy tests of arXiv 2609.25010, leaving out every test a Lens model was fit on. The first is the sha256 of its pre-registration. The second is entry 1 of its own ledger, which seals that pre-registration. Both are published here as hashes only, before any paid call. The pre-registration and the ledger are added with the results, and then these two lines can be checked.
- `mirofish-prereg` and `mirofish-prereg-head`: a post-publication addendum that runs MiroFish, an open-source multi-agent swarm simulator, on 150 of the Stage 9 tests and scores it against Lens and the frontier arms on the same tests. The first is the sha256 of its pre-registration. The second is entry 1 of its own ledger, which seals that pre-registration with a 15 USD cap. Both are published here as hashes only, before any MiroFish call on a holdout test. The pre-registration and the ledger are added with the results, and then these two lines can be checked.
- `stack-gate-prereg` and `stack-gate-final-head`: the sealed start and end of the earlier stack gate run that chose the model, and of its refit (`refit_nf4r`), which is the model Stage 9 used.
