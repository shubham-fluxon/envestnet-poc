#!/usr/bin/env python3
"""
Financial Chart Creation Agent - AWS Strands Demo
"""
from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import orchestrator

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         Financial Portfolio Assistant (Strands)          ║
╠══════════════════════════════════════════════════════════╣
║  Example queries:                                        ║
║  • Show me a summary of all portfolios                   ║
║  • Create a pie chart of tech portfolio holdings         ║
║  • Show the price history for AAPL as a line chart       ║
║  • Create a table of all holdings in balanced_portfolio  ║
║  • Compare performance of tech_portfolio stocks          ║
║  Type 'quit' or 'exit' to stop                          ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    print(BANNER)
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\nAssistant: ", end="", flush=True)
        try:
            result = orchestrator(user_input)
            print(str(result))
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
