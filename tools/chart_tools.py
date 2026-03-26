import json
import uuid
import plotly.graph_objects as go
from strands import tool

# In-memory chart store: chart_id → HTML string
# Shared with server.py (same process)
CHART_STORE: dict[str, str] = {}

_TEMPLATE = "plotly_dark"
_PAPER_BG = "#1e1e2e"
_PLOT_BG  = "#1e1e2e"
_FONT_CLR = "#cdd6f4"
_COLORS   = ["#89b4fa","#a6e3a1","#fab387","#f38ba8","#cba6f7",
              "#89dceb","#f9e2af","#94e2d5","#eba0ac","#b4befe"]


def _store(fig: go.Figure) -> str:
    """Render fig to an HTML div, store it, return the chart marker."""
    html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"responsive": True, "displayModeBar": True},
    )
    chart_id = str(uuid.uuid4())
    CHART_STORE[chart_id] = html
    return f"CHART::{chart_id}"


@tool
def create_chart(chart_type: str, data: str, title: str) -> str:
    """Create an interactive financial chart rendered in the browser.

    Args:
        chart_type: 'line', 'bar', or 'pie'
        data: JSON string. For line/bar: {"labels": [...], "values": [...], "xlabel": "...", "ylabel": "..."}
              For pie: {"labels": [...], "values": [...]}
        title: Chart title

    Returns:
        A CHART:: marker string that the frontend will replace with the interactive chart.
    """
    try:
        d = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"

    labels = d.get("labels", [])
    values = d.get("values", [])
    if not labels or not values:
        return "Error: 'labels' and 'values' are required."
    if len(labels) != len(values):
        return "Error: 'labels' and 'values' must be the same length."

    if chart_type == "line":
        fig = go.Figure(go.Scatter(
            x=labels, y=values,
            mode="lines+markers",
            line=dict(color=_COLORS[0], width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(137,180,250,0.1)",
        ))
        fig.update_layout(
            xaxis_title=d.get("xlabel", ""),
            yaxis_title=d.get("ylabel", "Price (USD)"),
        )

    elif chart_type == "bar":
        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=[_COLORS[i % len(_COLORS)] for i in range(len(labels))],
            text=[f"${v:,.0f}" if v > 100 else f"{v:.1f}%" for v in values],
            textposition="outside",
        ))
        fig.update_layout(
            xaxis_title=d.get("xlabel", ""),
            yaxis_title=d.get("ylabel", "Value (USD)"),
        )

    elif chart_type == "pie":
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker=dict(colors=_COLORS[:len(labels)],
                        line=dict(color=_PAPER_BG, width=2)),
            textinfo="label+percent",
            hole=0.35,
        ))

    else:
        return f"Error: Unknown chart_type '{chart_type}'. Use 'line', 'bar', or 'pie'."

    fig.update_layout(
        title=dict(text=title, font=dict(color=_FONT_CLR, size=16)),
        paper_bgcolor=_PAPER_BG,
        plot_bgcolor=_PLOT_BG,
        font=dict(color=_FONT_CLR),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return _store(fig)


@tool
def create_table(data: str, title: str) -> str:
    """Create an interactive financial data table rendered in the browser.

    Args:
        data: JSON string — list of dicts (rows) or {"headers": [...], "rows": [[...], ...]}
        title: Table title

    Returns:
        A CHART:: marker string that the frontend will replace with the interactive table.
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"

    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        headers = list(parsed[0].keys())
        rows = [[str(row.get(h, "")) for h in headers] for row in parsed]
    elif isinstance(parsed, dict) and "headers" in parsed and "rows" in parsed:
        headers = parsed["headers"]
        rows = [[str(v) for v in row] for row in parsed["rows"]]
    else:
        return "Error: data must be a list of dicts or {'headers': [...], 'rows': [[...], ...]}"

    # Transpose rows → columns for Plotly Table
    columns = [[row[i] for row in rows] for i in range(len(headers))]

    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color="#313244",
            font=dict(color="#89b4fa", size=12),
            align="center",
            line_color="#45475a",
            height=32,
        ),
        cells=dict(
            values=columns,
            fill_color=[[_PAPER_BG if i % 2 == 0 else "#2a2a3e" for i in range(len(rows))]
                        for _ in headers],
            font=dict(color=_FONT_CLR, size=11),
            align="center",
            line_color="#45475a",
            height=28,
        ),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=_FONT_CLR, size=16)),
        paper_bgcolor=_PAPER_BG,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return _store(fig)
