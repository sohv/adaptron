"""
Zerodha Service
Wrapper around Zerodha API for dashboard use
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ZerodhaService:
    """Service layer for Zerodha API operations"""
    
    def __init__(self, api_key: str = None, access_token: str = None):
        self.api_key = api_key or os.getenv("ZERODHA_API_KEY")
        self.access_token = access_token or os.getenv("ZERODHA_ACCESS_TOKEN")
        
        if not self.api_key:
            raise ValueError("Zerodha API key not provided")
            
        self.kite = KiteConnect(api_key=self.api_key)
        if self.access_token:
            self.kite.set_access_token(self.access_token)
    
    def get_quote(self, symbols: List[str], exchange: str = "NSE") -> Dict:
        """Get real-time quotes"""
        try:
            instruments = [f"{exchange}:{symbol}" for symbol in symbols]
            return self.kite.quote(instruments)
        except Exception as e:
            logger.error(f"Error fetching quotes: {str(e)}")
            raise
    
    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day"
    ) -> List[Dict]:
        """Get historical OHLC data"""
        try:
            return self.kite.historical_data(
                instrument_token,
                from_date,
                to_date,
                interval
            )
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise
    
    def get_holdings(self) -> List[Dict]:
        """Get current holdings"""
        try:
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Error fetching holdings: {str(e)}")
            raise
    
    def get_positions(self) -> Dict:
        """Get open positions"""
        try:
            return self.kite.positions()
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            raise
    
    def get_orders(self) -> List[Dict]:
        """Get order history"""
        try:
            return self.kite.orders()
        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}")
            raise
    
    def get_instruments(self, exchange: str = "NSE") -> List[Dict]:
        """Get all instruments for an exchange"""
        try:
            return self.kite.instruments(exchange)
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            raise
    
    def get_market_depth(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get market depth (order book)"""
        try:
            instrument = f"{exchange}:{symbol}"
            quote = self.kite.quote(instrument)
            return quote[instrument].get("depth", {})
        except Exception as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            raise
    
    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        product: str = "CNC",
        price: float = None
    ) -> str:
        """Place an order"""
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price
            )
            return order_id
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise
