import React from 'react';
import { formatCurrency, formatPercent, formatNumber, getPnlColor, getPnlBgColor } from '../utils/formatters';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ScaleIcon,
} from '@heroicons/react/24/outline';

const PositionsTable = ({ positions, settings, account }) => {
  // Calculate summary metrics
  const positionCount = positions?.length || 0;
  const maxPositions = settings?.max_open_positions || 20;
  const maxExposure = settings?.max_total_exposure || 50000;

  // Calculate totals from positions
  const totalMarketValue = positions?.reduce((sum, pos) => {
    return sum + (pos.current_price * pos.quantity);
  }, 0) || 0;

  const totalPnl = positions?.reduce((sum, pos) => sum + (pos.pnl || 0), 0) || 0;

  const totalCost = positions?.reduce((sum, pos) => {
    return sum + (pos.entry_price * pos.quantity);
  }, 0) || 0;

  const totalPnlPercent = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;

  // Current exposure (market value of all positions)
  const currentExposure = totalMarketValue;
  const exposurePercent = maxExposure > 0 ? (currentExposure / maxExposure) * 100 : 0;
  const positionPercent = maxPositions > 0 ? (positionCount / maxPositions) * 100 : 0;

  // Summary metrics component
  const SummaryMetrics = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {/* Positions Count */}
      <div className="bg-slate-700/50 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400 flex items-center">
            <ChartBarIcon className="h-3.5 w-3.5 mr-1" />
            Positions
          </span>
          <span className={`text-xs font-medium ${
            positionPercent >= 90 ? 'text-red-400' :
            positionPercent >= 70 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {positionPercent.toFixed(0)}%
          </span>
        </div>
        <div className="text-lg font-semibold text-white">
          {positionCount} <span className="text-sm text-slate-400">/ {maxPositions}</span>
        </div>
        <div className="mt-1 h-1.5 bg-slate-600 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              positionPercent >= 90 ? 'bg-red-500' :
              positionPercent >= 70 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(positionPercent, 100)}%` }}
          />
        </div>
      </div>

      {/* Current Exposure */}
      <div className="bg-slate-700/50 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400 flex items-center">
            <ScaleIcon className="h-3.5 w-3.5 mr-1" />
            Exposure
          </span>
          <span className={`text-xs font-medium ${
            exposurePercent >= 90 ? 'text-red-400' :
            exposurePercent >= 70 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {exposurePercent.toFixed(0)}%
          </span>
        </div>
        <div className="text-lg font-semibold text-white">
          {formatCurrency(currentExposure)}
        </div>
        <div className="text-xs text-slate-400">
          of {formatCurrency(maxExposure)} max
        </div>
        <div className="mt-1 h-1.5 bg-slate-600 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              exposurePercent >= 90 ? 'bg-red-500' :
              exposurePercent >= 70 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(exposurePercent, 100)}%` }}
          />
        </div>
      </div>

      {/* Total Market Value */}
      <div className="bg-slate-700/50 rounded-lg p-3">
        <div className="flex items-center mb-1">
          <span className="text-xs text-slate-400 flex items-center">
            <CurrencyDollarIcon className="h-3.5 w-3.5 mr-1" />
            Market Value
          </span>
        </div>
        <div className="text-lg font-semibold text-white">
          {formatCurrency(totalMarketValue)}
        </div>
        <div className="text-xs text-slate-400">
          Cost basis: {formatCurrency(totalCost)}
        </div>
      </div>

      {/* Total P&L */}
      <div className="bg-slate-700/50 rounded-lg p-3">
        <div className="flex items-center mb-1">
          <span className="text-xs text-slate-400 flex items-center">
            <ArrowTrendingUpIcon className="h-3.5 w-3.5 mr-1" />
            Unrealized P&L
          </span>
        </div>
        <div className={`text-lg font-semibold ${getPnlColor(totalPnl)}`}>
          {totalPnl >= 0 ? '+' : ''}{formatCurrency(totalPnl)}
        </div>
        <div className={`text-xs ${getPnlColor(totalPnlPercent)}`}>
          {totalPnlPercent >= 0 ? '+' : ''}{totalPnlPercent.toFixed(2)}%
        </div>
      </div>
    </div>
  );

  if (!positions || positions.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4">Open Positions</h2>
        <SummaryMetrics />
        <p className="text-slate-400 text-center py-8">No open positions</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4">Open Positions</h2>
      <SummaryMetrics />
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-700">
          <thead>
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Side
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                Quantity
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                Entry Price
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                Current Price
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                P&L
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                P&L %
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {positions.map((position) => (
              <tr key={position.symbol} className="hover:bg-slate-700/50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-white">{position.symbol}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    position.side === 'long'
                      ? 'bg-green-900/30 text-trading-green'
                      : 'bg-red-900/30 text-trading-red'
                  }`}>
                    {position.side.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-300">
                  {formatNumber(position.quantity, 0)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-300">
                  {formatCurrency(position.entry_price)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-300">
                  {formatCurrency(position.current_price)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${getPnlColor(position.pnl)}`}>
                  {formatCurrency(position.pnl)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${getPnlBgColor(position.pnl_percent)} ${getPnlColor(position.pnl_percent)}`}>
                    {formatPercent(position.pnl_percent)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PositionsTable;
