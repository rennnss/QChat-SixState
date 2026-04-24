"""Streamlit UI for the QKD Protocol Simulator.

Run with::

    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import matplotlib
matplotlib.use("Agg")

from analysis.key_rate import (
    compare_protocols,
    compute_effective_key_rate,
    compute_secure_key_rate,
)
from protocols.bb84 import BB84Protocol
from protocols.base import ProtocolResult
from protocols.six_state import SixStateProtocol
from visualization.plots import (
    plot_qber_eve_comparison,
    plot_qber_vs_noise,
    plot_key_rate_vs_qubits,
    plot_secure_key_rate_vs_qber,
)

import matplotlib.pyplot as plt
import numpy as np


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="QKD Simulator",
    page_icon="🔐",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown("## 🔐 QKD Simulator Controls")

n_qubits = st.sidebar.slider(
    "Number of Qubits",
    min_value=50, max_value=5000, value=500, step=50,
    help="Total qubits Alice transmits to Bob",
)

eve_present = st.sidebar.toggle("Enable Eve 🕵️", value=False)

noise_type = st.sidebar.selectbox(
    "Noise Model",
    options=["none", "bit_flip", "depolarizing"],
    format_func=lambda x: {
        "none": "None (ideal channel)",
        "bit_flip": "Bit-Flip",
        "depolarizing": "Depolarizing",
    }[x],
)

noise_level = 0.0
if noise_type != "none":
    noise_level = st.sidebar.slider(
        "Noise Probability",
        min_value=0.0, max_value=0.5, value=0.05, step=0.01,
    )

protocol_mode = st.sidebar.radio(
    "Protocol",
    ["Six-State", "BB84", "Compare Both"],
)

run_sweep = st.sidebar.toggle("Run Parameter Sweeps 📊", value=False)

run_button = st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True)

# ── Main content ──────────────────────────────────────────────────────────────

st.markdown('<p class="main-header">Quantum Key Distribution Simulator</p>', unsafe_allow_html=True)
st.markdown("Simulate and analyze the **Six-State** and **BB84** QKD protocols with configurable noise and eavesdropping.")

if run_button:
    results = {}

    with st.spinner("Running quantum simulation..."):
        # ── Run protocols ─────────────────────────────────────────────────
        if protocol_mode in ("Six-State", "Compare Both"):
            proto = SixStateProtocol()
            results["Six-State"] = proto.run(
                n_qubits, eve_present=eve_present,
                noise_type=noise_type, noise_prob=noise_level,
            )

        if protocol_mode in ("BB84", "Compare Both"):
            proto = BB84Protocol()
            results["BB84"] = proto.run(
                n_qubits, eve_present=eve_present,
                noise_type=noise_type, noise_prob=noise_level,
            )

    # ── Display results ───────────────────────────────────────────────────
    for name, result in results.items():
        st.markdown(f"### {name} Protocol Results")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sifted Key Length", result.sifted_length)
        with col2:
            st.metric("QBER", f"{result.qber:.4f}", f"{result.qber * 100:.1f}%")
        with col3:
            skr = compute_secure_key_rate(
                result.qber,
                name.lower().replace("-", "_"),
            )
            st.metric("Secure Key Rate", f"{skr:.4f}")
        with col4:
            st.metric("Final Key Length", len(result.final_key))

        # Detection status
        if result.eve_detected:
            st.error("⚠️ **EAVESDROPPING DETECTED** — Key is compromised!")
        elif result.eve_present:
            st.warning("⚠️ Eve was present but **not detected** (lucky Eve)")
        else:
            st.success("✅ Channel is secure — key is safe")

        st.divider()

    # ── Comparison ────────────────────────────────────────────────────────
    if protocol_mode == "Compare Both":
        st.markdown("### 📊 Protocol Comparison")

        comp = compare_protocols(
            results["Six-State"].qber,
            results["BB84"].qber,
        )

        col1, col2 = st.columns(2)
        for i, (proto, metrics) in enumerate(comp.items()):
            with (col1 if i == 0 else col2):
                st.markdown(f"**{proto}**")
                for k, v in metrics.items():
                    st.write(f"- {k}: `{v:.4f}`")

    # ── Plots ─────────────────────────────────────────────────────────────
    st.markdown("### 📈 Visualizations")

    # Secure key rate vs QBER (always available)
    tab1, tab2, tab3, tab4 = st.tabs([
        "Secure Rate vs QBER",
        "Eve Detection",
        "QBER vs Noise Sweep",
        "Key Rate vs Qubits",
    ])

    with tab1:
        from analysis.key_rate import compute_secure_key_rate as _skr
        fig, ax = plt.subplots(figsize=(8, 5))
        qbers = np.linspace(0, 0.5, 200)
        ax.plot(qbers, [_skr(q, "six_state") for q in qbers],
                "-", color="#2196F3", linewidth=2, label="Six-State")
        ax.plot(qbers, [_skr(q, "bb84") for q in qbers],
                "--", color="#FF9800", linewidth=2, label="BB84")
        ax.axvline(x=1/3, color="#2196F3", linestyle=":", alpha=0.5)
        ax.axvline(x=0.25, color="#FF9800", linestyle=":", alpha=0.5)

        # Mark current QBER
        for name, result in results.items():
            color = "#2196F3" if name == "Six-State" else "#FF9800"
            proto_key = name.lower().replace("-", "_")
            ax.plot(result.qber, _skr(result.qber, proto_key),
                    "o", color=color, markersize=10, zorder=5)
            ax.annotate(f"{name}\nQBER={result.qber:.3f}",
                       (result.qber, _skr(result.qber, proto_key)),
                       textcoords="offset points", xytext=(15, 10),
                       fontsize=9, color=color)

        ax.set_xlabel("QBER")
        ax.set_ylabel("Secure Key Rate")
        ax.set_title("Secure Key Rate vs QBER")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    with tab2:
        if protocol_mode == "Compare Both":
            # Run without Eve for comparison
            six_no_eve = SixStateProtocol().run(
                n_qubits, eve_present=False,
                noise_type=noise_type, noise_prob=noise_level)
            bb84_no_eve = BB84Protocol().run(
                n_qubits, eve_present=False,
                noise_type=noise_type, noise_prob=noise_level)

            fig, ax = plt.subplots(figsize=(8, 5))
            x = np.arange(2)
            width = 0.35
            ax.bar(x - width/2,
                   [six_no_eve.qber, bb84_no_eve.qber],
                   width, label="No Eve", color="#4CAF50", alpha=0.85)

            six_eve = results.get("Six-State", SixStateProtocol().run(
                n_qubits, eve_present=True,
                noise_type=noise_type, noise_prob=noise_level))
            bb84_eve = results.get("BB84", BB84Protocol().run(
                n_qubits, eve_present=True,
                noise_type=noise_type, noise_prob=noise_level))

            if not eve_present:
                six_eve = SixStateProtocol().run(
                    n_qubits, eve_present=True,
                    noise_type=noise_type, noise_prob=noise_level)
                bb84_eve = BB84Protocol().run(
                    n_qubits, eve_present=True,
                    noise_type=noise_type, noise_prob=noise_level)

            ax.bar(x + width/2,
                   [six_eve.qber, bb84_eve.qber],
                   width, label="With Eve", color="#F44336", alpha=0.85)

            ax.set_xticks(x)
            ax.set_xticklabels(["Six-State", "BB84"])
            ax.set_ylabel("QBER")
            ax.set_title("QBER: No Eve vs Eavesdropping")
            ax.legend()
            ax.grid(True, alpha=0.3, axis="y")
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Select 'Compare Both' to see Eve detection comparison")

    with tab3:
        if run_sweep:
            with st.spinner("Running noise sweep..."):
                nt = noise_type if noise_type != "none" else "depolarizing"
                noise_levels = [0.0, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3]
                six_qbers = []
                bb84_qbers = []

                progress = st.progress(0)
                for i, p in enumerate(noise_levels):
                    r = SixStateProtocol().run(n_qubits, noise_type=nt, noise_prob=p)
                    six_qbers.append(r.qber)
                    r = BB84Protocol().run(n_qubits, noise_type=nt, noise_prob=p)
                    bb84_qbers.append(r.qber)
                    progress.progress((i + 1) / len(noise_levels))

                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(noise_levels, six_qbers, "o-", color="#2196F3",
                       linewidth=2, label="Six-State")
                ax.plot(noise_levels, bb84_qbers, "s--", color="#FF9800",
                       linewidth=2, label="BB84")
                ax.axhline(y=1/3, color="#2196F3", linestyle=":", alpha=0.5)
                ax.axhline(y=0.25, color="#FF9800", linestyle=":", alpha=0.5)
                ax.set_xlabel("Noise Probability")
                ax.set_ylabel("QBER")
                ax.set_title(f"QBER vs {nt.replace('_', ' ').title()} Noise")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close(fig)
        else:
            st.info("Enable 'Run Parameter Sweeps' in the sidebar")

    with tab4:
        if run_sweep:
            with st.spinner("Running qubit sweep..."):
                counts = [50, 100, 200, 500, 750, 1000, 1500, 2000]
                six_rates = []
                bb84_rates = []

                progress = st.progress(0)
                for i, n in enumerate(counts):
                    r = SixStateProtocol().run(n)
                    six_rates.append(compute_effective_key_rate(
                        n, r.sifted_length, r.qber, "six_state"))
                    r = BB84Protocol().run(n)
                    bb84_rates.append(compute_effective_key_rate(
                        n, r.sifted_length, r.qber, "bb84"))
                    progress.progress((i + 1) / len(counts))

                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(counts, six_rates, "o-", color="#2196F3",
                       linewidth=2, label="Six-State")
                ax.plot(counts, bb84_rates, "s--", color="#FF9800",
                       linewidth=2, label="BB84")
                ax.set_xlabel("Number of Qubits")
                ax.set_ylabel("Effective Key Rate")
                ax.set_title("Key Rate vs Number of Qubits")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close(fig)
        else:
            st.info("Enable 'Run Parameter Sweeps' in the sidebar")

    # ── Raw key preview ───────────────────────────────────────────────────
    st.markdown("### 🔑 Key Preview")
    for name, result in results.items():
        preview = result.final_key[:50]
        key_str = "".join(str(b) for b in preview)
        if len(result.final_key) > 50:
            key_str += "..."
        st.code(f"{name}: {key_str}", language="text")

else:
    st.info("👈 Configure parameters in the sidebar and click **Run Simulation**")

    # Show protocol info
    with st.expander("ℹ️ About the Six-State Protocol"):
        st.markdown("""
        The **Six-State protocol** uses three mutually unbiased bases
        (Z, X, Y) for qubit encoding, compared to BB84's two bases (Z, X).

        **Key differences from BB84:**
        - **Sifting rate**: ~1/3 (vs ~1/2 for BB84)
        - **Eve detection**: QBER ≈ 33% under intercept-resend (vs 25% for BB84)
        - **Security**: Tolerates higher noise before key rate drops to zero
        - **Trade-off**: Lower raw key rate but better security margin

        | Property | Six-State | BB84 |
        |----------|-----------|------|
        | Bases | Z, X, Y | Z, X |
        | Sifting rate | ~1/3 | ~1/2 |
        | Eve QBER | ~33% | ~25% |
        | Max tolerable QBER | ~27.6% | ~11% |
        """)
