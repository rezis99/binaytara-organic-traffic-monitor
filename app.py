"""
Binaytara SEO Monitor — Main Application
Interactive GA4 + GSC organic-traffic monitoring dashboard.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from config import (
    DATE_PRESETS, DATA_LAG_DAYS, DEFAULT_PRESET, BRAND_NAVY, BRAND_GREEN, BRAND_RED,
    SECTIONS, DEFAULT_SECTION, GRANULARITY_OPTIONS, SMOOTHING_OPTIONS,
)
from utils import mtd_ranges

st.set_page_config(page_title="Binaytara SEO Monitor", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
    .stMetric {{
        background: {BRAND_NAVY}08; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid {BRAND_NAVY};
    }}
    .stTabs [data-baseweb="tab"] {{ padding: 8px 18px; font-weight: 500; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.5rem; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<h2 style="color:{BRAND_NAVY};margin-bottom:0;">📊 Binaytara</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#666;font-size:13px;margin-top:0;">SEO Monitor</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**📅 Date range**")
    preset = st.selectbox("Period", list(DATE_PRESETS.keys()),
                          index=list(DATE_PRESETS.keys()).index(DEFAULT_PRESET))
    today = date.today()
    safe_end = today - timedelta(days=DATA_LAG_DAYS)

    if preset == "Custom":
        a, b = st.columns(2)
        with a: curr_start = st.date_input("Current start", value=safe_end - timedelta(days=27), max_value=safe_end)
        with b: curr_end = st.date_input("Current end", value=safe_end, max_value=safe_end)
        st.markdown("<small style='color:#666;'>compared with</small>", unsafe_allow_html=True)
        c, d = st.columns(2)
        with c:
            prev_start = st.date_input("Compare start",
                                       value=curr_start - timedelta(days=(curr_end - curr_start).days + 1),
                                       max_value=safe_end)
        with d: prev_end = st.date_input("Compare end", value=curr_start - timedelta(days=1), max_value=safe_end)
        if curr_start > curr_end: st.error("Current start must be before end.")
        if prev_start > prev_end: st.error("Compare start must be before end.")
    else:
        days = DATE_PRESETS[preset]
        curr_end = safe_end
        curr_start = safe_end - timedelta(days=days - 1)
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        st.caption(f"Current: {curr_start} to {curr_end}")
        st.caption(f"Compare: {prev_start} to {prev_end}")

    dates = {"curr_start": str(curr_start), "curr_end": str(curr_end),
             "prev_start": str(prev_start), "prev_end": str(prev_end)}
    show_comparison = st.checkbox("Compare with previous period", value=True)
    dates["show_comparison"] = show_comparison
    st.divider()

    st.markdown("**📈 Chart controls**")
    granularity = st.radio("Granularity", GRANULARITY_OPTIONS, index=0, horizontal=True)
    smoothing = st.selectbox("Smoothing (daily only)", SMOOTHING_OPTIONS, index=0)
    hero_split = st.checkbox("Split hero by section", value=False)
    hero_show_impr = st.checkbox("Show impressions on hero", value=False)
    controls = {"granularity": granularity, "smoothing": smoothing,
                "hero_split_section": hero_split, "hero_show_impressions": hero_show_impr}
    st.divider()

    # Traffic type: checkboxes so both can be on simultaneously
    st.markdown("**📊 Traffic type**")
    show_organic = st.checkbox("Organic Traffic", value=True)
    show_total = st.checkbox("Total Traffic", value=False)
    if not show_organic and not show_total:
        show_organic = True  # at least one must be on
    controls["show_organic"] = show_organic
    controls["show_total"] = show_total
    # For tabs that need a single flag, organic takes priority when both are on
    organic_only = show_organic and not show_total
    st.divider()

    st.markdown("**🏷 Sections**")
    section_names = ["All Sections"] + [s["name"] for s in SECTIONS] + [DEFAULT_SECTION]
    section_filter = st.multiselect("Study these sections", section_names, default=["All Sections"])
    if not section_filter:
        section_filter = ["All Sections"]
    st.divider()

    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption(f"Data as of: {safe_end} (recent partial days excluded)")

# ── Month-to-date pace card ───────────────────────────────────────
mtd = mtd_ranges(DATA_LAG_DAYS)

with st.expander(f"📅 **Month-to-date: {mtd['month_name']}** — day {mtd['safe_day']} of {mtd['days_in_month']} "
                 f"({mtd['days_remaining']} days remaining)", expanded=True):
  try:
    from data.ga4 import fetch_daily_traffic
    from data.gsc import fetch_gsc_daily_totals

    mtd_ga = fetch_daily_traffic(mtd["this_start"], mtd["this_end"], True)
    mtd_gsc = fetch_gsc_daily_totals(mtd["this_start"], mtd["this_end"])
    prev_ga = fetch_daily_traffic(mtd["last_mtd_start"], mtd["last_mtd_end"], True)
    prev_gsc = fetch_gsc_daily_totals(mtd["last_mtd_start"], mtd["last_mtd_end"])
    full_ga = fetch_daily_traffic(mtd["last_full_start"], mtd["last_full_end"], True)
    full_gsc = fetch_gsc_daily_totals(mtd["last_full_start"], mtd["last_full_end"])

    def _s(df, col):
        return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum()) if not df.empty and col in df.columns else 0

    this_users = _s(mtd_ga, "totalUsers")
    this_clicks = _s(mtd_gsc, "clicks")
    prev_users = _s(prev_ga, "totalUsers")
    prev_clicks = _s(prev_gsc, "clicks")
    full_users = _s(full_ga, "totalUsers")
    full_clicks = _s(full_gsc, "clicks")

    proj_users = int(this_users / mtd["days_elapsed"] * mtd["days_in_month"]) if mtd["days_elapsed"] else 0
    proj_clicks = int(this_clicks / mtd["days_elapsed"] * mtd["days_in_month"]) if mtd["days_elapsed"] else 0

    def _pct(cur, prev):
        if not prev: return ""
        d = (cur - prev) / prev * 100
        color = BRAND_GREEN if d >= 0 else BRAND_RED
        return f' <span style="color:{color};font-weight:600;">({d:+.0f}%)</span>'

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"**GA4 organic users**")
        st.markdown(f"This month so far: **{this_users:,}**{_pct(this_users, prev_users)}", unsafe_allow_html=True)
        st.markdown(f"{mtd['prev_month_name']} through day {mtd['safe_day']}: {prev_users:,}", unsafe_allow_html=True)
    with m2:
        st.markdown(f"**GSC clicks (Google)**")
        st.markdown(f"This month so far: **{this_clicks:,}**{_pct(this_clicks, prev_clicks)}", unsafe_allow_html=True)
        st.markdown(f"{mtd['prev_month_name']} through day {mtd['safe_day']}: {prev_clicks:,}", unsafe_allow_html=True)
    with m3:
        st.markdown(f"**Projected month-end**")
        st.markdown(f"Users: **{proj_users:,}**{_pct(proj_users, full_users)}", unsafe_allow_html=True)
        st.markdown(f"Clicks: **{proj_clicks:,}**{_pct(proj_clicks, full_clicks)}", unsafe_allow_html=True)
    with m4:
        st.markdown(f"**{mtd['prev_month_name']} actual**")
        st.markdown(f"Users: {full_users:,}")
        st.markdown(f"Clicks: {full_clicks:,}")

    st.caption(
        f"Pace = (total so far ÷ {mtd['days_elapsed']} days elapsed) × {mtd['days_in_month']} days in month. "
        f"GA4 organic users cover all search engines; GSC clicks are Google Search only. "
        f"The last {DATA_LAG_DAYS} days of data are excluded because GA4 and GSC need "
        f"2 to 3 days to finalize, so the most recent included day is {mtd['this_end']}."
    )
  except Exception as mtd_err:
    st.warning(f"Could not load month-to-date data: {mtd_err}. "
               "Click 'Refresh data' in the sidebar to retry. If this keeps happening, "
               "check that the service account credentials are valid.")

# ── Header ────────────────────────────────────────────────────────
scope = "All sections" if "All Sections" in section_filter else " + ".join(section_filter)
traffic_label = []
if show_organic: traffic_label.append("Organic")
if show_total: traffic_label.append("Total")
state = (f'{" + ".join(traffic_label)} · {granularity} · '
         f'{dates["curr_start"]} to {dates["curr_end"]}'
         f'{" vs " + dates["prev_start"] + " to " + dates["prev_end"] if show_comparison else ""} · {scope}')
st.markdown(f'<h1 style="color:{BRAND_NAVY};font-size:1.7rem;margin-bottom:2px;">Binaytara SEO Monitor</h1>',
            unsafe_allow_html=True)
st.markdown(f'<p style="color:#666;font-size:13px;margin-top:0;">{state}</p>', unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", "🔎 Search Performance", "📄 Pages",
    "🧭 Keyword Deep Dive", "💡 Opportunities",
])

try:
    with tab1:
        from tabs.overview import render as r1
        r1(dates, organic_only, section_filter, controls)
    with tab2:
        from tabs.search_performance import render as r2
        r2(dates, organic_only, section_filter, controls)
    with tab3:
        from tabs.pages import render as r3
        r3(dates, organic_only, section_filter)
    with tab4:
        from tabs.keywords import render as r4
        r4(dates, organic_only, section_filter)
    with tab5:
        from tabs.opportunities import render as r5
        r5(dates, organic_only, section_filter)
except Exception as e:
    st.error(f"An error occurred: {e}")
    st.caption("Check that the service account has Viewer on GA4 (property 468739074) and "
               "Full access on GSC (sc-domain:binaytara.org). If this is a transient SSL error, "
               "click 'Refresh data' in the sidebar to retry.")
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
