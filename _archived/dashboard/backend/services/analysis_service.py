"""
Analysis Service
Technical and fundamental analysis calculations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class TechnicalAnalysisService:
    """Calculate technical indicators and generate signals"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def get_trading_signal(
        current_price: float,
        rsi: float,
        macd_histogram: float,
        sma_50: float,
        sma_200: float
    ) -> Dict:
        """Generate trading signal based on indicators"""
        signals = []
        overall_score = 0
        
        # RSI signals
        if rsi < 30:
            signals.append("RSI oversold (bullish)")
            overall_score += 1
        elif rsi > 70:
            signals.append("RSI overbought (bearish)")
            overall_score -= 1
        
        # MACD signals
        if macd_histogram > 0:
            signals.append("MACD bullish")
            overall_score += 1
        else:
            signals.append("MACD bearish")
            overall_score -= 1
        
        # Moving average crossover
        if current_price > sma_50 > sma_200:
            signals.append("Price above moving averages (bullish)")
            overall_score += 2
        elif current_price < sma_50 < sma_200:
            signals.append("Price below moving averages (bearish)")
            overall_score -= 2
        
        # Determine overall signal
        if overall_score >= 2:
            signal = "buy"
            confidence = min(overall_score / 4, 1.0)
        elif overall_score <= -2:
            signal = "sell"
            confidence = min(abs(overall_score) / 4, 1.0)
        else:
            signal = "hold"
            confidence = 0.5
        
        return {
            "signal": signal,
            "confidence": confidence,
            "score": overall_score,
            "reasons": signals
        }
    
    @staticmethod
    def find_support_resistance(
        df: pd.DataFrame,
        window: int = 20
    ) -> Tuple[List[float], List[float]]:
        """Find support and resistance levels"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        # Find local maxima (resistance)
        resistance = df[df['high'] == highs]['high'].unique()
        
        # Find local minima (support)
        support = df[df['low'] == lows]['low'].unique()
        
        return sorted(support.tolist()), sorted(resistance.tolist(), reverse=True)


class FundamentalAnalysisService:
    """Fundamental analysis calculations and valuation"""
    
    @staticmethod
    def calculate_intrinsic_value_pe(
        eps: float,
        industry_pe: float,
        growth_rate: float
    ) -> float:
        """Calculate intrinsic value using P/E method"""
        adjusted_pe = industry_pe * (1 + growth_rate)
        return eps * adjusted_pe
    
    @staticmethod
    def calculate_intrinsic_value_dcf(
        free_cash_flow: float,
        growth_rate: float,
        discount_rate: float,
        years: int = 5
    ) -> float:
        """Calculate intrinsic value using DCF"""
        pv_sum = 0
        for year in range(1, years + 1):
            fcf = free_cash_flow * ((1 + growth_rate) ** year)
            pv = fcf / ((1 + discount_rate) ** year)
            pv_sum += pv
        
        # Terminal value
        terminal_fcf = free_cash_flow * ((1 + growth_rate) ** years)
        terminal_value = terminal_fcf / (discount_rate - growth_rate)
        terminal_pv = terminal_value / ((1 + discount_rate) ** years)
        
        return pv_sum + terminal_pv
    
    @staticmethod
    def evaluate_fundamentals(
        pe_ratio: float,
        pb_ratio: float,
        roe: float,
        debt_to_equity: float,
        dividend_yield: float
    ) -> Dict:
        """Evaluate fundamental health"""
        score = 0
        signals = []
        
        # P/E evaluation
        if pe_ratio < 15:
            signals.append("Undervalued P/E")
            score += 1
        elif pe_ratio > 30:
            signals.append("Overvalued P/E")
            score -= 1
        
        # P/B evaluation
        if pb_ratio < 1:
            signals.append("Trading below book value")
            score += 1
        
        # ROE evaluation
        if roe > 15:
            signals.append("Strong ROE")
            score += 1
        elif roe < 5:
            signals.append("Weak ROE")
            score -= 1
        
        # Debt evaluation
        if debt_to_equity < 0.5:
            signals.append("Low debt")
            score += 1
        elif debt_to_equity > 2:
            signals.append("High debt")
            score -= 1
        
        # Dividend evaluation
        if dividend_yield > 2:
            signals.append("Good dividend yield")
            score += 1
        
        return {
            "score": score,
            "rating": "Strong Buy" if score >= 3 else "Buy" if score >= 1 else "Hold" if score >= -1 else "Sell",
            "signals": signals
        }
