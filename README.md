# ByBit Trading Bot

A Python-based trading bot for ByBit that uses a Simple Moving Average (SMA) crossover strategy.

## Features
- **Strategy**: SMA Crossover (Short/Long windows).
- **Exchange**: ByBit (Demo & Mainnet support).
- **Safety**: Simulation mode enabled by default.
- **Logging**: Detailed logs in `trading_bot.log`.

## Prerequisites
- Python 3.8+
- ByBit Account (Demo recommended for development)

## Setup

1. **Clone/Download** the repository.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**:
   - Create a `.env` file (or rename `.env.example` to `.env`).
   - Add your ByBit API credentials:
     ```env
     BYBIT_API_KEY=your_api_key
     BYBIT_API_SECRET=your_api_secret
     BYBIT_DEMO=True
     ```

## Running the Bot

To start the bot, run:

```bash
python bot.py
```

## Monitoring
- The bot outputs logs to the console.
- Detailed logs are saved to `trading_bot.log`.
- Errors are saved to `error_log.txt`.

## UI
Currently, this bot is a **Command Line Interface (CLI)** application. It does not have a graphical user interface (UI).
