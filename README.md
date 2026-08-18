# Binance Trading Bot

Hey! I'm Thomas, I'm 29 years old, and I want to build a trading bot that can surf the market while I'm doing something more interesting.

This project will implement a trading bot and configuration to operate on Binance. I'm not entirely sure how I'll implement everything yet, but let's get started! 🚀

## How to Run

### 1. Create a Binance API Key

For the test environment, create an API key at:

https://testnet.binance.vision/

For production, create an API key through your Binance account.

> **⚠️ Important:** Never commit your API keys or `.env` file to the repository.

### 2. Configure Environment Variables

Create a `.env` file in the root of the project:

```env
BINANCE_API_KEY=your_public_api_key
BINANCE_SECRET_KEY=your_private_api_key

# true = Binance Testnet
# false = Binance Production
USE_TESTNET=true

# Trading pair
SYMBOL=SOL/USDT

# Candle timeframe
TIMEFRAME=1h

# Starting amount in USDT
# Only used in the practice/test environment.
AMOUNT_USDT=50
```

### Configuration

| Variable             | Description                                          | Example                |
| -------------------- | ---------------------------------------------------- | ---------------------- |
| `BINANCE_API_KEY`    | Binance API public key                               | `your_public_api_key`  |
| `BINANCE_SECRET_KEY` | Binance API secret key                               | `your_private_api_key` |
| `USE_TESTNET`        | Whether to use Binance Testnet instead of production | `true`                 |
| `SYMBOL`             | Trading pair                                         | `SOL/USDT`             |
| `TIMEFRAME`          | Trading/candle timeframe                             | `1h`                   |
| `AMOUNT_USDT`        | Starting amount for the bot                          | `50`                   |

> **Note:** The `TIMEFRAME` configuration is currently set to `1h`, but this will probably become configurable in the future.

### 3. Start the Project

Once the `.env` file is configured, start the project with Docker Compose:

```bash
docker compose up
```

That's it! The bot should now be running and ready to start surfing the market. 📈
