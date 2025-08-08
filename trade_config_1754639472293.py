import json
import os
from typing import Optional, Dict, Any

class TradeConfig:
    """Configuration class for trading parameters"""
    
    def __init__(self):
        self.reset()
        self.config_file = "trade_config.json"
        self.load_config()
    
    def reset(self):
        """Reset all configuration to defaults"""
        self.pair: Optional[str] = None
        self.side: Optional[str] = None  # 'long' or 'short'
        self.amount: Optional[float] = None
        self.entry_price: Optional[float] = None
        self.leverage: int = 1
        
        # Take profit levels
        self.tp1_price: Optional[float] = None
        self.tp1_percent: Optional[float] = None
        self.tp2_price: Optional[float] = None
        self.tp2_percent: Optional[float] = None
        self.tp3_price: Optional[float] = None
        self.tp3_percent: Optional[float] = None
        
        # Stop loss
        self.sl_price: Optional[float] = None
        
        # Break-even settings
        self.breakeven_enabled: bool = False
        self.breakeven_trigger: Optional[str] = None  # 'tp1', 'tp2', or 'tp3'
        self.breakeven_tp: Optional[str] = None  # Alias for compatibility
        
        # Trailing stop
        self.trailing_stop_enabled: bool = False
        self.trailing_stop_percent: Optional[float] = None
        
        # Mode settings
        self.dry_run: bool = True  # Start in dry run mode for safety
        
        # Trade state
        self.trade_active: bool = False
        self.position_size: Optional[float] = None
        self.entry_filled: bool = False
        self.tp1_filled: bool = False
        self.tp2_filled: bool = False
        self.tp3_filled: bool = False
        self.breakeven_moved: bool = False
        self.trailing_active: bool = False
        self.highest_price: Optional[float] = None
    
    def set_pair(self, pair: str) -> bool:
        """Set trading pair"""
        try:
            # Normalize pair format (e.g., BTC/USDT)
            if '/' not in pair:
                # Try to add /USDT if no separator
                pair = f"{pair}/USDT"
            self.pair = pair.upper()
            self.save_config()
            return True
        except Exception:
            return False
    
    def set_side(self, side: str) -> bool:
        """Set trade side (long/short)"""
        if side.lower() in ['long', 'short']:
            self.side = side.lower()
            self.save_config()
            return True
        return False
    
    def set_amount(self, amount: float) -> bool:
        """Set trade amount"""
        if amount > 0:
            self.amount = amount
            self.save_config()
            return True
        return False
    
    def set_entry(self, price: float) -> bool:
        """Set entry price"""
        if price > 0:
            self.entry_price = price
            self.save_config()
            return True
        return False
    
    def set_tp(self, level: int, price: float, percent: float) -> bool:
        """Set take profit level"""
        if level not in [1, 2, 3] or price <= 0 or percent <= 0 or percent > 100:
            return False
        
        if level == 1:
            self.tp1_price = price
            self.tp1_percent = percent
        elif level == 2:
            self.tp2_price = price
            self.tp2_percent = percent
        elif level == 3:
            self.tp3_price = price
            self.tp3_percent = percent
        
        self.save_config()
        return True
    
    def set_sl(self, price: float) -> bool:
        """Set stop loss price"""
        if price > 0:
            self.sl_price = price
            self.save_config()
            return True
        return False
    
    def set_leverage(self, leverage: int) -> bool:
        """Set leverage"""
        if 1 <= leverage <= 100:
            self.leverage = leverage
            self.save_config()
            return True
        return False
    
    def set_dry_run(self, enabled: bool):
        """Set dry run mode"""
        self.dry_run = enabled
        self.save_config()
    
    def set_breakeven_tp(self, trigger: str) -> bool:
        """Set break-even trigger"""
        if trigger.lower() in ['tp1', 'tp2', 'tp3', 'none']:
            if trigger.lower() == 'none':
                self.breakeven_enabled = False
                self.breakeven_trigger = None
                self.breakeven_tp = None
            else:
                self.breakeven_enabled = True
                self.breakeven_trigger = trigger.lower()
                self.breakeven_tp = trigger.lower()
            self.save_config()
            return True
        return False
    
    def set_breakeven(self, trigger: str) -> bool:
        """Set break-even trigger"""
        if trigger.lower() in ['tp1', 'tp2', 'tp3']:
            self.breakeven_enabled = True
            self.breakeven_trigger = trigger.lower()
            self.save_config()
            return True
        return False
    
    def disable_breakeven(self):
        """Disable break-even"""
        self.breakeven_enabled = False
        self.breakeven_trigger = None
        self.save_config()
    
    def set_trailing_stop(self, percent: float) -> bool:
        """Set trailing stop percentage"""
        if 0 < percent <= 50:
            self.trailing_stop_enabled = True
            self.trailing_stop_percent = percent
            self.save_config()
            return True
        return False
    
    def disable_trailing_stop(self):
        """Disable trailing stop"""
        self.trailing_stop_enabled = False
        self.trailing_stop_percent = None
        self.save_config()
    
    def is_valid_for_trading(self) -> tuple[bool, str]:
        """Check if configuration is valid for trading"""
        if not self.pair:
            return False, "Pair not set"
        if not self.side:
            return False, "Side not set"
        if not self.amount:
            return False, "Amount not set"
        
        # Entry price can be 0 for market orders or a specific price for limit orders
        if self.entry_price is None:
            return False, "Entry price not set (use market order or set specific price)"
        
        # For basic trading, we don't require SL and TP to be set
        # This allows for quick market entry trades
        
        # If TP percentages are set, validate they don't exceed 100%
        total_tp_percent = 0
        if self.tp1_price and self.tp1_percent:
            total_tp_percent += self.tp1_percent
        if self.tp2_price and self.tp2_percent:
            total_tp_percent += self.tp2_percent
        if self.tp3_price and self.tp3_percent:
            total_tp_percent += self.tp3_percent
        
        if total_tp_percent > 100:
            return False, "Total TP percentages cannot exceed 100%"
        
        return True, "Configuration valid"
    
    def reset_trade_state(self):
        """Reset trade execution state"""
        self.trade_active = False
        self.position_size = None
        self.entry_filled = False
        self.tp1_filled = False
        self.tp2_filled = False
        self.tp3_filled = False
        self.breakeven_moved = False
        self.trailing_active = False
        self.highest_price = None
        self.save_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'pair': self.pair,
            'side': self.side,
            'amount': self.amount,
            'entry_price': self.entry_price,
            'leverage': self.leverage,
            'tp1_price': self.tp1_price,
            'tp1_percent': self.tp1_percent,
            'tp2_price': self.tp2_price,
            'tp2_percent': self.tp2_percent,
            'tp3_price': self.tp3_price,
            'tp3_percent': self.tp3_percent,
            'sl_price': self.sl_price,
            'breakeven_enabled': self.breakeven_enabled,
            'breakeven_trigger': self.breakeven_trigger,
            'trailing_stop_enabled': self.trailing_stop_enabled,
            'trailing_stop_percent': self.trailing_stop_percent,
            'dry_run': self.dry_run,
            'trade_active': self.trade_active,
            'position_size': self.position_size,
            'entry_filled': self.entry_filled,
            'tp1_filled': self.tp1_filled,
            'tp2_filled': self.tp2_filled,
            'tp3_filled': self.tp3_filled,
            'breakeven_moved': self.breakeven_moved,
            'trailing_active': self.trailing_active,
            'highest_price': self.highest_price
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
        except Exception as e:
            print(f"Error loading config: {e}")
