import os
import logging
import asyncio
import threading
from flask import Flask, request, render_template, jsonify
from bot.telegram_handlers import TelegramBot
from bot.trade_bot import TradeBot

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram_trading_bot_secret_key")

# Initialize bot instances
telegram_bot = None
trade_bot = None

def initialize_bots():
    """Initialize the Telegram and Trade bots"""
    global telegram_bot, trade_bot
    
    try:
        # Get bot token from environment
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
            return False
            
        # Initialize trade bot first
        trade_bot = TradeBot()
        
        # Initialize telegram bot with trade bot reference
        telegram_bot = TelegramBot(bot_token, trade_bot)
        
        # Trade monitoring will be started when a trade is placed
        # No need to start monitoring on app startup
        
        logger.info("Bots initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize bots: {e}")
        return False

# Initialize bots on startup
bots_initialized = initialize_bots()

@app.route('/')
def alive():
    """Keep-alive endpoint for UptimeRobot"""
    return "alive"

@app.route('/status')
def status():
    """Status page showing bot health and configuration"""
    global trade_bot
    
    status_data = {
        'bots_initialized': bots_initialized,
        'trade_bot_active': trade_bot is not None,
        'current_config': None,
        'trade_status': None
    }
    
    if trade_bot:
        status_data['current_config'] = trade_bot.get_config_dict()
        status_data['trade_status'] = trade_bot.get_trade_status()
    
    return render_template('status.html', **status_data)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    global telegram_bot
    
    if not telegram_bot:
        logger.error("Telegram bot not initialized")
        return "Bot not initialized", 500
    
    try:
        update = request.get_json()
        if update:
            telegram_bot.handle_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy' if bots_initialized else 'unhealthy',
        'telegram_bot': telegram_bot is not None,
        'trade_bot': trade_bot is not None
    }
    return jsonify(health_status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
