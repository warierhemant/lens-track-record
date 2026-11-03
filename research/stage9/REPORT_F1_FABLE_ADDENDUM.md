# Stage 9 v2 report: F1 addendum (Claude Fable 5.1 arm)

**This is a post-publication addendum.** This model was left out of the earlier comparison. The arm was pre-registered in `research/stage9/F1_FABLE_ADDENDUM_PREREG.md` and sealed in its own ledger before any call. The result is reported whichever way it goes.

- Pre-registration sha256: `222af630062c2ea68149888982efb0d6f5c89f91434ae97ea6b6fccced44c2c2`
- Addendum ledger head the results were scored at: `84abdbb3f7b0a4c46e957d10c8ee14d60c499c23854b62d3d3fe21322fa3e505`
- `research/stage9/results_f1_fable.json` sha256: `0069e7f1aee51c1c25c7fa831a7213090a27da08070510acea3acccb73481d22`
- Settings: the Opus arm's exact requests with only the model id changed, Message Batches API.
- Actual spend: 9.01 USD (cap 30 USD).
- Before any number was computed, the code reproduced the published Claude and OpenAI arms exactly.
- Like every Upworthy number in the report, these are provisional, and F1 sits after the hierarchy. It is never gated and proves no endpoint.

## All frontier arms on the same tests

| Arm | Picked the best arm | Chance | L | Lens minus arm (95% CI) | Recognised in probe |
|---|---|---|---|---|---|
| Lens | 49.9% | 25.2% | | | |
| opus_5_5_zero_shot | 35.7% | 25.2% | 0.140 | +14.3 pts (+11.8 pts to +16.6 pts) | 1 of 300 |
| sonnet_5_5_zero_shot | 34.5% | 25.2% | 0.124 | +15.4 pts (+13.1 pts to +17.8 pts) | 2 of 300 |
| gpt_6_1_sol_zero_shot | 37.3% | 25.2% | 0.162 | +12.6 pts (+10.4 pts to +14.8 pts) | 1 of 300 |
| gpt_6_1_terra_zero_shot | 36.8% | 25.2% | 0.154 | +13.2 pts (+10.9 pts to +15.5 pts) | 2 of 300 |
| gpt_6_astra_zero_shot | 37.8% | 25.2% | 0.169 | +12.1 pts (+9.8 pts to +14.4 pts) | 0 of 300 |
| fable_5_1_zero_shot | 33.6% | 25.2% | 0.112 | +16.3 pts (+14.1 pts to +18.5 pts) | 2 of 300 |

Fable beats Lens (the 95% CI of Lens minus Fable lies wholly below 0): no.

---

## Frontier arms (F1, after the hierarchy, never gated)

Label: post-publication addendum (2026-11), provisional, after the hierarchy, never gated. Each arm ran zero-shot on the same holdout tests as Lens; "Lens beats" an arm only if the 95% CI lower bound of Lens minus the arm is above 0.

- **fable_5_1_zero_shot**: L = 0.112; it picked the best arm 33.6% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.7% of the 300 probe tests (2 of 300), and the arm it named won 50.0% of those (1 of 2). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +16.3 pts (95% CI +14.1 pts to +18.5 pts). Lens beats this arm: yes.

## Answer quality

- 4520 of 4520 requests returned, 3500 gave a valid answer, 0 hit the 512-token limit (0 of those still gave a valid answer), 2 were refused.
