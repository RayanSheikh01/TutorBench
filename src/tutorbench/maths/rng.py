"""Seeded RNG helper — reproducible question generation."""
import random


def make_rng(seed: int) -> random.Random:
    """Return a fresh RNG seeded for reproducibility (same seed -> same question)."""
    return random.Random(seed)
