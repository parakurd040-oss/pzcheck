import os
import re

# ============================================================
# 1. Fix dashboard.html — Settings link
# ============================================================
dash_path = "templates/dashboard.html"
if os.path.exists(dash_path):
    with open(dash_path, "r", encoding="utf-8") as f:
        dash = f.read()

# Replace any Settings menu item with href="#" to href="/settings"
    dash = re.sub(
        r'<a class="menu-item" href="#">(\s*<span class="icon">[^<]*</span>\s*Settings\s*)</a>',
        r'<a class="menu-item" href="/settings">\1</a>',
        dash
    )
    # Also handle single-line variant
    dash = dash.replace(
        '<a class="menu-item" href="#"><span class="icon">⚙</span> Settings</a>',
        '<a class="menu-item" href="/settings"><span class="icon">⚙</span> Settings</a>'
    )
    dash = dash.replace(
        '<a class="menu-item" href="#"><span class="icon">&#9881;</span> Settings</a>',
        '<a class="menu-item" href="/settings"><span class="icon">&#9881;</span> Settings</a>'
    )

with open(dash_path, "w", encoding="utf-8") as f:
        f.write(dash)
    print("Fixed dashboard.html Settings link")

# ============================================================
# 2. Write correct settings.html (HTML only, no Python wrapper)
# ============================================================
settings_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - PZ Checker</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #000000;
            --sidebar-bg: rgba(0, 10, 5, 0.85);
            --card-bg: rgba(0, 20, 10, 0.6);
            --card-bg-2: rgba(0, 30, 15, 0.7);
            --border: rgba(0, 255, 100, 0.15);
            --border-2: rgba(0, 255, 100, 0.3);
            --text: #d0ffe0;
            --text-dim: #4a8a5a;
            --text-dimmer: #2a4a35;
            --green: #00ff66;
            --green-glow: rgba(0, 255, 100, 0.4);
            --green-soft: rgba(0, 255, 100, 0.08);
            --red: #ff3355;
            --red-glow: rgba(255, 51, 85, 0.4);
            --yellow: #ffcc00;
            --cyan: #00e5ff;
        }
        html, body { height: 100%; overflow-x: hidden; }
        body {
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            font-size: 13px;
            position: relative;
        }
        #matrix-canvas {
            position: fixed;
            inset: 0;
            z-index: -1;
            opacity: 0.55;
        }
        .scanlines {
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background: repeating-linear-gradient(0deg, rgba(0,0,0,0.15) 0px, rgba(0,0,0,0.15) 1px, transparent 1px, transparent 3px);
            mix-blend-mode: overlay;
        }
        .vignette {
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background: radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.85) 100%);
        }
        .top-glow {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 300px;
            z-index: 0;
            pointer-events: none;
            background: radial-gradient(ellipse at top, rgba(0,255,100,0.15), transparent 70%);
        }
        .sidebar {
            width: 240px;
            background: var(--sidebar-bg);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--border);
            padding: 20px 0;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            left: 0; top: 0;
            z-index: 100;
        }
        .sidebar .logo {
            padding: 0 20px 24px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1rem;
            font-weight: 800;
        }
        .sidebar .logo .logo-icon {
            width: 30px; height: 30px;
            border-radius: 6px;
            background: linear-gradient(135deg, var(--green), #00aa44);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 0.95rem;
            font-weight: 800;
            box-shadow: 0 0 20px var(--green-glow);
        }
        .sidebar .logo .logo-text { color: var(--green); text-shadow: 0 0 10px var(--green-glow); }
        .sidebar .logo .logo-badge {
            background: var(--green);
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 800;
        }
        .sidebar .menu-label {
            padding: 0 20px 8px;
            font-size: 0.65rem;
            color: var(--text-dimmer);
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 700;
        }
        .sidebar .menu {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 0 12px;
        }
        .sidebar .menu-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 6px;
            color: var(--text-dim);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.15s;
            position: relative;
        }
        .sidebar .menu-item:hover { background: var(--green-soft); color: var(--green); }
        .sidebar .menu-item.active {
            background: var(--green-soft);
            color: var(--green);
            font-weight: 700;
            box-shadow: inset 0 0 0 1px var(--border-2);
        }
        .sidebar .menu-item.active::before {
            content: '';
            position: absolute;
            left: 0; top: 50%;
            transform: translateY(-50%);
            width: 3px; height: 60%;
            background: var(--green);
            border-radius: 0 3px 3px 0;
            box-shadow: 0 0 10px var(--green);
        }
        .sidebar .menu-item .icon {
            width: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.95rem;
        }
        .sidebar .version {
            margin-top: auto;
            padding: 20px;
            font-size: 0.7rem;
            color: var(--text-dimmer);
        }
        .sidebar .version::before { content: '> '; color: var(--green); }
        .main {
            margin-left: 240px;
            flex: 1;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 1;
        }
        .topbar {
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            background: rgba(0, 10, 5, 0.7);
            backdrop-filter: blur(20px);
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .topbar .page-title h1 {
            font-size: 1rem;
            font-weight: 700;
            color: var(--green);
            text-shadow: 0 0 10px var(--green-glow);
        }
        .topbar .page-title h1::before { content: '$ '; color: var(--text-dim); }
        .topbar .page-title p {
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 2px;
        }
        .topbar .topbar-right { display: flex; align-items: center; gap: 10px; }
        .topbar .pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 6px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            font-size: 0.75rem;
            color: var(--text);
            font-weight: 500;
        }
        .topbar .pill .dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 8px var(--green);
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .topbar .icon-btn {
            width: 36px; height: 36px;
            border-radius: 6px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--text-dim);
            position: relative;
            text-decoration: none;
        }
        .topbar .icon-btn:hover { background: var(--green-soft); color: var(--green); }
        .topbar .icon-btn .badge {
            position: absolute;
            top: -4px; right: -4px;
            background: var(--red);
            color: #fff;
            font-size: 0.6rem;
            font-weight: 700;
            padding: 1px 5px;
            border-radius: 8px;
            min-width: 16px;
            text-align: center;
        }
        .topbar .user {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px 6px 6px;
            border-radius: 6px;
            background: var(--card-bg);
            border: 1px solid var(--border);
        }
        .topbar .user .avatar {
            width: 26px; height: 26px;
            border-radius: 4px;
            background: linear-gradient(135deg, var(--green), #00aa44);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 800;
            color: #000;
        }
        .topbar .user .name {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text);
        }
        .content {
            padding: 28px 32px;
            flex: 1;
            max-width: 1200px;
            width: 100%;
        }
        .settings-layout {
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 32px;
            align-items: start;
        }
        .settings-nav {
            display: flex;
            flex-direction: column;
            gap: 4px;
            position: sticky;
            top: 100px;
        }
        .settings-nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            border-radius: 6px;
            color: var(--text-dim);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.15s;
            border: 1px solid transparent;
        }
        .settings-nav-item:hover { background: var(--green-soft); color: var(--green); }
        .settings-nav-item.active {
            background: var(--green-soft);
            color: var(--green);
            font-weight: 700;
            border-color: var(--border-2);
        }
        .settings-panels {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .panel {
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }
        .panel::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--green), transparent);
            opacity: 0.4;
        }
        .panel-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--green);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 0 8px var(--green-glow);
        }
        .panel-body { padding: 20px; }
        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
        }
        .info-row:last-child { border-bottom: none; }
        .info-row .info-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text);
        }
        .info-row .info-sub {
            font-size: 0.7rem;
            color: var(--text-dim);
            margin-top: 2px;
        }
        .info-row .info-value {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--green);
            padding: 4px 12px;
            background: var(--green-soft);
            border: 1px solid var(--border-2);
            border-radius: 4px;
        }
        .info-row .info-value.dim {
            color: var(--text-dim);
            background: transparent;
            border: none;
            padding: 0;
            font-weight: 500;
        }
        .warning-banner {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            background: rgba(255, 204, 0, 0.06);
            border: 1px solid rgba(255, 204, 0, 0.3);
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 0.75rem;
            color: var(--yellow);
        }
        .warning-banner strong { color: #ffdd44; font-weight: 700; }
        .form-group { margin-bottom: 18px; }
        .form-group label {
            display: block;
            font-size: 0.7rem;
            color: var(--text-dim);
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .input-wrapper { position: relative; }
        .input-wrapper .input-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            font-size: 0.85rem;
            pointer-events: none;
        }
        .input-wrapper input {
            width: 100%;
            padding: 12px 44px 12px 42px;
            background: var(--card-bg-2);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            outline: none;
            transition: all 0.15s;
        }
        .input-wrapper input:focus {
            border-color: var(--green);
            box-shadow: 0 0 0 3px rgba(0, 255, 100, 0.1);
        }
        .input-wrapper input::placeholder { color: var(--text-dimmer); }
        .input-wrapper .toggle-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            padding: 4px 6px;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        .input-wrapper .toggle-btn:hover { color: var(--green); }
        .btn-submit {
            padding: 12px 24px;
            border-radius: 6px;
            border: 1px solid var(--green);
            background: linear-gradient(135deg, rgba(0, 255, 100, 0.15), rgba(0, 200, 80, 0.1));
            color: var(--green);
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            box-shadow: 0 0 30px rgba(0, 255, 100, 0.2);
        }
        .btn-submit:hover {
            box-shadow: 0 0 50px rgba(0, 255, 100, 0.4);
            transform: translateY(-1px);
        }
        .flash-messages { margin-bottom: 20px; }
        .flash {
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 0.75rem;
            margin-bottom: 10px;
        }
        .flash.error { background: rgba(255, 51, 85, 0.1); border: 1px solid rgba(255, 51, 85, 0.3); color: var(--red); }
        .flash.success { background: rgba(0, 255, 100, 0.1); border: 1px solid rgba(0, 255, 100, 0.3); color: var(--green); }
        .flash.info { background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.3); color: var(--cyan); }
        .placeholder-panel {
            padding: 60px 20px;
            text-align: center;
            color: var(--text-dimmer);
            font-size: 0.8rem;
        }
        .placeholder-panel .ph-icon {
            font-size: 2.5rem;
            opacity: 0.3;
            margin-bottom: 12px;
        }
        @media (max-width: 900px) {
            .sidebar { transform: translateX(-100%); }
            .main { margin-left: 0; }
            .settings-layout { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <canvas id="matrix-canvas"></canvas>
    <div class="scanlines"></div>
    <div class="vignette"></div>
    <div class="top-glow"></div>

<aside class="sidebar">
        <div class="logo">
            <div class="logo-icon">&#10003;</div>
            <span class="logo-text">PZ</span>
            <span class="logo-badge">HUB</span>
        </div>
        <div class="menu-label">// Menu</div>
        <nav class="menu">
            <a class="menu-item" href="/dashboard"><span class="icon">&#9638;</span> Dashboard</a>
            <a class="menu-item" href="#"><span class="icon">&#9889;</span> Live</a>
            <a class="menu-item" href="#"><span class="icon">&#9881;</span> Tools</a>
            <a class="menu-item" href="#"><span class="icon">&#128269;</span> DB Search</a>
            <a class="menu-item" href="#"><span class="icon">&#128214;</span> Tutorials</a>
            <a class="menu-item" href="#"><span class="icon">&#128202;</span> Stats</a>
            <a class="menu-item" href="#"><span class="icon">&#128178;</span> OurPrices</a>
            <a class="menu-item active" href="/settings"><span class="icon">&#9881;</span> Settings</a>
        </nav>
        <div class="version">PZHub v1.0</div>
    </aside>

<div class="main">
        <header class="topbar">
            <div class="page-title">
                <h1>Settings</h1>
                <p>Account, security & preferences</p>
            </div>
            <div class="topbar-right">
                <div class="pill"><span class="dot"></span> Credits: <strong>&#8734;</strong></div>
                <div class="pill">&#11088; No VIP</div>
                <div class="icon-btn">&#128276;<span class="badge">3</span></div>
                <div class="user">
                    <div class="avatar">{{ username[0]|upper }}</div>
                    <span class="name">{{ username }}</span>
                </div>
                <a href="{{ url_for('logout') }}" class="icon-btn" title="Logout">&#9211;</a>
            </div>
        </header>

<main class="content">
            {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
            <div class="flash-messages">
                {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
            {% endif %}
            {% endwith %}

<div class="settings-layout">
                <nav class="settings-nav">
                    <a class="settings-nav-item {% if active_tab == 'account' %}active{% endif %}" href="/settings?tab=account">
                        <span>&#128100;</span> Account
                    </a>
                    <a class="settings-nav-item {% if active_tab == 'security' %}active{% endif %}" href="/settings?tab=security">
                        <span>&#128274;</span> Security
                    </a>
                    <a class="settings-nav-item {% if active_tab == 'telegram' %}active{% endif %}" href="/settings?tab=telegram">
                        <span>&#9992;</span> Telegram
                    </a>
                    <a class="settings-nav-item {% if active_tab == 'theme' %}active{% endif %}" href="/settings?tab=theme">
                        <span>&#127912;</span> Theme
                    </a>
                    <a class="settings-nav-item {% if active_tab == 'notifications' %}active{% endif %}" href="/settings?tab=notifications">
                        <span>&#128276;</span> Notifications
                    </a>
                </nav>

<div class="settings-panels">
                    {% if active_tab == 'account' %}
                    <div class="panel">
                        <div class="panel-header"><span>&#128100;</span> Profile</div>
                        <div class="panel-body">
                            <div class="info-row">
                                <div>
                                    <div class="info-label">Username</div>
                                    <div class="info-sub">Your unique handle - can't be changed.</div>
                                </div>
                                <div class="info-value">{{ username }}</div>
                            </div>
                            <div class="info-row">
                                <div><div class="info-label">Member since</div></div>
                                <div class="info-value dim">{{ member_since }}</div>
                            </div>
                        </div>
                    </div>

<div class="panel">
                        <div class="panel-header"><span>&#128273;</span> Change Password</div>
                        <div class="panel-body">
                            <div class="warning-banner">
                                <span>&#9888;</span>
                                <div>Passwords can be changed <strong>anytime</strong>. Choose a strong password with at least 6 characters.</div>
                            </div>
                            <form method="POST" action="{{ url_for('change_password') }}">
                                <div class="form-group">
                                    <label for="current_password">Current Password</label>
                                    <div class="input-wrapper">
                                        <span class="input-icon">&#128274;</span>
                                        <input type="password" id="current_password" name="current_password" placeholder="Enter current password" required>
                                        <button type="button" class="toggle-btn" data-target="current_password">&#128065;</button>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="new_password">New Password</label>
                                    <div class="input-wrapper">
                                        <span class="input-icon">&#128274;</span>
                                        <input type="password" id="new_password" name="new_password" placeholder="Enter new password" required>
                                        <button type="button" class="toggle-btn" data-target="new_password">&#128065;</button>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="confirm_password">Confirm New Password</label>
                                    <div class="input-wrapper">
                                        <span class="input-icon">&#128274;</span>
                                        <input type="password" id="confirm_password" name="confirm_password" placeholder="Confirm new password" required>
                                        <button type="button" class="toggle-btn" data-target="confirm_password">&#128065;</button>
                                    </div>
                                </div>
                                <button type="submit" class="btn-submit">Update Password</button>
                            </form>
                        </div>
                    </div>
                    {% elif active_tab == 'security' %}
                    <div class="panel">
                        <div class="panel-header"><span>&#128274;</span> Security</div>
                        <div class="panel-body">
                            <div class="placeholder-panel">
                                <div class="ph-icon">&#128274;</div>
                                <div>// Security settings coming soon</div>
                            </div>
                        </div>
                    </div>
                    {% elif active_tab == 'telegram' %}
                    <div class="panel">
                        <div class="panel-header"><span>&#9992;</span> Telegram</div>
                        <div class="panel-body">
                            <div class="placeholder-panel">
                                <div class="ph-icon">&#9992;</div>
                                <div>// Telegram integration coming soon</div>
                            </div>
                        </div>
                    </div>
                    {% elif active_tab == 'theme' %}
                    <div class="panel">
                        <div class="panel-header"><span>&#127912;</span> Theme</div>
                        <div class="panel-body">
                            <div class="placeholder-panel">
                                <div class="ph-icon">&#127912;</div>
                                <div>// Theme customization coming soon</div>
                            </div>
                        </div>
                    </div>
                    {% elif active_tab == 'notifications' %}
                    <div class="panel">
                        <div class="panel-header"><span>&#128276;</span> Notifications</div>
                        <div class="panel-body">
                            <div class="placeholder-panel">
                                <div class="ph-icon">&#128276;</div>
                                <div>// Notification settings coming soon</div>
                            </div>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </main>
    </div>

<script>
        (function matrixRain() {
            const canvas = document.getElementById('matrix-canvas');
            const ctx = canvas.getContext('2d');
            let width, height, columns, drops;
            const fontSize = 14;
            const chars = '0123456789ABCDEF<>{}[]()/\\\\|=+-*&^%$#@!?';
            function resize() {
                width = canvas.width = window.innerWidth;
                height = canvas.height = window.innerHeight;
                columns = Math.floor(width / fontSize);
                drops = [];
                for (let i = 0; i < columns; i++) drops[i] = Math.random() * -100;
            }
            resize();
            window.addEventListener('resize', resize);
            function draw() {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.06)';
                ctx.fillRect(0, 0, width, height);
                ctx.font = fontSize + 'px JetBrains Mono, monospace';
                ctx.shadowColor = '#00ff66';
                for (let i = 0; i < drops.length; i++) {
                    const text = chars[Math.floor(Math.random() * chars.length)];
                    const x = i * fontSize;
                    const y = drops[i] * fontSize;
                    if (Math.random() > 0.975) {
                        ctx.fillStyle = '#aaffcc';
                        ctx.shadowBlur = 15;
                    } else {
                        ctx.fillStyle = '#00ff66';
                        ctx.shadowBlur = 6;
                    }
                    ctx.fillText(text, x, y);
                    if (y > height && Math.random() > 0.975) drops[i] = 0;
                    drops[i]++;
                }
            }
            setInterval(draw, 50);
        })();

document.querySelectorAll('.toggle-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const target = document.getElementById(btn.dataset.target);
                if (!target) return;
                if (target.type === 'password') {
                    target.type = 'text';
                    btn.textContent = 'HIDE';
                } else {
                    target.type = 'password';
                    btn.textContent = 'SHOW';
                }
            });
        });
    </script>
</body>
</html>
'''

with open("templates/settings.html", "w", encoding="utf-8") as f:
    f.write(settings_html)
print("Wrote correct templates/settings.html")

print()
print("Done. Now:")
print("1. Restart: python app.py")
print("2. Refresh browser with Ctrl+Shift+R")
print("3. Click Settings in the sidebar")