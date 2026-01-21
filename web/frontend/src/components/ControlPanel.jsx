import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { PlayIcon, StopIcon, Cog6ToothIcon, ClockIcon, CpuChipIcon } from '@heroicons/react/24/solid';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BoltIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';
import apiClient from '../utils/api';
import { formatCurrency } from '../utils/formatters';

const ControlPanel = ({
  botRunning,
  onStart,
  onStop,
  isConnected,
  configured = true,
  initialized = true,
  scanIntervalMinutes = 5,
  lastScanTime = null,
  botStartTime = null,
  updateBotStartTime = () => {},
  resetBotState = () => {}
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const [todayStats, setTodayStats] = useState(null);
  const countdownRef = useRef(null);
  const statsRef = useRef(null);

  // Calculate and update countdown
  useEffect(() => {
    if (botRunning && scanIntervalMinutes > 0) {
      // If bot just started and we don't have a start time, set it
      if (!botStartTime) {
        updateBotStartTime(Date.now());
      }

      const updateCountdown = () => {
        const now = Date.now();
        const startTime = lastScanTime ? new Date(lastScanTime).getTime() : (botStartTime || now);
        const intervalMs = scanIntervalMinutes * 60 * 1000;

        // Calculate time since last scan (or bot start)
        const elapsed = now - startTime;
        const remaining = intervalMs - (elapsed % intervalMs);

        // Convert to minutes and seconds
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);

        setCountdown({ minutes, seconds, total: remaining, progress: ((intervalMs - remaining) / intervalMs) * 100 });
      };

      // Update immediately
      updateCountdown();

      // Update every second
      countdownRef.current = setInterval(updateCountdown, 1000);

      return () => {
        if (countdownRef.current) {
          clearInterval(countdownRef.current);
        }
      };
    } else {
      // Bot stopped, clear countdown (context state is managed by Dashboard)
      setCountdown(null);
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    }
  }, [botRunning, scanIntervalMinutes, botStartTime, lastScanTime, updateBotStartTime]);

  // Fetch today's stats for the metrics display
  useEffect(() => {
    const fetchTodayStats = async () => {
      try {
        const response = await apiClient.getTodayReport();
        if (response.report) {
          setTodayStats(response.report);
        }
      } catch (err) {
        // Silently fail - stats are optional
        console.debug('Could not fetch today stats:', err.message);
      }
    };

    // Fetch immediately
    fetchTodayStats();

    // Refresh every 30 seconds when bot is running
    if (botRunning) {
      statsRef.current = setInterval(fetchTodayStats, 30000);
      return () => {
        if (statsRef.current) {
          clearInterval(statsRef.current);
        }
      };
    }
  }, [botRunning, lastScanTime]); // Refresh when lastScanTime changes (new scan completed)

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      await onStart();
      updateBotStartTime(Date.now());
    } catch (err) {
      console.error('Error starting bot:', err);
      setError(err.response?.data?.detail || 'Failed to start bot');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await onStop();
      resetBotState();
      setCountdown(null);
    } catch (error) {
      console.error('Error stopping bot:', error);
    } finally {
      setLoading(false);
    }
  };

  // Format countdown display
  const formatCountdown = () => {
    if (!countdown) return '--:--';
    const mins = String(countdown.minutes).padStart(2, '0');
    const secs = String(countdown.seconds).padStart(2, '0');
    return `${mins}:${secs}`;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
        <CpuChipIcon className="h-6 w-6 mr-2 text-purple-400" />
        Trading Engine
      </h2>

      <div className="space-y-4">
        {/* Status indicator */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Status:</span>
          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${botRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className={`text-sm font-medium ${botRunning ? 'text-green-400' : 'text-red-400'}`}>
              {botRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        {/* WebSocket connection status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Connection:</span>
          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-blue-500' : 'bg-gray-500'}`}></div>
            <span className={`text-sm font-medium ${isConnected ? 'text-blue-400' : 'text-gray-400'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Next Scan Countdown - Only show when bot is running */}
        {botRunning && countdown && (
          <div className="bg-slate-700/50 rounded-lg p-4 mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <ClockIcon className="h-5 w-5 text-purple-400 mr-2" />
                <span className="text-sm text-slate-300">Next Scan</span>
              </div>
              <span className="text-2xl font-mono font-bold text-purple-400">
                {formatCountdown()}
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-600 rounded-full h-2 overflow-hidden">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-1000 ease-linear"
                style={{ width: `${countdown.progress}%` }}
              />
            </div>

            <p className="text-xs text-slate-500 mt-2 text-center">
              Scanning every {scanIntervalMinutes} minute{scanIntervalMinutes !== 1 ? 's' : ''}
            </p>
          </div>
        )}

        {/* Today's Performance Metrics - Always show */}
        <div className="bg-slate-700/50 rounded-lg p-4 mt-4">
          <div className="flex items-center mb-3">
            <ChartBarIcon className="h-5 w-5 text-blue-400 mr-2" />
            <span className="text-sm font-medium text-slate-300">Today's Performance</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Daily P&L */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Daily P&L</div>
              <div className={`text-lg font-bold ${
                (todayStats?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(todayStats?.total_pnl || 0)}
              </div>
            </div>

            {/* Trades Executed */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Trades Today</div>
              <div className="text-lg font-bold text-white">
                {todayStats?.trades?.length || 0}
              </div>
            </div>

            {/* Signals Analyzed */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Signals Analyzed</div>
              <div className="flex items-center">
                <SignalIcon className="h-4 w-4 text-yellow-400 mr-1" />
                <span className="text-lg font-bold text-white">
                  {todayStats?.signals_analyzed || 0}
                </span>
              </div>
            </div>

            {/* Win Rate */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Win Rate</div>
              <div className="flex items-center">
                {(todayStats?.win_count || 0) >= (todayStats?.loss_count || 0) ? (
                  <ArrowTrendingUpIcon className="h-4 w-4 text-green-400 mr-1" />
                ) : (
                  <ArrowTrendingDownIcon className="h-4 w-4 text-red-400 mr-1" />
                )}
                <span className="text-lg font-bold text-white">
                  {(todayStats?.win_count || 0) + (todayStats?.loss_count || 0) > 0
                    ? `${Math.round(((todayStats?.win_count || 0) / ((todayStats?.win_count || 0) + (todayStats?.loss_count || 0))) * 100)}%`
                    : '--'}
                </span>
                <span className="text-xs text-slate-500 ml-1">
                  ({todayStats?.win_count || 0}W/{todayStats?.loss_count || 0}L)
                </span>
              </div>
            </div>
          </div>

          {/* Blocked Trades indicator */}
          {(todayStats?.blocked_trades?.length || 0) > 0 && (
            <div className="mt-3 text-xs text-slate-400 flex items-center justify-center">
              <BoltIcon className="h-3 w-3 text-orange-400 mr-1" />
              {todayStats.blocked_trades.length} trade{todayStats.blocked_trades.length !== 1 ? 's' : ''} blocked by risk rules
            </div>
          )}
        </div>

        {/* Configuration status */}
        {!configured && (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3 mt-4">
            <p className="text-yellow-400 text-sm">
              API keys not configured. Please go to Settings to configure.
            </p>
            <Link
              to="/settings"
              className="mt-2 inline-flex items-center text-sm text-yellow-300 hover:text-yellow-200"
            >
              <Cog6ToothIcon className="h-4 w-4 mr-1" />
              Go to Settings
            </Link>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-3 mt-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Control buttons */}
        <div className="flex space-x-3 mt-6">
          <button
            onClick={handleStart}
            disabled={botRunning || loading || !configured}
            className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
              botRunning || loading || !configured
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
            title={!configured ? 'Please configure API keys in Settings first' : ''}
          >
            <PlayIcon className="h-5 w-5 mr-2" />
            Start
          </button>

          <button
            onClick={handleStop}
            disabled={!botRunning || loading}
            className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
              !botRunning || loading
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            <StopIcon className="h-5 w-5 mr-2" />
            Stop
          </button>
        </div>

        {loading && (
          <div className="text-center">
            <p className="text-sm text-slate-400">Processing...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ControlPanel;
