"""Reusable Plotly figures."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from .helpers import status_color


DARK_BG = "#0f1e2e"
GRID = "#1e3247"
TXT = "#e0e6ee"
GREEN = "#7ac74f"


def _apply_theme(fig):
    fig.update_layout(
        paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
        font=dict(color=TXT, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def sensor_trend_chart(df: pd.DataFrame, sensors, title="Sensor Trends"):
    fig = go.Figure()
    palette = [GREEN, "#ff9800", "#f44336", "#42a5f5", "#ab47bc"]
    for i, s in enumerate(sensors):
        if s not in df:
            continue
        fig.add_trace(go.Scatter(
            x=df["ts"], y=df[s], name=s,
            line=dict(color=palette[i % len(palette)], width=2),
        ))
    fig.update_layout(title=title, hovermode="x unified")
    return _apply_theme(fig)


def degradation_bar(severities: dict):
    from .helpers import pretty_component
    comps = [pretty_component(c) for c in severities]
    vals  = [round(v * 100, 1) for v in severities.values()]
    colors = ["#f44336" if v > 75 else "#ff9800" if v > 40 else GREEN for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=comps, orientation="h",
                            marker_color=colors, text=[f"{v}%" for v in vals],
                            textposition="outside"))
    fig.update_layout(title="Component Degradation", xaxis_range=[0, 105],
                      xaxis_title="Degradation (%)", yaxis_title="")
    return _apply_theme(fig)


def risk_gauge(risk: float, reliability: float, status: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk,
        number={"suffix": "", "font": {"size": 42}},
        title={"text": f"Risk Score — {status}<br><sub>Reliability {reliability:.0f}%</sub>"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": status_color(status)},
            "steps": [
                {"range": [0, 25],  "color": "#1b3d22"},
                {"range": [25, 50], "color": "#3d3417"},
                {"range": [50, 75], "color": "#3d2717"},
                {"range": [75, 100],"color": "#3d1717"},
            ],
            "threshold": {"line": {"color": "white", "width": 3},
                          "thickness": 0.8, "value": risk},
        },
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=60, b=10))
    return _apply_theme(fig)


def scenario_comparison_chart(projections: dict):
    """projections: {policy_name: [{hour, engine_temp_c}, ...]}"""
    fig = go.Figure()
    colors = {"repair_now": GREEN, "delay_48h": "#ff9800", "continue": "#f44336"}
    labels = {"repair_now": "Repair Now", "delay_48h": "Delay 48h", "continue": "Continue Operating"}
    for policy, rows in projections.items():
        hours = [r["hour"] for r in rows]
        temps = [r["engine_temp_c"] for r in rows]
        fig.add_trace(go.Scatter(x=hours, y=temps, mode="lines+markers",
                                  name=labels[policy],
                                  line=dict(color=colors[policy], width=2)))
    fig.update_layout(title="Engine Temperature Projection", xaxis_title="Hours from now",
                      yaxis_title="Engine Temp (°C)", hovermode="x unified")
    return _apply_theme(fig)