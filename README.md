# Envestnet POC — Financial Portfolio Agent

A multi-agent system for financial portfolio analysis and interactive chart creation, built with [AWS Strands Agents SDK](https://strandsagents.com), Claude (Anthropic API), AG-UI protocol, and FastAPI.

## Architecture

```
User (Browser)
    │
    ▼
FastAPI Server  ──  AG-UI SSE stream  ──▶  Browser UI (Plotly charts)
    │
    ▼
Orchestrator Agent (Claude)
    ├──▶ Data Agent      → query_portfolio_data, get_portfolio_summary, get_price_history
    └──▶ Chart Agent     → create_chart, create_table (interactive Plotly)
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

**1. Clone the repo**
```bash
git clone git@github.com:shubham-fluxon/envestnet-poc.git
cd envestnet-poc
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
npm install
```

**4. Add your Anthropic API key**

Create a `.env` file in the project root:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Running

**Development** (two terminals):
```bash
npm run server   # Backend on :8000
npm run dev      # Vite dev server on :5173 (proxies API to :8000)
```

Open **http://localhost:5173**.

**Production**:
```bash
npm run build    # Build frontend to dist/
npm run server   # Serves both API and dist/
```

## Usage

Type a question in the chat box or click a suggestion chip. Examples:

- `Summarize all portfolios`
- `Create a pie chart of tech portfolio holdings`
- `Show AAPL price history as a line chart`
- `Create a table of balanced portfolio holdings`
- `Compare performance of all tech stocks`

Charts are rendered interactively in the browser (hover, zoom, pan).

## Project Structure

```
├── index.html              # Vite entrypoint
├── package.json            # Frontend deps & scripts
├── vite.config.ts          # Vite config (dev proxy to :8000)
├── tsconfig.json
├── server.py               # FastAPI server — AG-UI /agent endpoint
├── main.py                 # CLI entry point (terminal REPL)
├── requirements.txt
├── .env                    # API key (not committed)
├── frontend/
│   ├── main.ts         # Chat UI logic (AG-UI SSE consumer)
│   └── style.css       # Styles
├── data/
│   └── portfolio.json      # Dummy portfolio data (2 portfolios, 10 tickers)
├── agents/
│   ├── orchestrator.py     # Orchestrator agent
│   ├── data_agent.py       # Data analyst sub-agent
│   ├── chart_agent.py      # Chart specialist sub-agent
│   └── model.py            # Shared Anthropic model config
└── tools/
    ├── data_tools.py       # Portfolio query tools
    └── chart_tools.py      # Plotly chart/table tools
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | [Strands Agents SDK](https://strandsagents.com) |
| LLM | Claude Sonnet 4.6 (Anthropic API) |
| Agent–UI protocol | [AG-UI](https://docs.ag-ui.com) |
| Backend | FastAPI + Uvicorn |
| Charts | Plotly (interactive, browser-rendered) |
| Frontend | TypeScript + Vite + React | 
