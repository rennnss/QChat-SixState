"""Tests for the BB84 protocol."""

from __future__ import annotations

from protocols.bb84 import BB84Protocol


class TestBB84Protocol:
    """Tests for BB84Protocol."""

    def test_basic_run_no_eve(self) -> None:
        """Without Eve, QBER should be near zero."""
        proto = BB84Protocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, eve_present=False)

        assert result.protocol_name == "BB84"
        assert result.n_qubits == 500
        assert result.sifted_length > 0
        assert result.qber < 0.05
        assert not result.eve_detected

    def test_run_with_eve(self) -> None:
        """With Eve, QBER should be significantly elevated."""
        proto = BB84Protocol(alice_seed=10, bob_seed=20, eve_seed=30)
        result = proto.run(500, eve_present=True)

        assert result.eve_present
        assert result.qber > 0.05
        assert result.eve_detected

    def test_sifting_rate_approximately_one_half(self) -> None:
        """Sifting rate should be approximately 1/2 for 2 bases."""
        proto = BB84Protocol(alice_seed=42, bob_seed=43)
        result = proto.run(1500, eve_present=False)

        sifting_rate = result.sifted_length / result.n_qubits
        # Should be around 1/2 = 0.5, allow wide margin
        assert 0.35 < sifting_rate < 0.65, f"Unexpected sifting rate: {sifting_rate}"

    def test_run_with_noise(self) -> None:
        proto = BB84Protocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, noise_type="bit_flip", noise_prob=0.1)
        assert result.qber > 0.0

    def test_final_key_produced(self) -> None:
        proto = BB84Protocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, eve_present=False)
        assert len(result.final_key) > 0
