"""Tests for quantum.eve – intercept‑resend attack."""

from __future__ import annotations

from quantum.alice import Alice
from quantum.bob import Bob
from quantum.eve import Eve
from quantum.utils import SIX_STATE_BASES, BB84_BASES
from protocols.base import sift_keys
from analysis.qber import compute_qber


class TestEve:
    """Tests for the Eve class."""

    def test_intercept_returns_correct_count(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=10)
        state = alice.prepare_qubits(50)
        eve = Eve(basis_set=SIX_STATE_BASES, seed=30)
        eve_state = eve.intercept(state.circuits)
        assert len(eve_state.bases) == 50
        assert len(eve_state.intercepted_bits) == 50
        assert len(eve_state.forwarded_circuits) == 50

    def test_intercepted_bits_are_binary(self) -> None:
        alice = Alice(basis_set=SIX_STATE_BASES, seed=10)
        state = alice.prepare_qubits(100)
        eve = Eve(basis_set=SIX_STATE_BASES, seed=30)
        eve_state = eve.intercept(state.circuits)
        assert all(b in (0, 1) for b in eve_state.intercepted_bits)

    def test_eve_introduces_errors_six_state(self) -> None:
        """Eve's interception should introduce ~33% QBER in Six‑State."""
        n = 600
        alice = Alice(basis_set=SIX_STATE_BASES, seed=1)
        state = alice.prepare_qubits(n)

        eve = Eve(basis_set=SIX_STATE_BASES, seed=2)
        eve_state = eve.intercept(state.circuits)

        bob = Bob(basis_set=SIX_STATE_BASES, seed=3)
        bob_state = bob.measure_qubits(eve_state.forwarded_circuits)

        alice_sifted, bob_sifted, _ = sift_keys(
            state.bases, bob_state.bases, state.bits, bob_state.results
        )

        if len(alice_sifted) > 0:
            qber = compute_qber(alice_sifted, bob_sifted)
            # Theoretical QBER with Eve on Six‑State ≈ 1/3 ≈ 0.333
            # Allow statistical variation: should be well above 0.05
            assert qber > 0.05, f"QBER too low with Eve: {qber:.4f}"

    def test_eve_introduces_errors_bb84(self) -> None:
        """Eve's interception should introduce ~25% QBER in BB84."""
        n = 600
        alice = Alice(basis_set=BB84_BASES, seed=1)
        state = alice.prepare_qubits(n)

        eve = Eve(basis_set=BB84_BASES, seed=2)
        eve_state = eve.intercept(state.circuits)

        bob = Bob(basis_set=BB84_BASES, seed=3)
        bob_state = bob.measure_qubits(eve_state.forwarded_circuits)

        alice_sifted, bob_sifted, _ = sift_keys(
            state.bases, bob_state.bases, state.bits, bob_state.results
        )

        if len(alice_sifted) > 0:
            qber = compute_qber(alice_sifted, bob_sifted)
            # Theoretical ≈ 0.25; should be well above 0.05
            assert qber > 0.05, f"QBER too low with Eve: {qber:.4f}"
