import ccxt
import asyncio
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class ExchangeManager:
    """Manages exchange connections and trading operations"""
    
    def __init__(self):
        self.exchange = None
        self.testnet = os.getenv("TOOBIT_TESTNET", "true").lower() == "true"
        self.initialize_exchange()
    
    def initialize_exchange(self):
        """Initialize Toobit exchange connection"""
        try:
            api_key = os.getenv("TOOBIT_API_KEY", "")
            api_secret = os.getenv("TOOBIT_API_SECRET", "")
            
            # Initialize exchange (using a generic exchange for now, can be configured)
            # Note: Toobit might not be directly supported by ccxt, using binance as template
            # Users should configure their specific exchange in environment variables
            try:
                self.exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'sandbox': self.testnet,
                    'defaultType': 'future',  # USDT-M Perpetual Futures
                    'options': {
                        'defaultType': 'future'
                    }
                })
            except:
                # Fallback to generic exchange for testing
                self.exchange = None
                logger.warning("Exchange initialization failed - running in simulation mode")
            
            logger.info(f"Toobit exchange initialized (testnet: {self.testnet})")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            self.exchange = None
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker for symbol"""
        try:
            if not self.exchange:
                return None
            
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.fetch_ticker, symbol
            )
            return dict(ticker) if ticker else None
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def get_balance(self) -> Optional[Dict[str, Any]]:
        """Get account balance"""
        try:
            if not self.exchange:
                return None
            
            balance = await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.fetch_balance
            )
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    async def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Create market order"""
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return None
            
            if params is None:
                params = {}
            
            order = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.exchange.create_market_order(symbol, side, amount, None, params)
            )
            
            logger.info(f"Market order created: {order}")
            return dict(order) if order else None
            
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    async def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Create limit order"""
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return None
            
            if params is None:
                params = {}
            
            order = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.exchange.create_limit_order(symbol, side, amount, price, params)
            )
            
            logger.info(f"Limit order created: {order}")
            return dict(order) if order else None
            
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            return None
    
    async def create_stop_order(self, symbol: str, side: str, amount: float, price: float, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Create stop order"""
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return None
            
            if params is None:
                params = {}
            
            # Set stop price
            params['stopPrice'] = price
            
            order = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.exchange.create_order(symbol, 'stop_market', side, amount, None, params)
            )
            
            logger.info(f"Stop order created: {order}")
            return dict(order) if order else None
            
        except Exception as e:
            logger.error(f"Error creating stop order: {e}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel order"""
        try:
            if not self.exchange:
                return False
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.cancel_order,
                order_id, symbol
            )
            
            logger.info(f"Order {order_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order status"""
        try:
            if not self.exchange:
                return None
            
            order = await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.fetch_order,
                order_id, symbol
            )
            
            return dict(order) if order else None
            
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
    
    async def get_positions(self, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get current positions"""
        try:
            if not self.exchange:
                return None
            
            positions = await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.fetch_positions,
                [symbol] if symbol else None
            )
            
            return [dict(pos) for pos in positions] if positions else None
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            if not self.exchange:
                return False
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.set_leverage,
                leverage, symbol
            )
            
            logger.info(f"Leverage set to {leverage} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return False
