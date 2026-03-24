# CryptoPortfolioManager

A lightweight Python tool suite for crypto portfolio management: data ingestion, analysis, risk checks, predictions, investment mix recommendations, rebalancing hints, and reports.

## Project overview
- Fetches historical data for popular cryptocurrencies (via CoinGecko).
- Stores data in SQLite and CSV.
- Computes returns, volatility, correlation, covariance.
- Runs risk detection and 30-day future return forecasts.
- Creates optimized allocation by risk profile (conservative/balanced/aggressive).
- Offers stress test scenarios + rebalance action planning.
- Sends email alerts when risk thresholds are breached.
- Includes a Streamlit dashboard (`app.py`) for interactive use.

## Prerequisites
- Python 3.8+
- `pip` installed

## Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/youruser/CryptoPortfolioManager.git
   cd CryptoPortfolioManager
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   # source venv/bin/activate      # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` file in project root with values:
   ```text
   CG_API_KEY=<your_coin_gecko_key>
   EMAIL_SENDER=<sender_email>
   EMAIL_PASSWORD=<email_password>
   EMAIL_RECEIVER=<receiver_email>
   ```

## Usage
### CLI pipeline
```bash
python main.py
```

### Streamlit UI
```bash
streamlit run app.py
```

## Configuration
- `config.py` holds settings:
  - coins list, API endpoints, thresholds, file and folder paths.

## Output folders
- `reports/` for output CSV reports
- `analysis/` for intermediate metrics
- `visualisation/` for graphs

## Notes
- Ensure internet access for CoinGecko API requests.
- Email alert requires valid SMTP account credentials.
