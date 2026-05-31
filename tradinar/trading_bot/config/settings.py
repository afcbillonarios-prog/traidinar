import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Kraken API credentials
    KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY", "")
    KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET", "")
    
    # Telegram Bot credentials
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Trading parameters
    SYMBOL = "XAUT/USD"
    TIMEFRAME = "15m"
    RISK_PER_TRADE = 0.01  # 1% risk per trade
    MAX_DAILY_TRADES = 10
    MIN_CONFIDENCE_THRESHOLD = 0.65  # Minimum confidence to take a trade
    
    # MT5 parameters
    MT5_LOGIN = os.getenv("MT5_LOGIN", "")
    MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER = os.getenv("MT5_SERVER", "")
    
    # Model parameters
    MODEL_UPDATE_INTERVAL = 3600  # Update model every hour (in seconds)
    
    # Trading hours (UTC)
    # London session: 7-16 UTC
    # New York session: 12-21 UTC
    # Overlap: 12-16 UTC (most active)
    TRADING_SESSION_START = 7
    TRADING_SESSION_END = 21
    
    # Risk management
    MAX_POSITION_SIZE = 10.0  # Maximum lot size
    MIN_POSITION_SIZE = 0.01  # Minimum lot size