"""Tests for quantum.channel – noise models."""

from __future__ import annotations

import pytest

from quantum.channel import NoiseType, create_noise_model


class TestCreateNoiseModel:
    """Tests for create_noise_model()."""

    def test_none_returns_none(self) -> None:
        model = create_noise_model(NoiseType.NONE, 0.1)
        assert model is None

    def test_zero_probability_returns_none(self) -> None:
        model = create_noise_model(NoiseType.BIT_FLIP, 0.0)
        assert model is None

    def test_bit_flip_returns_model(self) -> None:
        model = create_noise_model(NoiseType.BIT_FLIP, 0.1)
        assert model is not None

    def test_depolarizing_returns_model(self) -> None:
        model = create_noise_model(NoiseType.DEPOLARIZING, 0.05)
        assert model is not None

    def test_invalid_probability_raises(self) -> None:
        with pytest.raises(ValueError):
            create_noise_model(NoiseType.BIT_FLIP, -0.1)
        with pytest.raises(ValueError):
            create_noise_model(NoiseType.BIT_FLIP, 1.5)
