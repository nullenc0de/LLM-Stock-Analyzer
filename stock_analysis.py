# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys
import yfinance as yf
import ollama
import pandas as pd
from datetime import datetime, timedelta
import argparse
from colorama import init, Fore, Style, Back

def get_stock_data(ticker):
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
        print(Fore.RED + "Error fetching data for {0}: {1}".format(ticker, str(e)) + Style.RESET_ALL)
        return None, None

def generate_analysis_prompt(ticker, data, info):
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

    prompt = """You are an expert stock analyst. Provide a comprehensive analysis of {0} to determine if it's a good short-term (day/swing trade) or long-term investment.

INSIDER TRADES:
{21}

SENATOR TRADES:
{22}


COMPANY INFORMATION:
Name: {1}
Industry: {2} 
Sector: {3}
Market Cap: ${4:,.2f}

CURRENT MARKET DATA:
Price: ${5:.2f}
52-Week Range: ${6:.2f} - ${7:.2f}
Volume: {8:,}
Average Volume: {9:,}

TECHNICAL INDICATORS:
RSI (14): {10:.2f}
SMA 20: ${11:.2f} 
SMA 50: ${12:.2f}
VWAP: ${13:.2f}

PERFORMANCE:  
Daily Change: {14:.2f}%
Weekly Change: {15:.2f}%
Monthly Change: {16:.2f}%

FUNDAMENTAL METRICS:
P/E Ratio: {17}
EPS (TTM): ${18:.2f}
Forward P/E: {19}
PEG Ratio: {20}

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

Format your response clearly with sections, colorful elements and provide specific actionable insights.
""".format(
        ticker,
        info.get('longName', 'N/A'),
        info.get('industry', 'N/A'),
        info.get('sector', 'N/A'),
        info.get('marketCap', 0),
        current_price,
        info.get('fiftyTwoWeekLow', 0),
        info.get('fiftyTwoWeekHigh', 0),
        info.get('volume', 0),
        info.get('averageVolume', 0),
        rsi,
        sma_20,
        sma_50,
        vwap,
        daily_change,
        weekly_change,
        monthly_change,
        info.get('trailingPE', 'N/A'),
        info.get('trailingEps', 0),
        info.get('forwardPE', 'N/A'),
        info.get('pegRatio', 'N/A'),
        info.get('insiderTransactions', 'N/A'),
        info.get('senatorTransactions', 'N/A')  # Assuming this field exists in the yfinance data
    )
    return prompt

def print_header(ticker):
    """Print formatted header"""
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "STOCK ANALYSIS: " + Fore.YELLOW + ticker + Style.RESET_ALL)
    print(Fore.CYAN + "=" * 80 + Style.RESET_ALL + "\n")

def format_analysis(analysis):
    """Format analysis output with color coding and organization"""
    formatted_analysis = analysis.replace("Short-Term Outlook", Fore.CYAN + Style.BRIGHT + "Short-Term Outlook" + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Long-Term Outlook", Fore.CYAN + Style.BRIGHT + "\nLong-Term Outlook" + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Key Considerations", Fore.CYAN + Style.BRIGHT + "\nKey Considerations" + Style.RESET_ALL)

    formatted_analysis = formatted_analysis.replace("Recommendation: Buy", "Recommendation: " + Back.GREEN + Fore.BLACK + " Buy " + Style.RESET_ALL)
    formatted_analysis = formatted_analysis.replace("Recommendation: Sell ", "Recommendation: " + Back.RED + Fore.BLACK + " Sell " + Style.RESET_ALL)
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

def main():
    parser = argparse.ArgumentParser(description='Analyze a stock for trading opportunities')
    parser.add_argument('ticker', help='Stock ticker symbol')
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print_header(ticker)
    
    print(Fore.YELLOW + "Fetching data for {0}...".format(ticker) + Style.RESET_ALL)
    data, info = get_stock_data(ticker)
    
    if data is None or info is None:
        return
    
    print(Fore.YELLOW + "Analyzing {0}...".format(ticker) + Style.RESET_ALL)
    prompt = generate_analysis_prompt(ticker, data, info)
    
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
        print(Fore.RED + "Error generating analysis: {0}".format(str(e)) + Style.RESET_ALL)

if __name__ == "__main__":
    init()  # Initialize colorama 
    if len(sys.argv) < 2:
        print(Fore.RED + "Please provide a ticker symbol. Usage: python3 {0} TICKER".format(sys.argv[0]) + Style.RESET_ALL)
    else:
        main()
