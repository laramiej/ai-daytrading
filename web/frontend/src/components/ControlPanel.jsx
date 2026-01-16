import React, { useState } from 'react';
import { PlayIcon, StopIcon } from '@heroicons/react/24/solid';

const ControlPanel = ({ botRunning, onStart, onStop, isConnected }) => {
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await onStart();
    } catch (error) {
      console.error('Error starting bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await onStop();
    } catch (error) {
      console.error('Error stopping bot:', error);
    } finally {
      setLoading(false);
    }
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

        {/* Control buttons */}
        <div className="flex space-x-3 mt-6">
          <button
            onClick={handleStart}
            disabled={botRunning || loading}
            className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
              botRunning || loading
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
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
