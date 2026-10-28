# Stage 9 v2 report: F1 addendum (OpenAI frontier arms)

**This is a post-publication addendum, run on 2026-10-27.** The published Stage 9 v2 report, `research/stage9/results.json` and both Stage 9 ledgers were only read. The OpenAI arms were pre-registered in `research/stage9/F1_OPENAI_ADDENDUM_PREREG.md` and sealed in their own ledger before any OpenAI call.

- Pre-registration sha256: `ec1b8a119c87fa80829a6565666020e185b1e6998d7805c62b6e24ad49b28aa7`
- Addendum ledger head the results were scored at (before the f1oa:RESULTS seal): `d5120e3b45b83f8857914224edf2998c6d2b975f14ad133beca88298b8653f50`
- Stage 9 final head the arms were scored against: `593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f`
- `research/stage9/results_f1_openai.json` sha256: `4cc07be2c37a8fdc2784876706c3bb3ff201475a587d840772811e082d8ed815`
- Settings for every OpenAI arm: the Claude arms' exact user messages, reasoning_effort `low`, max_completion_tokens 512, OpenAI Batch API.
- Actual spend: 6.54 USD (cap 90 USD).
- Before any OpenAI number was computed, the scoring code re-derived the Opus and Sonnet arms through the same path and matched the published F1 block exactly.
- Like every Upworthy number in the report, these are provisional, and F1 sits after the hierarchy. It is never gated and proves no endpoint.

## All frontier arms on the same tests

| Arm | Model | Picked the best arm | Chance | L | Lens minus arm (95% CI) | Recognised in probe |
|---|---|---|---|---|---|---|
| Lens | Stage 9 stack | 49.9% | 25.2% | | | |
| opus_5_5_zero_shot | `claude-opus-5-5` | 35.7% | 25.2% | 0.140 | +14.3 pts (+11.8 pts to +16.6 pts) | 1 of 300 |
| sonnet_5_5_zero_shot | `claude-sonnet-5-5` | 34.5% | 25.2% | 0.124 | +15.4 pts (+13.1 pts to +17.8 pts) | 2 of 300 |
| gpt_6_1_sol_zero_shot | `gpt-6.1-sol` | 37.3% | 25.2% | 0.162 | +12.6 pts (+10.4 pts to +14.8 pts) | 1 of 300 |
| gpt_6_1_terra_zero_shot | `gpt-6.1-terra` | 36.8% | 25.2% | 0.154 | +13.2 pts (+10.9 pts to +15.5 pts) | 2 of 300 |
| gpt_6_astra_zero_shot | `gpt-6-astra` | 37.8% | 25.2% | 0.169 | +12.1 pts (+9.8 pts to +14.4 pts) | 0 of 300 |

The Opus and Sonnet rows are the published Stage 9 values, reproduced.

---

## Frontier arms (F1, after the hierarchy, never gated)

Label: post-publication addendum (2026-10-27), provisional, after the hierarchy, never gated. Each arm ran zero-shot on the same holdout tests as Lens; "Lens beats" an arm only if the 95% CI lower bound of Lens minus the arm is above 0.

- **gpt_6_1_sol_zero_shot**: L = 0.162; it picked the best arm 37.3% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.3% of the 300 probe tests (1 of 300), and the arm it named won 0.0% of those (0 of 1). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +12.6 pts (95% CI +10.4 pts to +14.8 pts). Lens beats this arm: yes.
- **gpt_6_1_terra_zero_shot**: L = 0.154; it picked the best arm 36.8% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.7% of the 300 probe tests (2 of 300), and the arm it named won 0.0% of those (0 of 2). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +13.2 pts (95% CI +10.9 pts to +15.5 pts). Lens beats this arm: yes.
- **gpt_6_astra_zero_shot**: L = 0.169; it picked the best arm 37.8% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.0% of the 300 probe tests (0 of 300). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +12.1 pts (95% CI +9.8 pts to +14.4 pts). Lens beats this arm: yes.

## Answer quality

- **gpt_6_1_terra_zero_shot**: 4520 of 4520 requests returned, 4520 gave a valid answer, 0 hit the 512-token limit.
- **gpt_6_1_sol_zero_shot**: 4520 of 4520 requests returned, 4520 gave a valid answer, 0 hit the 512-token limit.
- **gpt_6_astra_zero_shot**: 4520 of 4520 requests returned, 4520 gave a valid answer, 0 hit the 512-token limit.
