"""Quantum utility functions for QKD protocol simulation.

Provides core circuit building blocks for qubit preparation and measurement
in the Z, X, and Y bases using Qiskit quantum circuits.
"""

from __future__ import annotations

import enum
from typing import List

import numpy as np
from qiskit import QuantumCircuit


class Basis(enum.Enum):
    """Measurement/preparation basis for QKD protocols."""

    Z = "Z"  # Computational basis: |0⟩, |1⟩
    X = "X"  # Hadamard basis:      |+⟩, |−⟩
    Y = "Y"  # Circular basis:      |+i⟩, |−i⟩


# ── Basis sets for each protocol ──────────────────────────────────────────────

SIX_STATE_BASES: List[Basis] = [Basis.Z, Basis.X, Basis.Y]
BB84_BASES: List[Basis] = [Basis.Z, Basis.X]


def random_bits(n: int, rng: np.random.Generator | None = None) -> List[int]:
    """Generate *n* uniformly random classical bits (0 or 1).

    Args:
        n: Number of bits to generate.
        rng: Optional NumPy random generator for reproducibility.

    Returns:
        List of integers, each 0 or 1.
    """
    if rng is None:
        rng = np.random.default_rng()
    return rng.integers(0, 2, size=n).tolist()


def random_bases(
    n: int,
    basis_set: List[Basis],
    rng: np.random.Generator | None = None,
) -> List[Basis]:
    """Choose *n* random bases from the given *basis_set*.

    Args:
        n: Number of bases to choose.
        basis_set: Available bases (e.g. ``SIX_STATE_BASES`` or ``BB84_BASES``).
        rng: Optional NumPy random generator for reproducibility.

    Returns:
        List of ``Basis`` enum members.
    """
    if rng is None:
        rng = np.random.default_rng()
    indices = rng.integers(0, len(basis_set), size=n)
    return [basis_set[i] for i in indices]


def prepare_qubit(circuit: QuantumCircuit, bit: int, basis: Basis) -> None:
    """Encode a classical *bit* into the given *basis* on qubit 0 of *circuit*.

    Gate sequences:
        - **Z basis**: ``|0⟩`` or ``X|0⟩ = |1⟩``
        - **X basis**: ``H|0⟩ = |+⟩`` or ``XH|0⟩ = |−⟩``  (bit‑flip then Hadamard order: X then H)
        - **Y basis**: ``SH|0⟩ = |+i⟩`` or ``XSH|0⟩ = |−i⟩``

    Args:
        circuit: A ``QuantumCircuit(1, 1)`` in the ``|0⟩`` state.
        bit: Classical bit value (0 or 1).
        basis: Preparation basis.
    """
    if bit == 1:
        circuit.x(0)

    if basis == Basis.X:
        circuit.h(0)
    elif basis == Basis.Y:
        circuit.h(0)
        circuit.s(0)


def measure_qubit(circuit: QuantumCircuit, basis: Basis) -> None:
    """Append measurement gates for the given *basis* to *circuit*.

    The inverse of the preparation rotation is applied before a Z‑basis
    measurement so that the result reflects the logical bit.

    Args:
        circuit: Quantum circuit to append measurement to.
        basis: Measurement basis.
    """
    if basis == Basis.X:
        circuit.h(0)
    elif basis == Basis.Y:
        circuit.sdg(0)
        circuit.h(0)

    circuit.measure(0, 0)


def create_single_qubit_circuit() -> QuantumCircuit:
    """Return a fresh ``QuantumCircuit(1, 1)`` ready for qubit preparation.

    Returns:
        A single‑qubit, single‑classical‑bit quantum circuit.
    """
    return QuantumCircuit(1, 1)
