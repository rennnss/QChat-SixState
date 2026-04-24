#!/usr/bin/env python3
"""QKD Chat Server – Real-time demonstration of Six-State QKD protocol.

Two users (Alice and Bob) exchange messages encrypted with keys generated
via the Six-State QKD protocol. The entire quantum process is visualized
step-by-step in real-time on both clients.

Run with::

    cd chat && python chat_server.py
"""

from __future__ import annotations

import os
import sys
import time
import json
from typing import Dict, List, Optional

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

# Add parent directory to path for quantum imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantum.alice import Alice
from quantum.bob import Bob
from quantum.eve import Eve
from quantum.utils import Basis, SIX_STATE_BASES
from quantum.channel import NoiseType, create_noise_model
from protocols.base import sift_keys
from analysis.qber import compute_qber, split_sample

app = Flask(__name__)
app.config["SECRET_KEY"] = "qkd-demo-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Global state ──────────────────────────────────────────────────────────────

ROOM = "qkd-chat"

state: Dict = {
    "users": {},          # sid → role
    "eve_active": False,
    "n_qubits": 64,       # per message
    "message_count": 0,
}


def _basis_symbol(b: Basis) -> str:
    return {"Z": "⊕", "X": "⊗", "Y": "◉"}[b.value]


def _state_label(bit: int, basis: Basis) -> str:
    labels = {
        (0, "Z"): "|0⟩",
        (1, "Z"): "|1⟩",
        (0, "X"): "|+⟩",
        (1, "X"): "|-⟩",
        (0, "Y"): "|+i⟩",
        (1, "Y"): "|-i⟩",
    }
    return labels.get((bit, basis.value), "?")


def _encrypt_message(message: str, key_bits: List[int]) -> tuple:
    """XOR-encrypt message with one-time pad key.

    Returns (encrypted_binary, encrypted_hex, success).
    """
    msg_bits = []
    for ch in message:
        bits = format(ord(ch), '08b')
        msg_bits.extend(int(b) for b in bits)

    if len(key_bits) < len(msg_bits):
        return "", "", False

    key_used = key_bits[:len(msg_bits)]
    encrypted_bits = [m ^ k for m, k in zip(msg_bits, key_used)]

    encrypted_hex = ""
    for i in range(0, len(encrypted_bits), 8):
        byte = encrypted_bits[i:i+8]
        byte_val = int("".join(str(b) for b in byte), 2)
        encrypted_hex += format(byte_val, '02x')

    return encrypted_bits, encrypted_hex, True


def _decrypt_message(encrypted_bits: List[int], key_bits: List[int]) -> str:
    """XOR-decrypt with one-time pad key."""
    key_used = key_bits[:len(encrypted_bits)]
    decrypted_bits = [e ^ k for e, k in zip(encrypted_bits, key_used)]

    chars = []
    for i in range(0, len(decrypted_bits), 8):
        byte = decrypted_bits[i:i+8]
        if len(byte) == 8:
            char_val = int("".join(str(b) for b in byte), 2)
            chars.append(chr(char_val))
    return "".join(chars)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Socket events ─────────────────────────────────────────────────────────────

@socketio.on("connect")
def handle_connect():
    join_room(ROOM)


@socketio.on("join")
def handle_join(data):
    role = data.get("role", "spectator")
    state["users"][request.sid] = role  # type: ignore[index]
    join_room(ROOM)

    roles_taken = list(state["users"].values())
    emit("user_joined", {
        "role": role,
        "users_online": roles_taken,
    }, room=ROOM)


@socketio.on("disconnect")
def handle_disconnect():
    role = state["users"].pop(request.sid, None)
    if role:
        emit("user_left", {"role": role}, room=ROOM)


@socketio.on("toggle_eve")
def handle_toggle_eve(data):
    state["eve_active"] = data.get("active", False)
    emit("eve_status", {"active": state["eve_active"]}, room=ROOM)


@socketio.on("set_qubits")
def handle_set_qubits(data):
    state["n_qubits"] = max(32, min(256, data.get("n_qubits", 64)))
    emit("qubits_updated", {"n_qubits": state["n_qubits"]}, room=ROOM)


@socketio.on("send_message")
def handle_send_message(data):
    sender_role = state["users"].get(request.sid, "unknown")
    message = data.get("message", "").strip()
    if not message:
        return

    state["message_count"] += 1
    msg_id = state["message_count"]

    # Calculate qubits needed: 8 bits/char × safety margin for sifting + sampling
    msg_bits_needed = len(message) * 8
    n_qubits = max(state["n_qubits"], msg_bits_needed * 8)

    eve_active = state["eve_active"]

    # ── STEP 1: Alice prepares qubits ────────────────────────────────────
    alice = Alice(basis_set=SIX_STATE_BASES)
    alice_state = alice.prepare_qubits(n_qubits)

    # Build qubit display data (show first 20)
    display_count = min(20, n_qubits)
    qubit_data = []
    for i in range(display_count):
        qubit_data.append({
            "index": i,
            "bit": alice_state.bits[i],
            "basis": alice_state.bases[i].value,
            "symbol": _basis_symbol(alice_state.bases[i]),
            "state": _state_label(alice_state.bits[i], alice_state.bases[i]),
        })

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "preparation",
        "sender": sender_role,
        "title": "🔵 Alice Prepares Qubits",
        "description": f"Encoding {n_qubits} random bits in random bases (Z, X, Y)",
        "data": {
            "total_qubits": n_qubits,
            "qubits": qubit_data,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 2: Quantum channel (+ optional Eve) ────────────────────────
    circuits = alice_state.circuits
    eve_data = None

    if eve_active:
        eve = Eve(basis_set=SIX_STATE_BASES)
        eve_state = eve.intercept(circuits)
        circuits = eve_state.forwarded_circuits

        eve_qubit_data = []
        for i in range(display_count):
            eve_qubit_data.append({
                "index": i,
                "eve_basis": eve_state.bases[i].value,
                "eve_bit": eve_state.intercepted_bits[i],
                "alice_basis": alice_state.bases[i].value,
                "match": eve_state.bases[i] == alice_state.bases[i],
            })
        eve_data = {"qubits": eve_qubit_data}

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "channel",
        "sender": sender_role,
        "title": "📡 Quantum Channel" + (" (🕵️ Eve Intercepting!)" if eve_active else ""),
        "description": (
            "Eve intercepts, measures, and re-sends each qubit!"
            if eve_active else
            "Qubits transmitted through secure quantum channel"
        ),
        "data": {
            "eve_active": eve_active,
            "eve_data": eve_data,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 3: Bob measures ──────────────────────────────────────────────
    bob = Bob(basis_set=SIX_STATE_BASES)
    bob_state = bob.measure_qubits(circuits)

    bob_qubit_data = []
    for i in range(display_count):
        bob_qubit_data.append({
            "index": i,
            "basis": bob_state.bases[i].value,
            "symbol": _basis_symbol(bob_state.bases[i]),
            "result": bob_state.results[i],
        })

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "measurement",
        "sender": sender_role,
        "title": "🟢 Bob Measures Qubits",
        "description": f"Bob measures {n_qubits} qubits in random bases",
        "data": {
            "qubits": bob_qubit_data,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 4: Basis reconciliation ──────────────────────────────────────
    alice_sifted, bob_sifted, matching_indices = sift_keys(
        alice_state.bases, bob_state.bases,
        alice_state.bits, bob_state.results,
    )

    sift_data = []
    for i in range(display_count):
        match = alice_state.bases[i] == bob_state.bases[i]
        sift_data.append({
            "index": i,
            "alice_basis": alice_state.bases[i].value,
            "bob_basis": bob_state.bases[i].value,
            "match": match,
            "alice_bit": alice_state.bits[i] if match else None,
            "bob_bit": bob_state.results[i] if match else None,
        })

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "sifting",
        "sender": sender_role,
        "title": "🔗 Basis Reconciliation",
        "description": f"Keeping {len(alice_sifted)} of {n_qubits} bits where bases matched ({len(alice_sifted)*100//n_qubits}%)",
        "data": {
            "total": n_qubits,
            "sifted": len(alice_sifted),
            "rate": round(len(alice_sifted) / n_qubits, 4),
            "qubits": sift_data,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 5: QBER estimation ───────────────────────────────────────────
    if len(alice_sifted) > 0:
        sample_alice, sample_bob, key_alice, key_bob = split_sample(
            alice_sifted, bob_sifted, 0.5
        )
        qber = compute_qber(sample_alice, sample_bob)
        errors = sum(a != b for a, b in zip(sample_alice, sample_bob))
    else:
        qber = 0.0
        key_alice = []
        key_bob = []
        errors = 0
        sample_alice = []

    eve_detected = qber > (1.0 / 3.0 * 0.5)

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "qber",
        "sender": sender_role,
        "title": "📊 QBER Estimation",
        "description": f"Compared {len(sample_alice)} sample bits — {errors} errors found",
        "data": {
            "qber": round(qber, 4),
            "qber_percent": round(qber * 100, 2),
            "sample_size": len(sample_alice),
            "errors": errors,
            "eve_detected": eve_detected,
            "threshold": round(1.0 / 6.0, 4),
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 6: Key generation ────────────────────────────────────────────
    key_preview = key_alice[:32]

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "key",
        "sender": sender_role,
        "title": "🔑 Shared Key Generated",
        "description": f"Key length: {len(key_alice)} bits" + (
            " ⚠️ KEY MAY BE COMPROMISED" if eve_detected else " ✅ Secure"
        ),
        "data": {
            "key_length": len(key_alice),
            "key_preview": "".join(str(b) for b in key_preview) + ("..." if len(key_alice) > 32 else ""),
            "secure": not eve_detected,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 7: Encrypt & send message ────────────────────────────────────
    encrypted_bits, encrypted_hex, success = _encrypt_message(message, key_alice)

    if success:
        decrypted_message = _decrypt_message(encrypted_bits, key_bob)
    else:
        decrypted_message = f"[Key too short — need {len(message)*8} bits, have {len(key_alice)}]"
        encrypted_hex = "[FAILED]"

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "encrypt",
        "sender": sender_role,
        "title": "🔒 Message Encrypted",
        "description": f'"{message}" → {encrypted_hex[:40]}{"..." if len(encrypted_hex) > 40 else ""}',
        "data": {
            "original": message,
            "encrypted_hex": encrypted_hex,
            "success": success,
        },
    }, room=ROOM)

    socketio.sleep(0.05)

    # ── STEP 8: Deliver decrypted message ─────────────────────────────────
    receiver_role = "Bob" if sender_role == "Alice" else "Alice"

    socketio.emit("qkd_step", {
        "msg_id": msg_id,
        "step": "decrypt",
        "sender": sender_role,
        "title": f"🔓 {receiver_role} Decrypts",
        "description": f'Decrypted: "{decrypted_message}"',
        "data": {
            "decrypted": decrypted_message,
            "matches_original": decrypted_message == message,
            "eve_detected": eve_detected,
        },
    }, room=ROOM)

    # ── Final: deliver chat message ───────────────────────────────────────
    socketio.emit("chat_message", {
        "msg_id": msg_id,
        "sender": sender_role,
        "message": message,
        "decrypted": decrypted_message,
        "encrypted_hex": encrypted_hex,
        "qber": round(qber, 4),
        "eve_detected": eve_detected,
        "key_length": len(key_alice),
        "sifted_length": len(alice_sifted),
        "n_qubits": n_qubits,
        "success": success and (decrypted_message == message),
    }, room=ROOM)


if __name__ == "__main__":
    print("\n🔐 QKD Chat Server")
    print("   Open two browser tabs at http://localhost:5050")
    print("   Join as Alice in one tab, Bob in the other\n")
    socketio.run(app, host="0.0.0.0", port=5050, debug=True, allow_unsafe_werkzeug=True)
