import logging
import json
from typing import Dict, Any, Optional
from utils import send_telegram_message, answer_callback_query, create_inline_keyboard, create_button

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
            [create_button("📈 Pair", "select_pair"), create_button("📊 Side", "select_side")],
            [create_button("💰 Amount", "set_amount"), create_button("🎯 Entry", "set_entry")],
            [create_button("⚡ Leverage", "select_leverage"), create_button("🛑 Stop Loss", "set_sl")],
            [create_button("🎯 Take Profits", "set_tp_menu")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_trading_menu(self):
        """Show trading menu"""
        config = self.trade_bot.config
        trade_status = self.trade_bot.get_trade_status()
        
        is_valid, validation_msg = config.is_valid_for_trading()
        
        text = (
            "📊 **Trading Menu**\n\n"
            f"Status: {'🟢 Active' if trade_status['trade_active'] else '🔴 Inactive'}\n"
            f"Mode: {'🧪 DRY RUN' if config.dry_run else '🔴 LIVE'}\n\n"
        )
        
        if is_valid:
            text += "✅ Configuration is valid for trading\n"
        else:
            text += f"❌ {validation_msg}\n"
        
        text += "\nChoose an action:"
        
        buttons = []
        if is_valid and not trade_status['trade_active']:
            buttons.append([create_button("🚀 Place Trade", "place")])
        
        if trade_status['trade_active']:
            buttons.append([create_button("🛑 Cancel Trade", "cancel")])
        
        buttons.extend([
            [create_button("📊 View Status", "status")],
            [create_button("🔄 Reset Config", "reset")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        keyboard = create_inline_keyboard(buttons)
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_advanced_menu(self):
        """Show advanced settings menu"""
        config = self.trade_bot.config
        
        text = (
            "⚡ **Advanced Settings**\n\n"
            f"🧪 Mode: {'DRY RUN' if config.dry_run else 'LIVE'}\n"
            f"🔄 Break-even: {config.breakeven_trigger.upper() if config.breakeven_enabled else 'Disabled'}\n"
            f"📈 Trailing Stop: {config.trailing_stop_percent}% " if config.trailing_stop_enabled else "📈 Trailing Stop: Disabled\n"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🧪 Trading Mode", "select_dryrun")],
            [create_button("🔄 Break-even", "select_breakeven")],
            [create_button("📈 Trailing Stop", "set_trailing")],
            [create_button("🏠 Main Menu", "main_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_pair_selection(self):
        """Show pair selection menu"""
        text = "📈 **Select Trading Pair**"
        
        pairs = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT",
            "SOL/USDT", "XRP/USDT", "DOGE/USDT", "DOT/USDT"
        ]
        
        buttons = []
        for i in range(0, len(pairs), 2):
            row = []
            for j in range(2):
                if i + j < len(pairs):
                    pair = pairs[i + j]
                    row.append(create_button(pair, f"select_pair|{pair}"))
            if row:
                buttons.append(row)
        
        buttons.append([create_button("🔙 Back", "config_menu")])
        
        keyboard = create_inline_keyboard(buttons)
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_side_selection(self):
        """Show side selection menu"""
        text = "📊 **Select Trade Direction**"
        
        keyboard = create_inline_keyboard([
            [create_button("🟢 LONG", "select_side|long"), create_button("🔴 SHORT", "select_side|short")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_leverage_selection(self):
        """Show leverage selection menu"""
        text = "⚡ **Select Leverage**"
        
        leverages = [1, 2, 3, 5, 10, 20, 25, 50]
        
        buttons = []
        for i in range(0, len(leverages), 4):
            row = []
            for j in range(4):
                if i + j < len(leverages):
                    lev = leverages[i + j]
                    row.append(create_button(f"{lev}x", f"select_leverage|{lev}"))
            if row:
                buttons.append(row)
        
        buttons.append([create_button("🔙 Back", "config_menu")])
        
        keyboard = create_inline_keyboard(buttons)
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_dryrun_selection(self):
        """Show dry run mode selection"""
        text = "🧪 **Select Trading Mode**"
        
        keyboard = create_inline_keyboard([
            [create_button("🧪 DRY RUN (Safe)", "select_dryrun|on")],
            [create_button("🔴 LIVE (Real Money)", "select_dryrun|off")],
            [create_button("🔙 Back", "advanced_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_breakeven_selection(self):
        """Show break-even selection menu"""
        text = "🔄 **Select Break-even Trigger**"
        
        keyboard = create_inline_keyboard([
            [create_button("🎯 TP1", "select_breakeven|tp1"), create_button("🎯 TP2", "select_breakeven|tp2")],
            [create_button("🎯 TP3", "select_breakeven|tp3"), create_button("❌ None", "select_breakeven|none")],
            [create_button("🔙 Back", "advanced_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_amount_input(self):
        """Show amount input options"""
        text = "💰 **Set Position Size**\n\nSend the amount as a message (e.g., 100)"
        
        # Quick amount buttons
        amounts = [10, 25, 50, 100, 250, 500]
        
        buttons = []
        for i in range(0, len(amounts), 3):
            row = []
            for j in range(3):
                if i + j < len(amounts):
                    amount = amounts[i + j]
                    row.append(create_button(f"${amount}", f"set_amount_value|{amount}"))
            if row:
                buttons.append(row)
        
        buttons.append([create_button("🔙 Back", "config_menu")])
        
        keyboard = create_inline_keyboard(buttons)
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_entry_options(self):
        """Show entry order options"""
        text = "🎯 **Set Entry Order**"
        
        keyboard = create_inline_keyboard([
            [create_button("📈 Market Order", "market_order")],
            [create_button("🎯 Limit Order", "limit_order")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_market_order(self):
        """Handle market order selection"""
        self.trade_bot.config.set_entry(0)  # 0 indicates market order
        self._send_message("✅ Entry set to Market Order")
        self._show_config_menu()
    
    def _show_limit_price_input(self):
        """Show limit price input"""
        text = "🎯 **Set Limit Price**\n\nSend the price as a message (e.g., 45000)"
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_sl_input(self):
        """Show stop loss input"""
        text = "🛑 **Set Stop Loss Price**\n\nSend the price as a message (e.g., 42000)"
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_tp_menu(self):
        """Show take profit menu"""
        config = self.trade_bot.config
        
        text = (
            "🎯 **Take Profit Configuration**\n\n"
            f"TP1: {config.tp1_price or 'Not set'} ({config.tp1_percent or 0}%)\n"
            f"TP2: {config.tp2_price or 'Not set'} ({config.tp2_percent or 0}%)\n"
            f"TP3: {config.tp3_price or 'Not set'} ({config.tp3_percent or 0}%)\n"
        )
        
        keyboard = create_inline_keyboard([
            [create_button("🎯 Set TP1", "set_tp1"), create_button("🎯 Set TP2", "set_tp2")],
            [create_button("🎯 Set TP3", "set_tp3"), create_button("🗑️ Clear All", "clear_all_tp")],
            [create_button("🔙 Back", "config_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _show_tp_input(self, level: int):
        """Show take profit input for specific level"""
        text = f"🎯 **Set TP{level}**\n\nSend in format: price,percentage\nExample: 50000,30"
        
        keyboard = create_inline_keyboard([
            [create_button("🔙 Back", "set_tp_menu")]
        ])
        
        self._send_message_with_keyboard(text, keyboard)
    
    def _handle_clear_all_tp(self):
        """Clear all take profit levels"""
        self.trade_bot.config.tp1_price = None
        self.trade_bot.config.tp1_percent = None
        self.trade_bot.config.tp2_price = None
        self.trade_bot.config.tp2_percent = None
        self.trade_bot.config.tp3_price = None
        self.trade_bot.config.tp3_percent = None
        self.trade_bot.config.save_config()
        
        self._send_message("✅ All take profits cleared")
        self._show_tp_menu()
    
    # Command handlers for text commands
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
        """Handle /selectpair command"""
        self._show_pair_selection()
        return None
    
    def _handle_set_side(self, args) -> str:
        """Handle /set_side command"""
        if not args:
            return "Usage: /set_side <long|short>\nExample: /set_side long"
        
        side = args[0].lower()
        if self.trade_bot.config.set_side(side):
            return f"✅ Trade side set to: {side.upper()}"
        else:
            return "❌ Invalid side. Use 'long' or 'short'"
    
    def _handle_set_amount(self, args) -> str:
        """Handle /set_amount command"""
        if not args:
            return "Usage: /set_amount <amount>\nExample: /set_amount 100"
        
        try:
            amount = float(args[0])
            if self.trade_bot.config.set_amount(amount):
                return f"✅ Position size set to: {amount}"
            else:
                return "❌ Invalid amount. Must be greater than 0"
        except ValueError:
            return "❌ Invalid amount format"
    
    def _handle_set_entry(self, args) -> str:
        """Handle /set_entry command"""
        if not args:
            return "Usage: /set_entry <price>\nExample: /set_entry 45000 or /set_entry 0 for market order"
        
        try:
            price = float(args[0])
            if self.trade_bot.config.set_entry(price):
                if price == 0:
                    return "✅ Entry set to Market Order"
                else:
                    return f"✅ Entry price set to: {price}"
            else:
                return "❌ Invalid price"
        except ValueError:
            return "❌ Invalid price format"
    
    def _handle_set_tp1(self, args) -> str:
        """Handle /set_tp1 command"""
        return self._handle_set_tp(args, 1)
    
    def _handle_set_tp2(self, args) -> str:
        """Handle /set_tp2 command"""
        return self._handle_set_tp(args, 2)
    
    def _handle_set_tp3(self, args) -> str:
        """Handle /set_tp3 command"""
        return self._handle_set_tp(args, 3)
    
    def _handle_set_tp(self, args, level: int) -> str:
        """Handle take profit setting"""
        if len(args) < 2:
            return f"Usage: /set_tp{level} <price> <percentage>\nExample: /set_tp{level} 50000 30"
        
        try:
            price = float(args[0])
            percent = float(args[1])
            
            if self.trade_bot.config.set_tp(level, price, percent):
                return f"✅ TP{level} set to: {price} ({percent}%)"
            else:
                return "❌ Invalid TP settings"
        except ValueError:
            return "❌ Invalid format"
    
    def _handle_set_sl(self, args) -> str:
        """Handle /set_sl command"""
        if not args:
            return "Usage: /set_sl <price>\nExample: /set_sl 42000"
        
        try:
            price = float(args[0])
            if self.trade_bot.config.set_sl(price):
                return f"✅ Stop loss set to: {price}"
            else:
                return "❌ Invalid stop loss price"
        except ValueError:
            return "❌ Invalid price format"
    
    def _handle_set_leverage(self, args) -> str:
        """Handle /set_leverage command"""
        if not args:
            return "Usage: /set_leverage <1-100>\nExample: /set_leverage 10"
        
        try:
            leverage = int(args[0])
            if self.trade_bot.config.set_leverage(leverage):
                return f"✅ Leverage set to: {leverage}x"
            else:
                return "❌ Invalid leverage. Must be between 1-100"
        except ValueError:
            return "❌ Invalid leverage format"
    
    def _handle_set_dryrun(self, args) -> str:
        """Handle /set_dryrun command"""
        if not args:
            return "Usage: /set_dryrun <on|off>\nExample: /set_dryrun on"
        
        mode = args[0].lower()
        if mode in ['on', 'true', '1']:
            self.trade_bot.config.set_dry_run(True)
            return "✅ Dry run mode enabled"
        elif mode in ['off', 'false', '0']:
            self.trade_bot.config.set_dry_run(False)
            return "✅ Live trading mode enabled"
        else:
            return "❌ Invalid mode. Use 'on' or 'off'"
    
    def _handle_set_breakeven(self, args) -> str:
        """Handle /set_breakeven command"""
        if not args:
            return "Usage: /set_breakeven <tp1|tp2|tp3|none>\nExample: /set_breakeven tp1"
        
        trigger = args[0].lower()
        if self.trade_bot.config.set_breakeven_tp(trigger):
            if trigger == 'none':
                return "✅ Break-even disabled"
            else:
                return f"✅ Break-even trigger set to: {trigger.upper()}"
        else:
            return "❌ Invalid trigger. Use tp1, tp2, tp3, or none"
    
    def _handle_set_trailstop(self, args) -> str:
        """Handle /set_trailstop command"""
        if not args:
            return "Usage: /set_trailstop <percentage>\nExample: /set_trailstop 2.5"
        
        try:
            percent = float(args[0])
            if self.trade_bot.config.set_trailing_stop(percent):
                return f"✅ Trailing stop set to: {percent}%"
            else:
                return "❌ Invalid percentage. Must be between 0.1-50"
        except ValueError:
            return "❌ Invalid percentage format"
    
    def _handle_place(self, args) -> str:
        """Handle /place command"""
        success, message = self.trade_bot.place_trade_sync()
        return f"{'✅' if success else '❌'} {message}"
    
    def _handle_status(self, args) -> str:
        """Handle /status command"""
        config = self.trade_bot.config
        trade_status = self.trade_bot.get_trade_status()
        
        text = "📊 **Trading Bot Status**\n\n"
        
        # Configuration
        text += f"📈 Pair: {config.pair or 'Not set'}\n"
        text += f"📊 Side: {config.side.upper() if config.side else 'Not set'}\n"
        text += f"💰 Amount: {config.amount or 'Not set'}\n"
        text += f"🎯 Entry: {config.entry_price or 'Not set'}\n"
        text += f"⚡ Leverage: {config.leverage}x\n"
        text += f"🛑 Stop Loss: {config.sl_price or 'Not set'}\n"
        
        # Take profits
        if config.tp1_price:
            text += f"🎯 TP1: {config.tp1_price} ({config.tp1_percent}%)\n"
        if config.tp2_price:
            text += f"🎯 TP2: {config.tp2_price} ({config.tp2_percent}%)\n"
        if config.tp3_price:
            text += f"🎯 TP3: {config.tp3_price} ({config.tp3_percent}%)\n"
        
        # Status
        text += f"\n🧪 Mode: {'DRY RUN' if config.dry_run else 'LIVE'}\n"
        text += f"🔄 Trade Active: {'Yes' if trade_status['trade_active'] else 'No'}\n"
        
        if trade_status['trade_active']:
            text += f"✅ Entry Filled: {'Yes' if trade_status['entry_filled'] else 'No'}\n"
            if config.tp1_price:
                text += f"🎯 TP1 Filled: {'Yes' if trade_status['tp1_filled'] else 'No'}\n"
            if config.tp2_price:
                text += f"🎯 TP2 Filled: {'Yes' if trade_status['tp2_filled'] else 'No'}\n"
            if config.tp3_price:
                text += f"🎯 TP3 Filled: {'Yes' if trade_status['tp3_filled'] else 'No'}\n"
        
        return text
    
    def _handle_cancel(self, args) -> str:
        """Handle /cancel command"""
        success = self.trade_bot.cancel_trade_sync()
        return f"{'✅' if success else '❌'} {'Trade cancelled' if success else 'Failed to cancel trade'}"
    
    def _handle_reset(self, args) -> str:
        """Handle /reset command"""
        self.trade_bot.config.reset()
        return "✅ Configuration reset to defaults"
