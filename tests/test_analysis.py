"""Tests for the analysis modules (QBER + key rate)."""

from __future__ import annotations

import pytest

from analysis.key_rate import (
    compute_effective_key_rate,
    compute_raw_key_rate,
    compute_secure_key_rate,
    compare_protocols,
)
from analysis.qber import compute_qber, split_sample


class TestComputeQBER:
    """Tests for compute_qber()."""

    def test_identical_bits(self) -> None:
        assert compute_qber([0, 1, 0, 1], [0, 1, 0, 1]) == 0.0

    def test_all_different(self) -> None:
        assert compute_qber([0, 0, 0], [1, 1, 1]) == 1.0

    def test_half_errors(self) -> None:
        assert compute_qber([0, 0, 1, 1], [0, 1, 1, 0]) == 0.5

    def test_empty_lists(self) -> None:
        assert compute_qber([], []) == 0.0

    def test_different_lengths_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_qber([0, 1], [0])


class TestSplitSample:
    """Tests for split_sample()."""

    def test_split_half(self) -> None:
        a = [0, 1, 0, 1, 0, 1]
        b = [0, 1, 0, 1, 0, 1]
        sa, sb, ka, kb = split_sample(a, b, 0.5)
        assert len(sa) + len(ka) == 6
        assert len(sb) + len(kb) == 6

    def test_split_preserves_all_bits(self) -> None:
        a = list(range(10))
        b = list(range(10, 20))
        sa, sb, ka, kb = split_sample(a, b, 0.3)
        assert sa + ka == a
        assert sb + kb == b


class TestKeyRate:
    """Tests for key rate computation."""

    def test_raw_key_rate(self) -> None:
        assert compute_raw_key_rate(1000, 333) == pytest.approx(0.333)

    def test_raw_key_rate_zero_qubits(self) -> None:
        assert compute_raw_key_rate(0, 0) == 0.0

    def test_secure_key_rate_zero_qber(self) -> None:
        """Perfect channel → rate = 1.0."""
        assert compute_secure_key_rate(0.0, "six_state") == 1.0
        assert compute_secure_key_rate(0.0, "bb84") == 1.0

    def test_secure_key_rate_high_qber(self) -> None:
        """Very high QBER → rate = 0."""
        assert compute_secure_key_rate(0.5, "six_state") == 0.0
        assert compute_secure_key_rate(0.5, "bb84") == 0.0

    def test_six_state_tolerates_higher_qber(self) -> None:
        """Six‑State should have positive key rate at QBER where BB84 doesn't."""
        # At QBER = 0.12, BB84 key rate should be ~0, Six-State should be positive
        six_rate = compute_secure_key_rate(0.12, "six_state")
        bb84_rate = compute_secure_key_rate(0.12, "bb84")
        assert six_rate > bb84_rate

    def test_effective_key_rate(self) -> None:
        rate = compute_effective_key_rate(1000, 333, 0.0, "six_state")
        assert rate > 0.0

    def test_compare_protocols(self) -> None:
        result = compare_protocols(0.05, 0.08)
        assert "Six-State" in result
        assert "BB84" in result
        assert "qber" in result["Six-State"]
