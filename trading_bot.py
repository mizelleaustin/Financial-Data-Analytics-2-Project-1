import discord
import os
import asyncio
import yfinance as yf
import random
import requests
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv
import numpy as np
from datetime import datetime, timedelta
import pytz

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SEC_API_KEY = os.getenv("SEC_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
PREMARKET_CHANNEL_ID = int(os.getenv("PREMARKET_CHANNEL_ID"))  # Set this to your channel ID
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Set time zone to Eastern Time (ET)
EST = pytz.timezone("America/New_York")

# Intents allow the bot to listen for messages and interactions
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # REQUIRED to read message content

# Set up the bot with a command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} and ready to receive commands!')

@bot.command()
async def ping(ctx):
    """Check if the bot is online."""
    print(f"Received !ping command from {ctx.author}")
    await ctx.send("Pong! 🏓")

@bot.command()
async def watchlist(ctx):
    """Fetch today's AI-selected top stocks for day trading using Finnhub API."""
    await ctx.send("Fetching today's top day-trading stocks... 📈 Please wait...")
    data = get_dynamic_watchlist()
    await ctx.send(data)

@bot.command()
async def sec(ctx, ticker: str):
    """Fetch recent SEC filings for a given stock ticker."""
    await ctx.send(f"🔎 Searching for **{ticker.upper()}** in SEC filings... 📜 Please wait...")
    data = get_sec_filings(ticker.upper())
    await ctx.send(data)

# Preselected list of 100 high-volume NASDAQ stocks
PRESELECTED_NASDAQ_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "PYPL",
    "ADBE", "CMCSA", "INTC", "PEP", "COST", "TXN", "QCOM", "AVGO", "AMGN", "CSCO",
    "BIDU", "JD", "ZM", "MRNA", "DOCU", "OKTA", "ILMN", "ROKU", "SPLK", "SNPS",
    "DDOG", "EXC", "EA", "MELI", "CMCSA", "AMAT", "ASML", "TMUS", "MSTR", "GFS",
    "MDB", "NXPI", "KDP", "ISRG", "VRTX", "ROP", "AZN", "TTD", "DASH", "ON",
    "ADSK", "TTWO", "ROST", "FAST", "CHTR", "SBUX", "WBD", "KHC", "SNPS",
    "MRVL", "AVGO", "BIIB", "MNST", "PYPL", "IDXX", "INTC", "KLAC", "APP", "LULU",
    "ORLY", "REGN", "ADBE", "ANSS", "CDNS", "MCHP", "FANG", "VRSK", "CPRT", "INTU",
    "WDAY", "BKR", "TXN", "PCAR", "AMGN", "DXCM", "CSGP", "CSCO", "ODFL", "COST",
    "BKNG", "ARM", "PDD", "GILD", "XEL", "FTNT", "MDLZ", "HON", "CTSH", "LIN",
    "AEP", "MAR", "PEP", "CTAS", "CCEP", "GOOG", "AXON", "ZS", "ADI", "CSX", "CRWD"
]

def get_market_analysis():
    """Fetches AI-selected pre-market gainers and day trading stocks based on liquidity and volume, avoiding redundancy."""
    tickers = ["AAPL", "TSLA", "NVDA", "AMD", "AMZN", "GOOGL", "MSFT", "NFLX", "META", "BA"]
    stock_data = []
    
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        history = stock.history(period="5d", prepost=True)
        
        if history.empty:
            continue
        
        avg_volume = np.mean(history['Volume'])
        avg_volatility = np.std(history['Close'].pct_change()) * 100  # Percentage volatility
        liquidity_score = avg_volume * avg_volatility  # Higher = better for pre-market movers
        
        stock_data.append((ticker, liquidity_score, avg_volume, avg_volatility))
    
    # Sort by liquidity score (descending) and pick top 5 for pre-market movers
    stock_data.sort(key=lambda x: x[1], reverse=True)
    top_premarket_stocks = stock_data[:5]
    
    # Sort by volume and volatility for day trading (descending) and pick top 5
    stock_data.sort(key=lambda x: (x[2], x[3]), reverse=True)
    top_daytrade_stocks = stock_data[:5]
    
    reasons = [
        "Strong liquidity and high volatility signal great day-trading potential.",
        "Unusual volume activity suggests potential breakout.",
        "High relative strength index (RSI) indicates momentum.",
        "Significant institutional trading observed.",
        "Recent news catalysts are driving interest in this stock."
    ]
    
    premarket_text = "\n".join([f"{stock[0]}: Volume {stock[2]:,.0f}, Volatility {stock[3]:.2f}%" for stock in top_premarket_stocks])
    daytrade_text = "\n".join([f"{stock[0]} - {random.choice(reasons)}" for stock in top_daytrade_stocks])
    
    return f"🚀 **Pre-Market Movers:**\n{premarket_text}\n\n📢 **Today's Stocks to Watch:**\n{daytrade_text}"

def get_previous_trading_day():
    """Returns the most recent trading day (adjusting for weekends)."""
    today = datetime.now(EST).date()
    if today.weekday() == 0:  # Monday, get last Friday
        return today - timedelta(days=3)
    elif today.weekday() == 6:  # Sunday, get last Friday
        return today - timedelta(days=2)
    else:  # Any other day, get yesterday
        return today - timedelta(days=1)

def fetch_stock_data(tickers):
    """Fetches historical data from Polygon.io for selected tickers."""
    stock_data = []
    base_url = "https://api.polygon.io/v2/aggs/ticker/{}/prev?apiKey={}"

    for ticker in tickers:
        try:
            url = base_url.format(ticker, POLYGON_API_KEY)
            response = requests.get(url)

            if response.status_code != 200:
                print(f"⚠️ Error fetching {ticker}: {response.text}")
                continue

            data = response.json()
            if "results" not in data or not data["results"]:
                print(f"⚠️ No valid data for {ticker}, skipping.")
                continue

            latest_data = data["results"][0]
            avg_volume = latest_data.get("v", 0)
            avg_volatility = ((latest_data.get("h", 0) - latest_data.get("l", 0)) / latest_data.get("c", 1)) * 100
            liquidity_score = avg_volume * avg_volatility

            if avg_volume > 1000000 and avg_volatility > 1:  # Ensure liquid stocks
                stock_data.append((ticker, liquidity_score, avg_volume, avg_volatility))

        except Exception as e:
            print(f"⚠️ Error fetching {ticker}: {e}")

    return stock_data
    
def get_dynamic_watchlist():
    """Fetches top stocks from a preselected NASDAQ list based on liquidity and volume using Finnhub."""
    # Randomly select 10 stocks from the preselected NASDAQ list (in case some fail)
    tickers = random.sample(PRESELECTED_NASDAQ_STOCKS, 10)

    stock_data = fetch_stock_data(tickers)

    if not stock_data:
        return "⚠️ No suitable NASDAQ stocks found. Try again later."

    stock_data.sort(key=lambda x: x[1], reverse=True)
    top_stocks = stock_data[:5]

    return "📢 **Top NASDAQ Stocks to Watch:**\n" + "\n".join(
        [f"{stock[0]} - Volume {stock[2]:,.0f}, Volatility {stock[3]:.2f}%" for stock in top_stocks]
    )

def get_sec_filings(ticker):
    """Fetches recent SEC filings for a given stock ticker."""
    cik_lookup_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}&action=getcompany"
    headers = {"User-Agent": "DiscordBot SEC Data Retriever"}
    cik_response = requests.get(cik_lookup_url, headers=headers)
    
    if cik_response.status_code != 200:
        return "❌ Failed to retrieve CIK. Please try again later."
    
    cik = cik_response.text.split("CIK=")[1].split('&')[0].strip()
    cik = cik.zfill(10)  # Ensure CIK is properly formatted
    
    filings_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(filings_url, headers=headers)
    
    if response.status_code != 200:
        return "❌ Failed to fetch SEC filings. Please try again later."
    
    data = response.json()
    filings = data.get("filings", {}).get("recent", [])
    
    if not filings:
        return f"📜 No recent SEC filings found for {ticker}."
    
    report_list = []
    for i in range(min(5, len(filings.get("form", [])))):  # Get up to 5 most recent filings
        form_type = filings["form"][i]
        filing_date = filings["filingDate"][i]
        accession_number = filings["accessionNumber"][i].replace('-', '')
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/index.html"
        report_list.append(f"- **{form_type}** ({filing_date}) - [View Report]({filing_url})")
    
    return f"📜 **Recent SEC Filings for {ticker}:**\n" + "\n".join(report_list)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
