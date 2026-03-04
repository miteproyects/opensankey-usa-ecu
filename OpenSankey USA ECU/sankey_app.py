# ============================================================
# OpenSankey USA-ECU — Dual-Country Financial Sankey Diagram Generator
# Supports US Yahoo Finance data and Ecuador NIIF-compliant data
# ============================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="OpenSankey USA-ECU • Financial Diagrams",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

.company-btn {
    background: linear-gradient(135deg, #FFD100, #FDB913);
    color: #000;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

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

SAMPLE_DATA_PREV = {
    "Total Revenue":          52582e6,
    "Cost of Revenue":        14892e6,
    "Gross Profit":           37690e6,
    "R&D":                     7346e6,
    "SG&A":                    2159e6,
    "Other Operating Exp":        0.0,
    "Operating Income":       28185e6,
    "Interest Expense":           0.0,
    "Pretax Income":          29154e6,
    "Income Tax":              3620e6,
    "Net Income":             25534e6,
}

# ─────────────────────────────────────────────
# ECUADOR COMPANIES DATA
# ─────────────────────────────────────────────

ECUADOR_COMPANIES = {
    "True Flavor": {
        "ruc": "2390028132001",
        "name": "EXPORTADORA TRUE FLAVOR S.A.",
        "short_name": "TRUE FLAVOR",
        2023: {
            "Total Revenue":          842372.00,
            "Cost of Revenue":        586446.42,
            "Gross Profit":           255925.58,
            "R&D":                    0.0,
            "SG&A":                   211948.47,
            "Other Operating Exp":    54.35,
            "Operating Income":       11681.68,
            "Interest Expense":       32241.08,
            "Pretax Income":          11681.68,
            "Income Tax":             0.0,
            "Net Income":             11681.68,
        },
        2024: {
            "Total Revenue":          1040113.67,
            "Cost of Revenue":        725536.75,
            "Gross Profit":           314576.92,
            "R&D":                    0.0,
            "SG&A":                   215989.13,
            "Other Operating Exp":    0.0,
            "Operating Income":       78053.59,
            "Interest Expense":       20534.20,
            "Pretax Income":          78053.59,
            "Income Tax":             0.0,
            "Net Income":             85216.55,
            "Total Assets":           300765.67,
            "Total Liabilities":      275265.15,
            "Equity":                 25500.52,
        }
    },
    "Supermaxi": {
        "ruc": "1790016919001",
        "name": "CORPORACION FAVORITA C.A.",
        "short_name": "SUPERMAXI",
        2023: {
            "Total Revenue":          2483015099.25,
            "Cost of Revenue":        1817217513.45,
            "Gross Profit":           665797585.80,
            "R&D":                    0.0,
            "SG&A":                   87685271.84,
            "Other Operating Exp":    304020295.32,
            "Operating Income":       274092018.64,
            "Interest Expense":       27811078.97,
            "Pretax Income":          209338798.72,
            "Income Tax":             44103982.30,
            "Net Income":             165234816.42,
        },
        2024: {
            "Total Revenue":          2546101459.75,
            "Cost of Revenue":        1870957440.66,
            "Gross Profit":           675144019.09,
            "R&D":                    0.0,
            "SG&A":                   102530577.54,
            "Other Operating Exp":    306000724.92,
            "Operating Income":       266612716.63,
            "Interest Expense":       25572918.55,
            "Pretax Income":          204883828.37,
            "Income Tax":             47105742.31,
            "Net Income":             157778086.06,
            "Total Assets":           1500000000.00,
            "Total Liabilities":      900000000.00,
            "Equity":                 600000000.00,
        }
    }
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

def fmt(val, currency="$", scale="B"):
    if val is None or (isinstance(val, float) and pd.isna(val)) or val == 0:
        return "—"
    divisors = {"B": 1e9, "M": 1e6, "K": 1e3, "Raw": 1}
    d = divisors.get(scale, 1e9)
    return f"{currency}{val/d:.2f}{scale}"

def scale_val(val, scale="B"):
    divisors = {"B": 1e9, "M": 1e6, "K": 1e3, "Raw": 1}
    return val / divisors.get(scale, 1e9)

def get_col(df, candidates, col_idx=0, default=0.0):
    if df is None or df.empty:
        return default
    for name in candidates:
        for idx in df.index:
            if name.lower().replace(" ", "") in str(idx).lower().replace(" ", ""):
                row = df.loc[idx]
                try:
                    col_vals = row.dropna()
                    if col_idx < len(col_vals):
                        return float(col_vals.iloc[col_idx])
                    return default
                except Exception:
                    return default
    return default

def fetch_ticker(symbol: str):
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
    net_income = g(["Net Income"])
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

def build_sankey(data: dict, currency="$", scale="B", palette="vivid", title="Income Statement", is_ecuador=False) -> go.Figure:
    colors = NODE_PALETTES.get(palette, NODE_PALETTES["vivid"])
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

def main():
    for k, v in [("fin", None), ("info", {}), ("ticker", None),
                 ("income", None), ("year_opts", ["Latest"]), ("country_mode", "US"),
                 ("ecuador_company", "True Flavor"), ("ecuador_year", 2024), ("ecuador_yoy", True)]:
        if k not in st.session_state:
            st.session_state[k] = v

    col_header_left, col_header_right = st.columns([3, 1])
    with col_header_left:
        st.markdown('<p class="title-gradient">💹 OpenSankey USA-ECU</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Financial Statement → Sankey Diagram</p>', unsafe_allow_html=True)
    with col_header_right:
        st.markdown("<br>", unsafe_allow_html=True)
        flag_cols = st.columns(2)
        with flag_cols[0]:
            if st.button("🇺🇸 US", key="us_flag", use_container_width=True, 
                        type="primary" if st.session_state.country_mode == "US" else "secondary"):
                st.session_state.country_mode = "US"
                st.session_state.income = None
                st.rerun()
        with flag_cols[1]:
            if st.button("🇪🇨 ECU", key="ec_flag", use_container_width=True,
                        type="primary" if st.session_state.country_mode == "EC" else "secondary"):
                st.session_state.country_mode = "EC"
                st.session_state.income = ECUADOR_COMPANIES["True Flavor"][2024].copy()
                st.rerun()
    st.divider()
    
    country_mode = st.session_state.country_mode
    
    with st.sidebar:
        if country_mode == "US":
            st.markdown("## 🇺🇸 United States Mode")
            st.caption("Data from Yahoo Finance")
        else:
            st.markdown("## 🇪🇨 Ecuador Mode")
            st.caption("NIIF-compliant data")
        
        st.divider()

        if country_mode == "US":
            st.markdown("### 📈 Stock Data")
            ticker_sym = st.text_input("Ticker Symbol", value="NVDA").upper().strip()
            fetch_btn = st.button("🔄 Fetch from Yahoo Finance", type="primary", use_container_width=True)
            st.divider()
        else:
            ticker_sym = ""
            fetch_btn = False
            st.markdown("### 🏢 Company")
            selected_company = st.selectbox(
                "Select Company", 
                list(ECUADOR_COMPANIES.keys()),
                index=list(ECUADOR_COMPANIES.keys()).index(st.session_state.ecuador_company)
            )
            if selected_company != st.session_state.ecuador_company:
                st.session_state.ecuador_company = selected_company
                company_data = ECUADOR_COMPANIES[selected_company]
                st.session_state.income = company_data[st.session_state.ecuador_year].copy()
                st.rerun()
            
            company_info = ECUADOR_COMPANIES[selected_company]
            st.write(f"**{company_info['name']}**")
            st.write(f"RUC: {company_info['ruc']}")
            st.divider()
            
            st.markdown("### 📅 Year")
            ec_year = st.selectbox("Fiscal Year", [2024, 2023], 
                                   index=0 if st.session_state.ecuador_year == 2024 else 1)
            if ec_year != st.session_state.ecuador_year:
                st.session_state.ecuador_year = ec_year
                st.session_state.income = company_info[ec_year].copy()
                st.rerun()
            show_yoy_ec = st.checkbox("YoY comparison", value=st.session_state.ecuador_yoy, key="ecuador_yoy")
            st.divider()

        st.markdown("### 🎨 Appearance")
        if country_mode == "EC":
            currency = "$"
            st.info("🇪🇨 Ecuador uses USD as official currency")
        else:
            currency = st.selectbox("Currency", ["$","€","£","¥"], index=0)
            
        if country_mode == "EC":
            scale = st.selectbox("Value Scale", ["M","K","B","Raw"], index=0,
                               help="M=Millions for Ecuador retailers")
        else:
            scale = st.selectbox("Value Scale", ["B","M","K","Raw"], index=0)
            
        theme = st.selectbox("Theme", list(THEMES.keys()), index=0)
        
        if country_mode == "EC":
            palette = st.selectbox("Colors", list(NODE_PALETTES.keys()), index=4)
        else:
            palette = st.selectbox("Colors", list(NODE_PALETTES.keys()), index=0)
            
        font_sz = st.slider("Font Size", 10, 18, 12)
        st.divider()

        if country_mode == "US":
            st.markdown("### 📅 Year")
            year_opts = st.session_state.get("year_opts", ["Latest"])
            sel_year = st.selectbox("Fiscal Year", year_opts)
            show_yoy = st.checkbox("YoY comparison", value=True)
            st.divider()
        else:
            sel_year = str(st.session_state.ecuador_year)
            show_yoy = st.session_state.ecuador_yoy
            st.divider()

        st.markdown("### 💾 Export")
        exp_fmt = st.selectbox("Format", ["HTML","PNG","SVG"])
        exp_btn = st.button("⬇️ Export Diagram", use_container_width=True)

    cfg = dict(
        country_mode=country_mode, ticker=ticker_sym, fetch=fetch_btn,
        currency=currency, scale=scale, theme=theme, palette=palette, font_sz=font_sz,
        sel_year=sel_year, show_yoy=show_yoy if country_mode == "US" else st.session_state.ecuador_yoy,
        exp_fmt=exp_fmt, exp_btn=exp_btn,
    )

    if country_mode == "US":
        if cfg["fetch"] and cfg["ticker"]:
            with st.spinner(f"Fetching {cfg['ticker']}…"):
                fin, info, err = fetch_ticker(cfg["ticker"])
            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state.fin = fin
                st.session_state.info = info
                st.session_state.ticker = cfg["ticker"]
                cols = list(fin.columns)
                years = [c.strftime("%Y") if hasattr(c, "strftime") else str(c) for c in cols]
                st.session_state.year_opts = years
                st.session_state.income = parse_income(fin, 0)
                st.success(f"✅ Loaded {info.get('shortName', cfg['ticker'])}")
                st.rerun()

        fin = st.session_state.fin
        info = st.session_state.info
        col_idx = 0
        if fin is not None:
            yo = st.session_state.year_opts
            if cfg["sel_year"] in yo:
                col_idx = yo.index(cfg["sel_year"])
            income = parse_income(fin, col_idx)
            yoy = parse_income(fin, col_idx + 1) if (cfg["show_yoy"] and col_idx + 1 < fin.shape[1]) else None
        else:
            income = st.session_state.income or SAMPLE_DATA
            yoy = SAMPLE_DATA_PREV if cfg["show_yoy"] else None
        company_label = st.session_state.ticker or "Sample"
        year_label = cfg["sel_year"] if fin is not None else "FY2024"
        
    else:
        current_company = st.session_state.ecuador_company
        current_year = st.session_state.ecuador_year
        company_data = ECUADOR_COMPANIES[current_company]
        
        if st.session_state.income is None:
            st.session_state.income = company_data[current_year].copy()
        
        income = st.session_state.income
        
        yoy = None
        if st.session_state.ecuador_yoy and current_year == 2024:
            yoy = company_data[2023]
        
        fin = None
        info = None
        company_label = company_data['short_name']
        year_label = str(current_year)
        ruc = company_data['ruc']
        full_name = company_data['name']

    th = THEMES[cfg["theme"]]
    t1, t2, t3, t4 = st.tabs(["📊 Sankey", "📋 Data", "📈 Info", "❓ Help"])
    
    with t1:
        if country_mode == "US":
            using_sample = (fin is None)
            if using_sample:
                st.info("📌 Showing sample data. Enter a ticker or click 🇪🇨 ECU for Ecuador data.")
            c1, c2, c3, c4 = st.columns(4)
            for col, sym, emoji in [(c1,"NVDA","🟢"),(c2,"AAPL","🍎"),(c3,"MSFT","🪟"),(c4,"GOOGL","🔍")]:
                with col:
                    if st.button(f"{emoji} {sym}", use_container_width=True):
                        with st.spinner(f"Loading {sym}…"):
                            fin2, info2, err2 = fetch_ticker(sym)
                        if err2:
                            st.error(err2)
                        else:
                            st.session_state.fin = fin2
                            st.session_state.info = info2
                            st.session_state.ticker = sym
                            cols2 = list(fin2.columns)
                            years2 = [c.strftime("%Y") if hasattr(c,"strftime") else str(c) for c in cols2]
                            st.session_state.year_opts = years2
                            st.session_state.income = parse_income(fin2, 0)
                            st.rerun()
        else:
            st.info(f"🇪🇨 **{full_name}** (RUC: {ruc}) — Fiscal Year {year_label}")
            st.markdown(f"<span class='niff-badge'>NIIF-compliant</span>", unsafe_allow_html=True)
            
            # Company selection buttons like US mode
            st.markdown("### 🏢 Select Company")
            c1, c2 = st.columns(2)
            with c1:
                btn_type_tf = "primary" if st.session_state.ecuador_company == "True Flavor" else "secondary"
                if st.button("🍌 True Flavor", use_container_width=True, type=btn_type_tf):
                    st.session_state.ecuador_company = "True Flavor"
                    st.session_state.income = ECUADOR_COMPANIES["True Flavor"][st.session_state.ecuador_year].copy()
                    st.rerun()
            with c2:
                btn_type_sm = "primary" if st.session_state.ecuador_company == "Supermaxi" else "secondary"
                if st.button("🛒 Supermaxi", use_container_width=True, type=btn_type_sm):
                    st.session_state.ecuador_company = "Supermaxi"
                    st.session_state.income = ECUADOR_COMPANIES["Supermaxi"][st.session_state.ecuador_year].copy()
                    st.rerun()
            
            # Year toggle buttons
            st.markdown("### 📅 Select Year")
            y1, y2 = st.columns(2)
            with y1:
                if st.button("📅 2024", use_container_width=True, type="primary" if year_label == "2024" else "secondary"):
                    st.session_state.ecuador_year = 2024
                    st.session_state.income = company_data[2024].copy()
                    st.rerun()
            with y2:
                if st.button("📅 2023", use_container_width=True, type="primary" if year_label == "2023" else "secondary"):
                    st.session_state.ecuador_year = 2023
                    st.session_state.income = company_data[2023].copy()
                    st.rerun()

        st.divider()
        
        # KPI metrics with YoY
        sc, cur = cfg["scale"], cfg["currency"]
        m1, m2, m3, m4 = st.columns(4)

        def delta_str(key):
            if yoy and yoy.get(key, 0):
                prev, curr = yoy[key], income.get(key, 0)
                if prev:
                    return f"{((curr - prev)/abs(prev)*100):+.1f}% YoY"
            return None

        m1.metric("Revenue", fmt(income.get("Total Revenue",0), cur, sc), delta_str("Total Revenue"))
        m2.metric("Gross Profit", fmt(income.get("Gross Profit",0), cur, sc), delta_str("Gross Profit"))
        m3.metric("Operating Income", fmt(income.get("Operating Income",0), cur, sc), delta_str("Operating Income"))
        m4.metric("Net Income", fmt(income.get("Net Income",0), cur, sc), delta_str("Net Income"))

        st.divider()
        
        title = f"{company_label} · {year_label}"
        if country_mode == "EC":
            title = f"🇪🇨 {company_label} · {year_label}"
        
        fig = build_sankey(income, cur, sc, cfg["palette"], title, is_ecuador=(country_mode=="EC"))
        fig.update_layout(
            paper_bgcolor=th["bg"],
            font=dict(color=th["font"], size=cfg["font_sz"], family="Inter, Arial, sans-serif"),
            title_font_color=th["font"],
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with t3:
        if country_mode == "EC":
            st.subheader(f"🇪🇨 {full_name}")
            st.markdown(f"**RUC:** {ruc}")
            st.markdown(f"**Short Name:** {company_label}")
            st.divider()
            
            # Show both years comparison
            c1, c2 = st.columns(2)
            data_2023 = company_data[            data_2024 = company_data[2024]
            with c1:
                st.markdown("#### 2023")
                st.metric("Revenue", fmt(data_2023['Total Revenue'], "$", "M" if data_2023['Total Revenue'] > 1000000 else "K"))
                st.metric("Gross Profit", fmt(data_2023['Gross Profit'], "$", "M" if data_2023['Gross Profit'] > 1000000 else "K"))
                st.metric("Net Income", fmt(data_2023['Net Income'], "$", "M" if data_2023['Net Income'] > 1000000 else "K"))
            with c2:
                st.markdown("#### 2024")
                st.metric("Revenue", fmt(data_2024['Total Revenue'], "$", "M" if data_2024['Total Revenue'] > 1000000 else "K"))
                st.metric("Gross Profit", fmt(data_2024['Gross Profit'], "$", "M" if data_2024['Gross Profit'] > 1000000 else "K"))
                st.metric("Net Income", fmt(data_2024['Net Income'], "$", "M" if data_2024['Net Income'] > 1000000 else "K"))
            
            st.divider()
            # Calculate and show growth
            growth_rev = ((data_2024['Total Revenue'] - data_2023['Total Revenue']) / data_2023['Total Revenue'] * 100)
            growth_ni = ((data_2024['Net Income'] - data_2023['Net Income']) / data_2023['Net Income'] * 100)
            st.markdown(f"**Revenue Growth (2023→2024):** {growth_rev:+.1f}%")
            st.markdown(f"**Net Income Growth (2023→2024):** {growth_ni:+.1f}%")
            
        elif info:
            st.metric("Company", info.get("shortName", "—"))
            st.metric("Sector", info.get("sector", "—"))
            st.metric("Industry", info.get("industry", "—"))
            
    with t4:
        st.markdown(f"""
## How to Use

**🇺🇸 US Mode:** Enter a ticker (AAPL, NVDA, etc.) to fetch Yahoo Finance data with YoY comparison.

**🇪🇨 Ecuador Mode:** Select from available companies:
- **True Flavor S.A.** (RUC 2390028132001) - Exportadora agrícola
- **Supermaxi** (RUC 1790016919001) - Corporación Favorita C.A., retail

### Available Ecuador Companies
| Company | 2024 Revenue | 2023 Revenue | Growth |
|---------|-------------|--------------|--------|
| True Flavor | $1.04M | $842K | +23.5% |
| Supermaxi | $2,546M | $2,483M | +2.5% |

Use the **🏢 Select Company** buttons to switch between companies, and **📅 Select Year** buttons to compare years.
        """)
        
    st.divider()
    if country_mode == "EC":
        st.caption(f"🇪🇨 OpenSankey • {full_name} • RUC {ruc}")
    else:
        st.caption("🇺🇸 OpenSankey • Yahoo Finance data")

if __name__ == "__main__":
    main()
