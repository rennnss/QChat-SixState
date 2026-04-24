"""QBER (Quantum Bit Error Rate) computation utilities.

Provides functions for computing QBER from sifted key bits and
splitting keys into sample / final portions for error estimation.
"""

from __future__ import annotations

import math
from typing import List, Tuple


def compute_qber(alice_bits: List[int], bob_bits: List[int]) -> float:
    """Compute the Quantum Bit Error Rate between two bit strings.

    QBER = (number of mismatched bits) / (total compared bits)

    Args:
        alice_bits: Alice's sifted key bits.
        bob_bits: Bob's sifted key bits.

    Returns:
        QBER as a float in [0, 1].  Returns 0.0 if either list is empty.

    Raises:
        ValueError: If the lists have different lengths.
    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError(
            f"Bit‑string lengths differ: {len(alice_bits)} vs {len(bob_bits)}"
        )

    n = len(alice_bits)
    if n == 0:
        return 0.0

    errors = sum(a != b for a, b in zip(alice_bits, bob_bits))
    return errors / n


def split_sample(
    alice_bits: List[int],
    bob_bits: List[int],
    sample_fraction: float = 0.5,
) -> Tuple[List[int], List[int], List[int], List[int]]:
    """Split sifted key into a QBER‑estimation sample and the remaining key.

    The first ``ceil(n * sample_fraction)`` bits form the sample;
    the rest become the final key.

    Args:
        alice_bits: Alice's sifted key bits.
        bob_bits: Bob's sifted key bits.
        sample_fraction: Fraction of bits to use for QBER estimation.

    Returns:
        Tuple of (sample_alice, sample_bob, key_alice, key_bob).
    """
    n = len(alice_bits)
    sample_size = max(1, math.ceil(n * sample_fraction))
    sample_size = min(sample_size, n)  # clamp

    sample_alice = alice_bits[:sample_size]
    sample_bob = bob_bits[:sample_size]
    key_alice = alice_bits[sample_size:]
    key_bob = bob_bits[sample_size:]

    return sample_alice, sample_bob, key_alice, key_bob
