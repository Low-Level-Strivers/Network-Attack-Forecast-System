"""
Executive Light Theme & Semantic Risk System for Predictive Cyber Defence Dashboard.
Color System:
- Normal / Clean State: Green (Text: #2B8A3E, Bg: #E6FCF5, Border: #63E6BE)
- Medium Risk State: Orange / Yellow (Text: #D9480F, Bg: #FFF9DB, Border: #FFE066)
- High Risk State: Red (Text: #C92A2A, Bg: #FFF5F5, Border: #FFA8A8)
- Monochrome Foundation: Background #FFFFFF, Dark Text #111111, Grey Accents #E9ECEF
"""

import textwrap
import streamlit as st
import plotly.graph_objects as go


def safe_html(html_str: str):
    """
    Renders raw HTML safely without Streamlit markdown converting indented
    lines to preformatted code blocks.
    """
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


LIGHT_THEME_CSS = """
<style>
    /* 1. Global Reset & High-Contrast Typography */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #111111 !important;
    }

    .stApp {
        background-color: #FFFFFF !important;
    }

    /* 2. Fix Header Bar Glitch (Eliminate black top bar) */
    header[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        border-bottom: 1px solid #E9ECEF !important;
    }

    /* 3. Sidebar Styling with Strict Label Visibility */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #DEE2E6 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #111111 !important;
    }

    /* Fix Radio Button Labels Visibility in Sidebar */
    div[role="radiogroup"] label,
    div[role="radiogroup"] label *,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label *,
    div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] span {
        color: #111111 !important;
        opacity: 1 !important;
        visibility: visible !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    div[role="radiogroup"] label {
        padding: 6px 10px !important;
        border-radius: 6px !important;
        transition: background-color 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
        margin-bottom: 2px !important;
    }

    div[role="radiogroup"] label:hover {
        background-color: #E9ECEF !important;
    }

    div[role="radiogroup"] label[aria-checked="true"] {
        background-color: #E9ECEF !important;
        font-weight: 700 !important;
    }

    /* Fix Slider Labels & Values Visibility */
    div[data-testid="stSlider"] label,
    div[data-testid="stSlider"] label *,
    div[data-testid="stSlider"] label p,
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
        color: #111111 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    div[data-testid="stSlider"] [data-baseweb="slider"] *,
    div[data-testid="stSlider"] div[data-testid="stTickBar"] * {
        color: #495057 !important;
        font-size: 12px !important;
    }

    /* Fix Selectbox Labels & Dropdown Text */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label *,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #111111 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        opacity: 1 !important;
    }

    /* File Uploader Light Styling */
    div[data-testid="stFileUploader"] label,
    div[data-testid="stFileUploader"] label * {
        color: #111111 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #FFFFFF !important;
        border: 1px dashed #CED4DA !important;
        border-radius: 6px !important;
    }
    div[data-testid="stFileUploader"] section * {
        color: #495057 !important;
    }

    /* Sidebar Badge Overrides */
    section[data-testid="stSidebar"] .badge-clean {
        color: #2B8A3E !important;
    }
    section[data-testid="stSidebar"] .badge-medium {
        color: #D9480F !important;
    }
    section[data-testid="stSidebar"] .badge-high {
        color: #C92A2A !important;
    }

    /* 4. Headings */
    h1, h2, h3, h4 {
        color: #111111 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    /* 5. Semantic Metric Cards */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 16px 20px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #DEE2E6;
        margin-bottom: 12px;
    }

    .metric-card-green {
        background-color: #E6FCF5;
        border: 1.5px solid #63E6BE;
    }
    .metric-card-green .card-val { color: #2B8A3E !important; }
    .metric-card-green .card-label { color: #087F5B !important; }
    .metric-card-green .card-sub { color: #20C997 !important; }

    .metric-card-orange {
        background-color: #FFF9DB;
        border: 1.5px solid #FFE066;
    }
    .metric-card-orange .card-val { color: #D9480F !important; }
    .metric-card-orange .card-label { color: #E8590C !important; }
    .metric-card-orange .card-sub { color: #F76707 !important; }

    .metric-card-red {
        background-color: #FFF5F5;
        border: 1.5px solid #FFA8A8;
    }
    .metric-card-red .card-val { color: #C92A2A !important; }
    .metric-card-red .card-label { color: #E03131 !important; }
    .metric-card-red .card-sub { color: #FA5252 !important; }

    .metric-card-neutral {
        background-color: #F8F9FA;
        border: 1px solid #CED4DA;
    }
    .metric-card-neutral .card-val { color: #111111 !important; }
    .metric-card-neutral .card-label { color: #495057 !important; }
    .metric-card-neutral .card-sub { color: #6C757D !important; }

    .card-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }

    .card-val {
        font-size: 28px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 4px;
    }

    .card-sub {
        font-size: 12px;
        font-weight: 500;
    }

    /* 6. Semantic Status Badges */
    .badge-clean {
        display: inline-block;
        background-color: #E6FCF5;
        color: #2B8A3E;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #63E6BE;
    }

    .badge-medium {
        display: inline-block;
        background-color: #FFF9DB;
        color: #D9480F;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #FFE066;
    }

    .badge-high {
        display: inline-block;
        background-color: #FFF5F5;
        color: #C92A2A;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #FFA8A8;
    }

    /* 7. Semantic Alert Banners */
    .alert-banner-red {
        background-color: #FFF5F5;
        border-left: 5px solid #C92A2A;
        border-top: 1px solid #FFA8A8;
        border-right: 1px solid #FFA8A8;
        border-bottom: 1px solid #FFA8A8;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 18px;
    }
    .alert-banner-red .title { color: #C92A2A; font-weight: 700; font-size: 15px; }
    .alert-banner-red .desc { color: #495057; font-size: 13px; margin-top: 4px; }

    .alert-banner-orange {
        background-color: #FFF9DB;
        border-left: 5px solid #D9480F;
        border-top: 1px solid #FFE066;
        border-right: 1px solid #FFE066;
        border-bottom: 1px solid #FFE066;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 18px;
    }
    .alert-banner-orange .title { color: #D9480F; font-weight: 700; font-size: 15px; }
    .alert-banner-orange .desc { color: #495057; font-size: 13px; margin-top: 4px; }

    .alert-banner-green {
        background-color: #E6FCF5;
        border-left: 5px solid #2B8A3E;
        border-top: 1px solid #63E6BE;
        border-right: 1px solid #63E6BE;
        border-bottom: 1px solid #63E6BE;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 18px;
    }
    .alert-banner-green .title { color: #2B8A3E; font-weight: 700; font-size: 15px; }
    .alert-banner-green .desc { color: #495057; font-size: 13px; margin-top: 4px; }

    /* Clean Dividers */
    hr {
        border: 0;
        border-top: 1px solid #DEE2E6 !important;
        margin: 20px 0 !important;
    }
</style>
"""


def apply_light_theme():
    """Injects high-contrast executive light styling."""
    safe_html(LIGHT_THEME_CSS)


def render_semantic_card(label: str, value: str, subtext: str = "", risk_score: float = None):
    """
    Renders a clean card with strict semantic risk coloring:
    - Red: High Risk (>= 50% or >= 0.50)
    - Yellow/Orange: Medium Risk (20% - 50% or 0.20 - 0.50)
    - Green: Normal/Clean (< 20% or < 0.20)
    """
    if risk_score is not None:
        val_pct = risk_score * 100.0 if risk_score <= 1.0 else risk_score
        if val_pct >= 50.0:
            color_class = "metric-card-red"
        elif val_pct >= 20.0:
            color_class = "metric-card-orange"
        else:
            color_class = "metric-card-green"
    else:
        color_class = "metric-card-neutral"

    html = f"""
    <div class="metric-card {color_class}">
        <div>
            <div class="card-label">{label}</div>
            <div class="card-val">{value}</div>
        </div>
        <div class="card-sub">{subtext}</div>
    </div>
    """
    safe_html(html)


def render_semantic_alert(risk_pct: float, lead_time_min: int, stage_name: str):
    """
    Renders an alert banner based on risk severity:
    - Red: High Risk (>= 50%)
    - Yellow/Orange: Medium Risk (20% - 50%)
    - Green: Normal (< 20%)
    """
    if risk_pct >= 50.0:
        html = f"""
        <div class="alert-banner-red">
            <div class="title">CRITICAL EARLY WARNING: High Attack Risk Projected</div>
            <div class="desc">
                World Model forecast indicates risk escalating to <strong>{risk_pct:.1f}%</strong> ({stage_name})
                within <strong>+{lead_time_min} minutes</strong>. Urgent: Trigger automated perimeter ACL blocklist.
            </div>
        </div>
        """
    elif risk_pct >= 20.0:
        html = f"""
        <div class="alert-banner-orange">
            <div class="title">ELEVATED THREAT ADVISORY: Medium Risk Activity Detected</div>
            <div class="desc">
                Forecasted risk is rising to <strong>{risk_pct:.1f}%</strong> ({stage_name})
                within <strong>+{lead_time_min} minutes</strong>. Action: Place authentication gateways under scrutiny.
            </div>
        </div>
        """
    else:
        html = f"""
        <div class="alert-banner-green">
            <div class="title">NORMAL OPERATIONAL STATUS: Traffic Baseline Steady</div>
            <div class="desc">
                Forecasted network behaviour remains within healthy baseline bounds (Risk: <strong>{risk_pct:.1f}%</strong>). No active threat detected.
            </div>
        </div>
        """
    safe_html(html)


def render_risk_trajectory_chart(forecast_timeline: list, current_risk_pct: float):
    """
    Renders an interactive Plotly chart with light theme and shaded risk zones:
    - Green zone (0 - 20%): Normal Traffic
    - Yellow/Orange zone (20 - 50%): Medium Risk
    - Red zone (50 - 100%): High Risk
    """
    steps = ["Current (t)"] + [item["step"] for item in forecast_timeline]
    risks = [current_risk_pct] + [item["predicted_risk_pct"] for item in forecast_timeline]
    hover_texts = [f"Risk: {r:.1f}%" for r in risks]

    fig = go.Figure()

    # 1. Shaded Risk Zones (Bands)
    fig.add_hrect(
        y0=0, y1=20, fillcolor="#E6FCF5", opacity=0.8,
        layer="below", line_width=0, annotation_text="NORMAL TRAFFIC (<20%)",
        annotation_position="top left", annotation_font_color="#2B8A3E",
        annotation_font_size=11, annotation_font_family="sans-serif"
    )
    fig.add_hrect(
        y0=20, y1=50, fillcolor="#FFF9DB", opacity=0.8,
        layer="below", line_width=0, annotation_text="MEDIUM RISK (20% - 50%)",
        annotation_position="top left", annotation_font_color="#D9480F",
        annotation_font_size=11, annotation_font_family="sans-serif"
    )
    fig.add_hrect(
        y0=50, y1=100, fillcolor="#FFF5F5", opacity=0.8,
        layer="below", line_width=0, annotation_text="HIGH ATTACK RISK (>=50%)",
        annotation_position="top left", annotation_font_color="#C92A2A",
        annotation_font_size=11, annotation_font_family="sans-serif"
    )

    # 2. Risk Trajectory Line & Points
    # Dynamic marker color based on value
    marker_colors = []
    for r in risks:
        if r >= 50.0:
            marker_colors.append("#C92A2A")
        elif r >= 20.0:
            marker_colors.append("#D9480F")
        else:
            marker_colors.append("#2B8A3E")

    fig.add_trace(go.Scatter(
        x=steps,
        y=risks,
        mode="lines+markers+text",
        line=dict(color="#111111", width=3),
        marker=dict(size=12, color=marker_colors, line=dict(color="#FFFFFF", width=2)),
        text=[f"{r:.1f}%" for r in risks],
        textposition="top center",
        textfont=dict(size=12, color="#111111", family="sans-serif"),
        hoverinfo="text",
        hovertext=hover_texts,
        name="Forecasted Risk"
    ))

    # 3. Layout Formatting for Light Mode
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=380,
        margin=dict(l=40, r=30, t=30, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor="#E9ECEF",
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=12, family="sans-serif")
        ),
        yaxis=dict(
            range=[0, 105],
            showgrid=True,
            gridcolor="#E9ECEF",
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=12, family="sans-serif"),
            ticksuffix="%"
        ),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def render_horizontal_attribution_chart(attributions: list):
    """
    Renders an interactive HORIZONTAL bar chart for feature attributions (Section 7 requirement).
    Strictly horizontal bars with semantic risk coloring:
    - Red (#C92A2A): Features increasing risk (Risk Escalation +)
    - Green (#2B8A3E): Features decreasing risk (Risk Mitigation -)
    - Slate (#495057): Neutral / baseline contribution
    """
    if not attributions:
        st.info("No attribution data available.")
        return

    # Sort ascending by importance so the highest importance appears at the TOP
    sorted_attrs = sorted(attributions, key=lambda x: x.get("importance_pct", 0.0))

    feature_names = [item["feature_name"] for item in sorted_attrs]
    importance_vals = [item["importance_pct"] for item in sorted_attrs]
    directions = [item.get("direction", "NEUTRAL") for item in sorted_attrs]

    bar_colors = []
    text_labels = []
    for d, val in zip(directions, importance_vals):
        text_labels.append(f"{val:.1f}%")
        if "(+)" in d or "ESCALATION" in d:
            bar_colors.append("#C92A2A")  # Crimson Red
        elif "(-)" in d or "MITIGATION" in d:
            bar_colors.append("#2B8A3E")  # Forest Green
        else:
            bar_colors.append("#495057")  # Slate Grey

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=importance_vals,
        y=feature_names,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="#FFFFFF", width=1.5)
        ),
        text=text_labels,
        textposition="outside",
        textfont=dict(size=12, color="#111111", family="sans-serif"),
        cliponaxis=False,
        hoverinfo="y+x+text",
        hovertext=[f"Impact: {d}" for d in directions]
    ))

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=max(280, len(feature_names) * 44),
        margin=dict(l=20, r=40, t=10, b=30),
        xaxis=dict(
            title=dict(text="Feature Attribution Impact (%)", font=dict(size=12, color="#495057")),
            showgrid=True,
            gridcolor="#E9ECEF",
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=11),
            ticksuffix="%"
        ),
        yaxis=dict(
            showgrid=False,
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=12, family="sans-serif")
        ),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sequential_trajectory_chart(
    observed_history: list,
    forecast_timeline: list,
    current_idx: int,
    current_time_str: str = ""
):
    """
    Renders the Sequential Risk Trajectory Chart (Section 1 & 12 requirement):
    - Solid dark line: Observed historical risk leading up to state S(t)
    - Prominent highlighted marker on current active state S(t)
    - Dashed line: Autoregressive K-step future forecast trajectory S(t+1)...S(t+K)
    - Shaded background risk zones: Normal (<20%), Medium (20-50%), High (>=50%)
    """
    fig = go.Figure()

    # 1. Shaded Risk Zones (Bands)
    fig.add_hrect(
        y0=0, y1=20, fillcolor="#E6FCF5", opacity=0.75,
        layer="below", line_width=0, annotation_text="NORMAL BASELINE (<20%)",
        annotation_position="top left", annotation_font_color="#2B8A3E",
        annotation_font_size=10, annotation_font_family="sans-serif"
    )
    fig.add_hrect(
        y0=20, y1=50, fillcolor="#FFF9DB", opacity=0.75,
        layer="below", line_width=0, annotation_text="MEDIUM THREAT ZONE (20% - 50%)",
        annotation_position="top left", annotation_font_color="#D9480F",
        annotation_font_size=10, annotation_font_family="sans-serif"
    )
    fig.add_hrect(
        y0=50, y1=100, fillcolor="#FFF5F5", opacity=0.75,
        layer="below", line_width=0, annotation_text="HIGH ATTACK RISK (>=50%)",
        annotation_position="top left", annotation_font_color="#C92A2A",
        annotation_font_size=10, annotation_font_family="sans-serif"
    )

    # 2. Observed Historical Points
    obs_x = [item["label"] for item in observed_history]
    obs_y = [item["risk_pct"] for item in observed_history]
    obs_hover = [f"{item['label']} | Time: {item.get('time', '')}<br>Risk: {item['risk_pct']:.1f}%" for item in observed_history]

    fig.add_trace(go.Scatter(
        x=obs_x,
        y=obs_y,
        mode="lines+markers",
        name="Observed History",
        line=dict(color="#111111", width=2.5),
        marker=dict(size=7, color="#111111"),
        hoverinfo="text",
        hovertext=obs_hover
    ))

    # 3. Highlighted Active State S(t)
    if observed_history:
        active_item = observed_history[-1]
        fig.add_trace(go.Scatter(
            x=[active_item["label"]],
            y=[active_item["risk_pct"]],
            mode="markers+text",
            name="Current State S(t)",
            marker=dict(
                size=16,
                color="#C92A2A" if active_item["risk_pct"] >= 50 else ("#D9480F" if active_item["risk_pct"] >= 20 else "#2B8A3E"),
                line=dict(color="#111111", width=3)
            ),
            text=[f"S(t): {active_item['risk_pct']:.1f}%"],
            textposition="top center",
            textfont=dict(size=12, color="#111111", family="sans-serif"),
            hoverinfo="text",
            hovertext=[f"ACTIVE STATE S(t)<br>Time: {current_time_str}<br>Risk: {active_item['risk_pct']:.1f}%"]
        ))

    # 4. Projected Future Forecast Trajectory (Dashed)
    if forecast_timeline and observed_history:
        fut_x = [active_item["label"]] + [item["step"] for item in forecast_timeline]
        fut_y = [active_item["risk_pct"]] + [item["predicted_risk_pct"] for item in forecast_timeline]
        fut_hover = [f"Origin: {active_item['label']} ({active_item['risk_pct']:.1f}%)"] + [
            f"Forecast {item['step']} (+{item['minutes_ahead']}m)<br>Risk: {item['predicted_risk_pct']:.1f}%<br>Stage: {item['predicted_stage_name']}"
            for item in forecast_timeline
        ]

        marker_colors = []
        for r in fut_y[1:]:
            if r >= 50.0:
                marker_colors.append("#C92A2A")
            elif r >= 20.0:
                marker_colors.append("#D9480F")
            else:
                marker_colors.append("#2B8A3E")

        fig.add_trace(go.Scatter(
            x=fut_x,
            y=fut_y,
            mode="lines+markers+text",
            name="K-Step Forecast",
            line=dict(color="#D9480F", width=2.5, dash="dash"),
            marker=dict(size=10, color=["#111111"] + marker_colors, line=dict(color="#FFFFFF", width=1.5)),
            text=[""] + [f"{r:.1f}%" for r in fut_y[1:]],
            textposition="top center",
            textfont=dict(size=11, color="#111111"),
            hoverinfo="text",
            hovertext=fut_hover
        ))

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=380,
        margin=dict(l=40, r=30, t=25, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor="#E9ECEF",
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=11, family="sans-serif")
        ),
        yaxis=dict(
            range=[0, 105],
            showgrid=True,
            gridcolor="#E9ECEF",
            linecolor="#CED4DA",
            tickfont=dict(color="#111111", size=11, family="sans-serif"),
            ticksuffix="%"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#111111")
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def render_mitre_progression_timeline(progression_items: list):
    """
    Renders the MITRE ATT&CK tactical progression timeline (Section 6 requirement).
    Connects observed behavior at S(t) to predicted future stages S(t+1)...S(t+K).
    """
    if not progression_items:
        st.info("No tactical progression data available.")
        return

    for idx, item in enumerate(progression_items):
        is_observed = item.get("type") == "OBSERVED"
        risk_pct = item.get("risk_pct", 0.0)

        if risk_pct >= 50.0:
            border_col = "#FFA8A8"
            bg_col = "#FFF5F5"
            badge_class = "badge-high"
        elif risk_pct >= 20.0:
            border_col = "#FFE066"
            bg_col = "#FFF9DB"
            badge_class = "badge-medium"
        else:
            border_col = "#63E6BE"
            bg_col = "#E6FCF5"
            badge_class = "badge-clean"

        header_badge = "OBSERVED TELEMETRY" if is_observed else f"PREDICTED FUTURE (+{item.get('timestamp', '')})"
        type_badge_class = "badge-clean" if is_observed else "badge-medium"

        card_html = f"""
        <div style="background-color: #FFFFFF; border: 1.5px solid {border_col}; border-left: 6px solid {border_col}; border-radius: 8px; padding: 18px 20px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #E9ECEF; padding-bottom: 8px;">
                <div>
                    <span style="font-size: 15px; font-weight: 700; color: #111111;">{item.get('step_label')}</span>
                    <span style="margin-left: 10px; font-size: 12px; color: #6C757D;">{item.get('timestamp', '')}</span>
                </div>
                <div>
                    <span class="{type_badge_class}" style="margin-right: 8px;">{header_badge}</span>
                    <span class="{badge_class}">Risk: {risk_pct:.1f}%</span>
                    <span style="margin-left: 8px; font-size: 11px; font-weight: 700; background: #E9ECEF; padding: 3px 8px; border-radius: 4px; color: #495057;">CONFIDENCE: {item.get('confidence', 'HIGH')}</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
                <div>
                    <div style="font-size: 11px; font-weight: 700; color: #6C757D; text-transform: uppercase;">Tactical MITRE Stage</div>
                    <div style="font-size: 16px; font-weight: 800; color: #111111; margin: 2px 0 6px 0;">{item.get('stage_name')}</div>
                    <div style="font-size: 13px; color: #212529;"><strong>Tactic:</strong> <code>{item.get('tactic_id')}</code> — {item.get('tactic_name')}</div>
                    <div style="font-size: 13px; color: #212529; margin-top: 2px;"><strong>Technique:</strong> <code>{item.get('technique_id')}</code> — {item.get('technique_name')}</div>
                    <div style="font-size: 12px; color: #495057; margin-top: 8px; font-style: italic;">{item.get('description', '')}</div>
                </div>
                <div>
                    <div style="font-size: 11px; font-weight: 700; color: #6C757D; text-transform: uppercase;">Behavioural Signatures & Mitigations</div>
                    <div style="background-color: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 6px; padding: 8px 12px; font-size: 12px; color: #212529; margin: 4px 0 8px 0;">
                        <strong>Network Indicators:</strong> {item.get('behavioral_indicators', 'Standard activity')}
                    </div>
                    <div style="font-size: 12px; color: #111111;">
                        <strong>SOC Defensive Playbook:</strong>
                        <ul style="margin: 4px 0 0 16px; padding: 0;">
        """
        for mit in item.get("mitigations", []):
            card_html += f"<li style='margin-bottom: 2px;'>{mit}</li>"

        card_html += """
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
        safe_html(card_html)

        if idx < len(progression_items) - 1:
            safe_html("<div style='text-align: center; color: #868E96; font-size: 18px; margin: -6px 0 8px 0;'>↓</div>")


def render_state_stream(current_idx: int, total_states: int, state_ids: list = None, timestamps: list = None):
    """
    Renders the dynamic horizontal state pipeline tracker (Section 5 requirement).
    Shows state progression: S001 ✓ → S002 ✓ → 👉 S003 [ACTIVE] → S004 [t+1] → ...
    """
    start_window = max(0, current_idx - 4)
    end_window = min(total_states, current_idx + 3)

    pills = ["<div style='display: flex; gap: 8px; align-items: center; overflow-x: auto; padding: 8px 0; margin-bottom: 8px;'>"]
    for idx in range(start_window, end_window):
        s_num = idx + 1
        s_id = state_ids[idx] if state_ids and idx < len(state_ids) else f"S{s_num:03d}"
        t_str = str(timestamps[idx])[-8:-3] if timestamps and idx < len(timestamps) else f"{s_num}m"

        if s_num < current_idx:
            pills.append(
                f"<div style='background-color: #F1F3F5; border: 1px solid #CED4DA; border-radius: 6px; padding: 5px 10px; font-size: 12px; color: #495057; white-space: nowrap;'>"
                f"<span style='font-weight: 700;'>{s_id}</span> <span style='color: #2B8A3E;'>✓</span>"
                f"<div style='font-size: 10px; color: #868E96;'>{t_str}</div>"
                f"</div>"
            )
        elif s_num == current_idx:
            pills.append(
                f"<div style='background-color: #111111; border: 1px solid #111111; border-radius: 6px; padding: 5px 12px; font-size: 12px; color: #FFFFFF; font-weight: 800; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.15);'>"
                f"👉 {s_id} <span style='background: #C92A2A; color: #FFFFFF; padding: 1px 4px; border-radius: 3px; font-size: 9px; margin-left: 4px;'>ACTIVE</span>"
                f"<div style='font-size: 10px; color: #E9ECEF; font-weight: normal;'>{t_str}</div>"
                f"</div>"
            )
        else:
            diff = s_num - current_idx
            pills.append(
                f"<div style='background-color: #FFFFFF; border: 1px dashed #ADB5BD; border-radius: 6px; padding: 5px 10px; font-size: 12px; color: #868E96; white-space: nowrap;'>"
                f"<span style='font-weight: 600;'>{s_id}</span> <span style='color: #D9480F; font-size: 10px;'>[t+{diff}]</span>"
                f"<div style='font-size: 10px; color: #ADB5BD;'>Pending</div>"
                f"</div>"
            )

    pills.append("</div>")
    pills_html = "".join(pills)
    safe_html(pills_html)


def render_processing_pipeline(stages_status: list):
    """
    Renders the live 8-stage CSV processing pipeline tracker (Section 3 requirement).
    """
    stages = [
        "1. CSV Validation",
        "2. Timestamp Parsing",
        "3. Data Cleaning",
        "4. Feature Extraction",
        "5. Time-Window Aggregation",
        "6. Network State Construction",
        "7. State Vector Generation",
        "8. Sequential Forecast Initialization"
    ]

    cols = st.columns(4)
    for i, stage_name in enumerate(stages):
        col = cols[i % 4]
        status = stages_status[i] if i < len(stages_status) else "Waiting"
        if status == "Completed" or status is True or status == "✓":
            badge_html = "<span style='color: #2B8A3E; font-weight: 800;'>✓ COMPLETED</span>"
            border = "1px solid #63E6BE"
            bg = "#E6FCF5"
        elif "Processing" in status or status == "Active":
            badge_html = "<span style='color: #D9480F; font-weight: 800;'>⏳ PROCESSING...</span>"
            border = "1.5px solid #FFE066"
            bg = "#FFF9DB"
        else:
            badge_html = "<span style='color: #868E96;'>PENDING</span>"
            border = "1px solid #DEE2E6"
            bg = "#F8F9FA"

        with col:
            item_html = (
                f"<div style='background-color: {bg}; border: {border}; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; font-size: 12px;'>"
                f"<div style='font-weight: 700; color: #111111;'>{stage_name}</div>"
                f"<div style='font-size: 11px; margin-top: 2px;'>{badge_html}</div>"
                f"</div>"
            )
            safe_html(item_html)

