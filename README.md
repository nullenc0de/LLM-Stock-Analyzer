
# Stock Analysis Tool

A Python-based tool to analyze stock performance and provide insights using historical data, technical indicators, and market trends. The tool fetches data for a given stock ticker using the Yahoo Finance API (`yfinance`) and generates a comprehensive analysis report using a custom AI model (`ollama`).

## Features
- Fetches historical stock data (daily, weekly, and monthly)
- Calculates technical indicators (RSI, SMA, VWAP)
- Provides a comprehensive analysis of short-term and long-term investment potential
- Colorful, easy-to-read output with formatted analysis
- Supports stock ticker input via command line

## Requirements
- Python 3.x
- `yfinance` library
- `ollama` API for analysis generation
- `colorama` library for colorful output
- `pandas` for data handling

You can install the required dependencies by running:

```bash
pip install yfinance ollama colorama pandas
```

## Usage

### Command-line Arguments
- `ticker`: The stock ticker symbol (e.g., `AAPL`, `GOOG`, `TSLA`)

### Example Command:
```bash
python3 stock_analysis.py AAPL
```

This will fetch data for the stock ticker `AAPL` and provide an analysis.

## Functions

### `get_stock_data(ticker)`
Fetches comprehensive stock data from Yahoo Finance for the given ticker symbol, including:
- Historical data (daily, weekly, monthly)
- Technical indicators (RSI, SMA, VWAP)
- Company information (market cap, volume, etc.)

### `generate_analysis_prompt(ticker, data, info)`
Generates a detailed analysis prompt based on the fetched data for use with the AI model. The prompt includes:
- Insider and senator trades (if available)
- Company info (name, industry, sector, etc.)
- Current market data (price, volume, 52-week range, etc.)
- Technical indicators (RSI, SMA, VWAP)
- Performance metrics (daily, weekly, and monthly changes)
- Fundamental metrics (P/E ratio, EPS, forward P/E, PEG ratio)

### `print_header(ticker)`
Prints a formatted header for the ticker symbol being analyzed.

### `format_analysis(analysis)`
Formats the AI-generated analysis with color coding for improved readability. It highlights key sections like recommendations, risk levels, support and resistance levels, and target price ranges.

### `main()`
The main entry point of the script that orchestrates the stock data fetching, analysis generation, and result printing.

## Example Output

When running the script, the output will look something like this:

```
================================================================================
STOCK ANALYSIS: AAPL
================================================================================

Fetching data for AAPL...
Analyzing AAPL...

ANALYSIS RESULTS:
--------------------------------------------------------------------------------

Short-Term Outlook (1-5 days)
Recommendation:  Buy 
Support Levels: $280.00
Resistance Levels: $300.00
Entry Points: $282.50
Exit Points: $270.00
Risk: Low

Long-Term Outlook (6-12 months)
Investment Recommendation: Hold
Growth Potential: Moderate
Key Risks: Competition in the tech sector
Target Price Range: $310.00 - $350.00

Key Considerations:
Technical analysis insights: Bullish RSI, positive moving averages
Fundamental strengths/weaknesses: Strong earnings growth
Market sentiment: Optimistic
Industry trends: Growing demand for consumer electronics

--------------------------------------------------------------------------------
```

## Error Handling
- If no ticker symbol is provided, the script will print a usage message:
  ```bash
  Please provide a ticker symbol. Usage: python3 stock_analysis.py TICKER
  ```

- If any errors occur while fetching data or generating the analysis, they will be printed in red.

## License
This project is licensed under the MIT License.
