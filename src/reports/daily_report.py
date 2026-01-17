"""
Daily Report Module

Manages daily trading reports with portfolio snapshots, trade records, and P&L tracking.
Reports are persisted as JSON files in data/reports/YYYY-MM-DD.json
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PositionSnapshot:
    """Position state at snapshot time"""
    symbol: str
    quantity: float
    side: str  # "long" | "short"
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


@dataclass
class PortfolioSnapshot:
    """Point-in-time portfolio state"""
    timestamp: str
    snapshot_type: str  # "market_open" | "market_close" | "manual"
    cash: float
    equity: float
    portfolio_value: float
    buying_power: float
    positions: List[PositionSnapshot] = field(default_factory=list)
    total_positions: int = 0
    current_exposure: float = 0.0
    daily_pnl: float = 0.0

    def __post_init__(self):
        # Convert dict positions to PositionSnapshot objects if needed
        if self.positions and isinstance(self.positions[0], dict):
            self.positions = [PositionSnapshot(**p) for p in self.positions]
        self.total_positions = len(self.positions)


@dataclass
class TradeRecord:
    """Individual trade execution record"""
    timestamp: str
    symbol: str
    side: str  # "buy" | "sell"
    quantity: float
    price: float
    total_value: float
    signal_confidence: float
    llm_provider: str
    reasoning: str = ""
    realized_pnl: Optional[float] = None
    execution_status: str = "executed"  # "executed" | "blocked" | "rejected"
    block_reason: Optional[str] = None


@dataclass
class DailyReport:
    """Complete daily trading report"""
    date: str  # YYYY-MM-DD format
    market_open_snapshot: Optional[PortfolioSnapshot] = None
    market_close_snapshot: Optional[PortfolioSnapshot] = None
    trades: List[TradeRecord] = field(default_factory=list)
    blocked_trades: List[TradeRecord] = field(default_factory=list)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    signals_analyzed: int = 0
    signals_actioned: int = 0
    win_count: int = 0
    loss_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        # Convert dict snapshots to objects if needed
        if self.market_open_snapshot and isinstance(self.market_open_snapshot, dict):
            self.market_open_snapshot = PortfolioSnapshot(**self.market_open_snapshot)
        if self.market_close_snapshot and isinstance(self.market_close_snapshot, dict):
            self.market_close_snapshot = PortfolioSnapshot(**self.market_close_snapshot)
        # Convert dict trades to TradeRecord objects if needed
        if self.trades and isinstance(self.trades[0], dict):
            self.trades = [TradeRecord(**t) for t in self.trades]
        if self.blocked_trades and isinstance(self.blocked_trades[0], dict):
            self.blocked_trades = [TradeRecord(**t) for t in self.blocked_trades]

    @property
    def trade_count(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        total = self.win_count + self.loss_count
        return (self.win_count / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        def convert(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: convert(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return obj

        return convert(self)


class DailyReportManager:
    """Manages daily report creation, updates, and persistence"""

    def __init__(self, reports_dir: str = None, broker=None, risk_manager=None, portfolio=None):
        if reports_dir is None:
            # Default to data/reports relative to project root
            project_root = Path(__file__).parent.parent.parent
            reports_dir = project_root / "data" / "reports"

        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.broker = broker
        self.risk_manager = risk_manager
        self.portfolio = portfolio

        self._current_report: Optional[DailyReport] = None
        self._today: Optional[str] = None

        logger.info(f"DailyReportManager initialized with reports_dir: {self.reports_dir}")

    def set_trading_components(self, broker, risk_manager, portfolio):
        """Set trading components after initialization"""
        self.broker = broker
        self.risk_manager = risk_manager
        self.portfolio = portfolio

    def _get_report_path(self, date_str: str) -> Path:
        """Get file path for a report date"""
        return self.reports_dir / f"{date_str}.json"

    def _today_str(self) -> str:
        """Get today's date as YYYY-MM-DD string"""
        return datetime.now().strftime("%Y-%m-%d")

    def get_or_create_today_report(self) -> DailyReport:
        """Get today's report, creating it if it doesn't exist"""
        today = self._today_str()

        # Check if we have a cached report for today
        if self._current_report and self._today == today:
            return self._current_report

        # Try to load from file
        report = self.load_report(today)

        if report is None:
            # Create new report
            now = datetime.now().isoformat()
            report = DailyReport(
                date=today,
                created_at=now,
                updated_at=now,
            )
            self.save_report(report)
            logger.info(f"Created new daily report for {today}")

        self._current_report = report
        self._today = today
        return report

    def capture_snapshot(self, snapshot_type: str = "manual") -> Optional[PortfolioSnapshot]:
        """Capture current portfolio state as a snapshot"""
        if not self.broker:
            logger.warning("Cannot capture snapshot: broker not set")
            return None

        try:
            account = self.broker.get_account_info()
            positions = self.broker.get_positions()

            position_snapshots = []
            for pos in positions:
                position_snapshots.append(PositionSnapshot(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    side=pos.side,
                    entry_price=pos.entry_price,
                    current_price=pos.current_price,
                    market_value=pos.quantity * pos.current_price,
                    unrealized_pnl=pos.pnl,
                    unrealized_pnl_percent=pos.pnl_percent,
                ))

            # Calculate exposure
            total_position_value = sum(p.market_value for p in position_snapshots)

            snapshot = PortfolioSnapshot(
                timestamp=datetime.now().isoformat(),
                snapshot_type=snapshot_type,
                cash=account.get("cash", 0),
                equity=account.get("equity", 0),
                portfolio_value=account.get("portfolio_value", 0),
                buying_power=account.get("buying_power", 0),
                positions=position_snapshots,
                total_positions=len(position_snapshots),
                current_exposure=total_position_value,
                daily_pnl=self.risk_manager.daily_pnl if self.risk_manager else 0,
            )

            # Update today's report with snapshot
            report = self.get_or_create_today_report()

            if snapshot_type == "market_open":
                report.market_open_snapshot = snapshot
            elif snapshot_type == "market_close":
                report.market_close_snapshot = snapshot
                # Calculate unrealized P&L from positions at close
                report.unrealized_pnl = sum(p.unrealized_pnl for p in position_snapshots)
                report.total_pnl = report.realized_pnl + report.unrealized_pnl

            report.updated_at = datetime.now().isoformat()
            self.save_report(report)

            logger.info(f"Captured {snapshot_type} snapshot: portfolio_value=${snapshot.portfolio_value:.2f}")
            return snapshot

        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return None

    def record_trade(self, trade_data: Dict[str, Any], blocked: bool = False) -> TradeRecord:
        """Record an executed or blocked trade"""
        trade = TradeRecord(
            timestamp=trade_data.get("timestamp", datetime.now().isoformat()),
            symbol=trade_data.get("symbol", ""),
            side=trade_data.get("side", "").lower(),
            quantity=trade_data.get("quantity", 0),
            price=trade_data.get("price", 0),
            total_value=trade_data.get("quantity", 0) * trade_data.get("price", 0),
            signal_confidence=trade_data.get("signal_confidence", 0),
            llm_provider=trade_data.get("llm_provider", ""),
            reasoning=trade_data.get("reasoning", ""),
            realized_pnl=trade_data.get("realized_pnl"),
            execution_status="blocked" if blocked else "executed",
            block_reason=trade_data.get("block_reason") if blocked else None,
        )

        report = self.get_or_create_today_report()

        if blocked:
            report.blocked_trades.append(trade)
        else:
            report.trades.append(trade)
            report.signals_actioned += 1

            # Update P&L tracking
            if trade.realized_pnl is not None:
                report.realized_pnl += trade.realized_pnl
                report.total_pnl = report.realized_pnl + report.unrealized_pnl

                if trade.realized_pnl > 0:
                    report.win_count += 1
                elif trade.realized_pnl < 0:
                    report.loss_count += 1

        report.updated_at = datetime.now().isoformat()
        self.save_report(report)

        logger.info(f"Recorded {'blocked ' if blocked else ''}trade: {trade.side} {trade.quantity} {trade.symbol} @ ${trade.price:.2f}")
        return trade

    def record_signal_analyzed(self):
        """Increment the signals analyzed counter"""
        report = self.get_or_create_today_report()
        report.signals_analyzed += 1
        report.updated_at = datetime.now().isoformat()
        self.save_report(report)

    def save_report(self, report: DailyReport):
        """Save report to JSON file"""
        try:
            path = self._get_report_path(report.date)
            with open(path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            logger.debug(f"Saved report to {path}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def load_report(self, date_str: str) -> Optional[DailyReport]:
        """Load report from JSON file"""
        path = self._get_report_path(date_str)

        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return DailyReport(**data)
        except Exception as e:
            logger.error(f"Error loading report from {path}: {e}")
            return None

    def list_available_reports(self) -> List[str]:
        """List all available report dates, sorted newest first"""
        reports = []
        for path in self.reports_dir.glob("*.json"):
            # Extract date from filename (YYYY-MM-DD.json)
            date_str = path.stem
            try:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
                reports.append(date_str)
            except ValueError:
                continue

        return sorted(reports, reverse=True)

    def get_report_summary(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a report (for list views)"""
        report = self.load_report(date_str)
        if not report:
            return None

        return {
            "date": report.date,
            "trade_count": report.trade_count,
            "realized_pnl": report.realized_pnl,
            "unrealized_pnl": report.unrealized_pnl,
            "total_pnl": report.total_pnl,
            "win_rate": report.win_rate,
            "has_open_snapshot": report.market_open_snapshot is not None,
            "has_close_snapshot": report.market_close_snapshot is not None,
        }
