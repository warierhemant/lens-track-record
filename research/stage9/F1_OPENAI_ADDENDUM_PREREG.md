# Stage 9 F1 addendum: OpenAI frontier arms (pre-registration)

Written 2026-10-27, before any OpenAI call. This is a post-publication addendum to the Stage 9 v2 report. The published report, `research/stage9/results.json` and both Stage 9 ledgers stay exactly as they are. The owner approved real spend of about 40 to 90 USD on 2026-10-27 and added 100 USD of prepaid OpenAI credit.

## What runs

Three new F1 arms, zero-shot, on the same 2,110 sealed Upworthy holdout tests as Lens and the two Claude arms:

| Arm | Model id | Batch price per million tokens (input / output) |
|---|---|---|
| gpt_6_1_terra_zero_shot | `gpt-6.1-terra` | 0.50 / 2.50 USD |
| gpt_6_1_sol_zero_shot | `gpt-6.1-sol` | 1.00 / 5.00 USD |
| gpt_6_astra_zero_shot | `gpt-6-astra` | 5.00 / 25.00 USD |

Prices are OpenAI's published Batch rates (half the Standard rates) read on 2026-10-27. Cached input is counted at the full input price, so the spend figure can only run high.

## Requests

- The user messages are the exact texts the Claude F1 arms were sent. They are read from the sealed text-only pre-collection (`engine/experiments/stage9/precollect/requests.jsonl` sha256 `71b99ce85dddb2e2b6bd239b691f7ee14819601a47118add2b1699a105d3a900` and `index.jsonl` sha256 `854eacab632d0d6351c6eb74fc2a1731ec2c7f7bba6809e068f6d0ec0cac7b01`, each checked against the sha256 in the `stage9_pre:BUILD` entry of the pre-collection ledger, verified at the head the published Stage 9 predictions manifest names). Per model that is the Opus arm's 2,110 forward picks, 2,110 reversed picks and the 300-test recognition probe, 4,520 requests.
- Prompt templates: `engine/experiments/8_1/frontier_arm.py` PROMPT sha256 `1a50b6346ee8012ab83dcd6a33345d4336f60c060c5af5327132128d5e8fcdbe` and RECOG sha256 `9a63cc3d5d17996e520b5fd04b447820ba2a45bd669e6a741a3f5ab96058b7d3`, the values the frozen Stage 9 config holds.
- API: the OpenAI Batch API on `/v1/chat/completions`, one user message, no system message, no temperature.
- Reasoning setting, the same for all three models: `reasoning_effort: "low"`. The Claude arms ran at effort `low`, their lowest effort level. `low` is also the lowest effort that all three OpenAI models accept (Astra and Sol reject `none`). The API default is `medium`, which is further from how Claude ran.
- `max_completion_tokens: 512`. The Claude arms had `max_tokens: 512` with thinking counted inside it. OpenAI counts reasoning tokens inside this limit in the same way.

## Parsing and scoring

- Each reply is parsed by `precollect.parse_letter`, the parser the Claude arms used. The recognition probe also accepts N.
- An arm's score for a headline is 0.5 for each order in which it picked that headline. An invalid, missing, errored or expired pick gives no vote. This is the 8.1 rule the Claude arms used.
- Scores are attached to the published Stage 9 arm records the way `runner._frontier_fields` attached the Claude scores, and `stage9_analysis.frontier_endpoint` computes F1 with the frozen bootstrap (2,000 resamples clustered by test, seed 9000).
- Before any OpenAI number is computed, the scoring code re-derives both Claude arms through the same path. It refuses unless it reproduces the sealed arm records and the published F1 block exactly.
- Reported per model: L, its pick rate beside chance, Lens minus the arm with its 95% CI, whether Lens beats the arm (the CI lower bound is above 0) and the recognition-probe rates. Like every Upworthy number, these are provisional, and F1 sits after the hierarchy. It is never gated and proves no endpoint.

## Pilot

The pilot is the first 20 holdout tests by sha256 of `lens.stage9.f1_openai.pilot/1|` plus the test id, with their forward and reversed picks and any probe request, 42 requests per model. It measures real tokens, reasoning tokens included. Pilot answers are sealed and never scored. The full run re-sends every request, pilot tests included. The projected full cost per model is the pilot's mean cost per request of each kind times the full count of that kind.

Pilot gate: a model whose pilot gives a valid answer on fewer than half of its 42 requests is skipped (`f1oa:SKIP`), gets no full run and is reported as not run. This guards against paying for a full run whose replies are all cut off or empty. The tool stops after the pilots by default (`--until pilot`), so the projection is read and reported before any full chunk goes out.

## Spend rule and cap

- Hard cap 90 USD across all three models. The first `--max-usd` (90) is sealed at the first submit. A later lower value is sealed too, and the cap never rises.
- Chunks go out one at a time in this order: pilot Terra, pilot Sol, pilot Astra, then full Terra, full Sol, full Astra. Cheapest goes first, so a model that does not fit is the most expensive one left.
- Before each chunk, the actual spend so far plus that chunk's worst case (every request uses all 512 output tokens) must stay within the cap. The chunk's worst case must also fit in the credit left, which is the smaller of the figure given and the credit sealed at the first submit less the actual spend. If either check fails, `f1oa:STOPPED` is sealed and nothing more is sent. Any model left out is reported as not run, with the reason.
- A chunk whose batch fails validation (OpenAI bills nothing for it) is re-sent at most once more. After two failed attempts the run stops. An expired or cancelled chunk keeps the results it returned, a request with no result is a missing pick, and the chunk is never re-sent.
- If a create call's outcome is unknown, every submit is refused until `reconcile` either records the batch made from that upload or, at least 30 minutes later and on two listings of the server's batches, seals that no batch was made. A batch that still turns up later from that upload is recorded, collected and counted in the spend. Only the first collected batch of a chunk is scored.
- An INTENT entry is sealed before every create call and a SUBMIT entry right after it. Each chunk is collected and its actual spend sealed before the next decision. A server batch that is not in the ledger blocks every submit.
- Worst cases at build time: pilots 0.84 USD in total, full Terra 6.91 USD, full Sol 13.81 USD, full Astra 69.06 USD.

## The record

- Ledger: `engine/experiments/stage9/f1_openai/ledger.sqlite`. Entry 1, `f1oa:PREREG`, holds this file's sha256, the tool's sha256 (`engine/lens_engine/stage9/f1_openai.py`), the model ids, the settings, the prompt hashes, the pre-collection hashes and the chunk plan with each chunk's request-file sha256. The tool refuses to send anything unless this file and the tool still match that entry.
- The tool also refuses if `precollect.py`, `stage9_analysis.py` or `report.py` change after the seal, since it reuses their parser, votes rule, F1 endpoint and renderer.
- This file's sha256 and the ledger head after entry 1 are published in `docs/track-record/README.md` before any paid call.
- Scoring runs only once every full chunk is collected or skipped, or the run is STOPPED. It seals `f1oa:RESULTS` with the results file's sha256, and nothing can be sent after that.

## What gets published

- `research/stage9/REPORT_F1_OPENAI_ADDENDUM.md`, rendered by `f1_openai.render`. Its arm lines come from the existing renderer `report.frontier_lines`, and a table puts each OpenAI arm next to Lens, Opus and Sonnet. It is labelled as a post-publication addendum.
- `research/stage9/results_f1_openai.json`, with the F1 numbers, the reproduced Claude block, answer quality counts and the actual spend.
- The ledger's final head, as a new line in `docs/track-record/README.md`.
- Every model that ran is published, whatever its result. A model the spend rule left out, or one the pilot gate skipped, is listed as not run with its reason.
