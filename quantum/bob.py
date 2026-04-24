"""Bob – the receiver in a QKD protocol.

Bob measures the incoming qubits in randomly chosen bases and records
the measurement outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from qiskit import QuantumCircuit

from quantum.utils import (
    Basis,
    measure_qubit,
    random_bases,
)

# Qiskit Aer imports – handle both old and new package layouts
try:
    from qiskit_aer import AerSimulator
except ImportError:
    from qiskit.providers.aer import AerSimulator  # type: ignore[import-untyped]

from qiskit_aer.noise import NoiseModel


@dataclass
class BobState:
    """Immutable record of Bob's measurement round."""

    bases: List[Basis] = field(default_factory=list)
    results: List[int] = field(default_factory=list)


class Bob:
    """QKD receiver that measures qubits in random bases.

    Args:
        basis_set: List of bases to choose from.
        seed: Optional RNG seed for reproducibility.
    """

    def __init__(
        self,
        basis_set: List[Basis],
        seed: int | None = None,
    ) -> None:
        self.basis_set = basis_set
        self._rng = np.random.default_rng(seed)

    def measure_qubits(
        self,
        circuits: List[QuantumCircuit],
        noise_model: Optional[NoiseModel] = None,
    ) -> BobState:
        """Measure each circuit in a randomly chosen basis.

        Each circuit is executed independently on the Aer simulator with a
        single shot to preserve quantum randomness.

        Args:
            circuits: List of single‑qubit circuits (already prepared by Alice
                      and optionally intercepted by Eve).
            noise_model: Optional Qiskit ``NoiseModel`` to apply during
                         simulation.

        Returns:
            A ``BobState`` containing the chosen bases and measurement results.
        """
        n_qubits = len(circuits)
        bases = random_bases(n_qubits, self.basis_set, rng=self._rng)
        results: List[int] = []

        simulator = AerSimulator()

        for i in range(n_qubits):
            # Copy the circuit so we don't mutate Alice's original
            qc = circuits[i].copy()
            measure_qubit(qc, bases[i])

            # Execute with 1 shot – true quantum measurement
            if noise_model is not None:
                job = simulator.run(qc, shots=1, noise_model=noise_model)
            else:
                job = simulator.run(qc, shots=1)

            counts: Dict[str, int] = job.result().get_counts()
            measured_bit = int(list(counts.keys())[0])
            results.append(measured_bit)

        return BobState(bases=bases, results=results)
