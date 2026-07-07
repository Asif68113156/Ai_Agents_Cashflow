import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(page_title="Godrej Properties | Command Center", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Neumorphic base color is typically a soft gray matching the elements */
.stApp {
    background: #E0E5EC !important;
}

/* ── HIDE DEFAULTS ── */
header[data-testid="stHeader"], footer, #MainMenu,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #E0E5EC !important;
    border-right: none !important;
    box-shadow: 4px 0 15px rgba(163,177,198,0.4) !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebarNav"] { display:none !important; }


/* ── MAIN PADDING ── */
.main .block-container { padding: 1.5rem 2.5rem 4rem !important; max-width: 100% !important; }

/* NEUMORPHIC TABS */
[data-baseweb="tab-list"] {
    background: #E0E5EC !important;
    border-radius: 12px !important;
    padding: 6px !important;
    gap: 4px !important;
    border: none !important;
    box-shadow: inset 5px 5px 10px rgba(163,177,198,0.5), inset -5px -5px 10px rgba(255,255,255,0.8) !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: #475569 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease-in-out !important;
    border: none !important;
}
[aria-selected="true"] {
    background: #E0E5EC !important;
    color: #1E293B !important;
    box-shadow: 4px 4px 8px rgba(163,177,198,0.5), -4px -4px 8px rgba(255,255,255,0.8) !important;
}
[data-baseweb="tab-panel"] { padding-top: 2rem !important; }

/* ── DIVIDERS ── */
hr { 
    border-color: #D1D5DB !important; 
    margin: 2rem 0 !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.5);
}

/* ── DATAFRAMES (Soft UI) ── */
[data-testid="stDataFrame"] {
    border: none !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    background: #E0E5EC !important;
    box-shadow:  9px 9px 16px rgba(163,177,198,0.6), -9px -9px 16px rgba(255,255,255,0.8) !important;
}
[data-testid="stDataFrame"] * { color: #334155 !important; font-size: 0.82rem !important; }

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: #E0E5EC !important;
    border: none !important;
    border-radius: 12px !important;
    color: #1E293B !important;
    box-shadow: inset 4px 4px 8px rgba(163,177,198,0.5), inset -4px -4px 8px rgba(255,255,255,0.8) !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #E0E5EC !important;
    border: none !important;
    border-radius: 16px !important;
    box-shadow:  5px 5px 10px rgba(163,177,198,0.6), -5px -5px 10px rgba(255,255,255,0.8) !important;
}

/* ── DOWNLOAD BTN ── */
[data-testid="stDownloadButton"] button {
    background: #E0E5EC !important;
    color: #1D4ED8 !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 0.85rem !important; padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
    box-shadow:  4px 4px 8px rgba(163,177,198,0.6), -4px -4px 8px rgba(255,255,255,0.8) !important;
}
[data-testid="stDownloadButton"] button:hover {
    box-shadow:  2px 2px 4px rgba(163,177,198,0.6), -2px -2px 4px rgba(255,255,255,0.8) !important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════
C = {
    "bg":     "#E0E5EC",
    "card":   "#E0E5EC",
    "blue":   "#1D4ED8",
    "cyan":   "#0891B2",
    "emerald":"#059669",
    "amber":  "#D97706",
    "red":    "#DC2626",
    "violet": "#6D28D9",
    "text":   "#1E293B",
    "muted":  "#64748B",
    "border": "transparent",
}

PL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C["text"], size=11),
    margin=dict(l=12,r=12,t=36,b=12),
    xaxis=dict(gridcolor="rgba(163,177,198,0.2)", linecolor="rgba(163,177,198,0.4)",
               tickfont=dict(color=C["muted"],size=10)),
    yaxis=dict(gridcolor="rgba(163,177,198,0.2)", linecolor="rgba(163,177,198,0.4)",
               tickfont=dict(color=C["muted"],size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
    title_font=dict(size=14, color=C["text"], family="Outfit"),
    colorway=[C["blue"],C["emerald"],C["amber"],C["red"],C["violet"],C["cyan"]],
)

def apply_pl(fig, title="", h=300):
    fig.update_layout(**PL, height=h)
    if title: fig.update_layout(title_text=title)
    return fig

def card(content_html, padding="1.4rem 1.6rem", extra_style=""):
    st.markdown(f"""
    <div style="background:{C['card']};border:1px solid {C['border']};border-radius:16px;
    padding:{padding};backdrop-filter:blur(20px);{extra_style}">{content_html}</div>
    """, unsafe_allow_html=True)

def kpi(icon, label, value, sub="", color="#2563EB", delta=None, delta_good=True):
    delta_html = ""
    if delta is not None:
        da = "#059669" if delta_good else "#DC2626"
        ds = "▲" if delta_good else "▼"
        delta_html = f'<div style="font-size:0.75rem;color:{da};font-weight:600;margin-top:4px;">{ds} {delta}</div>'
    return f"""
    <div style="background:#E0E5EC;border:none;
    border-radius:18px;padding:1.4rem;
    box-shadow: 7px 7px 14px rgba(163,177,198,0.6), -7px -7px 14px rgba(255,255,255,0.8);
    position:relative;overflow:hidden;">
      <div style="width:40px;height:40px;position:absolute;top:15px;right:15px;font-size:1.5rem;
      background:#E0E5EC;border-radius:50%;display:flex;align-items:center;justify-content:center;
      box-shadow:inset 3px 3px 6px rgba(163,177,198,0.4), inset -3px -3px 6px rgba(255,255,255,0.6);">{icon}</div>
      <div style="font-family:'Outfit',sans-serif;font-size:0.75rem;font-weight:700;color:#64748B;letter-spacing:0.08em;
      text-transform:uppercase;margin-bottom:0.5rem;display:flex;align-items:center;gap:8px;">
        <div style="width:8px;height:20px;background:{color};border-radius:4px;box-shadow:inset 1px 1px 2px rgba(0,0,0,0.2);"></div>
        {label}
      </div>
      <div style="font-size:1.6rem;font-weight:800;color:#1E293B;font-family:'DM Mono',monospace;
      line-height:1.1;">{value}</div>
      {f'<div style="font-size:0.75rem;color:#64748B;margin-top:8px;">{sub}</div>' if sub else ""}
      {delta_html}
    </div>"""

def section(icon, title, sub=""):
    sub_html = f'<div style="color:#64748B;font-size:0.8rem;margin-top:2px;">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div style="margin:2.5rem 0 1.2rem;">
      <div style="display:flex;align-items:center;gap:0.75rem;">
        <div style="width:36px;height:36px;background:#EFF6FF;border-radius:10px;
        display:flex;align-items:center;justify-content:center;font-size:1rem;color:#1D4ED8;border:1px solid #BFDBFE;">{icon}</div>
        <div>
          <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;color:#0F172A;">{title}</div>
          {sub_html}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

def rag_pill(text, typ="red"):
    colors = {
        "red":    ("#ef4444","rgba(239,68,68,.12)"),
        "amber":  ("#f59e0b","rgba(245,158,11,.12)"),
        "green":  ("#10b981","rgba(16,185,129,.12)"),
        "blue":   ("#3b82f6","rgba(59,130,246,.12)"),
        "muted":  ("#64748b","rgba(100,116,139,.1)"),
    }
    c, bg = colors.get(typ, colors["muted"])
    return f'<span style="background:{bg};color:{c};border:1px solid {c}50;padding:2px 10px;border-radius:99px;font-size:.72rem;font-weight:700;">{text}</span>'

def hr():
    st.markdown(f"<hr style='border-color:{C['border']};margin:1.5rem 0'>", unsafe_allow_html=True)

@st.cache_data
def load_all():
    def sr(path, **kw):
        if not os.path.exists(path): return pd.DataFrame()
        try:
            d = pd.read_excel(path, **kw)
        except ValueError:
            # Sheet name not found in this workbook (e.g. older output file
            # generated before this sheet existed) — fail soft, not crash.
            return pd.DataFrame()
        for c in d.columns:
            if d[c].dtype == 'object': d[c] = d[c].astype(str)
        return d
    return {
        "sales":      sr("output/sales_vs_aop.xlsx"),
        "col":        sr("output/collections_vs_aop.xlsx"),
        "con":        sr("output/construction_vs_aop.xlsx"),
        "df":         sr("output/final_merged_dataset.xlsx"),
        "esc":        sr("output/escalation_report.xlsx", sheet_name="Escalation Summary"),
        "cf":         sr("output/cash_flow_report.xlsx",  sheet_name="Cash Flow Summary"),
        "cf_risks":   sr("output/cash_flow_report.xlsx",  sheet_name="Top Cash Flow Risks"),
        "cf_monthly": sr("output/cash_flow_report.xlsx",  sheet_name="Monthly AOP Targets"),
        "ap":         sr("output/action_plan.xlsx",        sheet_name="Action Plan"),
        "dq":         sr("output/data_quality_report.xlsx",sheet_name="All Issues"),
        "dq_sum":     sr("output/data_quality_report.xlsx",sheet_name="Summary by Category"),
        "scorecard":  sr("output/performance_report.xlsx", sheet_name="Executive Scorecard"),
        "product_mix":sr("output/performance_report.xlsx", sheet_name="Product Mix Analysis"),
        "ai_recs":    sr("output/performance_report.xlsx", sheet_name="AI Recommendations"),
        "decision":   sr("output/performance_report.xlsx", sheet_name="Decision Items"),
        "draft":      sr("output/draft_communications.xlsx"),
    }

D = load_all()
df = D["df"].copy()

import base64

logo_html = '🏢'
logo_base64 = ""
for ext in ["png", "jpg", "jpeg", "webp"]:
    if os.path.exists(f"logo.{ext}"):
        with open(f"logo.{ext}", "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        logo_html = f'<img src="data:image/{ext};base64,{logo_base64}" style="max-width:100%;max-height:100%;object-fit:contain;mix-blend-mode:multiply;"/>'
        break

# ════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:#E0E5EC;border:none;border-radius:24px;
padding:2rem 2.5rem;margin-bottom:2rem;position:relative;
box-shadow: 9px 9px 16px rgba(163,177,198,0.6), -9px -9px 16px rgba(255,255,255,0.8);">

  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1.5rem;">
    <div>
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
        <div style="background:#E0E5EC;border-radius:12px;
        width:140px;height:55px;display:flex;align-items:center;justify-content:center;
        border:none;overflow:hidden;padding:5px;
        box-shadow: inset 4px 4px 8px rgba(163,177,198,0.5), inset -4px -4px 8px rgba(255,255,255,0.8);">
        {logo_html}
        </div>
        <div>
          <div style="font-family:'Outfit',sans-serif;font-size:0.75rem;font-weight:800;letter-spacing:0.15em;
          color:#1D4ED8;text-transform:uppercase;">Godrej Properties Ltd.</div>
          <h1 style="font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:900;color:#1E293B;line-height:1.1;
          margin:0;letter-spacing:-0.02em;">Site Performance Command Center</h1>
        </div>
      </div>
      <p style="color:#64748B;font-size:0.9rem;max-width:550px;margin:0;line-height:1.5;">
        AI-powered month-end intelligence · Sales · Collections · Construction · Cash Flow · Risk
      </p>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.5rem;
    background:#E0E5EC;padding:1rem 1.25rem;border-radius:16px;
    box-shadow: inset 4px 4px 8px rgba(163,177,198,0.5), inset -4px -4px 8px rgba(255,255,255,0.8);">
      <div style="display:flex;align-items:center;gap:0.5rem;">
        <span style="font-family:'Outfit',sans-serif;font-size:0.75rem;font-weight:700;color:#059669;letter-spacing:0.05em;">LIVE — AI ENGINE ACTIVE</span>
      </div>
      <div style="font-size:0.75rem;font-weight:600;color:#64748B;">{len(D)} Active Outputs · Dynamic Rule Engine</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:#1E293B;margin-bottom:2rem;text-align:center;letter-spacing:0.05em;padding-top:1rem;">
    Godrej Command
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:0.8rem;font-weight:700;color:#64748B;margin-bottom:0.5rem;'>GLOBAL FILTER</div>", unsafe_allow_html=True)
    projects = ["All Projects"] + sorted(df["Project Name"].dropna().unique().tolist()) if "Project Name" in df.columns else ["All Projects"]
    sel_proj = st.selectbox("Select Project", projects, label_visibility="collapsed")
    
    st.markdown("<hr style='margin:2rem 0;border-color:#D1D5DB;box-shadow: 0 1px 0 rgba(255,255,255,0.5);'>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background:#E0E5EC;border-radius:16px;padding:1.5rem 1rem;
    box-shadow:inset 4px 4px 8px rgba(163,177,198,0.5), inset -4px -4px 8px rgba(255,255,255,0.8);
    display:flex;flex-direction:column;gap:0.75rem;text-align:center;">
        <div style="display:flex;align-items:center;justify-content:center;gap:8px;">
            <div style="width:8px;height:8px;background:#10B981;border-radius:50%;box-shadow:0 0 10px #10B981;"></div>
            <span style="font-family:'Outfit',sans-serif;font-size:0.8rem;font-weight:800;color:#059669;letter-spacing:0.05em;">SYSTEM ONLINE</span>
        </div>
        <div style="font-size:0.75rem;font-weight:600;color:#64748B;">{len(df)} Units Tracked</div>
        <div style="font-size:0.75rem;font-weight:600;color:#64748B;">Reporting YTD FY25</div>
    </div>
    """, unsafe_allow_html=True)

if sel_proj != "All Projects" and "Project Name" in df.columns:
    df = df[df["Project Name"] == sel_proj]

hr()

# ════════════════════════════════════════════════════
# KPI STRIP
# ════════════════════════════════════════════════════
outstanding = pd.to_numeric(df.get("Outstanding Amount", pd.Series([])), errors="coerce").sum() if "Outstanding Amount" in df.columns else 0
collected   = pd.to_numeric(df.get("Amount Collected",  pd.Series([])), errors="coerce").sum() if "Amount Collected"  in df.columns else 0
high_risk   = int((df.get("Risk Level", pd.Series([])) == "High").sum())
ceo_esc     = int((df.get("Escalation", pd.Series([])).astype(str).str.contains("CEO", na=False)).sum())
overdue30   = df[pd.to_numeric(df.get("Days Overdue",pd.Series([])),errors="coerce")>30] if "Days Overdue" in df.columns else pd.DataFrame()
recovery    = collected/(collected+outstanding)*100 if (collected+outstanding)>0 else 0
dq_issues   = len(D["dq"])

cols = st.columns(7)
kpis = [
    ("🏢","Total Units",       str(len(df)),                  f"{df['Project Name'].nunique() if 'Project Name' in df.columns else 1} projects",  C["blue"],   None,  True),
    ("💰","Outstanding",       f"₹{outstanding/1e6:.1f}M",   "Total receivable",                                          C["amber"],  None,  True),
    ("✅","Collected",         f"₹{collected/1e6:.1f}M",     f"{recovery:.0f}% recovery",                                 C["emerald"],None,  True),
    ("🚨","High Risk Units",   str(high_risk),                "Requiring action",                                          C["red"],    None,  False),
    ("⚡","CEO Escalations",   str(ceo_esc),                  "Cross-functional",                                          C["violet"], None,  False),
    ("⏰","Overdue >30d",      str(len(overdue30)),           f"₹{pd.to_numeric(overdue30.get('Outstanding Amount',pd.Series([])),errors='coerce').sum()/1e6:.1f}M at risk" if not overdue30.empty else "",  C["amber"],  None,  False),
    ("🔍","Data Quality",      str(dq_issues),               "Issues flagged",                                            "#64748b",   None,  False),
]

for c,(icon,lbl,val,sub,color,dlt,good) in zip(cols, kpis):
    c.markdown(kpi(icon,lbl,val,sub,color,dlt,good), unsafe_allow_html=True)

hr()

# ════════════════════════════════════════════════════
# MAIN TABS
# ════════════════════════════════════════════════════
T = st.tabs(["📊 Overview","💰 Cash Flow","🚨 Escalation","🏗 Operations","📋 Action Plan","🤖 AI Intelligence","🔍 Data Quality","⬇ Reports"])

# ── TAB 1: OVERVIEW ─────────────────────────────────
with T[0]:
    # Scorecard
    section("📊","Executive RAG Scorecard","Actual vs AOP — auto-rated Red / Amber / Green")
    sc = D["scorecard"]
    if not sc.empty:
        # Build custom scorecard table
        rows_html = ""
        for _, r in sc.iterrows():
            rag = str(r.get("RAG Status",""))
            t = "green" if "🟢" in rag else ("amber" if "🟡" in rag else "red")
            rows_html += f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
              <td style="padding:.7rem 1rem;font-weight:600;color:{C['text']};font-size:.83rem;">{r.get('KPI','')}</td>
              <td style="padding:.7rem 1rem;font-family:'DM Mono';color:{C['cyan']};font-size:.82rem;">{r.get('Actual','')}</td>
              <td style="padding:.7rem 1rem;font-family:'DM Mono';color:{C['muted']};font-size:.82rem;">{r.get('Target (AOP)','')}</td>
              <td style="padding:.7rem 1rem;font-weight:700;font-size:.85rem;{'color:#10b981' if t=='green' else 'color:#f59e0b' if t=='amber' else 'color:#ef4444'};">{r.get('Achievement %','')}</td>
              <td style="padding:.7rem 1rem;">{rag_pill(rag.replace('🟢','').replace('🟡','').replace('🔴','').strip(),t)}</td>
              <td style="padding:.7rem .8rem;color:{C['muted']};font-size:.78rem;">{r.get('Comment','')}</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:{C['card']};border:1px solid {C['border']};border-radius:16px;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:rgba(59,130,246,.08);border-bottom:1px solid rgba(59,130,246,.15);">
              {''.join(f'<th style="padding:.7rem 1rem;text-align:left;font-size:.7rem;font-weight:700;color:{C["muted"]};letter-spacing:.08em;text-transform:uppercase;">{h}</th>' for h in ['KPI','Actual','AOP Target','Achievement','Status','Comment'])}
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Run `python app.py` to generate scorecard.")

    hr()

    # Three gauges
    section("🎯","Performance vs AOP")
    s_pct = float(D["sales"]["Achievement %"].iloc[0])   if not D["sales"].empty   and "Achievement %" in D["sales"].columns   else 0
    c_pct = float(D["col"]["Achievement %"].iloc[0])     if not D["col"].empty     and "Achievement %" in D["col"].columns     else 0
    n_pct = float(D["con"]["Achievement %"].iloc[0])     if not D["con"].empty     and "Achievement %" in D["con"].columns     else 0

    g1,g2,g3 = st.columns(3)
    for gcol, label, pct, g_thr, a_thr, main_c in [
        (g1,"📈 Sales vs AOP",        s_pct, 80, 60, C["blue"]),
        (g2,"💰 Collections vs AOP",  c_pct, 85, 65, C["cyan"]),
        (g3,"🏗 Construction vs AOP", n_pct, 90, 70, C["emerald"]),
    ]:
        bar_c = C["emerald"] if pct >= g_thr else (C["amber"] if pct >= a_thr else C["red"])
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(pct, 1),
            number={"suffix":"%","font":{"size":32,"color":C["text"],"family":"DM Mono"}},
            gauge={
                "axis":{"range":[0,120],"tickfont":{"color":C["muted"],"size":9},"tickwidth":1,"tickcolor":C["muted"]},
                "bar":{"color":bar_c,"thickness":0.22},
                "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                "steps":[
                    {"range":[0,a_thr],   "color":"rgba(239,68,68,.12)"},
                    {"range":[a_thr,g_thr],"color":"rgba(245,158,11,.1)"},
                    {"range":[g_thr,120],  "color":"rgba(16,185,129,.08)"},
                ],
                "threshold":{"line":{"color":bar_c,"width":2},"thickness":.8,"value":pct},
            },
            title={"text":label,"font":{"color":C["muted"],"size":12,"family":"Inter"}},
        ))
        apply_pl(fig, h=220)
        with gcol: st.plotly_chart(fig, use_container_width=True)

    hr()

    # Monthly trend + Risk donut
    section("📈","Sales Intelligence")
    ta, tb = st.columns([3,2])
    with ta:
        if "Booking Date" in df.columns and "Total Agreement Amount" in df.columns:
            temp = df.copy()
            temp["Booking Date"] = pd.to_datetime(temp["Booking Date"], errors="coerce")
            temp = temp.dropna(subset=["Booking Date"])
            if not temp.empty:
                monthly = temp.groupby(temp["Booking Date"].dt.to_period("M"))["Total Agreement Amount"].sum().reset_index()
                monthly["Booking Date"] = monthly["Booking Date"].astype(str)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["Booking Date"], y=monthly["Total Agreement Amount"],
                    mode="lines+markers", name="Booking Value",
                    line=dict(color=C["blue"],width=2.5),
                    marker=dict(size=6,color=C["cyan"],line=dict(color=C["bg"],width=2)),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
                ))
                apply_pl(fig, "Monthly Booking Value (₹)", h=260)
                st.plotly_chart(fig, use_container_width=True)
    with tb:
        if "Risk Level" in df.columns:
            rdf = df["Risk Level"].value_counts().reset_index()
            rdf.columns = ["Risk","Count"]
            cm = {"Critical":C["red"],"High":"#f97316","Medium":C["amber"],"Low":C["emerald"]}
            clrs = [cm.get(r,C["muted"]) for r in rdf["Risk"]]
            fig = go.Figure(go.Pie(
                labels=rdf["Risk"], values=rdf["Count"], hole=.58,
                marker=dict(colors=clrs,line=dict(color=C["bg"],width=3)),
                textinfo="label+percent", textfont=dict(color=C["text"],size=10),
            ))
            apply_pl(fig, "Risk Distribution", h=260)
            fig.update_layout(annotations=[dict(text=f"<b>{rdf['Count'].sum()}</b><br><span style='font-size:10px'>Units</span>",
                                                x=.5,y=.5,font=dict(size=16,color=C["text"]),showarrow=False)])
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: CASH FLOW ────────────────────────────────
with T[1]:
    section("💰","Cash Flow Summary","Inflows · CoC Outflows · Net Cash Flow · Variance vs AOP")
    cf = D["cf"]

    def cfv(m):
        if cf.empty: return 0
        row = cf[cf["Metric"]==m]["Value (₹)"]
        try: return float(row.values[0])
        except: return 0

    inflow  = cfv("Collections Inflow (Actual)")
    coc_out = cfv("Total CoC Outflow")
    ncf     = cfv("Net Cash Flow (Actual)")
    ncf_tgt = cfv("Net Cash Flow Target (AOP — GPL Pre-BD NCF)")
    ncf_var = cfv("NCF Variance (Actual vs AOP)")
    od30    = cfv("Overdue Amount (>30 days)")
    col_tgt = cfv("Collections Target (AOP)")
    coc_tgt = cfv("CoC Target (AOP)")

    k1,k2,k3,k4 = st.columns(4)
    for col_c, data in zip([k1,k2,k3,k4],[
        ("📥","Collections Inflow",  f"₹{inflow/1e6:.2f}M",   f"Target ₹{col_tgt/1e6:.1f}M", C["emerald"]),
        ("📤","CoC Outflow",        f"₹{coc_out/1e6:.2f}M",  f"Target ₹{coc_tgt/1e6:.1f}M", C["amber"]),
        ("💵","Net Cash Flow",      f"₹{ncf/1e6:.2f}M",      f"Var ₹{ncf_var/1e6:.2f}M vs AOP", C["blue"] if ncf>0 else C["red"]),
        ("⏰","Overdue >30 Days",   f"₹{od30/1e6:.2f}M",     "Immediate recovery needed", C["red"]),
    ]):
        col_c.markdown(kpi(data[0],data[1],data[2],data[3],data[4]), unsafe_allow_html=True)

    hr()

    if not cf.empty:
        section("📋","Full Cash Flow Statement")
        rows_html=""
        for _,r in cf.iterrows():
            metric = str(r.get("Metric",""))
            val    = str(r.get("Value (₹)",""))
            rag    = str(r.get("RAG Status",""))
            if "———" in metric:
                rows_html += f'<tr><td colspan="3" style="padding:.3rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);"></td></tr>'
                continue
            t_c = C["emerald"] if "🟢" in rag else (C["red"] if "🔴" in rag else C["muted"])
            rows_html += f"""<tr style="border-bottom:1px solid rgba(255,255,255,.03);">
              <td style="padding:.55rem 1rem;color:{C['text']};font-size:.82rem;">{metric}</td>
              <td style="padding:.55rem 1rem;font-family:'DM Mono';color:{C['cyan']};font-size:.82rem;text-align:right;">{val}</td>
              <td style="padding:.55rem 1rem;text-align:center;font-size:.78rem;color:{t_c};">{rag}</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:{C['card']};border:1px solid {C['border']};border-radius:16px;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:rgba(59,130,246,.08);">
              {''.join(f'<th style="padding:.7rem 1rem;text-align:left;font-size:.7rem;font-weight:700;color:{C["muted"]};letter-spacing:.08em;text-transform:uppercase;">{h}</th>' for h in ['Metric','Value (₹)','Status'])}
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

    hr()
    if not D["cf_risks"].empty:
        section("🚨","Top Cash Flow Risks")
        for _,r in D["cf_risks"].iterrows():
            sev = str(r.get("Severity",""))
            if "—" in str(r.get("Risk Area","")): continue
            bg = "rgba(239,68,68,.07)" if "🔴" in sev else "rgba(245,158,11,.07)"
            bc = "rgba(239,68,68,.3)"  if "🔴" in sev else "rgba(245,158,11,.3)"
            lc = C["red"] if "🔴" in sev else C["amber"]
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-left:3px solid {lc};
            border-radius:12px;padding:.9rem 1.3rem;margin:.5rem 0;">
              <div style="font-weight:700;color:{C['text']};font-size:.85rem;margin-bottom:.3rem;">
                {sev} — {r.get('Risk Area','')}</div>
              <div style="color:{C['muted']};font-size:.8rem;margin-bottom:.4rem;">{r.get('Description','')}</div>
              <div style="color:{C['blue']};font-size:.78rem;">→ {r.get('Suggested Action','')}</div>
            </div>""", unsafe_allow_html=True)

# ── TAB 3: ESCALATION ───────────────────────────────
with T[2]:
    section("🚨","Escalation Registry","Red · Amber items with owner, action & due date")
    esc = D["esc"]
    if not esc.empty:
        red   = int((esc.get("Status","").astype(str).str.contains("Red",  na=False)).sum())
        amber = int((esc.get("Status","").astype(str).str.contains("Amber",na=False)).sum())
        e1,e2,e3,e4 = st.columns(4)
        e1.markdown(kpi("🔴","Red Items",    str(red),   "Immediate action",C["red"]),   unsafe_allow_html=True)
        e2.markdown(kpi("🟡","Amber Items",  str(amber), "Monitor closely",  C["amber"]), unsafe_allow_html=True)
        e3.markdown(kpi("📋","Total Flagged",str(len(esc)),"All escalated",  C["blue"]),  unsafe_allow_html=True)
        e4.markdown(kpi("✅","Clean Units",  str(len(df)-len(esc)),"No issues",C["emerald"]),unsafe_allow_html=True)
        hr()

        # Charts row
        ca, cb = st.columns(2)
        with ca:
            if "Escalation To" in esc.columns:
                edf = esc["Escalation To"].value_counts().reset_index()
                edf.columns=["Owner","Count"]
                fig=px.bar(edf.sort_values("Count"),x="Count",y="Owner",orientation="h",
                           text="Count",color="Count",
                           color_continuous_scale=[[0,C["blue"]],[0.5,C["amber"]],[1,C["red"]]])
                fig.update_traces(textfont=dict(color=C["text"]),textposition="outside")
                fig.update_coloraxes(showscale=False)
                apply_pl(fig,"Escalations by Owner")
                st.plotly_chart(fig,use_container_width=True)
        with cb:
            if "Risk Level" in esc.columns:
                rdf=esc["Risk Level"].value_counts().reset_index()
                rdf.columns=["Risk","Count"]
                cm={"Critical":C["red"],"High":"#f97316","Medium":C["amber"],"Low":C["emerald"]}
                clrs=[cm.get(r,C["muted"]) for r in rdf["Risk"]]
                fig=go.Figure(go.Pie(labels=rdf["Risk"],values=rdf["Count"],hole=.5,
                                     marker=dict(colors=clrs,line=dict(color=C["bg"],width=3)),
                                     textinfo="label+percent",textfont=dict(color=C["text"],size=10)))
                apply_pl(fig,"Risk Level Breakdown")
                st.plotly_chart(fig,use_container_width=True)

        hr()
        sf=st.multiselect("Filter",["🔴 Red","🟡 Amber"],default=["🔴 Red","🟡 Amber"],label_visibility="collapsed")
        ev=esc[esc["Status"].isin(sf)] if sf and "Status" in esc.columns else esc
        st.dataframe(ev, use_container_width=True, height=380)
    else:
        st.info("Run `python app.py` first.")

# ── TAB 4: OPERATIONS ───────────────────────────────
with T[3]:
    pt=st.tabs(["📈 Sales","💰 Collections","🏗 Construction","🔢 Product Mix","⚙️ Business Rules"])

    def ops_tab(tab, res, ac, tc, is_pct=False):
        with tab:
            if res.empty: st.info("No data"); return
            actual=float(res[ac].iloc[0]); target=float(res[tc].iloc[0])
            achiev=float(res["Achievement %"].iloc[0])
            fmt=(lambda v:f"{v:.2f}%") if is_pct else (lambda v:f"₹{v:,.0f}")
            gap = target-actual
            a1,a2,a3,a4=st.columns(4)
            a1.markdown(kpi("📊","Actual",fmt(actual),"",C["blue"]),unsafe_allow_html=True)
            a2.markdown(kpi("🎯","AOP Target",fmt(target),"",C["muted"]),unsafe_allow_html=True)
            a3.markdown(kpi("📈","Achievement",f"{achiev:.1f}%","",C["emerald"] if achiev>=85 else (C["amber"] if achiev>=65 else C["red"])),unsafe_allow_html=True)
            a4.markdown(kpi("↔️","Gap",fmt(gap),"vs Target",C["red"] if gap>0 else C["emerald"]),unsafe_allow_html=True)
            st.progress(min(achiev/100,1.0))
            fig=go.Figure()
            fig.add_trace(go.Bar(name="Actual",x=["Performance"],y=[actual],marker_color=C["blue"],width=.3))
            fig.add_trace(go.Bar(name="Target",x=["Performance"],y=[target],marker_color="rgba(100,116,139,.4)",
                                 marker_line_color=C["muted"],marker_line_width=1.5,width=.3))
            apply_pl(fig,"Actual vs AOP Target",h=220)
            fig.update_layout(barmode="group")
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(res,use_container_width=True)

    ops_tab(pt[0],D["sales"],   "Actual Booking Value","Target Booking Value")
    ops_tab(pt[1],D["col"],    "Actual Collection","Target Collection")
    ops_tab(pt[2],D["con"],    "Actual Progress %","Target Progress %",True)

    with pt[3]:
        section("🔢","Product Mix Analysis","1BHK · 2BHK · 3BHK actual vs AOP targets")
        pm=D["product_mix"]
        if not pm.empty: st.dataframe(pm,use_container_width=True,height=300)
        else: st.info("Product mix data unavailable — check `Type` column in Sales input")

    with pt[4]:
        section("⚙️","Business Rule Violations")
        if "Business Rule" in df.columns:
            all_r=[]
            for s in df["Business Rule"].dropna():
                for r in str(s).split(","):
                    r=r.strip()
                    if r and r!="Healthy": all_r.append(r)
            if all_r:
                rdf=pd.Series(all_r).value_counts().head(10).reset_index()
                rdf.columns=["Rule","Count"]
                fig=px.bar(rdf.sort_values("Count"),x="Count",y="Rule",orientation="h",text="Count",
                           color="Count",color_continuous_scale=[[0,C["blue"]],[1,C["red"]]])
                fig.update_coloraxes(showscale=False)
                fig.update_traces(textfont=dict(color=C["text"]),textposition="outside")
                apply_pl(fig,"Top Business Rule Violations",h=380)
                st.plotly_chart(fig,use_container_width=True)

# ── TAB 5: ACTION PLAN ──────────────────────────────
with T[4]:
    section("📋","Owner-wise Action Plan","Prioritised actions per department with due dates")
    ap=D["ap"]
    if not ap.empty:
        crit=ap[ap.get("Priority",pd.Series([])).astype(str).str.contains("Critical",na=False)] if "Priority" in ap.columns else pd.DataFrame()
        high=ap[ap.get("Priority",pd.Series([])).astype(str).str.contains("High",na=False)]     if "Priority" in ap.columns else pd.DataFrame()
        p1,p2,p3=st.columns(3)
        p1.markdown(kpi("🔴","Critical Actions",str(len(crit)),"Immediate",C["red"]),unsafe_allow_html=True)
        p2.markdown(kpi("🟡","High Priority",   str(len(high)),"This week", C["amber"]),unsafe_allow_html=True)
        p3.markdown(kpi("📋","Total Actions",   str(len(ap)),  "All depts", C["blue"]),unsafe_allow_html=True)
        hr()

        # Cards for critical
        for _,r in crit.head(5).iterrows():
            dept=str(r.get("Department",""))
            st.markdown(f"""
            <div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);
            border-left:3px solid {C['red']};border-radius:12px;padding:1rem 1.4rem;margin:.5rem 0;
            display:flex;gap:1.2rem;align-items:flex-start;">
              <div style="background:rgba(239,68,68,.15);color:{C['red']};padding:4px 10px;
              border-radius:6px;font-size:.7rem;font-weight:700;white-space:nowrap;
              border:1px solid rgba(239,68,68,.3);">{dept}</div>
              <div style="flex:1;">
                <div style="color:{C['text']};font-size:.84rem;margin-bottom:.3rem;">{r.get('Action','')}</div>
                <div style="display:flex;gap:1rem;flex-wrap:wrap;">
                  <span style="color:{C['muted']};font-size:.75rem;">👤 {r.get('Owner','')}</span>
                  <span style="color:{C['muted']};font-size:.75rem;">📅 {r.get('Due Date','')}</span>
                  <span style="color:{C['blue']};font-size:.75rem;">📌 {r.get('Metric Impacted','')}</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        hr()
        dept_list = sorted(ap["Department"].dropna().unique()) if "Department" in ap.columns else []
        df_sel = st.multiselect("Department Filter", dept_list, default=dept_list, label_visibility="collapsed")
        ap_v = ap[ap["Department"].isin(df_sel)] if df_sel and "Department" in ap.columns else ap
        st.dataframe(ap_v, use_container_width=True, height=360)

        hr()
        section("✉️","Draft Communications","Ready-to-send stakeholder messages")
        for _,r in D["draft"].iterrows():
            with st.expander(f"📧 To: {r.get('To','')}  |  {r.get('Subject','')}"):
                st.code(r.get("Draft",""),language=None)
    else:
        st.info("Run `python app.py` first.")

# ── TAB 6: AI INTELLIGENCE ──────────────────────────
with T[5]:
    section("🤖","AI Management Summary","Rule-based synthesis of all computed metrics")
    try:
        with open("output/ai_summary.txt",encoding="utf-8") as f: txt=f.read()
        lines=txt.strip().splitlines(); fmtd=[]
        for ln in lines:
            ln=ln.strip()
            if not ln: fmtd.append("<br>")
            elif "✅" in ln: fmtd.append(f'<div style="color:{C["emerald"]};margin:3px 0;font-size:.85rem;">✅ {ln.replace("✅","").strip()}</div>')
            elif "⚠" in ln:  fmtd.append(f'<div style="color:{C["amber"]};margin:3px 0;font-size:.85rem;">⚠️ {ln.replace("⚠","").strip()}</div>')
            elif ln.startswith("-"): fmtd.append(f'<div style="color:{C["muted"]};margin:2px 0 2px 1rem;font-size:.83rem;">› {ln[1:].strip()}</div>')
            elif "====" in ln or "----" in ln: fmtd.append(f'<div style="color:{C["blue"]};font-weight:700;font-size:.75rem;letter-spacing:.12em;margin:12px 0 5px;text-transform:uppercase;">{ln.replace("=","").replace("-","").strip()}</div>')
            else: fmtd.append(f'<div style="color:#334155;margin:2px 0;font-size:.84rem;">{ln}</div>')
        card(f"<div style='line-height:1.8;'>{''.join(fmtd)}</div>")
    except: st.warning("Run `python app.py` first.")

    hr()
    section("🎯","AI Recommendations","Priority actions with expected business impact")
    recs=D["ai_recs"]
    if not recs.empty:
        for _,r in recs.iterrows():
            pri=str(r.get("Priority",""))
            is_crit="1" in pri or "2" in pri
            bg=f"rgba(239,68,68,.06)" if is_crit else "rgba(245,158,11,.05)"
            bc=f"rgba(239,68,68,.2)"  if is_crit else "rgba(245,158,11,.18)"
            lc=C["red"] if is_crit else C["amber"]
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-left:3px solid {lc};
            border-radius:12px;padding:1rem 1.4rem;margin:.4rem 0;">
              <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;margin-bottom:.4rem;">
                <span style="font-weight:700;color:{C['text']};font-size:.85rem;">{pri} — {r.get('Area','')}</span>
                <span style="color:{C['muted']};font-size:.75rem;">Owner: {r.get('Owner','')}</span>
              </div>
              <div style="color:#334155;font-size:.83rem;margin-bottom:.3rem;">{r.get('Recommendation','')}</div>
              <div style="color:{C['blue']};font-size:.76rem;">Impact: {r.get('Expected Impact','')}</div>
            </div>""", unsafe_allow_html=True)

    hr()
    section("📌","AOP Decision Items")
    dec=D["decision"]
    if not dec.empty: st.dataframe(dec,use_container_width=True,height=280)
    else: st.info("No decision items found.")

# ── TAB 7: DATA QUALITY ─────────────────────────────
with T[6]:
    section("🔍","Data Quality Report","⚠️ Review before presenting to leadership")
    dq=D["dq"]
    if not dq.empty:
        high_dq=dq[dq.get("Severity","").astype(str).str.contains("High|🔴",na=False)] if "Severity" in dq.columns else pd.DataFrame()
        d1,d2,d3=st.columns(3)
        d1.markdown(kpi("🔴","High Severity", str(len(high_dq)), "Require action",  C["red"]),    unsafe_allow_html=True)
        d2.markdown(kpi("📋","Total Issues",  str(len(dq)),      "All categories",  C["amber"]),  unsafe_allow_html=True)
        d3.markdown(kpi("🗂","Categories",    str(dq["Category"].nunique() if "Category" in dq.columns else 0),"Issue types",C["blue"]),unsafe_allow_html=True)

        st.markdown(f"""<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);
        border-left:3px solid {C['amber']};border-radius:12px;padding:.85rem 1.2rem;margin:.8rem 0;
        font-size:.83rem;color:{C['amber']};font-weight:600;">
        ⚠️ Issues below require human review and correction before the final leadership presentation.
        </div>""", unsafe_allow_html=True)

        hr()
        if not D["dq_sum"].empty:
            fig=px.bar(D["dq_sum"],x="Count",y="Category",orientation="h",text="Count",
                       color="Count",color_continuous_scale=[[0,C["blue"]],[1,C["red"]]])
            fig.update_coloraxes(showscale=False)
            fig.update_traces(textfont=dict(color=C["text"]),textposition="outside")
            apply_pl(fig,"Issues by Category",h=260)
            st.plotly_chart(fig,use_container_width=True)
        hr()
        cats=sorted(dq["Category"].dropna().unique()) if "Category" in dq.columns else []
        cf2=st.multiselect("Category Filter",cats,default=cats,label_visibility="collapsed")
        dqv=dq[dq["Category"].isin(cf2)] if cf2 and "Category" in dq.columns else dq
        st.dataframe(dqv,use_container_width=True,height=400)
    else:
        card(f'<div style="color:{C["emerald"]};font-weight:600;font-size:.95rem;text-align:center;padding:1rem 0;">✅ All data quality checks passed — no issues detected.</div>')

# ── TAB 8: REPORTS ──────────────────────────────────
with T[7]:
    files=[
        ("output/performance_report.xlsx","📊 Month-End Leadership Report","CBE-style report · Scorecard · Escalation · AI Recs"),
        ("output/cash_flow_report.xlsx",  "💰 Cash Flow Report",           "Inflows · CoC · NCF · Variance vs AOP · Top Risks"),
        ("output/escalation_report.xlsx", "🚨 Escalation Summary",         "Red/Amber table · Owner · Action · Due Date"),
        ("output/action_plan.xlsx",       "📋 Owner-wise Action Plan",      "Sales · Collections · Construction · Finance · Leadership"),
        ("output/draft_communications.xlsx","✉️ Draft Communications",      "Stakeholder email drafts (table)"),
        ("output/draft_communications.txt","✉️ Draft Emails (Text)",        "Copy-paste ready full email text"),
        ("output/data_quality_report.xlsx","🔍 Data Quality Report",        "Mismatches · Missing Owners · Conflicts [Human Review]"),
        ("output/final_merged_dataset.xlsx","🗄 Master Dataset",            "All input files linked — working master dataset"),
        ("output/business_rule_report.xlsx","⚙️ Business Rule Report",     "Deterministic rules applied per unit"),
        ("output/risk_report.xlsx",        "⚠️ Risk Report",               "Critical/High/Medium/Low per unit"),
        ("output/sales_vs_aop.xlsx",       "📈 Sales vs AOP",              "Sales achievement vs annual operating plan"),
        ("output/collections_vs_aop.xlsx", "💰 Collections vs AOP",        "Collections achievement vs AOP"),
        ("output/construction_vs_aop.xlsx","🏗 Construction vs AOP",       "Construction progress vs planned milestones"),
        ("output/ai_summary.txt",          "🤖 AI Summary",                "AI-generated executive text summary"),
    ]
    found_count = sum(1 for path,_,_ in files if os.path.exists(path))
    section("⬇","Report Download Center", f"{found_count} of {len(files)} outputs ready — generated from your input files")
    for path,label,desc in files:
        fa,fb,fc=st.columns([2,4,1])
        with fa: st.markdown(f"<div style='color:{C['text']};font-weight:600;font-size:.84rem;padding:.45rem 0;'>{label}</div>",unsafe_allow_html=True)
        with fb: st.markdown(f"<div style='color:{C['muted']};font-size:.78rem;padding:.45rem 0;'>{desc}</div>",unsafe_allow_html=True)
        with fc:
            if os.path.exists(path):
                with open(path,"rb") as f:
                    st.download_button("⬇",f,file_name=os.path.basename(path),key=path)
            else:
                st.markdown(f"<span style='color:{C['red']};font-size:.75rem;'>Not found</span>",unsafe_allow_html=True)
        st.markdown(f"<hr style='border-color:{C['border']};margin:.25rem 0'>",unsafe_allow_html=True)

# ── FOOTER ──────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:3rem;padding:1.4rem 2rem;background:transparent;
border:none;border-radius:14px;
display:flex;justify-content:center;align-items:center;text-align:center;">
  <div>
    <div style="font-weight:700;color:{C['text']};font-size:.88rem;">🏢 Godrej Properties — AI Site Performance Command Center</div>
    <div style="color:{C['muted']};font-size:.73rem;margin-top:3px;">
      Python · Pandas · Streamlit · Plotly · AI Metrics Engine
    </div>
  </div>
</div>
<div style="height:2rem;"></div>
""",unsafe_allow_html=True)