# Stage 9 v2 report: F1 addendum (frontier arms)

**This is an addendum, generated on 2026-10-24, after publication.** The published Stage 9 v2 report (`research/stage9/REPORT.md`, ledger head after the join `593b7996`) did not print the F1 block, although runbook step K required each frontier arm's L, chance line and recognition-probe hit rate beside it. The numbers were in `results.json` all along (`analysis.F1`); only the renderer left them out.

Nothing below was recomputed or re-run. The section was rendered from the unchanged, published `research/stage9/results.json` by the fixed renderer function `lens_engine.stage9.report.frontier_lines` (branch `cloud/s9-followups`). `REPORT.md` and `results.json` stay exactly as published; the fix changes the Stage 9 code hash for future runs only.

- `research/stage9/results.json` sha256: `d6c863ba520661b29e95804b696f29037b61702b2440d033267697b6ee6b9d6e`
- Config SHA-256 (from that file): `53933780bf8f695821c3fee2613f04299f2a2cf86550295c5d326e22e9e7a993`
- Ledger head after the join (from that file): `593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f`
- Like every Upworthy number in the report, these are provisional (fewer than 100 decided post-cutoff pairs), and F1 sits after the hierarchy: it is never gated and proves no endpoint.
- Reading the recognition probe: each arm was shown the headlines of 300 probe tests and asked whether it recognised the test and, if so, which headline won. Opus named a winner once and Sonnet twice, so the share where the named arm won rests on 1 and 2 tests and says nothing on its own.

To reproduce:

```
cd engine && python -c "import json; from lens_engine.stage9 import report; print('\n'.join(report.frontier_lines(json.load(open('../research/stage9/results.json'))['analysis']['F1'])))"
```

---

## Frontier arms (F1, after the hierarchy, never gated)

Label: provisional; after the hierarchy, never gated. Each arm ran zero-shot on the same holdout tests as Lens; "Lens beats" an arm only if the 95% CI lower bound of Lens minus the arm is above 0.

- **opus_5_5_zero_shot**: L = 0.140; it picked the best arm 35.7% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.3% of the 300 probe tests (1 of 300), and the arm it named won 100.0% of those (1 of 1). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +14.3 pts (95% CI +11.8 pts to +16.6 pts). Lens beats this arm: yes.
- **sonnet_5_5_zero_shot**: L = 0.124; it picked the best arm 34.5% of the time where chance is 25.2%; recognition probe: it claimed to recognise 0.7% of the 300 probe tests (2 of 300), and the arm it named won 50.0% of those (1 of 2). On 2110 tests Lens picked the best arm 49.9% of the time: Lens minus the arm +15.4 pts (95% CI +13.1 pts to +17.8 pts). Lens beats this arm: yes.
