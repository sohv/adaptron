"""
Zerodha Kite Connect Integration
Real-time data with <100ms latency (₹2,000/month subscription required)
"""

from .data_zerodha import (
    fetch_historical_data_zerodha,
    get_instrument_token,
    fetch_realtime_quote_zerodha,
    fetch_market_depth_zerodha,
    add_technical_indicators_zerodha,
    prepare_data_zerodha,
    get_latest_market_data_zerodha,
    calculate_slippage_zerodha
)

from .zerodha_integration import (
    ZerodhaDataFeed,
    ZerodhaTrader
)

__all__ = [
    'fetch_historical_data_zerodha',
    'get_instrument_token',
    'fetch_realtime_quote_zerodha',
    'fetch_market_depth_zerodha',
    'add_technical_indicators_zerodha',
    'prepare_data_zerodha',
    'get_latest_market_data_zerodha',
    'calculate_slippage_zerodha',
    'ZerodhaDataFeed',
    'ZerodhaTrader'
]
