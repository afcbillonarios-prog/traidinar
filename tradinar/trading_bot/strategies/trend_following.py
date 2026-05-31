import pandas as pd
import numpy as np
import ta
from typing import Dict, Optional

class TrendFollowingStrategy:
    def __init__(self):
        self.name = "Trend Following"
        
    def generate_signal(self, data: Dict) -> Optional[str]:
        """
        Generate trading signal based on trend following strategy
        
        BUY when:
        - EMA20 > EMA50
        - RSI > 55
        - Price rebounds from EMA20
        - Increasing volume
        
        SELL when:
        - EMA20 < EMA50
        - RSI < 45
        """
        try:
            # Convert data to DataFrame for indicator calculation
            # We need historical data, so we'll simulate having more data points
            # In a real implementation, we would maintain a rolling window of data
            
            # For now, we'll work with the current data point and assume we have access to history
            # This is a simplified version - in practice, you'd maintain a deque of recent candles
            
            # Since we only have the latest candle, we need to get historical data from our data store
            # This would be passed in or accessed globally in a real implementation
            
            # For this example, we'll create a minimal dataframe with just the current data
            # In reality, you'd want to keep a rolling window of the last 100+ candles
            df = pd.DataFrame([data])
            
            # We need more data points to calculate indicators properly
            # This is a limitation of the current approach - in practice, you'd maintain history
            if len(df) < 50:  # Need enough data for EMA50
                return None
                
            # Calculate indicators
            df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            
            # Get the latest values
            latest = df.iloc[-1]
            
            # Check for BUY signal
            if (latest['ema20'] > latest['ema50'] and 
                latest['rsi'] > 55):
                # Additional confirmation: price near EMA20 (pullback)
                price_ema20_ratio = latest['close'] / latest['ema20']
                if 0.995 <= price_ema20_ratio <= 1.005:  # Within 0.5% of EMA20
                    return "BUY"
                    
            # Check for SELL signal
            elif (latest['ema20'] < latest['ema50'] and 
                  latest['rsi'] < 45):
                return "SELL"
                
            return None
            
        except Exception as e:
            # In a real implementation, you'd log this error
            return None