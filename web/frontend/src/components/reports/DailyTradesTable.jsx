import React, { useState } from 'react';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  XCircleIcon,
  CheckCircleIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const DailyTradesTable = ({ trades = [], blockedTrades = [] }) => {
  const [showBlocked, setShowBlocked] = useState(true);
  const [filterSymbol, setFilterSymbol] = useState('');

  // Combine and sort all trades
  const allTrades = [
    ...trades.map(t => ({ ...t, wasBlocked: false })),
    ...blockedTrades.map(t => ({ ...t, wasBlocked: true })),
  ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // Filter trades
  const filteredTrades = allTrades.filter(trade => {
    if (!showBlocked && trade.wasBlocked) return false;
    if (filterSymbol && !trade.symbol.toLowerCase().includes(filterSymbol.toLowerCase())) return false;
    return true;
  });

  // Get unique symbols for filter
  const uniqueSymbols = [...new Set(allTrades.map(t => t.symbol))];

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  };

  // Render confidence badge
  const ConfidenceBadge = ({ confidence }) => {
    const getColor = (conf) => {
      if (conf >= 80) return 'bg-green-900/30 text-green-400 border-green-700';
      if (conf >= 60) return 'bg-yellow-900/30 text-yellow-400 border-yellow-700';
      return 'bg-red-900/30 text-red-400 border-red-700';
    };

    return (
      <span className={`px-2 py-0.5 text-xs rounded-full border ${getColor(confidence)}`}>
        {confidence?.toFixed(0)}%
      </span>
    );
  };

  if (allTrades.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Trades Executed</h3>
        <div className="text-center py-12 text-slate-500">
          <div className="text-lg font-medium">No Trades</div>
          <div className="text-sm mt-1">No trades were executed on this day</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      {/* Header with filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-white">Trades Executed</h3>
          <span className="text-sm text-slate-400">
            {trades.length} executed
            {blockedTrades.length > 0 && `, ${blockedTrades.length} blocked`}
          </span>
        </div>

        <div className="flex items-center space-x-3">
          {/* Symbol filter */}
          <div className="relative">
            <FunnelIcon className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="bg-slate-700 text-white text-sm rounded-lg pl-9 pr-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Symbols</option>
              {uniqueSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>

          {/* Show blocked toggle */}
          {blockedTrades.length > 0 && (
            <label className="flex items-center space-x-2 text-sm text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showBlocked}
                onChange={(e) => setShowBlocked(e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
              />
              <span>Show blocked</span>
            </label>
          )}
        </div>
      </div>

      {/* Trades table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-400 border-b border-slate-700">
              <th className="pb-3 font-medium">Time</th>
              <th className="pb-3 font-medium">Symbol</th>
              <th className="pb-3 font-medium">Action</th>
              <th className="pb-3 font-medium text-right">Qty</th>
              <th className="pb-3 font-medium text-right">Price</th>
              <th className="pb-3 font-medium text-right">Value</th>
              <th className="pb-3 font-medium text-right">P&L</th>
              <th className="pb-3 font-medium text-center">Conf</th>
              <th className="pb-3 font-medium">Provider</th>
              <th className="pb-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {filteredTrades.map((trade, idx) => (
              <tr
                key={idx}
                className={`hover:bg-slate-700/50 ${trade.wasBlocked ? 'opacity-60' : ''}`}
              >
                <td className="py-3 text-slate-300">
                  {formatTime(trade.timestamp)}
                </td>
                <td className="py-3 font-medium text-white">
                  {trade.symbol}
                </td>
                <td className="py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    trade.side === 'buy'
                      ? 'bg-green-900/30 text-green-400'
                      : 'bg-red-900/30 text-red-400'
                  }`}>
                    {trade.side === 'buy' ? (
                      <ArrowUpIcon className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowDownIcon className="h-3 w-3 mr-1" />
                    )}
                    {trade.side?.toUpperCase()}
                  </span>
                </td>
                <td className="py-3 text-right text-slate-300">
                  {trade.quantity}
                </td>
                <td className="py-3 text-right text-slate-300">
                  {formatCurrency(trade.price)}
                </td>
                <td className="py-3 text-right text-slate-300">
                  {formatCurrency(trade.total_value)}
                </td>
                <td className="py-3 text-right">
                  {trade.realized_pnl != null ? (
                    <span className={trade.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {formatCurrency(trade.realized_pnl)}
                    </span>
                  ) : (
                    <span className="text-slate-500">-</span>
                  )}
                </td>
                <td className="py-3 text-center">
                  <ConfidenceBadge confidence={trade.signal_confidence} />
                </td>
                <td className="py-3 text-slate-400 text-xs">
                  {trade.llm_provider}
                </td>
                <td className="py-3">
                  {trade.wasBlocked ? (
                    <span className="inline-flex items-center text-red-400" title={trade.block_reason}>
                      <XCircleIcon className="h-4 w-4 mr-1" />
                      Blocked
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-green-400">
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                      Executed
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Blocked trades reasoning (expandable) */}
      {filteredTrades.filter(t => t.wasBlocked && t.block_reason).length > 0 && showBlocked && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <h4 className="text-sm font-medium text-slate-400 mb-2">Block Reasons</h4>
          <div className="space-y-2">
            {filteredTrades.filter(t => t.wasBlocked && t.block_reason).map((trade, idx) => (
              <div key={idx} className="text-xs bg-red-900/10 border border-red-900/30 rounded p-2">
                <span className="font-medium text-red-400">{trade.symbol}:</span>
                <span className="text-slate-400 ml-2">{trade.block_reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyTradesTable;
