"""
═══════════════════════════════════════════════════════════════════
  EQUITY RESEARCH DASHBOARD
  Tab 1 — Trading Comparables + News Feed
  Tab 2 — Valuation (DCF + EV/EBITDA Exit + Football Field)
═══════════════════════════════════════════════════════════════════
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import json
import os
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Equity Research Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# COLOUR TOKENS — single source of truth for the dark theme
# ─────────────────────────────────────────────────────────────────
T = {
    "bg":     "#0a0e14",
    "card":   "#0d1117",
    "card2":  "#111827",
    "border": "#1e2530",
    "primary":"#f0f4ff",
    "muted":  "#9aa3b8",
    "faint":  "#6b7a99",
    "ghost":  "#2a3550",
    "red":    "#e63946",
    "teal":   "#2dd4bf",
    "blue":   "#3b82f6",
    "amber":  "#f59e0b",
    "purple": "#a78bfa",
    "cgrid":  "rgba(100,120,150,0.12)",
    "cline":  "rgba(100,120,150,0.22)",
}

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono, monospace", color=T["faint"], size=11),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=T["cline"],
                borderwidth=1, font=dict(size=10)),
)
# xaxis and yaxis deliberately excluded from LAYOUT.
# Passing xaxis=dict(...) via **LAYOUT alongside xaxis_title= causes
# TypeError: duplicate keyword argument in Python.
# Use _ax(fig) after every update_layout() call to apply axis grid styling.

def _ax(fig, subplots=False, rows=2, cols=1):
    """
    Apply dark grid styling to all axes.
    subplots=False  → simple figure, no row/col args (default for all standard charts)
    subplots=True   → make_subplots figure, loop over rows/cols (candlestick only)
    row/col args only valid on subplot figures — passing them to a regular figure
    raises Exception from plotly.basedatatypes._validate_get_grid_ref().
    """
    s = dict(gridcolor=T["cgrid"], linecolor=T["cline"], zerolinecolor=T["cline"])
    if subplots:
        for r in range(1, rows+1):
            for c in range(1, cols+1):
                fig.update_xaxes(s, row=r, col=c)
                fig.update_yaxes(s, row=r, col=c)
    else:
        fig.update_xaxes(s)
        fig.update_yaxes(s)
    return fig


# ─────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html,body,[class*="css"],.stApp,
section[data-testid="stSidebar"],
div[data-testid="stAppViewContainer"],
div[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
div[data-testid="stDeployButton"],
header[data-testid="stHeader"],
.main,.block-container {{
    background-color:{T["bg"]} !important;
    color:{T["muted"]} !important;
    font-family:'IBM Plex Sans',sans-serif;
}}

/* ── Top bar: the white strip at the very top of Streamlit apps ── */
/* Streamlit renders a header bar with a white background by default. */
/* These selectors target every known variant across Streamlit versions. */
header[data-testid="stHeader"] {{
    background-color:{T["bg"]} !important;
    border-bottom:1px solid {T["border"]} !important;
}}
div[data-testid="stToolbar"] {{
    background-color:{T["bg"]} !important;
}}
/* The decoration bar is a 2px coloured stripe at the very top */
div[data-testid="stDecoration"] {{
    background:{T["red"]} !important;
    height:2px !important;
}}
/* Status widget (hamburger menu area) */
div[data-testid="stStatusWidget"] {{
    background-color:{T["bg"]} !important;
}}
/* The "Deploy" button area */
div[data-testid="stDeployButton"] {{
    background-color:{T["bg"]} !important;
}}
/* Main app view container background */
div[data-testid="stAppViewContainer"] {{
    background-color:{T["bg"]} !important;
}}
/* Catch-all for any remaining white containers */
.stApp > header {{
    background-color:{T["bg"]} !important;
}}
.stApp > div:first-child {{
    background-color:{T["bg"]} !important;
}}

.main .block-container {{ padding:1.5rem 2rem; max-width:1400px; }}
[data-testid="stSidebar"] {{
    background-color:{T["card"]} !important;
    border-right:1px solid {T["border"]} !important;
}}
[data-testid="stSidebar"] .block-container {{ padding:1.2rem 1rem; }}

/* ── Sidebar collapse/expand arrow ── */
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebar"] button svg,
button[aria-label="Collapse sidebar"] svg,
button[aria-label="Expand sidebar"] svg,
[class*="collapsedControl"] svg {{
    color:#f0f4ff !important;
    fill:#f0f4ff !important;
}}
[data-testid="stSidebarCollapsedControl"] button,
button[aria-label="Collapse sidebar"],
button[aria-label="Expand sidebar"] {{
    background:#0d1117 !important;
    border:1px solid #1e2530 !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background:{T["card"]};
    border-bottom:1px solid {T["border"]};
    gap:0;
}}
.stTabs [data-baseweb="tab"] {{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.72rem; letter-spacing:0.08em; text-transform:uppercase;
    color:{T["faint"]}; background:{T["card"]}; border:none;
    padding:0.65rem 1.4rem; border-bottom:2px solid transparent;
}}
.stTabs [aria-selected="true"] {{
    color:{T["primary"]} !important;
    border-bottom:2px solid {T["red"]} !important;
    background:{T["bg"]} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    background:{T["bg"]}; padding-top:1.2rem;
}}

.hdr {{
    background:linear-gradient(90deg,{T["card"]} 0%,{T["card2"]} 100%);
    border:1px solid {T["border"]}; border-left:3px solid {T["red"]};
    padding:.9rem 1.4rem; margin-bottom:1.2rem;
    display:flex; align-items:center; justify-content:space-between;
}}
.hdr-title {{
    font-family:'IBM Plex Mono',monospace; font-size:1rem; font-weight:600;
    color:{T["primary"]}; letter-spacing:.05em; text-transform:uppercase;
}}
.hdr-sub {{ font-size:.7rem; color:{T["faint"]}; font-family:'IBM Plex Mono',monospace; margin-top:.15rem; }}

.slbl {{
    font-family:'IBM Plex Mono',monospace; font-size:.6rem; color:{T["faint"]};
    letter-spacing:.15em; text-transform:uppercase;
    border-bottom:1px solid {T["border"]}; padding-bottom:.3rem;
    margin-bottom:.8rem; margin-top:1.2rem;
}}

.kpi {{ background:{T["card"]}; border:1px solid {T["border"]}; padding:.85rem 1rem; }}
.kpi.hi {{ border-left:3px solid {T["red"]}; }}
.kpi-lbl {{ font-family:'IBM Plex Mono',monospace; font-size:.58rem; color:{T["faint"]}; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.2rem; }}
.kpi-val {{ font-family:'IBM Plex Mono',monospace; font-size:1.25rem; font-weight:600; color:{T["primary"]}; }}

.news-card {{
    background:{T["card"]}; border:1px solid {T["border"]};
    border-left:3px solid {T["blue"]};
    padding:.75rem 1rem; margin-bottom:.5rem;
}}
.news-ticker {{ font-family:'IBM Plex Mono',monospace; font-size:.62rem; color:{T["blue"]}; letter-spacing:.1em; text-transform:uppercase; }}
.news-title {{ font-size:.8rem; color:{T["primary"]}; font-weight:500; margin:.2rem 0; line-height:1.4; }}
.news-meta {{ font-family:'IBM Plex Mono',monospace; font-size:.62rem; color:{T["faint"]}; }}

.val-card {{ background:{T["card"]}; border:1px solid {T["border"]}; padding:1rem 1.2rem; margin-bottom:.6rem; }}
.val-title {{ font-family:'IBM Plex Mono',monospace; font-size:.65rem; color:{T["faint"]}; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.6rem; }}

.badge {{ display:inline-block; font-family:'IBM Plex Mono',monospace; font-size:.65rem; font-weight:600; padding:.2rem .6rem; border:1px solid; letter-spacing:.06em; }}
.badge-bear {{ border-color:{T["red"]};   color:{T["red"]};   background:rgba(230,57,70,0.08); }}
.badge-base {{ border-color:{T["amber"]}; color:{T["amber"]}; background:rgba(245,158,11,0.08); }}
.badge-bull {{ border-color:{T["teal"]};  color:{T["teal"]};  background:rgba(45,212,191,0.08); }}

.stTextInput input,.stNumberInput input,.stSelectbox>div>div,input,select,textarea {{
    background:{T["card"]} !important; border:1px solid {T["border"]} !important;
    color:{T["primary"]} !important; font-family:'IBM Plex Mono',monospace !important;
}}
label,.stSelectbox label,.stMultiselect label,.stSlider label,.stTextInput label,.stNumberInput label {{
    font-family:'IBM Plex Mono',monospace !important; font-size:.65rem !important;
    color:{T["faint"]} !important; letter-spacing:.1em !important; text-transform:uppercase !important;
}}
.stButton>button {{
    background:{T["card"]} !important; border:1px solid {T["border"]} !important;
    color:{T["muted"]} !important; font-family:'IBM Plex Mono',monospace !important; font-size:.7rem !important;
}}
.stButton>button:hover {{ border-color:{T["red"]} !important; color:{T["red"]} !important; }}
div[data-testid="stExpander"] {{ background:{T["card"]} !important; border:1px solid {T["border"]} !important; }}
.stAlert {{ background:{T["card"]} !important; border:1px solid {T["border"]} !important; color:{T["muted"]} !important; }}
h1,h2,h3 {{ font-family:'IBM Plex Mono',monospace !important; color:{T["primary"]} !important; }}
hr {{ border-color:{T["border"]} !important; opacity:1 !important; }}
::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background:{T["bg"]}; }}
::-webkit-scrollbar-thumb {{ background:{T["border"]}; border-radius:2px; }}

/* ── Force dark on DataFrame tables ── */
.stDataFrame {{ background:#0d1117 !important; }}
.stDataFrame table {{ background:#0d1117 !important; }}
.stDataFrame thead tr th {{
    background:#0d1117 !important;
    color:#6b7a99 !important;
    border-bottom:1px solid #1e2530 !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:.68rem !important;
}}
.stDataFrame tbody tr td {{
    background:#0d1117 !important;
    color:#9aa3b8 !important;
    border-bottom:1px solid #1e2530 !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:.75rem !important;
}}
.stDataFrame tbody tr:hover td {{ background:#111827 !important; }}

/* ── Number inputs ── */
.stNumberInput input {{
    background:#0d1117 !important;
    border:1px solid #1e2530 !important;
    color:#f0f4ff !important;
    font-family:'IBM Plex Mono',monospace !important;
}}
.stNumberInput > div > div {{
    background:#0d1117 !important;
    border:1px solid #1e2530 !important;
}}

/* ── Radio buttons ── */
.stRadio > div {{ background:#0a0e14 !important; }}
.stRadio label {{
    color:#9aa3b8 !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:.72rem !important;
}}

/* ── Expander content ── */
div[data-testid="stExpander"] > div {{
    background:#0d1117 !important;
    border:none !important;
}}
div[data-testid="stExpanderDetails"] {{
    background:#0d1117 !important;
}}

/* ── Multiselect ── */
.stMultiSelect > div > div {{
    background:#0d1117 !important;
    border:1px solid #1e2530 !important;
    color:#f0f4ff !important;
}}

/* ── Tab panel ── */
div[data-testid="stTabsContent"] {{ background:#0a0e14 !important; }}
[data-baseweb="tab-panel"] {{ background:#0a0e14 !important; }}

/* ── Caption ── */
.stCaptionContainer p, .stCaption, small {{
    color:#6b7a99 !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:.65rem !important;
}}

/* ── Spinner ── */
.stSpinner > div > div {{ border-top-color:#e63946 !important; }}

/* ── Select slider track ── */
.stSlider [data-baseweb="slider"] {{ background:#1e2530 !important; }}

/* ── Notification / warning / info boxes ── */
[data-testid="stNotification"], .stAlert, [data-baseweb="notification"] {{
    background:#0d1117 !important;
    border:1px solid #1e2530 !important;
    color:#9aa3b8 !important;
    font-family:'IBM Plex Mono',monospace !important;
}}

/* ── Tooltip / popover ── */
[data-baseweb="tooltip"] {{ background:#0d1117 !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
DEFAULT_TICKERS = ["BUD","HEINY","CBRL.L","TAP","STZ","DEO","ABEV"]
DEFAULT_NAMES   = {
    "BUD":"Anheuser-Busch InBev","HEINY":"Heineken","CBRL.L":"Carlsberg",
    "TAP":"Molson Coors","STZ":"Constellation Brands","DEO":"Diageo","ABEV":"Ambev",
}
PEER_COLORS = {
    "BUD":T["red"],"HEINY":T["teal"],"CBRL.L":T["blue"],"TAP":T["amber"],
    "STZ":T["purple"],"DEO":"#34d399","ABEV":"#fb923c","_":T["faint"],
}
CACHE_FILE = "/tmp/erd_cache.json"

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
for k,v in {"tickers":DEFAULT_TICKERS.copy(),"focus":"BUD",
            "period":"2y","dcf_tkr":"BUD","_cache":None,
            "dcf_inputs":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────────
def _save(df, px, ts):
    p = {"ts":ts,"fund":df.to_json(orient="records"),
         "prices":px.to_json(orient="split") if not px.empty else None}
    st.session_state["_cache"] = p
    try:
        with open(CACHE_FILE,"w") as f: json.dump(p,f)
    except Exception: pass

def _load():
    p = st.session_state.get("_cache")
    if not p:
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE) as f: p = json.load(f)
        except Exception: pass
    if not p: return None,None,None
    try:
        df  = pd.read_json(p["fund"],orient="records")
        px_ = pd.read_json(p["prices"],orient="split") if p.get("prices") else pd.DataFrame()
        return df,px_,p.get("ts","unknown")
    except Exception: return None,None,None

# ─────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────
def _s(v, d=None):
    """Safe numeric cast — returns d if v is None or NaN."""
    try:
        if v is None: return d
        f = float(v)
        return d if f!=f else f
    except Exception: return d

def _parse_yield(raw):
    if raw is None: return None
    try:
        v = float(raw)
        return round(v,2) if v>0.30 else round(v*100,2)
    except Exception: return None

# ─────────────────────────────────────────────────────────────────
# FETCH FUNCTIONS
# ─────────────────────────────────────────────────────────────────
def _one(tkr):
    """Fetch all data for one ticker across four Yahoo endpoints."""
    d={"ticker":tkr}
    t=yf.Ticker(tkr)
    try:
        fi=t.fast_info
        d["price"] =_s(fi.last_price)
        d["mktcap"]=_s(fi.market_cap)
        d["hi52"]  =_s(fi.fifty_two_week_high)
        d["lo52"]  =_s(fi.fifty_two_week_low)
    except Exception: pass
    try:
        info=t.info
        if info and len(info)>5:
            g=lambda k:_s(info.get(k))
            d["name"]   =info.get("shortName") or tkr
            d["ev"]     =g("enterpriseValue")
            d["ev_ebi"] =g("enterpriseToEbitda")
            d["ev_rev"] =g("enterpriseToRevenue")
            d["pe"]     =g("trailingPE")
            d["pb"]     =g("priceToBook")
            d["dy"]     =g("dividendYield")
            d["beta"]   =g("beta")
            d["short"]  =g("shortPercentOfFloat")
            d["net_mg"] =g("profitMargins")
            d["rev_gr"] =g("revenueGrowth")
            d["debt"]   =g("totalDebt")
            d["cash"]   =g("totalCash")
            d["ebi_i"]  =g("ebitda")
            d["rev_i"]  =g("totalRevenue")
            d["sector"] =info.get("sector","")
    except Exception: pass
    try:
        fs=t.financials
        if fs is not None and not fs.empty:
            col=fs.iloc[:,0]
            def fr(l):
                m=[i for i in col.index if l.lower() in str(i).lower()]
                return float(col[m[0]]) if m else None
            d["rev_f"] =_s(fr("Total Revenue"))
            d["ebi_f"] =_s(fr("EBITDA"))
    except Exception: pass
    try:
        bs=t.balance_sheet
        if bs is not None and not bs.empty:
            col=bs.iloc[:,0]
            def br(l):
                m=[i for i in col.index if l.lower() in str(i).lower()]
                return float(col[m[0]]) if m else None
            d["debt_f"]=_s(br("Total Debt"))
            d["cash_f"]=_s(br("Cash And Cash Equivalents"))
    except Exception: pass
    return d


@st.cache_data(ttl=14400, show_spinner=False)
def fetch_comps(tickers: tuple) -> pd.DataFrame:
    rows=[]
    bar=st.progress(0,text="Fetching market data…")
    for i,tkr in enumerate(tickers):
        bar.progress(i/len(tickers), text=f"Fetching {tkr}… ({i+1}/{len(tickers)})")
        time.sleep(0.8)
        try:
            d=_one(tkr)
            rev   =d.get("rev_f")  or d.get("rev_i")
            ebitda=d.get("ebi_f")  or d.get("ebi_i")
            debt  =d.get("debt_f") or d.get("debt")
            cash  =d.get("cash_f") or d.get("cash")
            price =d.get("price")
            mktcap=d.get("mktcap")
            nd    =(debt-cash) if (debt is not None and cash is not None) else None
            em    =(ebitda/rev) if (ebitda and rev) else None
            nde   =(nd/ebitda)  if (nd is not None and ebitda and ebitda>0) else None
            ev=d.get("ev")
            if not ev and mktcap and nd is not None: ev=mktcap+nd
            ev_e=d.get("ev_ebi") or (round(ev/ebitda,1) if (ev and ebitda and ebitda>0) else None)
            ev_r=d.get("ev_rev") or (round(ev/rev,2)    if (ev and rev and rev>0)        else None)
            rows.append({
                "Ticker":         tkr,
                "Company":        d.get("name",DEFAULT_NAMES.get(tkr,tkr)),
                "Sector":         d.get("sector","—"),
                "Price":          round(price,2)      if price  is not None else None,
                "Mkt Cap ($B)":   round(mktcap/1e9,1) if mktcap is not None else None,
                "EV ($B)":        round(ev/1e9,1)      if ev     is not None else None,
                "52W High":       round(d["hi52"],2)   if d.get("hi52") else None,
                "52W Low":        round(d["lo52"],2)   if d.get("lo52") else None,
                "EV/EBITDA":      ev_e,
                "EV/Revenue":     ev_r,
                "P/E":            round(d["pe"],1)     if d.get("pe")     else None,
                "P/B":            round(d["pb"],2)     if d.get("pb")     else None,
                "EBITDA Margin":  round(em*100,1)      if em              else None,
                "Net Margin":     round(d["net_mg"]*100,1) if d.get("net_mg") else None,
                "Rev Growth YoY": round(d["rev_gr"]*100,1) if d.get("rev_gr") else None,
                "Net Debt/EBITDA":round(nde,1)         if nde is not None else None,
                "Div Yield":      _parse_yield(d.get("dy")),
                "Beta":           round(d["beta"],2)   if d.get("beta")   else None,
                "Short % Float":  round(d["short"]*100,2) if d.get("short") else None,
                "Revenue ($B)":   round(rev/1e9,2)     if rev             else None,
                "EBITDA ($B)":    round(ebitda/1e9,2)  if ebitda          else None,
                "Net Debt ($B)":  round(nd/1e9,2)      if nd is not None  else None,
            })
        except Exception as e:
            st.warning(f"Could not process {tkr}: {e}")
    bar.progress(1.0,text="Done."); time.sleep(0.3); bar.empty()
    return pd.DataFrame(rows)


@st.cache_data(ttl=14400, show_spinner=False)
def fetch_prices(tickers: tuple, period: str) -> pd.DataFrame:
    for attempt in range(3):
        try:
            time.sleep(1.5)
            raw=yf.download(list(tickers),period=period,
                            auto_adjust=True,progress=False,threads=False)
            if isinstance(raw.columns,pd.MultiIndex): raw=raw["Close"]
            elif "Close" in raw.columns: raw=raw[["Close"]]
            if isinstance(raw,pd.Series): raw=raw.to_frame(name=tickers[0])
            raw.dropna(how="all",inplace=True)
            if not raw.empty: return raw.div(raw.iloc[0]).mul(100)
        except Exception: pass
        time.sleep(3*(attempt+1))
    return pd.DataFrame()


@st.cache_data(ttl=14400, show_spinner=False)
def fetch_ohlcv(ticker: str, period: str) -> pd.DataFrame:
    for attempt in range(3):
        try:
            time.sleep(1.5)
            h=yf.Ticker(ticker).history(period=period,auto_adjust=True)
            if not h.empty: return h
        except Exception: pass
        time.sleep(3*(attempt+1))
    return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news(tickers: tuple) -> list:
    """
    Pull recent news for each ticker from Yahoo Finance.
    yfinance .news returns a list of article dicts.
    We normalise the structure (it varies across yfinance versions)
    and sort by publish date so newest articles appear first.
    """
    articles=[]
    for tkr in tickers:
        try:
            time.sleep(0.4)
            raw=yf.Ticker(tkr).news
            if not raw: continue
            for item in raw[:5]:
                # Handle both old and new yfinance news dict structures
                content = item.get("content", {})
                title   = (content.get("title") or item.get("title","")).strip()
                pub     = (content.get("provider",{}).get("displayName","") or
                           item.get("publisher","")).strip()
                link    = (content.get("canonicalUrl",{}).get("url","") or
                           item.get("link","")).strip()
                ts      = (content.get("pubDate","") or
                           item.get("providerPublishTime",""))
                if title:
                    articles.append({"ticker":tkr,"title":title,
                                     "publisher":pub,"link":link,"published":ts})
        except Exception: continue

    def _key(a):
        p=a.get("published","")
        if isinstance(p,int): return p
        try: return int(datetime.strptime(str(p)[:10],"%Y-%m-%d").timestamp())
        except Exception: return 0

    articles.sort(key=_key,reverse=True)
    return articles


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dcf_base(ticker: str) -> dict:
    """Pull historical financials to seed the DCF model."""
    out={}
    try:
        t=yf.Ticker(ticker)
        fi=t.fast_info
        out["price"] =_s(fi.last_price)
        out["shares"]=_s(fi.shares)
        info=t.info
        if info:
            out["net_debt"]=(_s(info.get("totalDebt"),0) or 0)-(_s(info.get("totalCash"),0) or 0)
            out["tax_rate"]=_s(info.get("effectiveTaxRate"),0.25) or 0.25
            out["name"]    =info.get("shortName",ticker)
            out["currency"]=info.get("currency","USD")
        fs=t.financials
        if fs is not None and not fs.empty:
            def fr(l):
                m=[i for i in fs.index if l.lower() in str(i).lower()]
                return [_s(fs.loc[m[0],c]) for c in fs.columns] if m else []
            r=fr("Total Revenue"); e=fr("EBIT"); da=fr("Reconciled Depreciation") or fr("Depreciation")
            out["hist_rev"] =[x/1e9 for x in r[:3]  if x]
            out["hist_ebit"]=[x/1e9 for x in e[:3]  if x]
            out["hist_da"]  =[x/1e9 for x in da[:3] if x]
        cf=t.cashflow
        if cf is not None and not cf.empty:
            def cfr(l):
                m=[i for i in cf.index if l.lower() in str(i).lower()]
                return [_s(cf.loc[m[0],c]) for c in cf.columns] if m else []
            cx=cfr("Capital Expenditure") or cfr("Capex")
            out["hist_capex"]=[abs(x)/1e9 for x in cx[:3] if x]
    except Exception: pass
    return out

# ─────────────────────────────────────────────────────────────────
# DCF ENGINE
# ─────────────────────────────────────────────────────────────────
def run_dcf(base_rev,growth,ebit_margin,tax_rate,da_pct,
            capex_pct,nwc_pct,wacc,tgr,net_debt,shares):
    """
    5-year explicit DCF using Free Cash Flow to Firm (FCFF).
    FCFF = NOPAT + D&A - Capex - change in NWC
    Terminal Value = FCF5 * (1+g) / (WACC - g)  [Gordon Growth]
    EV = PV(FCFs) + PV(TV)
    Equity Value = EV - Net Debt
    Implied Price = Equity Value / Shares
    """
    w=wacc/100; t_=tax_rate/100; g_=tgr/100
    years,revs,ebits,nopats,das,cxs,fcfs,pvs=[],[],[],[],[],[],[],[]
    rev=base_rev
    for yr in range(1,6):
        gr=growth[yr-1]/100; prev=rev; rev=prev*(1+gr)
        ebit=rev*(ebit_margin/100); nopat=ebit*(1-t_)
        da=rev*(da_pct/100); cx=rev*(capex_pct/100)
        dnwc=(rev-prev)*(nwc_pct/100)
        fcf=nopat+da-cx-dnwc
        years.append(f"Year {yr}"); revs.append(round(rev,2))
        ebits.append(round(ebit,2)); nopats.append(round(nopat,2))
        das.append(round(da,2)); cxs.append(round(cx,2))
        fcfs.append(round(fcf,2)); pvs.append(round(fcf/((1+w)**yr),2))
    tv=fcfs[-1]*(1+g_)/(w-g_) if w>g_ else 0
    pv_tv=tv/((1+w)**5); ev=sum(pvs)+pv_tv
    eq=ev-net_debt
    implied=(eq*1e9)/(shares*1e6) if shares else 0
    return {"years":years,"revenue":revs,"ebit":ebits,"nopat":nopats,
            "da":das,"capex":cxs,"fcf":fcfs,"pv_fcf":pvs,
            "sum_pv":round(sum(pvs),2),"tv":round(tv,2),"pv_tv":round(pv_tv,2),
            "ev":round(ev,2),"net_debt":round(net_debt,2),
            "eq_val":round(eq,2),"implied":round(implied,2)}


def sensitivity_table(base_rev,growth,ebit_margin,tax_rate,da_pct,
                      capex_pct,nwc_pct,net_debt,shares,wacc_range,tgr_range):
    rows={}
    for w in wacc_range:
        row={}
        for g in tgr_range:
            if w<=g: row[f"{g:.1f}%"]="—"
            else:
                r=run_dcf(base_rev,growth,ebit_margin,tax_rate,
                          da_pct,capex_pct,nwc_pct,w,g,net_debt,shares)
                row[f"{g:.1f}%"]=r["implied"]
        rows[f"{w:.1f}%"]=row
    return pd.DataFrame(rows).T

# ─────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────
def _c(tkr): return PEER_COLORS.get(tkr, PEER_COLORS["_"])

def chart_prices(df,tickers,focus):
    fig=go.Figure()
    for tkr in tickers:
        if tkr not in df.columns: continue
        fig.add_trace(go.Scatter(
            x=df.index,y=df[tkr],name=tkr,
            line=dict(color=_c(tkr),width=2.5 if tkr==focus else 1.5),
            hovertemplate=f"<b>{tkr}</b><br>%{{x|%d %b %Y}}<br>%{{y:.1f}}<extra></extra>"))
    fig.update_layout(**LAYOUT,height=360,
        title=dict(text="Indexed Price Performance (Base = 100)",font=dict(size=11),x=0),
        yaxis_title="Indexed",hovermode="x unified")
    _ax(fig)
    return fig

def chart_scatter(df,focus):
    df=df.copy()
    if df.index.name=="Ticker": df=df.reset_index()
    if "Ticker" not in df.columns: df["Ticker"]=df.index.astype(str)
    df_s=df.dropna(subset=["EV/EBITDA","Rev Growth YoY","Mkt Cap ($B)"])
    fig=go.Figure()
    if df_s.empty:
        fig.update_layout(**LAYOUT,height=360,
            title=dict(text="EV/EBITDA vs Revenue Growth",font=dict(size=11),x=0))
        _ax(fig)
        fig.add_annotation(text="Insufficient data — EV/EBITDA or Rev Growth unavailable",
            xref="paper",yref="paper",x=0.5,y=0.5,showarrow=False,
            font=dict(color=T["faint"],size=11))
        return fig
    for _,row in df_s.iterrows():
        tkr=row["Ticker"]
        fig.add_trace(go.Scatter(
            x=[row["Rev Growth YoY"]],y=[row["EV/EBITDA"]],
            mode="markers+text",
            marker=dict(size=max(row["Mkt Cap ($B)"]**0.45*6,12),color=_c(tkr),
                        line=dict(width=2 if tkr==focus else 0,
                                  color="#ffffff" if tkr==focus else "rgba(0,0,0,0)"),opacity=0.9),
            text=[tkr],textposition="top center",
            textfont=dict(size=10,color=_c(tkr),family="IBM Plex Mono, monospace"),
            name=tkr,
            hovertemplate=(f"<b>{row['Company']}</b><br>"
                           f"EV/EBITDA: {row['EV/EBITDA']}x<br>"
                           f"Rev Growth: {row['Rev Growth YoY']}%<br>"
                           f"Mkt Cap: ${row['Mkt Cap ($B)']}B<extra></extra>")))
    med=df_s["EV/EBITDA"].median()
    fig.update_layout(**LAYOUT,height=360,showlegend=False,
        title=dict(text="EV/EBITDA vs Revenue Growth",font=dict(size=11),x=0),
        xaxis_title="Rev Growth YoY (%)",yaxis_title="EV/EBITDA (x)")
    _ax(fig)
    fig.add_hline(y=med,line_dash="dash",line_color=T["faint"],
        annotation_text=f"Median {med:.1f}x",annotation_font_size=9)
    return fig

def chart_bar(series,title,suffix,focus):
    s=series.dropna().sort_values()
    fig=go.Figure(go.Bar(x=s.values,y=s.index,orientation="h",
        marker_color=[_c(t) for t in s.index],
        text=[f"{v:.1f}{suffix}" for v in s.values],
        textposition="outside",
        textfont=dict(size=10,family="IBM Plex Mono, monospace")))
    fig.update_layout(**LAYOUT,height=max(240,len(s)*40),
        title=dict(text=title,font=dict(size=11),x=0),showlegend=False)
    _ax(fig)
    fig.update_xaxes(showgrid=False)
    return fig

def chart_leverage(df,focus):
    d=df.set_index("Ticker")["Net Debt/EBITDA"].dropna().sort_values(ascending=False)
    if d.empty: return go.Figure()
    fig=go.Figure(go.Bar(x=d.index,y=d.values,marker_color=[_c(t) for t in d.index],
        text=[f"{v:.1f}x" for v in d.values],textposition="outside",
        textfont=dict(size=10,family="IBM Plex Mono, monospace")))
    fig.update_layout(**LAYOUT,height=280,
        title=dict(text="Net Debt / EBITDA",font=dict(size=11),x=0),
        yaxis_title="Net Debt / EBITDA (x)")
    _ax(fig)
    fig.add_hline(y=3.0,line_dash="dash",line_color=T["red"],
        annotation_text="3.0x",annotation_font_size=9,annotation_font_color=T["red"])
    return fig

def chart_candle(hist,ticker):
    h=hist.copy()
    h["MA50"]=h["Close"].rolling(50).mean()
    h["MA200"]=h["Close"].rolling(200).mean()
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,
                      row_heights=[0.75,0.25],vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=h.index,open=h["Open"],high=h["High"],
        low=h["Low"],close=h["Close"],
        increasing_line_color=T["teal"],decreasing_line_color=T["red"],name="OHLC"),row=1,col=1)
    for ma,col,lbl in [("MA50",T["amber"],"MA 50"),("MA200",T["purple"],"MA 200")]:
        fig.add_trace(go.Scatter(x=h.index,y=h[ma],name=lbl,
            line=dict(color=col,width=1.2,dash="dot")),row=1,col=1)
    clrs=[T["red"] if c<o else T["teal"] for c,o in zip(h["Close"],h["Open"])]
    fig.add_trace(go.Bar(x=h.index,y=h["Volume"],marker_color=clrs,
        name="Volume",showlegend=False),row=2,col=1)
    fig.update_layout(**LAYOUT,height=440,
        title=dict(text=f"{ticker} — Price & Volume | MA50 · MA200",font=dict(size=11),x=0),
        xaxis_rangeslider_visible=False)
    _ax(fig, subplots=True, rows=2, cols=1)
    fig.update_yaxes(title_text="Volume",row=2,col=1)
    return fig

def chart_waterfall(res):
    labels=[f"FCF {y}" for y in res["years"]]+["Terminal Value","Enterprise Value","(Net Debt)","Equity Value"]
    values=res["pv_fcf"]+[res["pv_tv"],0,-res["net_debt"],0]
    measures=["relative"]*5+["relative","total","relative","total"]
    fig=go.Figure(go.Waterfall(
        name="DCF Bridge",orientation="v",measure=measures,x=labels,y=values,
        connector=dict(line=dict(color=T["border"],width=1)),
        increasing=dict(marker_color=T["teal"]),decreasing=dict(marker_color=T["red"]),
        totals=dict(marker_color=T["blue"]),textposition="outside",
        text=[f"${v:.1f}B" if isinstance(v,(int,float)) else "" for v in values],
        textfont=dict(size=9,family="IBM Plex Mono, monospace",color=T["muted"])))
    fig.update_layout(**LAYOUT,height=380,showlegend=False,
        title=dict(text="DCF Value Bridge ($B)",font=dict(size=11),x=0))
    _ax(fig)
    return fig

def chart_fcf(res):
    fig=go.Figure(go.Bar(x=res["years"],y=res["fcf"],
        marker_color=[T["teal"] if v>=0 else T["red"] for v in res["fcf"]],
        text=[f"${v:.2f}B" for v in res["fcf"]],textposition="outside",
        textfont=dict(size=9,family="IBM Plex Mono, monospace")))
    fig.update_layout(**LAYOUT,height=280,
        title=dict(text="Projected Free Cash Flow ($B)",font=dict(size=11),x=0),
        yaxis_title="FCF ($B)",showlegend=False)
    _ax(fig)
    return fig

def chart_heatmap(sens_df, cur_price):
    """
    Sensitivity heatmap: implied share price at each WACC x TGR combination.
    Uses layout_no_margin to avoid TypeError from duplicate margin keyword —
    LAYOUT already contains margin, so we strip it and pass a custom one.
    """
    z = []
    text = []
    for _, row in sens_df.iterrows():
        zr = []
        tr = []
        for v in row.values:
            try:
                val = float(v)
                zr.append(val)
                tr.append(f"${val:.1f}")
            except Exception:
                zr.append(None)
                tr.append("—")
        z.append(zr)
        text.append(tr)

    heatmap = go.Heatmap(
        z=z,
        x=list(sens_df.columns),
        y=list(sens_df.index),
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=9, family="IBM Plex Mono, monospace"),
        colorscale=[[0, T["red"]], [0.5, T["card2"]], [1, T["teal"]]],
        zmid=cur_price,
        showscale=True,
        colorbar=dict(
            tickfont=dict(family="IBM Plex Mono, monospace", size=9),
            title=dict(text="Price ($)", font=dict(size=9)),
        ),
    )

    fig = go.Figure(heatmap)

    # Build layout without margin key to avoid duplicate keyword TypeError
    layout_no_margin = {k: v for k, v in LAYOUT.items() if k != "margin"}

    fig.update_layout(
        **layout_no_margin,
        height=320,
        margin=dict(l=60, r=40, t=40, b=40),
        title=dict(
            text="Sensitivity: Implied Price vs WACC x Terminal Growth Rate",
            font=dict(size=11),
            x=0,
        ),
        xaxis_title="Terminal Growth Rate",
        yaxis_title="WACC",
    )

    return fig

# ─────────────────────────────────────────────────────────────────
# HTML TABLE RENDERER
# st.dataframe uses an iframe shadow DOM that CSS cannot reach,
# so it always renders with a white background regardless of theme.
# The only reliable fix is to render tables as raw HTML using
# st.markdown(unsafe_allow_html=True).
# This function converts a DataFrame to a styled dark HTML table.
# ─────────────────────────────────────────────────────────────────
def dark_table(df: pd.DataFrame, height_px: int = None) -> str:
    """
    Convert a DataFrame to a dark-themed HTML table string.
    Returns HTML that can be passed to st.markdown(unsafe_allow_html=True).
    """
    bg      = T["card"]
    border  = T["border"]
    primary = T["primary"]
    muted   = T["muted"]
    faint   = T["faint"]
    card2   = T["card2"]

    scroll_style = f"max-height:{height_px}px;overflow-y:auto;" if height_px else ""

    html = f"""
    <div style="background:{bg};border:1px solid {border};{scroll_style}overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:.74rem;">
    <thead>
    <tr>
    <th style="background:{bg};color:{faint};font-size:.63rem;letter-spacing:.1em;
               text-transform:uppercase;padding:.5rem .7rem;border-bottom:1px solid {border};
               text-align:left;white-space:nowrap;">{df.index.name or ""}</th>
    """
    for col in df.columns:
        html += f'<th style="background:{bg};color:{faint};font-size:.63rem;letter-spacing:.1em;text-transform:uppercase;padding:.5rem .7rem;border-bottom:1px solid {border};text-align:right;white-space:nowrap;">{col}</th>'
    html += "</tr></thead><tbody>"

    for i, (idx, row) in enumerate(df.iterrows()):
        row_bg = card2 if i % 2 == 1 else bg
        html += f'<tr style="background:{row_bg};">'
        html += f'<td style="color:{faint};padding:.45rem .7rem;border-bottom:1px solid {border};white-space:nowrap;">{idx}</td>'
        for val in row.values:
            # Colour positive/negative values
            if isinstance(val, str):
                color = primary
            elif isinstance(val, (int, float)) and not pd.isna(val):
                color = muted
            else:
                color = faint
                val = "—"
            html += f'<td style="color:{color};padding:.45rem .7rem;border-bottom:1px solid {border};text-align:right;white-space:nowrap;">{val}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


def dark_table_from_styled(df: pd.DataFrame, fmt: dict = None,
                            focus_idx: str = None, height_px: int = None) -> str:
    """
    Render comps-style table with focus row highlight and green/red extremes per column.
    fmt: dict of {col: format_func} same as pandas .format()
    focus_idx: index value to highlight in red
    """
    bg      = T["card"]
    border  = T["border"]
    primary = T["primary"]
    muted   = T["muted"]
    faint   = T["faint"]
    red     = T["red"]
    teal    = T["teal"]

    scroll_style = f"max-height:{height_px}px;overflow-y:auto;" if height_px else ""

    # Pre-compute min/max for numeric columns
    extremes = {}
    for col in df.columns:
        num = pd.to_numeric(df[col], errors="coerce")
        if num.notna().sum() >= 2:
            extremes[col] = {"max": num.idxmax(), "min": num.idxmin()}

    html = f"""
    <div style="background:{bg};border:1px solid {border};{scroll_style}overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:.74rem;">
    <thead><tr>
    <th style="background:{bg};color:{faint};font-size:.62rem;letter-spacing:.12em;
               text-transform:uppercase;padding:.5rem .8rem;
               border-bottom:2px solid {border};text-align:left;">Ticker</th>
    """
    for col in df.columns:
        html += (f'<th style="background:{bg};color:{faint};font-size:.62rem;'
                 f'letter-spacing:.08em;text-transform:uppercase;padding:.5rem .6rem;'
                 f'border-bottom:2px solid {border};text-align:right;white-space:nowrap;">{col}</th>')
    html += "</tr></thead><tbody>"

    for idx, row in df.iterrows():
        is_focus = (idx == focus_idx)
        row_bg   = f"rgba(230,57,70,0.10)" if is_focus else bg
        fw       = "600" if is_focus else "400"
        html += f'<tr style="background:{row_bg};">'
        html += (f'<td style="color:{red if is_focus else faint};font-weight:{fw};'
                 f'padding:.45rem .8rem;border-bottom:1px solid {border};">{idx}</td>')
        for col, val in row.items():
            # Format value
            if fmt and col in fmt:
                try:
                    disp = fmt[col](val) if pd.notna(val) else "—"
                except Exception:
                    disp = "—"
            else:
                disp = str(val) if pd.notna(val) else "—"

            # Colour: focus row uses primary, extremes get teal/red, others get muted
            if is_focus:
                color = primary
            elif col in extremes and idx == extremes[col]["max"]:
                color = teal
            elif col in extremes and idx == extremes[col]["min"]:
                color = red
            else:
                color = muted

            html += (f'<td style="color:{color};font-weight:{fw};padding:.45rem .6rem;'
                     f'border-bottom:1px solid {border};text-align:right;'
                     f'white-space:nowrap;">{disp}</td>')
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:.78rem;'
                f'font-weight:600;color:{T["primary"]};letter-spacing:.05em;'
                f'text-transform:uppercase;margin-bottom:.8rem;">📊 Equity Research</div>',
                unsafe_allow_html=True)

    st.markdown('<div class="slbl">🔍 Add Ticker</div>', unsafe_allow_html=True)
    new_tkr=st.text_input("Add ticker",placeholder="e.g. NVDA, HSBA.L, 2503.T",
                           label_visibility="collapsed")
    ca,cb=st.columns(2)
    with ca:
        if st.button("Add",use_container_width=True):
            t_=new_tkr.strip().upper()
            if t_ and t_ not in st.session_state.tickers:
                st.session_state.tickers.append(t_)
                fetch_comps.clear(); fetch_prices.clear(); fetch_news.clear()
                st.rerun()
    with cb:
        if st.button("Clear all",use_container_width=True):
            st.session_state.tickers=[]; st.session_state.focus=""
            st.rerun()

    if st.session_state.tickers:
        st.markdown('<div class="slbl">📋 Watchlist</div>', unsafe_allow_html=True)
        for tkr in st.session_state.tickers.copy():
            c1,c2=st.columns([4,1])
            with c1:
                is_f=tkr==st.session_state.focus
                st.markdown(f'<span style="font-family:IBM Plex Mono,monospace;font-size:.7rem;'
                            f'color:{T["red"] if is_f else T["muted"]};">'
                            f'{"▶ " if is_f else "  "}{tkr}</span>',
                            unsafe_allow_html=True)
            with c2:
                if st.button("✕",key=f"rm_{tkr}"):
                    st.session_state.tickers.remove(tkr)
                    if st.session_state.focus==tkr:
                        st.session_state.focus=st.session_state.tickers[0] if st.session_state.tickers else ""
                    fetch_comps.clear(); fetch_prices.clear(); fetch_news.clear()
                    st.rerun()

        st.markdown('<div class="slbl">🎯 Focus Ticker</div>', unsafe_allow_html=True)
        fo=st.selectbox("Focus",st.session_state.tickers,
            index=st.session_state.tickers.index(st.session_state.focus)
                  if st.session_state.focus in st.session_state.tickers else 0,
            label_visibility="collapsed")
        if fo!=st.session_state.focus:
            st.session_state.focus=fo; st.rerun()

    st.markdown('<div class="slbl">📅 Price Period</div>', unsafe_allow_html=True)
    pm={"6M":"6mo","1Y":"1y","2Y":"2y","3Y":"3y","5Y":"5y"}
    pl=st.select_slider("Period",list(pm.keys()),value="2Y",label_visibility="collapsed")
    st.session_state.period=pm[pl]

    st.markdown('<div class="slbl">🔄 Data</div>', unsafe_allow_html=True)
    if st.button("Refresh data",use_container_width=True):
        fetch_comps.clear(); fetch_prices.clear()
        fetch_news.clear(); fetch_ohlcv.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:.58rem;'
                f'color:{T["ghost"]};line-height:1.8;">'
                f'Source: Yahoo Finance · yfinance<br>'
                f'Fundamentals cached 4h · News 30m<br>'
                f'{datetime.now().strftime("%d %b %Y %H:%M")} UTC<br><br>'
                f'⚠ LTM only · Not investment advice</div>',
                unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊  Research & Comparables", "📐  Valuation Models"])

# ═════════════════════════════════════════════════════════════════
# TAB 1 — COMPS + NEWS
# ═════════════════════════════════════════════════════════════════
with tab1:
    tickers=st.session_state.tickers
    focus  =st.session_state.focus
    period =st.session_state.period

    st.markdown(f"""
    <div class="hdr">
      <div>
        <div class="hdr-title">Equity Research Dashboard</div>
        <div class="hdr-sub">{len(tickers)} companies · LTM multiples · {datetime.now().strftime('%d %b %Y %H:%M')} UTC</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if not tickers:
        st.markdown(f'<div style="background:{T["card"]};border:1px dashed {T["border"]};'
                    f'padding:3rem;text-align:center;color:{T["faint"]};'
                    f'font-family:IBM Plex Mono,monospace;font-size:.8rem;">'
                    f'Add tickers in the sidebar to get started</div>',
                    unsafe_allow_html=True)
        st.stop()

    # ── Fetch ──
    _status="live"
    with st.spinner("Fetching market data…"):
        df=fetch_comps(tuple(tickers))
        prices=fetch_prices(tuple(tickers),period)

    if not df.empty:
        _ts=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        _save(df,prices,_ts)
    else:
        _cdf,_cpx,_ts=_load()
        if _cdf is not None and not _cdf.empty:
            df=_cdf; prices=_cpx or pd.DataFrame(); _status="cached"
        else:
            st.error("No data available. Yahoo Finance may be rate-limiting. Try again shortly.")
            st.stop()

    # ── Status bar ──
    sc1,sc2=st.columns([5,1])
    with sc1:
        if _status=="live":
            st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:.63rem;'
                        f'color:{T["faint"]};padding:.1rem 0 .5rem;">'
                        f'<span style="color:{T["teal"]};">●</span> LIVE · {_ts}</div>',
                        unsafe_allow_html=True)
        else:
            st.warning(f"⚠ Cached data from **{_ts}**. Click Refresh to retry.",icon="🕐")
    with sc2:
        if st.button("🔄 Refresh",use_container_width=True,key="t1_ref"):
            fetch_comps.clear(); fetch_prices.clear()
            fetch_news.clear(); fetch_ohlcv.clear(); st.rerun()

    # ── KPI strip ──
    fr=df[df["Ticker"]==focus]
    if not fr.empty:
        f=fr.iloc[0]
        st.markdown(f'<div class="slbl">📌 {focus} — KEY METRICS</div>', unsafe_allow_html=True)
        def _fmt(col,pre="",suf="",dec=2):
            v=f.get(col)
            return f"{pre}{v:.{dec}f}{suf}" if pd.notna(v) and v is not None else "—"
        kpis=[
            ("Price",          _fmt("Price","$","",2),         False),
            ("Mkt Cap",        _fmt("Mkt Cap ($B)","$","B",1), False),
            ("EV/EBITDA",      _fmt("EV/EBITDA","","x",1),     True),
            ("EV/Revenue",     _fmt("EV/Revenue","","x",2),    False),
            ("EBITDA Margin",  _fmt("EBITDA Margin","","%",1), False),
            ("Net Debt/EBITDA",_fmt("Net Debt/EBITDA","","x",1),True),
            ("Rev Growth",     _fmt("Rev Growth YoY","","%",1),False),
            ("Short % Float",  _fmt("Short % Float","","%",2), False),
        ]
        cols=st.columns(8)
        for col,(lbl,val,hi) in zip(cols,kpis):
            with col:
                st.markdown(f'<div class="kpi {"hi" if hi else ""}">'
                            f'<div class="kpi-lbl">{lbl}</div>'
                            f'<div class="kpi-val">{val}</div>'
                            f'</div>',unsafe_allow_html=True)

    # ── Comps table ──
    st.markdown('<div class="slbl">📊 TRADING COMPARABLES — LTM</div>', unsafe_allow_html=True)
    dc=["Ticker","Company","Price","Mkt Cap ($B)","EV ($B)",
        "EV/EBITDA","EV/Revenue","P/E","P/B",
        "EBITDA Margin","Net Margin","Rev Growth YoY",
        "Net Debt/EBITDA","Div Yield","Beta","Short % Float"]
    dc=[c for c in dc if c in df.columns]
    dd=df[dc].copy()

    def _sr(row):
        if row.name==focus:
            return [f"background:rgba(230,57,70,0.10);color:{T['primary']};font-weight:600"]*len(row)
        return [f"color:{T['muted']}"]*len(row)

    def _hl(s):
        styles=[""]*len(s); num=pd.to_numeric(s,errors="coerce")
        if num.notna().sum()<2: return styles
        for i,idx in enumerate(s.index):
            if idx==num.idxmax(): styles[i]=f"color:{T['teal']}"
            elif idx==num.idxmin(): styles[i]=f"color:{T['red']}"
        return styles

    fmt_map={
        "Price":          lambda x:f"${x:.2f}"  if pd.notna(x) else "—",
        "Mkt Cap ($B)":   lambda x:f"${x:.1f}B" if pd.notna(x) else "—",
        "EV ($B)":        lambda x:f"${x:.1f}B" if pd.notna(x) else "—",
        "EV/EBITDA":      lambda x:f"{x:.1f}x"  if pd.notna(x) else "—",
        "EV/Revenue":     lambda x:f"{x:.2f}x"  if pd.notna(x) else "—",
        "P/E":            lambda x:f"{x:.1f}x"  if pd.notna(x) else "—",
        "P/B":            lambda x:f"{x:.2f}x"  if pd.notna(x) else "—",
        "EBITDA Margin":  lambda x:f"{x:.1f}%"  if pd.notna(x) else "—",
        "Net Margin":     lambda x:f"{x:.1f}%"  if pd.notna(x) else "—",
        "Rev Growth YoY": lambda x:f"{x:.1f}%"  if pd.notna(x) else "—",
        "Net Debt/EBITDA":lambda x:f"{x:.1f}x"  if pd.notna(x) else "—",
        "Div Yield":      lambda x:f"{x:.2f}%"  if pd.notna(x) else "—",
        "Beta":           lambda x:f"{x:.2f}"   if pd.notna(x) else "—",
        "Short % Float":  lambda x:f"{x:.2f}%"  if pd.notna(x) else "—",
    }
    af={k:v for k,v in fmt_map.items() if k in dc}
    hc=[c for c in ["EV/EBITDA","EV/Revenue","P/E","EBITDA Margin",
                     "Rev Growth YoY","Net Debt/EBITDA"] if c in dc]
    # Render as HTML — st.dataframe uses an iframe shadow DOM that CSS
    # cannot reach, causing a white background regardless of theme settings.
    comps_indexed = dd.set_index("Ticker")
    st.markdown(
        dark_table_from_styled(comps_indexed, fmt=af, focus_idx=focus),
        unsafe_allow_html=True
    )

    with st.expander("📐 Peer median / mean"):
        nc=[c for c in ["EV/EBITDA","EV/Revenue","P/E","EBITDA Margin",
                         "Net Debt/EBITDA","Div Yield"] if c in df.columns]
        sm=df[nc].agg(["median","mean"]).round(2)
        sm.index=["Peer Median","Peer Mean"]
        st.markdown(dark_table(sm), unsafe_allow_html=True)

    # ── Charts ──
    st.markdown('<div class="slbl">📈 PEER COMPARISON CHARTS</div>', unsafe_allow_html=True)
    c1,c2=st.columns([3,2])
    with c1:
        if not prices.empty:
            st.plotly_chart(chart_prices(prices,tickers,focus),
                            use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Price history unavailable")
    with c2:
        st.plotly_chart(chart_scatter(df,focus),
                        use_container_width=True,config={"displayModeBar":False})

    di=df.set_index("Ticker")
    c3,c4=st.columns(2)
    with c3:
        if "EV/EBITDA" in di and di["EV/EBITDA"].notna().any():
            st.plotly_chart(chart_bar(di["EV/EBITDA"],"EV/EBITDA (x)","x",focus),
                            use_container_width=True,config={"displayModeBar":False})
    with c4:
        if "Net Debt/EBITDA" in di and di["Net Debt/EBITDA"].notna().any():
            st.plotly_chart(chart_leverage(df,focus),
                            use_container_width=True,config={"displayModeBar":False})

    c5,c6=st.columns(2)
    with c5:
        if "EBITDA Margin" in di and di["EBITDA Margin"].notna().any():
            st.plotly_chart(chart_bar(di["EBITDA Margin"],"EBITDA Margin (%)","% ",focus),
                            use_container_width=True,config={"displayModeBar":False})
    with c6:
        if "Rev Growth YoY" in di and di["Rev Growth YoY"].notna().any():
            st.plotly_chart(chart_bar(di["Rev Growth YoY"],"Revenue Growth YoY (%)","% ",focus),
                            use_container_width=True,config={"displayModeBar":False})

    # ── Candlestick ──
    st.markdown(f'<div class="slbl">🕯 {focus} — PRICE & VOLUME</div>', unsafe_allow_html=True)
    with st.spinner(f"Loading {focus} OHLCV…"):
        hist=fetch_ohlcv(focus,period)
    if not hist.empty:
        st.plotly_chart(chart_candle(hist,focus),use_container_width=True,
                        config={"displayModeBar":True})
    else:
        st.info(f"OHLCV data unavailable for {focus}")

    # ── News Feed ──
    st.markdown('<div class="slbl">📰 LATEST NEWS</div>', unsafe_allow_html=True)
    st.caption("Recent headlines from Yahoo Finance for all tickers in your watchlist · Refreshes every 30 min")

    with st.spinner("Loading news…"):
        news=fetch_news(tuple(tickers))

    if news:
        nf1,nf2=st.columns([2,4])
        with nf1:
            nf=st.selectbox("Filter by ticker",["All"]+sorted(set(a["ticker"] for a in news)),
                             label_visibility="collapsed")
        filtered=news if nf=="All" else [a for a in news if a["ticker"]==nf]
        for article in filtered[:20]:
            tkr  =article.get("ticker","")
            title=article.get("title","")
            pub  =article.get("publisher","")
            link =article.get("link","")
            ts   =article.get("published","")
            ts_str=""
            if isinstance(ts,int):
                try: ts_str=datetime.fromtimestamp(ts).strftime("%d %b %Y")
                except Exception: pass
            elif isinstance(ts,str) and ts:
                ts_str=ts[:10]
            if not title: continue
            title_html=(f'<a href="{link}" target="_blank" style="color:{T["primary"]};'
                        f'text-decoration:none;">{title}</a>' if link else title)
            st.markdown(f"""
            <div class="news-card">
              <div class="news-ticker">{tkr}</div>
              <div class="news-title">{title_html}</div>
              <div class="news-meta">{pub}{" · "+ts_str if ts_str else ""}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No news available at this time.")

# ═════════════════════════════════════════════════════════════════
# TAB 2 — VALUATION
# ═════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"""
    <div class="hdr" style="border-left-color:{T['blue']};">
      <div>
        <div class="hdr-title">Valuation Models</div>
        <div class="hdr-sub">DCF · EV/EBITDA Exit Multiple · Football Field</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Model selector
    model=st.radio("Model",
        ["DCF — Discounted Cash Flow",
         "EV/EBITDA Exit Multiple",
         "Football Field (Combined Ranges)"],
        horizontal=True,label_visibility="collapsed")

    # Ticker input
    v1,v2=st.columns([2,4])
    with v1:
        dcf_tkr=st.text_input("Ticker to value",value=st.session_state.dcf_tkr,
                               placeholder="e.g. BUD").strip().upper()
        if dcf_tkr!=st.session_state.dcf_tkr:
            st.session_state.dcf_tkr=dcf_tkr; fetch_dcf_base.clear(); st.rerun()
        st.button("Load financials →",use_container_width=True)

    base={}
    if dcf_tkr:
        with st.spinner(f"Loading {dcf_tkr} financials…"):
            base=fetch_dcf_base(dcf_tkr)

    cur_price =base.get("price",0) or 0
    cur_name  =base.get("name",dcf_tkr)
    shares_m  =(base.get("shares") or 1000e6)/1e6
    net_debt  =(base.get("net_debt") or 0)/1e9
    tax_rate  =(base.get("tax_rate") or 0.25)*100
    hist_rev  =base.get("hist_rev",[])
    base_rev_d=hist_rev[0] if hist_rev else 10.0

    with v2:
        if cur_price:
            st.markdown(f"""
            <div class="val-card" style="margin-top:0;">
              <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                <div><div class="kpi-lbl">Company</div><div class="kpi-val" style="font-size:.9rem;">{cur_name}</div></div>
                <div><div class="kpi-lbl">Current Price</div><div class="kpi-val" style="color:{T['blue']};">${cur_price:.2f}</div></div>
                <div><div class="kpi-lbl">Shares (M)</div><div class="kpi-val" style="font-size:.9rem;">{shares_m:.0f}M</div></div>
                <div><div class="kpi-lbl">Net Debt ($B)</div><div class="kpi-val" style="font-size:.9rem;">${net_debt:.1f}B</div></div>
                <div><div class="kpi-lbl">Tax Rate</div><div class="kpi-val" style="font-size:.9rem;">{tax_rate:.1f}%</div></div>
              </div>
            </div>""", unsafe_allow_html=True)

    # ─────── DCF ───────
    if "DCF" in model:
        st.markdown('<div class="slbl">⚙️ DCF ASSUMPTIONS</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="val-card">
          <div class="val-title">Model overview</div>
          <div style="font-size:.78rem;color:{T['muted']};line-height:1.7;">
          Projects <b style="color:{T['primary']}">Free Cash Flow to Firm (FCFF)</b> over 5 years.
          FCFF = NOPAT + D&A − Capex − ΔNWC. Terminal value via
          <b style="color:{T['primary']}">Gordon Growth Model</b>: FCF₅ × (1+g) / (WACC−g).
          EV = PV(FCFs) + PV(TV). Equity Value = EV − Net Debt.
          Implied Price = Equity Value / Diluted Shares.
          </div>
        </div>""", unsafe_allow_html=True)

        # Scenario presets
        SCENARIOS={
            "Bear": dict(g=[-2,-3,-4,-4,-3],margin=18.0,wacc=9.5,tgr=0.5, da=5.0,cx=6.0,nwc=2.0),
            "Base": dict(g=[1,  2,  2,  3,  3],margin=22.0,wacc=8.0,tgr=1.5, da=5.0,cx=5.5,nwc=2.0),
            "Bull": dict(g=[3,  4,  4,  5,  5],margin=25.0,wacc=7.0,tgr=2.0, da=5.0,cx=5.0,nwc=2.0),
        }
        if st.session_state.dcf_inputs is None:
            st.session_state.dcf_inputs=dict(SCENARIOS["Base"],base_rev=base_rev_d)

        st.markdown('<div class="slbl">📋 SCENARIO PRESETS</div>', unsafe_allow_html=True)
        p1,p2,p3,_=st.columns(4)
        def _ls(s):
            st.session_state.dcf_inputs=dict(SCENARIOS[s],base_rev=base_rev_d); st.rerun()
        with p1:
            st.markdown('<span class="badge badge-bear">BEAR</span>',unsafe_allow_html=True)
            if st.button("Load Bear",use_container_width=True): _ls("Bear")
        with p2:
            st.markdown('<span class="badge badge-base">BASE</span>',unsafe_allow_html=True)
            if st.button("Load Base",use_container_width=True): _ls("Base")
        with p3:
            st.markdown('<span class="badge badge-bull">BULL</span>',unsafe_allow_html=True)
            if st.button("Load Bull",use_container_width=True): _ls("Bull")

        inp=st.session_state.dcf_inputs
        st.markdown('<div class="slbl">📥 INPUTS</div>', unsafe_allow_html=True)
        ia,ib=st.columns(2)
        with ia:
            st.markdown(f'<div class="val-title">Revenue & Margins</div>',unsafe_allow_html=True)
            base_rev =st.number_input("Base Year Revenue ($B)",      value=float(inp.get("base_rev",base_rev_d)),step=0.5,format="%.2f")
            g1=st.number_input("Revenue Growth Year 1 (%)",          value=float(inp["g"][0]),step=0.5,format="%.1f")
            g2=st.number_input("Revenue Growth Year 2 (%)",          value=float(inp["g"][1]),step=0.5,format="%.1f")
            g3=st.number_input("Revenue Growth Year 3 (%)",          value=float(inp["g"][2]),step=0.5,format="%.1f")
            g4=st.number_input("Revenue Growth Year 4 (%)",          value=float(inp["g"][3]),step=0.5,format="%.1f")
            g5=st.number_input("Revenue Growth Year 5 (%)",          value=float(inp["g"][4]),step=0.5,format="%.1f")
            ebit_mg=st.number_input("EBIT Margin (%)",                value=float(inp["margin"]),step=0.5,format="%.1f")
        with ib:
            st.markdown(f'<div class="val-title">Capital & Discount Rate</div>',unsafe_allow_html=True)
            da_pct =st.number_input("D&A as % of Revenue",           value=float(inp["da"]),  step=0.25,format="%.2f")
            cx_pct =st.number_input("Capex as % of Revenue",         value=float(inp["cx"]),  step=0.25,format="%.2f")
            nwc_pct=st.number_input("Δ NWC as % of Revenue Change",  value=float(inp["nwc"]), step=0.25,format="%.2f")
            tx_rate=st.number_input("Tax Rate (%)",                   value=float(tax_rate),   step=0.5, format="%.1f")
            wacc   =st.number_input("WACC (%)",                       value=float(inp["wacc"]),step=0.25,format="%.2f")
            tgr    =st.number_input("Terminal Growth Rate (%)",       value=float(inp["tgr"]), step=0.25,format="%.2f")
            nd_in  =st.number_input("Net Debt ($B)",                  value=float(net_debt),   step=0.5, format="%.2f")
            sh_in  =st.number_input("Diluted Shares (M)",             value=float(shares_m),   step=10.0,format="%.0f")

        res=run_dcf(base_rev,[g1,g2,g3,g4,g5],ebit_mg,tx_rate,da_pct,cx_pct,nwc_pct,wacc,tgr,nd_in,sh_in)

        # Output
        st.markdown('<div class="slbl">📤 OUTPUT</div>', unsafe_allow_html=True)
        ud=((res["implied"]/cur_price)-1)*100 if cur_price else 0
        udc=T["teal"] if ud>=0 else T["red"]
        udl=f"↑ {ud:.1f}%" if ud>=0 else f"↓ {abs(ud):.1f}%"

        oa,ob,oc,od,oe=st.columns(5)
        for col,(lbl,val,hi) in zip([oa,ob,oc,od,oe],[
            ("Implied Price",  f"${res['implied']:.2f}",True),
            ("Current Price",  f"${cur_price:.2f}" if cur_price else "—",False),
            ("Upside/Downside",udl,False),
            ("Enterprise Value",f"${res['ev']:.1f}B",False),
            ("Equity Value",    f"${res['eq_val']:.1f}B",False),
        ]):
            with col:
                ov=f"color:{udc};" if lbl=="Upside/Downside" else ""
                st.markdown(f'<div class="kpi {"hi" if hi else ""}">'
                            f'<div class="kpi-lbl">{lbl}</div>'
                            f'<div class="kpi-val" style="font-size:1.1rem;{ov}">{val}</div>'
                            f'</div>',unsafe_allow_html=True)

        # Projection table
        st.markdown('<div class="slbl">📋 YEAR-BY-YEAR PROJECTION</div>', unsafe_allow_html=True)
        dcf_df=pd.DataFrame({
            "":["Revenue ($B)","EBIT ($B)","NOPAT ($B)","D&A ($B)","Capex ($B)","FCF ($B)","PV of FCF ($B)"],
            **{y:[r,e,n,d,c,f,p] for y,r,e,n,d,c,f,p in zip(
                res["years"],res["revenue"],res["ebit"],res["nopat"],
                res["da"],res["capex"],res["fcf"],res["pv_fcf"])}
        }).set_index("")
        # Render as HTML to guarantee dark background
        fmt_dcf = {col: (lambda x: f"{x:.2f}" if pd.notna(x) else "—")
                   for col in dcf_df.columns}
        st.markdown(dark_table(dcf_df, height_px=300), unsafe_allow_html=True)

        st.markdown(f"""
        <div class="val-card">
          <div style="display:flex;gap:2rem;flex-wrap:wrap;font-family:'IBM Plex Mono',monospace;font-size:.75rem;">
            <div><span style="color:{T['faint']};">PV of FCFs: </span><span style="color:{T['primary']};">${res['sum_pv']:.2f}B</span></div>
            <div><span style="color:{T['faint']};">Terminal Value: </span><span style="color:{T['primary']};">${res['tv']:.2f}B</span></div>
            <div><span style="color:{T['faint']};">PV of Terminal Value: </span><span style="color:{T['primary']};">${res['pv_tv']:.2f}B</span></div>
            <div><span style="color:{T['faint']};">TV as % of EV: </span><span style="color:{T['amber']};">{res['pv_tv']/res['ev']*100:.1f}%</span></div>
          </div>
        </div>""", unsafe_allow_html=True)

        ch1,ch2=st.columns(2)
        with ch1:
            st.plotly_chart(chart_fcf(res),use_container_width=True,config={"displayModeBar":False})
        with ch2:
            st.plotly_chart(chart_waterfall(res),use_container_width=True,config={"displayModeBar":False})

        # Sensitivity
        st.markdown('<div class="slbl">📊 SENSITIVITY — WACC × TERMINAL GROWTH RATE</div>', unsafe_allow_html=True)
        st.caption("Implied share price at each WACC/TGR combination. Green = above current price. Red = below.")
        wr=[round(wacc-2+i*0.5,1) for i in range(9)]
        gr=[round(tgr-1+i*0.5,1)  for i in range(7)]
        wr=[w for w in wr if w>0]; gr=[g for g in gr if g>=0]
        with st.spinner("Computing sensitivity…"):
            sens=sensitivity_table(base_rev,[g1,g2,g3,g4,g5],ebit_mg,tx_rate,
                                   da_pct,cx_pct,nwc_pct,nd_in,sh_in,wr,gr)
        st.plotly_chart(chart_heatmap(sens,cur_price),
                        use_container_width=True,config={"displayModeBar":False})

    # ─────── EV/EBITDA Exit ───────
    elif "Exit" in model:
        st.markdown('<div class="slbl">⚙️ EV/EBITDA EXIT MULTIPLE ASSUMPTIONS</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="val-card">
          <div class="val-title">How this model works</div>
          <div style="font-size:.78rem;color:{T['muted']};line-height:1.7;">
          Project forward EBITDA using revenue growth and margin assumptions.
          Apply an exit EV/EBITDA multiple — anchor this to where the peer group
          trades today (visible in Tab 1). Discount the implied Enterprise Value
          back at WACC. Subtract net debt to get equity value and implied price.
          This is the standard <b style="color:{T['primary']}">Private Equity</b> entry/exit framework.
          </div>
        </div>""", unsafe_allow_html=True)

        ea,eb=st.columns(2)
        with ea:
            em_rev   =st.number_input("Current Revenue ($B)",       value=float(base_rev_d),step=0.5, format="%.2f")
            em_gr    =st.number_input("Revenue CAGR (%)",           value=3.0,              step=0.5, format="%.1f")
            em_margin=st.number_input("Exit Year EBITDA Margin (%)",value=22.0,             step=0.5, format="%.1f")
            em_yrs   =st.number_input("Holding Period (years)",     value=5,                step=1,   format="%d")
        with eb:
            em_mult  =st.number_input("Exit EV/EBITDA Multiple (x)",value=10.0,             step=0.5, format="%.1f")
            em_wacc  =st.number_input("Discount Rate / WACC (%)",   value=8.0,              step=0.25,format="%.2f")
            em_nd    =st.number_input("Current Net Debt ($B)",       value=float(net_debt),  step=0.5, format="%.2f")
            em_sh    =st.number_input("Diluted Shares (M)",          value=float(shares_m),  step=10.0,format="%.0f")

        exit_rev    =em_rev*((1+em_gr/100)**em_yrs)
        exit_ebitda =exit_rev*(em_margin/100)
        exit_ev     =exit_ebitda*em_mult
        pv_ev       =exit_ev/((1+em_wacc/100)**em_yrs)
        eq_em       =pv_ev-em_nd
        implied_em  =(eq_em*1e9)/(em_sh*1e6) if em_sh else 0
        ud_em       =((implied_em/cur_price)-1)*100 if cur_price else 0
        udc_em      =T["teal"] if ud_em>=0 else T["red"]

        st.markdown('<div class="slbl">📤 OUTPUT</div>', unsafe_allow_html=True)
        ma,mb,mc,md,me=st.columns(5)
        for col,(lbl,val,hi) in zip([ma,mb,mc,md,me],[
            ("Implied Price",    f"${implied_em:.2f}",True),
            ("Exit EBITDA",      f"${exit_ebitda:.2f}B",False),
            ("Exit EV",          f"${exit_ev:.1f}B",False),
            ("PV of Exit EV",    f"${pv_ev:.1f}B",False),
            ("Upside/Downside",  f"{'↑' if ud_em>=0 else '↓'} {abs(ud_em):.1f}%",False),
        ]):
            with col:
                ov=f"color:{udc_em};" if lbl=="Upside/Downside" else ""
                st.markdown(f'<div class="kpi {"hi" if hi else ""}">'
                            f'<div class="kpi-lbl">{lbl}</div>'
                            f'<div class="kpi-val" style="font-size:1.1rem;{ov}">{val}</div>'
                            f'</div>',unsafe_allow_html=True)

    # ─────── Football Field ───────
    elif "Football" in model:
        st.markdown('<div class="slbl">⚽ FOOTBALL FIELD — VALUATION RANGE SUMMARY</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="val-card">
          <div class="val-title">What is a football field chart?</div>
          <div style="font-size:.78rem;color:{T['muted']};line-height:1.7;">
          Aggregates multiple valuation methodologies into a single range chart —
          the standard format used in investment bank pitchbooks. Each bar shows
          the implied share price range from one methodology. Enter your ranges below.
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="slbl">📥 ENTER RANGES</div>', unsafe_allow_html=True)
        methods=["DCF (Bear–Bull)","EV/EBITDA Exit","52-Week Trading Range",
                 "Analyst Price Targets","Precedent Transactions"]
        ff_data=[]
        for mth in methods:
            fa,fb,fc=st.columns([3,2,2])
            with fa:
                st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:.72rem;'
                            f'color:{T["muted"]};padding:.5rem 0;">{mth}</div>',
                            unsafe_allow_html=True)
            with fb: lo=st.number_input("Low", key=f"lo_{mth}",value=float(cur_price*0.7 if cur_price else 50),step=1.0,format="%.2f",label_visibility="collapsed")
            with fc: hi=st.number_input("High",key=f"hi_{mth}",value=float(cur_price*1.3 if cur_price else 90),step=1.0,format="%.2f",label_visibility="collapsed")
            ff_data.append((mth,lo,hi))

        fig_ff=go.Figure()
        for mth,lo,hi in ff_data:
            fig_ff.add_trace(go.Bar(
                x=[hi-lo],y=[mth],base=lo,orientation="h",
                marker_color=T["blue"],marker_opacity=0.75,showlegend=False,
                hovertemplate=f"<b>{mth}</b><br>Low: ${lo:.2f}<br>High: ${hi:.2f}<extra></extra>"))
        if cur_price:
            fig_ff.add_vline(x=cur_price,line_dash="dash",line_color=T["amber"],
                annotation_text=f"Current ${cur_price:.2f}",
                annotation_font_size=10,annotation_font_color=T["amber"])
        fig_ff.update_layout(**LAYOUT,height=340,showlegend=False,
            title=dict(text="Football Field — Implied Share Price Range by Methodology",
                       font=dict(size=11),x=0),
            xaxis_title="Implied Share Price ($)",barmode="overlay")
        _ax(fig_ff)
        st.plotly_chart(fig_ff,use_container_width=True,config={"displayModeBar":False})

    # Methodology notes
    with st.expander("📖 Methodology notes"):
        st.markdown(f"""
<div style="font-size:.78rem;color:{T['muted']};line-height:1.9;font-family:'IBM Plex Sans',sans-serif;">

**DCF — Discounted Cash Flow**
FCFF = NOPAT + D&A − Capex − ΔNWC. Terminal value via Gordon Growth Model.
EV = PV(FCFs) + PV(TV). Equity Value = EV − Net Debt. Implied Price = Equity / Shares.

**EV/EBITDA Exit Multiple**
Projects EBITDA forward, applies a peer-derived exit multiple to get future EV,
discounts back at WACC. Exit multiple should be anchored to current peer group comps (Tab 1).
Standard PE entry/exit framework.

**Football Field**
Aggregates methodology ranges into a single chart. Standard pitchbook format.
Prevents false precision — shows a range of outcomes rather than a single number.

**Key sensitivities:**
- Terminal value is typically 60–80% of total DCF value — TGR assumption is critical
- 1% WACC change moves implied value significantly — use the sensitivity heatmap
- EBIT margin is the biggest FCF driver — small changes compound over 5 years

**Limitations:** All assumptions are user-inputted. LTM data from Yahoo Finance only.
Not investment advice.
</div>""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:.6rem;color:{T["ghost"]}; '
            f'text-align:center;padding:.4rem 0 .8rem;line-height:1.9;">'
            f'Data: Yahoo Finance · yfinance · LTM multiples only · Not investment advice · '
            f'Built for portfolio demonstration · {datetime.now().year}</div>',
            unsafe_allow_html=True)
