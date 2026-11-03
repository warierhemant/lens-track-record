# Stage 9 F1 addendum: Claude Fable 5.1 arm (pre-registration)

**Status: written 2026-11-03, before any Fable call. The owner approved the spend in chat on 2026-11-03, with a hard cap of 30 USD.**

## Why this exists

Claude Fable 5.1 was left out of the earlier comparison. Stage 9 ran Claude Opus 5.5 and Claude Sonnet 5.5, and the first addendum added three OpenAI models. Fable 5.1 is Anthropic's most capable widely released model, so the comparison has a plain gap until it is tested.

**The result is reported whichever way it goes, including if Fable beats Lens.** The report states on its own line whether Fable beats Lens, meaning the 95% CI of Lens minus Fable lies wholly below 0. The published Stage 9 report, `research/stage9/results.json`, the OpenAI addendum and their ledgers stay exactly as they are.

## What runs

One new F1 arm, zero-shot, on the same 2,110 sealed Upworthy holdout tests as Lens and the other arms.

| Arm | Model id | Batch price per million tokens (input / output) |
|---|---|---|
| fable_5_1_zero_shot | `claude-fable-5-1` | 5.00 / 25.00 USD |

Price source: the Batch processing table at `platform.claude.com/docs/en/about-claude/pricing.md`, read on 2026-11-03. The input price and the output price both come from that table, and `shared/models.md` in the claude-api skill gives the same two figures.

## Requests

- The requests are the Opus arm's own: 2,110 forward picks, 2,110 reversed picks and 300 recognition probes, 4,520 in all. They come from the sealed text-only pre-collection, `engine/experiments/stage9/precollect/requests.jsonl` sha256 `71b99ce85dddb2e2b6bd239b691f7ee14819601a47118add2b1699a105d3a900` and `index.jsonl` sha256 `854eacab632d0d6351c6eb74fc2a1731ec2c7f7bba6809e068f6d0ec0cac7b01`. The tool checks each file against the `stage9_pre:BUILD` entry of the pre-collection ledger, verified at the head the published Stage 9 predictions manifest names.
- Each request's parameters are read from that file, and only the model id changes. The file holds `max_tokens: 512`, `output_config: {"effort": "low"}` and one user message. It sets no system message, no `thinking` field and no temperature. The tool refuses any sealed request with another shape.
- API: the Anthropic Message Batches API, `POST /v1/messages/batches`.
- No fallback is requested, because a fallback would answer with another model. A result from any other model stops collection.
- Prompt templates: PROMPT sha256 `1a50b6346ee8012ab83dcd6a33345d4336f60c060c5af5327132128d5e8fcdbe` and RECOG sha256 `9a63cc3d5d17996e520b5fd04b447820ba2a45bd669e6a741a3f5ab96058b7d3`, the values the frozen Stage 9 config holds.
- Request-file hashes at build time: pilot `61f9779ba82a86636b3e688c4d868c453ebd02cc40be259fdfb101093acb0f7f`, full `b3595268e39165b3b1e006a546c808b2d9e6133f46b3039300df352793b28e1f`.

## Parsing and scoring

- Each reply is parsed by `precollect.parse_letter`, the parser every earlier arm used. The recognition probe also accepts N.
- A headline scores 0.5 for each order in which the arm picked it. An invalid, missing, errored, expired or refused request gives no vote. A refusal is treated as no answer even if it carries partial text. The Claude arms had no refusals, so this rule changes nothing on their data.
- The parser reads only the start of the reply. It skips any symbols and spaces, allows the word Option, takes one letter from A to Q in either case, and requires that no letter comes straight after it. So `**B` is valid and votes B, `Because` is invalid, and `A good headline` votes A, even though that A was only the first word of a sentence. A letter beyond the number of options is invalid. A reply cut at the 512-token limit goes through this same parser, as on the Claude arms. If it has no text, or its text fails the parser, it is a missing pick. If its text passes, it votes. The report counts cut replies and, among them, those that were still valid.
- Scores are attached to the published Stage 9 arm records with `f1_openai.attach`, and `stage9_analysis.frontier_endpoint` computes F1 with the frozen bootstrap (2,000 resamples clustered by test, seed 9000).
- The code re-derives the two Claude arms and the three OpenAI arms from their sealed answers before the seal and again before scoring. It refuses unless they match `results.json` and `results_f1_openai.json` exactly.
- Reported: L, the pick rate beside chance, Lens minus the arm with its 95% CI, whether Lens beats the arm, whether the arm beats Lens, the recognition-probe rates and the answer quality counts. Like every Upworthy number, these are provisional. F1 sits after the hierarchy, is never gated and proves no endpoint.

## Pilot

The pilot uses the same 20 tests as the OpenAI addendum, with their forward and reversed picks and any probe request, 42 requests. Its answers are sealed and never scored. The full run re-sends every request. 
Pilot rule: if fewer than half of the 42 requests give a valid answer, the full run is skipped (`f1fa:SKIP`) and the arm is reported as not run, with the reason.

## The go rule

After the pilot, the full run goes out if and only if the pilot rule passes and the full-run spend gate below passes. Nobody chooses based on what the pilot shows. `run --until full` applies this rule with no pause between the pilot and the full run. Once the pilot's results exist, `decline` and a lower `--max-usd` both refuse. If the full chunk is not sent within 24 hours of the pilot's seal, the arm is reported as not run, with the time as the reason.

Every stop has a reported reason: spend rule, pilot rule, create call, time, owner declined or refusal. The owner can stop the run with `decline` only before the first submit, and the report states it as owner declined. `score` and `report` then still produce a published result that lists the arm as not run, with the pilot's counts when a pilot ran.

If a fail-closed check refuses in collection or scoring, for example a reply from another model, `close-refusal` re-runs those steps and takes the reason from the refusal itself. It seals the arm as not run with that reason and writes the results file and the report, with nothing scored. It first checks that this file and the tool still match the seal, and refuses if they differ. It closes nothing if no check refuses. Only the tool's own fail-closed refusals in collection and scoring count. Any other error, such as a network failure or a missing file, stops the command and seals nothing. Any batch left uncollected is named in the report, because its cost is missing from the actual spend.

## Cost and spend rule

| Figure | Pilot | Full run | Total |
|---|---|---|---|
| Expected, at the Opus arm's measured tokens | 0.17 USD | 17.89 USD | about 18 USD |
| Absolute worst case, every request at 512 output tokens | 0.64 USD | 69.06 USD | 69.70 USD |

- Expected arithmetic: the Opus arm used 1,062,772 input tokens and 502,945 output tokens on these requests. 1,062,772 x 5 / 1,000,000 + 502,945 x 25 / 1,000,000 = 17.89 USD. Fable always thinks, so its output may run above this figure. The pilot measures it.
- Worst-case arithmetic for the full run: input is bounded by characters / 2 + 200 tokens per request, 2,240,919 tokens, or 11.20 USD. Output is bounded by 512 tokens x 4,520 requests, 2,314,240 tokens, or 57.86 USD. Together that is 69.06 USD.
- Hard cap: 30 USD, which leaves room for other API use. The first `--max-usd` is sealed at the first submit. A lower value given before the pilot's results exist is sealed too. The cap never rises.
- Pilot spend gate: actual spend plus the pilot's worst case, 0.64 USD, must stay within the cap and within the credit left.
- Full-run gate: projected = 4,520 x (the pilot's mean input tokens per request x the ratio of full-run to pilot characters per request x 5 USD per million + the pilot's mean output tokens per request x 25 USD per million) x 1.25. The ratio is 0.9712, from 2,673,838 characters over 4,520 requests and 25,582 characters over 42 requests. It corrects for the pilot's different mix of picks and probes. The means come from the pilot results whose hash is sealed in the SPEND entry. Actual spend plus projected must stay within the cap, and projected must fit in the credit left. Credit left already has actual spend taken off. It is the smaller of the figure given and the credit sealed at the first submit less actual spend.
- The credit figure given to the tool is the balance read from the console at that moment.
- If a gate fails, `f1fa:STOPPED` is sealed, nothing more is sent, and the report gives the spend rule as the reason.
- Where it stops: at Opus's measured pilot usage (246.0 input and 110.2 output tokens per request), projected is 22.32 USD, and with the 0.17 USD pilot the gate figure is 22.49 USD, so the full run goes out. The gate stops the run when the pilot costs more than about 0.00528 USD per request after scaling. At Opus's input level, that is a mean above about 163 output tokens per request, or about 1.48 times Opus's output. The arm is then reported as not run, with the spend rule as the reason.
- Actual spend is input and output tokens at the pinned prices. Output tokens include thinking. A succeeded result always counts, refusals included, so the figure can only run high. Errored, canceled and expired requests are not billed, according to the batch processing documentation.
- A create call that made no batch is tried at most twice, then the run stops. An ended batch is never re-sent.

## Why the rule changed before sealing, and the limits on spend

The first version of this rule required the full run's 69.06 USD worst case to fit in the credit. The API credit balance was read at 34.17 USD on 2026-11-03, with auto-reload off, so that gate could never pass. The rule was changed for the full run only, before sealing and before any Fable call. The pilot spend gate still uses the worst case.

The spend limits are these:

- The balance is prepaid and auto-reload is off, so the balance is the hard stop on what the run can charge. The batch processing documentation warns that batches may go slightly over a Workspace spend limit because of their throughput, so a small overrun at that stop cannot be ruled out.
- The 30 USD cap is checked before each chunk goes out. Once the full batch is out, the tool does not watch or cancel it. If the full run costs more than 1.25 times what the pilot measured, the actual bill can pass 30 USD, and only the balance limits it. The cap is a gate on sending, and the balance is the limit on charging.
- If the balance runs out during the batch, the requests it cuts off come back errored. They count as missing picks and give no vote, under the rule for missing picks above, and the report publishes their count in its answer quality line. They are never re-sent.

## The record

- Ledger: `engine/experiments/stage9/f1_fable/ledger.sqlite`. Entry 1, `f1fa:PREREG`, holds this file's sha256, the tool's sha256, the sha256 of the reused code (`f1_openai.py`, `precollect.py`, `stage9_analysis.py`, `report.py`), the settings, prices, prompt hashes, pre-collection hashes, the reproduction hash and the chunk plan. The tool refuses to send anything if any of these change.
- An INTENT entry is sealed before every create call and a SUBMIT entry right after it. Each chunk is collected and its actual spend sealed before the next decision.
- A server batch that is not in the ledger blocks every submit. Message Batches carry no metadata, so `reconcile` matches a batch to an open INTENT by its request count and creation time, and collection then requires its exact custom ids. A batch of another size is recorded as another job's (`f1fa:FOREIGN`).
- This file's sha256 and the ledger head after entry 1 are published in `docs/track-record/README.md` before any paid call.

## What gets published

- `research/stage9/REPORT_F1_FABLE_ADDENDUM.md`, rendered by `f1_fable.render`, labelled as a post-publication addendum, with Fable beside Lens and all five published arms.
- `research/stage9/results_f1_fable.json`, and the ledger's final head as a new line in `docs/track-record/README.md`.
- If the arm does not reach the full run, these two files are still published. They list it as not run, with the reason and the pilot's counts.

## Checks at run time

1. **Parameters on Fable 5.1.** The documentation says Fable 5.1 accepts `effort: "low"`, `max_tokens: 512` and an omitted `thinking` field, and the batch documentation lists the model. The pilot is the first live test. If Fable rejects a parameter, the requests come back errored and the pilot rule skips the full run. Any change to a parameter needs a new pre-registration.
2. **The 512-token limit.** Thinking counts inside it. Fable may hit the limit more often than Opus, whose 4,520 requests all ended normally. A cut reply that fails the parser is a missing pick and lowers Fable's score. A cut reply that passes it still votes, under the parser rule in Parsing and scoring. The limit stays, for parity with the Opus arm, and the report publishes both counts.
3. **Data retention.** Fable 5.1 requires 30-day retention, and an organisation on zero data retention gets a 400. Check the account's setting before the pilot.
4. **The reproduction check.** It passed on 2026-11-03 against the main checkout, and `seal-prereg` runs it again before sealing.
5. **The track record.** Publish this file's sha256 and the ledger head after entry 1 before any paid call.
