import requests
import logging
import asyncio
import aiohttp
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TelegramSignalBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, message: str) -> bool:
        """
        Send a message via Telegram bot
        
        Args:
            message: Text message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info("Telegram message sent successfully")
                            return True
                        else:
                            logger.error(f"Telegram API error: {result}")
                            return False
                    else:
                        logger.error(f"HTTP error sending Telegram message: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
            
    async def send_signal(self, action: str, symbol: str, price: float, 
                         sl: float, tp: float, volume: float, 
                         confidence: float, strategy_used: str) -> bool:
        """
        Send trading signal via Telegram
        
        Args:
            action: 'BUY' or 'SELL'
            symbol: Trading symbol
            price: Entry price
            sl: Stop loss price
            tp: Take profit price
            volume: Position size in lots
            confidence: Signal confidence (0-1)
            strategy_used: Name of strategy that generated the signal
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Format message with emojis and clear formatting
            emoji = "🟢" if action.upper() == "BUY" else "🔴"
            action_text = "BUY" if action.upper() == "BUY" else "SELL"
            
            message = f"""
{emoji} <b>XAUT/USD Trading Signal</b> {emoji}

<b>Action:</b> {action_text}
<b>Symbol:</b> {symbol}
<b>Entry Price:</b> {price:.2f}
<b>Stop Loss:</b> {sl:.2f}
<b>Take Profit:</b> {tp:.2f}
<b>Volume:</b> {volume} lots
<b>Confidence:</b> {confidence:.1%}
<b>Strategy:</b> {strategy_used}
<b>Time:</b> {self._get_current_time()}
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error formatting/sending Telegram signal: {e}")
            return False
            
    def _get_current_time(self) -> str:
        """Get current time formatted as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
    async def test_connection(self) -> bool:
        """Test connection to Telegram Bot API"""
        try:
            url = f"{self.base_url}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info("Telegram bot connection test successful")
                            return True
                    logger.error("Telegram bot connection test failed")
                    return False
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False