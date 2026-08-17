Hey! i'm Thomas i'm 29 years old and i want to make a trading bot that surf the market while i'm doing something more interesing. 

This project will implement a bot and config to operates into binance. im not quiet sure how i will implement this but let start! 


## How to Run this project

1. create an api key in https://testnet.binance.vision/ for test environment or an api key in Binance for production 

2. Create a .env and set the following parameters:

BINANCE_API_KEY=your_public_api_key
BINANCE_SECRET_KEY=yout_private_api_key
USE_TESTNET=true for test false for production
SYMBOL=example 'SOL/USDT' 
TIMEFRAME= 1h => Will changfge in the future probably
AMOUNT_USDT= 50 => yout start amount of dollars. Only available in practice. I cannot print money :c

3. docker compose up