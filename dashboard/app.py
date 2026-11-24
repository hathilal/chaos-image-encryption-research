from pathlib import Path
from datetime import datetime
import hashlib
import io
import json
import sys
import time

import numpy as np
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
EXPERIMENTS = ROOT / "experiments"

for directory in (ARTIFACTS, EXPERIMENTS):
    directory.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))
from fpga_link import transact, PIXELS, DEFAULT_PORT


st.set_page_config(
    page_title="Chaos Encryption | FPGA Research Studio",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- LIGHT PROFESSIONAL THEME ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --ink:#f2eee8; --muted:#aaa3b5; --panel:#191722; --line:#393244;
  --bg:#100f16; --cyan:#c4a6ff; --lime:#d8bd83; --blue:#8e79c9;
}
.stApp { background: radial-gradient(ellipse at 78% 0%, #292238 0%, #121019 48%, #0c0b11 100%); color:var(--ink); font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:rgba(12,11,17,.92); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#171420,#100f16); border-right:1px solid #393244; }
[data-testid="stSidebar"] * { color:#e0d9e8; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:7px 10px; border-radius:8px; }
.block-container { max-width:1540px; padding-top:1.2rem; padding-bottom:4rem; }
.hero {
  position:relative; overflow:hidden; padding:34px 38px; margin:8px 0 24px;
  border:1px solid #4a3e59; border-radius:18px;
  background:linear-gradient(112deg,rgba(39,31,51,.98),rgba(24,21,32,.96) 58%,rgba(54,43,64,.90));
  box-shadow:0 18px 55px rgba(0,0,0,.22);
}
.hero:after { content:""; position:absolute; width:300px;height:300px;right:-90px;top:-155px;border:1px solid rgba(72,215,232,.22);border-radius:50%;box-shadow:0 0 0 28px rgba(72,215,232,.035),0 0 0 58px rgba(72,215,232,.025); }
.eyebrow { color:var(--cyan); letter-spacing:2.8px; font:500 10px 'DM Mono',monospace; }
.hero h1 { color:#f2f7ff; font-size:clamp(27px,3vw,42px); letter-spacing:-1.8px; font-weight:800; margin:10px 0 7px; }
.hero p { color:#a8bdd2; font-size:14px; max-width:760px; margin:0; }
.hero-meta { display:flex; gap:9px; flex-wrap:wrap; margin-top:22px; }
.hero-meta span { border:1px solid #594c68; border-radius:5px; padding:6px 9px; color:#e0d1b2; font:10px 'DM Mono',monospace; letter-spacing:.5px; }
h1,h2,h3,h4,p,label,li { color:var(--ink); }
h2,h3 { letter-spacing:-.5px; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#24202f,#191722); border:1px solid #45394f; padding:15px 17px; border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,.12); }
[data-testid="stMetricLabel"] { color:#93a9bf !important; font:10px 'DM Mono',monospace !important; text-transform:uppercase; letter-spacing:1px; }
[data-testid="stMetricValue"] { color:#eff8ff !important; font-weight:800; }
[data-testid="stMetricDelta"] { color:var(--lime) !important; }
.panel, [data-testid="stVerticalBlockBorderWrapper"] { background:rgba(28,24,36,.86); border:1px solid #3d3449; border-radius:13px; }
div[data-testid="stExpander"] { background:#1b1824; border:1px solid #3d3449; border-radius:11px; }
div[data-testid="stExpander"] summary { color:#dceafa; }
.stButton > button[kind="primary"], .stDownloadButton > button {
  background:linear-gradient(105deg,#a98be2,#d5b879); color:#17121d; border:0;
  border-radius:8px; min-height:46px; font-weight:800; letter-spacing:.2px;
}
.stButton > button[kind="primary"]:hover,.stDownloadButton > button:hover { background:linear-gradient(105deg,#c6aaff,#ead39e); color:#17121d; border:0; }
.stButton > button:not([kind="primary"]) { background:#252130; color:#eee7f2; border:1px solid #51445e; border-radius:8px; }
.stTextInput input,.stNumberInput input,.stSelectbox [data-baseweb="select"],.stTextArea textarea { background:#15131d; color:#f2eee8; border-color:#51445e; }
[data-testid="stFileUploader"] { background:#191722; border:1px dashed #78648b; border-radius:12px; padding:8px; }
[data-testid="stDataFrame"] { border:1px solid #233c53; border-radius:10px; }
.stAlert { border-radius:10px; }
hr { border-color:#393244; }
code, .stCode { font-family:'DM Mono',monospace !important; }
small { color:#8da2bb; }
</style>
""", unsafe_allow_html=True)


# ---------------- ANALYSIS FUNCTIONS ----------------

def image_entropy(data):
    values = np.frombuffer(data, dtype=np.uint8)
    counts = np.bincount(values, minlength=256)
    probabilities = counts[counts > 0] / values.size
    return float(-np.sum(probabilities * np.log2(probabilities)))


def image_correlations(data):
    image = np.frombuffer(data, dtype=np.uint8).reshape(128, 128).astype(float)

    def corr(a, b):
        a = a.ravel()
        b = b.ravel()
        if np.std(a) == 0 or np.std(b) == 0:
            return None
        value = float(np.corrcoef(a, b)[0, 1])
        return value if np.isfinite(value) else None

    return {
        "horizontal": corr(image[:, :-1], image[:, 1:]),
        "vertical": corr(image[:-1, :], image[1:, :]),
        "diagonal": corr(image[:-1, :-1], image[1:, 1:]),
    }


def differential_metrics(cipher_a, cipher_b):
    a = np.frombuffer(cipher_a, dtype=np.uint8).astype(np.int16)
    b = np.frombuffer(cipher_b, dtype=np.uint8).astype(np.int16)

    return {
        "npcr_percent": float(np.mean(a != b) * 100),
        "uaci_percent": float(np.mean(np.abs(a - b)) / 255 * 100),
    }


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def image_from_bytes(data):
    return Image.frombytes("L", (128, 128), data)


# ---------------- PERSISTENT EXPERIMENT ARCHIVE ----------------

def load_experiment_records():
    """Reload saved experiments from disk on every page render."""
    records = []
    for folder in EXPERIMENTS.iterdir():
        metadata_file = folder / "experiment.json"
        if not folder.is_dir() or not metadata_file.is_file():
            continue
        try:
            record = json.loads(metadata_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        records.append((folder, record))
    return sorted(records, key=lambda item: item[0].name, reverse=True)


def record_is_software(folder, record):
    return (
        record.get("implementation") == "Python software"
        or folder.name.startswith("software_")
    )


def record_is_fpga(folder, record):
    timings = record.get("timings") or {}
    return (
        record.get("platform") == "Zybo Z7-10"
        or "encryption" in timings
        or (not record_is_software(folder, record) and "operation" in record)
    )


def record_provenance(record):
    """Legacy records are historical unless they explicitly declare live execution."""
    return (
        "FRESH EXECUTION"
        if record.get("execution_provenance") == "live_execution"
        else "HISTORICAL / RESTORED"
    )


def record_label(item):
    folder, record = item
    kind = "SOFTWARE" if record_is_software(folder, record) else (
        "FPGA" if record_is_fpga(folder, record) else "LEGACY"
    )
    recovery = "RECOVERY PASS" if record.get("exact_recovery") is True else (
        "INCOMPLETE" if record.get("exact_recovery") is None else "RECOVERY FAIL"
    )
    return f"{kind} · {record_provenance(record)} · {recovery} · {folder.name}"


def _artifact_digest(folder, candidates, image=False):
    """Hash raw payload bytes, decoding grayscale PNGs to pixel bytes."""
    for name in candidates:
        path = folder / name
        if not path.is_file():
            continue
        if image:
            with Image.open(path) as source:
                payload = source.convert("L").tobytes()
        else:
            payload = path.read_bytes()
        return sha256(payload), path.name
    return None, None


def verify_record_artifacts(folder, record):
    """Compare available experiment payloads with metadata SHA-256 values."""
    specs = (
        ("input_sha256", ("original.bin", "input.bin"), ("original.png", "input.png")),
        ("ciphertext_sha256", ("ciphertext.bin", "encrypted.bin"), ("ciphertext.png", "encrypt_output.png")),
        ("recovered_sha256", ("recovered.bin", "decrypted.bin"), ("recovered.png",)),
    )
    results = []
    for key, binary_names, image_names in specs:
        expected = record.get(key)
        if not expected:
            results.append((key, "NOT RECORDED", None))
            continue
        actual, filename = _artifact_digest(folder, binary_names, image=False)
        if actual is None:
            actual, filename = _artifact_digest(folder, image_names, image=True)
        if actual is None:
            results.append((key, "MISSING", None))
        elif actual == expected:
            results.append((key, "MATCH", filename))
        else:
            results.append((key, "MISMATCH", filename))
    return results


def get_record_analysis(record):
    analysis = record.get("analysis") or {}
    differential = analysis.get("differential_metrics") or record.get("differential_metrics") or {}
    correlations = analysis.get("neighbor_correlations") or record.get("neighbor_correlations") or {}
    entropy = analysis.get("ciphertext_entropy_bits_per_pixel")
    if entropy is None:
        entropy = record.get("entropy_bits_per_pixel")
    return entropy, differential, correlations


def record_image_path(folder, candidates):
    return next((folder / name for name in candidates if (folder / name).is_file()), None)


def render_record_images(folder):
    image_specs = [
        ("Original input", ["original.png", "input.png"]),
        ("Encrypted ciphertext", ["ciphertext.png", "encrypt_output.png"]),
        ("Recovered output", ["recovered.png"]),
    ]
    columns = st.columns(3)
    for column, (label, names) in zip(columns, image_specs):
        image_path = record_image_path(folder, names)
        with column:
            st.markdown(f"**{label}**")
            if image_path:
                st.image(str(image_path), use_container_width=True)
            else:
                st.caption("Not included in this saved run.")


def render_record_summary(folder, record, show_images=True):
    """Present saved results as a human-readable report, never raw JSON."""
    software = record_is_software(folder, record)
    implementation = "Python software" if software else (
        record.get("platform") or "FPGA / UART"
    )
    entropy, differential, correlations = get_record_analysis(record)

    st.markdown(f"#### {implementation}")
    st.caption(
        f"Run ID: {record.get('run_id', folder.name)}"
        + (f"  ·  {record.get('timestamp')}" if record.get("timestamp") else "")
    )

    provenance = record_provenance(record)
    if provenance == "HISTORICAL / RESTORED":
        st.info(
            "HISTORICAL / RESTORED RESULT — archived evidence is being displayed. "
            "This is not a new execution performed during the current session."
        )
    elif software:
        st.success("FRESH SOFTWARE EXECUTION — generated by the current application run.")
    elif record.get("hardware_transaction_completed") is True:
        st.success("LIVE FPGA UART TRANSACTION — the recorded transaction completed.")
        if not record.get("bitstream_sha256") or not record.get("firmware_identity"):
            st.warning(
                "Hardware identity is not fully attested: firmware identity and/or "
                "programmed bitstream hash were not recorded. This validates the "
                "observed UART transaction, not a specific RTL/bitstream revision."
            )
    else:
        st.warning(
            "FPGA execution provenance is incomplete. Do not interpret this record "
            "as proof of a newly completed physical hardware transaction."
        )

    with st.expander("Artifact integrity and provenance", expanded=False):
        st.write(f"**Execution provenance:** {provenance}")
        st.write(f"**Hardware transaction completed:** {record.get('hardware_transaction_completed', 'Not recorded')}")
        st.write(f"**Firmware identity:** {record.get('firmware_identity', 'Not recorded')}")
        st.write(f"**Bitstream SHA-256:** {record.get('bitstream_sha256', 'Not recorded')}")
        integrity = verify_record_artifacts(folder, record)
        for hash_name, result, filename in integrity:
            suffix = f" · {filename}" if filename else ""
            st.write(f"**{hash_name}:** {result}{suffix}")
        if any(result == "MISMATCH" for _, result, _ in integrity):
            st.error("At least one available artifact does not match its recorded SHA-256.")
        elif any(result == "MISSING" for _, result, _ in integrity):
            st.warning("Some expected artifacts are missing; this record is only partially verifiable.")
        elif any(result == "NOT RECORDED" for _, result, _ in integrity):
            st.caption("One or more hashes were not recorded in the original metadata.")

    c1, c2, c3, c4 = st.columns(4)
    exact = record.get("exact_recovery")
    c1.metric("Exact recovery", "PASS" if exact is True else (
        "FAIL" if exact is False else "Not recorded"
    ))
    c2.metric("Matching pixels", (
        f"{record.get('matching_pixels'):,}"
        if isinstance(record.get("matching_pixels"), int) else "Not recorded"
    ))
    c3.metric("Ciphertext entropy", (
        f"{entropy:.4f} bits/pixel" if isinstance(entropy, (int, float)) else "Not recorded"
    ))
    c4.metric("Input size", (
        f"{record.get('input_bytes'):,} bytes"
        if isinstance(record.get("input_bytes"), int) else "Not recorded"
    ))

    d1, d2, d3 = st.columns(3)
    d1.metric("NPCR", (
        f"{differential['npcr_percent']:.4f}%"
        if isinstance(differential.get("npcr_percent"), (int, float)) else "Not recorded"
    ))
    d2.metric("UACI", (
        f"{differential['uaci_percent']:.4f}%"
        if isinstance(differential.get("uaci_percent"), (int, float)) else "Not recorded"
    ))
    d3.metric("Distinct ciphertext values", (
        str(record["distinct_values"]) if isinstance(record.get("distinct_values"), int)
        else "Not recorded"
    ))

    if show_images:
        render_record_images(folder)

    if correlations:
        valid = {
            name.capitalize(): value
            for name, value in correlations.items()
            if isinstance(value, (int, float))
        }
        if valid:
            st.markdown("**Adjacent-pixel correlation**")
            st.bar_chart({"Correlation": valid})

    timings = record.get("timings") or {}
    timing_rows = []
    if software:
        for key, label in (
            ("encryption_seconds", "Encryption computation"),
            ("decryption_seconds", "Decryption computation"),
            ("total_cipher_seconds", "Total cipher computation"),
        ):
            value = record.get(key)
            if isinstance(value, (int, float)):
                timing_rows.append({"Measurement": label, "Time (s)": value})
    else:
        for operation in ("encryption", "decryption", "differential_test_encryption"):
            values = timings.get(operation)
            if isinstance(values, dict):
                for key, value in values.items():
                    if isinstance(value, (int, float)):
                        timing_rows.append({
                            "Measurement": f"{operation.replace('_', ' ').title()} · {key.replace('_', ' ')}",
                            "Time (s)": value,
                        })
        # Older records may contain a single transaction rather than a full round trip.
        if not timing_rows:
            for key, value in timings.items():
                if isinstance(value, (int, float)):
                    timing_rows.append({
                        "Measurement": key.replace("_", " ").title(),
                        "Time (s)": value,
                    })

    if timing_rows:
        st.markdown("**Recorded timing measurements**")
        st.dataframe(timing_rows, use_container_width=True, hide_index=True)
        if not software:
            st.caption(
                "FPGA timings are host-side UART transaction measurements. "
                "They include communication and are not isolated FPGA core latency."
            )

    if record.get("algorithm"):
        st.caption(f"Software algorithm: {record['algorithm']}")
    if record.get("parameters"):
        params = record["parameters"]
        readable = " · ".join(f"{key}={value}" for key, value in params.items())
        st.caption(f"Recorded parameters: {readable}")


def render_recent_saved_run(kind):
    """Restore a previous result from disk when a user returns to a lab page."""
    candidates = [
        item for item in load_experiment_records()
        if (record_is_software(*item) if kind == "software" else record_is_fpga(*item))
    ]
    if not candidates:
        return
    with st.expander(f"Restore a saved {kind.upper()} result", expanded=True):
        labels = [record_label(item) for item in candidates]
        selected_index = st.selectbox(
            "Saved experiment",
            range(len(candidates)),
            format_func=lambda index: labels[index],
            key=f"restore_{kind}_record",
        )
        folder, record = candidates[selected_index]
        render_record_summary(folder, record, show_images=True)


def make_evidence_zip(folder):
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                archive.write(file, arcname=f"{folder.name}/{file.relative_to(folder)}")
    buffer.seek(0)
    return buffer.getvalue()


def software_total_seconds(record):
    value = record.get("total_cipher_seconds")
    if isinstance(value, (int, float)):
        return float(value)
    encryption = record.get("encryption_seconds")
    decryption = record.get("decryption_seconds")
    if isinstance(encryption, (int, float)) and isinstance(decryption, (int, float)):
        return float(encryption + decryption)
    return None


def fpga_transaction_seconds(record, operation):
    timings = record.get("timings") or {}
    values = timings.get(operation) or {}
    value = values.get("round_trip_seconds") if isinstance(values, dict) else None
    return float(value) if isinstance(value, (int, float)) else None



# ---------------- SIDEBAR ----------------

st.sidebar.markdown("## ◈ CHAOS / LAB")
st.sidebar.caption("EXPERIMENT CONTROL SYSTEM")

page = st.sidebar.radio(
    "WORKSPACES",
    [
        "Overview",
        "Unified Run",
        "Software Lab",
        "Hardware Lab",
        "Python Golden Model",
        "Analysis",
        "Software vs FPGA",
        "Previous Results",
        "Saved Demonstrations",
        "Evidence Center",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("**HARDWARE TARGET**")
st.sidebar.write("Zybo Z7-10")
st.sidebar.write("UART · 115200 baud")
st.sidebar.write("128 × 128 grayscale")
st.sidebar.divider()
st.sidebar.caption("PYTHON GOLDEN MODEL  /  FPGA VALIDATION")
st.sidebar.caption("LOCAL EXPERIMENT ARCHIVE")


# ---------------- HEADER ----------------

st.markdown("""
<div class="hero">
  <div class="eyebrow">CHAOS LAB / RESEARCH COMPUTE ENVIRONMENT</div>
  <h1>Image Cipher Validation Studio</h1>
  <p>A reproducible experimental workbench for Python golden-model analysis, Zybo Z7-10 hardware validation, paired execution and evidence capture.</p>
  <div class="hero-meta">
    <span>PLATFORM · ZYBO Z7-10</span>
    <span>PAYLOAD · 128 × 128 / 16,384 B</span>
    <span>INTERFACE · UART 115200</span>
    <span>MODE · EXPERIMENTAL</span>
  </div>
</div>
""", unsafe_allow_html=True)


def metric_row():
    cols = st.columns(4)
    cols[0].metric("Target device", "Zybo Z7-10")
    cols[1].metric("Image dimensions", "128 × 128")
    cols[2].metric("Input payload", "16,384 bytes")
    cols[3].metric("UART baud", "115200")


def find_vivado():
    candidates = [
        Path("/media/hathilal13/ubuntu_data/2026.1/Vivado/bin/vivado"),
        Path("/tools/Xilinx/Vivado/2026.1/bin/vivado"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None

def render_execution_lane(slot, title, subtitle, state, detail):
    palette = {
        "waiting": ("#d8bd83", "WAITING"),
        "running": ("#c4a6ff", "RUNNING"),
        "success": ("#a8d5b5", "PASS"),
        "error": ("#e39a9a", "FAILED"),
    }
    color, label = palette[state]
    html = (
        '<div style="background:linear-gradient(145deg,#24202f,#191722);'
        'border:1px solid #45394f;border-radius:14px;padding:18px 20px;min-height:142px">'
        f'<div style="font:10px DM Mono,monospace;letter-spacing:1.8px;color:#aaa3b5">{subtitle}</div>'
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin:10px 0 8px">'
        f'<div style="font-size:20px;font-weight:800;color:#f2eee8">{title}</div>'
        f'<div style="font:11px DM Mono,monospace;color:{color};border:1px solid {color};border-radius:20px;padding:5px 10px">{label}</div>'
        '</div>'
        f'<div style="font-size:13px;color:#b8afc2">{detail}</div></div>'
    )
    slot.markdown(html, unsafe_allow_html=True)


# ---------------- OVERVIEW ----------------

if page == "Overview":
    st.subheader("Research platform overview")
    metric_row()
    st.markdown(
        '<div class="panel"><span style="color:#c4a6ff;font:11px DM Mono,monospace;letter-spacing:1.5px">SYSTEM WORKFLOW</span>'
        '<h3 style="margin:8px 0 4px;color:#f2eee8">From image payload to reproducible evidence</h3>'
        '<p style="color:#aaa3b5;margin:0">Choose a paired run to execute one normalized image through both targets, or use the independent labs to isolate software and hardware experiments.</p></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.35, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Experimental workflow")
        st.markdown("""
        1. **Prepare input** — normalize an image to 128 × 128 grayscale.
        2. **Select execution targets** — configure the Python reference and Zybo Z7-10.
        3. **Execute independently** — run software and FPGA transactions in separate lanes.
        4. **Verify recovery** — check byte-for-byte reconstruction for each target.
        5. **Analyze** — inspect image statistics, timing boundaries and saved evidence.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        vivado = find_vivado()
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Environment detection")
        st.write("Vivado:", "Detected" if vivado else "Not detected")
        st.write("Vivado path:", str(vivado) if vivado else "Not found")
        st.write("FPGA serial port:", DEFAULT_PORT)
        st.write("Communication module:", "Loaded")
        st.markdown("</div>", unsafe_allow_html=True)

    st.info(
        "This is an independent FPGA application. The existing software "
        "dashboard and validated V7 project remain separate."
    )





# ---------------- UNIFIED SOFTWARE + FPGA RUN ----------------

elif page == "Unified Run":
    st.subheader("Unified experiment · one image, two execution targets")
    st.markdown(
        "Upload and normalize one image once. The exact same 128 × 128 grayscale "
        "byte payload is sent to the Python golden model and the Zybo FPGA. "
        "Both runs are archived separately and linked by a shared experiment ID."
    )

    from software_engine import run_software

    with st.container(border=True):
        st.markdown("#### 01 · Shared input")
        uploaded = st.file_uploader(
            "Upload one source image for both implementations",
            type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
            key="unified_shared_upload",
        )
        if uploaded is not None:
            try:
                with Image.open(io.BytesIO(uploaded.getvalue())) as source:
                    shared_gray = source.convert("L").resize(
                        (128, 128), Image.Resampling.LANCZOS
                    )
                shared_bytes = np.asarray(shared_gray, dtype=np.uint8).tobytes()
                shared_hash = sha256(shared_bytes)
                preview_col, detail_col = st.columns([1, 2])
                with preview_col:
                    st.image(shared_gray, caption="Shared normalized input", use_container_width=True)
                with detail_col:
                    st.metric("Payload", f"{len(shared_bytes):,} bytes")
                    st.code(f"SHA-256\n{shared_hash}")
                    st.caption("This exact byte sequence is reused by both execution paths.")
            except Exception as exc:
                st.error(f"Image preprocessing failed: {exc}")
                shared_bytes = None
                shared_hash = None
                shared_gray = None
        else:
            shared_bytes = shared_hash = shared_gray = None
            st.info("Upload one image to configure the paired experiment.")

    with st.container(border=True):
        st.markdown("#### 02 · Execution configuration")
        left, right = st.columns(2)
        with left:
            paired_algorithm = st.selectbox(
                "Python golden-model algorithm",
                [
                    "Bidirectional permutation-diffusion",
                    "Forward permutation-diffusion",
                    "XOR baseline",
                ],
                key="unified_algorithm",
            )
            px0, py0, pz0 = st.columns(3)
            with px0:
                paired_x0 = st.number_input("Initial X", value=1.0, format="%.6f", key="unified_x0")
            with py0:
                paired_y0 = st.number_input("Initial Y", value=1.0, format="%.6f", key="unified_y0")
            with pz0:
                paired_z0 = st.number_input("Initial Z", value=1.0, format="%.6f", key="unified_z0")
            paired_warmup = st.number_input(
                "Warm-up iterations", min_value=0, max_value=100000,
                value=100, step=10, key="unified_warmup"
            )
            paired_iv = st.number_input(
                "Initialization value (IV)", min_value=0, max_value=255,
                value=165, key="unified_iv"
            )
        with right:
            st.markdown("**Hardware target**")
            metric_row()
            paired_port = st.text_input("FPGA serial port", value=DEFAULT_PORT, key="unified_port")
            st.warning(
                "The FPGA must be connected and programmed for a live paired run. "
                "If it is unavailable, use Previous Results to present archived runs."
            )

    run_pair = st.button(
        "RUN BOTH · PYTHON + FPGA",
        type="primary",
        use_container_width=True,
        disabled=(shared_bytes is None),
        key="run_unified_pair",
    )

    if run_pair and shared_bytes is not None:
        pair_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        software_run_id = f"paired_{pair_id}_software"
        fpga_run_id = f"paired_{pair_id}_fpga"
        sw_dir = EXPERIMENTS / f"software_{software_run_id}"
        fpga_dir = EXPERIMENTS / fpga_run_id
        sw_dir.mkdir(parents=True, exist_ok=False)
        fpga_dir.mkdir(parents=True, exist_ok=False)
        parameters = {
            "x0": float(paired_x0), "y0": float(paired_y0),
            "z0": float(paired_z0), "warmup": int(paired_warmup),
            "iv": int(paired_iv),
        }
        sw_events = []

        def paired_log(message):
            stamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
            sw_events.append(f"[{stamp}] {message}")

        shared_gray.save(sw_dir / "original.png")
        shared_gray.save(fpga_dir / "original.png")
        pair_manifest = {
            "paired_run_id": pair_id,
            "shared_input_sha256": shared_hash,
            "input_bytes": len(shared_bytes),
            "timestamp": datetime.now().astimezone().isoformat(),
            "software_run_folder": sw_dir.name,
            "fpga_run_folder": fpga_dir.name,
            "status": "running",
        }
        (EXPERIMENTS / f"pair_{pair_id}.json").write_text(json.dumps(pair_manifest, indent=2))

        st.markdown("### Live execution · independent target lanes")
        lane_sw, lane_fpga = st.columns(2, gap="large")
        with lane_sw:
            sw_slot = st.empty()
        with lane_fpga:
            fpga_slot = st.empty()
        render_execution_lane(sw_slot, "Python golden model", "SOFTWARE EXECUTION", "running", "Executing encryption, decryption and recovery verification.")
        render_execution_lane(fpga_slot, "Zybo Z7-10 FPGA", "HARDWARE TRANSACTION", "waiting", "Queued next · UART transaction starts after the software run.")
        execution_stage = "software"
        try:
            with st.status("Executing Python golden model…", expanded=True) as status:
                sw_result = run_software(shared_bytes, paired_algorithm, parameters, paired_log)
                Image.frombytes("L", (128, 128), sw_result["ciphertext"]).save(sw_dir / "ciphertext.png")
                Image.frombytes("L", (128, 128), sw_result["recovered"]).save(sw_dir / "recovered.png")
                (sw_dir / "ciphertext.bin").write_bytes(sw_result["ciphertext"])
                (sw_dir / "execution.log").write_text("\n".join(sw_events) + "\n")
                sw_record = {
                    key: value for key, value in sw_result.items()
                    if key not in ("ciphertext", "recovered", "histogram")
                }
                sw_record.update({
                    "run_id": software_run_id,
                    "paired_run_id": pair_id,
                    "shared_input_sha256": shared_hash,
                    "execution_mode": "paired",
                    "implementation": "Python software",
                    "execution_provenance": "live_execution",
                    "execution_scope": "python_software_execution",
                    "algorithm": paired_algorithm,
                    "parameters": parameters,
                    "input_bytes": len(shared_bytes),
                    "timestamp": datetime.now().astimezone().isoformat(),
                    "histogram": sw_result["histogram"],
                })
                (sw_dir / "experiment.json").write_text(json.dumps(sw_record, indent=2))
                render_execution_lane(sw_slot, "Python golden model", "SOFTWARE EXECUTION", "success", f"Exact recovery: {'PASS' if sw_record['exact_recovery'] else 'FAIL'} · {sw_record.get('matching_pixels', 0):,}/{len(shared_bytes):,} pixels matched.")
                execution_stage = "fpga"
                render_execution_lane(fpga_slot, "Zybo Z7-10 FPGA", "HARDWARE TRANSACTION", "running", "Encrypt → decrypt → controlled differential test over UART.")
                status.update(label="Python complete. FPGA UART transaction in progress…", state="running")

                enc = transact(shared_bytes, operation="encrypt", port=paired_port.strip())
                fpga_cipher = enc["output"]
                dec = transact(fpga_cipher, operation="decrypt", port=paired_port.strip())
                fpga_recovered = dec["output"]
                changed = bytearray(shared_bytes)
                changed[0] = (changed[0] + 1) & 0xFF
                changed_enc = transact(bytes(changed), operation="encrypt", port=paired_port.strip())

                fpga_mismatches = int(np.count_nonzero(
                    np.frombuffer(shared_bytes, dtype=np.uint8) !=
                    np.frombuffer(fpga_recovered, dtype=np.uint8)
                ))
                fpga_analysis = {
                    "ciphertext_entropy_bits_per_pixel": image_entropy(fpga_cipher),
                    "neighbor_correlations": image_correlations(fpga_cipher),
                    "differential_metrics": differential_metrics(fpga_cipher, changed_enc["output"]),
                }
                fpga_record = {
                    "run_id": fpga_run_id,
                    "paired_run_id": pair_id,
                    "shared_input_sha256": shared_hash,
                    "execution_mode": "paired",
                    "timestamp": datetime.now().astimezone().isoformat(),
                    "platform": "Zybo Z7-10",
                    "interface": "UART",
                    "execution_provenance": "live_execution",
                    "hardware_transaction_completed": True,
                    "hardware_validation_scope": "live_uart_round_trip_only",
                    "firmware_identity": None,
                    "bitstream_sha256": None,
                    "port": paired_port,
                    "image_dimensions": [128, 128],
                    "input_bytes": len(shared_bytes),
                    "input_sha256": shared_hash,
                    "ciphertext_sha256": sha256(fpga_cipher),
                    "recovered_sha256": sha256(fpga_recovered),
                    "exact_recovery": fpga_mismatches == 0,
                    "matching_pixels": len(shared_bytes) - fpga_mismatches,
                    "mismatched_pixels": fpga_mismatches,
                    "analysis": fpga_analysis,
                    "timings": {
                        "encryption": enc["timings"],
                        "decryption": dec["timings"],
                        "differential_test_encryption": changed_enc["timings"],
                    },
                }
                Image.frombytes("L", (128, 128), fpga_cipher).save(fpga_dir / "ciphertext.png")
                Image.frombytes("L", (128, 128), fpga_recovered).save(fpga_dir / "recovered.png")
                (fpga_dir / "ciphertext.bin").write_bytes(fpga_cipher)
                (fpga_dir / "recovered.bin").write_bytes(fpga_recovered)
                (fpga_dir / "experiment.json").write_text(json.dumps(fpga_record, indent=2))
                pair_manifest["status"] = "completed"
                pair_manifest["software_exact_recovery"] = bool(sw_record["exact_recovery"])
                pair_manifest["fpga_exact_recovery"] = fpga_mismatches == 0
                (EXPERIMENTS / f"pair_{pair_id}.json").write_text(json.dumps(pair_manifest, indent=2))
                render_execution_lane(fpga_slot, "Zybo Z7-10 FPGA", "HARDWARE TRANSACTION", "success", f"Exact recovery: {'PASS' if fpga_record['exact_recovery'] else 'FAIL'} · {fpga_record['matching_pixels']:,}/{len(shared_bytes):,} pixels matched.")
                status.update(label="Paired experiment completed and archived.", state="complete", expanded=False)

            st.success("Both runs completed. The common input hash links the two records.")
            st.markdown("### Paired result overview")
            result_sw, result_fpga = st.columns(2, gap="large")
            with result_sw:
                st.markdown("#### Python golden model")
                st.metric("Exact recovery", "PASS" if sw_record["exact_recovery"] else "FAIL")
                st.metric("Matching pixels", f"{sw_record['matching_pixels']:,} / {len(shared_bytes):,}")
                st.metric("Ciphertext entropy", f"{sw_record.get('entropy_bits_per_pixel', 0):.5f} bits/pixel")
                st.caption(f"Run ID: {software_run_id}")
            with result_fpga:
                st.markdown("#### Zybo Z7-10 FPGA")
                st.metric("Exact recovery", "PASS" if fpga_record["exact_recovery"] else "FAIL")
                st.metric("Matching pixels", f"{fpga_record['matching_pixels']:,} / {len(shared_bytes):,}")
                st.metric("Ciphertext entropy", f"{fpga_analysis['ciphertext_entropy_bits_per_pixel']:.5f} bits/pixel")
                st.caption(f"Run ID: {fpga_run_id}")
            metric_cols = st.columns(4)
            metric_cols[0].metric("Shared input", "SHA-256 matched")
            metric_cols[1].metric("Python recovery", "PASS" if sw_record["exact_recovery"] else "FAIL")
            metric_cols[2].metric("FPGA recovery", "PASS" if fpga_record["exact_recovery"] else "FAIL")
            metric_cols[3].metric("Input bytes", f"{len(shared_bytes):,}")

            sw_entropy = sw_record.get("entropy_bits_per_pixel")
            fpga_entropy = fpga_analysis["ciphertext_entropy_bits_per_pixel"]
            sw_diff = sw_record.get("differential_metrics") or {}
            fpga_diff = fpga_analysis["differential_metrics"]
            comparison = [
                {"Metric": "Exact recovery", "Python": "PASS" if sw_record["exact_recovery"] else "FAIL", "FPGA": "PASS" if fpga_record["exact_recovery"] else "FAIL"},
                {"Metric": "Matching pixels", "Python": sw_record["matching_pixels"], "FPGA": fpga_record["matching_pixels"]},
                {"Metric": "Ciphertext entropy (bits/pixel)", "Python": sw_entropy, "FPGA": fpga_entropy},
                {"Metric": "NPCR (%)", "Python": sw_diff.get("npcr_percent"), "FPGA": fpga_diff.get("npcr_percent")},
                {"Metric": "UACI (%)", "Python": sw_diff.get("uaci_percent"), "FPGA": fpga_diff.get("uaci_percent")},
            ]
            st.dataframe(comparison, use_container_width=True, hide_index=True)

            st.markdown("### Visual evidence")
            visual_cols = st.columns(3)
            visual_cols[0].image(shared_gray, caption="Shared source image", use_container_width=True)
            visual_cols[1].image(Image.frombytes("L", (128, 128), sw_result["ciphertext"]), caption="Python ciphertext", use_container_width=True)
            visual_cols[2].image(Image.frombytes("L", (128, 128), fpga_cipher), caption="FPGA ciphertext", use_container_width=True)
            rec_cols = st.columns(2)
            rec_cols[0].image(Image.frombytes("L", (128, 128), sw_result["recovered"]), caption="Python recovered", use_container_width=True)
            rec_cols[1].image(Image.frombytes("L", (128, 128), fpga_recovered), caption="FPGA recovered", use_container_width=True)

            st.warning(
                "The common SHA-256 confirms identical input bytes. It does not by itself "
                "prove that the FPGA implements the same algorithm or parameters as the "
                "selected Python algorithm. Confirm algorithm equivalence from RTL and "
                "golden-model source before making that claim."
            )
        except Exception as exc:
            pair_manifest["status"] = "failed_or_partial"
            pair_manifest["error"] = str(exc)
            (EXPERIMENTS / f"pair_{pair_id}.json").write_text(json.dumps(pair_manifest, indent=2))
            st.error(f"Paired run failed or stopped part-way: {exc}")
            if execution_stage == "software":
                render_execution_lane(sw_slot, "Python golden model", "SOFTWARE EXECUTION", "error", "Software execution failed. Inspect the error and saved partial evidence.")
                render_execution_lane(fpga_slot, "Zybo Z7-10 FPGA", "HARDWARE TRANSACTION", "waiting", "Not started because the software stage failed.")
            else:
                render_execution_lane(fpga_slot, "Zybo Z7-10 FPGA", "HARDWARE TRANSACTION", "error", "Transaction failed or did not complete. Inspect the error and saved partial evidence.")
            st.info(
                "Any completed software record remains saved. The FPGA folder may contain "
                "partial evidence if the hardware stage failed."
            )

# ---------------- PYTHON GOLDEN MODEL ----------------

elif page == "Python Golden Model":
    st.subheader("Python golden model · algorithm specification")
    st.write(
        "This workspace documents the mathematical model used by the software reference "
        "implementation and its role as a verification oracle for the FPGA."
    )
    st.info(
        "The integration layer identifies three implementations: XOR baseline, "
        "forward permutation-diffusion, and bidirectional permutation-diffusion. "
        "The exact recurrence equations, permutation construction, key schedule and "
        "diffusion update rules must be extracted from the corresponding "
        "`python/chaos_cipher/*.py` source files. Those algorithm source files were "
        "not included in the source bundle inspected for this update, so this page "
        "does not invent or misattribute equations."
    )
    st.markdown("### Reference pipeline")
    st.code(
        "Input image → 128×128 grayscale byte vector → chaotic sequence / "
        "permutation → diffusion → ciphertext\n"
        "Ciphertext → inverse diffusion → inverse permutation → recovered image",
        language="text",
    )
    st.markdown("### Documented algorithm entry points")
    st.dataframe(
        [
            {"Algorithm": "XOR baseline", "Reference functions": "chaos_cipher.cipher.encrypt / decrypt"},
            {"Algorithm": "Forward permutation-diffusion", "Reference functions": "chaos_cipher.permutation_diffusion.encrypt / decrypt"},
            {"Algorithm": "Bidirectional permutation-diffusion", "Reference functions": "chaos_cipher.bidirectional_diffusion.encrypt / decrypt"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("### Golden-model verification contract")
    st.latex(r"C = E_K(P), \\qquad P' = D_K(C), \\qquad P' \\stackrel{?}{=} P")
    st.write(
        "For each test image, the model encrypts the normalized byte vector, decrypts "
        "the resulting ciphertext, and checks exact byte-for-byte recovery. The FPGA "
        "output can then be compared against the software reference only after "
        "confirming that both implementations use equivalent algorithm logic and "
        "parameters."
    )
    st.warning(
        "To publish the actual chaotic recurrence and diffusion equations, provide "
        "the files from `python/chaos_cipher/` (especially cipher.py, "
        "permutation_diffusion.py, bidirectional_diffusion.py, and any sequence or "
        "key-generation modules). The equations will then be transcribed directly "
        "from your implementation, not guessed."
    )


# ---------------- SOFTWARE LAB ----------------

elif page == "Software Lab":
    render_recent_saved_run("software")
    from software_engine import run_software

    st.subheader("Python software encryption laboratory")
    st.write(
        "Execute the repository's original Python algorithms. "
        "Encryption, decryption, verification and analysis run in one experiment."
    )

    algorithm = st.selectbox(
        "Encryption algorithm",
        [
            "Bidirectional permutation-diffusion",
            "Forward permutation-diffusion",
            "XOR baseline",
        ],
    )

    uploaded = st.file_uploader(
        "Upload an image for software encryption",
        type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
        key="software_lab_upload",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        x0 = st.number_input("Initial X", value=1.0, format="%.6f",
                             key="software_x0")
    with c2:
        y0 = st.number_input("Initial Y", value=1.0, format="%.6f",
                             key="software_y0")
    with c3:
        z0 = st.number_input("Initial Z", value=1.0, format="%.6f",
                             key="software_z0")

    c4, c5 = st.columns(2)
    with c4:
        warmup = st.number_input(
            "Warm-up iterations", min_value=0, max_value=100000,
            value=100, step=10, key="software_warmup"
        )
    with c5:
        iv = st.number_input(
            "Initialization value (IV)", min_value=0, max_value=255,
            value=165, key="software_iv"
        )

    if uploaded is not None:
        try:
            with Image.open(io.BytesIO(uploaded.getvalue())) as source_image:
                gray = source_image.convert("L").resize(
                    (128, 128), Image.Resampling.LANCZOS
                )

            original_bytes = np.asarray(gray, dtype=np.uint8).tobytes()

            st.image(gray, caption="Software experiment input", width=260)
            st.caption(
                f"128 × 128 grayscale · {len(original_bytes):,} bytes · "
                f"SHA-256: {hashlib.sha256(original_bytes).hexdigest()}"
            )

            if st.button(
                "▶ Run Complete Software Experiment",
                type="primary",
                use_container_width=True,
            ):
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                run_dir = EXPERIMENTS / f"software_{run_id}"
                run_dir.mkdir(parents=True, exist_ok=True)

                events = []

                def log_event(message):
                    stamp = datetime.now().astimezone().isoformat(
                        timespec="milliseconds"
                    )
                    line = f"[{stamp}] {message}"
                    events.append(line)
                    print(f"[SOFTWARE EXPERIMENT] {line}", flush=True)

                parameters = {
                    "x0": float(x0),
                    "y0": float(y0),
                    "z0": float(z0),
                    "warmup": int(warmup),
                    "iv": int(iv),
                }

                try:
                    with st.spinner("Running Python encryption and decryption..."):
                        result = run_software(
                            original_bytes, algorithm, parameters, log_event
                        )

                    Image.frombytes("L", (128, 128), result["ciphertext"]).save(
                        run_dir / "ciphertext.png"
                    )
                    Image.frombytes("L", (128, 128), result["recovered"]).save(
                        run_dir / "recovered.png"
                    )
                    gray.save(run_dir / "original.png")
                    (run_dir / "ciphertext.bin").write_bytes(
                        result["ciphertext"]
                    )
                    (run_dir / "execution.log").write_text(
                        "\n".join(events) + "\n"
                    )

                    record = {
                        key: value for key, value in result.items()
                        if key not in ("ciphertext", "recovered", "histogram")
                    }
                    record.update({
                        "run_id": run_id,
                        "implementation": "Python software",
                        "execution_provenance": "live_execution",
                        "execution_scope": "python_software_execution",
                        "algorithm": algorithm,
                        "parameters": parameters,
                        "input_bytes": len(original_bytes),
                        "timestamp": datetime.now().astimezone().isoformat(),
                        "histogram": result["histogram"],
                    })

                    (run_dir / "experiment.json").write_text(
                        json.dumps(record, indent=2)
                    )

                    st.session_state["latest_software_result"] = {
                        "run_id": run_id,
                        "record": record,
                    }

                    st.success(
                        "Software experiment completed. Evidence saved."
                    )

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric(
                        "Recovery",
                        "PASS" if result["exact_recovery"] else "FAIL",
                    )
                    m2.metric(
                        "Encryption",
                        f"{result['encryption_seconds']:.6f} s",
                    )
                    m3.metric(
                        "Decryption",
                        f"{result['decryption_seconds']:.6f} s",
                    )
                    m4.metric(
                        "Entropy",
                        f"{result['entropy_bits_per_pixel']:.4f} bits",
                    )

                    image_cols = st.columns(3)
                    image_cols[0].image(gray, caption="Original")
                    image_cols[1].image(
                        Image.frombytes("L", (128, 128), result["ciphertext"]),
                        caption="Software ciphertext",
                    )
                    image_cols[2].image(
                        Image.frombytes("L", (128, 128), result["recovered"]),
                        caption="Recovered image",
                    )

                    st.markdown("### Statistical analysis")
                    d = result["differential_metrics"]
                    a, b, c = st.columns(3)
                    a.metric("NPCR", f"{d['npcr_percent']:.4f}%")
                    b.metric("UACI", f"{d['uaci_percent']:.4f}%")
                    c.metric(
                        "Distinct ciphertext values",
                        str(result["distinct_values"]),
                    )

                    st.markdown("#### Neighboring-pixel correlations")
                    corr = result["neighbor_correlations"]
                    corr_cols = st.columns(3)
                    for col, (name, value) in zip(corr_cols, corr.items()):
                        col.metric(
                            name.capitalize(),
                            f"{value:.6f}" if value is not None else "Undefined",
                        )

                    st.markdown("### Live execution log")
                    st.code("\n".join(events), language="text")

                    st.markdown("### SHA-256 verification")
                    st.code(
                        f"Input:      {result['input_sha256']}\n"
                        f"Ciphertext: {result['ciphertext_sha256']}\n"
                        f"Recovered:  {result['recovered_sha256']}"
                    )

                    st.download_button(
                        "Download software experiment JSON",
                        data=(run_dir / "experiment.json").read_bytes(),
                        file_name=f"software_experiment_{run_id}.json",
                        mime="application/json",
                    )
                    st.download_button(
                        "Download execution log",
                        data=(run_dir / "execution.log").read_bytes(),
                        file_name=f"software_execution_{run_id}.log",
                        mime="text/plain",
                    )

                    st.info(
                        "The terminal running Streamlit also receives the "
                        "timestamped backend execution events."
                    )

                except Exception as exc:
                    log_event(f"EXPERIMENT FAILED: {exc}")
                    (run_dir / "execution.log").write_text(
                        "\n".join(events) + "\n"
                    )
                    st.error(f"Software experiment failed: {exc}")

        except Exception as exc:
            st.error(f"Image preprocessing failed: {exc}")
    else:
        st.info("Upload an image to configure a software experiment.")


# ---------------- HARDWARE LAB ----------------

elif page == "Hardware Lab":
    render_recent_saved_run("fpga")
    st.subheader("Complete FPGA encryption and decryption experiment")
    st.write(
        "One execution runs encryption followed immediately by decryption. "
        "The recovered image is checked against the original input."
    )
    metric_row()

    port = st.text_input("Serial port", value=DEFAULT_PORT)

    uploaded = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
    )

    if uploaded:
        try:
            with Image.open(io.BytesIO(uploaded.getvalue())) as source:
                gray = source.convert("L").resize(
                    (128, 128), Image.Resampling.LANCZOS
                )

            pixels = np.asarray(gray, dtype=np.uint8)
            original_bytes = pixels.tobytes()

            st.markdown("### Prepared input")
            c1, c2 = st.columns([1, 1.4])

            with c1:
                st.image(gray, caption="Normalized grayscale input", width=260)

            with c2:
                st.metric("Input payload", f"{len(original_bytes):,} bytes")
                st.code(f"SHA-256: {sha256(original_bytes)}")
                st.caption(
                    "The same 16,384 input bytes are used for the complete "
                    "hardware round trip."
                )

            if st.button(
                "▶  Run Complete FPGA Experiment",
                type="primary",
                use_container_width=True,
            ):
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                run_dir = EXPERIMENTS / run_id
                run_dir.mkdir(parents=True, exist_ok=True)

                try:
                    # Stage 1: FPGA encryption
                    st.markdown("### Stage 1 — Hardware encryption")
                    with st.spinner("Sending plaintext to FPGA for encryption..."):
                        encryption_result = transact(
                            original_bytes,
                            operation="encrypt",
                            port=port.strip(),
                        )

                    cipher_bytes = encryption_result["output"]
                    cipher_image = image_from_bytes(cipher_bytes)
                    st.success("FPGA encryption transaction completed.")

                    # Stage 2: FPGA decryption of the actual ciphertext
                    st.markdown("### Stage 2 — Hardware decryption")
                    with st.spinner("Sending FPGA ciphertext back for decryption..."):
                        decryption_result = transact(
                            cipher_bytes,
                            operation="decrypt",
                            port=port.strip(),
                        )

                    recovered_bytes = decryption_result["output"]
                    recovered_image = image_from_bytes(recovered_bytes)
                    st.success("FPGA decryption transaction completed.")

                    # Stage 3: Exact recovery verification
                    original_array = np.frombuffer(
                        original_bytes, dtype=np.uint8
                    )
                    recovered_array = np.frombuffer(
                        recovered_bytes, dtype=np.uint8
                    )
                    mismatches = int(np.count_nonzero(
                        original_array != recovered_array
                    ))
                    matches = PIXELS - mismatches
                    exact_recovery = mismatches == 0

                    st.markdown("### Stage 3 — Recovery verification")

                    if exact_recovery:
                        st.success(
                            f"EXACT RECOVERY PASS — {matches:,}/{PIXELS:,} "
                            "pixels match."
                        )
                    else:
                        st.error(
                            f"EXACT RECOVERY FAIL — {mismatches:,} "
                            "pixel mismatches detected."
                        )

                    # Stage 4: Image analysis
                    st.markdown("### Stage 4 — Ciphertext analysis")

                    entropy = image_entropy(cipher_bytes)
                    correlations = image_correlations(cipher_bytes)

                    # One-pixel differential test on the FPGA.
                    changed_input = bytearray(original_bytes)
                    changed_input[0] = (changed_input[0] + 1) & 0xFF

                    with st.spinner(
                        "Running additional FPGA encryption for NPCR/UACI..."
                    ):
                        changed_result = transact(
                            bytes(changed_input),
                            operation="encrypt",
                            port=port.strip(),
                        )

                    differential = differential_metrics(
                        cipher_bytes,
                        changed_result["output"],
                    )

                    st.success("Differential FPGA test completed.")

                    # Save images
                    gray.save(run_dir / "original.png")
                    cipher_image.save(run_dir / "ciphertext.png")
                    recovered_image.save(run_dir / "recovered.png")

                    # Timings
                    timings = {
                        "encryption": encryption_result["timings"],
                        "decryption": decryption_result["timings"],
                        "differential_test_encryption": changed_result["timings"],
                    }

                    analysis = {
                        "ciphertext_entropy_bits_per_pixel": entropy,
                        "neighbor_correlations": correlations,
                        "differential_metrics": differential,
                    }

                    record = {
                        "run_id": run_id,
                        "timestamp": datetime.now().astimezone().isoformat(),
                        "platform": "Zybo Z7-10",
                        "interface": "UART",
                        "execution_provenance": "live_execution",
                        "hardware_transaction_completed": True,
                        "hardware_validation_scope": "live_uart_round_trip_only",
                        "firmware_identity": None,
                        "bitstream_sha256": None,
                        "port": port,
                        "image_dimensions": [128, 128],
                        "input_bytes": PIXELS,
                        "input_sha256": sha256(original_bytes),
                        "ciphertext_sha256": sha256(cipher_bytes),
                        "recovered_sha256": sha256(recovered_bytes),
                        "exact_recovery": exact_recovery,
                        "matching_pixels": matches,
                        "mismatched_pixels": mismatches,
                        "analysis": analysis,
                        "timings": timings,
                    }

                    (run_dir / "experiment.json").write_text(
                        json.dumps(record, indent=2)
                    )

                    # Downloadable raw ciphertext and JSON
                    (run_dir / "ciphertext.bin").write_bytes(cipher_bytes)
                    (run_dir / "recovered.bin").write_bytes(recovered_bytes)

                    st.markdown("### Experimental results")

                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Recovery", "PASS" if exact_recovery else "FAIL")
                    r2.metric("Matching pixels", f"{matches:,}/{PIXELS:,}")
                    r3.metric("Ciphertext entropy", f"{entropy:.4f} bits")
                    r4.metric("Pixel mismatches", f"{mismatches:,}")

                    st.markdown("### Image comparison")
                    image_cols = st.columns(3)

                    with image_cols[0]:
                        st.image(gray, caption="1. Original input", width="stretch")
                    with image_cols[1]:
                        st.image(
                            cipher_image,
                            caption="2. FPGA ciphertext",
                            width="stretch",
                        )
                    with image_cols[2]:
                        st.image(
                            recovered_image,
                            caption="3. FPGA recovered image",
                            width="stretch",
                        )

                    st.markdown("### Statistical analysis")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("NPCR", f"{differential['npcr_percent']:.4f}%")
                    m2.metric("UACI", f"{differential['uaci_percent']:.4f}%")
                    m3.metric("Entropy", f"{entropy:.4f} bits/pixel")

                    st.markdown("#### Neighboring-pixel correlations")
                    corr_cols = st.columns(3)
                    for col, (name, value) in zip(
                        corr_cols, correlations.items()
                    ):
                        col.metric(
                            name.capitalize(),
                            f"{value:.6f}" if value is not None else "Undefined",
                        )

                    st.markdown("### Communication and execution timings")
                    timing_rows = []
                    for operation_name, operation_timings in timings.items():
                        for timing_name, seconds in operation_timings.items():
                            timing_rows.append({
                                "Operation": operation_name.replace("_", " ").title(),
                                "Measurement": timing_name.replace("_", " ").title(),
                                "Seconds": seconds,
                            })

                    st.dataframe(
                        timing_rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.info(
                        "Timing interpretation: host write/read and "
                        "round-trip values include serial communication. "
                        "The completion-wait interval is not a pure FPGA "
                        "computation-time measurement."
                    )

                    st.markdown("### SHA-256 evidence")
                    st.code(
                        "Input:      " + record["input_sha256"] + "\n"
                        "Ciphertext: " + record["ciphertext_sha256"] + "\n"
                        "Recovered:  " + record["recovered_sha256"]
                    )

                    st.download_button(
                        "Download complete experiment JSON",
                        data=(run_dir / "experiment.json").read_bytes(),
                        file_name=f"fpga_experiment_{run_id}.json",
                        mime="application/json",
                    )

                    st.download_button(
                        "Download ciphertext binary",
                        data=cipher_bytes,
                        file_name=f"ciphertext_{run_id}.bin",
                        mime="application/octet-stream",
                    )

                    st.success(
                        f"Experiment evidence saved in experiments/{run_id}"
                    )

                except Exception as exc:
                    st.error(f"Experiment failed: {exc}")
                    st.warning(
                        "A failed or incomplete transaction is not recorded "
                        "as a successful experiment. Check board power, "
                        "firmware, UART connection and selected port."
                    )

        except Exception as exc:
            st.error(f"Image preprocessing failed: {exc}")

    else:
        st.info("Upload an image to prepare the complete FPGA experiment.")



# ---------------- ANALYSIS ----------------

elif page == "Analysis":
    st.subheader("Research analysis center")
    st.write("Inspect saved measurements and image evidence from completed experiments.")

    records = load_experiment_records()
    complete_records = [item for item in records if item[1].get("exact_recovery") is not None]
    if not complete_records:
        st.info("No complete experiment records are available yet.")
    else:
        labels = [record_label(item) for item in complete_records]
        selected_index = st.selectbox(
            "Select an experiment",
            range(len(complete_records)),
            format_func=lambda index: labels[index],
            key="analysis_record_selection",
        )
        folder, data = complete_records[selected_index]
        render_record_summary(folder, data, show_images=True)

        with st.expander("Experiment identification", expanded=False):
            st.write(f"**Run ID:** {data.get('run_id', folder.name)}")
            st.write(f"**Input SHA-256:** {data.get('input_sha256', 'Not recorded')}")
            st.write(f"**Ciphertext SHA-256:** {data.get('ciphertext_sha256', 'Not recorded')}")
            st.write(f"**Recovered SHA-256:** {data.get('recovered_sha256', 'Not recorded')}")
            st.write(f"**Platform:** {data.get('platform', 'Python software' if record_is_software(folder, data) else 'Not recorded')}")
            st.write(f"**Interface:** {data.get('interface', 'Not applicable' if record_is_software(folder, data) else 'Not recorded')}")

        histogram = data.get("histogram")
        if isinstance(histogram, list) and len(histogram) == 256:
            st.markdown("### Ciphertext intensity distribution")
            st.bar_chart({"Pixel count": histogram}, height=220)

        st.markdown("### Interpretation")
        st.write(
            "Entropy describes the distribution of ciphertext byte values. "
            "Adjacent-pixel correlations describe linear relationships between "
            "neighboring pixels. NPCR and UACI describe changes between ciphertexts "
            "generated from a controlled input modification."
        )
        st.warning(
            "These statistical measurements do not independently establish "
            "cryptographic security. Interpret them alongside implementation "
            "evidence and cryptanalytic testing."
        )


# ---------------- SOFTWARE VS FPGA COMPARISON ----------------

elif page == "Software vs FPGA":
    st.subheader("Software and FPGA comparison")
    st.write(
        "Compare saved runs using the same input image bytes. Timing labels keep "
        "Python computation separate from FPGA host-to-board UART transactions."
    )

    all_records = load_experiment_records()
    software_records = [
        item for item in all_records
        if record_is_software(*item) and item[1].get("exact_recovery") is True
    ]
    fpga_records = [
        item for item in all_records
        if record_is_fpga(*item) and item[1].get("exact_recovery") is True
    ]

    software_by_hash = {}
    fpga_by_hash = {}
    for item in software_records:
        digest = item[1].get("input_sha256")
        if digest:
            software_by_hash.setdefault(digest, []).append(item)
    for item in fpga_records:
        digest = item[1].get("input_sha256")
        if digest:
            fpga_by_hash.setdefault(digest, []).append(item)

    common_hashes = sorted(
        set(software_by_hash) & set(fpga_by_hash),
        key=lambda digest: max(
            software_by_hash[digest][0][0].name,
            fpga_by_hash[digest][0][0].name,
        ),
        reverse=True,
    )

    if not common_hashes:
        st.info(
            "No completed Software and FPGA runs currently share an input SHA-256. "
            "Run both implementations using the same normalized 128 × 128 image "
            "to enable a like-for-like input comparison."
        )
    else:
        chosen_hash = st.selectbox(
            "Matched input image",
            common_hashes,
            format_func=lambda digest: f"{digest[:16]}… ({len(software_by_hash[digest])} software / {len(fpga_by_hash[digest])} FPGA runs)",
            key="comparison_input_hash",
        )
        software_options = software_by_hash[chosen_hash]
        fpga_options = fpga_by_hash[chosen_hash]

        left, right = st.columns(2)
        with left:
            sw_index = st.selectbox(
                "Software run",
                range(len(software_options)),
                format_func=lambda index: record_label(software_options[index]),
                key="comparison_software_run",
            )
        with right:
            fpga_index = st.selectbox(
                "FPGA run",
                range(len(fpga_options)),
                format_func=lambda index: record_label(fpga_options[index]),
                key="comparison_fpga_run",
            )

        sw_folder, sw = software_options[sw_index]
        fpga_folder, fpga = fpga_options[fpga_index]
        st.success("Input match confirmed: both records have the same input SHA-256.")
        st.caption(f"Input SHA-256: {chosen_hash}")

        sw_entropy, sw_diff, _ = get_record_analysis(sw)
        fpga_entropy, fpga_diff, _ = get_record_analysis(fpga)

        st.markdown("### Functional and statistical results")
        rows = [
            {
                "Measurement": "Exact recovery",
                "Software": "PASS" if sw.get("exact_recovery") is True else "FAIL",
                "FPGA": "PASS" if fpga.get("exact_recovery") is True else "FAIL",
            },
            {
                "Measurement": "Matching pixels",
                "Software": f"{sw.get('matching_pixels', '—')}",
                "FPGA": f"{fpga.get('matching_pixels', '—')}",
            },
            {
                "Measurement": "Ciphertext entropy (bits/pixel)",
                "Software": f"{sw_entropy:.4f}" if isinstance(sw_entropy, (int, float)) else "Not recorded",
                "FPGA": f"{fpga_entropy:.4f}" if isinstance(fpga_entropy, (int, float)) else "Not recorded",
            },
            {
                "Measurement": "NPCR (%)",
                "Software": f"{sw_diff['npcr_percent']:.4f}" if isinstance(sw_diff.get("npcr_percent"), (int, float)) else "Not recorded",
                "FPGA": f"{fpga_diff['npcr_percent']:.4f}" if isinstance(fpga_diff.get("npcr_percent"), (int, float)) else "Not recorded",
            },
            {
                "Measurement": "UACI (%)",
                "Software": f"{sw_diff['uaci_percent']:.4f}" if isinstance(sw_diff.get("uaci_percent"), (int, float)) else "Not recorded",
                "FPGA": f"{fpga_diff['uaci_percent']:.4f}" if isinstance(fpga_diff.get("uaci_percent"), (int, float)) else "Not recorded",
            },
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        sw_enc = sw.get("encryption_seconds")
        sw_dec = sw.get("decryption_seconds")
        sw_total = software_total_seconds(sw)
        fpga_enc = fpga_transaction_seconds(fpga, "encryption")
        fpga_dec = fpga_transaction_seconds(fpga, "decryption")
        fpga_total = (
            fpga_enc + fpga_dec
            if fpga_enc is not None and fpga_dec is not None else None
        )

        st.markdown("### Performance comparison")
        timing_rows = [
            {
                "Measurement": "Encryption",
                "Software computation (s)": f"{sw_enc:.6f}" if isinstance(sw_enc, (int, float)) else "Not recorded",
                "FPGA UART transaction (s)": f"{fpga_enc:.6f}" if fpga_enc is not None else "Not recorded",
            },
            {
                "Measurement": "Decryption",
                "Software computation (s)": f"{sw_dec:.6f}" if isinstance(sw_dec, (int, float)) else "Not recorded",
                "FPGA UART transaction (s)": f"{fpga_dec:.6f}" if fpga_dec is not None else "Not recorded",
            },
            {
                "Measurement": "Encrypt + decrypt",
                "Software computation (s)": f"{sw_total:.6f}" if sw_total is not None else "Not recorded",
                "FPGA UART transactions (s)": f"{fpga_total:.6f}" if fpga_total is not None else "Not recorded",
            },
        ]
        st.dataframe(timing_rows, use_container_width=True, hide_index=True)
        st.caption(
            "Software times measure Python cipher computation. FPGA times are the "
            "sum of host-side round-trip transactions and include UART handshake, "
            "payload transfer, completion wait and output reception. They are not "
            "pure FPGA processing latency."
        )

        st.markdown("### Image output comparison")
        sw_cols = st.columns(3)
        for column, title, names in zip(
            sw_cols,
            ("Original", "Software ciphertext", "Software recovered"),
            (["original.png", "input.png"], ["ciphertext.png", "encrypt_output.png"], ["recovered.png"]),
        ):
            image_path = record_image_path(sw_folder, names)
            with column:
                st.markdown(f"**{title}**")
                if image_path:
                    st.image(str(image_path), use_container_width=True)
        fpga_cols = st.columns(3)
        for column, title, names in zip(
            fpga_cols,
            ("Original", "FPGA ciphertext", "FPGA recovered"),
            (["original.png", "input.png"], ["ciphertext.png", "encrypt_output.png"], ["recovered.png"]),
        ):
            image_path = record_image_path(fpga_folder, names)
            with column:
                st.markdown(f"**{title}**")
                if image_path:
                    st.image(str(image_path), use_container_width=True)

        st.warning(
            "The input payloads are matched, but the FPGA records do not store an "
            "algorithm name or cipher parameters. Therefore this page does not claim "
            "that the software and FPGA cipher configurations are algorithmically "
            "identical. Treat statistical differences accordingly."
        )



# ---------------- PREVIOUS RESULTS ARCHIVE ----------------

elif page == "Previous Results":
    st.subheader("Previous Results")
    st.write(
        "Offline demonstration archive for previously completed software and FPGA "
        "experiments. These records are loaded from disk; the FPGA does not need to "
        "be connected to review historical results."
    )

    all_records = load_experiment_records()
    software_records = [item for item in all_records if record_is_software(*item)]
    fpga_records = [item for item in all_records if record_is_fpga(*item)]

    total_col, sw_col, fpga_col = st.columns(3)
    total_col.metric("Archived experiments", len(all_records))
    sw_col.metric("Software runs", len(software_records))
    fpga_col.metric("FPGA runs", len(fpga_records))

    st.info(
        "Demonstration fallback: this page reads saved experiment folders and does "
        "not perform a live hardware transaction. You can present these results even "
        "if the Zybo board is unavailable during your demonstration."
    )

    tab_sw, tab_fpga, tab_compare = st.tabs(
        ["Software results", "FPGA results", "Same-image comparisons"]
    )

    with tab_sw:
        st.markdown("### Archived software experiments")
        if not software_records:
            st.info("No software experiment records were found in the archive.")
        else:
            labels = [record_label(item) for item in software_records]
            selected = st.selectbox(
                "Select a software run",
                range(len(software_records)),
                format_func=lambda i: labels[i],
                key="previous_software_run",
            )
            folder, record = software_records[selected]
            render_record_summary(folder, record, show_images=True)
            st.download_button(
                "Download this software run (ZIP)",
                data=make_evidence_zip(folder),
                file_name=f"{folder.name}_evidence.zip",
                mime="application/zip",
                key="previous_sw_download",
            )

    with tab_fpga:
        st.markdown("### Archived FPGA experiments")
        if not fpga_records:
            st.info("No FPGA experiment records were found in the archive.")
        else:
            labels = [record_label(item) for item in fpga_records]
            selected = st.selectbox(
                "Select an FPGA run",
                range(len(fpga_records)),
                format_func=lambda i: labels[i],
                key="previous_fpga_run",
            )
            folder, record = fpga_records[selected]
            render_record_summary(folder, record, show_images=True)
            st.download_button(
                "Download this FPGA run (ZIP)",
                data=make_evidence_zip(folder),
                file_name=f"{folder.name}_evidence.zip",
                mime="application/zip",
                key="previous_fpga_download",
            )

    with tab_compare:
        st.markdown("### Compare software and FPGA runs of the same image")
        st.caption(
            "A pair is eligible only when both records contain the same input "
            "SHA-256. Each pair is an individual run-to-run comparison."
        )

        software_by_hash = {}
        fpga_by_hash = {}
        for item in software_records:
            digest = item[1].get("input_sha256")
            if digest:
                software_by_hash.setdefault(digest, []).append(item)
        for item in fpga_records:
            digest = item[1].get("input_sha256")
            if digest:
                fpga_by_hash.setdefault(digest, []).append(item)

        common_hashes = sorted(
            set(software_by_hash) & set(fpga_by_hash), reverse=True
        )

        if not common_hashes:
            st.warning(
                "No software/FPGA pairs with matching input SHA-256 were found. "
                "Run both implementations using the exact same 128 × 128 image bytes."
            )
        else:
            pair_count = sum(
                len(software_by_hash[digest]) * len(fpga_by_hash[digest])
                for digest in common_hashes
            )
            st.metric("Same-image run pairs available", pair_count)

            for digest_index, digest in enumerate(common_hashes):
                sw_runs = software_by_hash[digest]
                fpga_runs = fpga_by_hash[digest]
                with st.expander(
                    f"Image {digest[:16]}… · {len(sw_runs)} software × "
                    f"{len(fpga_runs)} FPGA runs",
                    expanded=(digest_index == 0),
                ):
                    st.caption(f"Full input SHA-256: {digest}")
                    pair_options = [
                        (si, fi)
                        for si in range(len(sw_runs))
                        for fi in range(len(fpga_runs))
                    ]
                    pair_index = st.selectbox(
                        "Select run pair",
                        range(len(pair_options)),
                        format_func=lambda i: (
                            f"{sw_runs[pair_options[i][0]][0].name}  ↔  "
                            f"{fpga_runs[pair_options[i][1]][0].name}"
                        ),
                        key=f"previous_pair_{digest[:12]}",
                    )
                    si, fi = pair_options[pair_index]
                    sw_folder, sw = sw_runs[si]
                    fpga_folder, fpga = fpga_runs[fi]

                    st.success("Same input confirmed by identical SHA-256.")
                    sw_entropy, sw_diff, sw_corr = get_record_analysis(sw)
                    fpga_entropy, fpga_diff, fpga_corr = get_record_analysis(fpga)

                    def fmt(value, digits=4):
                        return f"{value:.{digits}f}" if isinstance(value, (int, float)) else "Not recorded"

                    comparison_rows = [
                        {
                            "Metric": "Exact recovery",
                            "Software": "PASS" if sw.get("exact_recovery") is True else ("FAIL" if sw.get("exact_recovery") is False else "Not recorded"),
                            "FPGA": "PASS" if fpga.get("exact_recovery") is True else ("FAIL" if fpga.get("exact_recovery") is False else "Not recorded"),
                        },
                        {"Metric": "Matching pixels", "Software": sw.get("matching_pixels", "Not recorded"), "FPGA": fpga.get("matching_pixels", "Not recorded")},
                        {"Metric": "Mismatched pixels", "Software": sw.get("mismatched_pixels", "Not recorded"), "FPGA": fpga.get("mismatched_pixels", "Not recorded")},
                        {"Metric": "Ciphertext entropy (bits/pixel)", "Software": fmt(sw_entropy), "FPGA": fmt(fpga_entropy)},
                        {"Metric": "NPCR (%)", "Software": fmt(sw_diff.get("npcr_percent")), "FPGA": fmt(fpga_diff.get("npcr_percent"))},
                        {"Metric": "UACI (%)", "Software": fmt(sw_diff.get("uaci_percent")), "FPGA": fmt(fpga_diff.get("uaci_percent"))},
                        {"Metric": "Horizontal correlation", "Software": fmt(sw_corr.get("horizontal")), "FPGA": fmt(fpga_corr.get("horizontal"))},
                        {"Metric": "Vertical correlation", "Software": fmt(sw_corr.get("vertical")), "FPGA": fmt(fpga_corr.get("vertical"))},
                        {"Metric": "Diagonal correlation", "Software": fmt(sw_corr.get("diagonal")), "FPGA": fmt(fpga_corr.get("diagonal"))},
                    ]
                    st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

                    sw_enc = sw.get("encryption_seconds")
                    sw_dec = sw.get("decryption_seconds")
                    fpga_enc = fpga_transaction_seconds(fpga, "encryption")
                    fpga_dec = fpga_transaction_seconds(fpga, "decryption")
                    timing_rows = [
                        {"Operation": "Encryption", "Software computation (s)": fmt(sw_enc, 6), "FPGA UART transaction (s)": fmt(fpga_enc, 6)},
                        {"Operation": "Decryption", "Software computation (s)": fmt(sw_dec, 6), "FPGA UART transaction (s)": fmt(fpga_dec, 6)},
                    ]
                    st.markdown("#### Timing (different measurement boundaries)")
                    st.dataframe(timing_rows, use_container_width=True, hide_index=True)
                    st.caption(
                        "Software values are Python computation times. FPGA values are "
                        "host-side UART round trips including transfer and handshake; "
                        "they are not isolated FPGA-core latency."
                    )

                    st.markdown("#### Same-image output artifacts")
                    sw_cols = st.columns(3)
                    for column, title, names in zip(
                        sw_cols,
                        ("Input image", "Software ciphertext", "Software recovered"),
                        (["original.png", "input.png"], ["ciphertext.png", "encrypt_output.png"], ["recovered.png"]),
                    ):
                        image_path = record_image_path(sw_folder, names)
                        with column:
                            st.markdown(f"**{title}**")
                            if image_path:
                                st.image(str(image_path), use_container_width=True)
                            else:
                                st.caption("Image artifact not archived")
                    fpga_cols = st.columns(3)
                    for column, title, names in zip(
                        fpga_cols,
                        ("Input image", "FPGA ciphertext", "FPGA recovered"),
                        (["original.png", "input.png"], ["ciphertext.png", "encrypt_output.png"], ["recovered.png"]),
                    ):
                        image_path = record_image_path(fpga_folder, names)
                        with column:
                            st.markdown(f"**{title}**")
                            if image_path:
                                st.image(str(image_path), use_container_width=True)
                            else:
                                st.caption("Image artifact not archived")

                    st.warning(
                        "Matching SHA-256 proves the input bytes are identical. It does "
                        "not prove the software and FPGA used identical cipher algorithms "
                        "or parameters; historical FPGA metadata may not record those."
                    )

                    dl_left, dl_right = st.columns(2)
                    with dl_left:
                        st.download_button(
                            "Download software run",
                            data=make_evidence_zip(sw_folder),
                            file_name=f"{sw_folder.name}_evidence.zip",
                            mime="application/zip",
                            key=f"prev_pair_sw_{digest[:12]}_{pair_index}",
                        )
                    with dl_right:
                        st.download_button(
                            "Download FPGA run",
                            data=make_evidence_zip(fpga_folder),
                            file_name=f"{fpga_folder.name}_evidence.zip",
                            mime="application/zip",
                            key=f"prev_pair_fpga_{digest[:12]}_{pair_index}",
                        )


# ---------------- SAVED DEMONSTRATIONS ----------------

elif page == "Saved Demonstrations":
    st.subheader("Saved research demonstrations")
    st.write(
        "Reopen previously recorded experiments. This page reads the experiment "
        "archive from disk and does not execute a new software or FPGA transaction."
    )

    demo_records = [
        item for item in load_experiment_records()
        if item[1].get("exact_recovery") is True
    ]
    if not demo_records:
        st.info("No completed demonstrations are saved yet.")
    else:
        labels = [record_label(item) for item in demo_records]
        selected_index = st.selectbox(
            "Choose a saved demonstration",
            range(len(demo_records)),
            format_func=lambda index: labels[index],
            key="saved_demo_selection_v2",
        )
        folder, data = demo_records[selected_index]
        render_record_summary(folder, data, show_images=True)

        with st.expander("Experiment identifiers and integrity hashes", expanded=False):
            st.write(f"**Run ID:** {data.get('run_id', folder.name)}")
            st.write(f"**Timestamp:** {data.get('timestamp', 'Not recorded')}")
            st.write(f"**Input SHA-256:** {data.get('input_sha256', 'Not recorded')}")
            st.write(f"**Ciphertext SHA-256:** {data.get('ciphertext_sha256', 'Not recorded')}")
            st.write(f"**Recovered SHA-256:** {data.get('recovered_sha256', 'Not recorded')}")
            st.write(f"**Interface:** {data.get('interface', 'Not applicable' if record_is_software(folder, data) else 'Not recorded')}")

        log_file = folder / "execution.log"
        if log_file.is_file():
            with st.expander("Technical execution log", expanded=False):
                st.text(log_file.read_text())

        st.download_button(
            "Download complete demonstration evidence (.zip)",
            data=make_evidence_zip(folder),
            file_name=f"{folder.name}_evidence.zip",
            mime="application/zip",
            key=f"demo_bundle_{folder.name}",
            use_container_width=True,
        )

        st.caption(
            "Saved demonstrations replay archived evidence only. Use Hardware Lab "
            "to perform a new physical transaction with the board connected."
        )


# ---------------- EVIDENCE CENTER ----------------

elif page == "Evidence Center":
    st.subheader("Research evidence repository")
    st.write(
        "A persistent archive of completed experiments and generated build evidence. "
        "Records remain available when navigating between workspaces."
    )

    records = load_experiment_records()
    total = len(records)
    completed = sum(1 for _, record in records if record.get("exact_recovery") is True)
    software_count = sum(1 for folder, record in records if record_is_software(folder, record))
    fpga_count = sum(1 for folder, record in records if record_is_fpga(folder, record))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Archived runs", total)
    m2.metric("Verified recoveries", completed)
    m3.metric("Software runs", software_count)
    m4.metric("FPGA runs", fpga_count)

    if records:
        filter_choice = st.selectbox(
            "Filter archive",
            ["All experiments", "Software only", "FPGA only", "Exact recovery PASS", "Incomplete / legacy"],
            key="evidence_filter",
        )
        filtered = []
        for item in records:
            folder, record = item
            software = record_is_software(folder, record)
            fpga = record_is_fpga(folder, record)
            if filter_choice == "Software only" and not software:
                continue
            if filter_choice == "FPGA only" and not fpga:
                continue
            if filter_choice == "Exact recovery PASS" and record.get("exact_recovery") is not True:
                continue
            if filter_choice == "Incomplete / legacy" and record.get("exact_recovery") is not None:
                continue
            filtered.append(item)

        st.markdown("### Archived experiments")
        for folder, record in filtered:
            label = record_label((folder, record))
            with st.expander(label, expanded=False):
                render_record_summary(folder, record, show_images=False)
                st.download_button(
                    "Download this run's complete evidence (.zip)",
                    data=make_evidence_zip(folder),
                    file_name=f"{folder.name}_evidence.zip",
                    mime="application/zip",
                    key=f"evidence_bundle_{folder.name}",
                )
    else:
        st.info("No experiment metadata has been archived yet.")

    st.divider()
    st.markdown("### Vivado build artifacts")
    artifact_files = sorted(
        (path for path in ARTIFACTS.rglob("*") if path.is_file()),
        key=lambda path: str(path.relative_to(ROOT)),
    )
    if not artifact_files:
        st.info(
            "No Vivado reports or bitstreams have been added yet. "
            "After collecting reports through the Vivado Tcl Console, place them "
            "under artifacts/reports, artifacts/bitstreams or artifacts/logs."
        )
    else:
        for file in artifact_files:
            relative = file.relative_to(ROOT)
            st.download_button(
                f"Download {relative}",
                data=file.read_bytes(),
                file_name=file.name,
                key=f"artifact_{relative}",
                use_container_width=True,
            )


st.divider()
st.caption(
    "Chaos Encryption Research Studio · FPGA experimental platform · "
    "Archived results are historical unless metadata explicitly marks a fresh execution."
)
