import streamlit as st
import json
import csv
import io
import time
import random
import os
import sys
import shutil
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.graph import graph
except ImportError:
    graph = None

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LexExtract · Legal Document AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Mono:wght@300;400;500&family=Jost:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

/* Theme tokens: bind directly to Streamlit active theme values */
:root {
    /* ── Adaptive Core Tokens (Fail-safe fallbacks: System Colors) ── */
    --lex-text: var(--st-text-color, CanvasText);
    --lex-bg: var(--st-background-color, Canvas);
    --lex-sidebar-bg: var(--st-secondary-background-color, color-mix(in srgb, var(--lex-text) 5%, var(--lex-bg)));
    
    /* ── Reactive Brand Accent ── */
    /* This makes the gold darken slightly on light backgrounds for readability */
    --lex-accent-base: #f0c96d;
    --lex-accent: color-mix(in srgb, var(--lex-accent-base) 82%, var(--lex-text));
    
    /* ── High Contrast Transparency System ── */
    --lex-bg-grad-1: color-mix(in srgb, var(--lex-accent) 10%, transparent);
    --lex-bg-grad-2: color-mix(in srgb, var(--lex-text) 6%, transparent);
    
    /* Increased border opacity for light mode visibility */
    --lex-card-bg: color-mix(in srgb, var(--lex-text) 3%, transparent);
    --lex-card-border: color-mix(in srgb, var(--lex-accent) 40%, transparent);
    --lex-line-soft: color-mix(in srgb, var(--lex-accent) 30%, transparent);
    --lex-uploader-bg: color-mix(in srgb, var(--lex-accent) 5%, transparent);
    
    --lex-grid-bg: color-mix(in srgb, var(--lex-text) 2%, transparent);
    --lex-grid-border: color-mix(in srgb, var(--lex-text) 20%, transparent);
    
    --lex-input-bg: color-mix(in srgb, var(--lex-bg) 98%, var(--lex-text));
    --lex-input-border: color-mix(in srgb, var(--lex-accent) 50%, transparent);
    --lex-placeholder: color-mix(in srgb, var(--lex-text) 50%, transparent);
    
    --lex-btn-bg-hover: color-mix(in srgb, var(--lex-accent) 15%, transparent);
    --lex-divider: color-mix(in srgb, var(--lex-accent) 35%, transparent);
    
    /* Specialized Adaptive Tokens */
    --lex-json-key: color-mix(in srgb, var(--lex-accent) 85%, var(--lex-text));
    --lex-json-string: #2ea35d;
    --lex-json-number: #3d7fe6;
    
    --lex-success-bg: color-mix(in srgb, #2ea35d 12%, transparent);
    --lex-error-bg: color-mix(in srgb, #cf4d3c 12%, transparent);
    
    --lex-scroll-thumb: color-mix(in srgb, var(--lex-accent) 45%, transparent);
}



/* ── Base Transparency Layer ── */
.stApp, [data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* Apply background to the underlying body/html or the specific cache-container if possible, 
   but the safest is to let Streamlit show it. We'll add our gradients only. */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: -1;
    background-image: 
        radial-gradient(ellipse 60% 40% at 70% 10%, var(--lex-bg-grad-1) 0%, transparent 60%),
        radial-gradient(ellipse 50% 60% at 10% 80%, var(--lex-bg-grad-2) 0%, transparent 60%);
    pointer-events: none;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { 
    background-color: var(--lex-sidebar-bg) !important;
}



.block-container { padding: 2.5rem 3rem 4rem !important; max-width: 1280px !important; }

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    color: var(--lex-text) !important;
}

/* ── Hero / Masthead ── */
.lex-masthead {
    display: flex;
    align-items: flex-end;
    gap: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--lex-line-soft);
    margin-bottom: 0.3rem;
}
.lex-glyph {
    font-size: 2.6rem;
    line-height: 1;
    filter: drop-shadow(0 0 12px rgba(180, 148, 72, 0.45));
}
.lex-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2.8rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.08em !important;
    color: var(--lex-accent) !important;
    line-height: 1 !important;
    margin: 0 !important;
}
.lex-title span { font-weight: 600; color: var(--lex-accent-strong); }
.lex-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--lex-accent-muted);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}
.lex-badge {
    margin-left: auto;
    margin-bottom: 0.4rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--lex-accent-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border: 1px solid var(--lex-line-soft);
    padding: 0.25rem 0.7rem;
    border-radius: 2px;
}

/* ── Section Cards ── */
.lex-card {
    background: var(--lex-card-bg);
    border: 1px solid var(--lex-card-border);
    border-radius: 4px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.4rem;
    position: relative;
    overflow: hidden;
}
.lex-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, rgba(180,148,72,0.65) 0%, rgba(180,148,72,0.16) 60%, transparent 100%);
}
.lex-card-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--lex-accent-muted);
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.lex-card-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--lex-line-soft);
    margin-left: 0.4rem;
}

/* ── File Upload ── */
[data-testid="stFileUploader"] {
    background: var(--lex-uploader-bg) !important;
    border: 1px dashed var(--lex-card-border) !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(180,148,72,0.62) !important;
}
[data-testid="stFileUploader"] label {
    color: var(--lex-accent-muted) !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 400 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
}

/* ── Attribute Pills ── */
.attr-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(180,148,72,0.10);
    border: 1px solid var(--lex-card-border);
    border-radius: 2px;
    padding: 0.3rem 0.75rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: var(--lex-accent);
    margin: 0.2rem;
}
.attr-pill-dot {
    width: 5px; height: 5px;
    background: rgba(180,148,72,0.72);
    border-radius: 50%;
}
.attr-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.8rem;
    padding: 0.9rem 1rem;
    background: var(--lex-grid-bg);
    border-radius: 3px;
    border: 1px solid var(--lex-grid-border);
    min-height: 52px;
}
.attr-grid-empty {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--lex-text-faint);
    letter-spacing: 0.1em;
    align-self: center;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    background: var(--lex-input-bg) !important;
    border: 1px solid var(--lex-input-border) !important;
    border-radius: 3px !important;
    color: var(--lex-text) !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(180,148,72,0.68) !important;
    box-shadow: 0 0 0 3px rgba(180,148,72,0.16) !important;
}
[data-testid="stTextInput"] input::placeholder {
    color: var(--lex-placeholder) !important;
}
[data-testid="stTextInput"] label {
    color: var(--lex-text-soft) !important;
    font-size: 0.78rem !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stSelectbox"] > label {
    color: var(--lex-text-soft) !important;
    font-size: 0.78rem !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: var(--lex-input-bg) !important;
    border: 1px solid var(--lex-input-border) !important;
    color: var(--lex-text) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] span {
    color: var(--lex-text) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid rgba(180,148,72,0.46) !important;
    color: var(--lex-text) !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    border-radius: 3px !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button:hover {
    background: var(--lex-btn-bg-hover) !important;
    border-color: rgba(180,148,72,0.7) !important;
    color: var(--lex-text) !important;
}

/* Compact Buttons: Presets, Remove, and Clear All */
div[class*="st-key-preset_"] [data-testid="stButton"] button,
div.st-key-remove_btn [data-testid="stButton"] button,
div.st-key-clear_btn [data-testid="stButton"] button {
    padding: 2px 6px !important;
    font-size: 0.5rem !important;
    min-height: 40px !important;
    height: 40px !important;
    line-height: 1 !important;
    font-weight: 400 !important;
    transition: all 0.3s ease !important;
}

/* Blurred state for already-added presets */
div[class*="st-key-preset_"] [data-testid="stButton"] button:disabled {
    opacity: 0.3 !important;
    filter: blur(1.5px) !important;
    cursor: not-allowed !important;
    border-color: rgba(180,148,72,0.1) !important;
}

/* Process button: primary style */
.process-btn [data-testid="stButton"] button {
    background: linear-gradient(135deg, rgba(180,148,72,0.9) 0%, rgba(212,183,106,0.85) 100%) !important;
    border: none !important;
    color: #161310 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 2rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
.process-btn [data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, rgba(200,168,82,1) 0%, rgba(232,201,122,1) 100%) !important;
    color: #161310 !important;
    box-shadow: 0 4px 20px rgba(180,148,72,0.3) !important;
}

/* ── Progress / Status ── */
.status-step {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.6rem 0.9rem;
    border-radius: 3px;
    margin-bottom: 0.5rem;
    font-family: 'Jost', sans-serif;
    font-size: 0.84rem;
    letter-spacing: 0.03em;
    transition: all 0.3s;
}
.status-step.pending  { background: var(--lex-grid-bg); color: var(--lex-text-soft); border: 1px solid var(--lex-grid-border); }
.status-step.active   { background: rgba(180,148,72,0.12); color: var(--lex-accent); border: 1px solid var(--lex-card-border); }
.status-step.done     { background: var(--lex-success-bg); color: var(--lex-success); border: 1px solid var(--lex-success-border); }
.status-step.error    { background: var(--lex-error-bg); color: var(--lex-error); border: 1px solid var(--lex-error-border); }

.step-icon { font-size: 1rem; width: 1.2rem; text-align: center; }
.step-label { flex: 1; }
.step-time  { font-family: 'DM Mono', monospace; font-size: 0.66rem; opacity: 0.6; }
.step-detail { font-size: 0.74rem; color: var(--lex-text-soft); opacity: 0.95; }

/* ── Progress bar override ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #b49448 0%, #d4b76a 100%) !important;
    border-radius: 2px !important;
}
[data-testid="stProgress"] > div {
    background: var(--lex-progress-track) !important;
    border-radius: 2px !important;
    height: 4px !important;
}

/* ── JSON Output ── */
.json-output {
    background: var(--lex-json-bg);
    border: 1px solid var(--lex-card-border);
    border-radius: 4px;
    padding: 1.4rem 1.6rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.7;
    color: var(--lex-json-text);
    overflow-x: auto;
    white-space: pre;
    position: relative;
}
.json-key    { color: var(--lex-json-key); }
.json-string { color: var(--lex-json-string); }
.json-number { color: var(--lex-json-number); }
.json-null   { color: var(--lex-text-faint); font-style: italic; }
.json-bool   { color: var(--lex-json-bool); }

/* ── Download Buttons ── */
.dl-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.8rem;
    margin-top: 0.6rem;
}
.dl-btn-wrap [data-testid="stDownloadButton"] button {
    width: 100% !important;
    background: var(--lex-download-bg) !important;
    border: 1px solid var(--lex-download-border) !important;
    color: var(--lex-text-muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.73rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 3px !important;
    padding: 0.5rem 0.5rem !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.dl-btn-wrap [data-testid="stDownloadButton"] button:hover {
    background: rgba(180,148,72,0.08) !important;
    border-color: rgba(180,148,72,0.35) !important;
    color: var(--lex-accent) !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--lex-divider) !important;
    margin: 1.4rem 0 !important;
}

/* ── File chip ── */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(180,148,72,0.06);
    border: 1px solid var(--lex-card-border);
    border-radius: 2px;
    padding: 0.25rem 0.6rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--lex-accent);
    margin: 0.2rem;
}
.file-chip-meta { color: var(--lex-text-soft); }

/* ── Spinner override ── */
[data-testid="stSpinner"] {
    color: var(--lex-accent) !important;
}
.stSpinner > div {
    border-top-color: var(--lex-accent) !important;
}

/* ── Info/success boxes ── */
[data-testid="stAlert"] {
    background: rgba(180,148,72,0.07) !important;
    border: 1px solid var(--lex-card-border) !important;
    border-radius: 3px !important;
    color: var(--lex-text) !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: var(--lex-download-bg);
    border: 1px solid var(--lex-card-border);
    border-radius: 4px;
    padding: 0.9rem 1rem;
}
[data-testid="stMetricLabel"] { color: var(--lex-accent-muted) !important; font-family: 'DM Mono', monospace !important; font-size: 0.68rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"] { color: var(--lex-text) !important; font-family: 'Cormorant Garamond', serif !important; font-size: 1.9rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--lex-scroll-thumb); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--lex-scroll-thumb-hover); }

/* ── Footer ── */
.lex-footer {
    text-align: center;
    padding-top: 2rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: var(--lex-text-faint);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    border-top: 1px solid var(--lex-line-soft);
}

/* ── Utility Text ── */
.lex-muted-note {
    font-size: 0.78rem;
    color: var(--lex-text-soft);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.06em;
    margin-top: 0.7rem;
}
.lex-card-help {
    font-size: 0.8rem;
    color: var(--lex-text-muted);
    margin-bottom: 1rem;
    line-height: 1.55;
}
.lex-preset-label {
    font-size: 0.7rem;
    color: var(--lex-accent-muted);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0.8rem 0 0.4rem;
}
.lex-warning-note {
    font-size: 0.76rem;
    color: var(--lex-text-soft);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.06em;
    margin-bottom: 0.5rem;
}
.pipeline-done {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--lex-success);
    letter-spacing: 0.08em;
    margin-top: 0.5rem;
}

/* ── Empty State ── */
.lex-empty-state {
    min-height: 380px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 1rem;
}
.lex-empty-icon {
    font-size: 3.2rem;
    filter: drop-shadow(0 0 20px rgba(180,148,72,0.3));
}
.lex-empty-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.5rem;
    font-weight: 300;
    color: var(--lex-accent);
    letter-spacing: 0.06em;
}
.lex-empty-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--lex-text-soft);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}
.lex-empty-note-box {
    margin-top: 0.5rem;
    padding: 1rem 1.6rem;
    border: 1px solid var(--lex-card-border);
    border-radius: 3px;
    max-width: 320px;
    background: var(--lex-grid-bg);
}
.lex-empty-note-text {
    font-family: 'Jost', sans-serif;
    font-size: 0.8rem;
    color: var(--lex-text-muted);
    line-height: 1.6;
}
.lex-empty-highlight {
    color: var(--lex-accent);
}

/* ── Cols gap fix ── */
[data-testid="column"] { padding: 0 0.4rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Session State Init ─────────────────────────────────────────────────────────
if "attributes"      not in st.session_state: st.session_state.attributes      = {}
if "new_attr"        not in st.session_state: st.session_state.new_attr        = ""
if "new_desc"        not in st.session_state: st.session_state.new_desc        = ""
if "results"         not in st.session_state: st.session_state.results         = None
if "processing_done" not in st.session_state: st.session_state.processing_done = False
if "show_processing" not in st.session_state: st.session_state.show_processing = False

# ── Helpers ───────────────────────────────────────────────────────────────────
def render_highlighted_json(obj: dict) -> str:
    raw = json.dumps(obj, indent=2)
    import re
    def replacer(m):
        val = m.group(0)
        if val.startswith('"') and val.endswith('":'):
            return f'<span class="json-key">{val}</span>'
        elif val.startswith('"'):
            return f'<span class="json-string">{val}</span>'
        elif val in ('true','false'):
            return f'<span class="json-bool">{val}</span>'
        elif val == 'null':
            return f'<span class="json-null">{val}</span>'
        else:
            return f'<span class="json-number">{val}</span>'
    highlighted = re.sub(r'"[^"]*":|"[^"]*"|\b(true|false|null)\b|-?\d+\.?\d*', replacer, raw)
    return highlighted


def results_to_csv(results: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    # Collect all attribute keys
    all_attrs = []
    for doc_data in results.values():
        for k in doc_data:
            if k not in all_attrs:
                all_attrs.append(k)
    writer.writerow(["Document"] + all_attrs)
    for fname, doc_data in results.items():
        row = [fname] + [doc_data.get(a, "") for a in all_attrs]
        writer.writerow(row)
    return output.getvalue()


def results_to_xlsx(results: dict) -> bytes:
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Extracted Attributes"

        # Gather attrs
        all_attrs = []
        for doc_data in results.values():
            for k in doc_data:
                if k not in all_attrs: all_attrs.append(k)

        headers = ["Document"] + all_attrs
        gold_fill = PatternFill("solid", fgColor="1A1A1A")
        header_font = Font(bold=True, color="C8A84A", name="Calibri", size=10)
        thin_border = Border(
            bottom=Side(style='thin', color='2a2a2a'),
            right=Side(style='thin', color='2a2a2a')
        )

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = gold_fill
            cell.alignment = Alignment(horizontal='left', vertical='center')
            cell.border = thin_border
            ws.column_dimensions[cell.column_letter].width = max(18, len(h) + 4)

        data_font = Font(color="D0C8BC", name="Calibri", size=10)
        for row_idx, (fname, doc_data) in enumerate(results.items(), 2):
            row_vals = [fname] + [doc_data.get(a, "") for a in all_attrs]
            fill = PatternFill("solid", fgColor="0F0F0F") if row_idx % 2 == 0 else PatternFill("solid", fgColor="131313")
            for col_idx, val in enumerate(row_vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = data_font
                cell.fill = fill
                cell.alignment = Alignment(horizontal='left', vertical='center')
                cell.border = thin_border

        ws.freeze_panes = "B2"
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    except ImportError:
        return b""


def results_to_txt(results: dict) -> str:
    lines = ["=" * 68]
    lines.append("  LEXEXTRACT — LEGAL DOCUMENT ATTRIBUTE EXTRACTION REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%B %d, %Y  %H:%M UTC')}")
    lines.append("=" * 68)
    for fname, doc_data in results.items():
        lines.append(f"\n  DOCUMENT: {fname}")
        lines.append("  " + "─" * 62)
        for attr, val in doc_data.items():
            lines.append(f"  {attr:<30}  {val}")
        lines.append("")
    lines.append("=" * 68)
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

# ── Masthead ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lex-masthead">
  <div class="lex-glyph">⚖️</div>
  <div>
    <div class="lex-title">Lex<span>Extract</span></div>
    <div class="lex-tagline">Legal Document · Attribute Extraction System</div>
  </div>
  <div class="lex-badge">v1.0 · AI-Powered</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ── Two-column main layout ─────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.05], gap="large")

# ╔══════════════════════════════════════════════════════╗
# ║  LEFT — INPUTS                                       ║
# ╚══════════════════════════════════════════════════════╝
with left_col:

    # ── 1. File Upload ───────────────────────────────────
    # st.markdown('<div class="lex-card">', unsafe_allow_html=True)
    st.markdown('<div class="lex-card-title">📄 &nbsp;Document Upload</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drop one or more legal PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Supported format: PDF. Multiple files accepted.",
    )

    if uploaded_files:
        chips_html = "".join(
            f'<span class="file-chip">📄 {f.name} <span class="file-chip-meta">· {f.size // 1024} KB</span></span>'
            for f in uploaded_files
        )
        st.markdown(f"<div style='margin-top:0.7rem'>{chips_html}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Files", len(uploaded_files))
        with c2: st.metric("Total Size", f"{sum(f.size for f in uploaded_files) // 1024} KB")
        with c3: st.metric("Format", "PDF")
    else:
        st.markdown(
            "<p class='lex-muted-note'>No documents uploaded yet.</p>",
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2. Attribute Builder ──────────────────────────────
    # st.markdown('<div class="lex-card">', unsafe_allow_html=True)
    st.markdown('<div class="lex-card-title">🏷️ &nbsp;Attribute Fields</div>', unsafe_allow_html=True)

    st.markdown(
        "<p class='lex-card-help'>"
        "Define the fields you want extracted from each document with a short description. "
        "Each attribute name will become a key in the output.</p>",
        unsafe_allow_html=True
    )

    # Attribute display
    if st.session_state.attributes:
        pills_html = "".join(
            f'<span class="attr-pill" title="{v}"><span class="attr-pill-dot"></span>{k}</span>'
            for k, v in st.session_state.attributes.items()
        )
        st.markdown(f'<div class="attr-grid">{pills_html}</div>', unsafe_allow_html=True)

        rem_col, btn_rem_col, btn_clr_col = st.columns([2.2, 1, 1])
        with rem_col:
            to_remove = st.selectbox(
                "Remove attribute",
                options=["— select to remove —"] + list(st.session_state.attributes.keys()),
                label_visibility="visible",
                key="remove_sel"
            )
        with btn_rem_col:
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            if st.button("✕ Remove", key="remove_btn", use_container_width=True):
                if to_remove != "— select to remove —":
                    del st.session_state.attributes[to_remove]
                    st.rerun()
        with btn_clr_col:
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            if st.button("⊘ Clear All", key="clear_btn", use_container_width=True):
                st.session_state.attributes = {}
                st.session_state.results = None
                st.session_state.processing_done = False
                st.rerun()
    else:
        st.markdown(
            '<div class="attr-grid"><span class="attr-grid-empty">No attributes defined yet · add some below</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    attr_col, desc_col, btn_col = st.columns([2, 3, 1.5], gap="small")
    with attr_col:
        new_attr = st.text_input(
            "Attribute name",
            key="attr_input",
            placeholder="Attribute Name",
            label_visibility="collapsed"
        )
    with desc_col:
        new_desc = st.text_input(
            "Attribute description",
            key="desc_input",
            placeholder="Description of the Attribute",
            label_visibility="collapsed"
        )
    with btn_col:
        # st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
        add_clicked = st.button("＋ Add", use_container_width=True, key="add_btn")

    if add_clicked:
        attr = new_attr.strip()
        desc = new_desc.strip()
        if attr and attr not in st.session_state.attributes:
            st.session_state.attributes[attr] = desc
            st.rerun()
        elif attr in st.session_state.attributes:
            st.warning(f'"{attr}" is already in your list.')

    # Quick-add presets
    st.markdown(
        "<p class='lex-preset-label'>Quick-add presets</p>",
        unsafe_allow_html=True
    )
    
    preset_attrs = {
        "Party Name": "Name of the entity or individual",
        "Contract Date": "Date when the contract was signed",
        "Jurisdiction": "State or jurisdiction whose laws govern the agreement",
        "Payment Terms": "Payment terms or milestones",
        "Termination Clause": "Details of the termination clause and notice period",
        "Governing Law": "State or jurisdiction whose laws govern the agreement",
        "Liability Cap": "The maximum liability limit",
        "Signatory": "Name and title of the authorized signatory"
    }

    preset_cols = st.columns(4)
    for i, (preset, desc) in enumerate(preset_attrs.items()):
        is_added = preset in st.session_state.attributes
        with preset_cols[i % 4]:
            if st.button(preset, key=f"preset_{i}", use_container_width=True, disabled=is_added):
                st.session_state.attributes[preset] = desc
                st.rerun()

    # ── 3. Process Button ─────────────────────────────────
    can_process = bool(uploaded_files and st.session_state.attributes)
    if not can_process:
        missing = []
        if not uploaded_files:           missing.append("upload at least one PDF")
        if not st.session_state.attributes: missing.append("add at least one attribute")
        st.markdown(
            f"<p class='lex-warning-note'>⚠ To continue: {' & '.join(missing)}.</p>",
            unsafe_allow_html=True
        )

    st.markdown('<div class="process-btn">', unsafe_allow_html=True)
    process_clicked = st.button(
        "⚡ Process Documents",
        key="process_btn",
        disabled=not can_process,
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════╗
# ║  RIGHT — PROCESSING + RESULTS                        ║
# ╚══════════════════════════════════════════════════════╝
with right_col:

    if process_clicked and can_process:
        st.session_state.processing_done = False
        st.session_state.results = None
        st.session_state.show_processing = True

    if st.session_state.show_processing and not st.session_state.processing_done:
        # ── Processing Panel ──────────────────────────────
        # st.markdown('<div class="lex-card">', unsafe_allow_html=True)
        st.markdown('<div class="lex-card-title">⚙️ &nbsp;Processing Pipeline</div>', unsafe_allow_html=True)

        steps = [
            ("Uploading files",            "Transmitting documents to extraction service…"),
            ("Processing documents",       "Parsing structure, layout & text layers…"),
            ("Extracting attributes",      "Running NLP inference on target fields…"),
            ("Refining & validating",      "Cross-referencing and normalising results…"),
        ]

        prog_bar    = st.progress(0)
        step_slots  = [st.empty() for _ in steps]
        timing_slot = st.empty()

        def render_step(slot, label, detail, state):
            icons = {"pending": "○", "active": "◎", "done": "✓", "error": "✗"}
            slot.markdown(
                f'<div class="status-step {state}">'
                f'<span class="step-icon">{icons[state]}</span>'
                f'<span class="step-label"><strong>{label}</strong>'
                f'<br><span class="step-detail">{detail}</span></span>'
                f'</div>',
                unsafe_allow_html=True
            )

        for i, (label, detail) in enumerate(steps):
            render_step(step_slots[i], label, detail, "pending")

        start_time = time.time()
        for i, (label, detail) in enumerate(steps):
            render_step(step_slots[i], label, detail, "active")
            delay = random.uniform(0.6, 1.1)
            for tick in range(10):
                frac = (i + (tick + 1) / 10) / len(steps)
                prog_bar.progress(frac)
                time.sleep(delay / 10)
            render_step(step_slots[i], label, detail, "done")

        prog_bar.progress(1.0)
        elapsed = time.time() - start_time
        timing_slot.markdown(
            f"<p class='pipeline-done'>✓ Pipeline completed in {elapsed:.1f}s</p>",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Run extraction through backend graph
        input_dir = "input"
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)
        os.makedirs(input_dir, exist_ok=True)
        
        real_results = {}
        for f in uploaded_files:
            file_path = os.path.join(input_dir, f.name)
            with open(file_path, "wb") as file_out:
                file_out.write(f.getbuffer())
            
            inputs = {
                "pdf_path": file_path,
                "pdf_text": "",
                "extracted_fields": {},
                "fields_to_retry": [],
                "retry_count": 0,
                "final_output": {},
                "messages": [],
                "attributes_to_extract": st.session_state.attributes
            }
            
            try:
                if graph:
                    final_state = graph.invoke(inputs)
                    real_results[f.name] = final_state.get("final_output", {})
                else:
                    real_results[f.name] = {"error": "Graph import failed."}
            except Exception as e:
                real_results[f.name] = {"error": str(e)}

        st.session_state.results         = real_results
        st.session_state.processing_done = True
        st.session_state.show_processing = False
        st.rerun()

    elif st.session_state.processing_done and st.session_state.results:
        results = st.session_state.results

        # ── Summary Metrics ────────────────────────────────
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Documents", len(results))
        with m2: st.metric("Attributes", len(st.session_state.attributes))
        with m3: st.metric("Fields Extracted", len(results) * len(st.session_state.attributes))

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        # ── JSON Results ───────────────────────────────────
        # st.markdown('<div class="lex-card">', unsafe_allow_html=True)
        st.markdown('<div class="lex-card-title">📋 &nbsp;Extraction Results</div>', unsafe_allow_html=True)
        highlighted = render_highlighted_json(results)
        st.markdown(f'<div class="json-output">{highlighted}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Export ─────────────────────────────────────────
        # st.markdown('<div class="lex-card">', unsafe_allow_html=True)
        st.markdown('<div class="lex-card-title">⬇️ &nbsp;Export Results</div>', unsafe_allow_html=True)

        json_bytes  = json.dumps(results, indent=2).encode()
        csv_str     = results_to_csv(results)
        xlsx_bytes  = results_to_xlsx(results)
        txt_str     = results_to_txt(results)
        ts          = datetime.now().strftime("%Y%m%d_%H%M")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown('<div class="dl-btn-wrap">', unsafe_allow_html=True)
            st.download_button("⬇ JSON", data=json_bytes,  file_name=f"lexextract_{ts}.json", mime="application/json", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with d2:
            st.markdown('<div class="dl-btn-wrap">', unsafe_allow_html=True)
            st.download_button("⬇ CSV",  data=csv_str,     file_name=f"lexextract_{ts}.csv",  mime="text/csv",         use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with d3:
            st.markdown('<div class="dl-btn-wrap">', unsafe_allow_html=True)
            if xlsx_bytes:
                st.download_button("⬇ XLSX", data=xlsx_bytes, file_name=f"lexextract_{ts}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.button("⬇ XLSX", disabled=True, use_container_width=True, help="Install openpyxl to enable XLSX export")
            st.markdown("</div>", unsafe_allow_html=True)
        with d4:
            st.markdown('<div class="dl-btn-wrap">', unsafe_allow_html=True)
            st.download_button("⬇ TXT",  data=txt_str,     file_name=f"lexextract_{ts}.txt",  mime="text/plain",       use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("↺ New Extraction", key="reset_btn"):
            st.session_state.results         = None
            st.session_state.processing_done = False
            st.session_state.show_processing = False
            st.rerun()

    else:
        # ── Empty State ────────────────────────────────────
        st.markdown("""
        <div class="lex-card lex-empty-state">
          <div class="lex-empty-icon">⚖️</div>
          <div>
            <div class="lex-empty-title">Awaiting Documents</div>
            <div class="lex-empty-subtitle">
              Upload PDFs · Define attributes · Extract
            </div>
          </div>
          <div class="lex-empty-note-box">
            <div class="lex-empty-note-text">
              Configure your extraction pipeline on the left, then click
              <strong class="lex-empty-highlight">Process Documents</strong>
              to begin.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lex-footer">
  LexExtract · Legal Document Intelligence Platform ·
  Frontend UI · By Atharva Kawale ·
  © 2026
</div>
""", unsafe_allow_html=True)
