"""Tests for quantum.alice – qubit preparation."""

from __future__ import annotations

from quantum.alice import Alice
from quantum.utils import SIX_STATE_BASES, BB84_BASES, Basis


class TestAlice:
    """Tests for the Alice class."""

    def test_prepare_returns_correct_count(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=42)
        state = alice.prepare_qubits(100)
        assert len(state.bits) == 100
        assert len(state.bases) == 100
        assert len(state.circuits) == 100

    def test_bits_are_binary(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=42)
        state = alice.prepare_qubits(200)
        assert all(b in (0, 1) for b in state.bits)

    def test_bases_from_correct_set(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=42)
        state = alice.prepare_qubits(200)
        assert all(b in SIX_STATE_BASES for b in state.bases)

    def test_bb84_only_two_bases(self) -> None:
        alice = Alice(basis_set=BB84_BASES, seed=42)
        state = alice.prepare_qubits(200)
        assert all(b in BB84_BASES for b in state.bases)

    def test_reproducibility(self) -> None:
        alice1 = Alice(basis_set=SIX_STATE_BASES, seed=99)
        alice2 = Alice(basis_set=SIX_STATE_BASES, seed=99)
        s1 = alice1.prepare_qubits(50)
        s2 = alice2.prepare_qubits(50)
        assert s1.bits == s2.bits
        assert s1.bases == s2.bases

    def test_circuits_are_separate(self) -> None:
        """Each qubit should be a separate circuit."""
        alice = Alice(basis_set=SIX_STATE_BASES, seed=42)
        state = alice.prepare_qubits(10)
        for qc in state.circuits:
            assert qc.num_qubits == 1
