# 📊 Equity Research Dashboard
### Live Trading Comparables · News Feed · DCF Valuation
**Part 1 of 5** in a finance & data analytics portfolio  
Stack: Python · Streamlit · yfinance · Plotly  
Deploy free on Streamlit Cloud

---

## Table of Contents
1. [What This Dashboard Does](#1-what-this-dashboard-does)
2. [File Structure](#2-file-structure)
3. [How to Run & Deploy](#3-how-to-run--deploy)
4. [Code Architecture — The Big Picture](#4-code-architecture--the-big-picture)
5. [Section-by-Section Code Guide](#5-section-by-section-code-guide)
   - [Colour Tokens — T dictionary](#51-colour-tokens--t-dictionary)
   - [Plotly LAYOUT](#52-plotly-layout)
   - [CSS Block](#53-css-block)
   - [Constants](#54-constants)
   - [Session State](#55-session-state)
   - [Cache Helpers](#56-cache-helpers)
   - [Data Functions](#57-data-functions)
   - [DCF Engine](#58-dcf-engine)
   - [Chart Functions](#59-chart-functions)
   - [HTML Table Renderer](#510-html-table-renderer)
   - [Sidebar](#511-sidebar)
   - [Tab 1 — Research & Comparables](#512-tab-1--research--comparables)
   - [Tab 2 — Valuation Models](#513-tab-2--valuation-models)
6. [How to Customise](#6-how-to-customise)
   - [Change Colours](#61-change-colours)
   - [Change Fonts](#62-change-fonts)
   - [Change Chart Sizes](#63-change-chart-sizes)
   - [Change Font Sizes in Charts](#64-change-font-sizes-in-charts)
   - [Change the Default Peer Group](#65-change-the-default-peer-group)
   - [Change DCF Scenario Presets](#66-change-dcf-scenario-presets)
   - [Add a New Chart](#67-add-a-new-chart)
   - [Add a New Column to the Comps Table](#68-add-a-new-column-to-the-comps-table)
7. [Data Layer Explained](#7-data-layer-explained)
8. [Known Limitations](#8-known-limitations)
9. [Interview Guide](#9-interview-guide)

---

## 1. What This Dashboard Does

**Tab 1 — Research & Comparables**
- Live trading comps table with LTM (Last Twelve Months) valuation multiples, profitability metrics, leverage ratios, and market data for any user-selected peer group
- KPI strip showing 8 key metrics for the focus company
- Four peer comparison charts: indexed price performance, EV/EBITDA vs revenue growth scatter, bar charts for margins/leverage/growth
- Candlestick chart with MA50 and MA200 for the focus company
- Live news feed from Yahoo Finance for all tickers in the watchlist

**Tab 2 — Valuation Models**
- DCF model with 5-year explicit free cash flow projection, Gordon Growth terminal value, sensitivity heatmap (WACC × TGR), and Bear/Base/Bull scenario presets
- EV/EBITDA Exit Multiple model (standard PE entry/exit framework)
- Football Field chart aggregating multiple methodology ranges

---

## 2. File Structure

```
abi-dashboard/
│
├── app.py                  ← The entire application (~1,500 lines)
├── requirements.txt        ← Python package dependencies
├── README.md               ← This file
│
└── .streamlit/
    └── config.toml         ← Forces dark theme at Streamlit level
```

Everything is intentionally in one file. This is standard for Streamlit — splitting into multiple files requires imports and a package structure that adds complexity without benefit for a single-app portfolio project.

---

## 3. How to Run & Deploy

**Run locally:**
```bash
git clone https://github.com/YOUR_USERNAME/abi-dashboard.git
cd abi-dashboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**Deploy on Streamlit Cloud (free):**
```bash
git add . && git commit -m "update" && git push
```
Then go to share.streamlit.io → New app → select repo → `app.py` → Deploy.

**Keep it live with UptimeRobot:**
Go to uptimerobot.com → Add Monitor → HTTP(s) → paste your Streamlit URL → 5 minute interval. This pings your app every 5 minutes so Streamlit never puts it to sleep.

---

## 4. Code Architecture — The Big Picture

The file is structured in this exact order, top to bottom:

```
1.  Imports
2.  Page config         st.set_page_config()
3.  Colour tokens       T = { ... }
4.  Plotly base layout  LAYOUT = dict(...)
5.  CSS injection       st.markdown("<style>...</style>")
6.  Constants           DEFAULT_TICKERS, PEER_COLORS, CACHE_FILE
7.  Session state init  for k,v in {...}.items()
8.  Cache helpers       _save() and _load()
9.  Data helpers        _s(), _parse_yield()
10. Fetch functions     _one(), fetch_comps(), fetch_prices(), fetch_ohlcv(), fetch_news(), fetch_dcf_base()
11. DCF engine          run_dcf(), sensitivity_table()
12. Chart functions     chart_prices(), chart_scatter(), chart_bar(), chart_leverage(), chart_candle(), chart_waterfall(), chart_fcf(), chart_heatmap()
13. HTML table helpers  dark_table(), dark_table_from_styled()
14. Sidebar             with st.sidebar:
15. Tabs                tab1, tab2 = st.tabs(...)
16. Tab 1 content       with tab1:
17. Tab 2 content       with tab2:
18. Footer
```

Streamlit runs this entire file top-to-bottom on every user interaction. This is why:
- Constants and functions must be defined before the sidebar and tabs that use them
- `st.session_state` is used for anything that needs to persist across reruns (tickers list, focus ticker, DCF inputs)
- `@st.cache_data` is used on data-fetching functions so they don't re-run on every interaction

---

## 5. Section-by-Section Code Guide

---

### 5.1 Colour Tokens — `T` dictionary

**Location:** Lines ~35–53  
**What it is:** A Python dictionary that defines every colour used anywhere in the app.

```python
T = {
    "bg":     "#0a0e14",   # Page background — very dark navy
    "card":   "#0d1117",   # Card/sidebar background — slightly lighter
    "card2":  "#111827",   # Secondary card — used for alternating table rows
    "border": "#1e2530",   # All borders and dividers
    "primary":"#f0f4ff",   # Headings, key numbers, bold text
    "muted":  "#9aa3b8",   # Body text, most content
    "faint":  "#6b7a99",   # Labels, captions, secondary info
    "ghost":  "#2a3550",   # Very faint — footer text
    "red":    "#e63946",   # Short thesis, alerts, focus company, negative
    "teal":   "#2dd4bf",   # Positive, long thesis, best-in-class values
    "blue":   "#3b82f6",   # Neutral, info, valuation tab accent
    "amber":  "#f59e0b",   # Warnings, MA50 line, base case scenario
    "purple": "#a78bfa",   # MA200 line, STZ peer colour
    "cgrid":  "rgba(100,120,150,0.12)",  # Chart grid lines — very faint
    "cline":  "rgba(100,120,150,0.22)",  # Chart axis lines — slightly stronger
}
```

**How it is used:** Every colour reference anywhere in the file reads from `T`. For example `T["red"]` is used in the CSS, in Plotly chart colours, in the HTML table renderer, and in the KPI card styles. This means you can change a colour in exactly one place and it updates everywhere.

**To change the accent colour** from red to, for example, orange:
```python
"red": "#f97316",   # change this one line
```
This will update: the focus company border, the "SHORT" badge, all minimum-value highlights in the comps table, the negative FCF bars in the DCF chart, and the bear scenario badge.

---

### 5.2 Plotly LAYOUT

**Location:** Lines ~55–64  
**What it is:** A Python dictionary that is passed to every Plotly figure via `**LAYOUT`.

```python
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",  # Transparent — inherits page background
    plot_bgcolor="rgba(0,0,0,0)",   # Transparent — inherits page background
    font=dict(family="IBM Plex Mono, monospace", color=T["faint"], size=11),
    margin=dict(l=40, r=20, t=40, b=40),  # Chart margins in pixels
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=T["cline"],
                borderwidth=1, font=dict(size=10)),
    xaxis=dict(gridcolor=T["cgrid"], linecolor=T["cline"], zerolinecolor=T["cline"]),
    yaxis=dict(gridcolor=T["cgrid"], linecolor=T["cline"], zerolinecolor=T["cline"]),
)
```

**Why transparent backgrounds:** If you set `paper_bgcolor="#0a0e14"` the chart background is hardcoded dark. Using `rgba(0,0,0,0)` (fully transparent) means the chart sits on top of whatever the page background is — so if you ever change `T["bg"]`, the charts update automatically without any other changes.

**Important rule:** You cannot pass `margin` both inside `LAYOUT` and as a separate keyword argument in `update_layout()` — Python will throw `TypeError: got multiple values for keyword argument`. If a chart needs a different margin, use: `layout_no_margin = {k:v for k,v in LAYOUT.items() if k != "margin"}` and then pass your custom margin separately.

**To change all chart font sizes globally:**
```python
font=dict(family="IBM Plex Mono, monospace", color=T["faint"], size=13),  # change size here
```

**To change all chart margins globally:**
```python
margin=dict(l=50, r=30, t=50, b=50),
```

---

### 5.3 CSS Block

**Location:** Lines ~69–230 (approximately)  
**What it is:** A large f-string containing CSS injected into the page via `st.markdown(..., unsafe_allow_html=True)`.

The CSS is organised into these sections:

**Google Fonts import**
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono...');
```
Loads IBM Plex Mono (monospace, used for all numbers and labels) and IBM Plex Sans (used for body text). To change fonts, replace the URL and update the `font-family` references throughout.

**Base dark theme**
Targets every Streamlit container element and forces the dark background. Uses `!important` everywhere because Streamlit's own CSS has high specificity. Also targets the top header bar:
```css
header[data-testid="stHeader"]  { background-color: #0a0e14 !important; }
div[data-testid="stDecoration"]  { background: #e63946 !important; height: 2px; }
```
The decoration bar is the 2-pixel stripe at the very top — currently set to red. Change `{T["red"]}` to any colour or set `height: 0px` to hide it entirely.

**Tab styling** (`.stTabs`)
Controls the tab bar appearance — background, font, text colour, and the active tab underline colour. The active underline is set to `{T["red"]}`. To change it:
```css
.stTabs [aria-selected="true"] {
    border-bottom: 2px solid {T["blue"]} !important;  /* change to any colour */
}
```

**Custom component classes**
These are HTML classes used in `st.markdown()` calls throughout the app:
- `.hdr` — the header strip at the top of each tab
- `.hdr-title` — large heading text inside `.hdr`
- `.hdr-sub` — small subtitle text inside `.hdr`
- `.slbl` — section labels (e.g. "📊 TRADING COMPARABLES — LTM")
- `.kpi` — KPI metric cards
- `.kpi.hi` — highlighted KPI card with left red border
- `.kpi-lbl` — label above KPI value
- `.kpi-val` — the large number in a KPI card
- `.news-card` — individual news article cards
- `.news-ticker` — ticker badge on news card
- `.news-title` — headline text on news card
- `.news-meta` — publisher and date on news card
- `.val-card` — valuation section info boxes
- `.badge`, `.badge-bear`, `.badge-base`, `.badge-bull` — scenario preset badges

**To change KPI card font size:**
```css
.kpi-val { font-size: 1.5rem; }   /* currently 1.25rem */
```

**To change section label size:**
```css
.slbl { font-size: .7rem; }   /* currently .6rem */
```

**Streamlit component overrides**
These fix Streamlit's native components (buttons, inputs, expanders, radio buttons) to use dark colours. They target Streamlit's internal `data-testid` attributes and BaseWeb component classes.

---

### 5.4 Constants

**Location:** ~Lines 230–250

```python
DEFAULT_TICKERS = ["BUD","HEINY","CBRL.L","TAP","STZ","DEO","ABEV"]
```
The peer group loaded when the app first opens. Change these to whatever sector you want as the default.

```python
DEFAULT_NAMES = {
    "BUD": "Anheuser-Busch InBev",
    ...
}
```
Display names shown in the comps table Company column. If you add a ticker that isn't in this dict, the app falls back to Yahoo Finance's `shortName` field automatically.

```python
PEER_COLORS = {
    "BUD":   T["red"],
    "HEINY": T["teal"],
    ...
    "_":     T["faint"],   # fallback for any ticker not in this dict
}
```
Assigns a specific colour to each ticker for charts. BUD is always red (the short thesis focus). If you add a new ticker that isn't in this dict, it gets `T["faint"]` (grey). To assign a specific colour to a new ticker, add it here.

```python
CACHE_FILE = "/tmp/erd_cache.json"
```
Where the disk cache is saved on Streamlit Cloud. `/tmp` is writable on all cloud platforms but gets wiped on container restart. The session_state cache is the primary fallback; this is the secondary fallback.

---

### 5.5 Session State

**Location:** ~Lines 252–260

```python
for k,v in {
    "tickers":  DEFAULT_TICKERS.copy(),
    "focus":    "BUD",
    "period":   "2y",
    "dcf_tkr":  "BUD",
    "_cache":   None,
    "dcf_inputs": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v
```

**Why this pattern:** Streamlit reruns the entire script on every user interaction (every button click, every input change). Without session_state, every rerun would reset the tickers list to the default. The `if k not in st.session_state` check means we only set the default on the very first run — after that, the user's changes persist.

**What each key stores:**
- `tickers` — list of ticker strings currently in the watchlist
- `focus` — the selected focus ticker string (e.g. "BUD")
- `period` — the selected lookback period string (e.g. "2y")
- `dcf_tkr` — the ticker entered in the valuation tab
- `_cache` — the last known good data payload as a dict (fallback when Yahoo is rate-limiting)
- `dcf_inputs` — the current DCF assumption inputs (persists when user switches tabs)

---

### 5.6 Cache Helpers

**Location:** ~Lines 262–290

```python
def _save(df, px, ts):
    """Save fundamentals DataFrame and prices DataFrame to both
    session_state (in-memory, fast) and /tmp disk (survives TTL expiry)."""

def _load():
    """Load last known good data. Tries session_state first, then disk.
    Returns (df, prices, timestamp) or (None, None, None) if nothing saved."""
```

These are called in Tab 1 after every successful fetch. If Yahoo Finance fails on the next load, the app shows the cached data with a warning banner rather than going blank.

---

### 5.7 Data Functions

**Location:** ~Lines 292–540

#### `_s(v, d=None)` — Safe numeric extractor
```python
def _s(v, d=None):
    """Return float(v) if v is a real finite number, else return d."""
```
Used everywhere Yahoo Finance data is read. Yahoo sometimes returns `None`, `"N/A"`, or `NaN` (not-a-number) for missing fields. The NaN check `f != f` works because NaN is the only float that is not equal to itself — a Python quirk.

#### `_parse_yield(raw)` — Dividend yield parser
Yahoo Finance returns `dividendYield` inconsistently — sometimes as a decimal (`0.0142` meaning 1.42%) and sometimes already as a percentage (`1.42`). The rule: if the raw value is above `0.30` (above 30%), it is already in percentage form — use it directly. Otherwise multiply by 100. No legitimate dividend yield in this peer group exceeds 30%.

#### `_one(tkr)` — Single ticker data fetcher
The core data function. Makes four separate requests to Yahoo Finance for one ticker:
1. `fast_info` — price, market cap, 52W high/low. Most reliable endpoint, rarely rate-limited.
2. `.info` — valuation multiples, margins, growth rates. Most useful but most rate-limited on shared IPs.
3. `.financials` — income statement from SEC filings. Separate endpoint from `.info` so it often succeeds when `.info` fails.
4. `.balance_sheet` — debt and cash from SEC filings.

Each endpoint is wrapped in its own `try/except` so failure on one does not prevent the others from running. The function always returns whatever it managed to collect.

**`time.sleep(0.8)`** between tickers — this small delay staggers the requests so all 7 tickers don't hit Yahoo simultaneously, which would trigger rate limiting.

#### `@st.cache_data(ttl=14400)` — The cache decorator
`@st.cache_data` stores the function's return value. The next call with the same arguments returns the stored value instantly without calling Yahoo Finance again. `ttl=14400` means the cache is valid for 4 hours (14400 seconds). After 4 hours it expires and the next call fetches fresh data.

**Why `tuple` not `list`:** `@st.cache_data` requires hashable arguments to use as dictionary keys. Python lists are not hashable. Tuples are. So `fetch_comps(tickers)` is called as `fetch_comps(tuple(tickers))` — the tuple conversion happens at the call site.

#### `fetch_news(tickers)` — News feed
`ttl=1800` (30 minutes) — news refreshes more frequently than fundamentals. Uses `yf.Ticker(tkr).news` which returns Yahoo Finance's news feed for each ticker. The function handles two different dict structures that different versions of yfinance return (the `.content` nested structure in newer versions vs flat keys in older versions).

---

### 5.8 DCF Engine

**Location:** ~Lines 543–590

#### `run_dcf(...)` — Core valuation calculation
```python
def run_dcf(base_rev, growth, ebit_margin, tax_rate, da_pct,
            capex_pct, nwc_pct, wacc, tgr, net_debt, shares):
```

The formula chain:
```
Revenue(yr)    = Revenue(yr-1) × (1 + growth_rate)
EBIT           = Revenue × EBIT_margin
NOPAT          = EBIT × (1 - tax_rate)          # Net Operating Profit After Tax
D&A            = Revenue × da_pct
Capex          = Revenue × capex_pct
ΔNWC           = Revenue_change × nwc_pct       # Change in Net Working Capital
FCFF           = NOPAT + D&A - Capex - ΔNWC     # Free Cash Flow to Firm
PV(FCF_yr)     = FCFF / (1 + WACC)^yr           # Discounted to present value
Terminal Value = FCF_5 × (1+g) / (WACC - g)    # Gordon Growth Model
PV(TV)         = Terminal Value / (1+WACC)^5
Enterprise Value = Σ PV(FCF) + PV(TV)
Equity Value   = Enterprise Value - Net Debt
Implied Price  = Equity Value / Shares Outstanding
```

All monetary inputs and outputs are in **$B (billions)**. Shares are in **millions**. The final conversion `(eq*1e9) / (shares*1e6)` converts back to per-share dollars.

**The WACC > TGR guard:**
```python
tv = fcfs[-1] * (1+g_) / (w-g_) if w>g_ else 0
```
If WACC equals or is less than the terminal growth rate, the Gordon Growth formula produces a negative or infinite terminal value. This check sets TV to zero in that case. The sensitivity table shows `"—"` for those cells.

#### `sensitivity_table(...)` — WACC × TGR grid
Runs `run_dcf()` for every combination of WACC and TGR in the provided ranges. The ranges are generated dynamically around the user's central WACC and TGR assumptions:
```python
wacc_range = [round(wacc - 2 + i*0.5, 1) for i in range(9)]  # 9 values: central ±2%
tgr_range  = [round(tgr  - 1 + i*0.5, 1) for i in range(7)]  # 7 values: central ±1.5%
```
This means if the user's WACC is 8.0%, the table shows 6.0%, 6.5%, 7.0%, 7.5%, 8.0%, 8.5%, 9.0%, 9.5%, 10.0%.

---

### 5.9 Chart Functions

**Location:** ~Lines 593–732

All chart functions follow the same pattern:
```python
def chart_something(data, args) -> go.Figure:
    fig = go.Figure(...)         # create the figure
    fig.update_layout(**LAYOUT, height=X, title=..., ...)  # apply base layout + customise
    return fig                   # return for st.plotly_chart() to render
```

#### `chart_prices` — Indexed price performance
Normalises all prices to 100 at the start of the period using `raw.div(raw.iloc[0]).mul(100)`. This allows comparing percentage performance regardless of absolute price level — a $10 stock and a $500 stock both start at 100.

#### `chart_scatter` — EV/EBITDA vs Revenue Growth
Bubble chart where:
- X axis = Revenue Growth YoY
- Y axis = EV/EBITDA
- Bubble size = Market Cap (scaled via `mktcap^0.45 * 6`)
- Colour = per-ticker colour from PEER_COLORS
- Focus ticker has a white border ring

The median horizontal line is drawn with `fig.add_hline()`. Companies above the line (high multiple vs peers) are expensive relative to the peer group median. Companies to the left (low growth) with a high multiple are the strongest short argument.

**Defensive reset_index:** `if df.index.name == "Ticker": df = df.reset_index()` — this prevents a crash if the DataFrame was passed with Ticker as the index rather than as a column.

#### `chart_waterfall` — DCF value bridge
Shows the composition of equity value from left to right:
`FCF Year 1` → `FCF Year 2` → ... → `Terminal Value` → `Enterprise Value` → `(Net Debt)` → `Equity Value`

Uses Plotly's `go.Waterfall` trace. `measure` controls whether each bar is additive ("relative") or a running total ("total"). The net debt bar is negative (subtracts from EV to get equity value).

#### `chart_heatmap` — Sensitivity table
Uses `go.Heatmap`. `colorscale` goes from red (low implied price) through dark (at current price) to teal (high implied price). `zmid=cur_price` anchors the colour midpoint at the current trading price — cells above the current price are teal (upside), cells below are red (downside).

**The margin fix:** `layout_no_margin = {k:v for k,v in LAYOUT.items() if k != "margin"}` — this creates a copy of LAYOUT without the margin key so a custom margin can be passed without causing a `TypeError: duplicate keyword argument`.

---

### 5.10 HTML Table Renderer

**Location:** ~Lines 735–830

**Why these functions exist:** `st.dataframe()` renders inside an isolated component (similar to an `<iframe>`) that Streamlit calls the "Arrow table". CSS injected via `st.markdown()` lives in the parent document and cannot cross this isolation boundary. No matter how specific the CSS selector, it will never change the background of an Arrow table. The only reliable fix is to not use `st.dataframe()` and instead render raw HTML tables using `st.markdown(unsafe_allow_html=True)`.

#### `dark_table(df, height_px)` — Simple dark table
Used for the peer median/mean summary and the DCF projection table. Builds a `<table>` element with inline styles. Inline styles cannot be overridden by any external CSS, so the dark background is guaranteed. Alternates row backgrounds between `T["card"]` and `T["card2"]` for readability.

#### `dark_table_from_styled(df, fmt, focus_idx, height_px)` — Comps table
More sophisticated version used for the main trading comps table. Features:
- Focus row highlighted with `rgba(230,57,70,0.10)` background and bold text
- Per-column maximum shown in teal, minimum shown in red (pre-computed using `pd.to_numeric(...).idxmax()`)
- Custom format function applied per column (the same `fmt_map` dict used previously with pandas `.format()`)

---

### 5.11 Sidebar

**Location:** ~Lines 833–905

The sidebar contains all user controls:
- **Add ticker / Clear all** — modifies `st.session_state.tickers`, clears all relevant caches, then calls `st.rerun()` to force a full script rerun with the new data
- **Watchlist display** — iterates `st.session_state.tickers`, shows each with a remove button
- **Focus ticker** — `st.selectbox` writing to `st.session_state.focus`
- **Price period** — `st.select_slider` writing to `st.session_state.period`
- **Refresh data** — calls `.clear()` on all four cached functions then `st.rerun()`

**Why `.clear()` before `st.rerun()`:** Calling `fetch_comps.clear()` wipes Streamlit's in-memory cache for that function. Without this, `st.rerun()` would find the cached result for the new ticker tuple and return stale data. The clear forces a fresh Yahoo Finance fetch on the next run.

---

### 5.12 Tab 1 — Research & Comparables

**Location:** ~Lines 908–1160

Structure:
```
Header strip
Status bar (live/cached indicator + refresh button)
KPI strip (8 metrics for focus company)
Comps table (HTML rendered)
Peer median/mean expander
Charts (2×2 grid + candlestick)
News feed
```

**The fetch + fallback logic:**
```python
df = fetch_comps(tuple(tickers))          # try live
if not df.empty:
    _save(df, prices, timestamp)           # save to cache
else:
    df, prices, ts = _load()               # fall back to cache
    if df is None:
        st.error(...)
        st.stop()                          # nothing to show — stop the script
```

**`st.stop()`** halts execution of the rest of the script for this rerun. Everything below it does not render. This is cleaner than wrapping everything in `if df is not None`.

**KPI strip formatting:**
```python
def _fmt(col, pre="", suf="", dec=2):
    v = f.get(col)
    return f"{pre}{v:.{dec}f}{suf}" if pd.notna(v) and v is not None else "—"
```
A small helper that formats a value from the focus row with prefix, suffix, and decimal places. Returns `"—"` for missing values so the dashboard always shows something rather than crashing on None.

**News feed:**
```python
for article in filtered[:20]:
```
Limits to 20 articles maximum. Each article is rendered as a `.news-card` div with the ticker badge, clickable headline (if a link is available), publisher, and formatted date. The date formatting handles both Unix timestamps (integers returned by older yfinance) and ISO date strings (returned by newer yfinance).

---

### 5.13 Tab 2 — Valuation Models

**Location:** ~Lines 1163–1460

**Model selection via `st.radio`:**
```python
model = st.radio("Model",
    ["DCF — Discounted Cash Flow",
     "EV/EBITDA Exit Multiple",
     "Football Field (Combined Ranges)"],
    horizontal=True)
```
Python's `in` operator checks which model is selected: `if "DCF" in model`, `elif "Exit" in model`, `elif "Football" in model`. This is cleaner than checking exact string equality.

**`fetch_dcf_base(ticker)`:** Pulls historical financials (3 years of revenue, EBIT, D&A, capex) from Yahoo Finance to pre-populate the DCF inputs. The historical data appears in the base year revenue field as a starting point — the user can override it.

**DCF scenario presets:**
```python
SCENARIOS = {
    "Bear": dict(g=[-2,-3,-4,-4,-3], margin=18.0, wacc=9.5, tgr=0.5, da=5.0, cx=6.0, nwc=2.0),
    "Base": dict(g=[1, 2, 2, 3, 3],  margin=22.0, wacc=8.0, tgr=1.5, da=5.0, cx=5.5, nwc=2.0),
    "Bull": dict(g=[3, 4, 4, 5, 5],  margin=25.0, wacc=7.0, tgr=2.0, da=5.0, cx=5.0, nwc=2.0),
}
```
These are pre-loaded assumptions for BUD's ABI short thesis. The bear case embeds negative revenue growth (volume decline thesis), compressed margins, and higher WACC (elevated risk). Change these numbers to match your own thesis for any company.

**`st.session_state.dcf_inputs`:** The DCF inputs are stored in session_state so they persist when the user switches between tabs and comes back. Without this, switching to Tab 1 and back to Tab 2 would reset all inputs to defaults.

**Football field chart:** Uses `go.Bar` with `base=lo` and `x=[hi-lo]`. The base sets where the bar starts; the x value is the bar width (high minus low). This creates horizontal bars that represent ranges rather than values. The `add_vline` adds a vertical line at the current price.

---

## 6. How to Customise

### 6.1 Change Colours

All colours are defined in the `T` dictionary at the top of the file (~line 35). Change any value there and it updates everywhere.

```python
T = {
    "bg":     "#0a0e14",   # ← change page background
    "card":   "#0d1117",   # ← change card background
    "border": "#1e2530",   # ← change all borders
    "red":    "#e63946",   # ← change accent/focus/alert colour
    "teal":   "#2dd4bf",   # ← change positive indicator colour
    ...
}
```

Also update `.streamlit/config.toml` to match — Streamlit's native components (scrollbars, spinners, toggle switches) use the colours defined there:
```toml
[theme]
backgroundColor = "#0a0e14"          # match T["bg"]
secondaryBackgroundColor = "#0d1117" # match T["card"]
primaryColor = "#e63946"             # match T["red"]
textColor = "#d4d8e1"
```

---

### 6.2 Change Fonts

**Step 1 — Load the font in the CSS block:**
```css
@import url('https://fonts.googleapis.com/css2?family=YOUR_FONT_HERE&display=swap');
```

**Step 2 — Update the base CSS:**
```css
html, body, [class*="css"] {
    font-family: 'YOUR_FONT_HERE', sans-serif;
}
```

**Step 3 — Update LAYOUT:**
```python
LAYOUT = dict(
    font=dict(family="YOUR_FONT_HERE, monospace", ...),
    ...
)
```

**Step 4 — Update component CSS classes:**
Search for `font-family:'IBM Plex Mono'` in the file and replace all occurrences. There are approximately 25 references.

---

### 6.3 Change Chart Sizes

Each chart function has a `height=` parameter in its `update_layout` call. Change the number to make the chart taller or shorter:

```python
# In chart_prices():
fig.update_layout(**LAYOUT, height=360, ...)   # ← change 360 to any pixel height

# In chart_candle():
fig.update_layout(**LAYOUT, height=440, ...)   # ← change 440
```

To change chart width, use the `use_container_width=True` parameter in `st.plotly_chart()` — this makes the chart fill its column. To set a fixed width, change to `use_container_width=False` and add `width=800` to `update_layout`.

---

### 6.4 Change Font Sizes in Charts

**All charts globally** — change `size=11` in LAYOUT:
```python
LAYOUT = dict(
    font=dict(family="IBM Plex Mono, monospace", color=T["faint"], size=13),  # was 11
    ...
)
```

**Specific text in a specific chart** — add `textfont` to that trace:
```python
# In chart_scatter(), change the ticker label size:
textfont=dict(size=12, color=_c(tkr), family="IBM Plex Mono, monospace"),  # was 10
```

**Chart titles** — change `font=dict(size=11)` in each chart's `title=dict(...)`:
```python
fig.update_layout(**LAYOUT,
    title=dict(text="My Chart", font=dict(size=14), x=0),  # was size=11
    ...)
```

**Axis tick labels** — add `tickfont` to `update_xaxes`/`update_yaxes`:
```python
fig.update_xaxes(tickfont=dict(size=10, family="IBM Plex Mono, monospace"))
```

---

### 6.5 Change the Default Peer Group

To change what loads when the app first opens:

```python
# Around line 232
DEFAULT_TICKERS = ["NVDA", "AMD", "INTC", "TSM", "ASML", "QCOM"]

DEFAULT_NAMES = {
    "NVDA": "NVIDIA Corporation",
    "AMD":  "Advanced Micro Devices",
    "INTC": "Intel Corporation",
    "TSM":  "Taiwan Semiconductor",
    "ASML": "ASML Holding",
    "QCOM": "Qualcomm",
}

PEER_COLORS = {
    "NVDA": T["teal"],
    "AMD":  T["blue"],
    "INTC": T["red"],
    "TSM":  T["amber"],
    "ASML": T["purple"],
    "QCOM": "#34d399",
    "_":    T["faint"],
}
```

Also change the session state default:
```python
# Around line 255
for k,v in {
    "tickers": DEFAULT_TICKERS.copy(),
    "focus":   "NVDA",          # ← change focus company
    ...
}
```

---

### 6.6 Change DCF Scenario Presets

**Location:** Tab 2, inside `if "DCF" in model:`, around line 1240.

```python
SCENARIOS = {
    "Bear": dict(
        g=[-2, -3, -4, -4, -3],  # Year 1-5 revenue growth rates (%)
        margin=18.0,              # EBIT margin (%)
        wacc=9.5,                 # Discount rate (%)
        tgr=0.5,                  # Terminal growth rate (%)
        da=5.0,                   # D&A as % of revenue
        cx=6.0,                   # Capex as % of revenue
        nwc=2.0,                  # Change in NWC as % of revenue change
    ),
    "Base": dict(g=[1,2,2,3,3], margin=22.0, wacc=8.0, tgr=1.5, da=5.0, cx=5.5, nwc=2.0),
    "Bull": dict(g=[3,4,4,5,5], margin=25.0, wacc=7.0, tgr=2.0, da=5.0, cx=5.0, nwc=2.0),
}
```

These numbers are calibrated for the ABI short thesis. For a different company:
- Set `g` based on your revenue growth forecast
- Set `margin` based on historical EBIT margins and your thesis on whether they expand or contract
- Set `wacc` using CAPM for the equity component and the company's cost of debt
- Set `tgr` at or below long-run GDP growth (typically 1.0%–2.5%)
- Set `da` and `cx` from the company's historical financials (visible in `fetch_dcf_base` output)

---

### 6.7 Add a New Chart

1. Write a new function following the chart pattern:
```python
def chart_my_new_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(...))
    fig.update_layout(**LAYOUT, height=300,
        title=dict(text="My New Chart", font=dict(size=11), x=0))
    return fig
```

2. Call it in Tab 1 wherever you want it to appear:
```python
st.plotly_chart(chart_my_new_chart(df),
                use_container_width=True,
                config={"displayModeBar": False})
```

`config={"displayModeBar": False}` hides the Plotly toolbar (the save/zoom/pan buttons that appear on hover). Set to `True` if you want users to be able to save the chart as an image.

---

### 6.8 Add a New Column to the Comps Table

**Step 1 — Fetch the data in `_one(tkr)`:**
```python
# Inside the .info block in _one():
d["my_metric"] = _s(info.get("theYahooFinanceKey"))
```

**Step 2 — Add it to the `rows.append({...})` dict in `fetch_comps()`:**
```python
"My Metric": round(d["my_metric"] * 100, 1) if d.get("my_metric") else None,
```

**Step 3 — Add it to the display columns list in Tab 1:**
```python
dc = ["Ticker","Company","Price","Mkt Cap ($B)","EV ($B)",
      "EV/EBITDA","EV/Revenue","P/E","P/B",
      "EBITDA Margin","Net Margin","Rev Growth YoY",
      "Net Debt/EBITDA","Div Yield","Beta","Short % Float",
      "My Metric"]    # ← add here
```

**Step 4 — Add a format function:**
```python
fmt_map = {
    ...
    "My Metric": lambda x: f"{x:.1f}%" if pd.notna(x) else "—",
}
```

---

## 7. Data Layer Explained

**Why Yahoo Finance and not Bloomberg/Refinitiv?**
Bloomberg and Refinitiv are the professional standard but cost $20,000–$30,000/year per terminal. Yahoo Finance is free via the unofficial `yfinance` library. For a portfolio demonstration tool, this is the right tradeoff — the data quality is sufficient for LTM multiples and the constraint is explicit (disclosed in the footer).

**Why three endpoints instead of one?**
Yahoo Finance rate-limits heavily on shared cloud IPs (Streamlit Cloud's servers are shared with thousands of other apps). The `.info` endpoint is the most useful but most aggressively rate-limited. `fast_info` uses a different Yahoo API and is rarely blocked. `.financials` and `.balance_sheet` pull from SEC filing data — a completely separate endpoint. By using all three independently, the app can still show price and market cap (from `fast_info`) even when the `.info` endpoint is blocked.

**Why `ttl=14400` (4 hours)?**
The longer the cache, the less often the app hits Yahoo Finance, the less rate limiting. 4 hours is long enough that infrequent visitors (e.g. a hedge fund manager opening the link once) almost always see cached data from an earlier successful fetch. If you want more live data, reduce to `ttl=3600` (1 hour). If Yahoo Finance is causing problems, increase to `ttl=28800` (8 hours).

**LTM vs NTM (Forward) multiples:**
LTM = Last Twelve Months, using reported financial results. This is what the dashboard shows.
NTM = Next Twelve Months, using analyst consensus forecasts. NTM data requires Bloomberg, FactSet, or similar paid services. For interviews, acknowledge this limitation directly: "I use LTM multiples from reported financials — forward consensus would require Bloomberg which I don't have access to in this context."

---

## 8. Known Limitations

1. **LTM multiples only** — no forward estimates without a paid data provider
2. **Yahoo Finance reliability** — rate limited on shared cloud IPs; data may be incomplete during peak hours
3. **Currency mixing** — non-USD tickers (DEO in GBp, CBRL.L in DKKr) display in local currency; market cap and EV comparisons across currencies require adjustment
4. **No volume data by geography** — the ABI short thesis ideally tracks beer volume by region (US vs EM); Yahoo Finance doesn't provide this granularity
5. **DCF assumptions are manual** — the model uses user-inputted assumptions, not analyst consensus
6. **Historical data only** — `fetch_dcf_base` pulls 3 years of history; more years would require going deeper into the `.financials` DataFrame

---

## 9. Interview Guide

**Opening line for any interview:**
> "I built a live equity research dashboard where you define your own peer group and run a full DCF. It defaults to a short thesis I've developed on ABI. Want me to walk you through it?"

**For Hedge Fund interviews:**
Open Tab 1. Walk through the KPI strip for BUD — explain EV/EBITDA relative to peers. Open the scatter chart — show BUD in the expensive/low-growth quadrant. Explain the three structural headwinds (GLP-1, Gen Z, brand damage). Then open Tab 2, load the Bear scenario DCF, walk through each assumption and why you chose it. The sensitivity heatmap shows the range of outcomes.

**For IB interviews:**
Focus on the comps table methodology. Explain LTM vs NTM, why you used three Yahoo Finance endpoints, what each column measures, and how to read the green/red highlights (extremes within the peer group). Then walk through the DCF — IBD analysts build these every day, so showing you understand every line is the key differentiator.

**For PE interviews:**
Use the EV/EBITDA Exit Multiple model in Tab 2. Explain the entry/exit framework — "can you buy this business, reduce leverage, and exit at a higher multiple?" Point to the Net Debt/EBITDA leverage chart — ABI's elevated leverage constrains their ability to invest through volume headwinds. Discuss FCF yield and whether the dividend is sustainable.

**Questions you'll get asked — and how to answer:**
- *"What's your price target on BUD?"* — "My DCF bear case implies X at 8% WACC and 0.5% TGR, let me show you the sensitivity table for the range."
- *"Why LTM and not forward multiples?"* — "Forward consensus requires Bloomberg which I don't have access to for this tool. I deliberately disclosed this in the footer — in a professional context I'd layer in FactSet consensus estimates."
- *"What would make you wrong on the short?"* — "Faster-than-expected EM volume growth outpacing developed market structural decline, or multiple compression normalising relative to peers."
- *"Why did you build this?"* — "I wanted to demonstrate I can think like an analyst and build like an engineer. The tool works for any sector — let me switch the peer group to something you cover."

---

*Data: Yahoo Finance · yfinance · LTM multiples · Not investment advice · Portfolio demonstration*
