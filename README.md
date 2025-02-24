# 📈 Trading & SEC Filing Discord Bot

A powerful Discord bot designed for **day traders, swing traders, and cryptocurrency enthusiasts**.  
This bot utilizes AI and real-time data to fetch **stock watchlists** and **SEC filings**.

## 🚀 Features
- **`!watchlist`** → Fetches the **top AI-selected stocks** for trading.
- **`!sec [TICKER]`** → Retrieves **recent SEC filings** for a given stock.
- **Real-time stock data** via **Polygon.io API**.
- **SEC Filing integration** for **regulatory compliance tracking**.

---

## 🔧 Installation & Setup

### **1️⃣ Install Required Dependencies**
Make sure you have **Python 3.8+** installed, then install dependencies:

```sh
pip install -r requirements.txt
```

### **2️⃣ Create a `.env` File**
Create a file named **`.env`** in your project folder and add your API keys:

```
DISCORD_BOT_TOKEN=your_discord_bot_token_here
POLYGON_API_KEY=your_polygon_api_key_here
PREMARKET_CHANNEL_ID=your_discord_channel_id
```

### **3️⃣ Run the Bot**
```sh
python main.py
```

---

## 🤖 Bot Commands

| Command        | Description |
|---------------|------------|
| `!watchlist`  | Fetches **top AI-selected stocks** for day trading. |
| `!sec [TICKER]` | Retrieves **recent SEC filings** for a stock. |
| `!ping` | Checks if the bot is online. |

---

## 📡 API Usage
### **Polygon.io API** (Required)
- Used to fetch **stock prices, volume, and volatility**.
- Get a **free API key** at [Polygon.io](https://polygon.io/).

### **SEC Filings API**
- Fetches **company filings** directly from the **SEC EDGAR database**.

---

## ⚡ Deployment (Optional)
To deploy the bot using **Docker**:

1. Build the Docker image:
   ```sh
   docker build -t trading-bot .
   ```
2. Run the container:
   ```sh
   docker run -d --env-file .env trading-bot
   ```

---

## 🛠 Troubleshooting
### **🔴 Issue: API Errors**
- Make sure your **Polygon API key** is correct.
- Check if **SEC API is up** (SEC servers may experience delays).

### **⚠️ Issue: Bot Not Responding**
- Ensure the bot is **invited to the server**.
- Verify that `DISCORD_BOT_TOKEN` is correctly set in **`.env`**.

---

## 📜 License
This project is **open-source** and free to use under the **MIT License**.

---

## ✉️ Contact
For support or improvements, feel free to open an issue on GitHub. 🚀
