"""BB84 QKD Protocol implementation.

Uses two bases (Z, X) for qubit preparation and measurement.
The expected sifting rate is ≈ 1/2 and an intercept‑resend attack
introduces a QBER of ≈ 25%.

Provided for comparison against the Six‑State protocol.
"""

from __future__ import annotations

from typing import List

from analysis.qber import compute_qber, split_sample
from protocols.base import ProtocolResult, QKDProtocol, sift_keys
from quantum.alice import Alice
from quantum.bob import Bob
from quantum.channel import NoiseType, create_noise_model
from quantum.eve import Eve
from quantum.utils import BB84_BASES


class BB84Protocol(QKDProtocol):
    """BB84 QKD protocol.

    Args:
        alice_seed: RNG seed for Alice.
        bob_seed: RNG seed for Bob.
        eve_seed: RNG seed for Eve.
    """

    PROTOCOL_NAME = "BB84"
    QBER_THRESHOLD = 0.25  # Theoretical max QBER from Eve

    def __init__(
        self,
        alice_seed: int | None = None,
        bob_seed: int | None = None,
        eve_seed: int | None = None,
    ) -> None:
        self._alice_seed = alice_seed
        self._bob_seed = bob_seed
        self._eve_seed = eve_seed

    def run(
        self,
        n_qubits: int,
        eve_present: bool = False,
        noise_type: str = "none",
        noise_prob: float = 0.0,
        sample_fraction: float = 0.5,
    ) -> ProtocolResult:
        """Execute one round of the BB84 protocol.

        Pipeline:
        1. Alice prepares qubits in random bases (Z, X).
        2. (Optional) Eve intercepts and re‑sends.
        3. Bob measures qubits in random bases (Z, X).
        4. Basis reconciliation – keep matching bases (≈ 1/2).
        5. Sample a fraction for QBER estimation.
        6. Decide if Eve is detected based on QBER threshold.

        Args:
            n_qubits: Number of qubits to transmit.
            eve_present: Whether Eve is active.
            noise_type: Noise channel type.
            noise_prob: Noise probability.
            sample_fraction: Fraction of sifted key for QBER sampling.

        Returns:
            Protocol result with all metrics.
        """
        # ── 1. Alice prepares ─────────────────────────────────────────────
        alice = Alice(basis_set=BB84_BASES, seed=self._alice_seed)
        alice_state = alice.prepare_qubits(n_qubits)

        # ── 2. Eve intercepts (optional) ──────────────────────────────────
        circuits = alice_state.circuits
        if eve_present:
            eve = Eve(basis_set=BB84_BASES, seed=self._eve_seed)
            eve_state = eve.intercept(circuits)
            circuits = eve_state.forwarded_circuits

        # ── 3. Bob measures ───────────────────────────────────────────────
        noise_model = create_noise_model(
            NoiseType(noise_type), noise_prob
        )
        bob = Bob(basis_set=BB84_BASES, seed=self._bob_seed)
        bob_state = bob.measure_qubits(circuits, noise_model=noise_model)

        # ── 4. Basis reconciliation ───────────────────────────────────────
        alice_sifted, bob_sifted, _ = sift_keys(
            alice_state.bases,
            bob_state.bases,
            alice_state.bits,
            bob_state.results,
        )

        sifted_length = len(alice_sifted)

        # ── 5. QBER estimation ────────────────────────────────────────────
        if sifted_length == 0:
            qber = 0.0
            final_key: List[int] = []
            sample_size = 0
        else:
            sample_alice, sample_bob, key_alice, _ = split_sample(
                alice_sifted, bob_sifted, sample_fraction
            )
            qber = compute_qber(sample_alice, sample_bob)
            final_key = key_alice
            sample_size = len(sample_alice)

        # ── 6. Detection ─────────────────────────────────────────────────
        eve_detected = qber > (self.QBER_THRESHOLD * 0.5)

        raw_key_rate = sifted_length / n_qubits if n_qubits > 0 else 0.0

        return ProtocolResult(
            protocol_name=self.PROTOCOL_NAME,
            n_qubits=n_qubits,
            alice_sifted=alice_sifted,
            bob_sifted=bob_sifted,
            sifted_length=sifted_length,
            qber=qber,
            raw_key_rate=raw_key_rate,
            eve_detected=eve_detected,
            eve_present=eve_present,
            noise_type=noise_type,
            noise_prob=noise_prob,
            final_key=final_key,
            sample_size=sample_size,
        )
