import pandas as pd
import numpy as np
import ta
from typing import Dict, Optional

class BreakoutMomentumStrategy:
    def __init__(self):
        self.name = "Breakout Momentum"
        
    def generate_signal(self, data: Dict) -> Optional[str]:
        """
        Generate trading signal based on breakout momentum strategy
        
        BUY when:
        - Price breaks above 15-period high
        - Volume is significantly above average
        - ATR is expanding (increasing volatility)
        
        SELL when:
        - Price breaks below 15-period low
        - Volume is significantly above average
        - ATR is expanding
        """
        try:
            # Convert data to DataFrame for indicator calculation
            # We need historical data for range calculation
            df = pd.DataFrame([data])
            
            # We need sufficient data for indicators
            if len(df) < 20:  # Need enough data for 15-period high/low
                return None
                
            # Calculate indicators
            # 15-period high and low
            df['high_15'] = df['high'].rolling(window=15).max()
            df['low_15'] = df['low'].rolling(window=15).min()
            
            # Average volume
            df['avg_volume'] = df['volume'].rolling(window=15).mean()
            
            # ATR for volatility measurement
            df['atr'] = ta.volatility.average_true_range(
                df['high'], df['low'], df['close'], window=14
            )
            
            # ATR change (to detect expansion)
            df['atr_change'] = df['atr'].pct_change()
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # Check for BUY signal (breakout above resistance)
            if (latest['close'] > latest['high_15'] and  # Price broke above 15-period high
                latest['volume'] > latest['avg_volume'] * 1.5 and  # Volume 50% above average
                latest['atr_change'] > 0):  # ATR expanding
                return "BUY"
                
            # Check for SELL signal (breakdown below support)
            elif (latest['close'] < latest['low_15'] and  # Price broke below 15-period low
                  latest['volume'] > latest['avg_volume'] * 1.5 and  # Volume 50% above average
                  latest['atr_change'] > 0):  # ATR expanding
                return "SELL"
                
            return None
            
        except Exception as e:
            # In a real implementation, you'd log this error
            return None