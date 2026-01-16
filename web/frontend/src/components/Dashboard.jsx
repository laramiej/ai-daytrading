import React, { useState, useEffect } from 'react';
import {
  BanknotesIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
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
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    }
  });

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusData, positionsData] = await Promise.all([
        apiClient.getStatus(),
        apiClient.getPositions(),
      ]);

      setStatus(statusData);
      setPositions(positionsData.positions);
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

        {/* Control Panel and Positions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-1">
            <ControlPanel
              botRunning={botRunning}
              isConnected={isConnected}
              onStart={handleStartBot}
              onStop={handleStopBot}
            />
          </div>
          <div className="lg:col-span-2">
            <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
              <h2 className="text-xl font-semibold text-white mb-4">Quick Stats</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Cash Available</p>
                  <p className="text-lg font-semibold text-white mt-1">
                    {formatCurrency(account.cash || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Day P&L</p>
                  <p className={`text-lg font-semibold mt-1 ${
                    (account.day_profit_loss || 0) >= 0 ? 'text-trading-green' : 'text-trading-red'
                  }`}>
                    {formatCurrency(account.day_profit_loss || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Positions Table and Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <PositionsTable positions={positions} />
          </div>
          <div className="lg:col-span-1">
            <ActivityFeed activities={activities} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
