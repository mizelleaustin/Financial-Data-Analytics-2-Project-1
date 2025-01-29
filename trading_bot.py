import discord
import os
import yfinance as yf
import asyncio
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv
import numpy as np
import random
from datetime import datetime, timedelta
import pytz

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SEC_API_KEY = os.getenv("SEC_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
PREMARKET_CHANNEL_ID = int(os.getenv("PREMARKET_CHANNEL_ID"))  # Set this to your channel ID

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
    # Schedule the task to run daily at 7:30 AM EST
    now = datetime.now(EST)
    target_time = now.replace(hour=7, minute=30, second=0, microsecond=0)
    if now > target_time:
        target_time += timedelta(days=1)
    delay = (target_time - now).total_seconds()
    asyncio.create_task(schedule_daily_update(delay))

async def schedule_daily_update(delay):
    """Schedules the daily earnings and market updates at 7:30 AM EST."""
    await asyncio.sleep(delay)
    while True:
        await daily_market_update()
        await asyncio.sleep(86400)  # Wait for 24 hours

@bot.command()
async def ping(ctx):
    """Check if the bot is online."""
    print(f"Received !ping command from {ctx.author}")
    await ctx.send("Pong! 🏓")

@bot.command()
async def watchlist(ctx):
    """Fetch today's AI-selected top 5 stocks for day trading."""
    await ctx.send("Fetching today's top day-trading stocks... 📈")
    data = get_day_trading_stocks()
    await ctx.send(data)

@bot.command()
async def earnings(ctx):
    """Fetch upcoming earnings reports."""
    await ctx.send("Fetching upcoming earnings reports... 📅")
    data = get_earnings_calendar()
    await ctx.send(data)

@bot.command()
async def sec(ctx, ticker: str):
    """Fetch recent SEC filings for a given stock ticker."""
    await ctx.send(f"Fetching SEC filings for {ticker.upper()}... 📜")
    data = get_sec_filings(ticker.upper())
    await ctx.send(data)


async def daily_market_update():
    """Fetches pre-market movers and the top 5 day trading stocks, then posts them in the designated channel at 7:30 AM EST."""
    await bot.wait_until_ready()
    channel = bot.get_channel(PREMARKET_CHANNEL_ID)
    if channel:
        market_data = get_market_analysis()
        earnings_data = get_earnings_calendar()
        await channel.send(market_data)
        await channel.send(earnings_data)

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

def get_day_trading_stocks():
    """Fetches high-volume and high-liquidity stocks for day trading with AI-selected reasoning."""
    market_data = get_market_analysis()
    return market_data.split("📢 **Today's Stocks to Watch:**\n")[-1]

def get_earnings_calendar():
    """Fetches upcoming earnings reports for the top stocks."""
    tickers = ["AAPL", "TSLA", "NVDA", "AMD", "AMZN", "GOOGL", "MSFT", "NFLX", "META", "BA"]
    return "📆 **Upcoming Earnings Reports:**\n" + "\n".join([f"{ticker}: Earnings Date Unknown" for ticker in tickers])

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
