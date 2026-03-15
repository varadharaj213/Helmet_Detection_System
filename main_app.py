import streamlit as st
import subprocess
import os
import signal
import psutil
import time
from datetime import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HelmetGuard — Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0a0b0f;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0e0f14 !important;
    border-right: 1px solid #1e2030 !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0d1117 0%, #111827 50%, #0f1923 100%);
    border: 1px solid #1e2a3a;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(0,200,150,0.07) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 200px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #f0f4f8;
    letter-spacing: -0.5px;
    margin: 0 0 0.4rem 0;
    line-height: 1.1;
}
.hero-title span {
    color: #00c896;
}
.hero-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #4a5568;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 1rem 0;
}
.hero-desc {
    font-size: 0.95rem;
    color: #8892a4;
    max-width: 560px;
    line-height: 1.6;
    margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(0,200,150,0.1);
    border: 1px solid rgba(0,200,150,0.25);
    color: #00c896;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 1rem;
}

/* ── Section Headings ── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #3a4558;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin: 0 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1a1f2e;
}

/* ── Action Cards ── */
.action-card {
    background: #111520;
    border: 1px solid #1e2538;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, background 0.2s;
    position: relative;
    overflow: hidden;
}
.action-card:hover {
    border-color: #2a3555;
    background: #131825;
}
.action-card-icon {
    font-size: 1.5rem;
    margin-bottom: 0.75rem;
    display: block;
}
.action-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: #ccd6f6;
    margin: 0 0 0.3rem 0;
}
.action-card-desc {
    font-size: 0.82rem;
    color: #4a5568;
    line-height: 1.5;
    margin: 0;
}
.card-accent-green { border-left: 3px solid #00c896; }
.card-accent-blue  { border-left: 3px solid #3b82f6; }
.card-accent-amber { border-left: 3px solid #f59e0b; }
.card-accent-purple { border-left: 3px solid #8b5cf6; }
.card-accent-rose  { border-left: 3px solid #f43f5e; }

/* ── Status Pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.05em;
}
.status-running {
    background: rgba(0,200,150,0.1);
    border: 1px solid rgba(0,200,150,0.3);
    color: #00c896;
}
.status-idle {
    background: rgba(74,85,104,0.15);
    border: 1px solid rgba(74,85,104,0.3);
    color: #4a5568;
}
.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: currentColor;
}
.status-dot.pulse {
    animation: pulse-dot 1.5s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ── Metric Cards ── */
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 1.5rem;
}
.metric-card {
    flex: 1;
    background: #0e1018;
    border: 1px solid #1a2030;
    border-radius: 12px;
    padding: 1rem 1.25rem;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #3a4558;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1;
}
.metric-value.green { color: #00c896; }
.metric-value.blue  { color: #3b82f6; }
.metric-value.amber { color: #f59e0b; }

/* ── Buttons ── */
.stButton > button {
    background: #111520 !important;
    border: 1px solid #1e2538 !important;
    color: #8892a4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #1a2035 !important;
    border-color: #2a3555 !important;
    color: #c9d5f0 !important;
}
.stButton > button:disabled {
    opacity: 0.4 !important;
    cursor: not-allowed !important;
}

/* ── Primary Button ── */
div[data-testid="stButton"].primary-btn > button {
    background: #00c896 !important;
    border-color: #00c896 !important;
    color: #001a12 !important;
    font-weight: 600 !important;
}
div[data-testid="stButton"].primary-btn > button:hover {
    background: #00b085 !important;
    border-color: #00b085 !important;
}

/* ── Text Areas ── */
.stTextArea textarea {
    background: #0a0c12 !important;
    border: 1px solid #1e2538 !important;
    color: #8892a4 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    border-radius: 10px !important;
}

/* ── Alerts ── */
.stSuccess > div {
    background: rgba(0,200,150,0.08) !important;
    border: 1px solid rgba(0,200,150,0.2) !important;
    color: #00c896 !important;
    border-radius: 10px !important;
}
.stWarning > div {
    background: rgba(245,158,11,0.08) !important;
    border: 1px solid rgba(245,158,11,0.2) !important;
    color: #f59e0b !important;
    border-radius: 10px !important;
}
.stError > div {
    background: rgba(244,63,94,0.08) !important;
    border: 1px solid rgba(244,63,94,0.2) !important;
    color: #f43f5e !important;
    border-radius: 10px !important;
}

/* ── Sidebar Titles ── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0.5rem 1.5rem 0.5rem;
    border-bottom: 1px solid #1a1f2e;
    margin-bottom: 1.5rem;
}
.sidebar-logo-icon {
    width: 36px; height: 36px;
    background: #00c896;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}
.sidebar-logo-text {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #ccd6f6;
    line-height: 1.2;
}
.sidebar-logo-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #3a4558;
    letter-spacing: 0.1em;
}

/* ── Sidebar Process Items ── */
.process-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0.75rem;
    background: rgba(0,200,150,0.05);
    border: 1px solid rgba(0,200,150,0.15);
    border-radius: 8px;
    margin-bottom: 0.5rem;
}
.process-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #00c896;
}

/* ── Divider ── */
.styled-divider {
    border: none;
    border-top: 1px solid #1a1f2e;
    margin: 1.5rem 0;
}

/* ── Image Grid ── */
.stImage {
    border-radius: 10px !important;
    overflow: hidden;
}
.stImage > div {
    border-radius: 10px !important;
}

/* ── Columns gap ── */
[data-testid="column"] { padding: 0 0.4rem !important; }

/* ── Subheader override ── */
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: #ccd6f6 !important;
}

/* ── Process History Items ── */
.history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    background: #0e1018;
    border: 1px solid #1a2030;
    border-radius: 8px;
    margin-bottom: 6px;
    transition: border-color 0.2s;
}
.history-item:hover {
    border-color: #2a3555;
}
.history-time {
    color: #3a4558;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    min-width: 60px;
}
.history-script {
    color: #8892a4;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    flex: 1;
}
.history-status {
    color: #00c896;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
}
.history-status.stopped {
    color: #f43f5e;
}

/* ── Toggle Switch ── */
.stToggle > div {
    gap: 8px !important;
}
.stToggle label {
    font-family: 'DM Sans', sans-serif !important;
    color: #8892a4 !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = r"D:\Helemtworkingproject\Helmet-Detection-System"
IMAGES_DIR = os.path.join(SCRIPT_DIR, "number_plates")

# ─── Session State ─────────────────────────────────────────────────────────────
if 'processes' not in st.session_state:
    st.session_state.processes = {}
if 'process_status' not in st.session_state:
    st.session_state.process_status = {}
if 'show_plates' not in st.session_state:
    st.session_state.show_plates = False
if 'process_history' not in st.session_state:
    st.session_state.process_history = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# ─── Helpers ───────────────────────────────────────────────────────────────────
def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

def run_script(script_name):
    try:
        script_path = os.path.join(SCRIPT_DIR, script_name)
        process = subprocess.Popen(
            ["python", script_path],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        st.session_state.processes[script_name] = process
        st.session_state.process_status[script_name] = "running"

        output_placeholder = st.empty()
        stop_placeholder = st.empty()

        if stop_placeholder.button(f"⏹  Stop {script_name}", key=f"stop_{script_name}"):
            kill_process_tree(process.pid)
            st.session_state.process_status[script_name] = "stopped"
            st.rerun()

        output_text = ""
        while process.poll() is None:
            stdout_line = process.stdout.readline()
            if stdout_line:
                output_text += stdout_line
                output_placeholder.text_area(f"Console — {script_name}", output_text, height=240)
            stderr_line = process.stderr.readline()
            if stderr_line:
                output_text += stderr_line
                output_placeholder.text_area(f"Console — {script_name}", output_text, height=240)
            if st.session_state.process_status.get(script_name) == "stopped":
                kill_process_tree(process.pid)
                break
            time.sleep(0.1)

        stdout, stderr = process.communicate()
        if stdout:
            output_text += stdout
        if stderr:
            output_text += stderr

        if st.session_state.process_status.get(script_name) == "stopped":
            st.warning(f"{script_name} was stopped.")
            status = "stopped"
        else:
            output_placeholder.text_area(f"Console — {script_name}", output_text, height=240)
            st.success(f"✓  {script_name} completed successfully.")
            status = "completed"

        # Add to history
        st.session_state.process_history.append({
            'script': script_name,
            'time': datetime.now().strftime("%H:%M:%S"),
            'date': datetime.now().strftime("%Y-%m-%d"),
            'status': status
        })
        # Keep only last 20 entries
        if len(st.session_state.process_history) > 20:
            st.session_state.process_history = st.session_state.process_history[-20:]

        del st.session_state.processes[script_name]
        del st.session_state.process_status[script_name]

    except Exception as e:
        st.error(f"Error running {script_name}: {str(e)}")
        if script_name in st.session_state.processes:
            del st.session_state.processes[script_name]
        if script_name in st.session_state.process_status:
            del st.session_state.process_status[script_name]

def stop_process(script_name):
    if script_name in st.session_state.processes:
        process = st.session_state.processes[script_name]
        kill_process_tree(process.pid)
        st.session_state.process_status[script_name] = "stopped"
        
        # Add to history as stopped
        st.session_state.process_history.append({
            'script': script_name,
            'time': datetime.now().strftime("%H:%M:%S"),
            'date': datetime.now().strftime("%Y-%m-%d"),
            'status': 'stopped'
        })
        if len(st.session_state.process_history) > 20:
            st.session_state.process_history = st.session_state.process_history[-20:]
            
        st.success(f"Stopped {script_name}")
        st.rerun()

def kill_all_processes():
    for script_name in list(st.session_state.processes.keys()):
        stop_process(script_name)

def count_plates():
    if os.path.exists(IMAGES_DIR):
        return len([f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    return 0

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🛡️</div>
        <div>
            <div class="sidebar-logo-text">HelmetGuard</div>
            <div class="sidebar-logo-sub">DETECTION SYSTEM v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # System status
    st.markdown('<p class="section-label">System Status</p>', unsafe_allow_html=True)

    running_count = len(st.session_state.processes)
    if running_count > 0:
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
            <span class="status-pill status-running">
                <span class="status-dot pulse"></span>
                {running_count} PROCESS{'ES' if running_count > 1 else ''} RUNNING
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-bottom:1rem;">
            <span class="status-pill status-idle">
                <span class="status-dot"></span>
                SYSTEM IDLE
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Running processes
    if st.session_state.processes:
        st.markdown('<p class="section-label" style="margin-top:1rem;">Active Processes</p>', unsafe_allow_html=True)
        for script_name in list(st.session_state.processes.keys()):
            col_name, col_btn = st.columns([3, 1])
            with col_name:
                st.markdown(f'<div class="process-name">◉ {script_name}</div>', unsafe_allow_html=True)
            with col_btn:
                if st.button("✕", key=f"sidebar_stop_{script_name}"):
                    stop_process(script_name)

    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

    # Stats
    st.markdown('<p class="section-label">Quick Stats</p>', unsafe_allow_html=True)
    plates_found = count_plates()

    st.markdown(f"""
    <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="metric-card">
            <div class="metric-label">Plates Captured</div>
            <div class="metric-value {'green' if plates_found > 0 else ''}">{plates_found}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Active Jobs</div>
            <div class="metric-value {'amber' if running_count > 0 else ''}">{running_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

    # Refresh button
    col_refresh, col_auto = st.columns([1, 1])
    with col_refresh:
        if st.button("↻  Refresh", key="refresh", use_container_width=True):
            st.rerun()
    with col_auto:
        auto_refresh = st.toggle("🔄 Auto", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
        st.session_state.auto_refresh = auto_refresh

    # Process Manager Section
    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Process Manager</p>', unsafe_allow_html=True)

    # Kill all processes button
    if st.session_state.processes:
        if st.button("🛑  Kill All Processes", key="kill_all", use_container_width=True):
            kill_all_processes()
            st.success("All processes terminated")
            time.sleep(1)
            st.rerun()
    else:
        st.button("🛑  Kill All Processes", key="kill_all_disabled", disabled=True, use_container_width=True)

    # Clear history button
    if st.session_state.process_history:
        if st.button("🗑️  Clear History", key="clear_history", use_container_width=True):
            st.session_state.process_history = []
            st.rerun()

    # Auto-refresh logic
    if st.session_state.auto_refresh:
        st.markdown("""
        <div style="font-family:'DM Mono',monospace; font-size:0.65rem; color:#3a4558; text-align:center; margin:10px 0;">
            Auto-refreshing every 3 seconds...
        </div>
        """, unsafe_allow_html=True)
        time.sleep(3)
        st.rerun()

    st.markdown("""
                <br>
                <br>
                <br>
                <br>
                <br>
                <br>
    <div style="position:absolute; bottom:1.5rem; left:1rem; right:1rem;">
        <div style="font-family:'DM Mono',monospace; font-size:0.62rem; color:#2a3040; text-align:center; line-height:1.8;">
            HELMET DETECTION SYSTEM<br>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Main Content ───────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-banner">
    <span class="hero-badge">◉ AI-POWERED SAFETY ENFORCEMENT</span>
    <h1 class="hero-title">Helmet<span>Guard</span></h1>
    <p class="hero-subtitle">Intelligent Detection & Compliance Management Platform</p>
    <p class="hero-desc">
        Automated helmet violation detection using computer vision.
        Identify defaulters, extract number plates, and cross-reference
        student records in real time.
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Action Grid ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Detection Operations</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="action-card card-accent-green">
        <span class="action-card-icon">🎞️</span>
        <p class="action-card-title">Process Video Feed</p>
        <p class="action-card-desc">Analyze pre-recorded footage for helmet violations using YOLOv8 detection pipeline.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(
        "▶  Run Video Processing",
        key="btn_main",
        disabled="main.py" in st.session_state.processes
    ):
        run_script("main.py")

with col2:
    st.markdown("""
    <div class="action-card card-accent-blue">
        <span class="action-card-icon">📷</span>
        <p class="action-card-title">Live Camera Detection</p>
        <p class="action-card-desc">Stream from webcam and detect helmet compliance in real time with instant alerts.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(
        "▶  Start Live Camera",
        key="btn_webcam",
        disabled="webcam_main.py" in st.session_state.processes
    ):
        run_script("webcam_main.py")

st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

# ─── Post-Processing ────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Post-Processing Pipeline</p>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="action-card card-accent-amber">
        <span class="action-card-icon">🔍</span>
        <p class="action-card-title">Extract Defaulter Plates</p>
        <p class="action-card-desc">Run OCR pipeline to extract and log vehicle number plates from flagged frames.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(
        "▶  Extract Number Plates",
        key="btn_extract",
        disabled="extracting.py" in st.session_state.processes
    ):
        run_script("extracting.py")

with col4:
    st.markdown("""
    <div class="action-card card-accent-purple">
        <span class="action-card-icon">🗂️</span>
        <p class="action-card-title">Match Student Records</p>
        <p class="action-card-desc">Cross-reference detected plates against student database and save violation report.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(
        "▶  Match & Save Records",
        key="btn_plate",
        disabled="platefinder.py" in st.session_state.processes
    ):
        run_script("platefinder.py")

st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

# ─── Process History ───────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Process History</p>', unsafe_allow_html=True)

if st.session_state.process_history:
    for hist in reversed(st.session_state.process_history[-5:]):  # Show last 5, newest first
        status_class = "history-status stopped" if hist['status'] == 'stopped' else "history-status"
        status_icon = "⏹️" if hist['status'] == 'stopped' else "✓"
        st.markdown(f"""
        <div class="history-item">
            <span class="history-time">{hist['time']}</span>
            <span class="history-script">{hist['script']}</span>
            <span class="{status_class}">{status_icon} {hist['status'].upper()}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:20px; background:#0e1018; border:1px solid #1a2030; border-radius:8px;">
        <span style="font-family:'DM Mono',monospace; font-size:0.75rem; color:#3a4558;">No process history available</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

# ─── Defaulters Gallery ─────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Evidence Gallery</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 5])

with col_left:
    show_btn = st.button("🖼️  Show Plates", key="btn_show_plates", use_container_width=True)
    if show_btn:
        st.session_state.show_plates = not st.session_state.show_plates

if st.session_state.show_plates:
    if os.path.exists(IMAGES_DIR):
        image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if image_files:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem;">
                <span style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700; color:#ccd6f6;">
                    Captured Number Plates
                </span>
                <span style="background:rgba(0,200,150,0.1); border:1px solid rgba(0,200,150,0.25);
                             color:#00c896; font-family:'DM Mono',monospace; font-size:0.68rem;
                             padding:3px 10px; border-radius:20px;">
                    {len(image_files)} RECORDS
                </span>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(4)
            for idx, image_file in enumerate(image_files):
                with cols[idx % 4]:
                    image_path = os.path.join(IMAGES_DIR, image_file)
                    st.image(image_path, use_container_width=True)
                    st.markdown(f"""
                    <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                color:#3a4558; text-align:center; margin-top:4px;
                                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {image_file}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No captured plates found in the output directory.")
    else:
        st.error(f"Output folder not found: `{IMAGES_DIR}`")