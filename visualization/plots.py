"""Visualization module for QKD protocol analysis.

Generates publication‑quality Matplotlib plots comparing QBER, key rate,
and eavesdropping detection across protocols and parameter sweeps.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non‑interactive backend for server / CI
import matplotlib.pyplot as plt
import numpy as np

from protocols.base import ProtocolResult


# ── Style defaults ────────────────────────────────────────────────────────────

_COLORS = {
    "Six-State": "#2196F3",
    "BB84": "#FF9800",
    "Eve": "#F44336",
    "No Eve": "#4CAF50",
}

_DEFAULT_OUTPUT_DIR = "output"


def _ensure_output_dir(output_dir: str) -> str:
    """Create the output directory if it doesn't exist."""
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_qber_vs_noise(
    noise_levels: List[float],
    six_state_qbers: List[float],
    bb84_qbers: List[float],
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    filename: str = "qber_vs_noise.png",
) -> str:
    """Plot QBER as a function of channel noise for both protocols.

    Args:
        noise_levels: List of noise probabilities.
        six_state_qbers: QBER values for Six‑State at each noise level.
        bb84_qbers: QBER values for BB84 at each noise level.
        output_dir: Directory to save the plot.
        filename: Output filename.

    Returns:
        Path to the saved plot.
    """
    _ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        noise_levels, six_state_qbers,
        "o-", color=_COLORS["Six-State"], linewidth=2, markersize=6,
        label="Six-State",
    )
    ax.plot(
        noise_levels, bb84_qbers,
        "s--", color=_COLORS["BB84"], linewidth=2, markersize=6,
        label="BB84",
    )

    ax.axhline(y=1 / 3, color=_COLORS["Six-State"], linestyle=":",
               alpha=0.5, label="Six-State threshold (1/3)")
    ax.axhline(y=0.25, color=_COLORS["BB84"], linestyle=":",
               alpha=0.5, label="BB84 threshold (1/4)")

    ax.set_xlabel("Noise Probability", fontsize=12)
    ax.set_ylabel("QBER", fontsize=12)
    ax.set_title("QBER vs Channel Noise", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.02, 0.55)

    path = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_qber_eve_comparison(
    protocols: List[str],
    qber_no_eve: List[float],
    qber_with_eve: List[float],
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    filename: str = "qber_eve_comparison.png",
) -> str:
    """Bar chart comparing QBER with and without Eve for each protocol.

    Args:
        protocols: Protocol names.
        qber_no_eve: QBER without Eve for each protocol.
        qber_with_eve: QBER with Eve for each protocol.
        output_dir: Directory to save the plot.
        filename: Output filename.

    Returns:
        Path to the saved plot.
    """
    _ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.arange(len(protocols))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2, qber_no_eve, width,
        label="No Eve", color=_COLORS["No Eve"], alpha=0.85,
    )
    bars2 = ax.bar(
        x + width / 2, qber_with_eve, width,
        label="With Eve", color=_COLORS["Eve"], alpha=0.85,
    )

    # Add value labels on bars
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.005,
                f"{h:.3f}", ha="center", va="bottom", fontsize=9)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.005,
                f"{h:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_xlabel("Protocol", fontsize=12)
    ax.set_ylabel("QBER", fontsize=12)
    ax.set_title("QBER: No Eve vs Eavesdropping", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_key_rate_vs_qubits(
    qubit_counts: List[int],
    six_state_rates: List[float],
    bb84_rates: List[float],
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    filename: str = "key_rate_vs_qubits.png",
) -> str:
    """Plot key rate as a function of the number of transmitted qubits.

    Args:
        qubit_counts: List of qubit counts.
        six_state_rates: Key rates for Six‑State.
        bb84_rates: Key rates for BB84.
        output_dir: Directory to save the plot.
        filename: Output filename.

    Returns:
        Path to the saved plot.
    """
    _ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        qubit_counts, six_state_rates,
        "o-", color=_COLORS["Six-State"], linewidth=2, markersize=6,
        label="Six-State",
    )
    ax.plot(
        qubit_counts, bb84_rates,
        "s--", color=_COLORS["BB84"], linewidth=2, markersize=6,
        label="BB84",
    )

    ax.set_xlabel("Number of Qubits", fontsize=12)
    ax.set_ylabel("Effective Key Rate (bits/qubit)", fontsize=12)
    ax.set_title("Key Rate vs Number of Qubits", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_secure_key_rate_vs_qber(
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    filename: str = "secure_key_rate_vs_qber.png",
) -> str:
    """Plot theoretical secure key rate vs QBER for both protocols.

    Args:
        output_dir: Directory to save the plot.
        filename: Output filename.

    Returns:
        Path to the saved plot.
    """
    from analysis.key_rate import compute_secure_key_rate

    _ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    qbers = np.linspace(0, 0.5, 200)
    six_state_rates = [compute_secure_key_rate(q, "six_state") for q in qbers]
    bb84_rates = [compute_secure_key_rate(q, "bb84") for q in qbers]

    ax.plot(qbers, six_state_rates, "-", color=_COLORS["Six-State"],
            linewidth=2, label="Six-State")
    ax.plot(qbers, bb84_rates, "--", color=_COLORS["BB84"],
            linewidth=2, label="BB84")

    ax.axvline(x=1 / 3, color=_COLORS["Six-State"], linestyle=":",
               alpha=0.5, label="Six-State max QBER")
    ax.axvline(x=0.25, color=_COLORS["BB84"], linestyle=":",
               alpha=0.5, label="BB84 max QBER")

    ax.fill_between(qbers, 0, six_state_rates, alpha=0.07,
                     color=_COLORS["Six-State"])
    ax.fill_between(qbers, 0, bb84_rates, alpha=0.07,
                     color=_COLORS["BB84"])

    ax.set_xlabel("QBER", fontsize=12)
    ax.set_ylabel("Secure Key Rate (bits/sifted bit)", fontsize=12)
    ax.set_title("Secure Key Rate vs QBER", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 0.5)
    ax.set_ylim(0, 1.05)

    path = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_all_plots(
    results_no_eve_six: ProtocolResult,
    results_eve_six: ProtocolResult,
    results_no_eve_bb84: ProtocolResult,
    results_eve_bb84: ProtocolResult,
    noise_sweep: Optional[
        Dict[str, Tuple[List[float], List[float]]]
    ] = None,
    qubit_sweep: Optional[
        Dict[str, Tuple[List[int], List[float]]]
    ] = None,
    output_dir: str = _DEFAULT_OUTPUT_DIR,
) -> List[str]:
    """Generate all standard analysis plots.

    Args:
        results_no_eve_six: Six‑State result without Eve.
        results_eve_six: Six‑State result with Eve.
        results_no_eve_bb84: BB84 result without Eve.
        results_eve_bb84: BB84 result with Eve.
        noise_sweep: Optional ``{protocol: (noise_levels, qbers)}`` dict.
        qubit_sweep: Optional ``{protocol: (qubit_counts, key_rates)}`` dict.
        output_dir: Directory to save plots.

    Returns:
        List of saved plot file paths.
    """
    paths: List[str] = []

    # ── QBER Eve comparison ───────────────────────────────────────────────
    paths.append(plot_qber_eve_comparison(
        protocols=["Six-State", "BB84"],
        qber_no_eve=[results_no_eve_six.qber, results_no_eve_bb84.qber],
        qber_with_eve=[results_eve_six.qber, results_eve_bb84.qber],
        output_dir=output_dir,
    ))

    # ── Secure key rate vs QBER (theoretical) ────────────────────────────
    paths.append(plot_secure_key_rate_vs_qber(output_dir=output_dir))

    # ── Noise sweep ──────────────────────────────────────────────────────
    if noise_sweep is not None:
        six_levels, six_qbers = noise_sweep.get("Six-State", ([], []))
        bb84_levels, bb84_qbers = noise_sweep.get("BB84", ([], []))
        if six_levels and bb84_levels:
            paths.append(plot_qber_vs_noise(
                noise_levels=six_levels,
                six_state_qbers=six_qbers,
                bb84_qbers=bb84_qbers,
                output_dir=output_dir,
            ))

    # ── Qubit sweep ──────────────────────────────────────────────────────
    if qubit_sweep is not None:
        six_counts, six_rates = qubit_sweep.get("Six-State", ([], []))
        bb84_counts, bb84_rates = qubit_sweep.get("BB84", ([], []))
        if six_counts and bb84_counts:
            paths.append(plot_key_rate_vs_qubits(
                qubit_counts=six_counts,
                six_state_rates=six_rates,
                bb84_rates=bb84_rates,
                output_dir=output_dir,
            ))

    return paths
