# ============================================================
# OpenSankey USA-ECU — Dual-Country Financial Sankey Diagram Generator
# Supports US Yahoo Finance data and Ecuador NIIF-compliant data
# ============================================================
# INSTALL DEPENDENCIES:
#   pip install streamlit plotly pandas yfinance kaleido
#
# RUN:
#   streamlit run sankey_app.py
#
# DATA SOURCES:
#   - US: Yahoo Finance (yfinance) — internet needed only on fetch
#   - Ecuador: True Flavor S.A. (RUC 2390028132001) — 2024 financials
#
# RENDERING: 100% local (Plotly)
# ============================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import io

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OpenSankey USA-ECU • Financial Diagrams",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.title-gradient {
    font-size: 2.6rem; font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.subtitle { color: #9ca3af; font-size: 0.95rem; margin-top: -10px; margin-bottom: 10px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.9rem; }
div[data-testid="metric-container"] {
    background: #1e1e2e; border-radius: 12px;
    padding: 14px 18px; border: 1px solid #2d2d42;
}

/* Flag selector styling */
.flag-btn {
    font-size: 1.5rem;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
    background: rgba(255,255,255,0.1);
    transition: all 0.2s;
}
.flag-btn:hover {
    background: rgba(255,255,255,0.2);
}
.flag-btn.active {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.2);
}

/* Header container */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
}

/* NIFF badge */
.niff-badge {
    background: linear-gradient(135deg, #FFD100, #FDB913);
    color: #000;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    margin-left: 8px;
}

.country-badge {
    background: rgba(99, 102, 241, 0.2);
    color: #818cf8;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
    margin-left: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTS — SAMPLE DATA
# ─────────────────────────────────────────────
SAMPLE_DATA = {
    "Total Revenue":          60922e6,
    "Cost of Revenue":        16621e6,
    "Gross Profit":           44301e6,
    "R&D":                     8675e6,
    "SG&A":                    2654e6,
    "Other Operating Exp":        0.0,
    "Operating Income":       32972e6,
    "Interest Expense":           0.0,
    "Pretax Income":          33791e6,
    "Income Tax":              4042e6,
    "Net Income":             29760e6,
}

# ─────────────────────────────────────────────
# ECUADOR TRUE FLAVOR DATA (NIIF-compliant)
# RUC: 2390028132001 — Exportadora True Flavor S.A.
# Source: Superintendencia de Compañías 2024 filing
# Note: Full Income Statement breakdown needed from user
# ─────────────────────────────────────────────
ECUADOR_DATA = {
    "company_name": "EXPORTADORA TRUE FLAVOR S.A.",
    "ruc": "2390028132001",
    "year": 2024,
    "currency": "USD",
    # From Balance Sheet: RESULTADOS DEL EJERCICIO
    "Total Revenue":          0,  # TODO: Get from Income Statement
    "Cost of Revenue":        0,  # TODO: Get from Income Statement
    "Gross Profit":           0,  # TODO: Calculate
    "R&D":                    0,  # TODO: Get from Income Statement
    "SG&A":                   0,  # TODO: Get from Income Statement
    "Other Operating Exp":    0,  # TODO: Get from Income Statement
    "Operating Income":       0,  # TODO: Get from Income Statement
    "Interest Expense":       0,  # From financial expenses
    "Pretax Income":          85216.55,  # Approximate from Net Income
    "Income Tax":             0,  # TODO: Calculate from tax provision
    "Net Income":             85216.55,  # Confirmed from PDF
    # Balance Sheet data for reference
    "Total Assets":           300765.67,
    "Total Liabilities":      275265.15,
    "Equity":                 25500.52,
}

THEMES = {
    "dark":   {"bg": "#0e1117", "font": "#ffffff", "grid": "#1f2937"},
    "purple": {"bg": "#0f0a1e", "font": "#e9d5ff", "grid": "#1e1040"},
    "ocean":  {"bg": "#0a1628", "font": "#7dd3fc", "grid": "#0e2847"},
    "light":  {"bg": "#f9fafb", "font": "#111827", "grid": "#e5e7eb"},
    "sunset": {"bg": "#1a0500", "font": "#fed7aa", "grid": "#2d1000"},
}

NODE_PALETTES = {
    "vivid":   ["#22c55e","#ef4444","#3b82f6","#f59e0b","#f97316","#a855f7","#06b6d4","#64748b","#6366f1","#ec4899","#84cc16"],
    "pastel":  ["#86efac","#fca5a5","#93c5fd","#fcd34d","#fdba74","#d8b4fe","#67e8f9","#94a3b8","#a5b4fc","#f9a8d4","#bef264"],
    "neon":    ["#00ff88","#ff3366","#00aaff","#ffcc00","#ff6600","#cc00ff","#00cccc","#888888","#6600ff","#ff00aa","#aaff00"],
    "mono":    ["#d1d5db","#9ca3af","#6b7280","#4b5563","#374151","#1f2937","#111827","#e5e7eb","#f3f4f6","#374151","#d1d5db"],
    "ecuador": ["#FFD100","#0072CE","#CE1126","#FDB913","#3b82f6","#22c55e","#a855f7","#f97316","#06b6d4","#ec4899","#84cc16"],
}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt(val, currency="$", scale="B"):
    """Format a number as a financial value string."""
    if val is None or (isinstance(val, float) and pd.isna(val)) or val == 0:
        return "—"
    divisors = {"B": 1e9, "M": 1e6, "K": 1e3, "Raw": 1}
    d = divisors.get(scale, 1e9)
    return f"{currency}{val/d:.2f}{scale}"


def scale_val(val, scale="B"):
    """Convert raw value to scaled float."""
    divisors = {"B": 1e9, "M": 1e6, "K": 1e3, "Raw": 1}
    return val / divisors.get(scale, 1e9)


def safe_row(df, candidates):
    """Return the first matching row value from a DataFrame, by fuzzy index name."""
    if df is None or df.empty:
        return None
    for name in candidates:
        for idx in df.index:
            if name.lower().replace(" ", "") in str(idx).lower().replace(" ", ""):
                row = df.loc[idx]
                non_null = row.dropna()
                if len(non_null) > 0:
                    return row
    return None


def get_col(df, candidates, col_idx=0, default=0.0):
    """Get a single float value from a DataFrame row + column index."""
    row = safe_row(df, candidates)
    if row is None:
        return default
    try:
        col_vals = row.dropna()
        if col_idx < len(col_vals):
            return float(col_vals.iloc[col_idx])
        return default
    except Exception:
        return default


# ─────────────────────────────────────────────
# YAHOO FINANCE FETCH
# ─────────────────────────────────────────────
def fetch_ticker(symbol: str):
    """Fetch income statement + company info from Yahoo Finance."""
    try:
        t = yf.Ticker(symbol)
        fin = None
        for attr in ("income_stmt", "financials"):
            try:
                fin = getattr(t, attr)
                if fin is not None and not fin.empty:
                    break
            except Exception:
                pass

        if fin is None or fin.empty:
            return None, None, f"No income statement data found for '{symbol}'. Check the ticker symbol."

        info = {}
        try:
            info = t.info or {}
        except Exception:
            pass

        return fin, info, None
    except Exception as e:
        return None, None, f"Yahoo Finance error: {e}"


def parse_income(fin, col_idx=0):
    """Extract key income statement line items from a yfinance DataFrame."""
    g = lambda candidates: get_col(fin, candidates, col_idx)

    revenue    = g(["Total Revenue", "Revenue"])
    cogs       = g(["Cost Of Revenue", "Cost of Revenue", "Reconciled Cost Of Revenue"])
    gross      = g(["Gross Profit"])
    rd         = g(["Research And Development", "Research Development", "R&D"])
    sga        = g(["Selling General And Administration", "Selling General Administrative", "SGA"])
    other_opex = g(["Other Operating Expense", "Other Operating Expenses"])
    op_income  = g(["Operating Income", "Total Operating Income As Reported", "EBIT"])
    interest   = abs(g(["Interest Expense"]))
    pretax     = g(["Pretax Income", "Income Before Tax", "Pretax Income"])
    tax        = abs(g(["Tax Provision", "Income Tax Expense", "Income Tax"]))
    net_income = g(["Net Income", "Net Income Common Stockholders"])

    if gross == 0 and revenue > 0:
        gross = revenue - cogs
    if op_income == 0 and gross > 0:
        op_income = gross - rd - sga - abs(other_opex)
    if pretax == 0:
        pretax = op_income - interest
    if net_income == 0:
        net_income = pretax - tax

    return {
        "Total Revenue":      revenue,
        "Cost of Revenue":    abs(cogs),
        "Gross Profit":       abs(gross),
        "R&D":                abs(rd),
        "SG&A":               abs(sga),
        "Other Operating Exp":abs(other_opex),
        "Operating Income":   abs(op_income),
        "Interest Expense":   abs(interest),
        "Pretax Income":      abs(pretax),
        "Income Tax":         abs(tax),
        "Net Income":         abs(net_income),
    }


# ─────────────────────────────────────────────
# SANKEY BUILDER (column-per-stage, zero crossings)
# ─────────────────────────────────────────────
def build_sankey(data: dict, currency="$", scale="B", palette="vivid", title="Income Statement", is_ecuador=False) -> go.Figure:
    """
    Zero-crossing Sankey layout — each link only moves ONE column right.
    """
    colors = NODE_PALETTES.get(palette, NODE_PALETTES["vivid"])
    
    # Use Ecuador palette if in Ecuador mode
    if is_ecuador and palette == "vivid":
        colors = NODE_PALETTES["ecuador"]

    def rgba(hex_color, alpha=0.42):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{g},{b},{alpha})"

    d      = data
    rev    = max(d.get("Total Revenue",       0), 0)
    cogs   = max(d.get("Cost of Revenue",     0), 0)
    gross  = max(d.get("Gross Profit",        rev - cogs), 0)
    rd     = max(d.get("R&D",                 0), 0)
    sga    = max(d.get("SG&A",                0), 0)
    oo     = max(d.get("Other Operating Exp", 0), 0)
    op_inc = max(d.get("Operating Income",    gross - rd - sga - oo), 0)
    inter  = max(d.get("Interest Expense",    0), 0)
    pretax = max(d.get("Pretax Income",       op_inc - inter), 0)
    tax    = max(d.get("Income Tax",          0), 0)
    net    = max(d.get("Net Income",          pretax - tax), 0)

    sv = lambda v: scale_val(v, scale)
    fv = lambda v: fmt(v, currency, scale)

    X1, X2, X3, X4, X5 = 0.02, 0.25, 0.55, 0.78, 0.99

    nodes = []
    imap  = {}

    def add(name, val, color, x, y):
        y = round(max(0.01, min(0.99, y)), 4)
        imap[name] = len(nodes)
        nodes.append((name, val, color, x, y))

    add("Revenue",         rev,   colors[0], X1, 0.45)
    add("Cost of Revenue", cogs,  colors[1], X2, 0.05)
    add("Gross Profit",    gross, colors[2], X2, 0.58)

    exp_y    = 0.04
    exp_gap  = 0.13
    n_exp    = 0

    if rd > 0:
        add("R&D",        rd,  colors[3], X3, exp_y + n_exp * exp_gap)
        n_exp += 1
    if sga > 0:
        add("SG&A",       sga, colors[4], X3, exp_y + n_exp * exp_gap)
        n_exp += 1
    if oo > 0:
        add("Other OpEx", oo,  colors[5], X3, exp_y + n_exp * exp_gap)
        n_exp += 1

    oi_y = max(exp_y + n_exp * exp_gap + 0.16, 0.60)
    add("Operating Income", op_inc, colors[6], X3, oi_y)

    pt_y = oi_y + 0.14
    if inter > 0:
        inter_y = max(oi_y - 0.08, 0.50)
        add("Interest Exp.", inter, colors[7], X4, inter_y)
        pt_y = oi_y + 0.14

    add("Pretax Income", pretax, colors[8], X4, pt_y)

    tax_y = pt_y + 0.04
    net_y = pt_y + 0.14
    if tax > 0:
        add("Income Tax", tax, colors[9],  X5, min(tax_y, 0.88))
        net_y = tax_y + 0.12
    add("Net Income",   net,  colors[10], X5, min(net_y, 0.97))

    labels      = [f"{n[0]}\\n{fv(n[1])}" for n in nodes]
    node_colors = [n[2] for n in nodes]
    node_x      = [n[3] for n in nodes]
    node_y      = [n[4] for n in nodes]

    srcs, tgts, vals, lcolors = [], [], [], []

    def link(src, tgt, val, ci=0):
        s, t = imap.get(src, -1), imap.get(tgt, -1)
        if s >= 0 and t >= 0 and val > 0:
            srcs.append(s); tgts.append(t)
            vals.append(sv(val))
            lcolors.append(rgba(colors[ci]))

    link("Revenue",          "Cost of Revenue",  cogs,   1)
    link("Revenue",          "Gross Profit",     gross,  2)

    if rd  > 0: link("Gross Profit", "R&D",             rd,     3)
    if sga > 0: link("Gross Profit", "SG&A",            sga,    4)
    if oo  > 0: link("Gross Profit", "Other OpEx",      oo,     5)
    link("Gross Profit",     "Operating Income", op_inc, 6)

    if inter > 0: link("Operating Income", "Interest Exp.", inter, 7)
    link("Operating Income", "Pretax Income",    pretax, 8)

    if tax > 0: link("Pretax Income", "Income Tax", tax, 9)
    link("Pretax Income",    "Net Income",        net,   10)

    fig = go.Figure(go.Sankey(
        arrangement="fixed",
        node=dict(
            pad=18,
            thickness=24,
            line=dict(color="rgba(0,0,0,0)", width=0),
            label=labels,
            color=node_colors,
            x=node_x,
            y=node_y,
            hovertemplate="<b>%{label}</b><extra></extra>",
        ),
        link=dict(
            source=srcs,
            target=tgts,
            value=vals,
            color=lcolors,
            hovertemplate=f"Flow: %{{value:.2f}} {scale}<extra></extra>",
        ),
    ))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=18), x=0.5),
        height=650,
        margin=dict(l=10, r=10, t=70, b=20),
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def sidebar(country_mode):
    with st.sidebar:
        # Country indicator
        if country_mode == "US":
            st.markdown("## 🇺🇸 United States Mode")
            st.caption("Data from Yahoo Finance")
        else:
            st.markdown("## 🇪🇨 Ecuador Mode")
            st.caption("NIIF-compliant data • True Flavor S.A.")
            st.caption(f"RUC: {ECUADOR_DATA['ruc']}")
        
        st.divider()

        if country_mode == "US":
            # ── Fetch ──
            st.markdown("### 📈 Stock Data")
            ticker_sym = st.text_input("Ticker Symbol", value="NVDA",
                                       placeholder="AAPL, MSFT, NVDA …").upper().strip()
            fetch_btn = st.button("🔄 Fetch from Yahoo Finance", type="primary",
                                  use_container_width=True)
            st.divider()
        else:
            ticker_sym = ""
            fetch_btn = False
            # ── Ecuador Company Info ──
            st.markdown("### 🏢 Company Info")
            st.write(f"**{ECUADOR_DATA['company_name']}**")
            st.write(f"RUC: {ECUADOR_DATA['ruc']}")
            st.write(f"Year: {ECUADOR_DATA['year']}")
            st.divider()

        # ── Display ──
        st.markdown("### 🎨 Appearance")
        
        if country_mode == "EC":
            currency = "$"  # Ecuador uses USD
            st.info("🇪🇨 Ecuador uses USD as official currency")
        else:
            currency = st.selectbox("Currency", ["$","€","£","¥","₹","CHF "], index=0)
            
        if country_mode == "EC":
            scale = st.selectbox("Value Scale", ["K","M","B","Raw"], index=0,
                                help="K=Thousands for Ecuador data")
        else:
            scale    = st.selectbox("Value Scale", ["B","M","K","Raw"], index=0,
                                    help="B=Billions, M=Millions, K=Thousands")
                                    
        theme    = st.selectbox("Theme",   list(THEMES.keys()), index=0)
        
        if country_mode == "EC":
            palette  = st.selectbox("Colors",  list(NODE_PALETTES.keys()), index=4,
                                   help="Ecuador palette uses national colors")
        else:
            palette  = st.selectbox("Colors",  list(NODE_PALETTES.keys()), index=0)
            
        font_sz  = st.slider("Font Size", 10, 18, 12)

        st.divider()

        # ── Year ──
        if country_mode == "US":
            st.markdown("### 📅 Year")
            year_opts = st.session_state.get("year_opts", ["Latest"])
            sel_year  = st.selectbox("Fiscal Year", year_opts)
            show_yoy  = st.checkbox("YoY comparison", value=True)
            st.divider()
        else:
            sel_year = str(ECUADOR_DATA['year'])
            show_yoy = False
            st.markdown("### 📅 Year")
            st.write(f"Fiscal Year: {ECUADOR_DATA['year']}")
            st.divider()

        # ── Export ──
        st.markdown("### 💾 Export")
        exp_fmt = st.selectbox("Format", ["HTML","PNG","SVG"])
        exp_btn = st.button("⬇️ Export Diagram", use_container_width=True)

    return dict(
        country_mode=country_mode,
        ticker=ticker_sym, fetch=fetch_btn,
        currency=currency, scale=scale,
        theme=theme, palette=palette, font_sz=font_sz,
        sel_year=sel_year, show_yoy=show_yoy,
        exp_fmt=exp_fmt, exp_btn=exp_btn,
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # Session state init
    for k, v in [("fin", None), ("info", {}), ("ticker", None),
                 ("income", None), ("year_opts", ["Latest"]), ("country_mode", "US")]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Country Selector Header ─────────────────────────────────────
    col_header_left, col_header_right = st.columns([3, 1])
    
    with col_header_left:
        st.markdown('<p class="title-gradient">💹 OpenSankey USA-ECU</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Financial Statement → Sankey Diagram &nbsp;|&nbsp; US & Ecuador NIIF Support</p>', unsafe_allow_html=True)
    
    with col_header_right:
        st.markdown("<br>", unsafe_allow_html=True)
        # Flag selector using buttons
        flag_cols = st.columns(2)
        with flag_cols[0]:
            us_active = "active" if st.session_state.country_mode == "US" else ""
            if st.button("🇺🇸 US", key="us_flag", help="Switch to US Mode (Yahoo Finance)", 
                        use_container_width=True, type="primary" if st.session_state.country_mode == "US" else "secondary"):
                st.session_state.country_mode = "US"
                st.session_state.income = None
                st.rerun()
        with flag_cols[1]:
            ec_active = "active" if st.session_state.country_mode == "EC" else ""
            if st.button("🇪🇨 ECU", key="ec_flag", help="Switch to Ecuador Mode (True Flavor S.A.)", 
                        use_container_width=True, type="primary" if st.session_state.country_mode == "EC" else "secondary"):
                st.session_state.country_mode = "EC"
                st.session_state.income = ECUADOR_DATA.copy()
                st.rerun()
    
    st.divider()

    country_mode = st.session_state.country_mode
    cfg = sidebar(country_mode)

    # ── Fetch / Setup Data ────────────────────────────────────────
    if country_mode == "US":
        if cfg["fetch"] and cfg["ticker"]:
            with st.spinner(f"Fetching {cfg['ticker']} from Yahoo Finance…"):
                fin, info, err = fetch_ticker(cfg["ticker"])
            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state.fin    = fin
                st.session_state.info   = info
                st.session_state.ticker = cfg["ticker"]
                cols = list(fin.columns)
                years = [c.strftime("%Y") if hasattr(c, "strftime") else str(c) for c in cols]
                st.session_state.year_opts = years
                st.session_state.income    = parse_income(fin, 0)
                st.success(f"✅ Loaded {info.get('shortName', cfg['ticker'])}")
                st.rerun()

        # Resolve selected year → income data
        fin  = st.session_state.fin
        info = st.session_state.info

        col_idx = 0
        if fin is not None:
            yo = st.session_state.year_opts
            if cfg["sel_year"] in yo:
                col_idx = yo.index(cfg["sel_year"])
            income = parse_income(fin, col_idx)
            yoy    = parse_income(fin, col_idx + 1) if (cfg["show_yoy"] and col_idx + 1 < fin.shape[1]) else None
        else:
            income = st.session_state.income or SAMPLE_DATA
            yoy    = None
            
        company_label = st.session_state.ticker or "Sample"
        year_label   = cfg["sel_year"] if fin is not None else "FY2024 (approx.)"
        
    else:  # Ecuador mode
        income = st.session_state.income or ECUADOR_DATA.copy()
        yoy = None
        fin = None
        info = None
        company_label = "TRUE FLAVOR"
        year_label = str(ECUADOR_DATA['year'])

    th = THEMES[cfg["theme"]]

    # ── Tabs ─────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["📊 Sankey Diagram", "📋 Data Editor", "📈 Company Info", "❓ How to Use"])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 — SANKEY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    with t1:
        if country_mode == "US":
            using_sample = (fin is None)
            if using_sample:
                st.info("📌 Showing sample data (NVDA FY2024 approx.). Enter a ticker in the sidebar or click 🇪🇨 ECU for Ecuador data.")

            # Quick-load buttons
            c1, c2, c3, c4 = st.columns(4)
            for col, sym, emoji in [(c1,"NVDA","🟢"),(c2,"AAPL","🍎"),(c3,"MSFT","🪟"),(c4,"GOOGL","🔍")]:
                with col:
                    if st.button(f"{emoji} {sym}", use_container_width=True):
                        with st.spinner(f"Loading {sym}…"):
                            fin2, info2, err2 = fetch_ticker(sym)
                        if err2:
                            st.error(err2)
                        else:
                            st.session_state.fin    = fin2
                            st.session_state.info   = info2
                            st.session_state.ticker = sym
                            cols2 = list(fin2.columns)
                            years2 = [c.strftime("%Y") if hasattr(c,"strftime") else str(c) for c in cols2]
                            st.session_state.year_opts = years2
                            st.session_state.income    = parse_income(fin2, 0)
                            st.rerun()
        else:
            # Ecuador mode info
            st.info(f"🇪🇨 Showing **{ECUADOR_DATA['company_name']}** (RUC: {ECUADOR_DATA['ruc']}) — Fiscal Year {ECUADOR_DATA['year']}")
            st.markdown(f"<span class='niff-badge'>NIIF-compliant</span>", unsafe_allow_html=True)
            
            # Warning if data incomplete
            if income.get("Total Revenue", 0) == 0:
                st.warning("⚠️ Complete Income Statement breakdown not available. Showing Net Income from Balance Sheet. Please provide full Estado de Resultados PDF for detailed Sankey.")

        st.divider()

        # KPI metrics row
        sc  = cfg["scale"]
        cur = cfg["currency"]
        m1, m2, m3, m4 = st.columns(4)

        def delta_str(key):
            if yoy and yoy.get(key, 0):
                prev = yoy[key]
                curr = income.get(key, 0)
                if prev:
                    return f"{((curr - prev)/abs(prev)*100):+.1f}% YoY"
            return None

        if country_mode == "EC":
            m1.metric("Total Assets", fmt(income.get("Total Assets",0), cur, sc))
            m2.metric("Net Income",   fmt(income.get("Net Income",0), cur, sc))
            m3.metric("Total Liabilities", fmt(income.get("Total Liabilities",0), cur, sc))
            m4.metric("Equity",       fmt(income.get("Equity",0), cur, sc))
        else:
            m1.metric("Revenue",          fmt(income.get("Total Revenue",0),   cur, sc), delta_str("Total Revenue"))
            m2.metric("Gross Profit",     fmt(income.get("Gross Profit",0),    cur, sc), delta_str("Gross Profit"))
            m3.metric("Operating Income", fmt(income.get("Operating Income",0),cur, sc), delta_str("Operating Income"))
            m4.metric("Net Income",       fmt(income.get("Net Income",0),      cur, sc), delta_str("Net Income"))

        st.divider()

        # Build diagram
        title = f"{company_label} · Income Statement · {year_label}"
        if country_mode == "EC":
            title = f"🇪🇨 {company_label} · Estado de Resultados · {year_label}"

        fig = build_sankey(income, cur, sc, cfg["palette"], title, is_ecuador=(country_mode=="EC"))
        fig.update_layout(
            paper_bgcolor=th["bg"],
            font=dict(color=th["font"], size=cfg["font_sz"], family="Inter, Arial, sans-serif"),
            title_font_color=th["font"],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Export
        if cfg["exp_btn"]:
            fmt_choice = cfg["exp_fmt"]
            try:
                if fmt_choice == "HTML":
                    data                    = fig.to_html(include_plotlyjs="cdn")
                    st.download_button("📥 Download HTML", data=data,
                                       file_name=f"{company_label}_sankey.html",
                                       mime="text/html")
                else:
                    try:
                        img = fig.to_image(format=fmt_choice.lower(), width=1400, height=700, scale=2)
                        st.download_button(f"📥 Download {fmt_choice}", data=img,
                                           file_name=f"{company_label}_sankey.{fmt_choice.lower()}",
                                           mime=f"image/{fmt_choice.lower()}")
                    except Exception:
                        st.warning("⚠️ PNG/SVG requires kaleido: `pip install kaleido`. Exporting as HTML instead.")
                        data = fig.to_html(include_plotlyjs="cdn")
                        st.download_button("📥 Download HTML", data=data,
                                           file_name=f"{company_label}_sankey.html",
                                           mime="text/html")
            except Exception as e:
                st.error(f"Export error: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 — DATA EDITOR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    with t2:
        st.subheader("📋 Income Statement Editor")
        
        if country_mode == "EC":
            st.info("🇪🇨 Editing Ecuador data. Changes are local only.")
            st.markdown(f"**Company:** {ECUADOR_DATA['company_name']}")
            st.markdown(f"**RUC:** {ECUADOR_DATA['ruc']}")
        else:
            st.caption("Edit any value directly, or paste from Excel/Google Sheets. Changes update the diagram.")

        divisors = {"B": 1e9, "M": 1e6, "K": 1e3, "Raw": 1}
        div = divisors.get(cfg["scale"], 1e9)
        sc  = cfg["scale"]

        KEYS = [
            "Total Revenue","Cost of Revenue","Gross Profit",
            "R&D","SG&A","Other Operating Exp",
            "Operating Income","Interest Expense","Pretax Income",
            "Income Tax","Net Income",
        ]

        rows = []
        for k in KEYS:
            val  = income.get(k, 0)
            row  = {"Metric": k, f"Current ({sc})": round(val / div, 3)}
            if yoy:
                prev = yoy.get(k, 0)
                row[f"Prev Year ({sc})"] = round(prev / div, 3) if prev else 0
                if prev:
                    row["YoY %"] = f"{((val - prev)/abs(prev)*100):+.1f}%"
                else:
                    row["YoY %"] = "—"
            rows.append(row)

        df = pd.DataFrame(rows)

        col_cfg = {
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            f"Current ({sc})": st.column_config.NumberColumn(f"Current ({sc})", format="%.3f"),
        }
        if yoy:
            col_cfg[f"Prev Year ({sc})"] = st.column_config.NumberColumn(f"Prev Year ({sc})", format="%.3f", disabled=True)
            col_cfg["YoY %"] = st.column_config.TextColumn("YoY %", disabled=True)

        edited = st.data_editor(df, use_container_width=True, num_rows="fixed",
                                column_config=col_cfg, key="data_editor")

        if st.button("🔄 Apply Edits → Update Diagram", type="primary"):
            new_income = {}
            for _, row in edited.iterrows():
                new_income[row["Metric"]] = row[f"Current ({sc})"] * div
            st.session_state.income = new_income
            st.success("✅ Updated! Go to the **Sankey Diagram** tab.")

        st.divider()
        st.markdown("### ✏️ Start from Blank Template")
        blank_rows = [{"Metric": k, f"Value ({sc})": 0.0} for k in KEYS]
        blank_edited = st.data_editor(pd.DataFrame(blank_rows), use_container_width=True,
                                      num_rows="dynamic", key="blank_editor")
        if st.button("🚀 Generate from Template", type="secondary"):
            new_income = {}
            for _, row in blank_edited.iterrows():
                k = row.get("Metric","")
                v = row.get(f"Value ({sc})", 0.0)
                if k:
                    new_income[k] = float(v) * div
            st.session_state.income = new_income
            st.session_state.fin    = None
            st.session_state.ticker = "Custom"
            st.success("✅ Template set! Go to **Sankey Diagram** tab.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 3 — COMPANY INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    with t3:
        if country_mode == "EC":
            st.subheader("🇪🇨 Exportadora True Flavor S.A.")
            st.markdown(f"**RUC:** {ECUADOR_DATA['ruc']}")
            st.markdown(f"**Fiscal Year:** {ECUADOR_DATA['year']}")
            st.markdown(f"<span class='niff-badge'>NIIF-compliant Financial Reporting</span>", unsafe_allow_html=True)
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Assets", fmt(ECUADOR_DATA['Total Assets'], "$", "K"))
                st.metric("Current Assets", fmt(251273.53, "$", "K"))
                st.metric("Non-Current Assets", fmt(49492.14, "$", "K"))
            with col2:
                st.metric("Total Liabilities", fmt(ECUADOR_DATA['Total Liabilities'], "$", "K"))
                st.metric("Current Liabilities", fmt(244797.77, "$", "K"))
                st.metric("Non-Current Liabilities", fmt(30467.38, "$", "K"))
            
            st.divider()
            
            st.subheader("📊 Financial Highlights 2024")
            st.write(f"**Net Income:** {fmt(ECUADOR_DATA['Net Income'], '$', 'K')}")
            st.write(f"**Equity:** {fmt(ECUADOR_DATA['Equity'], '$', 'K')}")
            
            st.divider()
            
            st.markdown("### 📄 Source Document")
            st.write("Financial data extracted from:")
            st.write("- **Form:** SCV.NIIF.305170.2024.1")
            st.write("- **Superintendencia de Compañías, Valores y Seguros (Ecuador)**")
            st.write("- **Filing Date:** April 15, 2025")
            st.write("- **Legal Representative:** Flores Enriquez Nelson Sebastián")
            
            st.divider()
            
            st.markdown("### 🏛️ NIFF Compliance")
            st.write("""
            Ecuador adopted IFRS (NIIF) standards for all companies. This financial data follows:
            - **NIIF 1**: First-time Adoption of International Financial Reporting Standards
            - **NIIF 15**: Revenue from Contracts with Customers
            - **NIC 1**: Presentation of Financial Statements
            - **NIC 16**: Property, Plant and Equipment
            - **NIC 12**: Income Taxes
            """)
            
        elif info:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Company",    info.get("shortName", "—"))
                st.metric("Sector",     info.get("sector", "—"))
                st.metric("Industry",   info.get("industry", "—"))
                st.metric("Country",    info.get("country", "—"))
                st.metric("Market Cap", fmt(info.get("marketCap",0), cfg["currency"], "B"))
                pe = info.get("trailingPE")
                st.metric("P/E Ratio",  f"{pe:.1f}" if pe else "—")
                eps = info.get("trailingEps")
                st.metric("EPS",        f"{cfg['currency']}{eps:.2f}" if eps else "—")
            with c2:
                st.markdown("**Business Summary**")
                summary = info.get("longBusinessSummary","No description available.")
                st.write(summary[:1000] + ("…" if len(summary) > 1000 else ""))

                st.divider()
                st.markdown("**Raw Financials (all years)**")
                if fin is not None:
                    disp = fin.copy()
                    disp.columns = [c.strftime("%Y") if hasattr(c,"strftime") else str(c) for c in disp.columns]
                    st.dataframe(disp / 1e9, use_container_width=True,
                                 column_config={c: st.column_config.NumberColumn(c, format="%.2f B")
                                                for c in disp.columns})
        else:
            st.info("👈 Fetch a ticker symbol or switch to 🇪🇨 Ecuador mode to see company information.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 4 — HOW TO USE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━
    with t4:
        st.markdown("""
## How to Use OpenSankey USA-ECU

### 🌍 Country Modes

Click the flag buttons at the top right to switch between:
- **🇺🇸 US Mode**: Fetch live data from Yahoo Finance for any ticker
- **🇪🇨 Ecuador Mode**: View True Flavor S.A. (RUC 2390028132001) NIIF-compliant data

### 🚀 Quick Start (US Mode)
1. Ensure **🇺🇸 US** button is selected
2. Enter a **ticker symbol** in the sidebar (e.g. `NVDA`, `AAPL`, `TSLA`)
3. Click **Fetch from Yahoo Finance**
4. The Sankey diagram generates instantly

### 🇪🇨 Ecuador Mode
1. Click **🇪🇨 ECU** button
2. View **True Flavor S.A.** 2024 financial data
3. Data presented in **NIIF-compliant** format (Ecuadorian IFRS)
4. All values in **USD** (Ecuador's official currency)

### 🎨 Customize
- **Currency / Scale**: Switch between $, €, B/M/K/Raw
- **Theme**: Dark, Light, Ocean, Sunset, Purple
- **Colors**: Vivid, Pastel, Neon, Mono, Ecuador (special palette)
- **Font Size**: Adjust node label size

### 📋 Edit Data
- Go to **Data Editor** tab to tweak any value
- Paste directly from Excel or Google Sheets
- Click **Apply Edits** to regenerate the diagram

### 💾 Export
- **HTML**: Works everywhere, interactive, no install needed
- **PNG/SVG**: Requires `pip install kaleido`

### 📦 Dependencies
```bash
pip install streamlit plotly pandas yfinance kaleido
```

### 🔒 Privacy
- All data processing is local
- Yahoo Finance only called when you click **Fetch**
- Ecuador data is pre-loaded from official filings
- Nothing is stored in the cloud

### 🏛️ About NIFF (Ecuador)
Ecuador adopted **IFRS** (NIIF in Spanish) for all companies. Key standards:
- **NIIF 15**: Revenue recognition
- **NIIF 16**: Leases
- **NIC 1**: Financial statement presentation
- All amounts in **USD** (Ecuador dollarized in 2000)
        """)

    # Footer
    st.divider()
    if country_mode == "EC":
        st.caption("🇪🇨 OpenSankey USA-ECU • NIIF-compliant Ecuador data • True Flavor S.A. • Data: Superintendencia de Compañías")
    else:
        st.caption("🇺🇸 OpenSankey USA-ECU • Yahoo Finance data • Built with Streamlit & Plotly")


if __name__ == "__main__":
    main()
