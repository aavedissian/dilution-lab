"""
Dilution Lab — by Canonical.

A web app that lets founders model dilution, fundraising, and exit math
across multi-round funding scenarios.
"""

import streamlit as st
import pandas as pd
import math

from capmath import (
    Round,
    simulate,
    waterfall_all_common,
    waterfall_with_prefs,
)
from style import CSS, HERO_HTML


# =============================================================================
# Page config + style
# =============================================================================
st.set_page_config(
    page_title="Dilution Lab · Canonical",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO_HTML, unsafe_allow_html=True)


# =============================================================================
# State initialization
# =============================================================================
def _clear_widget_state():
    """Drop cached widget state so a new scenario actually appears in inputs."""
    prefixes = (
        "samt_", "scap_", "sname_",
        "iname_", "iamt_",
        "pre_", "raise_", "pool_",
        "rname_", "rkind_",
        "fname_", "fpct_",
        "pool_input",
    )
    for k in list(st.session_state.keys()):
        if any(k.startswith(p) for p in prefixes):
            del st.session_state[k]


def init_state():
    if "founders" not in st.session_state:
        load_template()
    if "rounds" not in st.session_state:
        st.session_state.rounds = []
    if "initial_pool_pct" not in st.session_state:
        st.session_state.initial_pool_pct = 0.10


def load_template():
    """Realistic seed-stage starting state."""
    st.session_state.founders = [
        {"name": "Founder A", "pct": 50.0},
        {"name": "Founder B", "pct": 50.0},
    ]
    st.session_state.initial_pool_pct = 0.10
    st.session_state.rounds = [
        {
            "name": "Pre-seed",
            "kind": "SAFE",
            "safes": [
                {"name": "Lead Angel", "amount": 1_000_000, "cap": 10_000_000},
                {"name": "Operator Angel", "amount": 250_000, "cap": 8_000_000},
            ],
            "pre_money": 0,
            "raise_amount": 0,
            "option_pool_pct_post": 0.10,
            "investors": [],
        },
        {
            "name": "Seed",
            "kind": "PRICED",
            "safes": [],
            "pre_money": 20_000_000,
            "raise_amount": 5_000_000,
            "option_pool_pct_post": 0.12,
            "investors": [{"name": "Seed Lead", "amount": 5_000_000}],
        },
    ]


def load_blank():
    st.session_state.founders = [{"name": "", "pct": 100.0}]
    st.session_state.initial_pool_pct = 0.10
    st.session_state.rounds = []


def load_stacked_example():
    """Showcases stacked SAFEs at different caps + multiple rounds."""
    st.session_state.founders = [
        {"name": "CEO", "pct": 40.0},
        {"name": "CTO", "pct": 40.0},
        {"name": "Chief Scientist", "pct": 20.0},
    ]
    st.session_state.initial_pool_pct = 0.10
    st.session_state.rounds = [
        {
            "name": "Pre-seed",
            "kind": "SAFE",
            "safes": [
                {"name": "Tier-1 Seed Fund", "amount": 1_500_000, "cap": 15_000_000},
                {"name": "Strategic Angel 1", "amount": 250_000, "cap": 12_000_000},
                {"name": "Strategic Angel 2", "amount": 250_000, "cap": 12_000_000},
                {"name": "Industry Operator", "amount": 100_000, "cap": 10_000_000},
            ],
            "pre_money": 0,
            "raise_amount": 0,
            "option_pool_pct_post": 0.10,
            "investors": [],
        },
        {
            "name": "Seed",
            "kind": "PRICED",
            "safes": [],
            "pre_money": 30_000_000,
            "raise_amount": 10_000_000,
            "option_pool_pct_post": 0.12,
            "investors": [{"name": "Seed Lead VC", "amount": 10_000_000}],
        },
        {
            "name": "Series A",
            "kind": "PRICED",
            "safes": [],
            "pre_money": 80_000_000,
            "raise_amount": 20_000_000,
            "option_pool_pct_post": 0.15,
            "investors": [{"name": "Series A Lead", "amount": 20_000_000}],
        },
    ]


init_state()


# =============================================================================
# Helpers
# =============================================================================
def fmt_money(x):
    if x >= 1_000_000_000:
        return f"${x/1_000_000_000:.1f}B"
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"


def fmt_pct(x):
    return f"{x*100:.2f}%"


# -----------------------------------------------------------------------------
# Money input helper: text_input with thousands separators + M/K/B shortcut
# -----------------------------------------------------------------------------
def parse_money(s: str) -> int:
    """Parse strings like '1,000,000', '$5M', '500k' into int dollars."""
    if not s:
        return 0
    s = str(s).replace(",", "").replace("$", "").replace(" ", "").upper()
    if not s:
        return 0
    mult = 1
    if s.endswith("B"):
        mult, s = 1_000_000_000, s[:-1]
    elif s.endswith("M"):
        mult, s = 1_000_000, s[:-1]
    elif s.endswith("K"):
        mult, s = 1_000, s[:-1]
    try:
        return int(float(s) * mult)
    except (ValueError, TypeError):
        return 0


def _reformat_money_cb(key):
    """on_change callback: reformat the stored value with commas after blur."""
    raw = st.session_state.get(key, "")
    parsed = parse_money(raw)
    st.session_state[key] = f"{parsed:,}" if parsed else ""


def dollar_input(label, value, key, label_visibility="visible", placeholder=""):
    """Text input that accepts numbers with commas/M/K/B and returns int dollars."""
    if key not in st.session_state:
        st.session_state[key] = f"{int(value):,}" if value else ""
    raw = st.text_input(
        label,
        key=key,
        label_visibility=label_visibility,
        on_change=_reformat_money_cb,
        args=(key,),
        placeholder=placeholder,
    )
    return parse_money(raw)


def rounds_to_objects(round_dicts):
    """Convert session state dicts to capmath Round objects."""
    out = []
    for r in round_dicts:
        if r["kind"] == "SAFE":
            out.append(Round(name=r["name"], kind="SAFE", safes=r["safes"]))
        else:
            out.append(
                Round(
                    name=r["name"],
                    kind="PRICED",
                    pre_money=r["pre_money"],
                    raise_amount=r["raise_amount"],
                    option_pool_pct_post=r["option_pool_pct_post"],
                    investors=r["investors"],
                )
            )
    return out


# =============================================================================
# SECTION 1 — Scenario controls
# =============================================================================
st.markdown('<div class="sec-num">01 · Scenario</div>', unsafe_allow_html=True)
st.markdown("### Start from a template, or build your own.")

col1, col2, col3, col4 = st.columns([1, 1, 1.5, 3])
with col1:
    if st.button("Template", use_container_width=True):
        _clear_widget_state()
        load_template()
        st.rerun()
with col2:
    if st.button("Blank Slate", use_container_width=True):
        _clear_widget_state()
        load_blank()
        st.rerun()
with col3:
    if st.button("Stacked Example", use_container_width=True):
        _clear_widget_state()
        load_stacked_example()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# SECTION 2 — Founders
# =============================================================================
st.markdown('<div class="sec-num">02 · Founders & Option Pool</div>', unsafe_allow_html=True)
st.markdown("### Who's on the cap table at incorporation?")

with st.container():
    pool_col, _ = st.columns([1.2, 7])
    with pool_col:
        pool_pct_input = st.number_input(
            "Initial option pool (%)",
            min_value=0.0, max_value=30.0,
            value=st.session_state.initial_pool_pct * 100,
            step=1.0,
            format="%.1f",
            key="pool_input",
        )
        st.session_state.initial_pool_pct = pool_pct_input / 100

    st.markdown("<br>", unsafe_allow_html=True)

    # Founder rows
    for i, f in enumerate(st.session_state.founders):
        fc1, fc2, fc3, _ = st.columns([2.5, 0.9, 0.5, 4.5])
        with fc1:
            f["name"] = st.text_input(
                f"Founder name #{i+1}",
                value=f["name"],
                key=f"fname_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
                placeholder="Name",
            )
        with fc2:
            f["pct"] = st.number_input(
                f"Equity % #{i+1}",
                min_value=0.0, max_value=100.0,
                value=float(f["pct"]),
                step=1.0,
                format="%.1f",
                key=f"fpct_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
        with fc3:
            if i > 0:
                if st.button("✕", key=f"rmf_{i}"):
                    st.session_state.founders.pop(i)
                    st.rerun()

    fc_a, fc_b = st.columns([1, 5])
    with fc_a:
        if st.button("+ Add founder"):
            st.session_state.founders.append({"name": "", "pct": 0.0})
            st.rerun()

    total_pct = sum(f["pct"] for f in st.session_state.founders)
    if abs(total_pct - 100) > 0.01:
        st.warning(f"Founder equity sums to {total_pct:.1f}%, not 100%. The math splits proportionally regardless, but check your inputs.", icon="⚠")


st.markdown("---")


# =============================================================================
# SECTION 3 — Rounds
# =============================================================================
st.markdown('<div class="sec-num">03 · Funding Rounds</div>', unsafe_allow_html=True)
st.markdown("### Add rounds in sequence. SAFEs convert at the next priced round.")

for ri, rnd in enumerate(st.session_state.rounds):
    with st.expander(f"**Round {ri+1}: {rnd['name']}** · {rnd['kind']}", expanded=True):
        # Round header
        rh1, rh2, rh3, _ = st.columns([2.5, 1.5, 0.5, 4])
        with rh1:
            rnd["name"] = st.text_input(
                "Round name",
                value=rnd["name"],
                key=f"rname_{ri}",
            )
        with rh2:
            new_kind = st.selectbox(
                "Round type",
                options=["SAFE", "PRICED"],
                index=0 if rnd["kind"] == "SAFE" else 1,
                key=f"rkind_{ri}",
            )
            if new_kind != rnd["kind"]:
                rnd["kind"] = new_kind
                if new_kind == "SAFE":
                    rnd["safes"] = rnd.get("safes", []) or [
                        {"name": "Investor", "amount": 500_000, "cap": 5_000_000}
                    ]
                else:
                    rnd["investors"] = rnd.get("investors", []) or [
                        {"name": "Lead Investor", "amount": 3_000_000}
                    ]
                    if rnd["pre_money"] == 0:
                        rnd["pre_money"] = 12_000_000
                        rnd["raise_amount"] = 3_000_000
        with rh3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✕", key=f"rmr_{ri}"):
                st.session_state.rounds.pop(ri)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # SAFE round inputs
        if rnd["kind"] == "SAFE":
            st.markdown("<span class='mono-label'>SAFE notes in this round</span>", unsafe_allow_html=True)
            for si, safe in enumerate(rnd["safes"]):
                sc1, sc2, sc3, sc4, _ = st.columns([2.4, 1.3, 1.5, 0.5, 3.3])
                with sc1:
                    safe["name"] = st.text_input(
                        "Investor",
                        value=safe["name"],
                        key=f"sname_{ri}_{si}",
                        label_visibility="collapsed" if si > 0 else "visible",
                    )
                with sc2:
                    safe["amount"] = dollar_input(
                        "Investment ($)",
                        value=int(safe["amount"]),
                        key=f"samt_{ri}_{si}",
                        label_visibility="collapsed" if si > 0 else "visible",
                        placeholder="500,000",
                    )
                with sc3:
                    safe["cap"] = dollar_input(
                        "Post-money cap ($)",
                        value=int(safe["cap"]),
                        key=f"scap_{ri}_{si}",
                        label_visibility="collapsed" if si > 0 else "visible",
                        placeholder="5,000,000",
                    )
                with sc4:
                    if len(rnd["safes"]) > 1:
                        if st.button("✕", key=f"rms_{ri}_{si}"):
                            rnd["safes"].pop(si)
                            st.rerun()

            if st.button("+ Add SAFE", key=f"adds_{ri}"):
                rnd["safes"].append({"name": "Investor", "amount": 500_000, "cap": 5_000_000})
                st.rerun()

        # Priced round inputs
        else:
            pc1, pc2, pc3, _ = st.columns([1.5, 1.5, 1.2, 4.8])
            with pc1:
                rnd["pre_money"] = dollar_input(
                    "Pre-money ($)",
                    value=int(rnd["pre_money"]),
                    key=f"pre_{ri}",
                    placeholder="20,000,000",
                )
            with pc2:
                rnd["raise_amount"] = dollar_input(
                    "Raise ($)",
                    value=int(rnd["raise_amount"]),
                    key=f"raise_{ri}",
                    placeholder="5,000,000",
                )
            with pc3:
                rnd["option_pool_pct_post"] = (
                    st.number_input(
                        "Pool target (%)",
                        min_value=0.0, max_value=30.0,
                        value=rnd["option_pool_pct_post"] * 100,
                        step=1.0,
                        format="%.1f",
                        key=f"pool_{ri}",
                    )
                    / 100
                )

            post_money = rnd["pre_money"] + rnd["raise_amount"]
            new_pct = (rnd["raise_amount"] / post_money * 100) if post_money > 0 else 0
            st.markdown(
                f"<span class='muted' style='font-family: JetBrains Mono, monospace; font-size: 11px; letter-spacing: 0.15em;'>"
                f"POST-MONEY {fmt_money(post_money)} · NEW INVESTOR SHARE {new_pct:.1f}%"
                f"</span>",
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<span class='mono-label'>Investors in this round</span>", unsafe_allow_html=True)
            for ii, inv in enumerate(rnd["investors"]):
                ic1, ic2, ic3, _ = st.columns([2.4, 1.5, 0.5, 4.6])
                with ic1:
                    inv["name"] = st.text_input(
                        "Investor",
                        value=inv["name"],
                        key=f"iname_{ri}_{ii}",
                        label_visibility="collapsed" if ii > 0 else "visible",
                    )
                with ic2:
                    inv["amount"] = dollar_input(
                        "Investment ($)",
                        value=int(inv["amount"]),
                        key=f"iamt_{ri}_{ii}",
                        label_visibility="collapsed" if ii > 0 else "visible",
                        placeholder="5,000,000",
                    )
                with ic3:
                    if len(rnd["investors"]) > 1:
                        if st.button("✕", key=f"rmi_{ri}_{ii}"):
                            rnd["investors"].pop(ii)
                            st.rerun()

            if st.button("+ Add investor", key=f"addi_{ri}"):
                rnd["investors"].append({"name": "Co-Lead", "amount": 1_000_000})
                st.rerun()


# Add round button
st.markdown("<br>", unsafe_allow_html=True)
add_c1, add_c2, _ = st.columns([1.5, 1.5, 4])
with add_c1:
    if st.button("+ Add SAFE round", use_container_width=True):
        n = len(st.session_state.rounds) + 1
        st.session_state.rounds.append({
            "name": f"Round {n}",
            "kind": "SAFE",
            "safes": [{"name": "Investor", "amount": 500_000, "cap": 5_000_000}],
            "pre_money": 0,
            "raise_amount": 0,
            "option_pool_pct_post": 0.10,
            "investors": [],
        })
        st.rerun()
with add_c2:
    if st.button("+ Add priced round", use_container_width=True):
        n = len(st.session_state.rounds) + 1
        st.session_state.rounds.append({
            "name": f"Round {n}",
            "kind": "PRICED",
            "safes": [],
            "pre_money": 20_000_000,
            "raise_amount": 5_000_000,
            "option_pool_pct_post": 0.12,
            "investors": [{"name": "Lead", "amount": 5_000_000}],
        })
        st.rerun()


st.markdown("---")


# =============================================================================
# SECTION 4 — Cap table
# =============================================================================
st.markdown('<div class="sec-num">04 · Cap Table</div>', unsafe_allow_html=True)
st.markdown("### Ownership evolution across rounds.")

# Run simulation
try:
    rounds_objs = rounds_to_objects(st.session_state.rounds)
    snapshots = simulate(
        founders=[f for f in st.session_state.founders if f["name"]],
        initial_pool_pct=st.session_state.initial_pool_pct,
        rounds=rounds_objs,
    )

    # Build HTML cap table — brand-styled
    column_names = ["At founding"] + [r["name"] for r in st.session_state.rounds]
    all_names = []
    for snap in snapshots:
        for h in snap.holders:
            if h.name not in all_names:
                all_names.append(h.name)

    def _cell(snap, name):
        h = next((x for x in snap.holders if x.name == name), None)
        if h is None:
            return '<td class="muted">—</td>'
        if h.is_unconverted_safe():
            inv = fmt_money(h.investment)
            cap = fmt_money(h.safe_cap)
            return f'<td><span class="safe-tag">SAFE · {inv} @ {cap}</span></td>'
        return f'<td class="number">{fmt_pct(snap.percent(h))}</td>'

    cap_html = ['<table class="dl-table">']
    cap_html.append('<thead><tr><th>Holder</th>')
    for col in column_names:
        cap_html.append(f'<th class="dl-num">{col}</th>')
    cap_html.append('</tr></thead><tbody>')
    for name in all_names:
        cap_html.append(f'<tr><td class="holder-name">{name}</td>')
        for snap in snapshots:
            cap_html.append(_cell(snap, name))
        cap_html.append('</tr>')
    cap_html.append('</tbody></table>')
    st.markdown("".join(cap_html), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Math error: {e}")
    snapshots = None


st.markdown("---")


# =============================================================================
# SECTION 5 — Exit waterfall
# =============================================================================
if snapshots:
    st.markdown('<div class="sec-num">05 · Exit Waterfall</div>', unsafe_allow_html=True)
    st.markdown("### Drag the slider. Watch the money move.")

    final_ct = snapshots[-1]

    # Slider: log scale for exit valuation
    LOG_MIN, LOG_MAX = math.log10(5_000_000), math.log10(10_000_000_000)
    if "exit_log" not in st.session_state:
        st.session_state.exit_log = math.log10(250_000_000)

    exit_log = st.slider(
        "Exit valuation",
        min_value=LOG_MIN,
        max_value=LOG_MAX,
        value=st.session_state.exit_log,
        step=0.01,
        format="",  # we'll show the formatted value separately
        key="exit_slider",
    )
    st.session_state.exit_log = exit_log
    exit_val = 10 ** exit_log

    # Big number display of exit value
    st.markdown(
        f"<div style='text-align: center; margin: 16px 0 32px;'>"
        f"<div class='bignum-label'>Exit Valuation</div>"
        f"<div class='bignum' style='font-size: 56px;'>{fmt_money(exit_val)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    common = waterfall_all_common(final_ct, exit_val)
    prefs = waterfall_with_prefs(final_ct, exit_val)

    # Brand-styled waterfall table
    wf_html = ['<table class="dl-table">']
    wf_html.append(
        '<thead><tr>'
        '<th>Holder</th>'
        '<th class="dl-num">Ownership</th>'
        '<th class="dl-num">All common</th>'
        '<th class="dl-num">1× non-part. preferred</th>'
        '</tr></thead><tbody>'
    )
    for h in final_ct.holders:
        if h.is_unconverted_safe():
            continue
        own = fmt_pct(final_ct.percent(h))
        c = fmt_money(common.get(h.name, 0))
        p = fmt_money(prefs.get(h.name, 0))
        wf_html.append(
            f'<tr>'
            f'<td class="holder-name">{h.name}</td>'
            f'<td class="number">{own}</td>'
            f'<td class="number">{c}</td>'
            f'<td class="number">{p}</td>'
            f'</tr>'
        )
    wf_html.append('</tbody></table>')
    st.markdown("".join(wf_html), unsafe_allow_html=True)

    # Headline founder takeaway
    founder_names = [f["name"] for f in st.session_state.founders if f["name"]]
    founder_total_prefs = sum(prefs.get(n, 0) for n in founder_names)
    founder_total_common = sum(common.get(n, 0) for n in founder_names)

    st.markdown("<br>", unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(
            f"<div class='card card-accent'>"
            f"<div class='bignum-label'>Founders (1x non-part. preferred)</div>"
            f"<div class='bignum'>{fmt_money(founder_total_prefs)}</div>"
            f"<div class='muted' style='font-size: 13px;'>Combined founder takeaway at this exit.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with cc2:
        st.markdown(
            f"<div class='card'>"
            f"<div class='bignum-label'>Founders (all common, no prefs)</div>"
            f"<div class='bignum' style='color: var(--subtle);'>{fmt_money(founder_total_common)}</div>"
            f"<div class='muted' style='font-size: 13px;'>What founders would get if no liquidation preferences existed.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# =============================================================================
# Footer
# =============================================================================
st.markdown(
    """
    <div class='footer'>
      Built by <a href='https://canonical.cc' target='_blank'>Canonical</a> · v0.1 ·
      Educational tool. Not legal or financial advice.
    </div>
    """,
    unsafe_allow_html=True,
)
