from strands import Agent, tool
from agents.model import model
from tools.chart_tools import create_chart, create_table

_chart_agent = Agent(
    model=model,
    system_prompt=(
        "You are a data visualization specialist focused on financial charts. "
        "Your job is to create clear, professional charts and tables from financial data. "
        "When given data and a visualization request, choose the most appropriate chart type: "
        "- Use 'line' charts for price history and time series data "
        "- Use 'bar' charts for comparing values across holdings or categories "
        "- Use 'pie' charts for portfolio allocation and sector breakdowns "
        "- Use tables for detailed holdings data with multiple columns. "
        "Always format data as proper JSON before passing to tools. "
        "Choose descriptive output filenames. Report the saved file path in your response."
    ),
    tools=[create_chart, create_table],
)


@tool
def consult_chart_specialist(request: str) -> str:
    """Consult the chart specialist to create financial visualizations (charts and tables).

    Args:
        request: A natural language request describing what chart or table to create,
                 including the data to visualize. Provide the actual data values in the request.
                 Examples: 'Create a pie chart of tech portfolio sectors with data: {...}',
                 'Create a line chart of AAPL price history: [...]',
                 'Create a table of holdings: [...]'

    Returns:
        The specialist's response including the path to the saved chart/table file.
    """
    result = _chart_agent(request)
    return str(result)
