"""Quantum channel with configurable noise models.

Wraps Qiskit Aer ``NoiseModel`` to simulate realistic channel imperfections
such as bit‑flip errors and depolarizing noise.
"""

from __future__ import annotations

import enum
from typing import Optional

from qiskit_aer.noise import NoiseModel, depolarizing_error


class NoiseType(enum.Enum):
    """Supported noise channel types."""

    NONE = "none"
    BIT_FLIP = "bit_flip"
    DEPOLARIZING = "depolarizing"


def create_noise_model(
    noise_type: NoiseType,
    probability: float,
) -> Optional[NoiseModel]:
    """Build a Qiskit ``NoiseModel`` for the specified channel noise.

    Args:
        noise_type: Type of noise to simulate.
        probability: Error probability (0.0 = perfect channel, 1.0 = max noise).

    Returns:
        A ``NoiseModel`` instance, or ``None`` if ``noise_type`` is
        ``NoiseType.NONE`` or *probability* is 0.

    Raises:
        ValueError: If *probability* is outside [0, 1].
    """
    if probability < 0.0 or probability > 1.0:
        raise ValueError(f"Probability must be in [0, 1], got {probability}")

    if noise_type == NoiseType.NONE or probability == 0.0:
        return None

    noise_model = NoiseModel()

    if noise_type == NoiseType.BIT_FLIP:
        # Bit‑flip channel: X applied with given probability
        error = depolarizing_error(0, 1)  # placeholder — build manually
        from qiskit_aer.noise import pauli_error

        error = pauli_error([("X", probability), ("I", 1 - probability)])
        # Apply to all single‑qubit gates that appear in our circuits
        for gate in ["x", "h", "s", "sdg", "id", "measure"]:
            noise_model.add_all_qubit_quantum_error(error, gate)

    elif noise_type == NoiseType.DEPOLARIZING:
        error = depolarizing_error(probability, 1)
        for gate in ["x", "h", "s", "sdg", "id", "measure"]:
            noise_model.add_all_qubit_quantum_error(error, gate)

    return noise_model
