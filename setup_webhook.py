#!/usr/bin/env python3
"""
Script to set up Telegram webhook for the trading bot
Run this once to configure your bot's webhook URL
"""

import os
import requests
import sys

def setup_telegram_webhook():
    """Set up the Telegram webhook"""
    
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    # Get the Replit URL (this will be the webhook URL)
    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
    if not replit_domain:
        replit_domains = os.getenv("REPLIT_DOMAINS", "")
        if replit_domains:
            replit_domain = replit_domains.split(',')[0].strip()
    
    if not replit_domain:
        print("Error: Could not determine Replit URL. Make sure you're running this on Replit.")
        return False
    
    replit_url = f"https://{replit_domain}"
    
    # Construct webhook URL
    webhook_url = f"{replit_url}/webhook"
    
    print(f"Setting up webhook for bot token: {bot_token[:10]}...")
    print(f"Webhook URL: {webhook_url}")
    
    # Set webhook
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        'url': webhook_url,
        'allowed_updates': ['message', 'callback_query']
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook set up successfully!")
            print(f"Webhook URL: {webhook_url}")
            print("\nYour bot is now ready to receive messages!")
            print("Send /start to your bot in Telegram to test it.")
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False

def get_webhook_info():
    """Get current webhook information"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found")
        return
    
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(api_url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            webhook_info = result.get('result', {})
            print("\n📋 Current Webhook Info:")
            print(f"URL: {webhook_info.get('url', 'Not set')}")
            print(f"Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
            print(f"Pending update count: {webhook_info.get('pending_update_count', 0)}")
            
            if webhook_info.get('last_error_date'):
                print(f"Last error: {webhook_info.get('last_error_message', 'Unknown')}")
        else:
            print(f"Failed to get webhook info: {result.get('description')}")
            
    except Exception as e:
        print(f"Error getting webhook info: {e}")

def delete_webhook():
    """Delete webhook to use polling mode"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found")
        return
    
    api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        response = requests.post(api_url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook deleted successfully!")
        else:
            print(f"❌ Failed to delete webhook: {result.get('description')}")
            
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")

if __name__ == "__main__":
    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "info":
            get_webhook_info()
        elif sys.argv[1] == "delete":
            delete_webhook()
        else:
            print("Usage: python setup_webhook.py [info|delete]")
    else:
        success = setup_telegram_webhook()
        if success:
            print("\n" + "=" * 40)
            get_webhook_info()