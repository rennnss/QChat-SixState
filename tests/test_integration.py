"""Integration tests – full end‑to‑end protocol runs."""

from __future__ import annotations

from protocols.bb84 import BB84Protocol
from protocols.six_state import SixStateProtocol


class TestIntegration:
    """End‑to‑end protocol integration tests."""

    def test_six_state_no_eve_no_noise(self) -> None:
        """Clean Six‑State run should produce usable key with near‑zero QBER."""
        result = SixStateProtocol(alice_seed=1, bob_seed=2).run(300)
        assert result.sifted_length > 0
        assert result.qber < 0.05
        assert len(result.final_key) > 0
        assert not result.eve_detected

    def test_bb84_no_eve_no_noise(self) -> None:
        result = BB84Protocol(alice_seed=1, bob_seed=2).run(300)
        assert result.sifted_length > 0
        assert result.qber < 0.05
        assert len(result.final_key) > 0
        assert not result.eve_detected

    def test_six_state_with_eve(self) -> None:
        result = SixStateProtocol(
            alice_seed=1, bob_seed=2, eve_seed=3
        ).run(500, eve_present=True)
        assert result.qber > 0.05
        assert result.eve_detected

    def test_bb84_with_eve(self) -> None:
        result = BB84Protocol(
            alice_seed=1, bob_seed=2, eve_seed=3
        ).run(500, eve_present=True)
        assert result.qber > 0.05
        assert result.eve_detected

    def test_six_state_with_noise(self) -> None:
        result = SixStateProtocol(alice_seed=1, bob_seed=2).run(
            300, noise_type="depolarizing", noise_prob=0.1)
        assert result.qber > 0.0
        assert result.sifted_length > 0

    def test_bb84_with_noise(self) -> None:
        result = BB84Protocol(alice_seed=1, bob_seed=2).run(
            300, noise_type="bit_flip", noise_prob=0.1)
        assert result.qber > 0.0
        assert result.sifted_length > 0

    def test_six_state_eve_has_higher_qber_than_no_eve(self) -> None:
        """Eve should measurably increase QBER."""
        no_eve = SixStateProtocol(alice_seed=1, bob_seed=2).run(500)
        with_eve = SixStateProtocol(
            alice_seed=1, bob_seed=2, eve_seed=3
        ).run(500, eve_present=True)
        assert with_eve.qber > no_eve.qber

    def test_bb84_sifting_rate_higher_than_six_state(self) -> None:
        """BB84 (2 bases) should sift more bits than Six‑State (3 bases)."""
        n = 1500
        six = SixStateProtocol(alice_seed=1, bob_seed=2).run(n)
        bb84 = BB84Protocol(alice_seed=1, bob_seed=2).run(n)
        assert bb84.raw_key_rate > six.raw_key_rate
