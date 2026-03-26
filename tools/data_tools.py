import json
import os
from strands import tool

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.json")


def _load_data() -> dict:
    with open(DATA_FILE, "r") as f:
        return json.load(f)


@tool
def get_portfolio_summary() -> str:
    """Get a high-level summary of all available portfolios including total value and number of holdings.

    Returns:
        JSON string with portfolio names, total values, and holding counts.
    """
    data = _load_data()
    summary = []
    for portfolio_id, portfolio in data["portfolios"].items():
        total_value = sum(
            h["shares"] * h["current_price"] for h in portfolio["holdings"]
        )
        total_cost = sum(
            h["shares"] * h["purchase_price"] for h in portfolio["holdings"]
        )
        gain_loss = total_value - total_cost
        gain_loss_pct = (gain_loss / total_cost) * 100 if total_cost > 0 else 0
        summary.append({
            "portfolio_id": portfolio_id,
            "name": portfolio["name"],
            "created_date": portfolio["created_date"],
            "num_holdings": len(portfolio["holdings"]),
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
        })
    return json.dumps(summary, indent=2)


@tool
def query_portfolio_data(portfolio_id: str, metric: str) -> str:
    """Query detailed data for a specific portfolio.

    Args:
        portfolio_id: The portfolio identifier (e.g., 'tech_portfolio', 'balanced_portfolio')
        metric: What to retrieve — one of 'holdings', 'performance', 'sectors', 'value'

    Returns:
        JSON string with the requested portfolio data.
    """
    data = _load_data()
    if portfolio_id not in data["portfolios"]:
        available = list(data["portfolios"].keys())
        return json.dumps({"error": f"Portfolio '{portfolio_id}' not found. Available: {available}"})

    portfolio = data["portfolios"][portfolio_id]
    holdings = portfolio["holdings"]

    if metric == "holdings":
        result = []
        for h in holdings:
            current_value = h["shares"] * h["current_price"]
            cost_basis = h["shares"] * h["purchase_price"]
            result.append({
                "ticker": h["ticker"],
                "name": h["name"],
                "shares": h["shares"],
                "purchase_price": h["purchase_price"],
                "current_price": h["current_price"],
                "current_value": round(current_value, 2),
                "cost_basis": round(cost_basis, 2),
                "gain_loss": round(current_value - cost_basis, 2),
                "gain_loss_pct": round(((current_value - cost_basis) / cost_basis) * 100, 2),
                "sector": h["sector"],
            })
        return json.dumps(result, indent=2)

    elif metric == "performance":
        result = []
        for h in holdings:
            gain_loss = (h["current_price"] - h["purchase_price"]) / h["purchase_price"] * 100
            result.append({
                "ticker": h["ticker"],
                "gain_loss_pct": round(gain_loss, 2),
                "current_price": h["current_price"],
                "purchase_price": h["purchase_price"],
            })
        result.sort(key=lambda x: x["gain_loss_pct"], reverse=True)
        return json.dumps(result, indent=2)

    elif metric == "sectors":
        sectors: dict = {}
        for h in holdings:
            sector = h["sector"]
            value = h["shares"] * h["current_price"]
            sectors[sector] = sectors.get(sector, 0) + value
        return json.dumps({k: round(v, 2) for k, v in sectors.items()}, indent=2)

    elif metric == "value":
        total = sum(h["shares"] * h["current_price"] for h in holdings)
        return json.dumps({"portfolio_id": portfolio_id, "total_value": round(total, 2)})

    else:
        return json.dumps({"error": f"Unknown metric '{metric}'. Use: holdings, performance, sectors, value"})


@tool
def get_price_history(ticker: str, days: int = 30) -> str:
    """Get historical daily closing price data for a specific ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
        days: Number of recent trading days to return (default: 30, max: 30)

    Returns:
        JSON string with a list of closing prices (most recent last).
    """
    data = _load_data()
    history = data.get("price_history", {})
    ticker = ticker.upper()

    if ticker not in history:
        available = list(history.keys())
        return json.dumps({"error": f"No history for '{ticker}'. Available tickers: {available}"})

    prices = history[ticker]
    days = min(days, len(prices))
    recent = prices[-days:]

    return json.dumps({
        "ticker": ticker,
        "days": days,
        "prices": recent,
        "min": round(min(recent), 2),
        "max": round(max(recent), 2),
        "current": recent[-1],
        "change_pct": round(((recent[-1] - recent[0]) / recent[0]) * 100, 2),
    }, indent=2)
