"""Tests for quantum.bob – qubit measurement."""

from __future__ import annotations

from quantum.alice import Alice
from quantum.bob import Bob
from quantum.utils import SIX_STATE_BASES, Basis


class TestBob:
    """Tests for the Bob class."""

    def test_measure_returns_correct_count(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=10)
        state = alice.prepare_qubits(50)
        bob = Bob(basis_set=SIX_STATE_BASES, seed=20)
        bob_state = bob.measure_qubits(state.circuits)
        assert len(bob_state.bases) == 50
        assert len(bob_state.results) == 50

    def test_results_are_binary(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=10)
        state = alice.prepare_qubits(100)
        bob = Bob(basis_set=SIX_STATE_BASES, seed=20)
        bob_state = bob.measure_qubits(state.circuits)
        assert all(r in (0, 1) for r in bob_state.results)

    def test_matching_bases_give_correct_bits(self) -> None:
        """When Alice and Bob use the same basis, Bob must get Alice's bit."""
        alice = Alice(basis_set=SIX_STATE_BASES, seed=42)
        state = alice.prepare_qubits(200)

        bob = Bob(basis_set=SIX_STATE_BASES, seed=43)
        bob_state = bob.measure_qubits(state.circuits)

        # Check only the matching-basis positions
        matching = [
            (state.bits[i], bob_state.results[i])
            for i in range(200)
            if state.bases[i] == bob_state.bases[i]
        ]

        # With no noise and no Eve, all matching-basis bits should agree
        errors = sum(a != b for a, b in matching)
        assert errors == 0, f"Expected 0 errors, got {errors}/{len(matching)}"
