"""
Zerodha Kite Connect Integration for Real-time Trading
Provides real-time market data and order execution capabilities

Setup Instructions:
1. Create Kite Connect App: https://kite.trade/
2. Get API Key and Secret
3. Set environment variables:
   export ZERODHA_API_KEY="your_api_key"
   export ZERODHA_API_SECRET="your_api_secret"
4. Install: pip install kiteconnect
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect, KiteTicker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZerodhaDataFeed:
    """
    Real-time and historical data fetching from Zerodha Kite Connect
    
    Features:
    - WebSocket streaming for real-time tick data
    - Historical OHLC data
    - Order book depth (Level 2 data)
    - Bid-Ask spreads
    - Real-time quotes
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, access_token: str = None):
        """
        Initialize Zerodha connection
        
        Args:
            api_key: Kite Connect API key (or from env ZERODHA_API_KEY)
            api_secret: API secret (or from env ZERODHA_API_SECRET)
            access_token: Access token (optional, will generate if not provided)
        """
        self.api_key = api_key or os.getenv('ZERODHA_API_KEY')
        self.api_secret = api_secret or os.getenv('ZERODHA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API credentials required. Set ZERODHA_API_KEY and ZERODHA_API_SECRET "
                "environment variables or pass them as arguments."
            )
        
        # Initialize KiteConnect
        self.kite = KiteConnect(api_key=self.api_key)
        self.ticker = None
        
        # Token management
        self.access_token = access_token
        if self.access_token:
            self.kite.set_access_token(self.access_token)
        
        # Data storage
        self.tick_data = {}
        self.quotes = {}
        self.ohlc_data = {}
        
        # WebSocket callbacks
        self.on_tick_callbacks = []
        self.on_order_update_callbacks = []
        
        logger.info("Zerodha DataFeed initialized")
    
    def login(self) -> str:
        """
        Generate login URL and get request token
        User must visit URL and authorize, then provide request token
        
        Returns:
            Login URL to visit
        """
        login_url = self.kite.login_url()
        logger.info(f"Please visit this URL to login: {login_url}")
        logger.info("After authorization, you'll get a request token in the redirect URL")
        return login_url
    
    def set_access_token_from_request(self, request_token: str) -> str:
        """
        Generate and set access token from request token
        
        Args:
            request_token: Request token from redirect URL after login
            
        Returns:
            Access token (save this for future use)
        """
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        self.access_token = data["access_token"]
        self.kite.set_access_token(self.access_token)
        
        logger.info("Access token generated and set successfully")
        logger.info(f"Save this token for future use: {self.access_token}")
        
        return self.access_token
    
    def get_instruments(self, exchange: str = "NSE") -> pd.DataFrame:
        """
        Get list of all tradable instruments
        
        Args:
            exchange: Exchange name (NSE, BSE, NFO, etc.)
            
        Returns:
            DataFrame with instrument details
        """
        instruments = self.kite.instruments(exchange)
        df = pd.DataFrame(instruments)
        return df
    
    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> int:
        """
        Get instrument token for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'TCS')
            exchange: Exchange name
            
        Returns:
            Instrument token (required for WebSocket subscription)
        """
        instruments = self.get_instruments(exchange)
        instrument = instruments[instruments['tradingsymbol'] == symbol]
        
        if instrument.empty:
            raise ValueError(f"Symbol {symbol} not found on {exchange}")
        
        return int(instrument.iloc[0]['instrument_token'])
    
    def get_quote(self, symbols: List[str], exchange: str = "NSE") -> Dict:
        """
        Get real-time quote for symbols
        
        Args:
            symbols: List of trading symbols
            exchange: Exchange name
            
        Returns:
            Dict with quote data including bid, ask, last price, volume
        """
        # Format symbols for Kite API
        formatted_symbols = [f"{exchange}:{symbol}" for symbol in symbols]
        quotes = self.kite.quote(formatted_symbols)
        
        # Store quotes
        self.quotes.update(quotes)
        
        return quotes
    
    def get_ohlc(self, symbols: List[str], exchange: str = "NSE") -> Dict:
        """
        Get OHLC data for symbols
        
        Args:
            symbols: List of trading symbols
            exchange: Exchange name
            
        Returns:
            Dict with OHLC data
        """
        formatted_symbols = [f"{exchange}:{symbol}" for symbol in symbols]
        ohlc = self.kite.ohlc(formatted_symbols)
        
        self.ohlc_data.update(ohlc)
        return ohlc
    
    def get_historical_data(self,
                           instrument_token: int,
                           from_date: datetime,
                           to_date: datetime,
                           interval: str = "day") -> pd.DataFrame:
        """
        Get historical OHLC data
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: Candle interval (minute, day, 3minute, 5minute, etc.)
            
        Returns:
            DataFrame with OHLC data
        """
        data = self.kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        return df
    
    def start_websocket(self, instrument_tokens: List[int], mode: str = "full"):
        """
        Start WebSocket for real-time tick data
        
        Args:
            instrument_tokens: List of instrument tokens to subscribe
            mode: Subscription mode ('ltp', 'quote', 'full')
                  - ltp: Only last traded price
                  - quote: LTP + OHLC + bid/ask
                  - full: Complete market depth
        """
        if not self.access_token:
            raise ValueError("Access token required for WebSocket. Call login() first.")
        
        # Initialize KiteTicker
        self.ticker = KiteTicker(self.api_key, self.access_token)
        
        # Define callbacks
        def on_ticks(ws, ticks):
            """Callback for tick data"""
            for tick in ticks:
                token = tick['instrument_token']
                self.tick_data[token] = tick
                
                # Log tick info
                logger.debug(f"Tick: {tick.get('tradingsymbol', token)} "
                           f"LTP: {tick.get('last_price', 'N/A')} "
                           f"Volume: {tick.get('volume', 'N/A')}")
                
                # Call registered callbacks
                for callback in self.on_tick_callbacks:
                    callback(tick)
        
        def on_connect(ws, response):
            """Callback on successful connect"""
            logger.info(f"WebSocket connected. Response: {response}")
            
            # Subscribe to instruments
            ws.subscribe(instrument_tokens)
            
            # Set mode
            if mode == "ltp":
                ws.set_mode(ws.MODE_LTP, instrument_tokens)
            elif mode == "quote":
                ws.set_mode(ws.MODE_QUOTE, instrument_tokens)
            elif mode == "full":
                ws.set_mode(ws.MODE_FULL, instrument_tokens)
        
        def on_close(ws, code, reason):
            """Callback on connection close"""
            logger.warning(f"WebSocket closed: {code} - {reason}")
        
        def on_error(ws, code, reason):
            """Callback on error"""
            logger.error(f"WebSocket error: {code} - {reason}")
        
        def on_reconnect(ws, attempts_count):
            """Callback on reconnect"""
            logger.info(f"WebSocket reconnecting... Attempt: {attempts_count}")
        
        def on_noreconnect(ws):
            """Callback when max reconnect attempts exceeded"""
            logger.error("WebSocket max reconnect attempts exceeded")
        
        def on_order_update(ws, data):
            """Callback for order updates"""
            logger.info(f"Order update: {data}")
            for callback in self.on_order_update_callbacks:
                callback(data)
        
        # Assign callbacks
        self.ticker.on_ticks = on_ticks
        self.ticker.on_connect = on_connect
        self.ticker.on_close = on_close
        self.ticker.on_error = on_error
        self.ticker.on_reconnect = on_reconnect
        self.ticker.on_noreconnect = on_noreconnect
        self.ticker.on_order_update = on_order_update
        
        # Start ticker in separate thread
        self.ticker.connect(threaded=True)
        logger.info(f"WebSocket started for {len(instrument_tokens)} instruments")
    
    def stop_websocket(self):
        """Stop WebSocket connection"""
        if self.ticker:
            self.ticker.close()
            logger.info("WebSocket stopped")
    
    def register_tick_callback(self, callback: Callable):
        """Register callback function for tick data"""
        self.on_tick_callbacks.append(callback)
    
    def register_order_callback(self, callback: Callable):
        """Register callback function for order updates"""
        self.on_order_update_callbacks.append(callback)
    
    def get_latest_tick(self, instrument_token: int) -> Optional[Dict]:
        """Get latest tick data for instrument"""
        return self.tick_data.get(instrument_token)
    
    def get_market_depth(self, symbol: str, exchange: str = "NSE") -> Dict:
        """
        Get Level 2 market depth (order book)
        
        Returns:
            Dict with bid/ask depth data
        """
        quote = self.get_quote([symbol], exchange)
        key = f"{exchange}:{symbol}"
        
        if key in quote:
            depth = quote[key].get('depth', {})
            return {
                'buy': depth.get('buy', []),
                'sell': depth.get('sell', [])
            }
        return {'buy': [], 'sell': []}


class ZerodhaTrader:
    """
    Order execution and portfolio management via Zerodha
    
    Features:
    - Order placement (market, limit, SL, SL-M)
    - Order modification and cancellation
    - Position tracking
    - Portfolio management
    - Risk management integration
    """
    
    def __init__(self, kite: KiteConnect):
        """
        Initialize trader with KiteConnect instance
        
        Args:
            kite: Authenticated KiteConnect instance
        """
        self.kite = kite
        self.orders = []
        self.positions = []
        self.holdings = []
        
        logger.info("Zerodha Trader initialized")
    
    def place_order(self,
                   symbol: str,
                   exchange: str,
                   transaction_type: str,
                   quantity: int,
                   order_type: str = "MARKET",
                   product: str = "CNC",
                   price: float = None,
                   trigger_price: float = None,
                   validity: str = "DAY",
                   disclosed_quantity: int = None,
                   tag: str = None) -> str:
        """
        Place an order
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, BSE, etc.)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, SL, SL-M
            product: CNC (delivery), MIS (intraday), NRML (carry forward)
            price: Limit price (for LIMIT and SL orders)
            trigger_price: Trigger price (for SL and SL-M orders)
            validity: DAY or IOC
            disclosed_quantity: Disclosed quantity for iceberg orders
            tag: Custom order tag
            
        Returns:
            Order ID
        """
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product=product,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                disclosed_quantity=disclosed_quantity,
                tag=tag,
                variety=self.kite.VARIETY_REGULAR
            )
            
            logger.info(f"Order placed: {order_id} | {transaction_type} {quantity} {symbol} @ {order_type}")
            return order_id
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise
    
    def modify_order(self,
                    order_id: str,
                    quantity: int = None,
                    price: float = None,
                    trigger_price: float = None,
                    order_type: str = None,
                    validity: str = None) -> str:
        """Modify an existing order"""
        try:
            modified_order_id = self.kite.modify_order(
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                order_type=order_type,
                validity=validity,
                variety=self.kite.VARIETY_REGULAR
            )
            
            logger.info(f"Order modified: {modified_order_id}")
            return modified_order_id
            
        except Exception as e:
            logger.error(f"Order modification failed: {e}")
            raise
    
    def cancel_order(self, order_id: str, variety: str = None) -> str:
        """Cancel an order"""
        try:
            order_id = self.kite.cancel_order(
                order_id=order_id,
                variety=variety or self.kite.VARIETY_REGULAR
            )
            
            logger.info(f"Order cancelled: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            raise
    
    def get_orders(self) -> List[Dict]:
        """Get all orders for the day"""
        self.orders = self.kite.orders()
        return self.orders
    
    def get_order_history(self, order_id: str) -> List[Dict]:
        """Get order history (all modifications/updates)"""
        return self.kite.order_history(order_id)
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        self.positions = self.kite.positions()
        return self.positions
    
    def get_holdings(self) -> List[Dict]:
        """Get holdings (long-term investments)"""
        self.holdings = self.kite.holdings()
        return self.holdings
    
    def get_margins(self) -> Dict:
        """Get available margins"""
        return self.kite.margins()
    
    def place_bracket_order(self,
                           symbol: str,
                           exchange: str,
                           transaction_type: str,
                           quantity: int,
                           price: float,
                           stoploss: float,
                           target: float,
                           trailing_stoploss: float = None) -> str:
        """
        Place bracket order (entry + SL + target)
        Only for intraday
        """
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                validity=self.kite.VALIDITY_DAY,
                variety=self.kite.VARIETY_BO,
                stoploss=stoploss,
                squareoff=target,
                trailing_stoploss=trailing_stoploss
            )
            
            logger.info(f"Bracket order placed: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Bracket order failed: {e}")
            raise
    
    def close_all_positions(self):
        """Emergency: Close all open positions"""
        positions = self.get_positions()
        
        for position_type in ['day', 'net']:
            for pos in positions.get(position_type, []):
                if pos['quantity'] != 0:
                    try:
                        # Determine transaction type (opposite of current position)
                        trans_type = "SELL" if pos['quantity'] > 0 else "BUY"
                        
                        self.place_order(
                            symbol=pos['tradingsymbol'],
                            exchange=pos['exchange'],
                            transaction_type=trans_type,
                            quantity=abs(pos['quantity']),
                            order_type="MARKET",
                            product=pos['product']
                        )
                        
                        logger.info(f"Closed position: {pos['tradingsymbol']}")
                        
                    except Exception as e:
                        logger.error(f"Failed to close {pos['tradingsymbol']}: {e}")


def save_access_token(access_token: str, filepath: str = ".zerodha_token"):
    """Save access token to file"""
    with open(filepath, 'w') as f:
        json.dump({'access_token': access_token, 'timestamp': datetime.now().isoformat()}, f)
    logger.info(f"Access token saved to {filepath}")


def load_access_token(filepath: str = ".zerodha_token") -> Optional[str]:
    """Load access token from file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get('access_token')
    except FileNotFoundError:
        return None


# Example usage
if __name__ == "__main__":
    # Initialize
    feed = ZerodhaDataFeed()
    
    # First time: Generate login URL
    # login_url = feed.login()
    # After visiting URL and getting request_token:
    # access_token = feed.set_access_token_from_request("YOUR_REQUEST_TOKEN")
    # save_access_token(access_token)
    
    # Subsequent times: Load saved token
    # access_token = load_access_token()
    # feed = ZerodhaDataFeed(access_token=access_token)
    
    # Get quote
    # quote = feed.get_quote(['RELIANCE', 'TCS'])
    # print(quote)
    
    # Start real-time streaming
    # tokens = [feed.get_instrument_token('RELIANCE')]
    # feed.start_websocket(tokens, mode='full')
    
    print("Zerodha integration module loaded successfully!")
    print("See docstrings for usage examples.")
