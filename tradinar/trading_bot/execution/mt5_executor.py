import MetaTrader5 as mt5
import logging
import time
from typing import Dict, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class MT5Executor:
    def __init__(self):
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            # Check if XAUT/USD is available
            symbol_info = mt5.symbol_info("XAUT/USD")
            if symbol_info is None:
                logger.error("XAUT/USD symbol not found in MT5")
                mt5.shutdown()
                return False
                
            # Enable the symbol if needed
            if not symbol_info.visible:
                if not mt5.symbol_select("XAUT/USD", True):
                    logger.error("Failed to select XAUT/USD symbol")
                    mt5.shutdown()
                    return False
                    
            self.initialized = True
            logger.info("MT5 initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False
            
    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            logger.info("MT5 connection closed")
            
    async def execute_order(self, symbol: str, action: str, volume: float, 
                           sl: float, tp: float, deviation: int = 10) -> bool:
        """
        Execute a trade order via MT5
        
        Args:
            symbol: Trading symbol (e.g., "XAUT/USD")
            action: "BUY" or "SELL"
            volume: Lot size
            sl: Stop loss price
            tp: Take profit price
            deviation: Price deviation in points
            
        Returns:
            True if order was successful, False otherwise
        """
        if not self.initialized:
            logger.error("MT5 not initialized")
            return False
            
        try:
            # Prepare order request
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol {symbol} not found")
                return False
                
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return False
                
            # Determine order type
            if action.upper() == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif action.upper() == "SELL":
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                logger.error(f"Invalid action: {action}")
                return False
                
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": 123456,  # Magic number to identify our bot's trades
                "comment": "XAUT USD AI Bot",
                "type_time": mt5.ORDER_TIME_GTC,  # Good till cancelled
                "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or cancel
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Order send failed: {mt5.last_error()}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return False
                
            logger.info(f"Order executed successfully: {action} {volume} {symbol} at {price}")
            logger.info(f"Order ticket: {result.order}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return False
            
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol"""
        if not self.initialized:
            return None
            
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None or len(positions) == 0:
                return None
                
            # Return the first position (we assume only one position per symbol)
            pos = positions[0]
            return {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'volume': pos.volume,
                'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit
            }
            
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return None
            
    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not self.initialized:
            return False
            
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False
                
            pos = position[0]
            
            # Prepare close request
            if pos.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(pos.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(pos.symbol).ask
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 10,
                "magic": 123456,
                "comment": "Close by AI Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Position close failed: {mt5.last_error()}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Position close failed: {result.retcode} - {result.comment}")
                return False
                
            logger.info(f"Position {ticket} closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False