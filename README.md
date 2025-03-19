# Binance and Gate.io Arbitrage Trading Bot

This repository contains a trading bot that performs arbitrage between the Binance and Gate.io exchanges, analyzing price differences and fees to find profitable opportunities. The bot also sends notifications via Telegram whenever a profitable arbitrage opportunity is found.

## Features

- **Real-time price fetching**: Fetches live market data from Binance and Gate.io for supported trading pairs.
- **Arbitrage strategy**: Compares price differences between Binance and Gate.io for each trading pair.
- **Fee calculation**: Includes withdrawal fees from both exchanges to accurately calculate profit margins.
- **Telegram notifications**: Sends updates to a Telegram channel about profitable opportunities.
- **Blacklisting pairs**: Excludes specific trading pairs (e.g., `QIUSDT`, `BIFIUSDT`) from the arbitrage process.
- **Customizable parameters**: Set minimum profit percentages and the margin difference required to trigger Telegram alerts.

## Requirements

- Python 3.7+.
- Required Python libraries:
  ```bash
  pip install aiohttp binance sympy telebot
