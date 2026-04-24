#!/usr/bin/env python3
"""Command‑line interface for the QKD protocol simulator.

Usage examples::

    # Basic Six‑State run
    python cli.py --n-qubits 500

    # Six‑State with Eve
    python cli.py --n-qubits 500 --eve

    # BB84 with depolarizing noise
    python cli.py --n-qubits 1000 --protocol bb84 --noise-type depolarizing --noise-level 0.05

    # Compare both protocols and generate plots
    python cli.py --n-qubits 1000 --protocol compare --plot

    # Full sweep analysis
    python cli.py --n-qubits 500 --protocol compare --eve --plot --sweep
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List, Tuple

from analysis.key_rate import (
    compare_protocols,
    compute_effective_key_rate,
    compute_secure_key_rate,
)
from protocols.bb84 import BB84Protocol
from protocols.base import ProtocolResult
from protocols.six_state import SixStateProtocol
from visualization.plots import (
    generate_all_plots,
    plot_key_rate_vs_qubits,
    plot_qber_vs_noise,
)


def _print_result(result: ProtocolResult) -> None:
    """Pretty‑print a protocol result to stdout."""
    print(f"\n{'═' * 60}")
    print(f"  {result.protocol_name} Protocol Results")
    print(f"{'═' * 60}")
    print(f"  Qubits transmitted:  {result.n_qubits}")
    print(f"  Sifted key length:   {result.sifted_length}")
    print(f"  Raw key rate:        {result.raw_key_rate:.4f}")
    print(f"  Sample size (QBER):  {result.sample_size}")
    print(f"  QBER:                {result.qber:.4f} ({result.qber * 100:.2f}%)")
    print(f"  Secure key rate:     {compute_secure_key_rate(result.qber, result.protocol_name.lower().replace('-', '_')):.4f}")
    print(f"  Final key length:    {len(result.final_key)}")
    print(f"  Eve present:         {result.eve_present}")
    print(f"  Eve detected:        {result.eve_detected}")
    print(f"  Noise:               {result.noise_type} (p={result.noise_prob})")

    if result.eve_detected:
        print(f"\n  ⚠️  EAVESDROPPING DETECTED — key compromised!")
    elif result.eve_present:
        print(f"\n  ⚠️  Eve was present but NOT detected (lucky Eve!)")
    else:
        print(f"\n  ✅  Channel secure — key is safe")
    print(f"{'═' * 60}\n")


def _run_noise_sweep(
    protocol_name: str,
    n_qubits: int,
    noise_type: str,
) -> Tuple[List[float], List[float]]:
    """Sweep noise levels and return (levels, qbers)."""
    noise_levels = [0.0, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
    qbers: List[float] = []

    for p in noise_levels:
        if protocol_name == "six_state":
            proto = SixStateProtocol()
        else:
            proto = BB84Protocol()
        result = proto.run(n_qubits, eve_present=False,
                           noise_type=noise_type, noise_prob=p)
        qbers.append(result.qber)
        print(f"  {protocol_name} | noise={p:.2f} → QBER={result.qber:.4f}")

    return noise_levels, qbers


def _run_qubit_sweep(
    protocol_name: str,
    eve_present: bool,
) -> Tuple[List[int], List[float]]:
    """Sweep qubit counts and return (counts, key_rates)."""
    qubit_counts = [50, 100, 200, 500, 750, 1000, 1500, 2000]
    rates: List[float] = []

    for n in qubit_counts:
        if protocol_name == "six_state":
            proto = SixStateProtocol()
        else:
            proto = BB84Protocol()
        result = proto.run(n, eve_present=eve_present)
        rate = compute_effective_key_rate(
            n, result.sifted_length, result.qber,
            protocol_name,
        )
        rates.append(rate)
        print(f"  {protocol_name} | n={n} → key_rate={rate:.4f}")

    return qubit_counts, rates


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Six‑State & BB84 QKD Protocol Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--n-qubits", type=int, default=1000,
        help="Number of qubits to transmit (default: 1000)",
    )
    parser.add_argument(
        "--eve", action="store_true", default=False,
        help="Enable eavesdropper (Eve)",
    )
    parser.add_argument(
        "--noise-type", type=str, default="none",
        choices=["none", "bit_flip", "depolarizing"],
        help="Channel noise model (default: none)",
    )
    parser.add_argument(
        "--noise-level", type=float, default=0.0,
        help="Noise probability [0.0–1.0] (default: 0.0)",
    )
    parser.add_argument(
        "--protocol", type=str, default="six_state",
        choices=["six_state", "bb84", "compare"],
        help="Protocol to run (default: six_state)",
    )
    parser.add_argument(
        "--plot", action="store_true", default=False,
        help="Generate plots in output/ directory",
    )
    parser.add_argument(
        "--sweep", action="store_true", default=False,
        help="Run parameter sweeps (noise + qubit count)",
    )
    parser.add_argument(
        "--output-dir", type=str, default="output",
        help="Directory for plot output (default: output)",
    )

    args = parser.parse_args()

    print("\n🔬 QKD Protocol Simulator")
    print(f"   Configuration: {args.n_qubits} qubits | "
          f"Eve={'ON' if args.eve else 'OFF'} | "
          f"Noise={args.noise_type}({args.noise_level})")
    print()

    # ── Single protocol run ───────────────────────────────────────────────
    if args.protocol in ("six_state", "compare"):
        print("▶ Running Six‑State protocol...")
        six_state = SixStateProtocol()
        result_six = six_state.run(
            args.n_qubits,
            eve_present=args.eve,
            noise_type=args.noise_type,
            noise_prob=args.noise_level,
        )
        _print_result(result_six)

    if args.protocol in ("bb84", "compare"):
        print("▶ Running BB84 protocol...")
        bb84 = BB84Protocol()
        result_bb84 = bb84.run(
            args.n_qubits,
            eve_present=args.eve,
            noise_type=args.noise_type,
            noise_prob=args.noise_level,
        )
        _print_result(result_bb84)

    # ── Comparison ────────────────────────────────────────────────────────
    if args.protocol == "compare":
        print("📊 Protocol Comparison:")
        comparison = compare_protocols(result_six.qber, result_bb84.qber)
        for proto, metrics in comparison.items():
            print(f"\n  {proto}:")
            for key, val in metrics.items():
                print(f"    {key}: {val:.4f}")

    # ── Parameter sweeps ──────────────────────────────────────────────────
    noise_sweep: Dict[str, Tuple[List[float], List[float]]] | None = None
    qubit_sweep: Dict[str, Tuple[List[int], List[float]]] | None = None

    if args.sweep:
        noise_type = args.noise_type if args.noise_type != "none" else "depolarizing"
        print(f"\n📈 Running noise sweep ({noise_type})...")
        noise_sweep = {}

        if args.protocol in ("six_state", "compare"):
            noise_sweep["Six-State"] = _run_noise_sweep(
                "six_state", args.n_qubits, noise_type)

        if args.protocol in ("bb84", "compare"):
            noise_sweep["BB84"] = _run_noise_sweep(
                "bb84", args.n_qubits, noise_type)

        print(f"\n📈 Running qubit count sweep...")
        qubit_sweep = {}

        if args.protocol in ("six_state", "compare"):
            qubit_sweep["Six-State"] = _run_qubit_sweep(
                "six_state", args.eve)

        if args.protocol in ("bb84", "compare"):
            qubit_sweep["BB84"] = _run_qubit_sweep(
                "bb84", args.eve)

    # ── Plots ─────────────────────────────────────────────────────────────
    if args.plot and args.protocol == "compare":
        print(f"\n🎨 Generating plots → {args.output_dir}/")

        # Need results for both protocols with and without Eve
        if not args.eve:
            result_six_eve = SixStateProtocol().run(
                args.n_qubits, eve_present=True,
                noise_type=args.noise_type, noise_prob=args.noise_level)
            result_bb84_eve = BB84Protocol().run(
                args.n_qubits, eve_present=True,
                noise_type=args.noise_type, noise_prob=args.noise_level)
            paths = generate_all_plots(
                result_six, result_six_eve,
                result_bb84, result_bb84_eve,
                noise_sweep=noise_sweep,
                qubit_sweep=qubit_sweep,
                output_dir=args.output_dir,
            )
        else:
            result_six_no_eve = SixStateProtocol().run(
                args.n_qubits, eve_present=False,
                noise_type=args.noise_type, noise_prob=args.noise_level)
            result_bb84_no_eve = BB84Protocol().run(
                args.n_qubits, eve_present=False,
                noise_type=args.noise_type, noise_prob=args.noise_level)
            paths = generate_all_plots(
                result_six_no_eve, result_six,
                result_bb84_no_eve, result_bb84,
                noise_sweep=noise_sweep,
                qubit_sweep=qubit_sweep,
                output_dir=args.output_dir,
            )

        for p in paths:
            print(f"  ✅ Saved: {p}")

    elif args.plot:
        print("\n⚠️  Use --protocol compare --plot for full plot generation")

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
