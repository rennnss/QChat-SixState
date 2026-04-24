"""Alice – the sender in a QKD protocol.

Alice prepares qubits by encoding random classical bits into randomly
chosen bases and sends them through the quantum channel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from quantum.utils import (
    Basis,
    create_single_qubit_circuit,
    prepare_qubit,
    random_bases,
    random_bits,
)

from qiskit import QuantumCircuit


@dataclass
class AliceState:
    """Immutable record of Alice's preparation round."""

    bits: List[int] = field(default_factory=list)
    bases: List[Basis] = field(default_factory=list)
    circuits: List[QuantumCircuit] = field(default_factory=list)


class Alice:
    """QKD sender that prepares qubits in random bases.

    Args:
        basis_set: List of bases to choose from (e.g. Z, X, Y for Six‑State).
        seed: Optional RNG seed for reproducibility.
    """

    def __init__(
        self,
        basis_set: List[Basis],
        seed: int | None = None,
    ) -> None:
        self.basis_set = basis_set
        self._rng = np.random.default_rng(seed)

    def prepare_qubits(self, n_qubits: int) -> AliceState:
        """Prepare *n_qubits* encoded qubits.

        Each qubit is created as a separate ``QuantumCircuit(1, 1)`` so that
        Eve can intercept individual qubits independently.

        Args:
            n_qubits: Number of qubits to prepare.

        Returns:
            An ``AliceState`` containing bits, bases, and circuits.
        """
        bits = random_bits(n_qubits, rng=self._rng)
        bases = random_bases(n_qubits, self.basis_set, rng=self._rng)

        circuits: List[QuantumCircuit] = []
        for i in range(n_qubits):
            qc = create_single_qubit_circuit()
            prepare_qubit(qc, bits[i], bases[i])
            circuits.append(qc)

        return AliceState(bits=bits, bases=bases, circuits=circuits)
