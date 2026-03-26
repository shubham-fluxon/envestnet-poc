from strands import Agent, tool
from agents.model import model
from tools.data_tools import get_portfolio_summary, query_portfolio_data, get_price_history

_data_agent = Agent(
    model=model,
    system_prompt=(
        "You are a financial data analyst. Your job is to retrieve and analyze portfolio data. "
        "Use the available tools to query portfolios, fetch holdings, calculate performance metrics, "
        "and retrieve historical price data. Return clear, structured data that can be used for "
        "visualization. Always include relevant numbers and context in your responses."
    ),
    tools=[get_portfolio_summary, query_portfolio_data, get_price_history],
)


@tool
def consult_data_analyst(request: str) -> str:
    """Consult the financial data analyst to retrieve portfolio data, holdings, performance metrics, or price history.

    Args:
        request: A natural language request describing what financial data is needed.
                 Examples: 'Get holdings for tech_portfolio', 'Fetch 30-day price history for AAPL',
                 'Summarize all portfolios', 'Get sector allocation for balanced_portfolio'

    Returns:
        The analyst's response with the requested data.
    """
    result = _data_agent(request)
    return str(result)
