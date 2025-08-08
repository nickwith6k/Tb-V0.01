import os
import logging
import asyncio
from flask import Flask, render_template, request, jsonify
from trade_config import TradeConfig
from trade_bot import TradeBot
from telegram_handlers import TelegramBot
from webhook import setup_telegram_webhook

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "trading-bot-secret-key")

# Global instances
trade_config = TradeConfig()
trade_bot = TradeBot()
telegram_bot = None
bots_initialized = False

def initialize_bots():
    """Initialize Telegram and trading bots"""
    global telegram_bot, bots_initialized
    
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return False
        
        # Initialize Telegram bot
        telegram_bot = TelegramBot(bot_token, trade_bot)
        
        # Setup webhook
        webhook_url = os.getenv("WEBHOOK_URL")
        if webhook_url:
            setup_telegram_webhook(bot_token, f"{webhook_url}/webhook")
        
        bots_initialized = True
        logger.info("Bots initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize bots: {e}")
        return False

@app.route('/')
def status():
    """Main status page"""
    try:
        current_config = trade_bot.config
        trade_status = trade_bot.get_trade_status()
        
        return render_template('status.html',
                             bots_initialized=bots_initialized,
                             current_config=current_config,
                             trade_bot_active=trade_status['trade_active'],
                             trade_status=trade_status)
    except Exception as e:
        logger.error(f"Error rendering status page: {e}")
        return render_template('status.html',
                             bots_initialized=False,
                             current_config=None,
                             trade_bot_active=False,
                             trade_status={})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if not telegram_bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    try:
        update = request.get_json()
        if update:
            telegram_bot.handle_update(update)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint for status data"""
    try:
        trade_status = trade_bot.get_trade_status()
        config_dict = trade_bot.get_config_dict()
        
        return jsonify({
            'bots_initialized': bots_initialized,
            'trade_status': trade_status,
            'config': config_dict
        })
    except Exception as e:
        logger.error(f"API status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/place_trade', methods=['POST'])
def api_place_trade():
    """API endpoint to place trade"""
    try:
        success, message = trade_bot.place_trade_sync()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"API place trade error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/cancel_trade', methods=['POST'])
def api_cancel_trade():
    """API endpoint to cancel trade"""
    try:
        success = trade_bot.cancel_trade_sync()
        return jsonify({
            'success': success,
            'message': 'Trade cancelled' if success else 'Failed to cancel trade'
        })
    except Exception as e:
        logger.error(f"API cancel trade error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Initialize bots on startup
with app.app_context():
    initialize_bots()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
