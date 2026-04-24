# 🔐 Six-State Quantum Key Distribution Simulator

A **production-ready** implementation of the Six-State QKD protocol using [Qiskit](https://qiskit.org/), with full support for eavesdropping simulation, channel noise, comparative analysis against BB84, and interactive visualization.

## 📖 Theory

### Quantum Key Distribution

QKD allows two parties (Alice and Bob) to establish a shared secret key with security guaranteed by the laws of quantum mechanics. Any eavesdropping attempt by Eve inevitably disturbs the quantum states, revealing her presence.

### Six-State Protocol

The Six-State protocol uses **three mutually unbiased bases** (MUBs):

| Basis | States | Qiskit Gates |
|-------|--------|-------------|
| **Z** (computational) | \|0⟩, \|1⟩ | Identity, X |
| **X** (Hadamard) | \|+⟩, \|−⟩ | H, XH |
| **Y** (circular) | \|+i⟩, \|−i⟩ | HS, XHS |

**Protocol steps:**
1. **Preparation**: Alice encodes random bits in random bases (Z, X, Y)
2. **Transmission**: Qubits sent through quantum channel
3. **Measurement**: Bob measures in randomly chosen bases
4. **Sifting**: Keep bits where bases match (~1/3 retained)
5. **QBER estimation**: Compare a sample to detect errors
6. **Key generation**: Remaining bits form the shared secret key

### Comparison with BB84

| Property | Six-State | BB84 |
|----------|-----------|------|
| Bases | Z, X, Y | Z, X |
| Sifting rate | ~1/3 | ~1/2 |
| Eve's QBER (intercept-resend) | ~33% | ~25% |
| Max tolerable QBER | ~27.6% | ~11% |
| Security margin | Higher | Lower |

### Intercept-Resend Attack

Eve intercepts each qubit, measures it in a random basis, and re-prepares based on her result. When her basis doesn't match Alice's, she introduces errors detectable through QBER estimation.

## 🛠️ Installation

```bash
# Clone the repository
git clone <repo-url> && cd Quantum

# Create virtual environment (recommended)
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements
- Python ≥ 3.10
- Qiskit ≥ 1.0.0
- Qiskit Aer ≥ 0.13.0
- NumPy, Matplotlib, Streamlit, pytest

## 🚀 Usage

### CLI

```bash
# Basic Six-State simulation
python cli.py --n-qubits 500

# With eavesdropper
python cli.py --n-qubits 500 --eve

# BB84 with noise
python cli.py --n-qubits 1000 --protocol bb84 --noise-type depolarizing --noise-level 0.05

# Compare protocols with plots
python cli.py --n-qubits 1000 --protocol compare --plot

# Full sweep analysis
python cli.py --n-qubits 500 --protocol compare --eve --plot --sweep
```

**CLI Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--n-qubits` | Number of qubits | 1000 |
| `--eve` | Enable eavesdropper | Off |
| `--noise-type` | `none`, `bit_flip`, `depolarizing` | `none` |
| `--noise-level` | Noise probability [0–1] | 0.0 |
| `--protocol` | `six_state`, `bb84`, `compare` | `six_state` |
| `--plot` | Generate plots | Off |
| `--sweep` | Run parameter sweeps | Off |

### Streamlit UI

```bash
streamlit run app.py
```

Interactive dashboard with:
- Sidebar controls for all parameters
- Real-time QBER and key rate metrics
- Protocol comparison mode
- Tabbed visualizations with parameter sweeps

### Demo Notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

## 📊 Sample Results

### No Eve (ideal channel)
```
Six-State: QBER ≈ 0.00%, Sifting ≈ 33%, Key Rate ≈ 0.167
BB84:      QBER ≈ 0.00%, Sifting ≈ 50%, Key Rate ≈ 0.250
```

### With Eve (intercept-resend)
```
Six-State: QBER ≈ 33%, Eve DETECTED ⚠️
BB84:      QBER ≈ 25%, Eve DETECTED ⚠️
```

## 📁 Project Structure

```
Quantum/
├── cli.py                    # CLI entry point
├── app.py                    # Streamlit dashboard
├── requirements.txt
├── quantum/
│   ├── utils.py              # Basis enum, circuit builders
│   ├── alice.py              # Sender (qubit preparation)
│   ├── bob.py                # Receiver (measurement)
│   ├── eve.py                # Eavesdropper (intercept-resend)
│   └── channel.py            # Noise models
├── protocols/
│   ├── base.py               # Abstract protocol + sifting
│   ├── six_state.py          # Six-State implementation
│   └── bb84.py               # BB84 implementation
├── analysis/
│   ├── qber.py               # QBER computation
│   └── key_rate.py           # Key rate estimation
├── visualization/
│   └── plots.py              # Matplotlib visualizations
├── tests/                    # Comprehensive pytest suite
└── notebooks/
    └── demo.ipynb            # Interactive demo
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_six_state.py -v

# With coverage
python -m pytest tests/ -v --tb=short
```

## 📄 License

MIT
