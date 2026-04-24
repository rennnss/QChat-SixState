/**
 * QKD Secure Chat – Client-side application
 *
 * Manages SocketIO connection, role selection, message sending,
 * and real-time QKD protocol step visualization.
 */

// ── State ────────────────────────────────────────────────────────────────────

let socket = null;
let myRole = null;
let peerConnected = false;
let qkdPanelVisible = true;
let helpModalVisible = false;

// ── Initialization ───────────────────────────────────────────────────────────

function init() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('user_joined', handleUserJoined);
    socket.on('user_left', handleUserLeft);
    socket.on('eve_status', handleEveStatus);
    socket.on('qkd_step', handleQKDStep);
    socket.on('chat_message', handleChatMessage);
}

// ── Role Selection ───────────────────────────────────────────────────────────

function joinAs(role) {
    myRole = role;
    socket.emit('join', { role: role });

    document.getElementById('role-screen').classList.remove('active');
    document.getElementById('chat-screen').classList.add('active');

    const avatar = document.getElementById('my-avatar');
    avatar.textContent = role[0];
    avatar.className = `role-avatar-sm ${role.toLowerCase()}-avatar`;
    avatar.style.background = role === 'Alice'
        ? 'linear-gradient(135deg, #6366f1, #a855f7)'
        : 'linear-gradient(135deg, #06b6d4, #22d3ee)';

    document.getElementById('my-role').textContent = role;
}

// ── Connection Events ────────────────────────────────────────────────────────

function handleUserJoined(data) {
    const users = data.users_online;
    const hasAlice = users.includes('Alice');
    const hasBob = users.includes('Bob');

    if (hasAlice && hasBob) {
        peerConnected = true;
        const peerName = myRole === 'Alice' ? 'Bob' : 'Alice';
        document.getElementById('peer-status').innerHTML =
            `<span class="status-dot online"></span><span>${peerName} is online</span>`;
        document.getElementById('header-status').textContent = `Connected with ${peerName}`;
        document.getElementById('header-status').className = 'header-badge connected';
        document.getElementById('message-input').disabled = false;
        document.getElementById('send-btn').disabled = false;
    }

    if (data.role !== myRole) {
        addSystemMessage(`${data.role} has joined the chat`);
    }
}

function handleUserLeft(data) {
    if (data.role !== myRole) {
        peerConnected = false;
        document.getElementById('peer-status').innerHTML =
            '<span class="status-dot offline"></span><span>Partner disconnected</span>';
        document.getElementById('header-status').textContent = 'Partner disconnected';
        document.getElementById('header-status').className = 'header-badge';
        document.getElementById('message-input').disabled = true;
        document.getElementById('send-btn').disabled = true;
        addSystemMessage(`${data.role} has left the chat`);
    }
}

// ── Eve Toggle ───────────────────────────────────────────────────────────────

function toggleEve() {
    const active = document.getElementById('eve-toggle').checked;
    socket.emit('toggle_eve', { active: active });
}

function handleEveStatus(data) {
    const indicator = document.getElementById('eve-indicator');
    const toggle = document.getElementById('eve-toggle');
    toggle.checked = data.active;
    if (data.active) {
        indicator.classList.remove('hidden');
        addSystemMessage('⚠️ Eve is now intercepting the quantum channel!');
    } else {
        indicator.classList.add('hidden');
        addSystemMessage('✅ Eve has stopped intercepting');
    }
}

// ── Message Sending ──────────────────────────────────────────────────────────

function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message || !peerConnected) return;

    input.value = '';
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;

    socket.emit('send_message', { message: message });
}

// ── QKD Panel Toggle ─────────────────────────────────────────────────────────

function toggleQKDPanel() {
    const panel = document.getElementById('qkd-panel');
    const arrow = document.getElementById('qkd-toggle-arrow');
    qkdPanelVisible = !qkdPanelVisible;
    if (qkdPanelVisible) {
        panel.classList.remove('collapsed');
        arrow.classList.remove('up');
    } else {
        panel.classList.add('collapsed');
        arrow.classList.add('up');
    }
}

// ── Help Modal ───────────────────────────────────────────────────────────────

function toggleHelp() {
    const modal = document.getElementById('help-modal');
    helpModalVisible = !helpModalVisible;
    if (helpModalVisible) {
        modal.classList.add('visible');
    } else {
        modal.classList.remove('visible');
    }
}

function closeHelpOnBackdrop(e) {
    if (e.target.id === 'help-modal') {
        toggleHelp();
    }
}

// ── QKD Step Visualization ───────────────────────────────────────────────────

function handleQKDStep(data) {
    const container = document.getElementById('qkd-steps');

    // Clear all previous steps when a NEW message starts
    if (data.step === 'preparation') {
        container.innerHTML = '';

        // Add message header
        const header = document.createElement('div');
        header.className = 'qkd-msg-header';
        header.innerHTML = `
            <span class="qkd-msg-icon">${data.sender === 'Alice' ? '🔵' : '🟢'}</span>
            <span>Message from <strong>${data.sender}</strong></span>
            <span class="qkd-msg-id">#${data.msg_id}</span>
        `;
        container.appendChild(header);
    }

    const card = createStepCard(data);
    container.appendChild(card);

    // Auto-scroll to the new step
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });
}

function createStepCard(data) {
    const card = document.createElement('div');
    const eveClass = data.step === 'channel' && data.data.eve_active ? ' eve-active' : '';
    card.className = `qkd-step-card step-${data.step}${eveClass}`;

    let badge = '';
    let bodyHTML = '';
    let stepNum = getStepNumber(data.step);

    switch (data.step) {
        case 'preparation':
            badge = `<span class="step-badge" style="background:rgba(99,102,241,0.15);color:#6366f1">${data.data.total_qubits} qubits</span>`;
            bodyHTML = renderPreparation(data.data);
            break;
        case 'channel':
            if (data.data.eve_active) {
                badge = '<span class="step-badge" style="background:rgba(244,63,94,0.15);color:#f43f5e">🕵️ INTERCEPTED</span>';
                bodyHTML = renderEveChannel(data.data);
            } else {
                badge = '<span class="step-badge" style="background:rgba(52,211,153,0.15);color:#34d399">SECURE</span>';
                bodyHTML = `<div class="step-description">${data.description}</div>`;
            }
            break;
        case 'measurement':
            badge = '';
            bodyHTML = renderMeasurement(data.data);
            break;
        case 'sifting':
            badge = `<span class="step-badge" style="background:rgba(168,85,247,0.15);color:#a855f7">${data.data.rate * 100 | 0}% kept</span>`;
            bodyHTML = renderSifting(data);
            break;
        case 'qber':
            const qberSafe = data.data.qber < 0.167;
            const qColor = qberSafe ? 'rgba(52,211,153,0.15)' : 'rgba(244,63,94,0.15)';
            const qTextColor = qberSafe ? '#34d399' : '#f43f5e';
            badge = `<span class="step-badge" style="background:${qColor};color:${qTextColor}">${data.data.qber_percent}%</span>`;
            bodyHTML = renderQBER(data.data);
            break;
        case 'key':
            const secure = data.data.secure;
            badge = secure
                ? '<span class="step-badge" style="background:rgba(52,211,153,0.15);color:#34d399">✅ SECURE</span>'
                : '<span class="step-badge" style="background:rgba(244,63,94,0.15);color:#f43f5e">⚠️ COMPROMISED</span>';
            bodyHTML = renderKey(data.data);
            break;
        case 'encrypt':
            badge = '<span class="step-badge" style="background:rgba(251,191,36,0.15);color:#fbbf24">OTP</span>';
            bodyHTML = renderEncrypt(data.data);
            break;
        case 'decrypt':
            const match = data.data.matches_original;
            badge = match
                ? '<span class="step-badge" style="background:rgba(52,211,153,0.15);color:#34d399">✅ OK</span>'
                : '<span class="step-badge" style="background:rgba(244,63,94,0.15);color:#f43f5e">❌ CORRUPTED</span>';
            bodyHTML = renderDecrypt(data.data);
            break;
        default:
            bodyHTML = `<div class="step-description">${data.description}</div>`;
    }

    card.innerHTML = `
        <div class="qkd-step-header" onclick="toggleStepBody(this)">
            <span class="step-num">${stepNum}</span>
            <span class="step-title">${data.title}</span>
            <div class="step-header-right">
                ${badge}
                <span class="step-chevron">▶</span>
            </div>
        </div>
        <div class="qkd-step-body">${bodyHTML}</div>
    `;

    return card;
}

function getStepNumber(step) {
    const order = {
        'preparation': '1', 'channel': '2', 'measurement': '3',
        'sifting': '4', 'qber': '5', 'key': '6',
        'encrypt': '7', 'decrypt': '8'
    };
    return order[step] || '?';
}

function toggleStepBody(header) {
    const body = header.nextElementSibling;
    const chevron = header.querySelector('.step-chevron');
    const isOpen = body.classList.contains('open');
    if (isOpen) {
        body.classList.remove('open');
        chevron.classList.remove('open');
    } else {
        body.classList.add('open');
        chevron.classList.add('open');
    }
}

// ── Step Renderers ───────────────────────────────────────────────────────────

function basisClass(basis) { return `basis-${basis.toLowerCase()}`; }
function bitClass(bit) { return `bit-${bit}`; }

function renderPreparation(data) {
    let rows = data.qubits.map(q => `
        <tr>
            <td>${q.index}</td>
            <td class="${basisClass(q.basis)}">${q.basis} ${q.symbol}</td>
            <td class="${bitClass(q.bit)}">${q.bit}</td>
            <td>${q.state}</td>
        </tr>
    `).join('');
    if (data.total_qubits > data.qubits.length) {
        rows += `<tr><td colspan="4" style="color:var(--text-muted);text-align:center">... ${data.total_qubits - data.qubits.length} more qubits</td></tr>`;
    }
    return `
        <div class="step-description">Encoding ${data.total_qubits} random bits in random bases (Z ⊕, X ⊗, Y ◉)</div>
        <div class="qubit-table-wrapper">
            <table class="qubit-table">
                <thead><tr><th>#</th><th>Basis</th><th>Bit</th><th>State</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderEveChannel(data) {
    if (!data.eve_data) return '<div class="eve-warning">Eve is intercepting!</div>';
    let rows = data.eve_data.qubits.map(q => `
        <tr class="${q.match ? 'match' : 'mismatch'}">
            <td>${q.index}</td>
            <td class="${basisClass(q.alice_basis)}">${q.alice_basis}</td>
            <td class="${basisClass(q.eve_basis)}">${q.eve_basis}</td>
            <td>${q.eve_bit}</td>
            <td>${q.match ? '✓' : '✗'}</td>
        </tr>
    `).join('');
    return `
        <div class="eve-warning">🕵️ Eve intercepts, measures, and re-prepares each qubit!</div>
        <div class="qubit-table-wrapper">
            <table class="qubit-table">
                <thead><tr><th>#</th><th>Alice</th><th>Eve</th><th>Bit</th><th>Match</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderMeasurement(data) {
    let rows = data.qubits.map(q => `
        <tr>
            <td>${q.index}</td>
            <td class="${basisClass(q.basis)}">${q.basis} ${q.symbol}</td>
            <td class="${bitClass(q.result)}">${q.result}</td>
        </tr>
    `).join('');
    return `
        <div class="step-description">Bob measures each received qubit in a randomly chosen basis</div>
        <div class="qubit-table-wrapper">
            <table class="qubit-table">
                <thead><tr><th>#</th><th>Basis</th><th>Result</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderSifting(data) {
    let rows = data.data.qubits.map(q => `
        <tr class="${q.match ? 'match' : 'mismatch'}">
            <td>${q.index}</td>
            <td class="${basisClass(q.alice_basis)}">${q.alice_basis}</td>
            <td class="${basisClass(q.bob_basis)}">${q.bob_basis}</td>
            <td>${q.match ? '✓' : '✗'}</td>
            ${q.match ? `<td class="${bitClass(q.alice_bit)}">${q.alice_bit}</td>` : '<td>—</td>'}
        </tr>
    `).join('');
    return `
        <div class="step-description">${data.description}</div>
        <div class="metrics-bar">
            <div class="metric"><div class="metric-value">${data.data.total}</div><div class="metric-label">Total</div></div>
            <div class="metric"><div class="metric-value safe">${data.data.sifted}</div><div class="metric-label">Sifted</div></div>
            <div class="metric"><div class="metric-value">${(data.data.rate * 100).toFixed(1)}%</div><div class="metric-label">Rate</div></div>
        </div>
        <div class="qubit-table-wrapper">
            <table class="qubit-table">
                <thead><tr><th>#</th><th>Alice</th><th>Bob</th><th>Match</th><th>Bit</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderQBER(data) {
    const isOk = !data.eve_detected;
    return `
        <div class="step-description">Compared ${data.sample_size} sample bits to estimate error rate</div>
        <div class="metrics-bar">
            <div class="metric"><div class="metric-value ${isOk ? 'safe' : 'danger'}">${data.qber_percent}%</div><div class="metric-label">QBER</div></div>
            <div class="metric"><div class="metric-value">${data.sample_size}</div><div class="metric-label">Sampled</div></div>
            <div class="metric"><div class="metric-value ${data.errors > 0 ? 'danger' : 'safe'}">${data.errors}</div><div class="metric-label">Errors</div></div>
            <div class="metric"><div class="metric-value">${(data.threshold * 100).toFixed(1)}%</div><div class="metric-label">Threshold</div></div>
        </div>
        ${data.eve_detected ? '<div class="eve-warning">⚠️ QBER exceeds detection threshold — eavesdropping suspected!</div>' : ''}
    `;
}

function renderKey(data) {
    return `
        <div class="step-description">Generated ${data.key_length}-bit shared secret key</div>
        <div class="key-display ${data.secure ? '' : 'compromised'}">${data.key_preview}</div>
    `;
}

function renderEncrypt(data) {
    return `
        <div class="step-description">Encrypting with One-Time Pad (XOR)</div>
        <div style="margin-top:0.5rem;">
            <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:2px;">Plaintext:</div>
            <div class="key-display" style="color:var(--text-primary)">"${escapeHtml(data.original)}"</div>
        </div>
        <div style="margin-top:0.4rem;">
            <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:2px;">Ciphertext (hex):</div>
            <div class="encrypted-display">${data.encrypted_hex}</div>
        </div>
    `;
}

function renderDecrypt(data) {
    return `
        <div style="margin-top:0.25rem;">
            <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:2px;">Decrypted message:</div>
            <div class="key-display ${data.matches_original ? '' : 'compromised'}">"${escapeHtml(data.decrypted)}"</div>
        </div>
        ${data.matches_original
            ? '<div style="margin-top:0.5rem;color:var(--accent-green);font-size:0.8rem;">✅ Message received correctly!</div>'
            : '<div class="eve-warning">❌ Message corrupted by eavesdropping!</div>'
        }
    `;
}

// ── Chat Messages ────────────────────────────────────────────────────────────

function handleChatMessage(data) {
    const isSent = data.sender === myRole;
    const container = document.getElementById('chat-messages');

    const welcome = container.querySelector('.welcome-msg');
    if (welcome) welcome.remove();

    const group = document.createElement('div');
    group.className = `msg-group ${isSent ? 'sent' : 'received'}`;

    const senderLabel = isSent ? 'You' : data.sender;
    const qberSafe = data.qber < 0.167;

    group.innerHTML = `
        <div class="msg-sender">${senderLabel}</div>
        <div class="msg-bubble">${escapeHtml(data.success ? (isSent ? data.message : data.decrypted) : '⚠️ Decryption failed')}</div>
        <div class="msg-meta">
            <span class="qber-badge ${qberSafe ? 'safe' : 'warning'}">QBER: ${(data.qber * 100).toFixed(1)}%</span>
            <span>🔑 ${data.key_length} bits</span>
            <span>📡 ${data.n_qubits} qubits</span>
            ${data.eve_detected ? '<span style="color:var(--accent-red)">⚠️ Eve!</span>' : ''}
        </div>
    `;

    container.appendChild(group);
    container.scrollTop = container.scrollHeight;

    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('message-input').focus();
}

function addSystemMessage(text) {
    const container = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.style.cssText = 'text-align:center;padding:0.5rem;color:var(--text-muted);font-size:0.78rem;';
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Start ────────────────────────────────────────────────────────────────────

init();
