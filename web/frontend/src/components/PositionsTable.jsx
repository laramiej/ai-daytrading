import React from 'react';
import { formatCurrency, formatPercent, formatNumber, getPnlColor, getPnlBgColor } from '../utils/formatters';

const PositionsTable = ({ positions }) => {
  if (!positions || positions.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4">Open Positions</h2>
        <p className="text-slate-400 text-center py-8">No open positions</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4">Open Positions</h2>
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
