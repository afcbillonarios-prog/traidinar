import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, Tuple, Optional
import logging
import ta

logger = logging.getLogger(__name__)

class MetaFilterAI:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = [
            'rsi', 'atr', 'ema_distance', 'volume_spike', 
            'vwap_deviation', 'session_london', 'session_ny', 
            'momentum', 'breakout_strength'
        ]
        self.is_trained = False
        
    async def load_models(self):
        """Load pre-trained AI models"""
        try:
            model_path = "models/meta_filter_model.joblib"
            scaler_path = "models/meta_filter_scaler.joblib"
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.is_trained = True
                logger.info("Loaded pre-trained meta-filter AI model")
            else:
                logger.warning("Pre-trained models not found. Using rule-based filtering.")
                # Initialize with default rule-based parameters
                self.is_trained = False
                
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
            self.is_trained = False
            
    def extract_features(self, data: Dict, trend_signal: str, 
                        mean_reversion_signal: str, breakout_signal: str) -> np.ndarray:
        """Extract features for AI meta-filter"""
        try:
            # Convert data to DataFrame for calculations
            df = pd.DataFrame([data])
            
            # We need historical data for feature calculation
            # In practice, this would come from a rolling window of recent data
            # For this example, we'll simulate having sufficient data
            
            if len(df) < 20:
                # Return neutral features if insufficient data
                return np.zeros(len(self.feature_names))
                
            # Calculate features
            # RSI
            rsi = ta.momentum.rsi(df['close'], window=14).iloc[-1]
            
            # ATR
            atr = ta.volatility.average_true_range(
                df['high'], df['low'], df['close'], window=14
            ).iloc[-1]
            
            # EMA distance (normalized)
            ema20 = ta.trend.ema_indicator(df['close'], window=20).iloc[-1]
            ema50 = ta.trend.ema_indicator(df['close'], window=50).iloc[-1]
            ema_distance = (ema20 - ema50) / ema50 if ema50 != 0 else 0
            
            # Volume spike (ratio to average)
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            volume_spike = df['volume'].iloc[-1] / avg_volume if avg_volume != 0 else 1
            
            # VWAP deviation
            vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            vwap_deviation = (df['close'].iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1] if vwap.iloc[-1] != 0 else 0
            
            # Session features (simplified - based on UTC time)
            # In practice, you'd use actual timestamps
            hour_utc = 12  # Placeholder - would come from data timestamp
            session_london = 1 if 7 <= hour_utc < 16 else 0  # London session 7-16 UTC
            session_ny = 1 if 12 <= hour_utc < 21 else 0    # NY session 12-21 UTC
            
            # Momentum (price change over last 5 periods)
            momentum = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] if len(df) >= 5 and df['close'].iloc[-5] != 0 else 0
            
            # Breakout strength (how far price is from recent range)
            high_20 = df['high'].rolling(window=20).max().iloc[-1]
            low_20 = df['low'].rolling(window=20).min().iloc[-1]
            range_20 = high_20 - low_20
            if range_20 != 0:
                breakout_strength = (df['close'].iloc[-1] - low_20) / range_20  # 0 to 1
            else:
                breakout_strength = 0.5
            
            features = np.array([[
                rsi, atr, ema_distance, volume_spike, 
                vwap_deviation, session_london, session_ny, 
                momentum, breakout_strength
            ]])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros(len(self.feature_names))
    
    async def filter_signal(self, trend_signal: str, mean_reversion_signal: str, 
                           breakout_signal: str, data: Dict) -> Tuple[Optional[str], float]:
        """
        Use AI to filter and select the best signal from the three strategies
        
        Returns:
            Tuple of (signal, confidence) where signal is 'BUY', 'SELL', or None
        """
        try:
            # If we have a trained model, use it
            if self.is_trained and self.model is not None and self.scaler is not None:
                features = self.extract_features(data, trend_signal, mean_reversion_signal, breakout_signal)
                features_scaled = self.scaler.transform(features)
                
                # Get prediction probabilities
                probabilities = self.model.predict_proba(features_scaled)[0]
                
                # Class mapping: 0=NO_TRADE, 1=BUY, 2=SELL
                max_prob_idx = np.argmax(probabilities)
                confidence = probabilities[max_prob_idx]
                
                if max_prob_idx == 0:  # NO_TRADE
                    return None, confidence
                elif max_prob_idx == 1:  # BUY
                    return "BUY", confidence
                else:  # SELL
                    return "SELL", confidence
            else:
                # Rule-based fallback when AI model is not available
                return self._rule_based_filter(trend_signal, mean_reversion_signal, breakout_signal, data)
                
        except Exception as e:
            logger.error(f"Error in AI filtering: {e}")
            # Fallback to rule-based
            return self._rule_based_filter(trend_signal, mean_reversion_signal, breakout_signal, data)
    
    def _rule_based_filter(self, trend_signal: str, mean_reversion_signal: str, 
                          breakout_signal: str, data: Dict) -> Tuple[Optional[str], float]:
        """
        Rule-based signal filtering when AI model is not available
        """
        # Count signals
        signals = [s for s in [trend_signal, mean_reversion_signal, breakout_signal] if s is not None]
        
        if not signals:
            return None, 0.0
            
        # If all signals agree, high confidence
        if len(set(signals)) == 1:
            return signals[0], 0.8
            
        # If there's disagreement, use priority: Trend > Breakout > Mean Reversion
        # This is based on the assumption that trend following is most reliable
        priority_order = ["Trend Following", "Breakout Momentum", "Mean Reversion"]
        strategy_map = {
            "Trend Following": trend_signal,
            "Breakout Momentum": breakout_signal,
            "Mean Reversion": mean_reversion_signal
        }
        
        for strategy_name in priority_order:
            signal = strategy_map[strategy_name]
            if signal is not None:
                return signal, 0.6  # Medium confidence for rule-based
                
        # Should not reach here, but just in case
        return signals[0], 0.5
    
    def get_active_strategy_name(self) -> str:
        """Get the name of the currently active strategy (for logging)"""
        # In a more sophisticated implementation, this would track which strategy was selected
        return "AI Meta Filter"
