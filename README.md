# ByBit Trading Bot

A powerful, automated trading bot for ByBit featuring a modern Web UI, advanced backtesting, and strategy optimization capabilities.

## 🚀 Features

-   **Web Dashboard**: Real-time monitoring of bot status, balance, and active trades.
-   **Multiple Strategies**:
    -   **Mean Reversion**: RSI and Bollinger Bands based strategy.
    -   **Scalp**: High-frequency trading strategy with tight stop-losses.
-   **Backtesting Engine**: Test strategies against historical data to verify performance before going live.
-   **Strategy Optimization**: Automatically find the best parameters for your strategies.
-   **Risk Management**: Configurable Stop Loss and Take Profit settings.
-   **Docker Support**: Easy one-command deployment.

## 🛠️ Tech Stack

-   **Backend**: Python 3.11, FastAPI
-   **Frontend**: React, Vite, TailwindCSS
-   **Database**: DuckDB (for efficient data storage)

## 📋 Prerequisites

-   **Docker** & **Docker Compose** (Recommended)
-   **ByBit Account** (API Key & Secret required)

## ⚡ Quick Start (Docker)

The easiest way to run the bot is using Docker.

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd trading_bot
    ```

2.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and add your ByBit credentials:
    ```env
    BYBIT_API_KEY=your_api_key
    BYBIT_API_SECRET=your_api_secret
    BYBIT_DEMO=True  # Set to False for Mainnet
    ```

3.  **Run the Bot**:
    ```bash
    docker-compose up -d --build
    ```

4.  **Access the UI**:
    Open your browser and navigate to:
    [http://localhost](http://localhost)

## 🔧 Manual Setup (Development)

If you want to run the backend and frontend separately for development:

### Backend

1.  Navigate to the root directory.
2.  Create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  Run the server:
    ```bash
    python run.py
    ```
    Backend API will be available at `http://localhost:8000`.

### Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    Frontend will be available at `http://localhost:5173`.

## 📂 Project Structure

```
trading_bot/
├── backend/            # FastAPI Backend
│   ├── app/            # Application logic (Strategies, Core, API)
│   └── requirements.txt
├── frontend/           # React Frontend
│   ├── src/            # Components, Pages, Hooks
│   └── package.json
├── data/               # Database storage
├── logs/               # Application logs
├── Dockerfile          # Multi-stage Docker build
└── docker-compose.yml  # Docker orchestration
```

## ⚠️ Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.
