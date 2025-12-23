"""
Monitoring and Alerting System
Real-time monitoring, health checks, and alerts for trading agent

Features:
- Performance tracking (P&L, Sharpe, drawdown)
- System health monitoring (latency, errors, data quality)
- Alert system (Email, SMS, Telegram)
- Trade logging and audit trail
- Dashboard metrics
"""

import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Track trading performance metrics"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        
        self.peak_equity = initial_capital
        self.max_drawdown = 0.0
        
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        
    def add_trade(self, trade: Dict):
        """Record a trade"""
        self.trades.append({
            **trade,
            'timestamp': datetime.now()
        })
        
        pnl = trade.get('pnl', 0)
        self.total_pnl += pnl
        
        if pnl > 0:
            self.wins += 1
        elif pnl < 0:
            self.losses += 1
    
    def update_equity(self, current_value: float):
        """Update equity curve"""
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'value': current_value
        })
        
        # Update peak and drawdown
        if current_value > self.peak_equity:
            self.peak_equity = current_value
        
        drawdown = (self.peak_equity - current_value) / self.peak_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def get_metrics(self) -> Dict:
        """Calculate performance metrics"""
        total_trades = len(self.trades)
        win_rate = self.wins / total_trades if total_trades > 0 else 0
        
        current_equity = self.equity_curve[-1]['value'] if self.equity_curve else self.initial_capital
        total_return = (current_equity - self.initial_capital) / self.initial_capital
        
        # Calculate Sharpe ratio (simplified)
        if len(self.daily_returns) > 0:
            returns = np.array(self.daily_returns)
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        return {
            'total_trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'total_return': total_return,
            'current_equity': current_equity,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe,
            'peak_equity': self.peak_equity
        }


class HealthMonitor:
    """Monitor system health and data quality"""
    
    def __init__(self, max_latency_ms: float = 100.0):
        self.max_latency_ms = max_latency_ms
        self.latencies = deque(maxlen=100)
        self.errors = deque(maxlen=100)
        self.data_quality_checks = deque(maxlen=100)
        
        self.last_data_update = None
        self.consecutive_errors = 0
        
    def record_latency(self, latency_ms: float):
        """Record data feed latency"""
        self.latencies.append({
            'timestamp': datetime.now(),
            'latency_ms': latency_ms
        })
        
        if latency_ms > self.max_latency_ms:
            logger.warning(f"⚠️  High latency: {latency_ms:.2f}ms (threshold: {self.max_latency_ms}ms)")
    
    def record_error(self, error_type: str, error_msg: str):
        """Record system error"""
        self.errors.append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': error_msg
        })
        
        self.consecutive_errors += 1
        
        if self.consecutive_errors >= 5:
            logger.critical(f"🔴 CRITICAL: {self.consecutive_errors} consecutive errors!")
    
    def clear_errors(self):
        """Clear error counter after successful operation"""
        self.consecutive_errors = 0
    
    def check_data_quality(self, data: Dict) -> bool:
        """
        Check if market data is valid
        
        Returns:
            True if data is valid
        """
        checks = {
            'has_price': 'last_price' in data and data['last_price'] > 0,
            'has_volume': 'volume' in data,
            'recent_timestamp': True  # Add timestamp check if available
        }
        
        self.data_quality_checks.append({
            'timestamp': datetime.now(),
            'checks': checks,
            'passed': all(checks.values())
        })
        
        self.last_data_update = datetime.now()
        
        if not all(checks.values()):
            logger.warning(f"⚠️  Data quality issue: {checks}")
            return False
        
        return True
    
    def check_data_staleness(self, max_age_seconds: int = 60) -> bool:
        """
        Check if data is stale
        
        Returns:
            True if data is fresh
        """
        if self.last_data_update is None:
            return False
        
        age = (datetime.now() - self.last_data_update).total_seconds()
        
        if age > max_age_seconds:
            logger.warning(f"⚠️  Stale data: Last update {age:.1f}s ago")
            return False
        
        return True
    
    def get_health_status(self) -> Dict:
        """Get overall system health"""
        avg_latency = np.mean([l['latency_ms'] for l in self.latencies]) if self.latencies else 0
        error_rate = len([e for e in self.errors if (datetime.now() - e['timestamp']).seconds < 300]) / 5  # Last 5 minutes
        
        data_freshness = self.check_data_staleness()
        
        health_score = 100
        if avg_latency > self.max_latency_ms:
            health_score -= 20
        if error_rate > 0.1:
            health_score -= 30
        if not data_freshness:
            health_score -= 50
        
        status = "HEALTHY"
        if health_score < 80:
            status = "DEGRADED"
        if health_score < 50:
            status = "CRITICAL"
        
        return {
            'status': status,
            'health_score': max(0, health_score),
            'avg_latency_ms': avg_latency,
            'error_rate': error_rate,
            'consecutive_errors': self.consecutive_errors,
            'data_fresh': data_freshness,
            'last_update': self.last_data_update
        }


class AlertManager:
    """Send alerts via multiple channels"""
    
    def __init__(self,
                 email_config: Optional[Dict] = None,
                 telegram_config: Optional[Dict] = None):
        """
        Initialize alert manager
        
        Args:
            email_config: {'smtp_server', 'smtp_port', 'username', 'password', 'to_email'}
            telegram_config: {'bot_token', 'chat_id'}
        """
        self.email_config = email_config
        self.telegram_config = telegram_config
        
        self.alert_history = deque(maxlen=100)
        self.last_alert_time = {}
        self.min_alert_interval = 300  # 5 minutes between similar alerts
        
    def should_send_alert(self, alert_type: str) -> bool:
        """Rate limit alerts to avoid spam"""
        now = datetime.now()
        
        if alert_type in self.last_alert_time:
            time_since_last = (now - self.last_alert_time[alert_type]).total_seconds()
            if time_since_last < self.min_alert_interval:
                return False
        
        self.last_alert_time[alert_type] = now
        return True
    
    def send_email(self, subject: str, body: str):
        """Send email alert"""
        if not self.email_config:
            logger.warning("Email not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = f"[Trading Agent] {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
    
    def send_telegram(self, message: str):
        """Send Telegram alert"""
        if not self.telegram_config:
            logger.warning("Telegram not configured")
            return
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            data = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info("Telegram alert sent")
            else:
                logger.error(f"Telegram failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram: {str(e)}")
    
    def alert(self, alert_type: str, severity: str, message: str):
        """
        Send alert through configured channels
        
        Args:
            alert_type: Type of alert (e.g., 'stop_loss', 'circuit_breaker')
            severity: 'INFO', 'WARNING', 'CRITICAL'
            message: Alert message
        """
        if not self.should_send_alert(alert_type):
            return
        
        self.alert_history.append({
            'timestamp': datetime.now(),
            'type': alert_type,
            'severity': severity,
            'message': message
        })
        
        # Format message
        formatted_msg = f"""
[{severity}] {alert_type.upper()}

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send through all channels
        if severity in ['WARNING', 'CRITICAL']:
            if self.email_config:
                self.send_email(f"{severity}: {alert_type}", formatted_msg)
            
            if self.telegram_config:
                self.send_telegram(formatted_msg)
        
        # Log
        log_func = {
            'INFO': logger.info,
            'WARNING': logger.warning,
            'CRITICAL': logger.critical
        }.get(severity, logger.info)
        
        log_func(formatted_msg)


class TradingMonitor:
    """
    Complete monitoring system for trading agent
    Combines performance, health, and alerting
    """
    
    def __init__(self,
                 initial_capital: float = 100000.0,
                 email_config: Optional[Dict] = None,
                 telegram_config: Optional[Dict] = None):
        
        self.performance = PerformanceMonitor(initial_capital)
        self.health = HealthMonitor()
        self.alerts = AlertManager(email_config, telegram_config)
        
        self.start_time = datetime.now()
        
        logger.info("Trading Monitor initialized")
    
    def record_trade(self, trade: Dict):
        """Record a completed trade"""
        self.performance.add_trade(trade)
        
        # Alert on large loss
        if trade.get('pnl', 0) < -5000:
            self.alerts.alert(
                'large_loss',
                'WARNING',
                f"Large loss: ₹{trade['pnl']:,.2f} on {trade.get('symbol', 'Unknown')}"
            )
    
    def update_portfolio(self, portfolio_value: float):
        """Update portfolio value"""
        self.performance.update_equity(portfolio_value)
        
        # Check drawdown
        metrics = self.performance.get_metrics()
        if metrics['max_drawdown'] > 0.10:  # 10% drawdown
            self.alerts.alert(
                'high_drawdown',
                'CRITICAL',
                f"Drawdown reached {metrics['max_drawdown']*100:.2f}%"
            )
    
    def check_health(self, latency_ms: float, data: Dict):
        """Check system health"""
        self.health.record_latency(latency_ms)
        self.health.check_data_quality(data)
        
        health = self.health.get_health_status()
        
        if health['status'] == 'CRITICAL':
            self.alerts.alert(
                'system_health',
                'CRITICAL',
                f"System health critical: {health}"
            )
    
    def get_dashboard(self) -> Dict:
        """Get dashboard metrics"""
        perf = self.performance.get_metrics()
        health = self.health.get_health_status()
        
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return {
            'performance': perf,
            'health': health,
            'uptime_hours': uptime,
            'recent_alerts': list(self.alerts.alert_history)[-10:]
        }
    
    def save_logs(self, filepath: str = "./logs/monitor_state.json"):
        """Save monitoring state"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        dashboard = self.get_dashboard()
        
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)
        
        logger.info(f"Monitoring state saved to {filepath}")


if __name__ == "__main__":
    # Test monitoring
    monitor = TradingMonitor(initial_capital=100000)
    
    # Simulate trade
    monitor.record_trade({
        'symbol': 'RELIANCE',
        'entry_price': 2500,
        'exit_price': 2550,
        'quantity': 10,
        'pnl': 500
    })
    
    # Update portfolio
    monitor.update_portfolio(100500)
    
    # Check health
    monitor.check_health(latency_ms=50, data={'last_price': 2550, 'volume': 1000})
    
    # Get dashboard
    dashboard = monitor.get_dashboard()
    print("Dashboard:", json.dumps(dashboard, indent=2, default=str))
