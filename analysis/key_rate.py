"""Key rate estimation for QKD protocols.

Computes raw key rate, secure key rate (based on Shannon entropy bounds),
and provides comparison utilities between Six‑State and BB84.
"""

from __future__ import annotations

import math
from typing import Dict


def _binary_entropy(p: float) -> float:
    """Compute the binary Shannon entropy H(p).

    Args:
        p: Error probability in [0, 1].

    Returns:
        H(p) in bits.  Returns 0.0 for p ∈ {0, 1}.
    """
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def compute_raw_key_rate(n_qubits: int, sifted_length: int) -> float:
    """Compute the raw key rate (sifted bits / total qubits).

    Args:
        n_qubits: Total number of qubits transmitted.
        sifted_length: Number of bits remaining after sifting.

    Returns:
        Raw key rate as a fraction in [0, 1].
    """
    if n_qubits == 0:
        return 0.0
    return sifted_length / n_qubits


def compute_secure_key_rate(qber: float, protocol: str = "six_state") -> float:
    """Estimate the asymptotic secure key rate per sifted bit.

    For the Six‑State protocol::

        r = 1 − H(QBER) − H(QBER)  (symmetric channel, one‑way post‑processing)

    A simplified Devetak–Winter bound is used:

    - **Six‑State**: ``r = 1 − (5/3) · H(QBER)`` (tighter than BB84)
    - **BB84**: ``r = 1 − 2 · H(QBER)``

    The key rate is clamped to [0, 1].

    Args:
        qber: Quantum Bit Error Rate in [0, 1].
        protocol: ``"six_state"`` or ``"bb84"``.

    Returns:
        Estimated secure key rate per sifted bit.
    """
    h = _binary_entropy(qber)

    if protocol == "six_state":
        rate = 1.0 - (5.0 / 3.0) * h
    else:  # BB84
        rate = 1.0 - 2.0 * h

    return max(0.0, rate)


def compute_effective_key_rate(
    n_qubits: int,
    sifted_length: int,
    qber: float,
    protocol: str = "six_state",
    sample_fraction: float = 0.5,
) -> float:
    """Compute the effective final key rate per transmitted qubit.

    Accounts for sifting loss, QBER sample sacrifice, and information‑theoretic
    bounds.

    Args:
        n_qubits: Total qubits transmitted.
        sifted_length: Number of sifted bits.
        qber: Measured QBER.
        protocol: Protocol name for secure rate calculation.
        sample_fraction: Fraction used for QBER estimation.

    Returns:
        Effective key rate per qubit.
    """
    if n_qubits == 0 or sifted_length == 0:
        return 0.0

    raw_rate = sifted_length / n_qubits
    remaining_fraction = 1.0 - sample_fraction
    secure_rate = compute_secure_key_rate(qber, protocol)

    return raw_rate * remaining_fraction * secure_rate


def compare_protocols(
    six_state_qber: float,
    bb84_qber: float,
) -> Dict[str, Dict[str, float]]:
    """Compare Six‑State and BB84 key rates at given QBERs.

    Args:
        six_state_qber: QBER observed in Six‑State run.
        bb84_qber: QBER observed in BB84 run.

    Returns:
        Dictionary mapping protocol name → metrics dict.
    """
    return {
        "Six-State": {
            "qber": six_state_qber,
            "secure_key_rate": compute_secure_key_rate(six_state_qber, "six_state"),
            "max_tolerable_qber": 1.0 / 3.0,
        },
        "BB84": {
            "qber": bb84_qber,
            "secure_key_rate": compute_secure_key_rate(bb84_qber, "bb84"),
            "max_tolerable_qber": 0.25,
        },
    }
