"""Tests for the Six‑State protocol."""

from __future__ import annotations

from protocols.six_state import SixStateProtocol


class TestSixStateProtocol:
    """Tests for SixStateProtocol."""

    def test_basic_run_no_eve(self) -> None:
        """Without Eve, QBER should be near zero."""
        proto = SixStateProtocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, eve_present=False)

        assert result.protocol_name == "Six-State"
        assert result.n_qubits == 500
        assert result.sifted_length > 0
        # QBER should be very close to 0 with no noise and no Eve
        assert result.qber < 0.05, f"QBER too high without Eve: {result.qber}"
        assert not result.eve_detected

    def test_run_with_eve(self) -> None:
        """With Eve, QBER should be significantly elevated."""
        proto = SixStateProtocol(alice_seed=10, bob_seed=20, eve_seed=30)
        result = proto.run(500, eve_present=True)

        assert result.eve_present
        # QBER should be noticeable
        assert result.qber > 0.05
        assert result.eve_detected

    def test_sifting_rate_approximately_one_third(self) -> None:
        """Sifting rate should be approximately 1/3 for 3 bases."""
        proto = SixStateProtocol(alice_seed=42, bob_seed=43)
        result = proto.run(1500, eve_present=False)

        sifting_rate = result.sifted_length / result.n_qubits
        # Should be around 1/3 ≈ 0.333, allow wide margin for randomness
        assert 0.2 < sifting_rate < 0.5, f"Unexpected sifting rate: {sifting_rate}"

    def test_run_with_noise(self) -> None:
        """Noise should increase QBER."""
        proto = SixStateProtocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, noise_type="depolarizing", noise_prob=0.1)

        # Noise should introduce some errors
        assert result.qber > 0.0

    def test_final_key_produced(self) -> None:
        """Should produce a non‑empty final key."""
        proto = SixStateProtocol(alice_seed=10, bob_seed=20)
        result = proto.run(500, eve_present=False)
        assert len(result.final_key) > 0
