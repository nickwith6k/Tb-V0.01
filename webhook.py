import requests
import logging

logger = logging.getLogger(__name__)

def setup_telegram_webhook(bot_token: str, webhook_url: str) -> bool:
    """Setup Telegram webhook"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        
        payload = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query']
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Webhook setup failed: {result.get('description')}")
                return False
        else:
            logger.error(f"Webhook setup HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return False

def remove_telegram_webhook(bot_token: str) -> bool:
    """Remove Telegram webhook"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("Webhook removed successfully")
                return True
            else:
                logger.error(f"Webhook removal failed: {result.get('description')}")
                return False
        else:
            logger.error(f"Webhook removal HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
        return False

def get_webhook_info(bot_token: str) -> dict:
    """Get current webhook information"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return result.get('result', {})
            else:
                logger.error(f"Get webhook info failed: {result.get('description')}")
                return {}
        else:
            logger.error(f"Get webhook info HTTP error: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return {}
