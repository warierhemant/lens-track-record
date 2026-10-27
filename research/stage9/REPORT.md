# Stage 9 accuracy proof: stage9-holdout-v2

## What we tested

The frozen config was written and sealed (its hash is the first entry of a tamper-evident ledger, and is published) before any prediction. Every prediction was sealed before any outcome was joined. Nothing here was tuned on these results.

- Config SHA-256: `53933780bf8f695821c3fee2613f04299f2a2cf86550295c5d326e22e9e7a993`
- Ledger head after the join: `593b7996e52d4a3146e170948211cd70c258d2e84be74171bf23b7411702282f`
- Model: lens-ens10-STACK 94ed011ee886
- 6875 pairs and 9324 arms joined; 10887 sealed entries have no outcome (undecided pairs, tied tests and the manifest).
- Arm-set rule (upworthy_holdout): the text-only pre-collection held 9324 arms in 2110 tests; the outcome read kept 9324 arms in 2110 tests. 0 arms (0 inside kept tests) and 0 whole tests are excluded by the rule fixed before the read (an arm whose packages all had zero impressions; a test left with fewer than 2 arms); every n above counts the kept arms only.

## Null tests (spec 4.7)

These check the machinery, not Lens. All must pass before any accuracy number is shown.

- **A mock that knows nothing scores like chance**: PASS. Kappa's 95% CI covered 0 on 5 of 5 runs (needs 4).
- **Shuffled outcomes give no signal**: PASS. 1000 shuffles of 1664 outcomes; uniformity test p = 0.375 (needs above 0.01).
- **Two identical texts are never called**: PASS. Called 0 of 200 (0.0%, 95% CI 0.0% to 1.9%); the bar is 5% or fewer.
- **Trivial rewordings are almost never called**: PASS. Called 0 of 200 (0.0%, 95% CI 0.0% to 1.9%); the bar is 10% or fewer.
- **False-winner rate on tests with no real difference**: PASS. Called 210 of 5191 null pairs (4.0%, 95% CI 3.5% to 4.6%); reported, needs at least 600 pairs.
- **Harness check: the probe follows a plain instruction (which has more words?)**: PASS. Followed word count on 200 of 200 (100.0%); the bar is 80%. A harness check (probe word-count:str.split:v1): the Stage 9 probe counts words with str.split (spec 4.7), so the row tests that the sampled pairs reach it intact, not a model's instruction following.
- **The full system beats the position, length, newer-arm, familiarity and recognition guesses**: PASS. Gain over each: position +35.4 pts (95% CI +31.9 pts to +38.9 pts); length +38.7 pts (95% CI +35.5 pts to +41.9 pts); always_newer +35.4 pts (95% CI +31.9 pts to +38.9 pts); familiarity +37.5 pts (95% CI +34.0 pts to +40.7 pts); recognition +38.9 pts (95% CI +35.4 pts to +42.4 pts).
- **A re-run with new seeds makes the same pick**: PASS. Same pick on 300 of 300 (100.0%); the bar is 90%.
- **Every edited, deleted or back-dated ledger entry is caught**: PASS. 9 of 9 tampered copies caught.

## The answer, endpoint by endpoint

Endpoints are checked in a fixed order; once one fails, later ones are shown but not claimed.

**Not every endpoint passed.** The hierarchy stopped at S2.

- **P. Lens finds the best headline of a test more often than chance (best-of-k lift)**: PASS. Lift L = 0.330 (95% CI 0.302 to 0.359) on 2110 tests; picked the best arm 49.9% of the time where chance is 25.2%. The bar is L of at least 0.171 at the lower end of the 95% CI; parity with LOLA is claimed.
- **S1. The text learner beats the position, length, newer-arm, familiarity and recognition guesses**: PASS. Gain over each: position +35.3 pts (95% CI +31.9 pts to +38.8 pts); length +38.6 pts (95% CI +35.5 pts to +41.7 pts); always_newer +35.3 pts (95% CI +31.9 pts to +38.8 pts); familiarity +37.4 pts (95% CI +33.9 pts to +40.6 pts); recognition +38.8 pts (95% CI +35.4 pts to +42.3 pts).
- **S2. The panel describe call adds to the text learner (log-loss)**: FAIL. Gain 0.0011 nats per pair (95% CI -0.0024 to 0.0046): DROP. Provisional until 8.7 has 100+ post-cutoff decided pairs.
- **S3. Lens's probabilities mean what they say (calibration)**: FAIL (not gated (hierarchy stopped at S2); proves nothing). Slope 1.13 (95% CI 1.01 to 1.27), inside the bar: no; intercept -0.02 (95% CI -0.19 to 0.17), contains 0: yes; Spiegelhalter p = 0.036. Debiased calibration error 0.9% (95% CI 0.0% to 4.7%, n = 1664).
- **S4. The can't-tell rule stays quiet on tests with no real difference**: PASS (not gated (hierarchy stopped at S2); proves nothing). At threshold 0.49: called 495 of 1664 decided pairs (coverage 29.7%, 95% CI 26.8% to 32.8%), right on 99.8% (95% CI 99.4% to 100.0%); called 4.0% of 5191 null pairs (95% CI 3.5% to 4.6%) and 0.0% of 20 identical pairs; at the decided base rate 29.2% of calls would be on nulls.
- **C98. When Lens is confident, it is right at least 98% of the time**: FAIL (not gated (hierarchy stopped at S2); proves nothing). Full system at threshold 0.41: called 1200 of 1664 decided pairs (coverage 72.1%, 95% CI 69.4% to 74.6%), right on 98.7% (95% CI 97.9% to 99.3%); called 31.7% of 5191 null pairs (95% CI 30.4% to 33.0%) and 0.0% of 20 identical pairs; at the decided base rate 57.1% of calls would be on nulls. Text-only at 0.41: called 1211 of 1664 decided pairs (coverage 72.8%, 95% CI 70.1% to 75.3%), right on 98.6% (95% CI 97.8% to 99.3%); called 30.8% of 5191 null pairs (95% CI 29.5% to 32.1%) and 0.0% of 20 identical pairs; at the decided base rate 56.2% of calls would be on nulls. A pass needs the lower end of the 95% CI of the full system at 98% or more.
- **S5. Lens picks the winner of decided pairs often enough**: PASS (not gated (hierarchy stopped at S2); proves nothing). Right on 92.8% of decided pairs (95% CI 91.3% to 94.2%); always keeping the control (earlier arm of the test) gets 57.4%; kappa 0.86 (95% CI 0.83 to 0.88). Target 86.1%.
- **S6. Letter-style claim: Lens beats the strongest naive guess (customer-v1 looks)**: PASS (not gated (hierarchy stopped at S2); proves nothing). 495 calls; last look at 40 against always_control: one-sided p = 9.54e-07 (needs 0.01 or less); edge shown at 40.

## The confident-call claim

Accuracy when confident: right on 98.7% of its calls, CI lower bound 97.9%; it calls 72.1% of decided pairs (coverage) and 31.7% of null pairs, tests whose arms truly tie (null-pair call rate). (C98 did not pass, so no rounded claim is made.)

## Reported, never gated

- Familiarity: the hit rate changes by 0.009 per standard deviation of familiarity gap (n = 1664); accuracy on pairs below the median familiarity gap 92.2%.

## Extra metrics (fixed before sealing, never gated)

- Kappa on the 49% most confident decided pairs: 0.99 (95% CI 0.98 to 1.00). Above the external 0.31 by the pre-set rule (CI lower bound above it): yes. The external figure comes from another vendor's data set.
- Reliability: accuracy rises with confidence (Kendall tau 0.28, 95% CI 0.25 to 0.31): yes. Bins (confidence -> accuracy): 62.3% -> 63.5%; 79.3% -> 85.0%; 89.2% -> 88.6%; 94.0% -> 94.6%; 96.5% -> 99.4%; 97.9% -> 98.2%; 98.7% -> 99.4%; 99.3% -> 99.4%; 99.6% -> 100.0%; 99.9% -> 100.0%.
- Confidence AUROC for a correct call (descriptive): 0.88 (95% CI 0.85 to 0.91).
- Debiased ECE (descriptive): 0.009 (95% CI 0.0% to 4.7%, n = 1664).

**Label: provisional.** provisional while the post-Opus-cutoff (June 2026) set has fewer than 100 decided pairs.

## What this does not show

- It covers only the datasets in the frozen config. It says nothing about other channels, audiences or a customer's own tests.
- Every Upworthy result stays provisional until 100 or more decided pairs from tests that ended after the Opus 5.5 training cutoff (June 2026) exist (spec 3.3).
- It says nothing about B2B buyers: B2B evidence is a separately sealed set and stays pending until it reaches its pre-registered size.
- No web-presence baseline: it was dropped before sealing because no free, licensed, pre-cutoff exact-phrase web index was found.
- "Confident" means the frozen threshold; coverage is how often Lens is willing to call at all. Most pairs may be "can't tell".
- An interval that crosses the bar is not a pass, even when the point estimate is above it.
