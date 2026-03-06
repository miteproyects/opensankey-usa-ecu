# ============================================================
# SankeyViz — Financial Sankey Diagram Generator
# Inspired by SankeyArt.com
# ============================================================
# INSTALL DEPENDENCIES:
#   pip install streamlit plotly pandas yfinance kaleido
#
# RUN:
#   streamlit run sankey_app.py
#
# DATA SOURCE: Yahoo Finance (yfinance) — internet needed only on fetch
# RENDERING:   100% local (Plotly)
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
    page_title="SankeyViz • Financial Diagrams",
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
/* Custom red button style */
.red-button button {
    background-color: #ff4b4b !important;
    color: white !important;
    border: none !important;
}
.red-button button:hover {
    background-color: #ff3333 !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTS — SAMPLE DATA (NVDA FY2024 approx.)
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
}

# ─────────────────────────────────────────────
# COMPANY ICONS MAPPING
# ─────────────────────────────────────────────
COMPANY_ICONS = {
    # Tech
    "NVDA": "🟢",      # NVIDIA - green chip
    "AAPL": "🍎",      # Apple - apple
    "MSFT": "🪟",      # Microsoft - windows
    "GOOGL": "🔍",     # Google - search
    "GOOG": "🔍",      # Google - search
    "META": "👥",      # Meta - people/social
    "AMZN": "📦",      # Amazon - package
    "TSLA": "⚡",      # Tesla - lightning
    "NFLX": "🎬",      # Netflix - movie
    "AMD": "🔴",       # AMD - red chip
    "INTC": "🔵",      # Intel - blue chip
    "IBM": "💻",       # IBM - computer
    "ORCL": "🗄️",      # Oracle - database
    "CRM": "☁️",       # Salesforce - cloud
    "ADBE": "🎨",      # Adobe - creative
    "PYPL": "💳",      # PayPal - payment
    "UBER": "🚗",      # Uber - car
    "LYFT": "🚙",      # Lyft - car
    "ABNB": "🏠",      # Airbnb - house
    "ZM": "📹",        # Zoom - video
    "SNOW": "❄️",      # Snowflake - snow
    "PLTR": "🔮",      # Palantir - crystal ball
    
    # Beverages / Food
    "KO": "🥤",        # Coca-Cola - soda can
    "PEP": "🥤",       # Pepsi - soda
    "MNST": "⚡",       # Monster Energy - energy
    "KDP": "☕",        # Keurig Dr Pepper - coffee
    "SBUX": "☕",       # Starbucks - coffee
    "MCD": "🍔",       # McDonald's - burger
    "YUM": "🍗",        # Yum Brands - chicken
    "CMG": "🌯",        # Chipotle - burrito
    "DPZ": "🍕",        # Domino's - pizza
    
    # Retail
    "WMT": "🛒",       # Walmart - cart
    "TGT": "🎯",        # Target - target
    "COST": "🏪",       # Costco - warehouse
    "HD": "🔨",         # Home Depot - tools
    "LOW": "🔧",        # Lowe's - tools
    "BBY": "📺",        # Best Buy - TV
    
    # Finance / Banking
    "JPM": "🏦",        # JPMorgan - bank
    "BAC": "🏛️",        # Bank of America - building
    "WFC": "🐎",        # Wells Fargo - stagecoach/horse
    "GS": "💰",         # Goldman Sachs - money
    "MS": "📈",         # Morgan Stanley - chart
    "C": "💳",          # Citigroup - card
    "AXP": "💳",        # American Express - card
    "V": "💳",          # Visa - card
    "MA": "💳",         # Mastercard - card
    "BLK": "⬛",        # BlackRock - black rock
    
    # Energy
    "XOM": "⛽",        # ExxonMobil - gas
    "CVX": "🛢️",        # Chevron - oil
    "COP": "🛢️",        # ConocoPhillips - oil
    "EOG": "🛢️",        # EOG Resources - oil
    "SLB": "🔧",        # Schlumberger - tools
    "OXY": "🏭",        # Occidental - factory
    
    # Healthcare / Pharma
    "JNJ": "💊",        # Johnson & Johnson - pill
    "PFE": "💉",        # Pfizer - syringe
    "MRK": "🧪",        # Merck - lab
    "ABBV": "💊",       # AbbVie - pill
    "LLY": "🧬",        # Eli Lilly - DNA
    "TMO": "🔬",        # Thermo Fisher - microscope
    "UNH": "🏥",        # UnitedHealth - hospital
    "CVS": "💊",        # CVS - pharmacy
    
    # Telecom
    "T": "📞",          # AT&T - phone
    "VZ": "📡",         # Verizon - signal
    "TMUS": "📱",       # T-Mobile - phone
    
    # Entertainment / Media
    "DIS": "🏰",        # Disney - castle
    "WBD": "📺",        # Warner Bros - TV
    "PARA": "🎬",       # Paramount - movie
    "SPOT": "🎵",       # Spotify - music
    "SONY": "🎮",       # Sony - gaming
    "EA": "🎮",         # Electronic Arts - gaming
    "TTWO": "🎮",       # Take-Two - gaming
    
    # Automotive
    "F": "🚗",          # Ford - car
    "GM": "🚙",         # GM - car
    "STLA": "🚐",       # Stellantis - van
    "TM": "🚘",         # Toyota - car
    "HMC": "🚗",        # Honda - car
    
    # Airlines / Travel
    "DAL": "✈️",        # Delta - plane
    "UAL": "✈️",        # United - plane
    "AAL": "✈️",        # American - plane
    "LUV": "💛",        # Southwest - heart
    "CCL": "🚢",        # Carnival - cruise
    "RCL": "🛳️",        # Royal Caribbean - ship
    
    # Industrial
    "GE": "⚙️",         # GE - gear
    "HON": "🏭",        # Honeywell - factory
    "CAT": "🚜",        # Caterpillar - tractor
    "DE": "🌾",         # Deere - tractor/farm
    "BA": "✈️",         # Boeing - plane
    "RTX": "🚀",        # Raytheon - rocket
    "LMT": "🛩️",        # Lockheed - jet
    
    # Materials / Mining
    "LIN": "🎈",        # Linde - gas
    "APD": "💨",        # Air Products - air
    "NEM": "⛏️",        # Newmont - mining
    "FCX": "⛏️",        # Freeport - mining
    
    # Real Estate
    "AMT": "📡",        # American Tower - tower
    "PLD": "🏭",        # Prologis - warehouse
    "CCI": "📶",        # Crown Castle - signal
    
    # Utilities
    "NEE": "⚡",         # NextEra - energy
    "DUK": "⚡",         # Duke - energy
    "SO": "⚡",          # Southern - energy
    "AEP": "⚡",         # AEP - energy
    
    # Misc / Default
    "DEFAULT": "🟢",    # Default green circle
}

def get_company_icon(ticker):
    """Get the appropriate icon for a company ticker."""
    return COMPANY_ICONS.get(ticker.upper(), COMPANY_ICONS["DEFAULT"])


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
            return None, None, f"No income statement data found for '{symbol}'."
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
    cogs       = g(["Cost Of Revenue", "Cost of Revenue"])
    gross      = g(["Gross Profit"])
    rd         = g(["Research And Development", "R&D"])
    sga        = g(["Selling General And Administration", "SGA"])
    other_opex = g(["Other Operating Expense"])
    op_income  = g(["Operating Income", "EBIT"])
    interest   = abs(g(["Interest Expense"]))
    pretax     = g(["Pretax Income", "Income Before Tax"])
    tax        = abs(g(["Tax Provision", "Income Tax Expense"]))
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
# SANKEY BUILDER
# ─────────────────────────────────────────────
def build_sankey(data: dict, currency="$", scale="B", palette="vivid", title="Income Statement") -> go.Figure:
    colors = NODE_PALETTES.get(palette, NODE_PALETTES["vivid"])
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
    add("Pretax Income", pretax, colors[8], X4, pt_y)
    tax_y = pt_y + 0.04
    net_y = pt_y + 0.14
    if tax > 0:
        add("Income Tax", tax, colors[9],  X5, min(tax_y, 0.88))
        net_y = tax_y + 0.12
    add("Net Income",   net,  colors[10], X5, min(net_y, 0.97))
    labels      = [f"{n[0]}\n{fv(n[1])}" for n in nodes]
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
            pad=18, thickness=24,
            line=dict(color="rgba(0,0,0,0)", width=0),
            label=labels, color=node_colors, x=node_x, y=node_y,
            hovertemplate="<b>%{label}</b><extra></extra>",
        ),
        link=dict(
            source=srcs, target=tgts, value=vals, color=lcolors,
            hovertemplate=f"Flow: %{{value:.2f}} {scale}<extra></extra>",
        ),
    ))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=18), x=0.5),
        height=650, margin=dict(l=10, r=10, t=70, b=20),
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR (Simplified)
# ─────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("## 💹 SankeyViz")
        st.caption("Financial diagrams — local & private")
        st.divider()

        # ── Display ──
        st.markdown("### 🎨 Appearance")
        currency = st.selectbox("Currency", ["$","€","£","¥","₹","CHF "], index=0)
        scale    = st.selectbox("Value Scale", ["B","M","K","Raw"], index=0)
        theme    = st.selectbox("Theme",   list(THEMES.keys()), index=0)
        palette  = st.selectbox("Colors",  list(NODE_PALETTES.keys()), index=0)
        font_sz  = st.slider("Font Size", 10, 18, 12)

        st.divider()

        # ── Export ──
        st.markdown("### 💾 Export")
        exp_fmt = st.selectbox("Format", ["HTML","PNG","SVG"])
        exp_btn = st.button("⬇️ Export Diagram", use_container_width=True)

    return dict(
        currency=currency, scale=scale,
        theme=theme, palette=palette, font_sz=font_sz,
        exp_fmt=exp_fmt, exp_btn=exp_btn,
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # Session state init
    for k, v in [("fin", None), ("info", {}), ("ticker", "NVDA"),
                 ("income", None), ("year_opts", ["2025", "2024", "2023", "2022"]),
                 ("analysis_year", 2025), ("comparison_year", 2024),
                 ("data_loaded", False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    cfg = sidebar()

    # ── Header ──────────────────────────────────────────────────────
    st.markdown('<p class="title-gradient">💹 SankeyViz</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Financial Statement → Sankey Diagram &nbsp;|&nbsp; Data: Yahoo Finance &nbsp;|&nbsp; Rendering: 100% local</p>', unsafe_allow_html=True)
    st.divider()

    # ── Main Search Interface ───────────────────────────────────────
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        ticker_input = st.text_input("Enter ticker symbol (e.g., NVDA)", 
                                     value=st.session_state.ticker,
                                     placeholder="AAPL, MSFT, NVDA, META...").upper().strip()
    
    with col2:
        period_type = st.selectbox("Period", ["Yearly", "Quarterly"], index=0)
    
    with col3:
        st.write("")  # Spacer
        st.write("")
    
    # Year selectors - interdependent, based on available Yahoo Finance data
    col1, col2 = st.columns([2, 2])
    
    # Get available years from Yahoo Finance data (or default if not loaded yet)
    if st.session_state.data_loaded and st.session_state.year_opts:
        # Extract years from Yahoo Finance data
        years_avail = st.session_state.year_opts
        available_years = []
        for y in years_avail:
            y_str = str(y)
            y_year = y_str[:4] if len(y_str) >= 4 else y_str
            try:
                year_int = int(y_year)
                if year_int not in available_years:
                    available_years.append(year_int)
            except ValueError:
                pass
        available_years.sort(reverse=True)  # Newest first
    else:
        # Default years until data is loaded
        available_years = [2025, 2024, 2023, 2022]
    
    # Get current values from session state
    current_analysis = st.session_state.analysis_year
    current_comparison = st.session_state.comparison_year
    
    # Ensure valid relationship: comparison < analysis
    if current_comparison >= current_analysis:
        # Find a valid comparison year (one less than analysis, if available)
        analysis_idx = available_years.index(current_analysis) if current_analysis in available_years else 0
        if analysis_idx + 1 < len(available_years):
            current_comparison = available_years[analysis_idx + 1]
        else:
            # Fallback: use the oldest available year
            current_comparison = available_years[-1] if available_years else 2022
        st.session_state.comparison_year = current_comparison
    
    with col1:
        st.markdown("**Initial time period to analyze:**")
        # Analysis year must be in available years and greater than comparison
        valid_analysis_years = [y for y in available_years if y > current_comparison]
        
        if not valid_analysis_years:
            valid_analysis_years = available_years[:1]  # At least the most recent
        
        # Ensure current analysis year is in valid options
        if current_analysis not in valid_analysis_years:
            current_analysis = valid_analysis_years[0]
            st.session_state.analysis_year = current_analysis
        
        analysis_index = valid_analysis_years.index(current_analysis)
        
        analysis_year = st.selectbox("Analysis Year", 
                                     valid_analysis_years, 
                                     index=analysis_index,
                                     label_visibility="collapsed",
                                     key="analysis_year_select")
        # Update session state immediately when changed
        if analysis_year != st.session_state.analysis_year:
            st.session_state.analysis_year = analysis_year
            st.rerun()
    
    with col2:
        st.markdown("**Period for comparison:**")
        # Comparison year must be in available years and less than analysis year
        valid_comparison_years = [y for y in available_years if y < analysis_year]
        
        if not valid_comparison_years:
            # If no valid comparison, use years less than max available
            max_year = max(available_years) if available_years else 2025
            valid_comparison_years = [y for y in available_years if y < max_year]
        
        # Ensure current comparison year is in valid options
        if current_comparison not in valid_comparison_years:
            current_comparison = valid_comparison_years[0] if valid_comparison_years else available_years[-1]
            st.session_state.comparison_year = current_comparison
        
        comparison_index = valid_comparison_years.index(current_comparison)
        
        comparison_year = st.selectbox("Comparison Year", 
                                       valid_comparison_years, 
                                       index=comparison_index,
                                       label_visibility="collapsed",
                                       key="comparison_year_select")
        # Update session state immediately when changed
        if comparison_year != st.session_state.comparison_year:
            st.session_state.comparison_year = comparison_year
            st.rerun()
    
    st.divider()

    # ── Check if we need to load/update data ────────────────────────
    # Trigger reload when ticker or years change
    ticker_changed = ticker_input != st.session_state.ticker
    years_changed = analysis_year != st.session_state.analysis_year or comparison_year != st.session_state.comparison_year
    needs_reload = ticker_changed or years_changed or not st.session_state.data_loaded

    if needs_reload and ticker_input:
        with st.spinner(f"Loading {ticker_input} data..."):
            # Only fetch from Yahoo if ticker changed or first load
            if ticker_changed or not st.session_state.data_loaded:
                fin, info, err = fetch_ticker(ticker_input)
                if err:
                    st.error(f"❌ {err}")
                    fin = None
                    info = None
                else:
                    st.session_state.fin = fin
                    st.session_state.info = info
                    st.session_state.ticker = ticker_input
                    st.session_state.data_loaded = True
                    
                    # Build year list from column headers
                    cols = list(fin.columns)
                    years_avail = [c.strftime("%Y") if hasattr(c, "strftime") else str(c) for c in cols]
                    st.session_state.year_opts = years_avail
            else:
                # Use existing data, just update years
                fin = st.session_state.fin
                info = st.session_state.info
                st.session_state.analysis_year = analysis_year
                st.session_state.comparison_year = comparison_year
            
            if fin is not None:
                # Find column indices for selected years
                years_avail = st.session_state.year_opts
                analysis_idx = 0
                comparison_idx = None
                for i, y in enumerate(years_avail):
                    y_str = str(y)
                    # Extract year from date string (e.g., "2020-01-31 00:00:00" -> "2020")
                    y_year = y_str[:4] if len(y_str) >= 4 else y_str
                    if str(analysis_year) == y_year:
                        analysis_idx = i
                    if str(comparison_year) == y_year:
                        comparison_idx = i
                
                st.session_state.analysis_idx = analysis_idx
                st.session_state.comparison_idx = comparison_idx
                st.session_state.income = parse_income(fin, analysis_idx)
                
                # Force rerun to update display with new data
                if ticker_changed:
                    st.rerun()

    # ── Resolve selected year → income data ────────────────────────
    fin  = st.session_state.fin
    info = st.session_state.info

    if fin is not None:
        # Recalculate indices based on current year selections
        years_avail = st.session_state.year_opts
        analysis_year = st.session_state.get("analysis_year", 2025)
        comparison_year = st.session_state.get("comparison_year", 2024)
        
        # Check if comparison year data is available
        
        analysis_idx = 0
        comparison_idx = None
        for i, y in enumerate(years_avail):
            y_str = str(y)
            # Extract year from date string (e.g., "2020-01-31 00:00:00" -> "2020")
            y_year = y_str[:4] if len(y_str) >= 4 else y_str
            if str(analysis_year) == y_year:
                analysis_idx = i
            if str(comparison_year) == y_year:
                comparison_idx = i
        
        # Store whether comparison data is available
        
        st.session_state.analysis_idx = analysis_idx
        st.session_state.comparison_idx = comparison_idx
        
        income = parse_income(fin, analysis_idx)
        yoy = parse_income(fin, comparison_idx) if comparison_idx is not None else None
    else:
        income = SAMPLE_DATA
        yoy = None

    th = THEMES[cfg["theme"]]

    # ── Display Results ─────────────────────────────────────────────
    
    # Company header with icon
    company_icon = get_company_icon(st.session_state.ticker)
    analysis_year = st.session_state.get("analysis_year", 2025)
    comparison_year = st.session_state.get("comparison_year", 2021)
    
    if info:
        st.markdown(f"### {company_icon} {st.session_state.ticker}")
    else:
        st.markdown(f"### 📊 {st.session_state.ticker}")
    
    # Show YoY comparison info
    if yoy:
        st.caption(f"📊 Comparing FY{analysis_year} vs FY{comparison_year}")
    else:
        st.caption(f"⚠️ No YoY data available for FY{comparison_year}")
    
    # KPI metrics row
    sc  = cfg["scale"]
    cur = cfg["currency"]
    m1, m2, m3, m4 = st.columns(4)

    def delta_str(key):
        if yoy and key in yoy and key in income:
            prev = yoy[key]
            curr = income[key]
            if prev and prev != 0:
                delta = ((curr - prev) / abs(prev)) * 100
                return f"{delta:+.1f}%"
        return None

    m1.metric("Revenue",          fmt(income.get("Total Revenue",0),   cur, sc), delta_str("Total Revenue"))
    m2.metric("Gross Profit",     fmt(income.get("Gross Profit",0),    cur, sc), delta_str("Gross Profit"))
    m3.metric("Operating Income", fmt(income.get("Operating Income",0),cur, sc), delta_str("Operating Income"))
    m4.metric("Net Income",       fmt(income.get("Net Income",0),      cur, sc), delta_str("Net Income"))

    st.divider()

    # Build diagram
    ticker_label = st.session_state.ticker
    analysis_year = st.session_state.get("analysis_year", 2025)
    title = f"{ticker_label} · Income Statement · FY{analysis_year}"

    fig = build_sankey(income, cur, sc, cfg["palette"], title)
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
                data = fig.to_html(include_plotlyjs="cdn")
                st.download_button("📥 Download HTML", data=data,
                                   file_name=f"{ticker_label}_sankey.html",
                                   mime="text/html")
            else:
                try:
                    img = fig.to_image(format=fmt_choice.lower(), width=1400, height=700, scale=2)
                    st.download_button(f"📥 Download {fmt_choice}", data=img,
                                       file_name=f"{ticker_label}_sankey.{fmt_choice.lower()}",
                                       mime=f"image/{fmt_choice.lower()}")
                except Exception:
                    st.warning("⚠️ PNG/SVG requires kaleido: `pip install kaleido`. Exporting as HTML instead.")
                    data = fig.to_html(include_plotlyjs="cdn")
                    st.download_button("📥 Download HTML", data=data,
                                       file_name=f"{ticker_label}_sankey.html",
                                       mime="text/html")
        except Exception as e:
            st.error(f"Export error: {e}")

    # Footer
    st.divider()
    st.caption("💹 SankeyViz • Local financial diagram tool • Data: Yahoo Finance • Built with Streamlit & Plotly")


if __name__ == "__main__":
    main()
