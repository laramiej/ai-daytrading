import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { PlayIcon, StopIcon, Cog6ToothIcon, ClockIcon } from '@heroicons/react/24/solid';

const ControlPanel = ({
  botRunning,
  onStart,
  onStop,
  isConnected,
  configured = true,
  initialized = true,
  scanIntervalMinutes = 5,
  lastScanTime = null
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const [botStartTime, setBotStartTime] = useState(null);
  const countdownRef = useRef(null);

  // Calculate and update countdown
  useEffect(() => {
    if (botRunning && scanIntervalMinutes > 0) {
      // If bot just started, set start time
      if (!botStartTime) {
        setBotStartTime(Date.now());
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
      // Bot stopped, clear countdown
      setCountdown(null);
      setBotStartTime(null);
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    }
  }, [botRunning, scanIntervalMinutes, botStartTime, lastScanTime]);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      await onStart();
      setBotStartTime(Date.now());
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
      setBotStartTime(null);
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
      <h2 className="text-xl font-semibold text-white mb-4">Bot Control</h2>

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
            Start Bot
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
            Stop Bot
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
