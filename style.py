"""Canonical brand styling — injected as CSS via st.markdown."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ============ CANONICAL TOKENS ============ */
:root {
  --bg: #0a1428;
  --bg-2: #0f1b33;
  --bg-3: #142440;
  --line: #1f2d4a;
  --ink: #ffffff;
  --muted: #8fa3c2;
  --subtle: #b8c5da;
  --accent: #4a9eff;
  --accent-2: #7cc4ff;
  --accent-soft: #2563b5;
}

/* ============ GLOBAL ============ */
html, body, [class*="css"], .stApp {
  background-color: var(--bg) !important;
  color: var(--ink) !important;
  font-family: 'Inter Tight', system-ui, sans-serif !important;
}

.main .block-container {
  max-width: 1200px;
  padding-top: 2rem;
  padding-bottom: 4rem;
}

/* Subtle grain background */
.stApp::before {
  content: "";
  position: fixed; inset: 0;
  background-image: radial-gradient(rgba(255,255,255,0.012) 1px, transparent 1px);
  background-size: 3px 3px;
  pointer-events: none;
  z-index: 0;
}

/* ============ TYPOGRAPHY ============ */
h1, h2, h3, h4 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 400 !important;
  letter-spacing: -0.02em !important;
  color: var(--ink) !important;
}

h1 { font-size: clamp(40px, 6vw, 64px) !important; line-height: 1.0 !important; }
h2 { font-size: clamp(28px, 4vw, 40px) !important; line-height: 1.1 !important; margin-top: 1.5rem !important; }
h3 { font-size: clamp(20px, 3vw, 26px) !important; line-height: 1.2 !important; }

h1 em, h2 em, h3 em {
  font-style: italic;
  color: var(--accent);
}

p, li, label, .stMarkdown {
  color: var(--subtle) !important;
  font-family: 'Inter Tight', sans-serif !important;
}

/* mono labels */
.mono-label {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.2em;
  color: var(--accent);
  font-weight: 600;
  margin-bottom: 8px;
  display: block;
}

.muted { color: var(--muted) !important; }
.subtle { color: var(--subtle) !important; }
.ink { color: var(--ink) !important; }

/* ============ HERO ============ */
.hero {
  padding: 24px 0 32px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 32px;
}
.hero .brand {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--subtle);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}
.hero .brand .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px var(--accent);
}
.hero .brand a {
  color: var(--accent);
  text-decoration: none;
  transition: color 0.15s ease;
}
.hero .brand a:hover {
  color: var(--accent-2);
}
.hero h1 {
  margin: 20px 0 12px !important;
  font-size: clamp(48px, 7vw, 84px) !important;
}
.hero .tagline {
  font-family: 'Inter Tight', sans-serif;
  color: var(--subtle);
  font-size: 18px;
  max-width: 640px;
  margin: 0;
}

/* ============ CARDS / SECTIONS ============ */
.card {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 24px;
  margin-bottom: 16px;
}
.card-accent {
  border-left: 2px solid var(--accent);
}

/* Big number display */
.bignum {
  font-family: 'Fraunces', serif;
  font-weight: 400;
  font-size: clamp(36px, 5vw, 52px);
  color: var(--accent-2);
  line-height: 1.0;
  margin: 8px 0;
}
.bignum-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 4px;
}

/* ============ INPUTS ============ */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div {
  background-color: var(--bg-3) !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
  font-family: 'Inter Tight', sans-serif !important;
  border-radius: 3px !important;
}

/* Tighten Streamlit column gaps */
[data-testid="stHorizontalBlock"] {
  gap: 12px !important;
}

/* Reduce excess vertical spacing between elements */
[data-testid="stVerticalBlock"] [data-testid="stElementContainer"] {
  margin-bottom: 4px !important;
}

/* Add Inter Tight monospace numeric tabular feel to inputs */
.stTextInput input,
.stNumberInput input {
  font-feature-settings: "tnum";
}

/* ============ CUSTOM CAP TABLE (matches brand) ============ */
.dl-table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 24px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  overflow: hidden;
  font-family: 'Inter Tight', sans-serif;
}
.dl-table th {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 600;
  padding: 16px 18px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
  background: rgba(74, 158, 255, 0.04);
}
.dl-table th.dl-num {
  text-align: right;
}
.dl-table td {
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  color: var(--subtle);
  font-size: 14px;
  vertical-align: middle;
}
.dl-table tbody tr:last-child td {
  border-bottom: none;
}
.dl-table tbody tr:hover td {
  background: rgba(74, 158, 255, 0.03);
}
.dl-table td.holder-name {
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.005em;
}
.dl-table td.number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.dl-table td.muted {
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  opacity: 0.45;
}
.dl-table .safe-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--accent-2);
  background: rgba(74, 158, 255, 0.08);
  padding: 4px 8px;
  border-radius: 3px;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.dl-table tfoot td {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  border-top: 1px solid var(--line);
  border-bottom: none;
  padding-top: 14px;
}

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stSlider label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  font-weight: 600 !important;
}

.stRadio label, .stCheckbox label {
  color: var(--subtle) !important;
  font-family: 'Inter Tight', sans-serif !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
}

/* Buttons */
.stButton button {
  background: transparent !important;
  border: 1px solid var(--accent) !important;
  color: var(--accent) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  border-radius: 3px !important;
  padding: 8px 16px !important;
  transition: all 0.15s ease !important;
}
.stButton button:hover {
  background: var(--accent) !important;
  color: var(--bg) !important;
}
.stButton button:focus {
  box-shadow: 0 0 0 2px var(--accent-soft) !important;
}

/* Primary action button */
.stButton button[kind="primary"] {
  background: var(--accent) !important;
  color: var(--bg) !important;
}
.stButton button[kind="primary"]:hover {
  background: var(--accent-2) !important;
}

/* ============ SLIDER ============ */
.stSlider > div > div > div {
  background: var(--accent) !important;
}
.stSlider div[role="slider"] {
  background: var(--accent-2) !important;
  box-shadow: 0 0 8px var(--accent) !important;
}

/* ============ DATAFRAME / TABLE ============ */
.stDataFrame, .stTable {
  background: var(--bg-2) !important;
  border: 1px solid var(--line) !important;
  border-radius: 4px !important;
}

/* Pandas dataframe styling */
.stDataFrame [data-testid="stTable"] table {
  font-family: 'Inter Tight', sans-serif !important;
  color: var(--ink) !important;
}

/* ============ DIVIDERS ============ */
hr {
  border: none !important;
  border-top: 1px solid var(--line) !important;
  margin: 32px 0 !important;
}

/* ============ TABS ============ */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  border-radius: 0 !important;
  padding: 12px 20px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
}

/* ============ EXPANDER ============ */
.streamlit-expanderHeader {
  background: var(--bg-2) !important;
  border: 1px solid var(--line) !important;
  border-radius: 3px !important;
  color: var(--ink) !important;
  font-family: 'Inter Tight', sans-serif !important;
}

/* ============ FOOTER ============ */
.footer {
  margin-top: 60px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  text-align: center;
}
.footer a {
  color: var(--accent);
  text-decoration: none;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Section numbering */
.sec-num {
  font-family: 'JetBrains Mono', monospace;
  color: var(--accent);
  font-size: 11px;
  letter-spacing: 0.3em;
  margin-bottom: 8px;
  text-transform: uppercase;
}
</style>
"""


HERO_HTML = """
<div class="hero">
  <div class="brand">
    <span class="dot"></span>
    <span><a href="https://canonical.cc" target="_blank" rel="noopener">Canonical</a> &mdash; Dilution Lab</span>
  </div>
  <h1>Dilution <em>Lab</em></h1>
  <p class="tagline">See what every term sheet actually costs you. Model SAFEs, priced rounds, option pools, and exit math, all in your browser.</p>
</div>
"""
