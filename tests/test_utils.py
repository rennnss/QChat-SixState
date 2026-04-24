"""Tests for quantum.utils – basis encoding, preparation, measurement."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from quantum.utils import (
    Basis,
    BB84_BASES,
    SIX_STATE_BASES,
    create_single_qubit_circuit,
    measure_qubit,
    prepare_qubit,
    random_bases,
    random_bits,
)

try:
    from qiskit_aer import AerSimulator
except ImportError:
    from qiskit.providers.aer import AerSimulator


class TestRandomBits:
    """Tests for random_bits()."""

    def test_length(self) -> None:
        bits = random_bits(100)
        assert len(bits) == 100

    def test_values_are_binary(self) -> None:
        bits = random_bits(500)
        assert all(b in (0, 1) for b in bits)

    def test_reproducibility(self) -> None:
        import numpy as np
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        assert random_bits(50, rng1) == random_bits(50, rng2)


class TestRandomBases:
    """Tests for random_bases()."""

    def test_length(self) -> None:
        bases = random_bases(100, SIX_STATE_BASES)
        assert len(bases) == 100

    def test_values_in_set(self) -> None:
        bases = random_bases(200, SIX_STATE_BASES)
        assert all(b in SIX_STATE_BASES for b in bases)

    def test_bb84_only_two_bases(self) -> None:
        bases = random_bases(200, BB84_BASES)
        assert all(b in BB84_BASES for b in bases)

    def test_all_bases_appear(self) -> None:
        """With enough samples, all bases should appear."""
        bases = random_bases(500, SIX_STATE_BASES)
        assert set(bases) == set(SIX_STATE_BASES)


class TestPrepareAndMeasure:
    """Test that prepare → measure in the same basis returns the original bit."""

    @pytest.mark.parametrize("basis", [Basis.Z, Basis.X, Basis.Y])
    @pytest.mark.parametrize("bit", [0, 1])
    def test_matching_basis_returns_correct_bit(self, basis: Basis, bit: int) -> None:
        """Measurement in the preparation basis must always return the same bit."""
        simulator = AerSimulator()
        # Run multiple times to be statistically confident
        correct = 0
        trials = 20
        for _ in range(trials):
            qc = create_single_qubit_circuit()
            prepare_qubit(qc, bit, basis)
            measure_qubit(qc, basis)
            job = simulator.run(qc, shots=1)
            result_bit = int(list(job.result().get_counts().keys())[0])
            if result_bit == bit:
                correct += 1
        # Should be 100% correct with matching basis
        assert correct == trials, (
            f"Basis {basis}, bit {bit}: {correct}/{trials} correct"
        )


class TestCreateCircuit:
    """Tests for create_single_qubit_circuit()."""

    def test_circuit_has_one_qubit(self) -> None:
        qc = create_single_qubit_circuit()
        assert qc.num_qubits == 1
        assert qc.num_clbits == 1
