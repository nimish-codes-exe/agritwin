"""Small shared formatters."""

STATUS_COLORS = {
    "Healthy":      "#4caf50",
    "Warning":      "#ff9800",
    "High Risk":    "#ff5722",
    "Critical":     "#f44336",
    "Low Confidence": "#9e9e9e",
}

COMPONENT_LABELS = {
    "engine_heat":   "Engine Overheating",
    "cooling":       "Cooling System",
    "oil_pressure":  "Oil Pressure",
    "vibration":     "Engine Vibration",
}


def fmt_pct(v):
    return f"{v:.0f}%"


def fmt_usd(v):
    return f"${v:,.2f}"


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "#9e9e9e")


def pretty_component(c: str) -> str:
    return COMPONENT_LABELS.get(c, c.replace("_", " ").title())