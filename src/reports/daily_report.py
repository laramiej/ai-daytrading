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

    def generate_pdf(self, date_str: str) -> Optional[bytes]:
        """Generate a PDF report for the given date

        Returns:
            PDF file content as bytes, or None if report not found
        """
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether, PageBreak
        )

        report = self.load_report(date_str)
        if not report:
            return None

        buffer = BytesIO()
        # Letter size is 8.5 x 11 inches, use 0.5 inch margins on all sides
        # Available width = 8.5 - 1.0 = 7.5 inches
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        available_width = 7.5 * inch
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=12,
            textColor=colors.HexColor('#1e3a5f')
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#2d5a87')
        )

        elements = []

        # Title
        elements.append(Paragraph("Daily Trading Report", title_style))
        elements.append(Paragraph(f"Date: {report.date}", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        elements.append(Spacer(1, 12))

        # Summary Section - use KeepTogether to prevent page break in middle
        summary_elements = []
        summary_elements.append(Paragraph("Summary", heading_style))

        summary_data = [
            ['Total P&L', f"${report.total_pnl:,.2f}"],
            ['Realized P&L', f"${report.realized_pnl:,.2f}"],
            ['Unrealized P&L', f"${report.unrealized_pnl:,.2f}"],
            ['Trades Executed', str(report.trade_count)],
            ['Signals Analyzed', str(report.signals_analyzed)],
            ['Win Rate', f"{report.win_rate:.1f}%"],
            ['Wins / Losses', f"{report.win_count} / {report.loss_count}"],
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        summary_elements.append(summary_table)
        summary_elements.append(Spacer(1, 16))
        elements.append(KeepTogether(summary_elements))

        # Portfolio Snapshots Section
        def format_snapshot(snapshot: PortfolioSnapshot, label: str):
            """Format a portfolio snapshot for the PDF"""
            snapshot_elements = []
            snapshot_elements.append(Paragraph(label, heading_style))

            if snapshot is None:
                snapshot_elements.append(Paragraph("No snapshot captured", styles['Normal']))
                snapshot_elements.append(Spacer(1, 12))
                return KeepTogether(snapshot_elements)

            # Parse timestamp for display
            try:
                ts = datetime.fromisoformat(snapshot.timestamp)
                time_str = ts.strftime("%I:%M %p")
            except:
                time_str = snapshot.timestamp

            snapshot_data = [
                ['Time', time_str],
                ['Portfolio Value', f"${snapshot.portfolio_value:,.2f}"],
                ['Cash', f"${snapshot.cash:,.2f}"],
                ['Equity', f"${snapshot.equity:,.2f}"],
                ['Buying Power', f"${snapshot.buying_power:,.2f}"],
                ['Open Positions', str(snapshot.total_positions)],
                ['Current Exposure', f"${snapshot.current_exposure:,.2f}"],
            ]

            snap_table = Table(snapshot_data, colWidths=[2.5*inch, 2.5*inch])
            snap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ]))
            snapshot_elements.append(snap_table)

            # Positions table if any
            if snapshot.positions:
                snapshot_elements.append(Spacer(1, 8))
                snapshot_elements.append(Paragraph("Positions:", styles['Normal']))

                pos_header = ['Symbol', 'Side', 'Qty', 'Entry', 'Current', 'P&L']
                pos_data = [pos_header]

                for pos in snapshot.positions:
                    pnl_str = f"${pos.unrealized_pnl:,.2f}" if pos.unrealized_pnl >= 0 else f"-${abs(pos.unrealized_pnl):,.2f}"
                    pos_data.append([
                        pos.symbol,
                        pos.side.upper(),
                        f"{pos.quantity:.0f}",
                        f"${pos.entry_price:,.2f}",
                        f"${pos.current_price:,.2f}",
                        pnl_str,
                    ])

                # Calculate column widths to fit within available width
                pos_col_widths = [0.9*inch, 0.7*inch, 0.6*inch, 1.1*inch, 1.1*inch, 1.1*inch]
                pos_table = Table(pos_data, colWidths=pos_col_widths)
                pos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ]))
                snapshot_elements.append(pos_table)

            snapshot_elements.append(Spacer(1, 12))
            return KeepTogether(snapshot_elements)

        elements.append(format_snapshot(report.market_open_snapshot, "Market Open Snapshot"))
        elements.append(format_snapshot(report.market_close_snapshot, "Market Close Snapshot"))

        # Trades Section - handle tables that might be long
        elements.append(Paragraph("Executed Trades", heading_style))

        if report.trades:
            trade_header = ['Time', 'Symbol', 'Side', 'Qty', 'Price', 'Value', 'Conf', 'P&L']

            # Column widths that fit within 7.5 inches
            # Time=0.75, Symbol=0.7, Side=0.5, Qty=0.6, Price=1.0, Value=1.1, Conf=0.6, P&L=1.0 = 6.25
            trade_col_widths = [0.8*inch, 0.75*inch, 0.5*inch, 0.55*inch, 0.95*inch, 1.05*inch, 0.55*inch, 0.95*inch]

            # For long tables, split into chunks to allow page breaks with repeated headers
            max_rows_per_chunk = 15
            trade_chunks = []
            for i in range(0, len(report.trades), max_rows_per_chunk):
                chunk = report.trades[i:i + max_rows_per_chunk]
                trade_chunks.append(chunk)

            for chunk_idx, chunk in enumerate(trade_chunks):
                trade_data = [trade_header]

                for trade in chunk:
                    try:
                        ts = datetime.fromisoformat(trade.timestamp)
                        time_str = ts.strftime("%I:%M %p")
                    except:
                        time_str = trade.timestamp[:8] if len(trade.timestamp) > 8 else trade.timestamp

                    pnl_str = "-"
                    if trade.realized_pnl is not None:
                        pnl_str = f"${trade.realized_pnl:,.2f}" if trade.realized_pnl >= 0 else f"-${abs(trade.realized_pnl):,.2f}"

                    trade_data.append([
                        time_str,
                        trade.symbol,
                        trade.side.upper(),
                        f"{trade.quantity:.0f}",
                        f"${trade.price:,.2f}",
                        f"${trade.total_value:,.2f}",
                        f"{trade.signal_confidence:.0f}%",
                        pnl_str,
                    ])

                trade_table = Table(trade_data, colWidths=trade_col_widths, repeatRows=1)
                trade_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ]))

                # Use KeepTogether for small tables, otherwise let it flow
                if len(chunk) <= 8:
                    elements.append(KeepTogether([trade_table]))
                else:
                    elements.append(trade_table)

                if chunk_idx < len(trade_chunks) - 1:
                    elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph("No trades executed on this day.", styles['Normal']))

        elements.append(Spacer(1, 16))

        # Blocked Trades Section (if any)
        if report.blocked_trades:
            blocked_elements = []
            blocked_elements.append(Paragraph("Blocked Trades", heading_style))

            blocked_header = ['Time', 'Symbol', 'Side', 'Qty', 'Reason']
            blocked_data = [blocked_header]

            for trade in report.blocked_trades:
                try:
                    ts = datetime.fromisoformat(trade.timestamp)
                    time_str = ts.strftime("%I:%M %p")
                except:
                    time_str = trade.timestamp[:8] if len(trade.timestamp) > 8 else trade.timestamp

                # Truncate long reasons
                reason = trade.block_reason or "Unknown"
                if len(reason) > 50:
                    reason = reason[:47] + "..."

                blocked_data.append([
                    time_str,
                    trade.symbol,
                    trade.side.upper(),
                    f"{trade.quantity:.0f}",
                    reason,
                ])

            # Column widths: Time=0.8, Symbol=0.7, Side=0.5, Qty=0.6, Reason=3.5 = 6.1
            blocked_col_widths = [0.8*inch, 0.7*inch, 0.55*inch, 0.55*inch, 3.4*inch]
            blocked_table = Table(blocked_data, colWidths=blocked_col_widths, repeatRows=1)
            blocked_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7f1d1d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (3, -1), 'CENTER'),
                ('ALIGN', (4, 1), (4, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')]),
            ]))
            blocked_elements.append(blocked_table)

            # Use KeepTogether if small enough
            if len(report.blocked_trades) <= 8:
                elements.append(KeepTogether(blocked_elements))
            else:
                elements.extend(blocked_elements)

        # Footer
        elements.append(Spacer(1, 24))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')} | AI Day Trading System",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)
        ))

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated PDF report for {date_str} ({len(pdf_bytes)} bytes)")
        return pdf_bytes
