"""What Stage 9 predicts with: the frozen stack, the familiarity scorer, the instruction probe.

Every predictor sees blind items only (sources.BLIND_KEYS / ARM_KEYS) and never an outcome.

StackedModel  the frozen Lens stack: predict_pairs(items) -> [{"p": full stack (text +
              describe), "p_text": text-only stack}]. Optional score_arms(arms) -> [float],
              the learner's per-arm score for best-of-k; without it the runner scores each arm
              by its mean pair logit within the test. Optional reseed(seed), used by the
              stability null test. `ServiceStack` adapts lens_engine.serving.ForecastService.
Familiarity   score_texts(texts) -> [mean token log-probability] under the open base model
              (spec 3.1a); it feeds the S1 familiarity baseline and the report-only
              familiarity regression.
Recognition   score_texts(texts) -> [recognition score]: how strongly the frozen model
              recognises the exact text as seen before (e.g. a membership score such as Min-K%
              token log-probability, or the model's own "have you seen this?" probability).
              Feeds the S1 recognition baseline: if the arm the model recognises more is the one
              that won, accuracy could come from memory, not from reading the text.
WebPresence   score_texts(texts) -> [log(1 + exact-phrase hits)] in a web index frozen before the
              model cutoff. Feeds the S1 web_presence baseline: a winning arm is republished and
              quoted more, so "pick the arm more present on the web" leaks the outcome.
Probe         more_words(items) -> [P(text_b has more words) or None]: the scrambled-
              instruction null test (spec 4.7) asks the model "which has more words?".

Familiarity, Recognition and WebPresence share one interface (TextScorer.score_texts). The real
recognition and web-presence scorers live outside this repo (the web index needs a licence or a
key); mocks.MockRecognition and mocks.MockWebPresence carry no signal.
"""
from __future__ import annotations

import importlib
from typing import Protocol

from lens_engine.stage9.sources import ARM_KEYS, BLIND_KEYS


class StackedModel(Protocol):
    name: str
    version: str

    def predict_pairs(self, items: list[dict]) -> list[dict]: ...


class TextScorer(Protocol):
    name: str

    def score_texts(self, texts: list[str]) -> list[float]: ...


Familiarity = Recognition = WebPresence = TextScorer  # WebPresence: unused since 2026-10-20 (dropped)


class Probe(Protocol):
    name: str

    def more_words(self, items: list[dict]) -> list[float | None]: ...


def blind(items: list[dict]) -> list[dict]:
    return [{k: it[k] for k in BLIND_KEYS} for it in items]


def blind_arms(arms: list[dict]) -> list[dict]:
    return [{k: a[k] for k in ARM_KEYS} for a in arms]


CHANNEL = {"headline": "headline", "email_subject_line": "email_subject_line",
           "ad_creative": "ad_creative", "web_page": "web_page"}


class ServiceStack:
    """Adapter from the forecast service to StackedModel. control = slot A, challenger = slot B,
    so p_challenger_beats_control is P(B wins). The workspace ledger of the service is not the
    Stage 9 ledger; the runner seals the returned p itself."""

    def __init__(self, full, text_only, name: str, version: str, workspace_id: str = "stage9"):
        self.full, self.text_only = full, text_only
        self.name, self.version, self.workspace_id = name, version, workspace_id

    def _requests(self, items):
        return [{"workspace_id": self.workspace_id,
                 "control": {"id": it["arm_a"], "text": it["text_a"]},
                 "challenger": {"id": it["arm_b"], "text": it["text_b"]},
                 "channel": CHANNEL.get(it["use_case"], "headline"), "metric": "click_rate",
                 "data_class": "public", "llm_policy": {"allow_describe": True}} for it in items]

    @staticmethod
    def _p(res: dict) -> float:
        if "p_challenger_beats_control" not in res:
            raise RuntimeError(f"stack returned no probability: {res.get('error', res)}")
        return float(res["p_challenger_beats_control"])

    def predict_pairs(self, items: list[dict]) -> list[dict]:
        reqs = self._requests(items)
        full = self.full.forecast_many(reqs)
        text = self.text_only.forecast_many(reqs)
        return [{"p": self._p(f), "p_text": self._p(t)} for f, t in zip(full, text)]


def load_object(spec: str):
    """'package.module:factory' -> factory(). Used by the CLI to plug in the real stack,
    familiarity, recognition and web-presence scorers and probe at Stage 9 (they live outside this repo or need keys)."""
    mod, _, attr = spec.partition(":")
    if not mod or not attr:
        raise ValueError(f"expected 'module:factory', got {spec!r}")
    return getattr(importlib.import_module(mod), attr)()
