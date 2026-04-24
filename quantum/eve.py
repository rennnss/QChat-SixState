"""Eve – the eavesdropper in a QKD protocol.

Implements the intercept‑resend attack: Eve measures each qubit in a
randomly chosen basis, learns a (possibly incorrect) bit value, and
re‑prepares the qubit in the same basis before forwarding it to Bob.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
from qiskit import QuantumCircuit

from quantum.utils import (
    Basis,
    create_single_qubit_circuit,
    measure_qubit,
    prepare_qubit,
    random_bases,
)

try:
    from qiskit_aer import AerSimulator
except ImportError:
    from qiskit.providers.aer import AerSimulator  # type: ignore[import-untyped]


@dataclass
class EveState:
    """Record of Eve's interception round."""

    bases: List[Basis] = field(default_factory=list)
    intercepted_bits: List[int] = field(default_factory=list)
    forwarded_circuits: List[QuantumCircuit] = field(default_factory=list)


class Eve:
    """Eavesdropper performing an intercept‑resend attack.

    Eve intercepts every qubit, measures it in a uniformly random basis
    from her ``basis_set``, and re‑prepares a fresh qubit encoding the
    measured bit in the same basis she used.  This inevitably disturbs
    qubits whose preparation basis differs from Eve's measurement basis.

    Args:
        basis_set: Bases available to Eve (should match the protocol).
        seed: Optional RNG seed for reproducibility.
    """

    def __init__(
        self,
        basis_set: List[Basis],
        seed: int | None = None,
    ) -> None:
        self.basis_set = basis_set
        self._rng = np.random.default_rng(seed)

    def intercept(self, circuits: List[QuantumCircuit]) -> EveState:
        """Perform intercept‑resend on every circuit.

        For each incoming qubit:
        1. Choose a random measurement basis.
        2. Measure the qubit (collapses the state).
        3. Create a new circuit encoding the measured bit in Eve's basis.

        Args:
            circuits: Qubit circuits sent from Alice.

        Returns:
            An ``EveState`` with Eve's bases, intercepted bits, and the
            replacement circuits forwarded to Bob.
        """
        n_qubits = len(circuits)
        eve_bases = random_bases(n_qubits, self.basis_set, rng=self._rng)
        intercepted_bits: List[int] = []
        forwarded: List[QuantumCircuit] = []

        simulator = AerSimulator()

        for i in range(n_qubits):
            # ── Step 1: Measure in Eve's basis ────────────────────────────
            qc = circuits[i].copy()
            measure_qubit(qc, eve_bases[i])

            job = simulator.run(qc, shots=1)
            counts: Dict[str, int] = job.result().get_counts()
            bit = int(list(counts.keys())[0])
            intercepted_bits.append(bit)

            # ── Step 2: Re‑prepare in the same basis ─────────────────────
            new_qc = create_single_qubit_circuit()
            prepare_qubit(new_qc, bit, eve_bases[i])
            forwarded.append(new_qc)

        return EveState(
            bases=eve_bases,
            intercepted_bits=intercepted_bits,
            forwarded_circuits=forwarded,
        )
