import pandas as pd
import numpy as np
import ta
from typing import Dict, Optional

class MeanReversionStrategy:
    def __init__(self):
        self.name = "Mean Reversion"
        
    def generate_signal(self, data: Dict) -> Optional[str]:
        """
        Generate trading signal based on mean reversion strategy
        
        BUY when:
        - Price touches lower Bollinger Band
        - RSI < 30 (oversold)
        - Price below VWAP
        
        SELL when:
        - Price touches upper Bollinger Band
        - RSI > 70 (overbought)
        - Price above VWAP
        """
        try:
            # Convert data to DataFrame for indicator calculation
            # We need historical data for Bollinger Bands and VWAP
            df = pd.DataFrame([data])
            
            # We need sufficient data for indicators
            if len(df) < 20:  # Need enough data for Bollinger Bands
                return None
                
            # Calculate indicators
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb_indicator.bollinger_hband()
            df['bb_lower'] = bb_indicator.bollinger_lband()
            df['bb_middle'] = bb_indicator.bollinger_mavg()
            
            # RSI
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            
            # VWAP approximation (simplified)
            # In reality, VWAP requires cumulative volume and price*volume
            # For simplicity, we'll use a rolling average as approximation
            df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            
            # Get latest values
            latest = df.iloc[-1]
            
            # Check for BUY signal
            if (latest['close'] <= latest['bb_lower'] and 
                latest['rsi'] < 30 and 
                latest['close'] < latest['vwap']):
                return "BUY"
                
            # Check for SELL signal
            elif (latest['close'] >= latest['bb_upper'] and 
                  latest['rsi'] > 70 and 
                  latest['close'] > latest['vwap']):
                return "SELL"
                
            return None
            
        except Exception as e:
            # In a real implementation, you'd log this error
            return None