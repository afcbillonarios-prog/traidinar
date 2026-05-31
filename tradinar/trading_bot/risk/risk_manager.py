import logging
import numpy as np
import ta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_per_trade: float = 0.01, max_daily_trades: int = 10):
        """
        Initialize risk manager
        
        Args:
            max_risk_per_trade: Maximum risk per trade as fraction of account (0.01 = 1%)
            max_daily_trades: Maximum number of trades per day
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_trades = max_daily_trades
        self.daily_trades = 0
        self.last_trade_date = None
        
    def can_trade(self, signal: str, data: Dict) -> bool:
        """
        Check if we can take a trade based on risk parameters
        
        Args:
            signal: Trading signal ('BUY' or 'SELL')
            data: Market data dictionary
            
        Returns:
            True if trade is allowed, False otherwise
        """
        try:
            # Reset daily trade counter if new day
            # In practice, you'd use actual date from data timestamp
            # For simplicity, we'll just check if we've exceeded daily limit
            
            if self.daily_trades >= self.max_daily_trades:
                logger.warning(f"Daily trade limit reached: {self.daily_trades}")
                return False
                
            # Additional checks could go here:
            # - News events
            # - Market volatility too high/low
            # - Correlation with existing positions
            # - Account margin level
            
            return True
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            return False
            
    def calculate_position_size(self, signal: str, data: Dict, 
                               risk_per_trade: float) -> float:
        """
        Calculate position size based on risk percentage and stop loss distance
        
        Args:
            signal: Trading signal ('BUY' or 'SELL')
            data: Market data dictionary
            risk_per_trade: Risk per trade as fraction of account (0.01 = 1%)
            
        Returns:
            Position size in lots
        """
        try:
            # In a real implementation, you'd get account balance from MT5
            # For this example, we'll assume a fixed account size
            account_balance = 10000  # $10,000 account
            
            # Calculate stop loss distance in price units
            sl_price, tp_price = self.calculate_sl_tp(signal, data)
            current_price = data['close']
            
            if signal.upper() == "BUY":
                sl_distance = current_price - sl_price
            else:  # SELL
                sl_distance = sl_price - current_price
                
            if sl_distance <= 0:
                logger.warning("Invalid stop loss distance")
                return 0.01  # Minimum lot size
                
            # Calculate position size
            # Risk amount = account_balance * risk_per_trade
            # Position size = risk_amount / (sl_distance * pip_value)
            # For simplicity, we'll assume 1 pip = 0.01 for XAUT/USD
            risk_amount = account_balance * risk_per_trade
            pip_value = 0.01  # $0.01 per pip for XAUT/USD (adjust based on actual contract size)
            
            # Position size in lots
            position_size = risk_amount / (sl_distance / pip_value)
            
            # Apply minimum and maximum limits
            min_lot = 0.01
            max_lot = 10.0
            
            position_size = max(min_lot, min(position_size, max_lot))
            
            # Round to 2 decimal places
            position_size = round(position_size, 2)
            
            logger.info(f"Calculated position size: {position_size} lots "
                       f"(Risk: {risk_amount}, SL distance: {sl_distance})")
                       
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Return minimum lot size on error
            
    def calculate_sl_tp(self, signal: str, data: Dict) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels based on ATR
        
        Args:
            signal: Trading signal ('BUY' or 'SELL')
            data: Market data dictionary
            
        Returns:
            Tuple of (stop_loss, take_profit) prices
        """
        try:
            # We need historical data to calculate ATR properly
            # In practice, this would come from our data storage
            # For this example, we'll simulate having sufficient data
            
            current_price = data['close']
            
            # Default ATR multiplier values
            atr_multiplier_sl = 1.5
            atr_multiplier_tp = 3.0
            
            # In a real implementation, we'd calculate ATR from historical data
            # For now, we'll use a simplified approach based on price range
            # This is NOT accurate - in practice, you'd maintain historical data
            high_price = data.get('high', current_price)
            low_price = data.get('low', current_price)
            
            # Simple range-based ATR approximation (poor substitute)
            # In reality, you'd use ta.volatility.average_true_range() on historical data
            price_range = high_price - low_price
            atr_approx = price_range  # Very rough approximation
            
            if signal.upper() == "BUY":
                sl = current_price - (atr_approx * atr_multiplier_sl)
                tp = current_price + (atr_approx * atr_multiplier_tp)
            else:  # SELL
                sl = current_price + (atr_approx * atr_multiplier_sl)
                tp = current_price - (atr_approx * atr_multiplier_tp)
                
            logger.info(f"Calculated SL/TP for {signal}: SL={sl:.2f}, TP={tp:.2f}")
            return sl, tp
            
        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            # Return default SL/TP on error
            current_price = data['close']
            if signal.upper() == "BUY":
                return current_price * 0.99, current_price * 1.02  # 1% SL, 2% TP
            else:
                return current_price * 1.01, current_price * 0.98  # 1% SL, 2% TP
                
    def update_daily_trades(self):
        """Increment daily trade counter"""
        self.daily_trades += 1
        logger.info(f"Daily trade count: {self.daily_trades}")
        
    def reset_daily_counter(self):
        """Reset daily trade counter (call at start of each day)"""
        self.daily_trades = 0
        logger.info("Daily trade counter reset")