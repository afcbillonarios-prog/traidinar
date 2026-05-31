#!/usr/bin/env python3
"""
XAUT/USD Trading Bot - Main Entry Point
Multi-strategy AI-powered trading system for XAUT/USD on Kraken
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Optional

# Import local modules
from data.kraken_websocket import KrakenWebSocket
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.breakout_momentum import BreakoutMomentumStrategy
from ai.meta_filter import MetaFilterAI
from execution.mt5_executor import MT5Executor
from risk.risk_manager import RiskManager
from telegram.signal_bot import TelegramSignalBot
from config.settings import Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.settings = Settings()
        self.running = False
        
        # Initialize components
        self.kraken_ws = KrakenWebSocket(self.settings.KRAKEN_API_KEY, self.settings.KRAKEN_API_SECRET)
        self.trend_strategy = TrendFollowingStrategy()
        self.mean_reversion_strategy = MeanReversionStrategy()
        self.breakout_strategy = BreakoutMomentumStrategy()
        self.meta_filter = MetaFilterAI()
        self.mt5_executor = MT5Executor()
        self.risk_manager = RiskManager()
        self.telegram_bot = TelegramSignalBot(self.settings.TELEGRAM_BOT_TOKEN, self.settings.TELEGRAM_CHAT_ID)
        
        # Data storage
        self.latest_data = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing XAUT/USD Trading Bot...")
        
        # Initialize MT5 connection
        if not self.mt5_executor.initialize():
            logger.error("Failed to initialize MT5 connection")
            return False
            
        # Initialize Kraken WebSocket
        await self.kraken_ws.connect()
        
        # Load AI models
        await self.meta_filter.load_models()
        
        logger.info("Trading Bot initialized successfully")
        return True
        
    async def process_market_data(self, data: Dict):
        """Process incoming market data and generate trading signals"""
        try:
            # Update latest data
            self.latest_data = data
            
            # Calculate indicators for all strategies
            trend_signal = self.trend_strategy.generate_signal(data)
            mean_reversion_signal = self.mean_reversion_strategy.generate_signal(data)
            breakout_signal = self.breakout_strategy.generate_signal(data)
            
            # Apply AI meta filter to determine best strategy
            final_signal, confidence = await self.meta_filter.filter_signal(
                trend_signal, mean_reversion_signal, breakout_signal, data
            )
            
            # If signal is valid, process it
            if final_signal and confidence > self.settings.MIN_CONFIDENCE_THRESHOLD:
                # Check risk parameters
                if self.risk_manager.can_trade(final_signal, data):
                    # Calculate position size
                    position_size = self.risk_manager.calculate_position_size(
                        final_signal, data, self.settings.RISK_PER_TRADE
                    )
                    
                    # Set stop loss and take profit
                    sl, tp = self.risk_manager.calculate_sl_tp(final_signal, data)
                    
                    # Execute trade via MT5
                    order_result = await self.mt5_executor.execute_order(
                        symbol="XAUT/USD",
                        action=final_signal,
                        volume=position_size,
                        sl=sl,
                        tp=tp
                    )
                    
                    if order_result:
                        # Send Telegram notification
                        await self.telegram_bot.send_signal(
                            action=final_signal,
                            symbol="XAUT/USD",
                            price=data['close'],
                            sl=sl,
                            tp=tp,
                            volume=position_size,
                            confidence=confidence,
                            strategy_used=self.meta_filter.get_active_strategy_name()
                        )
                        
                        logger.info(f"Executed {final_signal} order for XAUT/USD at {data['close']} "
                                  f"with SL={sl}, TP={tp}, Volume={position_size}, Confidence={confidence:.2f}")
                    else:
                        logger.warning("Failed to execute order")
                        
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            
    async def run(self):
        """Main trading loop"""
        self.running = True
        logger.info("Starting trading bot...")
        
        # Send startup notification
        await self.telegram_bot.send_message("🤖 XAUT/USD Trading Bot Started")
        
        try:
            while self.running:
                # Wait for new data from WebSocket
                data = await self.kraken_ws.get_latest_data()
                if data:
                    await self.process_market_data(data)
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down trading bot...")
        self.running = False
        
        # Close connections
        await self.kraken_ws.disconnect()
        self.mt5_executor.shutdown()
        await self.telegram_bot.send_message("🛑 XAUT/USD Trading Bot Stopped")
        
        logger.info("Trading bot shut down successfully")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot = TradingBot()
    
    if await bot.initialize():
        await bot.run()
    else:
        logger.error("Failed to initialize trading bot")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())