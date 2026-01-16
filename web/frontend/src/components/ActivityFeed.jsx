import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { formatDateTime } from '../utils/formatters';

const ActivityFeed = ({ activities }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'bot_status':
        return InformationCircleIcon;
      case 'trading_signals':
        return ArrowTrendingUpIcon;
      case 'trade_executed':
        return CheckCircleIcon;
      case 'error':
        return ExclamationCircleIcon;
      case 'scan_started':
      case 'scan_complete':
        return MagnifyingGlassIcon;
      case 'market_closed':
        return InformationCircleIcon;
      default:
        return InformationCircleIcon;
    }
  };

  const getIconColor = (type) => {
    switch (type) {
      case 'bot_status':
        return 'text-blue-400';
      case 'trading_signals':
        return 'text-yellow-400';
      case 'trade_executed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'scan_started':
        return 'text-purple-400';
      case 'scan_complete':
        return 'text-gray-400';
      case 'market_closed':
        return 'text-orange-400';
      default:
        return 'text-gray-400';
    }
  };

  const getBgColor = (type) => {
    switch (type) {
      case 'bot_status':
        return 'bg-blue-900/20';
      case 'trading_signals':
        return 'bg-yellow-900/20';
      case 'trade_executed':
        return 'bg-green-900/20';
      case 'error':
        return 'bg-red-900/20';
      case 'scan_started':
        return 'bg-purple-900/20';
      case 'scan_complete':
        return 'bg-gray-900/20';
      case 'market_closed':
        return 'bg-orange-900/20';
      default:
        return 'bg-gray-900/20';
    }
  };

  const formatActivity = (activity) => {
    switch (activity.type) {
      case 'bot_status':
        return {
          title: activity.data.running ? 'Bot Started' : 'Bot Stopped',
          description: activity.data.message || (activity.data.running ? 'Trading bot is now active' : 'Trading bot stopped'),
        };

      case 'trading_signals':
        return {
          title: `${activity.data.count} Trading Signal${activity.data.count > 1 ? 's' : ''} Found`,
          description: activity.data.signals.map(s =>
            `${s.symbol}: ${s.signal} (${s.confidence}% confidence)`
          ).join(' • '),
          details: activity.data.signals,
        };

      case 'trade_executed':
        return {
          title: activity.data.success ? 'Trade Executed' : 'Trade Failed',
          description: `${activity.data.signal} ${activity.data.symbol}`,
        };

      case 'error':
        return {
          title: 'Error',
          description: activity.data.message,
        };

      case 'scan_started':
        return {
          title: 'Market Scan Started',
          description: activity.data.message || 'Analyzing watchlist for opportunities...',
        };

      case 'scan_complete':
        return {
          title: 'Scan Complete',
          description: activity.data.message || 'No high-confidence signals found',
        };

      case 'market_closed':
        return {
          title: 'Market Closed',
          description: activity.data.message || 'Waiting for market to open...',
        };

      default:
        return {
          title: 'Activity',
          description: JSON.stringify(activity.data),
        };
    }
  };

  if (!activities || activities.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4">Activity Feed</h2>
        <p className="text-slate-400 text-center py-8">No activity yet. Start the bot to see updates.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4">Activity Feed</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activities.map((activity, index) => {
          const Icon = getIcon(activity.type);
          const iconColor = getIconColor(activity.type);
          const bgColor = getBgColor(activity.type);
          const formatted = formatActivity(activity);

          return (
            <div
              key={index}
              className={`${bgColor} border border-slate-700 rounded-lg p-4 transition-all hover:border-slate-600`}
            >
              <div className="flex items-start space-x-3">
                <Icon className={`h-5 w-5 ${iconColor} mt-0.5 flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-white">
                      {formatted.title}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatDateTime(activity.timestamp)}
                    </p>
                  </div>
                  <p className="mt-1 text-sm text-slate-300 break-words">
                    {formatted.description}
                  </p>

                  {/* Show signal details if available */}
                  {formatted.details && (
                    <div className="mt-2 space-y-1">
                      {formatted.details.map((signal, idx) => (
                        <div key={idx} className="text-xs bg-slate-900/50 rounded p-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">{signal.symbol}</span>
                            <span className={`px-2 py-0.5 rounded ${
                              signal.signal === 'BUY'
                                ? 'bg-green-900/30 text-green-400'
                                : 'bg-red-900/30 text-red-400'
                            }`}>
                              {signal.signal}
                            </span>
                          </div>
                          <p className="text-slate-400 mt-1 text-xs leading-relaxed">
                            {signal.reasoning}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ActivityFeed;
