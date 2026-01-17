import React, { useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  BoltIcon,
  ClockIcon,
  ShieldExclamationIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  CheckIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  MinusCircleIcon,
  ChartBarIcon,
  GlobeAltIcon,
  NewspaperIcon,
  UserGroupIcon,
  FireIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { formatDateTime, getConfidenceLevel, formatConfidence } from '../utils/formatters';
import ConfidenceBadge from './ConfidenceBadge';
import apiClient from '../utils/api';

const ActivityFeed = ({ activities }) => {
  const [expandedItems, setExpandedItems] = useState({});
  const [processingTrades, setProcessingTrades] = useState({});

  const toggleExpand = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleApprove = async (tradeId, symbol, signal) => {
    setProcessingTrades(prev => ({ ...prev, [tradeId]: 'approving' }));
    try {
      await apiClient.approveTrade(tradeId);
    } catch (error) {
      console.error('Error approving trade:', error);
      alert(`Failed to approve trade: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessingTrades(prev => ({ ...prev, [tradeId]: null }));
    }
  };

  const handleReject = async (tradeId, symbol, signal) => {
    setProcessingTrades(prev => ({ ...prev, [tradeId]: 'rejecting' }));
    try {
      await apiClient.rejectTrade(tradeId);
    } catch (error) {
      console.error('Error rejecting trade:', error);
      alert(`Failed to reject trade: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessingTrades(prev => ({ ...prev, [tradeId]: null }));
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'bot_status':
        return InformationCircleIcon;
      case 'trading_signals':
        return ArrowTrendingUpIcon;
      case 'trade_executed':
        return BoltIcon;
      case 'trade_rejected':
        return XMarkIcon;
      case 'trade_blocked':
        return ShieldExclamationIcon;
      case 'trade_pending_approval':
        return ExclamationTriangleIcon;
      case 'stock_analysis':
        return ChartBarIcon;
      case 'analyzing_symbol':
        return MagnifyingGlassIcon;
      case 'market_sentiment':
        return GlobeAltIcon;
      case 'error':
        return ExclamationCircleIcon;
      case 'scan_started':
      case 'scan_complete':
        return MagnifyingGlassIcon;
      case 'market_closed':
        return InformationCircleIcon;
      case 'pending_trades_update':
        return ClockIcon;
      default:
        return InformationCircleIcon;
    }
  };

  // Helper function to get sentiment color based on score
  const getSentimentColor = (score) => {
    if (score >= 0.3) return 'text-green-400';
    if (score >= 0.1) return 'text-green-300';
    if (score > -0.1) return 'text-slate-300';
    if (score > -0.3) return 'text-red-300';
    return 'text-red-400';
  };

  const getSentimentBgColor = (score) => {
    if (score >= 0.3) return 'bg-green-900/40 border-green-600';
    if (score >= 0.1) return 'bg-green-900/20 border-green-700';
    if (score > -0.1) return 'bg-slate-800/50 border-slate-600';
    if (score > -0.3) return 'bg-red-900/20 border-red-700';
    return 'bg-red-900/40 border-red-600';
  };

  const getSentimentIcon = (sourceName) => {
    switch (sourceName) {
      case 'news': return NewspaperIcon;
      case 'analysts': return UserGroupIcon;
      case 'trends': return FireIcon;
      case 'momentum': return ArrowTrendingUpIcon;
      case 'reddit': return ChatBubbleLeftRightIcon;
      default: return InformationCircleIcon;
    }
  };

  const getIconColor = (type, data = {}) => {
    if (type === 'stock_analysis') {
      if (data.signal === 'BUY') return 'text-green-400';
      if (data.signal === 'SELL') return 'text-red-400';
      if (data.signal === 'HOLD') return 'text-slate-400';
      return 'text-red-400'; // ERROR
    }
    switch (type) {
      case 'bot_status':
        return 'text-blue-400';
      case 'trading_signals':
        return 'text-yellow-400';
      case 'trade_executed':
        return 'text-green-400';
      case 'trade_rejected':
        return 'text-red-400';
      case 'trade_blocked':
        return 'text-orange-400';
      case 'trade_pending_approval':
        return 'text-amber-400';
      case 'analyzing_symbol':
        return 'text-blue-400';
      case 'error':
        return 'text-red-400';
      case 'scan_started':
        return 'text-purple-400';
      case 'scan_complete':
        return 'text-green-400';
      case 'market_closed':
        return 'text-orange-400';
      case 'pending_trades_update':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getBgColor = (type, data = {}) => {
    if (type === 'stock_analysis') {
      if (data.is_actionable) {
        return data.signal === 'BUY'
          ? 'bg-green-900/30 border-green-600'
          : 'bg-red-900/30 border-red-600';
      }
      if (data.signal === 'HOLD') return 'bg-slate-800/50 border-slate-600';
      if (data.signal === 'ERROR') return 'bg-red-900/20 border-red-700';
      return 'bg-slate-800/50 border-slate-700';
    }
    if (type === 'trade_pending_approval') {
      return 'bg-amber-900/30 border-amber-500';
    }
    switch (type) {
      case 'bot_status':
        return 'bg-blue-900/20 border-slate-700';
      case 'trading_signals':
        return 'bg-yellow-900/20 border-slate-700';
      case 'trade_executed':
        return 'bg-green-900/30 border-green-600';
      case 'trade_rejected':
        return 'bg-red-900/20 border-red-600';
      case 'trade_blocked':
        return 'bg-orange-900/30 border-orange-600';
      case 'error':
        return 'bg-red-900/20 border-slate-700';
      case 'scan_started':
        return 'bg-purple-900/20 border-slate-700';
      case 'scan_complete':
        return 'bg-slate-800/50 border-slate-700';
      case 'market_closed':
        return 'bg-orange-900/20 border-slate-700';
      case 'analyzing_symbol':
        return 'bg-blue-900/10 border-slate-700';
      default:
        return 'bg-gray-900/20 border-slate-700';
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `$${value.toFixed(2)}`;
  };

  const getConfidenceExplanation = (signal, confidence) => {
    const level = getConfidenceLevel(confidence);
    if (signal === 'BUY') {
      return `${level.label} confidence (${confidence}%) - AI sees this as a good buy opportunity`;
    } else if (signal === 'SELL') {
      return `${level.label} confidence (${confidence}%) - AI recommends selling`;
    } else if (signal === 'HOLD') {
      return `${level.label} confidence (${confidence}%) - AI recommends waiting for better setup`;
    }
    return '';
  };

  // Market Sentiment Card component
  const MarketSentimentCard = ({ data }) => {
    const sentiment = data.sentiment;
    if (!sentiment) return null;

    const score = sentiment.overall_score || 0;
    const summary = sentiment.summary || 'Unknown';
    const indicators = sentiment.indicators || {};

    return (
      <div className={`rounded-lg border ${getSentimentBgColor(score)} p-4`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <GlobeAltIcon className="h-5 w-5 text-blue-400" />
            <span className="font-semibold text-white">Market Sentiment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`font-bold text-lg ${getSentimentColor(score)}`}>
              {summary}
            </span>
            <span className={`text-sm ${getSentimentColor(score)}`}>
              ({score > 0 ? '+' : ''}{score.toFixed(2)})
            </span>
          </div>
        </div>

        {/* Market Indicators */}
        {Object.keys(indicators).length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {Object.entries(indicators).map(([name, data]) => {
              const indicatorScore = data.score || 0;
              return (
                <div key={name} className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500 capitalize">{name}</div>
                  <div className={`text-sm font-semibold ${getSentimentColor(indicatorScore)}`}>
                    {data.label || 'N/A'}
                  </div>
                  {data.value !== undefined && data.value !== null && (
                    <div className="text-xs text-slate-400">
                      {typeof data.value === 'number' ? data.value.toFixed(2) : data.value}
                      {data.change !== undefined && data.change !== null && (
                        <span className={data.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {' '}({data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}%)
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // Stock Sentiment display component (for use within StockAnalysisCard)
  const StockSentimentDisplay = ({ sentiment }) => {
    if (!sentiment) return null;

    const score = sentiment.overall_score || 0;
    const summary = sentiment.summary || 'Unknown';
    const sources = sentiment.sources || {};

    return (
      <div className="mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
          <GlobeAltIcon className="h-3 w-3" />
          Stock Sentiment
          <span className={`ml-auto font-semibold ${getSentimentColor(score)}`}>
            {summary} ({score > 0 ? '+' : ''}{score.toFixed(2)})
          </span>
        </div>
        {Object.keys(sources).length > 0 && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(sources).map(([name, data]) => {
              const SourceIcon = getSentimentIcon(name);
              const sourceScore = data.score || 0;
              return (
                <div
                  key={name}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                    sourceScore >= 0.1 ? 'bg-green-900/30 text-green-300' :
                    sourceScore <= -0.1 ? 'bg-red-900/30 text-red-300' :
                    'bg-slate-700 text-slate-300'
                  }`}
                >
                  <SourceIcon className="h-3 w-3" />
                  <span className="capitalize">{name}:</span>
                  <span className="font-semibold">{data.label || 'N/A'}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const StockAnalysisCard = ({ data, isExpanded, onToggle }) => {
    const isBuy = data.signal === 'BUY';
    const isSell = data.signal === 'SELL';
    const isHold = data.signal === 'HOLD';
    const isError = data.signal === 'ERROR';

    return (
      <div className={`rounded-lg border transition-all ${
        data.is_actionable
          ? isBuy
            ? 'bg-green-900/40 border-green-500 ring-1 ring-green-500/30'
            : 'bg-red-900/40 border-red-500 ring-1 ring-red-500/30'
          : isHold
          ? 'bg-slate-800/60 border-slate-600'
          : isError
          ? 'bg-red-900/20 border-red-700'
          : 'bg-slate-800/40 border-slate-700'
      }`}>
        {/* Header */}
        <div
          className="flex items-center justify-between p-3 cursor-pointer"
          onClick={onToggle}
        >
          <div className="flex items-center gap-3">
            <span className="font-bold text-white text-lg">{data.symbol}</span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold ${
                isBuy
                  ? 'bg-green-600 text-white'
                  : isSell
                  ? 'bg-red-600 text-white'
                  : isHold
                  ? 'bg-slate-600 text-slate-200'
                  : 'bg-red-800 text-red-200'
              }`}
            >
              {data.signal}
            </span>
            {data.is_actionable && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-600 text-white text-xs font-semibold">
                <SparklesIcon className="h-3 w-3" />
                ACTIONABLE
              </span>
            )}
            {isHold && (
              <span className="text-xs text-slate-400 italic">No trade recommended</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* Compact Metrics - Show confidence level with signal */}
            <div className="hidden sm:flex items-center gap-2 text-xs">
              <div className="flex items-center gap-1" title={getConfidenceExplanation(data.signal, data.confidence)}>
                <span className={`font-semibold px-2 py-0.5 rounded ${
                  isBuy ? 'bg-green-900/50 text-green-400' :
                  isSell ? 'bg-red-900/50 text-red-400' :
                  isHold ? 'bg-slate-700 text-slate-300' :
                  'bg-slate-700 text-slate-400'
                }`}>
                  {data.signal}
                </span>
                <ConfidenceBadge confidence={data.confidence} size="sm" />
              </div>
              {data.entry_price && !isHold && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">@</span>
                  <span className="text-white font-mono">{formatCurrency(data.entry_price)}</span>
                </div>
              )}
            </div>
            {isExpanded ? (
              <ChevronUpIcon className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronDownIcon className="h-4 w-4 text-slate-400" />
            )}
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-3 pb-3 border-t border-slate-700/50">
            {/* Confidence Explanation Banner */}
            <div className={`mt-3 mb-3 p-2 rounded text-sm ${
              isBuy ? 'bg-green-900/30 border border-green-700 text-green-300' :
              isSell ? 'bg-red-900/30 border border-red-700 text-red-300' :
              'bg-slate-700/50 border border-slate-600 text-slate-300'
            }`}>
              <span className="font-semibold">{data.signal}</span>{' '}
              <ConfidenceBadge confidence={data.confidence} size="sm" showPercent={true} />
              <span className="ml-2">
                {isBuy && '- AI sees this as a good buying opportunity based on technical and sentiment analysis.'}
                {isSell && '- AI recommends selling based on bearish signals in the analysis.'}
                {isHold && '- AI recommends waiting for better setup. Market conditions or technicals are mixed.'}
                {isError && '- Analysis failed for this symbol.'}
              </span>
            </div>

            {/* Metrics Grid - Only show trade details for BUY/SELL */}
            {!isHold && !isError && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 mb-3">
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Entry Price</div>
                  <div className="text-sm font-mono text-white">{formatCurrency(data.entry_price)}</div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Stop Loss</div>
                  <div className="text-sm font-mono text-red-400">{formatCurrency(data.stop_loss)}</div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Take Profit</div>
                  <div className="text-sm font-mono text-green-400">{formatCurrency(data.take_profit)}</div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Position Size</div>
                  <div className="text-sm text-white capitalize">{data.position_size || 'N/A'}</div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Time Horizon</div>
                  <div className="text-sm text-white capitalize">{data.time_horizon || 'N/A'}</div>
                </div>
              </div>
            )}

            {/* For HOLD signals, show simpler info */}
            {isHold && (
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Position Size</div>
                  <div className="text-sm text-white capitalize">{data.position_size || 'N/A'}</div>
                </div>
                <div className="bg-slate-900/50 rounded p-2">
                  <div className="text-xs text-slate-500">Time Horizon</div>
                  <div className="text-sm text-white capitalize">{data.time_horizon || 'N/A'}</div>
                </div>
              </div>
            )}

            {/* Stock Sentiment */}
            {data.stock_sentiment && (
              <StockSentimentDisplay sentiment={data.stock_sentiment} />
            )}

            {/* Risk Factors */}
            {data.risk_factors && data.risk_factors.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1 text-xs text-slate-500 mb-1">
                  <ShieldExclamationIcon className="h-3 w-3" />
                  Risk Factors
                </div>
                <div className="flex flex-wrap gap-1">
                  {data.risk_factors.map((risk, idx) => (
                    <span key={idx} className="text-xs px-2 py-0.5 bg-red-900/30 text-red-300 rounded">
                      {risk}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* AI Reasoning */}
            <div>
              <div className="flex items-center gap-1 text-xs text-slate-500 mb-1">
                <SparklesIcon className="h-3 w-3" />
                AI Analysis {data.llm_provider && `(${data.llm_provider})`}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">{data.reasoning}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  const PendingTradeCard = ({ data }) => {
    const tradeId = data.trade_id;
    const isProcessing = processingTrades[tradeId];
    const isBuy = data.signal === 'BUY';

    return (
      <div className="bg-amber-900/40 border-2 border-amber-500 rounded-lg p-4 ring-1 ring-amber-500/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="font-bold text-white text-lg">{data.symbol}</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
              isBuy ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
            }`}>
              {data.signal}
            </span>
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-600 text-white text-xs font-semibold animate-pulse">
              <ExclamationTriangleIcon className="h-3 w-3" />
              APPROVAL REQUIRED
            </span>
          </div>
          <ConfidenceBadge confidence={data.confidence} size="md" />
        </div>

        {/* Quick metrics */}
        <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
          <div className="bg-slate-900/50 rounded p-2">
            <span className="text-slate-500">Entry:</span>
            <span className="ml-1 text-white font-mono">{formatCurrency(data.entry_price)}</span>
          </div>
          <div className="bg-slate-900/50 rounded p-2">
            <span className="text-slate-500">Stop:</span>
            <span className="ml-1 text-red-400 font-mono">{formatCurrency(data.stop_loss)}</span>
          </div>
          <div className="bg-slate-900/50 rounded p-2">
            <span className="text-slate-500">Target:</span>
            <span className="ml-1 text-green-400 font-mono">{formatCurrency(data.take_profit)}</span>
          </div>
        </div>

        {/* AI Reasoning */}
        <p className="text-sm text-slate-300 mb-3 line-clamp-2">{data.reasoning}</p>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleApprove(tradeId, data.symbol, data.signal)}
            disabled={isProcessing}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all ${
              isProcessing === 'approving'
                ? 'bg-green-700 cursor-wait'
                : 'bg-green-600 hover:bg-green-500'
            } text-white disabled:opacity-50`}
          >
            {isProcessing === 'approving' ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Executing...
              </>
            ) : (
              <>
                <CheckIcon className="h-5 w-5" />
                Approve & Execute
              </>
            )}
          </button>
          <button
            onClick={() => handleReject(tradeId, data.symbol, data.signal)}
            disabled={isProcessing}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all ${
              isProcessing === 'rejecting'
                ? 'bg-red-700 cursor-wait'
                : 'bg-red-600 hover:bg-red-500'
            } text-white disabled:opacity-50`}
          >
            {isProcessing === 'rejecting' ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Rejecting...
              </>
            ) : (
              <>
                <XMarkIcon className="h-5 w-5" />
                Reject
              </>
            )}
          </button>
        </div>
      </div>
    );
  };

  const renderActivity = (activity, index) => {
    const Icon = getIcon(activity.type);
    const iconColor = getIconColor(activity.type, activity.data);
    const bgColor = getBgColor(activity.type, activity.data);

    // Skip internal events
    if (activity.type === 'pending_trades_update' || activity.type === 'analyzing_symbol') {
      return null;
    }

    // Market Sentiment
    if (activity.type === 'market_sentiment') {
      return <MarketSentimentCard key={index} data={activity.data} />;
    }

    // Stock Analysis - Individual report
    if (activity.type === 'stock_analysis') {
      return (
        <StockAnalysisCard
          key={index}
          data={activity.data}
          isExpanded={expandedItems[index]}
          onToggle={() => toggleExpand(index)}
        />
      );
    }

    // Trade Pending Approval
    if (activity.type === 'trade_pending_approval') {
      return <PendingTradeCard key={index} data={activity.data} />;
    }

    // Trade Executed
    if (activity.type === 'trade_executed') {
      const success = activity.data.success;
      return (
        <div
          key={index}
          className={`${success ? 'bg-green-900/40 border-green-500 ring-2 ring-green-500/50' : 'bg-red-900/30 border-red-600'} border rounded-lg p-4`}
        >
          <div className="flex items-start space-x-3">
            <div className={`p-1.5 rounded-full ${success ? 'bg-green-600' : 'bg-red-600'}`}>
              <BoltIcon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className={`text-sm font-medium ${success ? 'text-green-400' : 'text-red-400'}`}>
                  {success ? 'Trade Executed' : 'Trade Failed'}
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-600 text-white">
                    <BoltIcon className="h-3 w-3 mr-1" />
                    {activity.data.signal}
                  </span>
                </p>
                <p className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</p>
              </div>
              <p className="mt-1 text-sm text-white font-semibold flex items-center gap-2">
                {activity.data.symbol}
                {activity.data.confidence && (
                  <ConfidenceBadge confidence={activity.data.confidence} size="sm" />
                )}
              </p>
            </div>
          </div>
        </div>
      );
    }

    // Trade Rejected (by user)
    if (activity.type === 'trade_rejected') {
      return (
        <div key={index} className="bg-red-900/20 border border-red-600 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="p-1.5 rounded-full bg-red-600">
              <XMarkIcon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-red-400">Trade Rejected</p>
                <p className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</p>
              </div>
              <p className="mt-1 text-sm text-slate-300">
                {activity.data.signal} {activity.data.symbol} - Rejected by user
              </p>
            </div>
          </div>
        </div>
      );
    }

    // Trade Blocked (by risk manager)
    if (activity.type === 'trade_blocked') {
      return (
        <div key={index} className="bg-orange-900/30 border border-orange-600 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="p-1.5 rounded-full bg-orange-600">
              <ShieldExclamationIcon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-orange-400">
                  Trade Blocked
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs bg-orange-700 text-white">
                    {activity.data.signal}
                  </span>
                </p>
                <p className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</p>
              </div>
              <p className="mt-1 text-sm text-white font-semibold flex items-center gap-2">
                {activity.data.symbol}
                {activity.data.confidence && (
                  <ConfidenceBadge confidence={activity.data.confidence} size="sm" />
                )}
              </p>
              {activity.data.reason && (
                <p className="mt-2 text-sm text-orange-300 bg-orange-900/40 rounded p-2">
                  <span className="font-semibold">Reason:</span> {activity.data.reason}
                </p>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Scan Complete with analyses
    if (activity.type === 'scan_complete' && activity.data.analyses) {
      return (
        <div key={index} className={`${bgColor} border rounded-lg p-4`}>
          <div className="flex items-start space-x-3">
            <div className="p-1.5 rounded-full bg-green-600">
              <CheckCircleIcon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-green-400">
                  Scan Complete
                  <span className="ml-2 text-slate-400 font-normal">
                    {activity.data.total_analyzed} analyzed, {activity.data.actionable_count} actionable
                  </span>
                </p>
                <p className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // Default rendering for other types
    let title = 'Activity';
    let description = '';

    switch (activity.type) {
      case 'bot_status':
        title = activity.data.running ? 'Bot Started' : 'Bot Stopped';
        description = activity.data.message || (activity.data.running ? 'Trading bot is now active' : 'Trading bot stopped');
        break;
      case 'scan_started':
        title = 'Market Scan Started';
        description = activity.data.message || 'Analyzing watchlist...';
        break;
      case 'scan_complete':
        title = 'Scan Complete';
        description = activity.data.message || 'No signals found';
        break;
      case 'market_closed':
        title = 'Market Closed';
        description = activity.data.message || 'Waiting for market to open...';
        break;
      case 'error':
        title = 'Error';
        description = activity.data.message;
        break;
      default:
        description = JSON.stringify(activity.data);
    }

    return (
      <div key={index} className={`${bgColor} border rounded-lg p-4`}>
        <div className="flex items-start space-x-3">
          <div className="p-1.5 rounded-full bg-slate-700">
            <Icon className={`h-5 w-5 ${iconColor}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-white">{title}</p>
              <p className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</p>
            </div>
            <p className="mt-1 text-sm text-slate-300">{description}</p>
          </div>
        </div>
      </div>
    );
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
      <div className="space-y-3 max-h-[800px] overflow-y-auto">
        {activities.map((activity, index) => renderActivity(activity, index))}
      </div>
    </div>
  );
};

export default ActivityFeed;
