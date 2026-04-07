"""
Dashboard Energético Unificado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Combina:
  • EIA Energy Markets: precios spot históricos, futuros en tiempo real (Yahoo Finance),
    producción y almacenamiento de EE.UU.
  • Combustibles Argentina: precios en surtidor por provincia, producto y bandera
    (Fuente: datos.energia.gob.ar)

Instalación:
    pip install streamlit plotly pandas requests yfinance

Ejecución:
    streamlit run dashboard_energia.py

API Key EIA en .streamlit/secrets.toml:
    EIA_API_KEY = "tu_clave_aqui"
"""

# ─────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────
import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
from io import BytesIO
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Energético",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_BG      = "#f7f8fc"
C_SURFACE = "#ffffff"
C_BORDER  = "#dfe3eb"
C_BORDER2 = "#c7cfdb"
C_TEXT    = "#0f172a"
C_MUTED   = "#334155"
C_LINE    = "#2563eb"
C_LINE2   = "#60a5fa"
C_POS     = "#0f9f6e"
C_NEG     = "#dc2626"

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    background-color: {C_BG};
    color: {C_TEXT};
}}
.stApp {{ background-color: {C_BG}; }}
.block-container {{ padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1380px; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {C_SURFACE} !important;
    border-right: 1px solid {C_BORDER};
}}
[data-testid="stSidebar"] * {{ color: {C_MUTED} !important; }}
[data-testid="stSidebar"] label {{
    color: {C_MUTED} !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.3px;
}}
[data-testid="stSidebar"] .stTextInput input {{
    background: {C_BG} !important;
    border: 1px solid {C_BORDER2} !important;
    color: {C_TEXT} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    border-radius: 3px !important;
    padding: 6px 10px !important;
}}
[data-testid="stSidebar"] .stButton button {{
    background: {C_BG} !important;
    border: 1px solid {C_BORDER2} !important;
    color: {C_MUTED} !important;
    font-size: 0.78rem !important;
    border-radius: 3px !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    border-color: {C_TEXT} !important;
    color: {C_TEXT} !important;
}}

/* Header */
.dash-header {{
    background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
    border: 1px solid {C_BORDER};
    border-radius: 18px;
    padding: 20px 22px 16px 22px;
    margin-bottom: 22px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}}
.dash-header h1 {{
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: {C_TEXT};
    letter-spacing: -0.5px;
    margin: 0 0 6px 0;
}}
.dash-header .sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: {C_MUTED};
    letter-spacing: 0.4px;
}}

/* KPI grid (EIA) */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
    gap: 0;
    border: 1px solid {C_BORDER};
    margin-bottom: 40px;
}}
.kpi-card {{
    background: {C_BG};
    padding: 22px 24px;
    border-right: 1px solid {C_BORDER};
    border-bottom: 1px solid {C_BORDER};
}}
.kpi-card:last-child {{ border-right: none; }}
.kpi-card .label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.6rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {C_MUTED};
    margin-bottom: 12px;
    font-weight: 600;
}}
.kpi-card .price {{
    font-family: 'Inter', sans-serif;
    font-size: 1.7rem;
    font-weight: 600;
    color: {C_TEXT};
    line-height: 1;
    letter-spacing: -0.5px;
}}
.kpi-card .unit {{
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem;
    color: {C_MUTED};
    margin-top: 5px;
    letter-spacing: 0.3px;
}}
.kpi-card .chg {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    margin-top: 12px;
    letter-spacing: 0.2px;
    font-weight: 500;
}}
.kpi-card .date {{
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    color: {C_MUTED};
    margin-top: 6px;
    letter-spacing: 0.2px;
    font-weight: 500;
}}
.pos {{ color: {C_POS}; font-weight: 500; }}
.neg {{ color: {C_NEG}; font-weight: 500; }}
.neu {{ color: {C_MUTED}; }}

/* KPI card (combustibles AR) */
.ar-kpi-card {{
    background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
    border: 1px solid {C_BORDER};
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 10px 24px rgba(15,23,42,0.05);
    min-height: 92px;
}}
.ar-kpi-card .ar-kpi-title {{
    font-size: 0.76rem;
    color: {C_MUTED};
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    font-weight: 600;
}}
.ar-kpi-card .ar-kpi-value {{
    font-size: 1.55rem;
    font-weight: 700;
    color: {C_TEXT};
    line-height: 1.15;
    letter-spacing: -0.3px;
}}

/* Section label */
.sec-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {C_MUTED};
    border-bottom: 1px solid {C_BORDER};
    padding-bottom: 10px;
    margin-bottom: 24px;
    margin-top: 12px;
    font-weight: 600;
}}

/* Live badge */
.live-badge {{
    display: inline-block;
    border: 1px solid {C_BORDER2};
    color: {C_MUTED};
    font-family: 'Inter', sans-serif;
    font-size: 0.5rem;
    letter-spacing: 1px;
    padding: 1px 5px;
    border-radius: 2px;
    vertical-align: middle;
    margin-left: 8px;
    text-transform: uppercase;
}}

/* Futures table */
.fut-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
.fut-table th {{
    font-family: 'Inter', sans-serif;
    font-size: 0.57rem;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: {C_MUTED};
    border-bottom: 2px solid {C_TEXT};
    padding: 8px 14px;
    text-align: left;
    font-weight: 600;
}}
.fut-table td {{
    padding: 11px 14px;
    border-bottom: 1px solid {C_BORDER};
    color: {C_TEXT};
    vertical-align: middle;
}}
.fut-table tr:hover td {{ background: {C_SURFACE}; }}
.fut-price {{
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    color: {C_TEXT};
}}
.fut-name  {{ font-weight: 600; color: {C_TEXT}; }}
.fut-ticker {{
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    color: {C_MUTED};
    display: block;
    margin-top: 2px;
}}

/* Var strip */
.var-strip {{
    display: flex;
    gap: 0;
    border: 1px solid {C_BORDER};
    margin-top: 8px;
    margin-bottom: 28px;
}}
.var-cell {{
    flex: 1;
    padding: 14px 18px;
    border-right: 1px solid {C_BORDER};
}}
.var-cell:last-child {{ border-right: none; }}
.var-cell .var-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.57rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {C_MUTED};
    margin-bottom: 6px;
    font-weight: 600;
}}
.var-cell .var-val {{
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
}}

/* Info box */
.info-box {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-left: 3px solid {C_TEXT};
    border-radius: 2px;
    padding: 18px 22px;
    font-size: 0.83rem;
    color: {C_MUTED};
    margin-bottom: 20px;
    font-family: 'Inter', sans-serif;
    line-height: 1.7;
}}
.info-box a {{ color: {C_TEXT}; text-decoration: underline; }}
.info-box code {{
    background: {C_BG};
    padding: 2px 7px;
    border-radius: 2px;
    font-size: 0.8rem;
    color: {C_TEXT};
    border: 1px solid {C_BORDER2};
}}

/* Footer */
.footer {{
    font-family: 'Inter', sans-serif;
    font-size: 0.58rem;
    color: {C_MUTED};
    text-align: center;
    margin-top: 52px;
    padding-top: 16px;
    border-top: 1px solid {C_BORDER};
    letter-spacing: 0.3px;
}}

/* Streamlit overrides */
div[data-testid="stSelectbox"] > div > div {{
    background: #ffffff !important;
    border: 1px solid {C_BORDER2} !important;
    color: {C_TEXT} !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    min-height: 44px !important;
    transition: all 0.18s ease !important;
}}

div[data-testid="stSelectbox"] > div > div:hover {{
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.12) !important;
    cursor: pointer !important;
}}

div[data-testid="stSelectbox"] > div > div:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.18) !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    cursor: pointer !important;
}}

div[data-testid="stSelectbox"] svg {{
    color: #2563eb !important;
}}
/* Tabs + widgets */
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
.stTabs [data-baseweb="tab"] {{
    height: 40px;
    background: #eef3ff;
    border: 1px solid #d9e5ff;
    border-radius: 10px 10px 0 0;
    color: #37517e;
    padding: 0 14px;
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    background: #2563eb !important;
    color: white !important;
    border-color: #2563eb !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ background: transparent !important; }}
[data-testid="stSelectbox"] label, [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{
    color: {C_MUTED} !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}}
[data-testid="stRadio"] [role="radiogroup"] {{ gap: 10px; }}
[data-testid="stRadio"] label[data-baseweb="radio"] {{
    background: #ffffff;
    border: 1px solid {C_BORDER2};
    border-radius: 999px;
    padding: 6px 12px;
    min-height: 38px;
}}
[data-testid="stRadio"] label[data-baseweb="radio"] * {{
    color: {C_TEXT} !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}}
[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {{
    background: #eff6ff;
    border-color: #93c5fd;
    box-shadow: inset 0 0 0 1px #bfdbfe;
}}
[data-testid="stCheckbox"] div[role="checkbox"] {{
    border-color: {C_BORDER2} !important;
    background: #ffffff !important;
}}
[data-testid="stCheckbox"] label * {{
    color: {C_TEXT} !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}}
[data-testid="stCheckbox"] input:checked + div {{
    background: #2563eb !important;
    border-color: #2563eb !important;
}}
.stDownloadButton button {{
    background: #ffffff !important;
    border: 1px solid {C_BORDER2} !important;
    color: {C_TEXT} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 40px;
}}
.stDownloadButton button:hover {{
    border-color: #2563eb !important;
    color: #2563eb !important;
}}
.stAlert {{ border-radius: 14px; border: 1px solid {C_BORDER}; }}
/* Panels */
.panel {{
    background: white;
    border: 1px solid {C_BORDER};
    border-radius: 20px;
    padding: 18px 18px 10px 18px;
    box-shadow: 0 10px 24px rgba(15,23,42,0.05);
    margin-bottom: 18px;
}}
.panel-title {{
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    color: {C_MUTED};
    margin-bottom: 12px;
}}
.section-title-ar {{
    margin-top: 8px;
    margin-bottom: 14px;
}}
.section-title-ar .eyebrow {{
    display: inline-block;
    font-size: 0.72rem;
    color: #2563eb;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
.section-title-ar h3 {{
    margin: 0;
    font-size: 1.35rem;
    line-height: 1.2;
    color: {C_TEXT};
}}
.section-title-ar .meta {{
    margin-top: 6px;
    color: {C_MUTED};
    font-size: 0.88rem;
}}
.chart-note {{
    color: {C_MUTED};
    font-size: 0.78rem;
    margin-top: 8px;
}}

.stSpinner > div {{ border-top-color: {C_TEXT} !important; }}
div[data-testid="stDataFrameContainer"] {{
    border: 1px solid {C_BORDER} !important;
    border-radius: 2px;
}}

/* FIX títulos que no se ven */
h1, h2, h3, h4, strong {{
    color: #0f172a !important;
}}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  SHARED HELPERS
# ═══════════════════════════════════════════════════════
def fmt(value: float, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    formatted = f"{abs(value):,.{decimals}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-{formatted}" if value < 0 else formatted

def fmt_pct_eia(value: float) -> str:
    s = fmt(abs(value), 2)
    sign = "+" if value >= 0 else "-"
    return f"{sign}{s}%"

def fmt_ars(x, dec=2):
    if pd.isna(x):
        return "—"
    s = f"{x:,.{dec}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}"

def fmt_pct_ar(x, dec=1):
    if pd.isna(x):
        return "—"
    s = f"{x:.{dec}f}".replace(".", ",")
    return f"{s}%"

def hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ═══════════════════════════════════════════════════════
#  EIA — CONFIGURATION & DATA
# ═══════════════════════════════════════════════════════
BASE_URL = "https://api.eia.gov/v2"

COMMODITIES = {
    "WTI Crude Oil": {
        "route": "petroleum/pri/spt/data",
        "facet_key": "series", "facet_val": "RWTC",
        "unit": "$/bbl", "icon": "WTI", "freq": "daily",
    },
    "Brent Crude Oil": {
        "route": "petroleum/pri/spt/data",
        "facet_key": "series", "facet_val": "RBRTE",
        "unit": "$/bbl", "icon": "BRT", "freq": "daily",
    },
    "RBOB Gasoline": {
        "route": "petroleum/pri/spt/data",
        "facet_key": "series", "facet_val": "EER_EPMRR_PF4_Y35NY_DPG",
        "unit": "$/gal", "icon": "RBB", "freq": "daily",
    },
    "Heating Oil No.2": {
        "route": "petroleum/pri/spt/data",
        "facet_key": "series", "facet_val": "EER_EPD2F_PF4_Y35NY_DPG",
        "unit": "$/gal", "icon": "HO2", "freq": "daily",
    },
    "Propane (Mont Belvieu)": {
        "route": "petroleum/pri/spt/data",
        "facet_key": "series", "facet_val": "EER_EPLLPA_PF4_Y44MB_DPG",
        "unit": "$/gal", "icon": "LPG", "freq": "daily",
    },
    "Natural Gas (Henry Hub)": {
        "route": "natural-gas/pri/sum/data",
        "facet_key": "series", "facet_val": "RNGWHHD",
        "unit": "$/MMBtu", "icon": "GAS", "freq": "daily",
    },
}

FUTURES = [
    {"name": "WTI Crude Oil",   "ticker": "CL=F", "unit": "$/bbl",   "icon": "WTI"},
    {"name": "Brent Crude Oil", "ticker": "BZ=F", "unit": "$/bbl",   "icon": "BRT"},
    {"name": "Natural Gas",     "ticker": "NG=F", "unit": "$/MMBtu", "icon": "GAS"},
    {"name": "RBOB Gasoline",   "ticker": "RB=F", "unit": "$/gal",   "icon": "RBB"},
    {"name": "Heating Oil",     "ticker": "HO=F", "unit": "$/gal",   "icon": "HO2"},
    {"name": "Gold",            "ticker": "GC=F", "unit": "$/oz",    "icon": "XAU"},
    {"name": "Silver",          "ticker": "SI=F", "unit": "$/oz",    "icon": "XAG"},
    {"name": "Copper",          "ticker": "HG=F", "unit": "$/lb",    "icon": "CU"},
    {"name": "Corn",            "ticker": "ZC=F", "unit": "¢/bu",    "icon": "ZCN"},
    {"name": "Soybeans",        "ticker": "ZS=F", "unit": "¢/bu",    "icon": "ZSN"},
    {"name": "Wheat",           "ticker": "ZW=F", "unit": "¢/bu",    "icon": "ZWN"},
]

def get_api_key(manual_key: str) -> str:
    if manual_key:
        return manual_key
    try:
        k = st.secrets["EIA_API_KEY"]
        if k: return k
    except Exception:
        pass
    try:
        k = st.secrets["eia"]["api_key"]
        if k: return k
    except Exception:
        pass
    return ""

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_price(api_key: str, commodity_key: str, days: int = 1825) -> pd.DataFrame:
    cfg = COMMODITIES[commodity_key]
    end_dt   = datetime.today()
    start_dt = end_dt - timedelta(days=days)
    params = {
        "api_key": api_key, "frequency": cfg["freq"], "data[0]": "value",
        f"facets[{cfg['facet_key']}][]": cfg["facet_val"],
        "start": start_dt.strftime("%Y-%m-%d"), "end": end_dt.strftime("%Y-%m-%d"),
        "sort[0][column]": "period", "sort[0][direction]": "asc",
        "length": 5000, "offset": 0,
    }
    try:
        r = requests.get(f"{BASE_URL}/{cfg['route']}", params=params, timeout=18)
        r.raise_for_status()
        records = r.json().get("response", {}).get("data", [])
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df["period"] = pd.to_datetime(df["period"])
        df["value"]  = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna(subset=["value"]).sort_values("period")[["period", "value"]]
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_production(api_key: str, months: int = 36) -> pd.DataFrame:
    end_dt   = datetime.today()
    start_dt = end_dt - timedelta(days=months * 31)
    params = {
        "api_key": api_key, "frequency": "monthly", "data[0]": "value",
        "facets[duoarea][]": "NUS", "facets[product][]": "EPC0",
        "start": start_dt.strftime("%Y-%m"), "end": end_dt.strftime("%Y-%m"),
        "sort[0][column]": "period", "sort[0][direction]": "asc", "length": 500,
    }
    try:
        r = requests.get(f"{BASE_URL}/petroleum/crd/crpdn/data", params=params, timeout=18)
        r.raise_for_status()
        records = r.json().get("response", {}).get("data", [])
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df["period"] = pd.to_datetime(df["period"])
        df["value"]  = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna(subset=["value"]).sort_values("period")[["period", "value"]]
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_gas_storage(api_key: str, weeks: int = 104) -> pd.DataFrame:
    end_dt   = datetime.today()
    start_dt = end_dt - timedelta(weeks=weeks + 4)
    params = {
        "api_key": api_key, "frequency": "weekly", "data[0]": "value",
        "facets[duoarea][]": "NUS", "facets[process][]": "SAB",
        "start": start_dt.strftime("%Y-%m-%d"), "end": end_dt.strftime("%Y-%m-%d"),
        "sort[0][column]": "period", "sort[0][direction]": "asc", "length": 500,
    }
    try:
        r = requests.get(f"{BASE_URL}/natural-gas/stor/wkly/data", params=params, timeout=18)
        r.raise_for_status()
        records = r.json().get("response", {}).get("data", [])
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df["period"] = pd.to_datetime(df["period"])
        df["value"]  = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna(subset=["value"]).sort_values("period")[["period", "value"]]
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_futures() -> list[dict]:
    results = []
    tickers = [f["ticker"] for f in FUTURES]

    def _empty(fut):
        return {**fut, "price": None, "prev": None, "chg": 0.0, "pct": 0.0, "expiry": "", "ok": False}

    def _get_close(data, ticker, all_tickers):
        if len(all_tickers) == 1:
            s = data["Close"]
        else:
            try:
                s = data["Close"][ticker]
            except KeyError:
                try:
                    s = data[ticker]["Close"]
                except KeyError:
                    s = data["Close"]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s.dropna()

    try:
        data = yf.download(tickers, period="5d", interval="1d",
                           group_by="ticker", auto_adjust=True,
                           progress=False, threads=True)
        intraday_prices = {}
        try:
            live = yf.download(tickers, period="1d", interval="1m",
                               group_by="ticker", auto_adjust=True,
                               progress=False, threads=True)
            for ticker in tickers:
                try:
                    s = _get_close(live, ticker, tickers)
                    if not s.empty:
                        intraday_prices[ticker] = float(s.iloc[-1])
                except Exception:
                    pass
        except Exception:
            pass

        for fut in FUTURES:
            ticker = fut["ticker"]
            try:
                cs = _get_close(data, ticker, tickers)
                if len(cs) < 1:
                    raise ValueError("sin datos")
                last_close = float(cs.iloc[-1])
                prev_close = float(cs.iloc[-2]) if len(cs) >= 2 else last_close
                price = intraday_prices.get(ticker, last_close)
                chg = price - prev_close
                pct = (chg / prev_close * 100) if prev_close else 0.0
                expiry = ""
                try:
                    info = yf.Ticker(ticker).fast_info
                    ts2  = getattr(info, "expiry_date", None)
                    if ts2:
                        expiry = ts2.strftime("%b %Y") if hasattr(ts2, "strftime") else ""
                except Exception:
                    pass
                results.append({**fut, "price": price, "prev": prev_close,
                                 "chg": chg, "pct": pct, "expiry": expiry, "ok": True})
            except Exception:
                results.append(_empty(fut))
    except Exception:
        results = [_empty(f) for f in FUTURES]

    for r in results:
        r.setdefault("ok", False)
    return results

@st.cache_data(ttl=120, show_spinner=False)
def fetch_future_intraday(ticker: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period="1d", interval="5m",
                         progress=False, auto_adjust=True)
        if df.empty:
            df = yf.download(ticker, period="5d", interval="15m",
                             progress=False, auto_adjust=True)
        close = df[["Close"]].copy()
        if isinstance(close.columns, pd.MultiIndex):
            close.columns = ["value"]
        else:
            close.columns = ["value"]
        close = close.dropna().reset_index()
        close.columns = ["period", "value"]
        close["value"] = close["value"].astype(float)
        return close
    except Exception:
        return pd.DataFrame()

def calc_variation(df: pd.DataFrame, days_back: int) -> tuple:
    if df.empty or len(df) < 2:
        return None, None
    latest_val = float(df["value"].iloc[-1])
    cutoff     = df["period"].iloc[-1] - timedelta(days=days_back)
    past       = df[df["period"] <= cutoff]
    if past.empty:
        return None, None
    ref_val = float(past["value"].iloc[-1])
    if ref_val == 0:
        return None, None
    chg = latest_val - ref_val
    pct = chg / ref_val * 100
    return chg, pct

def var_cell_html(label: str, chg, pct) -> str:
    if chg is None:
        return f"""
        <div class="var-cell">
          <div class="var-label">{label}</div>
          <div class="var-val neu">—</div>
        </div>"""
    sign  = "+" if chg >= 0 else ""
    cls   = "pos" if chg >= 0 else "neg"
    arrow = "▲" if chg >= 0 else "▼"
    return f"""
    <div class="var-cell">
      <div class="var-label">{label}</div>
      <div class="var-val {cls}">{arrow} {sign}{fmt(chg)} ({sign}{fmt(pct)}%)</div>
    </div>"""

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Inter', sans-serif", color=C_MUTED, size=11.5),
    margin=dict(l=10, r=10, t=8, b=8),
    xaxis=dict(
        gridcolor="#ececea", linecolor=C_BORDER2, tickcolor=C_BORDER2,
        zerolinecolor="#ececea",
        tickfont=dict(family="'Inter', sans-serif", size=10, color=C_MUTED),
    ),
    yaxis=dict(
        gridcolor="#ececea", linecolor=C_BORDER2, tickcolor=C_BORDER2,
        zerolinecolor="#ececea",
        tickfont=dict(family="'Inter', sans-serif", size=10, color=C_MUTED),
    ),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor=C_BG, bordercolor=C_BORDER2,
        font=dict(family="'Inter', sans-serif", size=11, color=C_TEXT),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER,
        font=dict(family="'Inter', sans-serif", size=10, color=C_MUTED),
    ),
)

def make_line(df: pd.DataFrame, name: str, unit: str, height: int = 280) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["value"], mode="lines",
        line=dict(color=C_LINE, width=2.0),
        fill="tozeroy", fillcolor=hex_rgba(C_LINE2, 0.07),
        name=name,
        hovertemplate=f"%{{x|%d/%m/%Y}}<br><b>%{{y:.2f}}</b> {unit}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=height)
    return fig

def make_intraday(df: pd.DataFrame, name: str, unit: str, height: int = 260) -> go.Figure:
    if df.empty:
        return go.Figure().update_layout(**BASE_LAYOUT, height=height)
    open_price = float(df["value"].iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["value"], mode="lines",
        line=dict(color=C_LINE, width=2.0),
        fill="tozeroy", fillcolor=hex_rgba(C_LINE2, 0.07),
        name=name,
        hovertemplate=f"%{{x|%H:%M}}<br><b>%{{y:.3f}}</b> {unit}<extra></extra>",
    ))
    fig.add_hline(y=open_price,
                  line=dict(color="rgba(0,0,0,0.15)", width=1, dash="dot"),
                  annotation_text="apertura",
                  annotation_font_color=C_MUTED,
                  annotation_font_size=9)
    fig.update_layout(**BASE_LAYOUT, height=height)
    return fig

def make_bar(df: pd.DataFrame, name: str, unit: str, height: int = 270) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["period"], y=df["value"],
        marker_color=C_LINE, marker_line_width=0, opacity=0.75,
        name=name,
        hovertemplate=f"%{{x|%b %Y}}<br><b>%{{y:,.0f}}</b> {unit}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=height)
    return fig

def make_area(df: pd.DataFrame, name: str, unit: str, height: int = 270) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["value"], mode="lines", fill="tozeroy",
        line=dict(color=C_LINE, width=2.0),
        fillcolor=hex_rgba(C_LINE2, 0.07),
        name=name,
        hovertemplate=f"%{{x|%d/%m/%Y}}<br><b>%{{y:,.0f}}</b> {unit}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=height)
    return fig

def make_indexed(dfs_dict: dict, height: int = 360) -> go.Figure:
    grays = ["#1a56a0", "#c0392b", "#2e8b57", "#d4850a", "#7b52ab", "#1a7a8a"]
    fig   = go.Figure()
    for i, (name, (df, _)) in enumerate(dfs_dict.items()):
        if df.empty or df["value"].iloc[0] == 0:
            continue
        normed = df["value"] / df["value"].iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=df["period"], y=normed, mode="lines", name=name,
            line=dict(color=grays[i % len(grays)], width=2.0),
            hovertemplate=f"<b>{name}</b> · %{{x|%d/%m/%Y}}: %{{y:.1f}}<extra></extra>",
        ))
    layout = {**BASE_LAYOUT}
    layout["yaxis"] = {**layout["yaxis"], "title": "Índice (inicio = 100)"}
    layout["legend"] = {**layout["legend"], "orientation": "h", "y": -0.22}
    fig.update_layout(**layout, height=height)
    return fig

def kpi_html_eia(key: str, df: pd.DataFrame) -> str:
    cfg = COMMODITIES[key]
    if df.empty or len(df) < 2:
        return ""

    latest = float(df["value"].iloc[-1])
    prev   = float(df["value"].iloc[-2])
    chg    = latest - prev
    pct    = (chg / prev * 100) if prev else 0
    sign   = "+" if chg >= 0 else ""
    cls    = "pos" if chg >= 0 else "neg"
    arrow  = "▲" if chg >= 0 else "▼"

    dt = pd.to_datetime(df["period"].iloc[-1])
    meses_es = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    date = f"{dt.day} de {meses_es[dt.month]} de {dt.year}"

    return f"""
    <div class="kpi-card">
      <div class="label">{cfg['icon']} · {key}</div>
      <div class="price">{fmt(latest)}</div>
      <div class="unit">{cfg['unit']}</div>
      <div class="chg {cls}">{arrow} {sign}{fmt(chg)} &nbsp; ({sign}{fmt(pct)}%)</div>
      <div class="date">{date}</div>
    </div>"""

def futures_table_html(futures_data: list[dict]) -> str:
    rows = ""
    for f in futures_data:
        if not f.get("ok") or f["price"] is None:
            price_td = '<span style="color:#aaa">N/D</span>'
            chg_td   = '<span class="neu">—</span>'
        else:
            price_td = f'<span class="fut-price">{fmt(f["price"], 1)}</span>'
            sign  = "+" if f["chg"] >= 0 else ""
            cls   = "pos" if f["chg"] >= 0 else "neg"
            arrow = "▲" if f["chg"] >= 0 else "▼"
            chg_td = (
                f'<span class="{cls}">{arrow} {sign}{fmt(f["chg"], 1)}'
                f' &nbsp;({sign}{fmt(f["pct"])}%)</span>'
            )
        rows += f"""
        <tr>
          <td>
            <span class="fut-name">{f["name"]}</span>
            <span class="fut-ticker">{f["ticker"]} · {f["unit"]}</span>
          </td>
          <td>{price_td}</td>
          <td>{chg_td}</td>
        </tr>"""
    return f"""
    <table class="fut-table">
      <thead><tr>
        <th>Contrato</th>
        <th>Último precio</th>
        <th>Variación diaria</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


# ═══════════════════════════════════════════════════════
#  ARGENTINA COMBUSTIBLES — DATA
# ═══════════════════════════════════════════════════════
AR_URL = "http://datos.energia.gob.ar/dataset/1c181390-5045-475e-94dc-410429be4b17/resource/80ac25de-a44a-4445-9215-090cf55cfda5/download/precios-en-surtidor-resolucin-3142016.csv"

def clean_cols(df):
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip().str.lower()
        .str.replace("á", "a", regex=False).str.replace("é", "e", regex=False)
        .str.replace("í", "i", regex=False).str.replace("ó", "o", regex=False)
        .str.replace("ú", "u", regex=False).str.replace("ñ", "n", regex=False)
        .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_")
    )
    return df

def find_col(df, candidates):
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None

def normalize_text_series(s):
    return s.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

def load_raw_csv(url):
    for kwargs in [
        {},
        {"sep": ";"},
        {"sep": ";", "encoding": "latin1"},
        {"sep": None, "engine": "python"},
    ]:
        try:
            df = pd.read_csv(url, low_memory=False, **kwargs)
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(url, sep=None, engine="python", low_memory=False)

def parse_precio(series):
    s = series.astype(str).str.strip()
    mask_coma = s.str.contains(",", na=False)
    s.loc[mask_coma] = (
        s.loc[mask_coma]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(s, errors="coerce")

def compute_variation_vs_days(s, days):
    if s.empty or len(s) < 2:
        return np.nan
    s = s.sort_values("fecha").copy()
    last_date  = s["fecha"].max()
    last_value = s.loc[s["fecha"] == last_date, "precio_promedio"].iloc[-1]
    prev = s[s["fecha"] <= (last_date - pd.Timedelta(days=days))].sort_values("fecha")
    if prev.empty:
        return np.nan
    prev_value = prev["precio_promedio"].iloc[-1]
    if pd.isna(prev_value) or prev_value == 0:
        return np.nan
    return (last_value / prev_value - 1) * 100

def build_excel_download(df_export: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="serie_diaria")
    output.seek(0)
    return output.getvalue()

def ar_kpi_card(title, value):
    return f"""
    <div class="ar-kpi-card">
        <div class="ar-kpi-title">{title}</div>
        <div class="ar-kpi-value">{value}</div>
    </div>
    """

@st.cache_data(ttl=60 * 60 * 12, show_spinner=True)
def load_ar_data():
    df = load_raw_csv(AR_URL)
    df = clean_cols(df)
    original_cols = df.columns.tolist()

    fecha_col    = find_col(df, ["fecha", "fechavigencia", "fecha_vigencia", "fecha_actualizacion",
                                  "fechaactualizacion", "vigencia", "datetime", "timestamp"])
    provincia_col = find_col(df, ["provincia", "provincia_nombre", "nombre_provincia", "desc_provincia"])
    producto_col  = find_col(df, ["producto", "producto_nombre", "nombre_producto", "desc_producto",
                                   "tipo_combustible", "tipocombustible"])
    precio_col    = find_col(df, ["precio", "precio_vigente", "precio_venta", "precioventa", "valor"])
    bandera_col   = find_col(df, ["empresabandera", "empresa_bandera", "bandera", "bandera_nombre",
                                   "nombre_bandera", "desc_bandera", "marca"])

    missing = []
    if fecha_col is None:    missing.append("fecha")
    if provincia_col is None: missing.append("provincia")
    if producto_col is None:  missing.append("producto")
    if precio_col is None:    missing.append("precio")
    if missing:
        raise ValueError("No se pudieron detectar columnas clave: " + ", ".join(missing)
                         + f". Columnas encontradas: {original_cols}")

    rename_map = {fecha_col: "fecha", provincia_col: "provincia",
                  producto_col: "producto", precio_col: "precio"}
    if bandera_col is not None:
        rename_map[bandera_col] = "bandera"

    df = df.rename(columns=rename_map)
    df["fecha"]    = pd.to_datetime(df["fecha"], errors="coerce").dt.floor("D")
    df["provincia"] = normalize_text_series(df["provincia"])
    df["producto"]  = normalize_text_series(df["producto"])
    df["bandera"]   = normalize_text_series(df["bandera"]) if "bandera" in df.columns else "Todas"
    df["precio"]    = parse_precio(df["precio"])
    df = df.dropna(subset=["fecha", "provincia", "producto", "precio"]).copy()
    df = df[df["precio"] > 0].copy()

    agg_cols = dict(precio_promedio=("precio","mean"), cantidad_registros=("precio","size"),
                    precio_min=("precio","min"), precio_max=("precio","max"))

    serie_bandera = df.groupby(["fecha","provincia","producto","bandera"], as_index=False).agg(**agg_cols)
    serie_todas   = df.groupby(["fecha","provincia","producto"], as_index=False).agg(**agg_cols)
    serie_todas["bandera"] = "Todas"
    serie_nac_b   = df.groupby(["fecha","producto","bandera"], as_index=False).agg(**agg_cols)
    serie_nac_b["provincia"] = "Total país"
    serie_nac_t   = df.groupby(["fecha","producto"], as_index=False).agg(**agg_cols)
    serie_nac_t["provincia"] = "Total país"
    serie_nac_t["bandera"]   = "Todas"

    serie_full = (
        pd.concat([serie_bandera, serie_todas, serie_nac_b, serie_nac_t], ignore_index=True)
        .drop_duplicates()
        .sort_values(["provincia","producto","bandera","fecha"])
    )

    provincias = sorted(serie_full["provincia"].dropna().unique().tolist())
    productos  = sorted(serie_full["producto"].dropna().unique().tolist())
    banderas   = sorted(serie_full["bandera"].dropna().unique().tolist())

    metadata = dict(columnas_originales=original_cols, fecha_col=fecha_col,
                    provincia_col=provincia_col, producto_col=producto_col,
                    precio_col=precio_col, bandera_col=bandera_col)

    return df, serie_full, provincias, productos, banderas, metadata

# ═══════════════════════════════════════════════════════
#  FX HELPERS — CCL YPF + OFICIAL BCRA
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_ccl_ypf(start_date=None) -> pd.DataFrame:
    try:
        start = pd.to_datetime(start_date).strftime("%Y-%m-%d") if start_date is not None else None

        ypfd_ba = yf.download("YPFD.BA", start=start, progress=False, auto_adjust=True)
        ypf_us  = yf.download("YPF",     start=start, progress=False, auto_adjust=True)

        if ypfd_ba.empty or ypf_us.empty:
            return pd.DataFrame()

        df_ba = ypfd_ba[["Close"]].copy().reset_index()
        df_us = ypf_us[["Close"]].copy().reset_index()

        df_ba.columns = ["fecha", "ypfd_ba"]
        df_us.columns = ["fecha", "ypf_us"]

        df_ba["fecha"] = pd.to_datetime(df_ba["fecha"]).dt.floor("D")
        df_us["fecha"] = pd.to_datetime(df_us["fecha"]).dt.floor("D")

        df = pd.merge(df_ba, df_us, on="fecha", how="inner")
        df["ccl_ypf"] = df["ypfd_ba"] / df["ypf_us"]
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["ccl_ypf"])

        return df[["fecha", "ccl_ypf"]].sort_values("fecha")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60 * 60)
def get_monetaria_serie(id_variable: int) -> pd.DataFrame:
    """
    Descarga series del endpoint Monetarias/{id_variable}.
    Devuelve columnas: Date, value
    """
    url = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/{id_variable}"
    params = {"Limit": 1000, "Offset": 0}
    data = []
    last_err = None

    for _ in range(3):
        try:
            params["Offset"] = 0
            data = []

            while True:
                r = requests.get(url, params=params, timeout=20, verify=False)
                r.raise_for_status()
                payload = r.json()

                results = payload.get("results", [])
                if not results:
                    break

                detalle = results[0].get("detalle", [])
                if not detalle:
                    break

                data.extend(detalle)

                meta = payload.get("metadata", {}).get("resultset", {}) or {}
                count = meta.get("count")

                params["Offset"] += params["Limit"]

                if count is not None:
                    if params["Offset"] >= count:
                        break
                else:
                    if len(detalle) < params["Limit"]:
                        break

            break
        except requests.exceptions.RequestException as e:
            last_err = str(e)

    if not data:
        if last_err:
            st.error(f"Error BCRA Monetarias/{id_variable}: {last_err}")
        return pd.DataFrame(columns=["Date", "value"])

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df.get("fecha"), errors="coerce")
    df["value"] = pd.to_numeric(df.get("valor"), errors="coerce")

    return (
        df[["Date", "value"]]
        .dropna()
        .drop_duplicates(subset=["Date"])
        .sort_values("Date")
        .reset_index(drop=True)
    )


@st.cache_data(ttl=60 * 60)
def get_a3500() -> pd.DataFrame:
    """
    A3500 con fallback.
    Devuelve columnas: Date, FX
    """
    df = get_monetaria_serie(5)

    if df.empty:
        df = get_monetaria_serie(84)

    if df.empty:
        return pd.DataFrame(columns=["Date", "FX"])

    out = df.rename(columns={"value": "FX"}).copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out["FX"] = pd.to_numeric(out["FX"], errors="coerce")

    return (
        out[["Date", "FX"]]
        .dropna()
        .drop_duplicates(subset=["Date"])
        .sort_values("Date")
        .reset_index(drop=True)
    )
@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_dolar_oficial_bcra(start_date=None) -> pd.DataFrame:
    df = get_a3500().copy()

    if df.empty:
        return pd.DataFrame(columns=["fecha", "oficial"])

    df = df.rename(columns={"Date": "fecha", "FX": "oficial"})
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.floor("D")
    df["oficial"] = pd.to_numeric(df["oficial"], errors="coerce")

    if start_date is not None:
        df = df[df["fecha"] >= pd.to_datetime(start_date)]

    return (
        df[["fecha", "oficial"]]
        .dropna()
        .drop_duplicates(subset=["fecha"])
        .sort_values("fecha")
        .reset_index(drop=True)
    )


def build_combustible_fx_df(df_plot: pd.DataFrame) -> pd.DataFrame:
    if df_plot.empty:
        return pd.DataFrame()

    def _prep_df(df: pd.DataFrame, fecha_col: str = "fecha") -> pd.DataFrame:
        df = df.copy()
        df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce", utc=True)
        df[fecha_col] = df[fecha_col].dt.tz_convert(None).dt.normalize()
        df = df.dropna(subset=[fecha_col]).sort_values(fecha_col).copy()
        df = df.drop_duplicates(subset=[fecha_col], keep="last").copy()

        # clave numérica para merge_asof
        df["_merge_key"] = df[fecha_col].astype("int64")
        return df

    out = df_plot[["fecha", "precio_promedio"]].copy()
    out = _prep_df(out, "fecha")

    if out.empty:
        return pd.DataFrame(columns=[
            "fecha", "precio_promedio", "ccl_ypf", "oficial", "usd_ccl", "usd_oficial"
        ])

    start_date = out["fecha"].min() - pd.Timedelta(days=15)

    ccl_df = fetch_ccl_ypf(start_date=start_date)
    ofi_df = fetch_dolar_oficial_bcra(start_date=start_date)

    if not ccl_df.empty:
        ccl_df = _prep_df(ccl_df, "fecha")
        if not ccl_df.empty:
            out = pd.merge_asof(
                out.sort_values("_merge_key"),
                ccl_df.sort_values("_merge_key")[["_merge_key", "ccl_ypf"]],
                on="_merge_key",
                direction="backward"
            )
        else:
            out["ccl_ypf"] = np.nan
    else:
        out["ccl_ypf"] = np.nan

    if not ofi_df.empty:
        ofi_df = _prep_df(ofi_df, "fecha")
        if not ofi_df.empty:
            out = pd.merge_asof(
                out.sort_values("_merge_key"),
                ofi_df.sort_values("_merge_key")[["_merge_key", "oficial"]],
                on="_merge_key",
                direction="backward"
            )
        else:
            out["oficial"] = np.nan
    else:
        out["oficial"] = np.nan

    out["usd_ccl"] = out["precio_promedio"] / out["ccl_ypf"]
    out["usd_oficial"] = out["precio_promedio"] / out["oficial"]

    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.drop(columns=["_merge_key"], errors="ignore")

    return out

def apply_range_filter(df: pd.DataFrame, fecha_col: str, rango: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    fecha_max = df[fecha_col].max()

    if rango == "1M":
        return df[df[fecha_col] >= fecha_max - pd.DateOffset(months=1)].copy()
    elif rango == "3M":
        return df[df[fecha_col] >= fecha_max - pd.DateOffset(months=3)].copy()
    elif rango == "6M":
        return df[df[fecha_col] >= fecha_max - pd.DateOffset(months=6)].copy()
    elif rango == "1A":
        return df[df[fecha_col] >= fecha_max - pd.DateOffset(years=1)].copy()
    return df.copy()


def apply_date_slider_filter(df: pd.DataFrame, fecha_col: str, slider_range) -> pd.DataFrame:
    if df.empty or slider_range is None:
        return df.copy()

    f_ini, f_fin = slider_range
    f_ini = pd.to_datetime(f_ini)
    f_fin = pd.to_datetime(f_fin)

    return df[(df[fecha_col] >= f_ini) & (df[fecha_col] <= f_fin)].copy()
# ═══════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("#### ⚡ Dashboard Energético")
    st.markdown("---")

    # EIA API Key
    has_secret = False
    try:
        _ = st.secrets["EIA_API_KEY"]
        has_secret = bool(_)
    except Exception:
        try:
            _ = st.secrets["eia"]["api_key"]
            has_secret = bool(_)
        except Exception:
            pass

    if has_secret:
        st.success("API Key EIA detectada")
        manual_key = ""
    else:
        st.caption("Ingresá tu API key de EIA para datos spot")
        manual_key = st.text_input(
            "API Key EIA",
            type="password",
            placeholder="Ingresá tu clave aquí",
            help="Gratis en https://www.eia.gov/opendata/",
        )
        st.caption("[Obtener API Key gratis →](https://www.eia.gov/opendata/)")

    st.markdown("---")
    st.markdown("**Mercados internacionales (EIA)**")
    selected_commodities = st.multiselect(
        "Commodities EIA",
        list(COMMODITIES.keys()),
        default=list(COMMODITIES.keys()),
    )
    st.markdown("---")
    show_futures = st.checkbox("Futuros en tiempo real", value=True)
    show_intra   = st.checkbox("Gráfico intraday", value=True)
    show_prod    = st.checkbox("Producción crudo US", value=True)
    show_stor    = st.checkbox("Almacenamiento gas natural", value=True)
    show_idx     = st.checkbox("Comparación indexada", value=True)
    st.markdown("---")
    auto_refresh = st.checkbox("Auto-refresh cada 2 min", value=False)
    if auto_refresh:
        st.caption("● Refresh activo")
    if st.button("Refrescar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if auto_refresh:
    import streamlit.components.v1 as components
    components.html("<meta http-equiv='refresh' content='120'>", height=0)


# ═══════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <h1>⚡ Dashboard Energético</h1>
  <div class="sub">EIA Open Data API v2 &nbsp;·&nbsp; Yahoo Finance &nbsp;·&nbsp; datos.energia.gob.ar</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════
tab_eia, tab_ar = st.tabs(["◈ Mercados Internacionales (EIA)", "⛽ Combustibles Argentina"])


# ... (Mantener imports, configuración de página, CSS y helpers iguales)

# ───────────────────────────────────────────────────────
#  TAB 1: EIA
# ───────────────────────────────────────────────────────
with tab_eia:
    api_key = get_api_key(manual_key)

    if not api_key:
        st.markdown("""
        <div class="info-box">
        API key de EIA no encontrada.<br><br>
        <b>Registro gratuito:</b> <a href="https://www.eia.gov/opendata/" target="_blank">eia.gov/opendata</a>
        </div>
        """, unsafe_allow_html=True)

    # 1. SECCIÓN FUTUROS (Yahoo Finance)
    if show_futures:
        st.markdown('<div class="sec-label">Futuros front-month · tiempo real <span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
        with st.spinner("Cargando futuros…"):
            futures_data = fetch_futures()

        col_tbl, col_chart = st.columns([1.1, 1], gap="large")

        with col_tbl:
            st.markdown(futures_table_html(futures_data), unsafe_allow_html=True)
            st.markdown(
    f"""
    <div style="color:#475569; font-size:0.78rem; margin-top:6px;">
        Actualizado: {datetime.now().strftime('%H:%M:%S')} · Fuente: Yahoo Finance
    </div>
    """,
    unsafe_allow_html=True
)

        with col_chart:
            if show_intra:
                fut_options = [f["name"] for f in futures_data]
                selected_fut = st.selectbox("Contrato", fut_options, index=0, key="fut_sel_box")
                fut_cfg = next((f for f in futures_data if f["name"] == selected_fut), futures_data[0])
                
                view_yf = st.radio("Vista", ["Intraday", "Histórico"], horizontal=True, key="view_yf_toggle")

                if view_yf == "Intraday":
                    intra_df = fetch_future_intraday(fut_cfg["ticker"])
                    if not intra_df.empty:
                        st.plotly_chart(make_intraday(intra_df, fut_cfg["name"], fut_cfg["unit"]), use_container_width=True, config={"displayModeBar": False})
                else:
                    # Lógica de histórico YF (omito detalle por brevedad, pero se mantiene igual)
                    pass

    # 2. SECCIÓN EIA (Datos Spot y Producción)
    if api_key:
        active = selected_commodities or list(COMMODITIES.keys())

        # Indicadores de carga
        total_steps = len(active)
        if show_prod:
            total_steps += 1
        if show_stor:
            total_steps += 1

        progress_text = st.empty()
        progress_bar = st.progress(0)

        current_step = 0
        price_data = {}

        # Carga precios spot
        for key in active:
            progress_text.markdown(
                f"<div style='color:#475569; font-size:0.82rem; margin-bottom:6px;'>"
                f"Cargando datos EIA: <b>{key}</b> ({current_step + 1}/{total_steps})"
                f"</div>",
                unsafe_allow_html=True
            )
            price_data[key] = fetch_price(api_key, key)
            current_step += 1
            progress_bar.progress(current_step / total_steps)

        # Carga producción
        if show_prod:
            progress_text.markdown(
                f"<div style='color:#475569; font-size:0.82rem; margin-bottom:6px;'>"
                f"Cargando producción de crudo de EE.UU. ({current_step + 1}/{total_steps})"
                f"</div>",
                unsafe_allow_html=True
            )
            prod_df = fetch_production(api_key)
            current_step += 1
            progress_bar.progress(current_step / total_steps)
        else:
            prod_df = pd.DataFrame()

        # Carga almacenamiento
        if show_stor:
            progress_text.markdown(
                f"<div style='color:#475569; font-size:0.82rem; margin-bottom:6px;'>"
                f"Cargando almacenamiento de gas natural ({current_step + 1}/{total_steps})"
                f"</div>",
                unsafe_allow_html=True
            )
            stor_df = fetch_gas_storage(api_key)
            current_step += 1
            progress_bar.progress(current_step / total_steps)
        else:
            stor_df = pd.DataFrame()

        # Mensaje final breve
        progress_text.markdown(
            "<div style='color:#0f766e; font-size:0.82rem; margin-bottom:6px;'>"
            "Carga completada."
            "</div>",
            unsafe_allow_html=True
        )
        progress_bar.progress(1.0)

        # Opcional: limpiar luego de un instante visual
        progress_text.empty()
        progress_bar.empty()

        valid_keys = [k for k in active if not price_data[k].empty]
        
        if valid_keys:
            # RESTAURADO: KPIs de Precios Spot
            st.markdown('<div class="sec-label">Precios spot EIA · último dato disponible</div>', unsafe_allow_html=True)
            cards_html = "".join(kpi_html_eia(k, price_data[k]) for k in active)
            st.markdown(f'<div class="kpi-grid">{cards_html}</div>', unsafe_allow_html=True)

            # RESTAURADO: Gráficos con títulos visibles
            st.markdown('<div class="sec-label">Histórico de precios spot (EIA)</div>', unsafe_allow_html=True)
            for i in range(0, len(valid_keys), 2):
                row_keys = valid_keys[i:i+2]
                cols = st.columns(2)
                for j, key in enumerate(row_keys):
                    cfg = COMMODITIES[key]
                    with cols[j]:
                        # Títulos restaurados
                        st.markdown(f"**{cfg['icon']} {key}**") 
                        st.plotly_chart(make_line(price_data[key], key, cfg["unit"], height=260), use_container_width=True, config={"displayModeBar": False})

            # RESTAURADO: Gráfico Indexado
            if show_idx and len(valid_keys) >= 2:
                st.markdown('<div class="sec-label">Comparación indexada · base 100 = inicio del período</div>', unsafe_allow_html=True)
                dfs_map = {k: (price_data[k], None) for k in valid_keys}
                st.plotly_chart(make_indexed(dfs_map), use_container_width=True, config={"displayModeBar": False})

            # RESTAURADO: Complementarios (Producción/Storage)
            supp_elements = []
            if show_prod and not prod_df.empty: supp_elements.append(("prod", "Producción US de Crudo", "Mbbl/d", make_bar, prod_df))
            if show_stor and not stor_df.empty: supp_elements.append(("stor", "Almacenamiento Gas Natural US", "Bcf", make_area, stor_df))
            
            if supp_elements:
                st.markdown('<div class="sec-label">Datos de mercado complementarios</div>', unsafe_allow_html=True)
                grid_supp = st.columns(len(supp_elements))
                for idx, (id_tag, title, unit, func, df_source) in enumerate(supp_elements):
                    with grid_supp[idx]:
                        st.markdown(f"**{title}** &nbsp; <small>{unit}</small>", unsafe_allow_html=True)
                        st.plotly_chart(func(df_source, title, unit), use_container_width=True, config={"displayModeBar": False})





# ───────────────────────────────────────────────────────
#  TAB 2: COMBUSTIBLES ARGENTINA
# ───────────────────────────────────────────────────────
with tab_ar:
    try:
        raw_df, serie_full, provincias, productos, banderas, metadata = load_ar_data()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    st.markdown(
        "<div style='color:#475569; font-size:0.82rem; margin-bottom:10px;'>"
        "Seleccioná provincia, combustible y bandera desde los desplegables."
        "</div>",
        unsafe_allow_html=True
    )

    sel1, sel2, sel3 = st.columns(3)

    with sel1:
        idx_prov = provincias.index("Total país") if "Total país" in provincias else 0
        provincia_sel = st.selectbox("Provincia", provincias, index=idx_prov, key="provincia_sel_ar")

    with sel2:
        productos_disp = sorted(
            serie_full.loc[serie_full["provincia"] == provincia_sel, "producto"]
            .dropna().unique().tolist()
        )
        producto_sel = st.selectbox("Combustible", productos_disp, index=0, key="producto_sel_ar")

    with sel3:
        banderas_disp = sorted(
            serie_full.loc[
                (serie_full["provincia"] == provincia_sel) &
                (serie_full["producto"] == producto_sel),
                "bandera"
            ].dropna().unique().tolist()
        )
        idx_band = banderas_disp.index("Todas") if "Todas" in banderas_disp else 0
        bandera_sel = st.selectbox("Bandera", banderas_disp, index=idx_band, key="bandera_sel_ar")
        st.markdown(
            "<div style='color:#64748b; font-size:0.78rem; margin-top:4px;'>Hacé click en cada campo para desplegar opciones.</div>",
            unsafe_allow_html=True
        )

    df_plot = (
        serie_full[
            (serie_full["provincia"] == provincia_sel) &
            (serie_full["producto"] == producto_sel) &
            (serie_full["bandera"] == bandera_sel)
        ]
        .sort_values("fecha")
        .copy()
    )

    if df_plot.empty:
        st.warning("No hay datos para la combinación seleccionada.")
        st.stop()

    ultimo = df_plot.iloc[-1]
    fecha_ultimo = df_plot["fecha"].max()
    var_7d = compute_variation_vs_days(df_plot, 7)
    var_30d = compute_variation_vs_days(df_plot, 30)

    st.markdown(
        f"""
        <div class="section-title-ar">
            <div class="eyebrow">Precios en surtidor</div>
            <h3>{producto_sel} · {provincia_sel} · {bandera_sel}</h3>
            <div class="meta">Último dato disponible: {fecha_ultimo.strftime('%d/%m/%Y')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(ar_kpi_card("Último precio promedio", fmt_ars(ultimo["precio_promedio"], 2)), unsafe_allow_html=True)
    with k2:
        st.markdown(ar_kpi_card("Variación 7 días", fmt_pct_ar(var_7d, 1)), unsafe_allow_html=True)
    with k3:
        st.markdown(ar_kpi_card("Variación 30 días", fmt_pct_ar(var_30d, 1)), unsafe_allow_html=True)
    with k4:
        st.markdown(
            ar_kpi_card("Registros del último dato", f"{int(ultimo['cantidad_registros']):,}".replace(",", ".")),
            unsafe_allow_html=True
        )

    # ====================================================
    #  GRÁFICO 1 — ARS
    # ====================================================
    st.markdown('<div class="panel"><div class="panel-title">Serie histórica</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 1])
    with c1:
        rango_ars = st.radio(
            "Rango gráfico ARS",
            ["1M", "3M", "6M", "1A", "Todo"],
            horizontal=True,
            index=3,
            key="rango_combustibles_ars"
        )
    with c2:
        mostrar_ma7_ars = st.checkbox(
            "Mostrar media móvil 7d (ARS)",
            value=True,
            key="ma7_combustibles_ars"
        )

    df_chart_ars = apply_range_filter(df_plot, "fecha", rango_ars)

    fechas_ars = sorted(df_chart_ars["fecha"].dropna().unique().tolist())
    if len(fechas_ars) >= 2:
        slider_ars = st.select_slider(
            "Ventana temporal gráfico ARS",
            options=fechas_ars,
            value=(fechas_ars[0], fechas_ars[-1]),
            format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y"),
            key="slider_fechas_ars"
        )
        df_chart_ars = apply_date_slider_filter(df_chart_ars, "fecha", slider_ars)

    if mostrar_ma7_ars:
        df_chart_ars["media_movil_7d"] = df_chart_ars["precio_promedio"].rolling(7, min_periods=1).mean()

    fig_ar = go.Figure()
    fig_ar.add_trace(go.Scatter(
        x=df_chart_ars["fecha"],
        y=df_chart_ars["precio_promedio"],
        mode="lines",
        name="Precio promedio",
        line=dict(color="#2563eb", width=2.4),
        hovertemplate="%{x|%d/%m/%Y}<br><b>$ %{y:,.2f}</b><extra></extra>",
    ))

    if mostrar_ma7_ars and "media_movil_7d" in df_chart_ars.columns:
        fig_ar.add_trace(go.Scatter(
            x=df_chart_ars["fecha"],
            y=df_chart_ars["media_movil_7d"],
            mode="lines",
            name="Media móvil 7d",
            line=dict(color="#94a3b8", width=2, dash="dot"),
            hovertemplate="%{x|%d/%m/%Y}<br><b>$ %{y:,.2f}</b><extra></extra>",
        ))

    fig_ar.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=500,
        margin=dict(l=12, r=12, t=18, b=10),
        hovermode="x unified",
        font=dict(family="Inter, sans-serif", color="#475569"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            showgrid=False,
            linecolor="#cbd5e1",
            tickfont=dict(color="#64748b")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#e2e8f0",
            zeroline=False,
            linecolor="#cbd5e1",
            tickprefix="$ ",
            tickfont=dict(color="#64748b")
        ),
    )

    st.plotly_chart(
        fig_ar,
        use_container_width=True,
        config={"displayModeBar": False},
        key="chart_combustibles_main"
    )

    note_ars = (
        f"Primer dato total: {df_plot['fecha'].min().strftime('%d/%m/%Y')} "
        f"· Último dato total: {df_plot['fecha'].max().strftime('%d/%m/%Y')} "
        f"· Observaciones diarias: {len(df_plot):,}"
    ).replace(",", ".")
    st.markdown(f'<div class="chart-note">{note_ars}</div></div>', unsafe_allow_html=True)

    # ====================================================
    #  GRÁFICO 2 — RELATIVO AL TIPO DE CAMBIO
    # ====================================================
    df_fx_base = build_combustible_fx_df(df_plot)

    st.markdown(
        '<div class="panel"><div class="panel-title">Precio del combustible relativo al tipo de cambio</div>',
        unsafe_allow_html=True
    )

    fx1, fx2, fx3 = st.columns([1.1, 1.2, 1])
    with fx1:
        fx_mode = st.selectbox(
            "Tipo de cambio",
            ["USD al CCL", "USD al oficial"],
            index=0,
            key="fx_mode_combustibles"
        )
    with fx2:
        rango_fx = st.radio(
            "Rango gráfico USD",
            ["1M", "3M", "6M", "1A", "Todo"],
            horizontal=True,
            index=3,
            key="rango_combustibles_fx"
        )
    with fx3:
        mostrar_ma7_fx = st.checkbox(
            "Mostrar media móvil 7d (USD)",
            value=True,
            key="ma7_combustibles_fx"
        )

    df_fx = apply_range_filter(df_fx_base, "fecha", rango_fx)

    fechas_fx = sorted(df_fx["fecha"].dropna().unique().tolist())
    if len(fechas_fx) >= 2:
        slider_fx = st.select_slider(
            "Ventana temporal gráfico USD",
            options=fechas_fx,
            value=(fechas_fx[0], fechas_fx[-1]),
            format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y"),
            key="slider_fechas_fx"
        )
        df_fx = apply_date_slider_filter(df_fx, "fecha", slider_fx)

    serie_map = {
        "USD al CCL": ("usd_ccl", "Precio en USD al CCL implícito (YPFD.BA / YPF)"),
        "USD al oficial": ("usd_oficial", "Precio en USD al tipo de cambio oficial"),
    }
    serie_col, serie_title = serie_map[fx_mode]

    if not df_fx.empty and serie_col in df_fx.columns and df_fx[serie_col].notna().any():
        if mostrar_ma7_fx:
            df_fx["ma7_fx"] = df_fx[serie_col].rolling(7, min_periods=1).mean()

        fig_fx = go.Figure()

        fig_fx.add_trace(go.Scatter(
            x=df_fx["fecha"],
            y=df_fx[serie_col],
            mode="lines",
            name=serie_title,
            line=dict(color="#111827", width=2.2),
            hovertemplate="%{x|%d/%m/%Y}<br><b>USD %{y:,.3f}</b><extra></extra>",
        ))

        if mostrar_ma7_fx and "ma7_fx" in df_fx.columns:
            fig_fx.add_trace(go.Scatter(
                x=df_fx["fecha"],
                y=df_fx["ma7_fx"],
                mode="lines",
                name="Media móvil 7d",
                line=dict(color="#94a3b8", width=2, dash="dot"),
                hovertemplate="%{x|%d/%m/%Y}<br><b>USD %{y:,.3f}</b><extra></extra>",
            ))

        fig_fx.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            height=500,
            margin=dict(l=12, r=12, t=18, b=10),
            hovermode="x unified",
            font=dict(family="Inter, sans-serif", color="#475569"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0)"
            ),
            xaxis=dict(
                showgrid=False,
                linecolor="#cbd5e1",
                tickfont=dict(color="#64748b")
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#e2e8f0",
                zeroline=False,
                linecolor="#cbd5e1",
                tickprefix="USD ",
                tickfont=dict(color="#64748b"),
                ticks="outside"
            ),
        )

        st.plotly_chart(
            fig_fx,
            use_container_width=True,
            config={"displayModeBar": False},
            key="chart_combustibles_fx"
        )

        note_fx = {
            "USD al CCL": "Conversión aproximada usando CCL implícito calculado como YPFD.BA / YPF (Yahoo Finance).",
            "USD al oficial": "Conversión usando tipo de cambio mayorista oficial BCRA (A3500).",
        }
        st.markdown(f'<div class="chart-note">{note_fx[fx_mode]}</div></div>', unsafe_allow_html=True)
    else:
        st.info("No se pudo construir la serie en USD para el tipo de cambio seleccionado.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ====================================================
    #  DESCARGA
    # ====================================================
    st.markdown('<div class="panel"><div class="panel-title">Descarga de serie diaria</div>', unsafe_allow_html=True)

    excel_df = df_plot.sort_values("fecha", ascending=False).copy()
    excel_df["fecha"] = excel_df["fecha"].dt.strftime("%d/%m/%Y")
    excel_bytes = build_excel_download(excel_df[[
        "fecha", "provincia", "producto", "bandera",
        "precio_promedio", "precio_min", "precio_max", "cantidad_registros"
    ]])

    safe_prod = "".join(c if c.isalnum() else "_" for c in str(producto_sel))[:40].strip("_") or "combustible"
    safe_prov = "".join(c if c.isalnum() else "_" for c in str(provincia_sel))[:30].strip("_") or "pais"

    st.download_button(
        "Descargar serie diaria en Excel",
        data=excel_bytes,
        file_name=f"serie_diaria_{safe_prod}_{safe_prov}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Debug de columnas detectadas", expanded=False):
        st.write("Columnas originales:", metadata["columnas_originales"])
        for k in ["fecha_col", "provincia_col", "producto_col", "precio_col", "bandera_col"]:
            st.write(f"{k}:", metadata[k])

    with st.expander("Debug tipo de cambio", expanded=False):
        dbg_fx = build_combustible_fx_df(df_plot).tail(10).copy()
        st.dataframe(dbg_fx, use_container_width=True)

# ═══════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════
ts = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="footer">
  EIA Open Data API v2 &nbsp;·&nbsp; Yahoo Finance &nbsp;·&nbsp; datos.energia.gob.ar &nbsp;·&nbsp; {ts}<br>
  Datos EIA con rezago de 1-2 días hábiles &nbsp;·&nbsp; Futuros con caché de 2 minutos &nbsp;·&nbsp; Combustibles AR con caché de 12 horas
</div>
""", unsafe_allow_html=True)
