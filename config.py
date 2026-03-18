import os
from dotenv import load_dotenv

# Load the variables from .env into the system environment
load_dotenv()

# ===============================
# API Configuration (Secure)
# ===============================
API_KEY = os.getenv("CG_API_KEY")
BASE_URL = "https://api.coingecko.com/api/v3"

# ===============================
# Email Configuration (Secure)
# ===============================pppppppp
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# ===============================
# Database & Folder Settings
# ===============================
DB_NAME = "crypto_manager.db"
CSV = "crypto_data.csv"
REPORT_DIR = "reports"
VISUAL_DIR = "visualisation"
ANALYSIS_DIR = "analysis"

DAYS = "365"

COINS = [
    "bitcoin", "ethereum", "binancecoin", "solana", "ripple",
    "cardano", "dogecoin", "polkadot", "matic-network", "litecoin"
]

# Risk Thresholds
VOLATILITY_THRESHOLD = 0.08 
PRICE_DROP_THRESHOLD = -0.10
# Financial Settings
TRADING_FEE = 0.001  # 0.1% fee per trade
MIN_ORDER_VALUE = 10.0  # Minimum $10 per coin
SLIPPAGE_BUFFER = 0.005 # 0.5% buffer for price movements

# Rebalancing settings
REBALANCE_THRESHOLD = 0.05 # 5% drift triggers an alert