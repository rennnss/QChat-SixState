"""Abstract base class for QKD protocols.

Defines the common interface and data structures shared by the
Six‑State and BB84 protocol implementations.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from quantum.utils import Basis


@dataclass
class ProtocolResult:
    """Container for the outcome of a single QKD protocol run.

    Attributes:
        protocol_name: Human‑readable protocol identifier.
        n_qubits: Total number of qubits transmitted.
        alice_sifted: Alice's sifted key bits.
        bob_sifted: Bob's sifted key bits.
        sifted_length: Length of the sifted key.
        qber: Quantum Bit Error Rate computed on a sample.
        raw_key_rate: Fraction of transmitted qubits retained after sifting.
        eve_detected: Whether QBER exceeds the detection threshold.
        eve_present: Whether Eve was actually active.
        noise_type: Description of the noise channel used.
        noise_prob: Noise probability.
        final_key: Remaining key bits after QBER sampling.
        sample_size: Number of bits sacrificed for QBER estimation.
    """

    protocol_name: str = ""
    n_qubits: int = 0
    alice_sifted: List[int] = field(default_factory=list)
    bob_sifted: List[int] = field(default_factory=list)
    sifted_length: int = 0
    qber: float = 0.0
    raw_key_rate: float = 0.0
    eve_detected: bool = False
    eve_present: bool = False
    noise_type: str = "none"
    noise_prob: float = 0.0
    final_key: List[int] = field(default_factory=list)
    sample_size: int = 0


def sift_keys(
    alice_bases: List[Basis],
    bob_bases: List[Basis],
    alice_bits: List[int],
    bob_results: List[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Basis reconciliation (sifting).

    Keep only the bits where Alice and Bob chose the same basis.

    Args:
        alice_bases: Alice's preparation bases.
        bob_bases: Bob's measurement bases.
        alice_bits: Alice's encoded bit values.
        bob_results: Bob's measurement results.

    Returns:
        Tuple of (alice_sifted, bob_sifted, matching_indices).
    """
    alice_sifted: List[int] = []
    bob_sifted: List[int] = []
    matching_indices: List[int] = []

    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            alice_sifted.append(alice_bits[i])
            bob_sifted.append(bob_results[i])
            matching_indices.append(i)

    return alice_sifted, bob_sifted, matching_indices


class QKDProtocol(abc.ABC):
    """Abstract base for QKD protocol implementations.

    Subclasses must implement :meth:`run` with the full protocol pipeline.
    """

    @abc.abstractmethod
    def run(
        self,
        n_qubits: int,
        eve_present: bool = False,
        noise_type: str = "none",
        noise_prob: float = 0.0,
        sample_fraction: float = 0.5,
    ) -> ProtocolResult:
        """Execute one round of the protocol.

        Args:
            n_qubits: Number of qubits to transmit.
            eve_present: Whether Eve performs interception.
            noise_type: Noise model identifier (``"none"``, ``"bit_flip"``,
                        ``"depolarizing"``).
            noise_prob: Noise probability in [0, 1].
            sample_fraction: Fraction of sifted bits used for QBER estimation.

        Returns:
            A ``ProtocolResult`` with all computed metrics.
        """
        ...
