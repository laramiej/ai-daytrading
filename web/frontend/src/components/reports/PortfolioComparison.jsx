import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/solid';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const PortfolioComparison = ({ openSnapshot, closeSnapshot }) => {
  // Helper to format time from ISO string
  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Calculate change between snapshots
  const calculateChange = (openVal, closeVal) => {
    if (!openVal || !closeVal) return null;
    const change = closeVal - openVal;
    const percent = openVal > 0 ? (change / openVal) * 100 : 0;
    return { change, percent };
  };

  const portfolioChange = calculateChange(
    openSnapshot?.portfolio_value,
    closeSnapshot?.portfolio_value
  );

  // Render a single snapshot card
  const SnapshotCard = ({ snapshot, title, subtitle, showChange = false }) => {
    if (!snapshot) {
      return (
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="text-sm text-slate-400 mb-2">{title}</div>
          <div className="text-center py-8 text-slate-500">
            <div className="text-lg font-medium">No Snapshot</div>
            <div className="text-sm mt-1">Snapshot not captured</div>
          </div>
        </div>
      );
    }

    return (
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="text-sm text-slate-400">{title}</div>
            <div className="text-xs text-slate-500">{formatTime(snapshot.timestamp)}</div>
          </div>
          {subtitle && (
            <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
              {subtitle}
            </span>
          )}
        </div>

        {/* Portfolio Value */}
        <div className="mb-4">
          <div className="text-2xl font-bold text-white">
            {formatCurrency(snapshot.portfolio_value || 0)}
          </div>
          {showChange && portfolioChange && (
            <div className={`flex items-center text-sm ${
              portfolioChange.change >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {portfolioChange.change >= 0 ? (
                <ArrowUpIcon className="h-4 w-4 mr-1" />
              ) : (
                <ArrowDownIcon className="h-4 w-4 mr-1" />
              )}
              {formatCurrency(Math.abs(portfolioChange.change))} ({formatPercent(portfolioChange.percent)})
            </div>
          )}
        </div>

        {/* Account Details */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Cash</span>
            <span className="text-white">{formatCurrency(snapshot.cash || 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Equity</span>
            <span className="text-white">{formatCurrency(snapshot.equity || 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Buying Power</span>
            <span className="text-white">{formatCurrency(snapshot.buying_power || 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Positions</span>
            <span className="text-white">{snapshot.total_positions || 0}</span>
          </div>
        </div>

        {/* Positions List */}
        {snapshot.positions && snapshot.positions.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="text-xs text-slate-400 uppercase mb-2">Positions</div>
            <div className="space-y-2">
              {snapshot.positions.map((pos, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm">
                  <div className="flex items-center space-x-2">
                    <span className={`px-1.5 py-0.5 text-xs rounded ${
                      pos.side === 'long' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                    }`}>
                      {pos.side?.toUpperCase()}
                    </span>
                    <span className="text-white font-medium">{pos.symbol}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-slate-300">{pos.quantity} @ {formatCurrency(pos.entry_price)}</div>
                    <div className={pos.unrealized_pnl >= 0 ? 'text-green-400 text-xs' : 'text-red-400 text-xs'}>
                      {formatCurrency(pos.unrealized_pnl)} ({formatPercent(pos.unrealized_pnl_percent)})
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Portfolio Comparison</h3>

      {/* Summary bar if both snapshots exist */}
      {openSnapshot && closeSnapshot && portfolioChange && (
        <div className={`mb-4 p-3 rounded-lg ${
          portfolioChange.change >= 0 ? 'bg-green-900/20 border border-green-800' : 'bg-red-900/20 border border-red-800'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-slate-300">Day Change</span>
            <div className={`flex items-center font-medium ${
              portfolioChange.change >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {portfolioChange.change >= 0 ? (
                <ArrowUpIcon className="h-5 w-5 mr-1" />
              ) : (
                <ArrowDownIcon className="h-5 w-5 mr-1" />
              )}
              {formatCurrency(Math.abs(portfolioChange.change))} ({formatPercent(portfolioChange.percent)})
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SnapshotCard
          snapshot={openSnapshot}
          title="Market Open"
          subtitle="9:30 AM ET"
        />
        <SnapshotCard
          snapshot={closeSnapshot}
          title="Market Close"
          subtitle="4:00 PM ET"
          showChange={true}
        />
      </div>
    </div>
  );
};

export default PortfolioComparison;
