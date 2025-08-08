import asyncio
import logging
from typing import Optional, Dict, Any
from trade_config import TradeConfig
from exchange_manager import ExchangeManager

logger = logging.getLogger(__name__)

class TradeBot:
    """Main trading bot logic"""
    
    def __init__(self):
        self.config = TradeConfig()
        self.exchange = ExchangeManager()
        self.monitoring = False
        self.current_orders = {}  # Track active orders
        self.position_info = None
        self.logger = logger
        
    def get_config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return self.config.to_dict()
    
    def get_trade_status(self) -> Dict[str, Any]:
        """Get current trade status"""
        return {
            'monitoring': self.monitoring,
            'trade_active': self.config.trade_active,
            'entry_filled': self.config.entry_filled,
            'tp1_filled': self.config.tp1_filled,
            'tp2_filled': self.config.tp2_filled,
            'tp3_filled': self.config.tp3_filled,
            'breakeven_moved': self.config.breakeven_moved,
            'trailing_active': self.config.trailing_active,
            'current_orders': len(self.current_orders),
            'position_size': self.config.position_size
        }
    
    def place_trade_sync(self) -> tuple[bool, str]:
        """Synchronous wrapper for place_trade"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.place_trade())
            loop.close()
            return result
        except Exception as e:
            return False, f"Error placing trade: {str(e)}"
    
    def cancel_trade_sync(self) -> bool:
        """Synchronous wrapper for cancel_trade"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.cancel_trade())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error cancelling trade: {e}")
            return False
    
    async def place_trade(self) -> tuple[bool, str]:
        """Start trade execution"""
        # Validate configuration
        is_valid, message = self.config.is_valid_for_trading()
        if not is_valid:
            return False, f"Configuration invalid: {message}"
        
        if self.config.trade_active:
            return False, "Trade already active"
        
        try:
            # Set leverage first
            if self.exchange.exchange and self.config.pair:
                await self.exchange.set_leverage(self.config.pair, self.config.leverage)
            
            # Reset trade state
            self.config.reset_trade_state()
            self.config.trade_active = True
            self.config.save_config()
            
            # Place entry order
            success = await self._place_entry_order()
            if not success:
                self.config.trade_active = False
                self.config.save_config()
                return False, "Failed to place entry order"
            
            # Start monitoring
            if not self.monitoring:
                asyncio.create_task(self.start_monitoring())
            
            mode = "DRY RUN" if self.config.dry_run else "LIVE"
            return True, f"Trade placed successfully in {mode} mode"
            
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            self.config.trade_active = False
            self.config.save_config()
            return False, f"Error placing trade: {str(e)}"
    
    async def cancel_trade(self) -> bool:
        """Cancel active trade"""
        try:
            if not self.config.trade_active:
                return True
            
            # Cancel all active orders
            if not self.config.dry_run and self.config.pair:
                for order_type, order_id in self.current_orders.items():
                    try:
                        await self.exchange.cancel_order(order_id, self.config.pair)
                        logger.info(f"Cancelled {order_type} order: {order_id}")
                    except Exception as e:
                        logger.error(f"Error cancelling {order_type} order: {e}")
            
            # Reset trade state
            self.config.reset_trade_state()
            self.current_orders.clear()
            self.monitoring = False
            
            logger.info("Trade cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling trade: {e}")
            return False
    
    async def _place_entry_order(self) -> bool:
        """Place entry order"""
        try:
            # Handle market order (entry_price = 0)
            if self.config.entry_price == 0:
                try:
                    # Get current market price
                    ticker = self.exchange.exchange.fetch_ticker(self.config.pair)
                    current_price = ticker['last']
                    self.config.entry_price = current_price
                    self.config.save_config()
                    logger.info(f"Market order: Entry price set to current market price: {current_price}")
                except Exception as e:
                    logger.error(f"Failed to get market price: {e}")
                    return False
            
            if self.config.dry_run:
                logger.info(f"DRY RUN: Would place {self.config.side} entry order for {self.config.amount} {self.config.pair} at {self.config.entry_price}")
                self.config.entry_filled = True
                self.config.position_size = self.config.amount
                self.config.save_config()
                return True
            
            # Place actual limit order for entry
            if self.config.pair and self.config.amount and self.config.entry_price:
                order = await self.exchange.create_limit_order(
                    self.config.pair,
                    'buy' if self.config.side == 'long' else 'sell',
                    self.config.amount,
                    self.config.entry_price
                )
            else:
                return False
            
            if order:
                self.current_orders['entry'] = order['id']
                logger.info(f"Entry order placed: {order['id']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error placing entry order: {e}")
            return False
    
    async def _place_stop_loss(self) -> bool:
        """Place stop loss order"""
        try:
            if not self.config.sl_price or not self.config.position_size:
                return False
            
            if self.config.dry_run:
                logger.info(f"DRY RUN: Would place stop loss at {self.config.sl_price}")
                return True
            
            # Determine stop side (opposite of position)
            stop_side = 'sell' if self.config.side == 'long' else 'buy'
            
            if self.config.pair and self.config.position_size and self.config.sl_price:
                order = await self.exchange.create_stop_order(
                    self.config.pair,
                    stop_side,
                    self.config.position_size,
                    self.config.sl_price
                )
            else:
                return False
            
            if order:
                self.current_orders['sl'] = order['id']
                logger.info(f"Stop loss placed: {order['id']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
            return False
    
    async def _place_take_profit(self, level: int) -> bool:
        """Place take profit order for specified level"""
        try:
            tp_price = None
            tp_percent = None
            
            if level == 1:
                tp_price = self.config.tp1_price
                tp_percent = self.config.tp1_percent
            elif level == 2:
                tp_price = self.config.tp2_price
                tp_percent = self.config.tp2_percent
            elif level == 3:
                tp_price = self.config.tp3_price
                tp_percent = self.config.tp3_percent
            
            if not tp_price or not tp_percent or not self.config.position_size:
                return False
            
            # Calculate partial amount
            partial_amount = (self.config.position_size * tp_percent) / 100
            
            if self.config.dry_run:
                logger.info(f"DRY RUN: Would place TP{level} at {tp_price} for {partial_amount} ({tp_percent}%)")
                return True
            
            # Determine TP side (opposite of position)
            tp_side = 'sell' if self.config.side == 'long' else 'buy'
            
            if self.config.pair:
                order = await self.exchange.create_limit_order(
                    self.config.pair,
                    tp_side,
                    partial_amount,
                    tp_price
                )
            else:
                return False
            
            if order:
                self.current_orders[f'tp{level}'] = order['id']
                logger.info(f"TP{level} placed: {order['id']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error placing TP{level}: {e}")
            return False
    
    async def _update_stop_loss(self, new_price: float) -> bool:
        """Update stop loss to new price"""
        try:
            # Cancel existing stop loss
            if 'sl' in self.current_orders and not self.config.dry_run and self.config.pair:
                await self.exchange.cancel_order(self.current_orders['sl'], self.config.pair)
                del self.current_orders['sl']
            
            # Update config
            self.config.sl_price = new_price
            self.config.save_config()
            
            # Place new stop loss
            return await self._place_stop_loss()
            
        except Exception as e:
            logger.error(f"Error updating stop loss: {e}")
            return False
    
    async def start_monitoring(self):
        """Start trade monitoring loop"""
        self.monitoring = True
        logger.info("Trade monitoring started")
        
        try:
            while self.monitoring and self.config.trade_active:
                await self._monitor_trade()
                await asyncio.sleep(2)  # Check every 2 seconds
                
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.monitoring = False
            logger.info("Trade monitoring stopped")
    
    async def _monitor_trade(self):
        """Monitor active trade"""
        try:
            if not self.config.trade_active:
                return
            
            # Get current price
            if not self.config.pair:
                return
                
            ticker = await self.exchange.get_ticker(self.config.pair)
            if not ticker:
                return
            
            current_price = ticker['last']
            
            # Check entry order if not filled
            if not self.config.entry_filled:
                await self._check_entry_fill()
            
            # If entry is filled, manage the position
            if self.config.entry_filled:
                await self._manage_position(current_price)
            
        except Exception as e:
            logger.error(f"Error in trade monitoring: {e}")
    
    async def _check_entry_fill(self):
        """Check if entry order is filled"""
        try:
            if self.config.dry_run:
                # In dry run, simulate entry fill when price crosses entry
                if not self.config.pair:
                    return
                    
                ticker = await self.exchange.get_ticker(self.config.pair)
                if ticker:
                    current_price = ticker['last']
                    
                    # Check if price has crossed entry level
                    if ((self.config.side == 'long' and current_price <= self.config.entry_price) or
                        (self.config.side == 'short' and current_price >= self.config.entry_price)):
                        
                        self.config.entry_filled = True
                        self.config.position_size = self.config.amount
                        self.config.save_config()
                        
                        logger.info(f"DRY RUN: Entry filled at {current_price}")
                        
                        # Place stop loss and take profits
                        await self._place_stop_loss()
                        await self._place_all_take_profits()
                
                return
            
            # Check actual order status
            if 'entry' in self.current_orders and self.config.pair:
                order = await self.exchange.get_order_status(
                    self.current_orders['entry'], 
                    self.config.pair
                )
                
                if order and order['status'] == 'closed':
                    self.config.entry_filled = True
                    self.config.position_size = order['filled']
                    self.config.save_config()
                    
                    logger.info(f"Entry order filled: {order['filled']} at {order['average']}")
                    
                    # Place stop loss and take profits
                    await self._place_stop_loss()
                    await self._place_all_take_profits()
                    
        except Exception as e:
            logger.error(f"Error checking entry fill: {e}")
    
    async def _place_all_take_profits(self):
        """Place all configured take profit orders"""
        try:
            if self.config.tp1_price:
                await self._place_take_profit(1)
            if self.config.tp2_price:
                await self._place_take_profit(2)
            if self.config.tp3_price:
                await self._place_take_profit(3)
        except Exception as e:
            logger.error(f"Error placing take profits: {e}")
    
    async def _manage_position(self, current_price: float):
        """Manage active position with break-even and trailing stops"""
        try:
            # Check take profit fills
            await self._check_tp_fills()
            
            # Handle break-even logic
            if self.config.breakeven_enabled and not self.config.breakeven_moved:
                await self._check_breakeven(current_price)
            
            # Handle trailing stop
            if self.config.trailing_stop_enabled:
                await self._handle_trailing_stop(current_price)
            
        except Exception as e:
            logger.error(f"Error managing position: {e}")
    
    async def _check_tp_fills(self):
        """Check if take profit orders are filled"""
        try:
            if self.config.dry_run:
                # In dry run mode, simulate TP fills based on current price
                if not self.config.pair:
                    return
                    
                ticker = await self.exchange.get_ticker(self.config.pair)
                if not ticker:
                    return
                    
                current_price = ticker['last']
                
                # Check TP1
                if (self.config.tp1_price and not self.config.tp1_filled and
                    ((self.config.side == 'long' and current_price >= self.config.tp1_price) or
                     (self.config.side == 'short' and current_price <= self.config.tp1_price))):
                    self.config.tp1_filled = True
                    self.config.save_config()
                    logger.info(f"DRY RUN: TP1 filled at {current_price}")
                
                # Check TP2
                if (self.config.tp2_price and not self.config.tp2_filled and
                    ((self.config.side == 'long' and current_price >= self.config.tp2_price) or
                     (self.config.side == 'short' and current_price <= self.config.tp2_price))):
                    self.config.tp2_filled = True
                    self.config.save_config()
                    logger.info(f"DRY RUN: TP2 filled at {current_price}")
                
                # Check TP3
                if (self.config.tp3_price and not self.config.tp3_filled and
                    ((self.config.side == 'long' and current_price >= self.config.tp3_price) or
                     (self.config.side == 'short' and current_price <= self.config.tp3_price))):
                    self.config.tp3_filled = True
                    self.config.save_config()
                    logger.info(f"DRY RUN: TP3 filled at {current_price}")
                
                return
            
            # Check actual order statuses
            for level in [1, 2, 3]:
                order_key = f'tp{level}'
                if order_key in self.current_orders and self.config.pair:
                    order = await self.exchange.get_order_status(
                        self.current_orders[order_key],
                        self.config.pair
                    )
                    
                    if order and order['status'] == 'closed':
                        # Mark TP as filled
                        if level == 1:
                            self.config.tp1_filled = True
                        elif level == 2:
                            self.config.tp2_filled = True
                        elif level == 3:
                            self.config.tp3_filled = True
                        
                        self.config.save_config()
                        logger.info(f"TP{level} filled: {order['filled']} at {order['average']}")
                        
                        # Remove from tracking
                        del self.current_orders[order_key]
            
        except Exception as e:
            logger.error(f"Error checking TP fills: {e}")
    
    async def _check_breakeven(self, current_price: float):
        """Check and execute break-even move"""
        try:
            trigger_hit = False
            
            # Check if break-even trigger is hit
            if self.config.breakeven_trigger == 'tp1' and self.config.tp1_filled:
                trigger_hit = True
            elif self.config.breakeven_trigger == 'tp2' and self.config.tp2_filled:
                trigger_hit = True
            elif self.config.breakeven_trigger == 'tp3' and self.config.tp3_filled:
                trigger_hit = True
            
            if trigger_hit and self.config.entry_price:
                # Move stop loss to break-even (entry price)
                success = await self._update_stop_loss(self.config.entry_price)
                if success:
                    self.config.breakeven_moved = True
                    self.config.save_config()
                    logger.info(f"Stop loss moved to break-even: {self.config.entry_price}")
            
        except Exception as e:
            logger.error(f"Error checking break-even: {e}")
    
    async def _handle_trailing_stop(self, current_price: float):
        """Handle trailing stop logic"""
        try:
            if not self.config.trailing_stop_percent or not self.config.sl_price:
                return
            
            # Update highest/lowest price
            if self.config.side == 'long':
                if not self.config.highest_price or current_price > self.config.highest_price:
                    self.config.highest_price = current_price
                    self.config.trailing_active = True
                    
                    # Calculate new trailing stop
                    trailing_distance = current_price * (self.config.trailing_stop_percent / 100)
                    new_sl = current_price - trailing_distance
                    
                    # Only move stop loss up
                    if new_sl > self.config.sl_price:
                        success = await self._update_stop_loss(new_sl)
                        if success:
                            logger.info(f"Trailing stop updated: {new_sl}")
            
            else:  # short position
                if not self.config.highest_price or current_price < self.config.highest_price:
                    self.config.highest_price = current_price
                    self.config.trailing_active = True
                    
                    # Calculate new trailing stop
                    trailing_distance = current_price * (self.config.trailing_stop_percent / 100)
                    new_sl = current_price + trailing_distance
                    
                    # Only move stop loss down
                    if new_sl < self.config.sl_price:
                        success = await self._update_stop_loss(new_sl)
                        if success:
                            logger.info(f"Trailing stop updated: {new_sl}")
            
            self.config.save_config()
            
        except Exception as e:
            logger.error(f"Error handling trailing stop: {e}")
