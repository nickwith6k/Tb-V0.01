import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def send_telegram_message(bot_token: str, chat_id: int, text: str, parse_mode: str = "Markdown", 
                         reply_markup: Optional[Dict[str, Any]] = None) -> bool:
    """Send message via Telegram Bot API with optional keyboard"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def answer_callback_query(bot_token: str, callback_query_id: str, text: str = "") -> bool:
    """Answer callback query to remove loading state"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
        
        payload = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")
        return False

def create_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """Create inline keyboard markup"""
    return {
        "inline_keyboard": buttons
    }

def create_button(text: str, callback_data: str) -> Dict[str, str]:
    """Create inline keyboard button"""
    return {
        "text": text,
        "callback_data": callback_data
    }

def format_price(price: Optional[float], decimals: int = 2) -> str:
    """Format price with specified decimals"""
    if price is None:
        return "N/A"
    return f"{price:.{decimals}f}"

def format_percentage(percent: Optional[float]) -> str:
    """Format percentage"""
    if percent is None:
        return "N/A"
    return f"{percent:.1f}%"

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    try:
        if '/' not in symbol:
            return False
        
        base, quote = symbol.split('/')
        return len(base) > 0 and len(quote) > 0
    except:
        return False

def calculate_profit_percentage(entry_price: float, exit_price: float, side: str) -> float:
    """Calculate profit percentage"""
    try:
        if side == 'long':
            return ((exit_price - entry_price) / entry_price) * 100
        else:  # short
            return ((entry_price - exit_price) / entry_price) * 100
    except:
        return 0.0

def calculate_risk_reward(entry_price: float, tp_price: float, sl_price: float, side: str) -> float:
    """Calculate risk-reward ratio"""
    try:
        if side == 'long':
            profit = tp_price - entry_price
            risk = entry_price - sl_price
        else:  # short
            profit = entry_price - tp_price
            risk = sl_price - entry_price
        
        if risk <= 0:
            return 0.0
        
        return profit / risk
    except:
        return 0.0

def format_trade_summary(config) -> str:
    """Format trade configuration summary"""
    if not config.pair:
        return "No active configuration"
    
    summary = f"📊 {config.pair} {config.side.upper() if config.side else 'N/A'}\n"
    summary += f"💰 Size: {config.amount or 'N/A'}\n"
    summary += f"🎯 Entry: {format_price(config.entry_price)}\n"
    summary += f"🛑 SL: {format_price(config.sl_price)}\n"
    
    if config.tp1_price:
        summary += f"🎯 TP1: {format_price(config.tp1_price)} ({format_percentage(config.tp1_percent)})\n"
    if config.tp2_price:
        summary += f"🎯 TP2: {format_price(config.tp2_price)} ({format_percentage(config.tp2_percent)})\n"
    if config.tp3_price:
        summary += f"🎯 TP3: {format_price(config.tp3_price)} ({format_percentage(config.tp3_percent)})\n"
    
    summary += f"⚡ Leverage: {config.leverage}x\n"
    summary += f"🧪 Mode: {'DRY RUN' if config.dry_run else 'LIVE'}"
    
    return summary
