# Stage 9 addendum: MiroFish swarm arm (pre-registration)

**Status: final, pending the seal.** Drafted 2026-10-29 before any MiroFish call on any holdout test, and made final the same day with the owner's decisions below. It becomes binding when its sha256 is sealed as entry 1 (`mirofish:PREREG`) of a new ledger, `engine/experiments/stage9/mirofish/ledger.sqlite`. The published Stage 9 v2 report, `research/stage9/results.json`, both Stage 9 ledgers and the F1 OpenAI addendum stay exactly as they are.

## Owner decisions (2026-10-29)

- **Sample size: 150 tests.** The sealed number is final.
- **Hard spend cap: 15 USD** of OpenAI spend for the whole full run. The sealed cap never rises.
- **One MiroFish arm only.** The second MiroFish arm on `gpt-6.1-terra` is not run in this addendum. It would show what the swarm adds over the same model asked directly, and it would need its own compatibility check and its own pre-registration.

## The question

Does a multi-agent swarm simulation pick the winning headline of an Upworthy A/B test more often than chance, and how does it compare with Lens and with the zero-shot frontier arms on the same tests?

Lens's sealed record is 49.9% best-version picks on 2,110 holdout tests where chance is 25.2%. The best frontier arm (`gpt_6_astra_zero_shot`) picked the best version 37.8% of the time.

## What runs

- **System under test.** MiroFish (github.com/666ghj/MiroFish, AGPL-3.0) at commit `7657031ac01184afe2cb220f5ee3545573b5e843`, unmodified. It runs in its own folder at `~/lens-ext/mirofish`, outside every Lens repo. No MiroFish code is copied into Lens. Lens talks to it only over its HTTP API on 127.0.0.1.
- **Harness.** `~/lens-ext/mirofish-harness/mirofish_ab.py`, run in its full-run mode. Its sha256 is sealed in entry 1. The harness refuses to run if MiroFish is at any other commit or has modified tracked files.
- **Model.** `gpt-4o-mini` for every LLM call MiroFish makes. It is MiroFish's own default model. Standard prices are 0.15 USD per million input tokens and 0.60 USD per million output tokens (developers.openai.com/api/docs/pricing, read 2026-10-29). Cached input is charged at the full input price, so the spend figure can only run high.
- **MiroFish settings.** The Reddit platform only, run through MiroFish's parallel runner with Twitter switched off. That runner is the one that logs agent actions, which feed the run status and the Zep graph memory. The run has 24 simulation rounds per test, one simulated hour each, so the agents' active daytime hours are covered. A 10-round run starts at midnight and spends almost all of it in MiroFish's low-activity night hours, as the first pilot attempt showed. LLM persona generation is on with 5 profiles in parallel, graph memory update is on (MiroFish's own interface default), and everything else uses MiroFish defaults. The Twitter platform is left out because its feed ranker downloads a model from Hugging Face at run time, and a link-sharing feed with votes is the closer match to a news and viral content site. When a request names no output limit, the harness sets `max_completion_tokens` to 4,096.
- **End of a simulation.** After the last round MiroFish keeps the simulated world open and waits for commands. The harness treats the simulation as finished once MiroFish reports the Reddit run complete or the world waiting. It then closes the world through MiroFish's close-env endpoint and waits for the run to reach a terminal status, which MiroFish requires before it writes a report.
- **Transient provider errors.** A network error or an HTTP 429 or 5xx reply from OpenAI is retried exactly once by the harness, after the cap is checked again. A network error is charged its worst case, since it is unknown whether it was billed. Before each test the harness waits for api.openai.com to answer at all, for up to 20 minutes.
- **Memory store.** Zep Cloud, which MiroFish requires. Each test's graph is deleted after its answer is recorded.

## What MiroFish is given for each test

The seed is one short Markdown document with three parts:

1. One sentence saying a news and viral content website will publish one story and wrote k versions of its headline for a live test.
2. The versions, labelled A to E in a fixed order. The order is the arms sorted by sha256 of `lens.ext.mirofish.order/1|` plus the test id plus `|` plus the arm id.
3. A neutral audience description: ordinary visitors to a news and viral content website who arrive from social feeds, newsletters and the front page, skim headlines and click the ones they want to read. Each reader sees one version at random.

The prediction requirement is: "Predict which headline version will get the most clicks from readers of a news and viral content website when each reader is shown one version at random. The prediction must name exactly one version letter."

No outcome, no click count, no source name and no date is given. The seed does not say the tests come from Upworthy.

After MiroFish's ReportAgent writes its report, the harness asks the ReportAgent one fixed question through MiroFish's report chat endpoint. The question asks which single version will get the most clicks and tells it to end with one line in the form `ANSWER: <letter>`, or `ANSWER: N` when the simulation gives no basis to choose.

## Sample

- The sample is drawn from the same 2,110 sealed Upworthy holdout tests that Lens and the F1 arms ran on. The texts come from the sealed text-only pre-collection (`engine/experiments/stage9/precollect/requests.jsonl`, `index.jsonl` and `arms.jsonl`), checked against the sha256 values in the `stage9_pre:BUILD` entry, the same source and the same checks the F1 OpenAI addendum used. Each headline is read from the Opus arm's forward-order pick request and must match the sha256 of its text in `arms.jsonl`.
- Access goes through a new module, `lens_engine.stage9.mirofish`. Like the F1 OpenAI addendum, it never reads `data/sealed` and never passes `allow_holdout`. It refuses any caller outside `lens_engine.stage9`, as the holdout guard does, and it logs every access to `engine/experiments/stage9/mirofish/ACCESS_LOG.txt` with the time, the purpose and a count. That module hands MiroFish headline texts only. Outcomes are read only by the scoring step, after the predictions are sealed, from the published Stage 9 ledger at its final head.
- Eligible tests are those with 2 to 5 headline versions. The count of tests left out for having more than 5 is reported.
- The sample is the first 150 eligible tests by sha256 of `lens.stage9.mirofish.sample/1|` plus the test id. This is the selection rule the F1 addendum used for its pilot, with its own seed string. The owner set the size at 150 on 2026-10-29.
- Why 150: at a pick rate near 40%, the 95% interval on one arm is about plus or minus 8 points. The comparison with Lens is paired on the same tests, so its interval is narrower than that.

## Parse rule

- The reply is read line by line. A line counts when, with every bold mark (asterisk) removed and its ends trimmed, it reads `ANSWER:` followed by one letter, with case ignored. The last such line decides.
- A letter within the test's k versions is a pick.
- `N` is recorded as "cannot tell".
- Anything else, including no such line or a letter beyond k, is recorded as invalid.
- The question is never re-asked, and a reply is never read by a person or a second model to recover a pick.
- The harness applies this rule as each test finishes. The ingest step applies it again to every raw reply and refuses the predictions file if any result differs.

## Abstain and failure handling

- "Cannot tell" and invalid replies count as a miss in the primary pick rate. They are also reported separately as counts.
- Each stage has a time limit: graph build 30 minutes, preparation 30 minutes, simulation 40 minutes, closing the world 15 minutes and the report 60 minutes. A stage that runs past its limit is a failure, recorded with the stage name and MiroFish's last reported status.
- A test during which the host machine slept counts as a pipeline failure. The harness detects sleep by comparing the wall clock with the monotonic clock, and it holds an idle-sleep block while it runs. It checks at the end of every stage and again after the ask, so a sleep during any single call fails the attempt in that stage. A sleep during the ask counts as a miss, under the ask-step rule below. The ingest step refuses a test recorded as finished whose last attempt saw a sleep.
- A test whose pipeline fails before the question is asked (graph build, preparation, simulation or report error) is re-run once from the start. A second failure counts as a miss and is reported with its stage.
- A failure in the ask step itself counts as a miss and is never re-run, because the question is never re-asked.
- There is one full run. The harness refuses to start a second fresh run for the same entry 1, and the ingest step refuses unless exactly one run folder names entry 1 and the predictions file is the one inside it. A run cut off by a crash or a power loss resumes from its own files. An attempt that was cut off counts as a failed attempt. It gets the single re-run when the question had not yet been sent, and it counts as a miss when it had.
- A test left unrun because the spend cap was reached is reported as not run. A test that was in progress when the cap was reached is also reported as not run. The scores are then computed on the tests that ran, with Lens and the F1 arms scored on the same tests. The sample order is a hash order, so the tests that ran are still a fixed-seed draw.

## Scoring

- **Primary.** Best-version pick rate: the share of scored tests where MiroFish's pick is the best arm under the Stage 9 frozen definition. MiroFish's hit on a test is 1 when its pick is a best arm and 0 otherwise. A cannot-tell, invalid or failed test scores 0. Ties and null tests are handled the way the Stage 9 best-of-k endpoint handles them.
- **Chance line.** The mean of 1/k over the scored tests, where k is the number of arms the Stage 9 outcome read kept for that test. That can be fewer than the versions MiroFish was shown.
- **Dropped arms.** A valid MiroFish pick of an arm the outcome read dropped scores 0 and is reported as a separate count (`n_pick_off_record`).
- **Lift.** L = (pick rate minus chance) divided by (1 minus chance), the Stage 9 definition.
- **Intervals.** 95% percentile bootstrap with 2,000 resamples clustered by test and seed 9000, the frozen Stage 9 method. Each pick rate, each lift and each paired difference gets one.
- **Comparisons.** Lens minus MiroFish and the best F1 arm minus MiroFish, each paired on the same tests with the same bootstrap. The best F1 arm is `gpt_6_astra_zero_shot`, the frontier arm with the highest pick rate on all 2,110 tests in the published results. The same paired difference is also reported for each of the other four frontier arms (Opus, Sonnet, `gpt_6_1_sol_zero_shot` and `gpt_6_1_terra_zero_shot`). Lens and the F1 arms are re-scored from their sealed predictions. Nothing about them is re-run.
- **Reproduction check.** Before any MiroFish number is computed, the scoring step re-scores the Opus and Sonnet arms and the three OpenAI arms on all 2,110 tests from their sealed predictions. It refuses to go on unless they match the published F1 numbers exactly.
- **Differences stated beside every comparison.** MiroFish sees one fixed order per test and its pick scores 1 or 0. The F1 arms saw two orders and scored 0.5 per order. A MiroFish test with no valid pick scores 0, and an F1 arm with no valid pick gets chance credit, because the Stage 9 best-of-k rule splits a tie among the kept arms. The same split gives an F1 arm chance credit when its pick is an arm the outcome read dropped, where MiroFish scores 0. These three differences are stated beside every comparison.
- **Secondary, labelled as such.** The pick rate among answered tests only, the cannot-tell rate, the invalid rate, the count of failed tests by stage, mean agents per test, mean rounds run and mean USD per test.
- Like every Upworthy number, these results are provisional and sit after the Stage 9 hierarchy. They are never gated and prove no endpoint.

## Pilot (already run, separate from this run)

- Five Upworthy tests from the training side of split 00, drawn through `lens_engine.data.loaders` with the holdout guard on. Headlines only. The pilot is never scored.
- It measured real tokens per test, phase by phase, and parse reliability.
- Pilot gate: if fewer than 3 of the 5 pilot tests end in a valid pick or "cannot tell", the full run does not go ahead under this pre-registration.
- The projected full cost is the pilot's mean cost per test times the sample size.
- Pilot result (run `runs/20261029T102106Z`, 2026-10-29): all 5 tests finished with a valid pick, at a mean of 0.055 USD and 6 minutes per test, so the gate is passed. At 150 tests that projects to about 8 USD, and the owner set the cap at 15 USD.

## Spend rule and cap

- Every LLM request goes through a local metering proxy in the harness. MiroFish never holds the OpenAI key.
- Before each request, the actual spend so far plus open reservations plus that request's worst case (one token per byte of request, plus every allowed output token) must stay within the cap. Otherwise the proxy refuses, the run stops and nothing more is sent.
- After each reply, the real usage from the API response is charged. An HTTP 400 or higher reply with no usage block is charged 0 USD, because OpenAI does not bill a refused request. Any other reply without usage is charged its worst case. If a reply's real usage ever passes its reservation, that is logged, and the next cap check counts the real figure.
- The proxy only forwards requests whose message content is plain text, so one token per byte of request bounds the input. Content may also be absent, which is allowed only for an assistant message that carries a tool call. A request carrying an image, audio or a file is refused.
- The proxy forwards only the request fields MiroFish and its simulation library send at the pinned commit, and it refuses any other field, such as `prediction`. A `service_tier` is allowed only when it is absent, `auto` or `default`.
- At exit the harness first stops taking new reservations, including the second try of a retried request. It then waits a bounded time for requests still in flight. Any reservation still open after that is charged its worst case before the final spend is written.
- The cap is 15 USD, set by the owner on 2026-10-29. It is the pilot projection times 1.5, rounded up to the next 5 USD. The harness reads the cap from entry 1. A lower cap can be given at run time, and a higher one is refused.
- Spend carries over when a run resumes. Every reservation is written down, with a random id, before its request is sent, so a request that was open when the run was cut off is charged its worst case.
- Zep Cloud usage is reported from the Zep dashboard. It is outside the USD meter.

## Sealing and order of events

1. Entry 1, `mirofish:PREREG`, holds this file's sha256, the harness sha256, the MiroFish commit, the model id, the prices, every setting above, the sample size, the sha256 of the sampled test id list and the cap. It also holds the sha256 of the Lens module and of the Stage 9 code it reuses. The harness's own copy of the settings must match the sealed settings before the seal is made.
2. The harness refuses to send anything unless this file, the harness and the MiroFish checkout still match entry 1, and unless the exported sample matches the sealed test id list.
3. Every test's raw reply, parsed pick and spend is written as it finishes. When the last test finishes or the run stops, the harness writes the predictions file. The ingest step checks it against entry 1 and seals its sha256 as `mirofish:PREDICTIONS`. The harness refuses to run once that entry exists.
4. Only after that seal does the scoring step read any outcome. It seals `mirofish:RESULTS` with the results file's sha256, and nothing can be sent after that.

## Data leaving the machine

The holdout headlines go to OpenAI, as they did for the F1 arms, and to Zep Cloud, which is new. Zep holds each test's graph only until that test's answer is recorded, then the harness deletes it. The Upworthy archive is already public.

## What gets published

- An addendum report labelled as a post-publication addendum, with the MiroFish arm beside Lens, Opus, Sonnet and the three OpenAI arms on the same tests.
- A results file with the pick rate, chance, lift, intervals, parse counts and the actual spend.
- The ledger's final head, as a new line in `docs/track-record/README.md`.
- The result is published whatever it shows. If the cap stops the run, that is reported with the reason.
