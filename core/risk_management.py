"""
Risk Management System
Production-ready risk controls for trading agent

Features:
- Stop-loss management
- Position size limits
- Daily loss limits
- Circuit breakers
- Volatility-based sizing
- Drawdown protection
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, date
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    Comprehensive risk management system
    
    Protects against:
    - Excessive single-position risk
    - Daily losses exceeding limits
    - Trading during high volatility
    - Maximum drawdown breaches
    - Overtrading
    """
    
    def __init__(self,
                 max_position_size: float = 0.20,      # Max 20% per position
                 max_portfolio_risk: float = 1.0,       # Max 100% total exposure
                 stop_loss_pct: float = 0.02,           # 2% stop-loss per position
                 daily_loss_limit: float = 0.05,        # 5% max daily loss
                 max_trades_per_day: int = 50,          # Max trades per day
                 max_drawdown: float = 0.15,            # 15% max drawdown
                 volatility_threshold: float = 0.03,    # 3% volatility threshold
                 min_balance: float = 10000.0):         # Minimum balance to trade
        """
        Initialize risk manager
        
        Args:
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum total exposure
            stop_loss_pct: Stop-loss percentage per position
            daily_loss_limit: Maximum daily loss as fraction
            max_trades_per_day: Maximum number of trades per day
            max_drawdown: Maximum drawdown from peak
            volatility_threshold: Volatility threshold for position sizing
            min_balance: Minimum balance required to continue trading
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.stop_loss_pct = stop_loss_pct
        self.daily_loss_limit = daily_loss_limit
        self.max_trades_per_day = max_trades_per_day
        self.max_drawdown = max_drawdown
        self.volatility_threshold = volatility_threshold
        self.min_balance = min_balance
        
        # Tracking
        self.positions = {}  # {symbol: position_info}
        self.daily_start_value = None
        self.peak_portfolio_value = None
        self.trades_today = 0
        self.current_date = None
        self.trading_enabled = True
        self.circuit_breaker_triggered = False
        
        # Historical tracking
        self.trade_history = []
        self.daily_pnl = []
        
        logger.info("Risk Manager initialized")
        logger.info(f"  Max position size: {max_position_size*100:.1f}%")
        logger.info(f"  Stop-loss: {stop_loss_pct*100:.1f}%")
        logger.info(f"  Daily loss limit: {daily_loss_limit*100:.1f}%")
        logger.info(f"  Max drawdown: {max_drawdown*100:.1f}%")
    
    def reset_daily_counters(self, portfolio_value: float):
        """Reset daily counters at market open"""
        today = date.today()
        
        if self.current_date != today:
            self.current_date = today
            self.daily_start_value = portfolio_value
            self.trades_today = 0
            
            if self.peak_portfolio_value is None:
                self.peak_portfolio_value = portfolio_value
            else:
                self.peak_portfolio_value = max(self.peak_portfolio_value, portfolio_value)
            
            # Re-enable trading if it was disabled yesterday
            if self.circuit_breaker_triggered:
                logger.info("🟢 New day - re-enabling trading")
                self.circuit_breaker_triggered = False
                self.trading_enabled = True
            
            logger.info(f"Daily counters reset. Start value: ₹{portfolio_value:,.2f}")
    
    def check_daily_loss_limit(self, current_value: float) -> Tuple[bool, str]:
        """
        Check if daily loss limit exceeded
        
        Returns:
            (can_trade, reason)
        """
        if self.daily_start_value is None:
            return True, ""
        
        loss = (self.daily_start_value - current_value) / self.daily_start_value
        
        if loss > self.daily_loss_limit:
            self.circuit_breaker_triggered = True
            self.trading_enabled = False
            reason = f"🔴 CIRCUIT BREAKER: Daily loss {loss*100:.2f}% exceeds limit {self.daily_loss_limit*100:.1f}%"
            logger.critical(reason)
            return False, reason
        
        return True, ""
    
    def check_max_drawdown(self, current_value: float) -> Tuple[bool, str]:
        """
        Check if maximum drawdown exceeded
        
        Returns:
            (can_trade, reason)
        """
        if self.peak_portfolio_value is None:
            return True, ""
        
        drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
        
        if drawdown > self.max_drawdown:
            self.circuit_breaker_triggered = True
            self.trading_enabled = False
            reason = f"🔴 CIRCUIT BREAKER: Drawdown {drawdown*100:.2f}% exceeds limit {self.max_drawdown*100:.1f}%"
            logger.critical(reason)
            return False, reason
        
        return True, ""
    
    def check_min_balance(self, balance: float) -> Tuple[bool, str]:
        """Check if balance is above minimum"""
        if balance < self.min_balance:
            self.trading_enabled = False
            reason = f"⚠️  Balance ₹{balance:,.2f} below minimum ₹{self.min_balance:,.2f}"
            logger.warning(reason)
            return False, reason
        
        return True, ""
    
    def check_trade_limit(self) -> Tuple[bool, str]:
        """Check if max trades per day exceeded"""
        if self.trades_today >= self.max_trades_per_day:
            reason = f"⚠️  Max trades per day ({self.max_trades_per_day}) reached"
            logger.warning(reason)
            return False, reason
        
        return True, ""
    
    def calculate_position_size(self,
                                action: float,
                                balance: float,
                                portfolio_value: float,
                                current_price: float,
                                volatility: float = None) -> int:
        """
        Calculate safe position size based on risk parameters
        
        Args:
            action: Model action (-1 to 1)
            balance: Available cash
            portfolio_value: Total portfolio value
            current_price: Current stock price
            volatility: Stock volatility (optional)
            
        Returns:
            Number of shares to trade
        """
        # Base position size from action
        base_position_value = abs(action) * balance
        
        # Apply max position size limit
        max_position_value = portfolio_value * self.max_position_size
        position_value = min(base_position_value, max_position_value)
        
        # Adjust for volatility if provided
        if volatility is not None and volatility > self.volatility_threshold:
            # Reduce position size in high volatility
            volatility_factor = self.volatility_threshold / volatility
            position_value *= volatility_factor
            logger.info(f"High volatility ({volatility:.2%}) - reduced position by {(1-volatility_factor)*100:.1f}%")
        
        # Convert to shares
        shares = int(position_value / current_price)
        
        # Ensure we have enough balance
        if shares * current_price > balance:
            shares = int(balance / current_price)
        
        return shares
    
    def add_position(self,
                    symbol: str,
                    entry_price: float,
                    quantity: int,
                    timestamp: datetime = None):
        """Record new position with stop-loss"""
        if timestamp is None:
            timestamp = datetime.now()
        
        stop_loss_price = entry_price * (1 - self.stop_loss_pct)
        
        self.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss_price': stop_loss_price,
            'entry_time': timestamp,
            'highest_price': entry_price
        }
        
        self.trades_today += 1
        
        logger.info(f"Position added: {symbol} - {quantity} @ ₹{entry_price:.2f}, SL: ₹{stop_loss_price:.2f}")
    
    def update_position(self, symbol: str, current_price: float):
        """Update position with trailing stop-loss"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        
        # Update highest price for trailing stop
        if current_price > pos['highest_price']:
            pos['highest_price'] = current_price
            # Update trailing stop-loss
            pos['stop_loss_price'] = current_price * (1 - self.stop_loss_pct)
            logger.debug(f"Trailing SL updated for {symbol}: ₹{pos['stop_loss_price']:.2f}")
    
    def check_stop_loss(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """
        Check if stop-loss triggered
        
        Returns:
            (should_exit, reason)
        """
        if symbol not in self.positions:
            return False, ""
        
        pos = self.positions[symbol]
        
        if current_price <= pos['stop_loss_price']:
            loss_pct = (pos['entry_price'] - current_price) / pos['entry_price']
            reason = f"⚠️  STOP-LOSS triggered: {symbol} @ ₹{current_price:.2f} (Loss: {loss_pct*100:.2f}%)"
            logger.warning(reason)
            return True, reason
        
        return False, ""
    
    def remove_position(self, symbol: str, exit_price: float, timestamp: datetime = None):
        """Remove position after exit"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        pnl = (exit_price - pos['entry_price']) * pos['quantity']
        pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price']
        
        # Record trade
        self.trade_history.append({
            'symbol': symbol,
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'quantity': pos['quantity'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': pos['entry_time'],
            'exit_time': timestamp or datetime.now(),
            'stop_loss_hit': exit_price <= pos['stop_loss_price']
        })
        
        del self.positions[symbol]
        
        logger.info(f"Position closed: {symbol} - P&L: ₹{pnl:,.2f} ({pnl_pct*100:.2f}%)")
    
    def can_trade(self, portfolio_value: float, balance: float) -> Tuple[bool, str]:
        """
        Check all risk conditions before allowing trade
        
        Returns:
            (can_trade, reason)
        """
        # Reset daily counters if new day
        self.reset_daily_counters(portfolio_value)
        
        # Check if circuit breaker triggered
        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered - trading disabled"
        
        if not self.trading_enabled:
            return False, "Trading manually disabled"
        
        # Check daily loss limit
        can_trade, reason = self.check_daily_loss_limit(portfolio_value)
        if not can_trade:
            return False, reason
        
        # Check max drawdown
        can_trade, reason = self.check_max_drawdown(portfolio_value)
        if not can_trade:
            return False, reason
        
        # Check minimum balance
        can_trade, reason = self.check_min_balance(balance)
        if not can_trade:
            return False, reason
        
        # Check trade limit
        can_trade, reason = self.check_trade_limit()
        if not can_trade:
            return False, reason
        
        return True, ""
    
    def get_risk_metrics(self, portfolio_value: float) -> Dict:
        """Get current risk metrics"""
        metrics = {
            'trading_enabled': self.trading_enabled,
            'circuit_breaker': self.circuit_breaker_triggered,
            'trades_today': self.trades_today,
            'max_trades': self.max_trades_per_day,
            'open_positions': len(self.positions),
            'portfolio_value': portfolio_value
        }
        
        if self.daily_start_value:
            daily_pnl = portfolio_value - self.daily_start_value
            daily_pnl_pct = daily_pnl / self.daily_start_value
            metrics['daily_pnl'] = daily_pnl
            metrics['daily_pnl_pct'] = daily_pnl_pct
        
        if self.peak_portfolio_value:
            drawdown = (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
            metrics['current_drawdown'] = drawdown
            metrics['peak_value'] = self.peak_portfolio_value
        
        return metrics
    
    def save_state(self, filepath: str = "./logs/risk_state.json"):
        """Save risk manager state"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        state = {
            'positions': self.positions,
            'daily_start_value': self.daily_start_value,
            'peak_portfolio_value': self.peak_portfolio_value,
            'trades_today': self.trades_today,
            'current_date': str(self.current_date),
            'trading_enabled': self.trading_enabled,
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'trade_history': self.trade_history[-100:]  # Last 100 trades
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Risk state saved to {filepath}")
    
    def load_state(self, filepath: str = "./logs/risk_state.json"):
        """Load risk manager state"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.positions = state.get('positions', {})
            self.daily_start_value = state.get('daily_start_value')
            self.peak_portfolio_value = state.get('peak_portfolio_value')
            self.trades_today = state.get('trades_today', 0)
            self.trading_enabled = state.get('trading_enabled', True)
            self.circuit_breaker_triggered = state.get('circuit_breaker_triggered', False)
            self.trade_history = state.get('trade_history', [])
            
            logger.info(f"Risk state loaded from {filepath}")
            
        except FileNotFoundError:
            logger.warning(f"No saved state found at {filepath}")
    
    def emergency_stop(self, reason: str = "Manual intervention"):
        """Emergency stop - disable all trading"""
        self.trading_enabled = False
        self.circuit_breaker_triggered = True
        logger.critical(f"🔴 EMERGENCY STOP: {reason}")
    
    def resume_trading(self):
        """Resume trading after emergency stop (use with caution!)"""
        logger.warning("⚠️  Manually resuming trading...")
        self.trading_enabled = True
        self.circuit_breaker_triggered = False


if __name__ == "__main__":
    # Test
    rm = RiskManager()
    
    # Simulate trading
    portfolio_value = 100000
    balance = 100000
    
    can_trade, reason = rm.can_trade(portfolio_value, balance)
    print(f"Can trade: {can_trade}, Reason: {reason}")
    
    # Add position
    rm.add_position("RELIANCE", 2500, 10)
    
    # Check stop-loss
    should_exit, reason = rm.check_stop_loss("RELIANCE", 2450)
    print(f"Should exit: {should_exit}, Reason: {reason}")
    
    # Get metrics
    metrics = rm.get_risk_metrics(portfolio_value)
    print("Risk metrics:", metrics)
