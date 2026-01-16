import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BanknotesIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  KeyIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import StatusCard from './StatusCard';
import PositionsTable from './PositionsTable';
import ControlPanel from './ControlPanel';
import ActivityFeed from './ActivityFeed';
import { useWebSocket } from '../hooks/useWebSocket';
import apiClient from '../utils/api';
import { formatCurrency, formatPercent } from '../utils/formatters';

const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [positions, setPositions] = useState([]);
  const [settings, setSettings] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastScanTime, setLastScanTime] = useState(null);

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket((message) => {
    console.log('WebSocket message:', message);

    // Add to activity feed with deduplication
    if (message.type) {
      setActivities(prev => {
        // Check if this exact message already exists (within 1 second)
        const isDuplicate = prev.some(activity =>
          activity.type === message.type &&
          activity.timestamp === message.timestamp &&
          Math.abs(new Date(activity.timestamp) - new Date(message.timestamp)) < 1000
        );

        if (isDuplicate) {
          console.log('Duplicate message detected, skipping:', message.type);
          return prev;
        }

        return [{
          type: message.type,
          data: message,
          timestamp: message.timestamp || new Date().toISOString()
        }, ...prev].slice(0, 50); // Keep last 50 activities
      });
    }

    // Handle real-time updates
    if (message.type === 'status_update') {
      setStatus(message.data);
    } else if (message.type === 'positions_update') {
      setPositions(message.data);
    } else if (message.type === 'bot_status') {
      // Refresh data when bot status changes
      fetchData();
      // Reset last scan time when bot starts
      if (message.running) {
        setLastScanTime(message.timestamp);
      } else {
        setLastScanTime(null);
      }
    } else if (message.type === 'scan_started' || message.type === 'scan_complete' || message.type === 'trading_signals') {
      // Update last scan time when a scan occurs
      setLastScanTime(message.timestamp);
    }
  });

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusData, positionsData, settingsData] = await Promise.all([
        apiClient.getStatus(),
        apiClient.getPositions(),
        apiClient.getSettings(),
      ]);

      setStatus(statusData);
      setPositions(positionsData.positions);
      setSettings(settingsData);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Refresh data every 10 seconds
    const interval = setInterval(fetchData, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleStartBot = async () => {
    try {
      await apiClient.startBot();
      await fetchData(); // Refresh data
    } catch (err) {
      console.error('Error starting bot:', err);
      setError('Failed to start bot');
    }
  };

  const handleStopBot = async () => {
    try {
      await apiClient.stopBot();
      await fetchData(); // Refresh data
    } catch (err) {
      console.error('Error stopping bot:', err);
      setError('Failed to stop bot');
    }
  };

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-red-400 mb-4">Error: {error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const account = status?.account || {};
  const botRunning = status?.bot_running || false;
  const configured = status?.configured !== false;  // Default to true if not specified
  const initialized = status?.initialized !== false;

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">AI Day Trading Dashboard</h1>
          <p className="text-slate-400 mt-2">
            Real-time portfolio monitoring and bot control
          </p>
        </div>

        {/* Configuration Required Banner */}
        {status && status.configured === false && (
          <div className="mb-6 bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-start">
                <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-yellow-400 font-semibold">Configuration Required</h3>
                  <p className="text-yellow-300/80 text-sm mt-1">
                    Please configure your API keys in Settings to enable trading.
                    {status.missing && status.missing.length > 0 && (
                      <span className="block mt-1">Missing: {status.missing.join(', ')}</span>
                    )}
                  </p>
                </div>
              </div>
              <Link
                to="/settings"
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors flex items-center"
              >
                <Cog6ToothIcon className="h-5 w-5 mr-2" />
                Go to Settings
              </Link>
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-900 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title="Portfolio Value"
            value={formatCurrency(account.portfolio_value || 0)}
            icon={ChartBarIcon}
          />
          <StatusCard
            title="Equity"
            value={formatCurrency(account.equity || 0)}
            subValue={
              account.day_profit_loss !== undefined
                ? `${formatCurrency(account.day_profit_loss)} (${formatPercent(account.day_profit_loss_percent || 0)})`
                : null
            }
            trend={account.day_profit_loss}
            icon={BanknotesIcon}
          />
          <StatusCard
            title="Buying Power"
            value={formatCurrency(account.buying_power || 0)}
            icon={CurrencyDollarIcon}
          />
          <StatusCard
            title="Open Positions"
            value={status?.positions_count || 0}
            icon={ArrowTrendingUpIcon}
          />
        </div>

        {/* Control Panel and Settings */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-1">
            <ControlPanel
              botRunning={botRunning}
              isConnected={isConnected}
              onStart={handleStartBot}
              onStop={handleStopBot}
              configured={configured}
              initialized={initialized}
              scanIntervalMinutes={settings?.scan_interval_minutes || 5}
              lastScanTime={lastScanTime}
            />
          </div>
          <div className="lg:col-span-2">
            <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white flex items-center">
                  <Cog6ToothIcon className="h-6 w-6 mr-2" />
                  Trading Settings
                </h2>
                <Link
                  to="/settings"
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Edit Settings
                </Link>
              </div>

              {settings ? (
                <div className="space-y-4">
                  {/* API Keys Status */}
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <KeyIcon className="h-5 w-5 text-slate-400 mr-2" />
                      <h3 className="text-sm font-medium text-slate-300">API Keys</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex items-center">
                        {settings.alpaca_api_key ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-red-400 mr-2" />
                        )}
                        <span className="text-sm text-slate-400">Alpaca</span>
                        {settings.alpaca_api_key && (
                          <span className="ml-2 text-xs text-slate-500">{settings.alpaca_api_key}</span>
                        )}
                      </div>
                      <div className="flex items-center">
                        {settings.anthropic_api_key ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-red-400 mr-2" />
                        )}
                        <span className="text-sm text-slate-400">Anthropic</span>
                        {settings.anthropic_api_key && (
                          <span className="ml-2 text-xs text-slate-500">{settings.anthropic_api_key}</span>
                        )}
                      </div>
                      <div className="flex items-center">
                        {settings.openai_api_key ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-slate-600 mr-2" />
                        )}
                        <span className="text-sm text-slate-400">OpenAI</span>
                        {settings.openai_api_key && (
                          <span className="ml-2 text-xs text-slate-500">{settings.openai_api_key}</span>
                        )}
                      </div>
                      <div className="flex items-center">
                        {settings.finnhub_api_key ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-slate-600 mr-2" />
                        )}
                        <span className="text-sm text-slate-400">Finnhub</span>
                        {settings.finnhub_api_key && (
                          <span className="ml-2 text-xs text-slate-500">{settings.finnhub_api_key}</span>
                        )}
                      </div>
                      <div className="flex items-center">
                        {settings.google_api_key ? (
                          <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-4 w-4 text-slate-600 mr-2" />
                        )}
                        <span className="text-sm text-slate-400">Google</span>
                        {settings.google_api_key && (
                          <span className="ml-2 text-xs text-slate-500">{settings.google_api_key}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Trading Config */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-700/50 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <CurrencyDollarIcon className="h-5 w-5 text-slate-400 mr-2" />
                        <h3 className="text-sm font-medium text-slate-300">Position Limits</h3>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Max Position</span>
                          <span className="text-sm text-white">{formatCurrency(settings.max_position_size)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Max Exposure</span>
                          <span className="text-sm text-white">{formatCurrency(settings.max_total_exposure)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Max Open</span>
                          <span className="text-sm text-white">{settings.max_open_positions} positions</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-700/50 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <ShieldCheckIcon className="h-5 w-5 text-slate-400 mr-2" />
                        <h3 className="text-sm font-medium text-slate-300">Risk Management</h3>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Stop Loss</span>
                          <span className="text-sm text-white">{settings.stop_loss_percentage}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Take Profit</span>
                          <span className="text-sm text-white">{settings.take_profit_percentage}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Max Daily Loss</span>
                          <span className="text-sm text-white">{formatCurrency(settings.max_daily_loss)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Trading Options */}
                  <div className="flex flex-wrap gap-3">
                    <div className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                      settings.enable_auto_trading
                        ? 'bg-green-900/30 text-green-400 border border-green-700'
                        : 'bg-slate-700 text-slate-400 border border-slate-600'
                    }`}>
                      Auto Trading: {settings.enable_auto_trading ? 'ON' : 'OFF'}
                    </div>
                    <div className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                      settings.enable_short_selling
                        ? 'bg-blue-900/30 text-blue-400 border border-blue-700'
                        : 'bg-slate-700 text-slate-400 border border-slate-600'
                    }`}>
                      Short Selling: {settings.enable_short_selling ? 'ON' : 'OFF'}
                    </div>
                    <div className="px-3 py-1.5 rounded-full text-xs font-medium bg-purple-900/30 text-purple-400 border border-purple-700">
                      Scan: Every {settings.scan_interval_minutes || 5} min
                    </div>
                    <div className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300 border border-slate-600">
                      Min Confidence: {settings.min_confidence_threshold || 70}%
                    </div>
                    <div className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300 border border-slate-600">
                      LLM: {settings.default_llm_provider}
                    </div>
                  </div>

                  {/* Watchlist */}
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-slate-300 mb-2">Watchlist</h3>
                    <div className="flex flex-wrap gap-2">
                      {settings.watchlist?.map((symbol) => (
                        <span
                          key={symbol}
                          className="px-2 py-1 bg-slate-600 text-slate-200 text-xs rounded"
                        >
                          {symbol}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-2 text-slate-400 text-sm">Loading settings...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Positions Table */}
        <div className="mb-8">
          <PositionsTable positions={positions} settings={settings} account={account} />
        </div>

        {/* Activity Feed - Full Width */}
        <div className="mb-8">
          <ActivityFeed activities={activities} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
