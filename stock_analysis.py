# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys
import yfinance as yf
import ollama
import pandas as pd
from datetime import datetime, timedelta
import argparse
from colorama import init, Fore, Style, Back
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional

def get_insider_trades(ticker: str) -> List[Dict]:
    """
    Fetch recent insider trades from OpenInsider
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        List[Dict]: List of insider trades with relevant information
    """
    try:
        url = f"http://openinsider.com/search?q={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"class": "tinytable"})
        
        if not table:
            return []
            
        trades = []
        for row in table.find_all("tr")[1:6]:  # Get last 5 trades
            cols = row.find_all("td")
            if len(cols) >= 8:
                trade = {
                    'date': cols[1].text.strip(),
                    'insider': cols[3].text.strip(),
                    'title': cols[4].text.strip(),
                    'trade_type': cols[5].text.strip(),
                    'price': cols[6].text.strip(),
                    'qty': cols[7].text.strip(),
                    'owned': cols[8].text.strip(),
                    'delta_own': cols[9].text.strip(),
                    'value': cols[10].text.strip()
                }
                trades.append(trade)
                
        return trades
    except Exception as e:
        print(Fore.RED + f"Error fetching insider trades: {str(e)}" + Style.RESET_ALL)
        return []

def format_insider_trades(trades: List[Dict]) -> str:
    """
    Format insider trades data for the analysis prompt
    
    Args:
        trades (List[Dict]): List of insider trade dictionaries
        
    Returns:
        str: Formatted insider trades string
    """
    if not trades:
        return "No recent insider trades found"
        
    formatted = "Recent insider trades:\n"
    for trade in trades:
        formatted += f"Date: {trade['date']}\n"
        formatted += f"Insider: {trade['insider']} ({trade['title']})\n"
        formatted += f"Type: {trade['trade_type']} | Price: {trade['price']} | Quantity: {trade['qty']}\n"
        formatted += f"Value: {trade['value']} | Shares Owned: {trade['owned']}\n"
        formatted += "-" * 50 + "\n"
        
    return formatted

def get_stock_data(ticker: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Fetch comprehensive stock data"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get historical data for different timeframes
        data = {
            'daily': stock.history(period='1mo', interval='1d'),
            'weekly': stock.history(period='1y', interval='1wk'), 
            'monthly': stock.history(period='5y', interval='1mo')
        }
        
        # Get company info
        info = stock.info
        
        # Calculate technical indicators
        daily_data = data['daily']
        if not daily_data.empty:
            # RSI calculation
            delta = daily_data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            daily_data['RSI'] = 100 - (100 / (1 + rs))
            
            # Moving averages
            daily_data['SMA_20'] = daily_data['Close'].rolling(window=20).mean()
            daily_data['SMA_50'] = daily_data['Close'].rolling(window=50).mean()
            
            # Calculate VWAP
            daily_data['VWAP'] = (daily_data['Close'] * daily_data['Volume']).cumsum() / daily_data['Volume'].cumsum()
        
        return data, info
    except Exception as e:
        print(Fore.RED + f"Error fetching data for {ticker}: {str(e)}" + Style.RESET_ALL)
        return None, None

def generate_analysis_prompt(ticker: str, data: Dict, info: Dict, insider_trades: List[Dict]) -> str:
    """Generate comprehensive analysis prompt"""
    daily_data = data['daily']
    current_price = daily_data['Close'].iloc[-1]
    rsi = daily_data['RSI'].iloc[-1] 
    sma_20 = daily_data['SMA_20'].iloc[-1]
    sma_50 = daily_data['SMA_50'].iloc[-1]
    vwap = daily_data['VWAP'].iloc[-1]
    
    # Calculate price changes
    daily_change = (daily_data['Close'].iloc[-1] / daily_data['Close'].iloc[-2] - 1) * 100
    weekly_change = (data['weekly']['Close'].iloc[-1] / data['weekly']['Close'].iloc[-2] - 1) * 100  
    monthly_change = (data['monthly']['Close'].iloc[-1] / data['monthly']['Close'].iloc[-2] - 1) * 100

    # Format insider trades
    insider_trades_str = format_insider_trades(insider_trades)

    prompt = f"""You are an expert stock analyst. Provide a comprehensive analysis of {ticker} to determine if it's a good short-term (day/swing trade) or long-term investment.

INSIDER TRADES:
{insider_trades_str}

COMPANY INFORMATION:
Name: {info.get('longName', 'N/A')}
Industry: {info.get('industry', 'N/A')}
Sector: {info.get('sector', 'N/A')}
Market Cap: ${info.get('marketCap', 0):,.2f}

CURRENT MARKET DATA:
Price: ${current_price:.2f}
52-Week Range: ${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}
Volume: {info.get('volume', 0):,}
Average Volume: {info.get('averageVolume', 0):,}

TECHNICAL INDICATORS:
RSI (14): {rsi:.2f}
SMA 20: ${sma_20:.2f} 
SMA 50: ${sma_50:.2f}
VWAP: ${vwap:.2f}

PERFORMANCE:  
Daily Change: {daily_change:.2f}%
Weekly Change: {weekly_change:.2f}%
Monthly Change: {monthly_change:.2f}%

FUNDAMENTAL METRICS:
P/E Ratio: {info.get('trailingPE', 'N/A')}
EPS (TTM): ${info.get('trailingEps', 0):.2f}
Forward P/E: {info.get('forwardPE', 'N/A')}
PEG Ratio: {info.get('pegRatio', 'N/A')}

Based on this data, provide:
1. SHORT-TERM OUTLOOK (1-5 days)  
   - Clear buy/sell/hold recommendation
   - Key support and resistance levels
   - Potential entry/exit points
   - Risk assessment

2. LONG-TERM OUTLOOK (6-12 months)
   - Investment recommendation  
   - Growth potential
   - Key risks and catalysts
   - Target price range

3. KEY CONSIDERATIONS
   - Technical analysis insights
   - Fundamental strengths/weaknesses
   - Market sentiment
   - Industry trends
   - Impact of recent insider trading activity

Format your response clearly with sections and provide specific actionable insights.
"""
    return prompt

def print_header(ticker: str) -> None:
    """Print formatted header"""
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "STOCK ANALYSIS: " + Fore.YELLOW + ticker + Style.RESET_ALL)
    print(Fore.CYAN + "=" * 80 + Style.RESET_ALL + "\n")

def format_analysis(analysis: str) -> str:
    """Format analysis output with color coding and organization"""
    formatted_analysis = analysis.replace("Short-Term Outlook", Fore.CYAN + Style.BRIGHT + "Short-Term Outlook" + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Long-Term Outlook", Fore.CYAN + Style.BRIGHT + "\nLong-Term Outlook" + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Key Considerations", Fore.CYAN + Style.BRIGHT + "\nKey Considerations" + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Recommendation: Buy", "Recommendation: " + Back.GREEN + Fore.BLACK + " Buy " + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Recommendation: Sell", "Recommendation: " + Back.RED + Fore.BLACK + " Sell " + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Recommendation: Hold", "Recommendation: " + Back.YELLOW + Fore.BLACK + " Hold " + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Support Levels:", Fore.GREEN + "Support Levels:" + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Resistance Levels:", Fore.RED + "Resistance Levels:" + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Entry Points:", Fore.GREEN + "Entry Points:" + Style.RESET_ALL)  
    formatted_analysis = formatted_analysis.replace("Exit Points:", Fore.RED + "Exit Points:" + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Risk: High", "Risk: " + Back.RED + Fore.BLACK + " High " + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Risk: Medium", "Risk: " + Back.YELLOW + Fore.BLACK + " Medium " + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Risk: Low", "Risk: " + Back.GREEN + Fore.BLACK + " Low " + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Target Price Range:", Fore.GREEN + Style.BRIGHT + "Target Price Range:" + Style.RESET_ALL)

    return formatted_analysis

def main() -> None:
    parser = argparse.ArgumentParser(description='Analyze a stock for trading opportunities')
    parser.add_argument('ticker', help='Stock ticker symbol')
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print_header(ticker)
    
    print(Fore.YELLOW + f"Fetching data for {ticker}..." + Style.RESET_ALL)
    data, info = get_stock_data(ticker)
    
    if data is None or info is None:
        return
        
    print(Fore.YELLOW + f"Fetching insider trades for {ticker}..." + Style.RESET_ALL)
    insider_trades = get_insider_trades(ticker)
    
    print(Fore.YELLOW + f"Analyzing {ticker}..." + Style.RESET_ALL)
    prompt = generate_analysis_prompt(ticker, data, info, insider_trades)
    
    try:
        response = ollama.generate(
            model='llama3',
            prompt=prompt,
            options={
                'temperature': 0.2,
                'num_predict': 1000,
            }
        )
        
        analysis = response['response'].strip()
        formatted_analysis = format_analysis(analysis)

        print("\n" + Fore.GREEN + "ANALYSIS RESULTS:" + Style.RESET_ALL)
        print("-" * 80)
        print(formatted_analysis)
        print("-" * 80)
        
    except Exception as e:
        print(Fore.RED + f"Error generating analysis: {str(e)}" + Style.RESET_ALL)

if __name__ == "__main__":
    init()  # Initialize colorama 
    if len(sys.argv) < 2:
        print(Fore.RED + f"Please provide a ticker symbol. Usage: python3 {sys.argv[0]} TICKER" + Style.RESET_ALL)
    else:
        main()
