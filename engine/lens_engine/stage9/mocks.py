"""Mock predictors for tests and the synthetic dry run. No network, no keys, no model.

They read the noisy "strength" that SyntheticSource writes into each text, never an outcome.
"""
from __future__ import annotations

import math
import re
import zlib

import numpy as np

_S = re.compile(r"strength\s+(-?\d+\.\d+)")


def _strength(text: str) -> float:
    m = _S.search(text)
    return float(m.group(1)) if m else 0.0


def _sig(x: float) -> float:
    return 1 / (1 + math.exp(-x))


class MockStack:
    """Full stack = sharper read of the strength gap; text-only = a weaker one."""
    name, version = "mock-stack", "mock-1"

    def __init__(self, k_full: float = 2.2, k_text: float = 1.5, arm_scores: bool = True):
        self.k_full, self.k_text = k_full, k_text
        self.seen: list[dict] = []
        if not arm_scores:
            self.score_arms = None

    def predict_pairs(self, items):
        self.seen += items
        out = []
        for it in items:
            g = _strength(it["text_b"]) - _strength(it["text_a"])
            # text-only reads the gap with extra, text-fixed noise: the "describe" call helps
            e = (zlib.crc32((it["text_a"] + it["text_b"]).encode()) % 1000) / 1000 - 0.5
            out.append({"p": _sig(self.k_full * g), "p_text": _sig(self.k_text * (g + 1.2 * e))})
        return out

    def score_arms(self, arms):
        self.seen += arms
        return [_strength(a["text"]) for a in arms]


class RandomStack:
    """The spec 4.7 mock provider: p independent of the text and of every outcome."""
    name, version = "mock-random", "mock-1"

    def __init__(self, seed: int = 0):
        self.rng = np.random.default_rng(seed)

    def predict_pairs(self, items):
        p = self.rng.uniform(0.02, 0.98, len(items))
        return [{"p": float(x), "p_text": float(x)} for x in p]


class MockFamiliarity:
    """A stand-in for mean token log-probability: a stable hash of the text, no signal."""
    name = "mock-familiarity"

    def score_texts(self, texts):
        return [-3 + (zlib.crc32(t.encode()) % 1000) / 1000 for t in texts]


class MockRecognition:
    """A stand-in for a membership / recognition score: a stable hash, no signal."""
    name = "mock-recognition"

    def score_texts(self, texts):
        return [(zlib.crc32(b"rec:" + t.encode()) % 1000) / 1000 for t in texts]


class MockWebPresence:
    """A stand-in for log(1 + exact-phrase web hits): a stable hash, no signal."""
    name = "mock-web-presence"

    def score_texts(self, texts):
        return [(zlib.crc32(b"web:" + t.encode()) % 700) / 100 for t in texts]


class MockProbe:
    """Answers "which has more words?" by counting, wrong on every `wrong_every`th item."""
    name = "mock-probe"

    def __init__(self, wrong_every: int = 0):
        self.wrong_every, self.n = wrong_every, 0

    def more_words(self, items):
        out = []
        for it in items:
            self.n += 1
            right = len(it["text_b"].split()) > len(it["text_a"].split())
            if self.wrong_every and self.n % self.wrong_every == 0:
                right = not right
            out.append(0.9 if right else 0.1)
        return out


def stack():
    return MockStack()


def familiarity():
    return MockFamiliarity()


def probe():
    return MockProbe()


def recognition():
    return MockRecognition()


def web_presence():
    return MockWebPresence()
