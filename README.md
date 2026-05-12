# Dilution Lab

A web app that lets founders model dilution, fundraising, and exit math across multi-round funding scenarios.

Built by [Canonical](https://canonical.cc).

## What it does

- Model multi-round fundraises: post-money SAFEs and priced rounds
- Stack multiple SAFEs at different caps in the same round
- Track ownership evolution across rounds with a live cap table
- Drag the exit valuation slider and watch the waterfall move in real time
- See both "all common" and "1x non-participating preferred" outcomes side-by-side

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Deploy to Streamlit Cloud

1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io and connect the repo.
3. Set main file: `app.py`. Set Python version: 3.10+.
4. Deploy. You'll get a URL like `https://dilution-lab.streamlit.app`.

## Files

- `app.py` — Streamlit UI
- `capmath.py` — cap table math (shares, SAFE conversion, option pool, exit waterfall)
- `style.py` — Canonical-branded CSS
- `test_math.py` — sanity tests (`python3 test_math.py`)
- `.streamlit/config.toml` — Streamlit theme

## Math assumptions

- **SAFEs**: post-money valuation cap only (industry standard). Multiple SAFEs in the same round do not dilute each other; founders absorb dilution.
- **Conversion**: SAFEs convert at the next priced round, before option pool top-up and new investor shares.
- **Option pool top-up**: pre-money — dilutes existing shareholders before new investors come in.
- **Liquidation preferences**: 1x non-participating for all priced rounds and converted SAFEs. Each preferred holder takes `max(preference, as-converted)`.

## License

Educational tool. Not legal or financial advice. Use at your own risk.
