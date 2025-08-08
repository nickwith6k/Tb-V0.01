import logging
import json
from typing import Dict, Any, Optional
from .utils import send_telegram_message, answer_callback_query, create_inline_keyboard, create_button

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot handler for trading commands"""
    
    def __init__(self, bot_token: str, trade_bot):
        self.bot_token = bot_token
        self.trade_bot = trade_bot
        self.chat_id = None
        
        # Command handlers mapping
        self.commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/set_pair': self._handle_set_pair,
            '/selectpair': self._handle_select_pair,
            '/set_side': self._handle_set_side,
            '/set_amount': self._handle_set_amount,
            '/set_entry': self._handle_set_entry,
            '/set_tp1': self._handle_set_tp1,
            '/set_tp2': self._handle_set_tp2,
            '/set_tp3': self._handle_set_tp3,
            '/set_sl': self._handle_set_sl,
            '/set_leverage': self._handle_set_leverage,
            '/set_dryrun': self._handle_set_dryrun,
            '/set_breakeven': self._handle_set_breakeven,
            '/set_trailstop': self._handle_set_trailstop,
            '/place': self._handle_place,
            '/status': self._handle_status,
            '/cancel': self._handle_cancel,
            '/reset': self._handle_reset
        }
    
    def handle_update(self, update: Dict[str, Any]):
        """Handle incoming Telegram update"""
        try:
            # Handle callback queries (button presses)
            if 'callback_query' in update:
                self._handle_callback_query(update['callback_query'])
                return
            
            # Handle regular messages
            if 'message' not in update:
                return
            
            message = update['message']
            self.chat_id = message['chat']['id']
            
            if 'text' not in message:
                return
            
            text = message['text'].strip()
            
            # Parse command and arguments
            parts = text.split()
            if not parts:
                return
            
            command = parts[0].lower()
            args = parts[1:]
            
            # Handle command
            if command in self.commands:
                try:
                    response = self.commands[command](args)
                    if response:
                        if isinstance(response, tuple):
                            # Response with keyboard
                            text, keyboard = response
                            self._send_message_with_keyboard(text, keyboard)
                        else:
                            # Plain text response
                            self._send_message(response)
                except Exception as e:
                    logger.error(f"Error handling command {command}: {e}")
                    self._send_message(f"Error: {str(e)}")
            else:
                self._send_message("Unknown command. Type /help for available commands.")
                
        except Exception as e:
            logger.error(f"Error handling update: {e}")
    
    def _handle_callback_query(self, callback_query: Dict[str, Any]):
        """Handle callback query from inline keyboard"""
        try:
            self.chat_id = callback_query['message']['chat']['id']
            callback_data = callback_query['data']
            
            # Answer the callback query first
            answer_callback_query(self.bot_token, callback_query['id'])
            
            # Parse callback data
            if '|' in callback_data:
                action, value = callback_data.split('|', 1)
            else:
                action = callback_data
                value = None
            
            # Handle different callback actions
            self._handle_callback_action(action, value)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
    
    def _handle_callback_action(self, action: str, value: Optional[str] = None):
        """Handle callback action from button press"""
        try:
            if action == 'main_menu':
                self._show_main_menu()
            elif action == 'config_menu':
                self._show_config_menu()
            elif action == 'trading_menu':
                self._show_trading_menu()
            elif action == 'advanced_menu':
                self._show_advanced_menu()
            elif action == 'select_pair':
                if value:
                    self.trade_bot.config.set_pair(value)
                    self._send_message(f"✅ Trading pair set to: {value}")
                    self._show_config_menu()
                else:
                    self._show_pair_selection()
            elif action == 'select_side':
                if value:
                    self.trade_bot.config.set_side(value)
                    self._send_message(f"✅ Trade side set to: {value.upper()}")
                    self._show_config_menu()
                else:
                    self._show_side_selection()
            elif action == 'select_leverage':
                if value:
                    self.trade_bot.config.set_leverage(int(value))
                    self._send_message(f"✅ Leverage set to: {value}x")
                    self._show_config_menu()
                else:
                    self._show_leverage_selection()
            elif action == 'select_dryrun':
                if value:
                    dry_run = value == 'on'
                    self.trade_bot.config.set_dry_run(dry_run)
                    mode = "DRY RUN" if dry_run else "LIVE"
                    self._send_message(f"✅ Trading mode set to: {mode}")
                    self._show_advanced_menu()
                else:
                    self._show_dryrun_selection()
            elif action == 'select_breakeven':
                if value:
                    self.trade_bot.config.set_breakeven_tp(value)
                    self._send_message(f"✅ Break-even set to: {value.upper()}")
                    self._show_advanced_menu()
                else:
                    self._show_breakeven_selection()
            elif action == 'set_amount':
                self._show_amount_input()
            elif action == 'set_entry':
                self._show_entry_options()
            elif action == 'set_sl':
                self._show_sl_input()
            elif action == 'set_tp_menu':
                self._show_tp_menu()
            elif action == 'limit_order':
                self._show_limit_price_input()
            elif action == 'market_order':
                self._handle_market_order()
            elif action.startswith('set_tp'):
                # Handle TP level selection (set_tp1, set_tp2, set_tp3)
                if '|' in action:
                    tp_action, tp_level = action.split('|', 1)
                    self._show_tp_input(int(tp_level))
                else:
                    # Extract level from action (set_tp1 -> 1)
                    level = int(action[-1])
                    self._show_tp_input(level)
            elif action == 'clear_all_tp':
                self._handle_clear_all_tp()
            elif action == 'set_amount_value':
                if value:
                    amount = float(value)
                    if self.trade_bot.config.set_amount(amount):
                        self._send_message(f"✅ Position size set to: {amount}")
                        self._show_config_menu()
                    else:
                        self._send_message("❌ Invalid amount")
            elif action == 'status':
                self._handle_status([])
            elif action == 'place':
                success, message = self.trade_bot.place_trade_sync()
                text = f"{'✅' if success else '❌'} {message}"
                
                keyboard = create_inline_keyboard([
                    [create_button("📊 View Status", "status")],
                    [create_button("🏠 Main Menu", "main_menu")]
                ])
                
                self._send_message_with_keyboard(text, keyboard)
            elif action == 'cancel':
                self._handle_cancel([])
            elif action == 'reset':
                self._handle_reset([])
            elif action == 'help':
                self._show_help_menu()
            else:
                self._send_message("Unknown action")
                
        except Exception as e:
            logger.error(f"Error handling callback action {action}: {e}")
            self._send_message(f"Error: {str(e)}")
    
    def _send_message(self, text: str):
        """Send message to user"""
        if self.chat_id:
            success = send_telegram_message(self.bot_token, self.chat_id, text)
            if not success:
                logger.error(f"Failed to send message: {text}")
    
    def _send_message_with_keyboard(self, text: str, keyboard):
        """Send message with inline keyboard"""
        if self.chat_id:
            success = send_telegram_message(self.bot_token, self.chat_id, text, reply_markup=keyboard)
            if not success:
                logger.error(f"Failed to send message with keyboard: {text}")
    
    def _handle_start(self, args):
        """Handle /start command"""
        self._show_main_menu()
        return None
    
    def _show_main_menu(self):
        """Show main menu with interactive buttons"""
        text = (
            "🤖 Welcome to Toobit Futures Trading Bot!\n\n"
            "This bot helps you trade USDT-M futures with advanced features:\n"
            "• Partial take profits (TP1, TP2, TP3)\n"
            "• Break-even stop loss\n"
            "• Trailing stop\n"
            "• Dry-run mode for testing\n\n"
            "Choose an option below:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("⚙️ Configuration", "config_menu")],
            [create_button("📊 Trading", "trading_menu")],
            [create_button("⚡ Advanced Settings", "advanced_menu")],
            [create_button("📋 Status", "status"), create_button("❓ Help", "help")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_help(self, args):
        """Handle /help command"""
        self._show_help_menu()
        return None
    
    def _show_help_menu(self):
        """Show help menu with quick access buttons"""
        text = (
            "📋 Trading Bot Features:\n\n"
            "🔧 **Configuration**: Set up your trading pairs, position size, entry price, and leverage\n\n"
            "🎯 **Take Profits**: Configure up to 3 take profit levels with custom percentages\n\n"
            "🛑 **Stop Loss**: Set protective stop loss with break-even and trailing options\n\n"
            "⚡ **Advanced**: Dry-run mode, break-even protection, trailing stops\n\n"
            "🚀 **Trading**: Execute, monitor, and manage your trades\n\n"
            "All features are accessible through the interactive menus below!"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("⚙️ Configuration", "config_menu")],
            [create_button("📊 Trading", "trading_menu")],
            [create_button("⚡ Advanced", "advanced_menu")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_set_pair(self, args) -> str:
        """Handle /set_pair command"""
        if not args:
            return "Usage: /set_pair <symbol>\nExample: /set_pair BTC/USDT"
        
        pair = args[0].upper()
        if self.trade_bot.config.set_pair(pair):
            return f"✅ Trading pair set to: {pair}"
        else:
            return "❌ Invalid pair format. Use format like BTC/USDT"
    
    def _handle_select_pair(self, args):
        """Handle /selectpair command for interactive selection"""
        self._show_pair_selection()
        return None
    
    def _show_config_menu(self):
        """Show configuration menu"""
        config = self.trade_bot.config
        text = (
            "⚙️ **Configuration Menu**\n\n"
            f"📈 Pair: {config.pair or 'Not set'}\n"
            f"📊 Side: {config.side.upper() if config.side else 'Not set'}\n"
            f"💰 Amount: {config.amount or 'Not set'}\n"
            f"🎯 Entry: {config.entry_price or 'Not set'}\n"
            f"⚡ Leverage: {config.leverage}x\n\n"
            "Choose what to configure:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("📈 Trading Pair", "select_pair")],
            [create_button("📊 Long/Short", "select_side")],
            [create_button("💰 Position Size", "set_amount"), create_button("🎯 Entry Price", "set_entry")],
            [create_button("🛑 Stop Loss", "set_sl"), create_button("🎯 Take Profits", "set_tp_menu")],
            [create_button("⚡ Leverage", "select_leverage")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_trading_menu(self):
        """Show trading menu"""
        config = self.trade_bot.config
        text = (
            "📊 **Trading Menu**\n\n"
            f"Current Configuration:\n"
            f"📈 {config.pair or 'No pair'} - {config.side.upper() if config.side else 'No side'}\n"
            f"💰 Size: {config.amount or 'Not set'}\n"
            f"🎯 Entry: {config.entry_price or 'Not set'}\n"
            f"🛑 SL: {config.sl_price or 'Not set'}\n"
            f"🎯 TP1: {config.tp1_price or 'Not set'}\n"
            f"🎯 TP2: {config.tp2_price or 'Not set'}\n"
            f"🎯 TP3: {config.tp3_price or 'Not set'}\n\n"
            "Choose an action:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🚀 Place Trade", "place")],
            [create_button("📋 View Status", "status")],
            [create_button("❌ Cancel Trade", "cancel")],
            [create_button("🔄 Reset Config", "reset")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_advanced_menu(self):
        """Show advanced settings menu"""
        config = self.trade_bot.config
        text = (
            "⚡ **Advanced Settings**\n\n"
            f"🧪 Mode: {'DRY RUN' if config.dry_run else 'LIVE'}\n"
            f"⚖️ Break-even: {getattr(config, 'breakeven_tp', 'Not set')}\n"
            f"📈 Trailing: {config.trailing_stop_percent}% (after TP3)\n\n"
            "Configure advanced features:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🧪 Dry Run Mode", "select_dryrun")],
            [create_button("⚖️ Break-even", "select_breakeven")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_pair_selection(self):
        """Show trading pair selection menu"""
        text = "📈 **Select Trading Pair**\n\nChoose from popular pairs:"
        
        keyboard = create_inline_keyboard([
            [create_button("BTC/USDT", "select_pair|BTC/USDT"), create_button("ETH/USDT", "select_pair|ETH/USDT")],
            [create_button("BNB/USDT", "select_pair|BNB/USDT"), create_button("ADA/USDT", "select_pair|ADA/USDT")],
            [create_button("XRP/USDT", "select_pair|XRP/USDT"), create_button("SOL/USDT", "select_pair|SOL/USDT")],
            [create_button("DOT/USDT", "select_pair|DOT/USDT"), create_button("DOGE/USDT", "select_pair|DOGE/USDT")],
            [create_button("AVAX/USDT", "select_pair|AVAX/USDT"), create_button("MATIC/USDT", "select_pair|MATIC/USDT")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_side_selection(self):
        """Show side (long/short) selection menu"""
        text = "📊 **Select Trade Direction**\n\nChoose your position type:"
        
        keyboard = create_inline_keyboard([
            [create_button("📈 LONG (Buy)", "select_side|long")],
            [create_button("📉 SHORT (Sell)", "select_side|short")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_leverage_selection(self):
        """Show leverage selection menu"""
        text = "⚡ **Select Leverage**\n\nChoose your leverage multiplier:"
        
        keyboard = create_inline_keyboard([
            [create_button("1x", "select_leverage|1"), create_button("2x", "select_leverage|2"), create_button("5x", "select_leverage|5")],
            [create_button("10x", "select_leverage|10"), create_button("20x", "select_leverage|20"), create_button("50x", "select_leverage|50")],
            [create_button("75x", "select_leverage|75"), create_button("100x", "select_leverage|100")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_dryrun_selection(self):
        """Show dry run mode selection"""
        text = "🧪 **Trading Mode**\n\nChoose your trading mode:"
        
        keyboard = create_inline_keyboard([
            [create_button("🧪 DRY RUN (Safe Testing)", "select_dryrun|on")],
            [create_button("🚀 LIVE TRADING", "select_dryrun|off")],
            [create_button("🔙 Back", "advanced_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_breakeven_selection(self):
        """Show break-even selection menu"""
        text = "⚖️ **Break-even Protection**\n\nMove stop loss to entry price after which take profit?"
        
        keyboard = create_inline_keyboard([
            [create_button("After TP1", "select_breakeven|tp1")],
            [create_button("After TP2", "select_breakeven|tp2")],
            [create_button("After TP3", "select_breakeven|tp3")],
            [create_button("❌ Disable", "select_breakeven|none")],
            [create_button("🔙 Back", "advanced_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_set_side(self, args) -> str:
        """Handle /set_side command"""
        if not args:
            return "Usage: /set_side <long|short>"
        
        side = args[0].lower()
        if self.trade_bot.config.set_side(side):
            return f"✅ Trade side set to: {side.upper()}"
        else:
            return "❌ Invalid side. Use 'long' or 'short'"
    
    def _handle_set_amount(self, args) -> str:
        """Handle /set_amount command"""
        if not args:
            return "Usage: /set_amount <value>\nExample: /set_amount 0.01"
        
        try:
            amount = float(args[0])
            if self.trade_bot.config.set_amount(amount):
                return f"✅ Position size set to: {amount}"
            else:
                return "❌ Amount must be greater than 0"
        except ValueError:
            return "❌ Invalid amount format"
    
    def _handle_set_entry(self, args) -> str:
        """Handle /set_entry command"""
        if not args:
            return "Usage: /set_entry <price>\nExample: /set_entry 45000"
        
        try:
            price = float(args[0])
            if self.trade_bot.config.set_entry(price):
                return f"✅ Entry price set to: {price}"
            else:
                return "❌ Price must be greater than 0"
        except ValueError:
            return "❌ Invalid price format"
    
    def _handle_set_tp1(self, args) -> str:
        """Handle /set_tp1 command"""
        return self._handle_set_tp(1, args)
    
    def _handle_set_tp2(self, args) -> str:
        """Handle /set_tp2 command"""
        return self._handle_set_tp(2, args)
    
    def _handle_set_tp3(self, args) -> str:
        """Handle /set_tp3 command"""
        return self._handle_set_tp(3, args)
    
    def _handle_set_tp(self, level: int, args) -> str:
        """Handle take profit setting"""
        if len(args) < 2:
            return f"Usage: /set_tp{level} <price> <percent>\nExample: /set_tp{level} 50000 30"
        
        try:
            price = float(args[0])
            percent = float(args[1])
            
            if self.trade_bot.config.set_tp(level, price, percent):
                return f"✅ TP{level} set to: {price} ({percent}%)"
            else:
                return "❌ Invalid TP settings. Price > 0, percent 0-100"
        except ValueError:
            return "❌ Invalid number format"
    
    def _handle_set_sl(self, args) -> str:
        """Handle /set_sl command"""
        if not args:
            return "Usage: /set_sl <price>\nExample: /set_sl 40000"
        
        try:
            price = float(args[0])
            if self.trade_bot.config.set_sl(price):
                return f"✅ Stop loss set to: {price}"
            else:
                return "❌ Price must be greater than 0"
        except ValueError:
            return "❌ Invalid price format"
    
    def _handle_set_leverage(self, args) -> str:
        """Handle /set_leverage command"""
        if not args:
            return "Usage: /set_leverage <value>\nExample: /set_leverage 10"
        
        try:
            leverage = int(args[0])
            if self.trade_bot.config.set_leverage(leverage):
                return f"✅ Leverage set to: {leverage}x"
            else:
                return "❌ Leverage must be between 1 and 100"
        except ValueError:
            return "❌ Invalid leverage format"
    
    def _handle_set_dryrun(self, args) -> str:
        """Handle /set_dryrun command"""
        if not args:
            return "Usage: /set_dryrun <on|off>"
        
        mode = args[0].lower()
        if mode in ['on', 'true', '1']:
            self.trade_bot.config.set_dry_run(True)
            return "✅ Dry-run mode ENABLED - No real orders will be placed"
        elif mode in ['off', 'false', '0']:
            self.trade_bot.config.set_dry_run(False)
            return "⚠️ Dry-run mode DISABLED - Real orders will be placed!"
        else:
            return "❌ Use 'on' or 'off'"
    
    def _handle_set_breakeven(self, args) -> str:
        """Handle /set_breakeven command"""
        if not args:
            return "Usage: /set_breakeven <tp1|tp2|tp3>\nExample: /set_breakeven tp1"
        
        trigger = args[0].lower()
        if self.trade_bot.config.set_breakeven(trigger):
            return f"✅ Break-even enabled - SL will move to entry after {trigger.upper()}"
        else:
            return "❌ Invalid trigger. Use tp1, tp2, or tp3"
    
    def _handle_set_trailstop(self, args) -> str:
        """Handle /set_trailstop command"""
        if not args:
            return "Usage: /set_trailstop <percent>\nExample: /set_trailstop 2"
        
        try:
            percent = float(args[0])
            if self.trade_bot.config.set_trailing_stop(percent):
                return f"✅ Trailing stop enabled at {percent}% after TP3"
            else:
                return "❌ Percent must be between 0 and 50"
        except ValueError:
            return "❌ Invalid percent format"
    
    def _handle_place(self, args) -> str:
        """Handle /place command"""
        import asyncio
        
        # Run the async place_trade method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success, message = loop.run_until_complete(self.trade_bot.place_trade())
            return f"{'✅' if success else '❌'} {message}"
        except Exception as e:
            return f"❌ Error placing trade: {str(e)}"
        finally:
            loop.close()
    
    def _handle_status(self, args):
        """Handle /status command"""
        config = self.trade_bot.config
        trade_status = self.trade_bot.get_trade_status()
        
        if not config.pair:
            text = "❌ No configuration set. Use the Configuration menu to set up your trade."
        else:
            text = (
                "📊 **Current Configuration & Status**\n\n"
                f"📈 Pair: {config.pair}\n"
                f"📊 Side: {config.side.upper() if config.side else 'Not set'}\n"
                f"💰 Amount: {config.amount or 'Not set'}\n"
                f"🎯 Entry: {config.entry_price or 'Not set'}\n"
                f"🛑 SL: {config.sl_price or 'Not set'}\n"
                f"⚡ Leverage: {config.leverage}x\n\n"
                "🎯 **Take Profits:**\n"
                f"TP1: {config.tp1_price or 'Not set'} ({config.tp1_percent or 0}%)\n"
                f"TP2: {config.tp2_price or 'Not set'} ({config.tp2_percent or 0}%)\n"
                f"TP3: {config.tp3_price or 'Not set'} ({config.tp3_percent or 0}%)\n\n"
                f"⚖️ Break-even: {getattr(config, 'breakeven_tp', 'Disabled')}\n"
                f"📈 Trailing: {config.trailing_stop_percent}% (after TP3)\n"
                f"🧪 Mode: {'DRY RUN' if config.dry_run else 'LIVE'}\n\n"
                f"🔄 **Trade Status:** {trade_status}"
            )
        
        keyboard = create_inline_keyboard([
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
        return None
    
    def _handle_cancel(self, args):
        """Handle /cancel command"""
        success, message = self.trade_bot.cancel_trade()
        text = f"{'✅' if success else '❌'} {message}"
        
        keyboard = create_inline_keyboard([
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
        return None
    
    def _handle_reset(self, args):
        """Handle /reset command"""
        self.trade_bot.config.reset()
        self.trade_bot.stop_monitoring()
        text = "✅ All configuration reset to defaults"
        
        keyboard = create_inline_keyboard([
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
        return None
    def _show_amount_input(self):
        """Show amount input instructions with preset options"""
        text = (
            "💰 **Set Position Size**\n\n"
            "Choose a preset amount or type your custom amount:\n"
            "`/set_amount <value>`\n\n"
            "Examples:\n"
            "• `/set_amount 0.01` - for 0.01 BTC\n"
            "• `/set_amount 100` - for 100 USDT\n"
            "• `/set_amount 0.5` - for 0.5 ETH\n\n"
            "Or use preset amounts below:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("0.01", "set_amount_value|0.01"), create_button("0.1", "set_amount_value|0.1")],
            [create_button("1", "set_amount_value|1"), create_button("10", "set_amount_value|10")],
            [create_button("100", "set_amount_value|100"), create_button("1000", "set_amount_value|1000")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)

    def _show_entry_options(self):
        """Show entry price options"""
        text = "🎯 **Entry Price Options**\n\nChoose how you want to enter the trade:"
        
        keyboard = create_inline_keyboard([
            [create_button("📊 Market Order (Current Price)", "market_order")],
            [create_button("📝 Set Limit Price", "limit_order")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)

    def _handle_market_order(self):
        """Handle market order selection"""
        self.trade_bot.config.entry_price = 0  # 0 indicates market order
        self.trade_bot.config.save_config()
        
        text = "✅ Market order selected! Entry will be executed at current market price when you place the trade."
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back to Config", "config_menu")],
            [create_button("🚀 Continue to Trading", "trading_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_tp_menu(self):
        """Show take profit menu with options for TP1, TP2, TP3"""
        config = self.trade_bot.config
        text = (
            "🎯 **Take Profit Configuration**\n\n"
            f"Current Settings:\n"
            f"TP1: {config.tp1_price or 'Not set'} ({config.tp1_percent or 0}%)\n"
            f"TP2: {config.tp2_price or 'Not set'} ({config.tp2_percent or 0}%)\n"
            f"TP3: {config.tp3_price or 'Not set'} ({config.tp3_percent or 0}%)\n\n"
            "Choose which take profit level to configure:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🎯 Set TP1", "set_tp|1"), create_button("🎯 Set TP2", "set_tp|2")],
            [create_button("🎯 Set TP3", "set_tp|3")],
            [create_button("🔄 Clear All TPs", "clear_all_tp")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_tp_input(self, level: int):
        """Show input instructions for specific TP level"""
        text = (
            f"🎯 **Set Take Profit {level}**\n\n"
            f"Please type the TP{level} price and percentage in this format:\n"
            f"`/set_tp{level} <price> <percent>`\n\n"
            f"Examples:\n"
            f"• `/set_tp{level} 50000 30` - TP at $50,000 (30% of position)\n"
            f"• `/set_tp{level} 45000 50` - TP at $45,000 (50% of position)\n\n"
            f"Type your TP{level} command:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back to TP Menu", "set_tp_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_sl_input(self):
        """Show stop loss input instructions"""
        text = (
            "🛑 **Set Stop Loss**\n\n"
            "Please type the stop loss price:\n"
            "`/set_sl <price>`\n\n"
            "Examples:\n"
            "• `/set_sl 40000` - Stop loss at $40,000\n"
            "• `/set_sl 35500` - Stop loss at $35,500\n\n"
            "Type your stop loss command:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_limit_price_input(self):
        """Show limit price input instructions"""
        text = (
            "📝 **Set Limit Entry Price**\n\n"
            "Please type the limit price for your entry:\n"
            "`/set_entry <price>`\n\n"
            "Examples:\n"
            "• `/set_entry 42000` - Enter at $42,000\n"
            "• `/set_entry 41500` - Enter at $41,500\n\n"
            "Type your entry price command:"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("📊 Use Market Price Instead", "market_order")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_clear_all_tp(self):
        """Handle clearing all take profit levels"""
        self.trade_bot.config.tp1_price = None
        self.trade_bot.config.tp1_percent = None
        self.trade_bot.config.tp2_price = None
        self.trade_bot.config.tp2_percent = None
        self.trade_bot.config.tp3_price = None
        self.trade_bot.config.tp3_percent = None
        self.trade_bot.config.save_config()
        
        text = "✅ All take profit levels have been cleared!"
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back to TP Menu", "set_tp_menu")],
            [create_button("⚙️ Config Menu", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
