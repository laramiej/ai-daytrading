import React, { useState, useEffect } from 'react';
import {
  Cog6ToothIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  KeyIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import apiClient from '../utils/api';
import { formatCurrency } from '../utils/formatters';

const Settings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSettings();
      setSettings(data);
      setFormData(data);
    } catch (err) {
      console.error('Error fetching settings:', err);
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await apiClient.updateSettings(formData);

      // Refresh settings to get updated config status
      const updatedSettings = await apiClient.getSettings();
      setSettings(updatedSettings);
      setFormData(updatedSettings);

      if (updatedSettings.configured && !updatedSettings.initialized) {
        setSuccessMessage('Settings saved! Click "Initialize System" to apply changes.');
      } else {
        setSuccessMessage('Settings saved successfully!');
      }
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleInitialize = async () => {
    try {
      setInitializing(true);
      setError(null);
      setSuccessMessage(null);

      const result = await apiClient.initializeSystem();

      if (result.initialized) {
        setSuccessMessage('Trading system initialized successfully! You can now start the bot.');
        // Refresh settings to update status
        const updatedSettings = await apiClient.getSettings();
        setSettings(updatedSettings);
        setFormData(updatedSettings);
      } else {
        setError(result.message || 'Failed to initialize');
      }
    } catch (err) {
      console.error('Error initializing system:', err);
      setError(err.response?.data?.detail || 'Failed to initialize trading system');
    } finally {
      setInitializing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white flex items-center">
            <Cog6ToothIcon className="h-8 w-8 mr-3" />
            Settings
          </h1>
          <p className="text-slate-400 mt-2">
            Configure your trading bot parameters and API credentials
          </p>
        </div>

        {/* Configuration Status Banner */}
        {settings && !settings.configured && (
          <div className="mb-6 bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-yellow-400 font-semibold">Configuration Required</h3>
                <p className="text-yellow-300/80 text-sm mt-1">
                  Please configure the following to enable trading:
                </p>
                <ul className="text-yellow-300/80 text-sm mt-2 list-disc list-inside">
                  {settings.missing?.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* System Ready but Not Initialized */}
        {settings && settings.configured && !settings.initialized && (
          <div className="mb-6 bg-blue-900/20 border border-blue-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-start">
                <ArrowPathIcon className="h-6 w-6 text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-blue-400 font-semibold">Ready to Initialize</h3>
                  <p className="text-blue-300/80 text-sm mt-1">
                    API keys are configured. Initialize the system to start trading.
                  </p>
                </div>
              </div>
              <button
                onClick={handleInitialize}
                disabled={initializing}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center"
              >
                {initializing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Initializing...
                  </>
                ) : (
                  'Initialize System'
                )}
              </button>
            </div>
          </div>
        )}

        {/* System Initialized */}
        {settings && settings.configured && settings.initialized && (
          <div className="mb-6 bg-green-900/20 border border-green-700 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-6 w-6 text-green-400 mr-3" />
              <div>
                <h3 className="text-green-400 font-semibold">System Ready</h3>
                <p className="text-green-300/80 text-sm">
                  Trading system is initialized and ready. You can start the bot from the Dashboard.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 bg-green-900/20 border border-green-900 rounded-lg p-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3" />
            <p className="text-green-400">{successMessage}</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-900 rounded-lg p-4 flex items-center">
            <ExclamationCircleIcon className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* API Credentials Section */}
        <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700 mb-6">
          <div className="flex items-center mb-4">
            <KeyIcon className="h-6 w-6 text-blue-400 mr-2" />
            <h2 className="text-xl font-semibold text-white">API Credentials</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Alpaca API Key
              </label>
              <input
                type="password"
                value={formData.alpaca_api_key || ''}
                onChange={(e) => handleInputChange('alpaca_api_key', e.target.value)}
                placeholder="Enter your Alpaca API key"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Alpaca Secret Key
              </label>
              <input
                type="password"
                value={formData.alpaca_secret_key || ''}
                onChange={(e) => handleInputChange('alpaca_secret_key', e.target.value)}
                placeholder="Enter your Alpaca secret key"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className={formData.default_llm_provider === 'n8n' ? 'opacity-50' : ''}>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Anthropic API Key {formData.default_llm_provider === 'n8n' && <span className="text-slate-500">(not used with n8n)</span>}
              </label>
              <input
                type="password"
                value={formData.anthropic_api_key || ''}
                onChange={(e) => handleInputChange('anthropic_api_key', e.target.value)}
                placeholder="Enter your Anthropic API key"
                disabled={formData.default_llm_provider === 'n8n'}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:cursor-not-allowed"
              />
            </div>

            <div className={formData.default_llm_provider === 'n8n' ? 'opacity-50' : ''}>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                OpenAI API Key (Optional) {formData.default_llm_provider === 'n8n' && <span className="text-slate-500">(not used with n8n)</span>}
              </label>
              <input
                type="password"
                value={formData.openai_api_key || ''}
                onChange={(e) => handleInputChange('openai_api_key', e.target.value)}
                placeholder="Enter your OpenAI API key"
                disabled={formData.default_llm_provider === 'n8n'}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Finnhub API Key (Optional)
              </label>
              <input
                type="password"
                value={formData.finnhub_api_key || ''}
                onChange={(e) => handleInputChange('finnhub_api_key', e.target.value)}
                placeholder="Enter your Finnhub API key"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <span className="text-sm text-slate-300">Enable Finnhub Sentiment</span>
                  <p className="text-xs text-slate-500">Use Finnhub for market and stock sentiment analysis (requires API key)</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleInputChange('enable_finnhub', !formData.enable_finnhub)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    formData.enable_finnhub ? 'bg-blue-600' : 'bg-slate-600'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      formData.enable_finnhub ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            <div className={formData.default_llm_provider === 'n8n' ? 'opacity-50' : ''}>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Google API Key (Optional) {formData.default_llm_provider === 'n8n' && <span className="text-slate-500">(not used with n8n)</span>}
              </label>
              <input
                type="password"
                value={formData.google_api_key || ''}
                onChange={(e) => handleInputChange('google_api_key', e.target.value)}
                placeholder="Enter your Google API key"
                disabled={formData.default_llm_provider === 'n8n'}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Default LLM Provider
              </label>
              <select
                value={formData.default_llm_provider || 'anthropic'}
                onChange={(e) => {
                  const newProvider = e.target.value;
                  handleInputChange('default_llm_provider', newProvider);
                  // Clear irrelevant API keys when switching to n8n
                  if (newProvider === 'n8n') {
                    // n8n doesn't need traditional LLM keys
                  }
                }}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openai">OpenAI (GPT)</option>
                <option value="google">Google (Gemini)</option>
                <option value="n8n">n8n Workflow (External)</option>
              </select>
              {formData.default_llm_provider === 'n8n' && (
                <p className="text-xs text-amber-400 mt-2">
                  n8n mode delegates all analysis to an external n8n workflow. Traditional LLM API keys are not used.
                </p>
              )}
            </div>

            {/* n8n Webhook URL - only shown when n8n is selected */}
            {formData.default_llm_provider === 'n8n' && (
              <div className="mt-4 p-4 bg-slate-700/50 rounded-lg border border-amber-600/30">
                <label className="block text-sm font-medium text-amber-300 mb-2">
                  n8n Webhook URL
                </label>
                <input
                  type="text"
                  value={formData.n8n_webhook_url || ''}
                  onChange={(e) => handleInputChange('n8n_webhook_url', e.target.value)}
                  placeholder="https://your-n8n-instance.com/webhook/stock-analysis"
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
                <p className="text-xs text-slate-400 mt-2">
                  The webhook URL from your n8n stock analysis workflow. Import the workflow from <code className="text-amber-400">n8n/stock_analysis_workflow.json</code>.
                </p>
              </div>
            )}

            {/* Note about provider requirements */}
            {formData.default_llm_provider !== 'n8n' && (
              <p className="text-xs text-slate-500 mt-2">
                Make sure you have a valid API key configured for the selected provider above.
              </p>
            )}
          </div>
        </div>

        {/* Risk Management Section */}
        <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700 mb-6">
          <div className="flex items-center mb-4">
            <ShieldCheckIcon className="h-6 w-6 text-green-400 mr-2" />
            <h2 className="text-xl font-semibold text-white">Risk Management</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Max Position Size (USD)
              </label>
              <input
                type="number"
                value={formData.max_position_size || 0}
                onChange={(e) => handleInputChange('max_position_size', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {formatCurrency(settings?.max_position_size || 0)}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Max Daily Loss (USD)
              </label>
              <input
                type="number"
                value={formData.max_daily_loss || 0}
                onChange={(e) => handleInputChange('max_daily_loss', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {formatCurrency(settings?.max_daily_loss || 0)}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Max Total Exposure (USD)
              </label>
              <input
                type="number"
                value={formData.max_total_exposure || 0}
                onChange={(e) => handleInputChange('max_total_exposure', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {formatCurrency(settings?.max_total_exposure || 0)}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Max Open Positions
              </label>
              <input
                type="number"
                value={formData.max_open_positions || 0}
                onChange={(e) => handleInputChange('max_open_positions', parseInt(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {settings?.max_open_positions || 0}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Max Position Exposure (%)
              </label>
              <input
                type="number"
                step="1"
                min="1"
                max="100"
                value={formData.max_position_exposure_percent || 25}
                onChange={(e) => handleInputChange('max_position_exposure_percent', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">
                Current: {settings?.max_position_exposure_percent || 25}% of max exposure per position
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Stop Loss Percentage (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.stop_loss_percentage || 0}
                onChange={(e) => handleInputChange('stop_loss_percentage', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {settings?.stop_loss_percentage || 0}%</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Take Profit Percentage (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.take_profit_percentage || 0}
                onChange={(e) => handleInputChange('take_profit_percentage', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Current: {settings?.take_profit_percentage || 0}%</p>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.enable_auto_trading || false}
                onChange={(e) => handleInputChange('enable_auto_trading', e.target.checked)}
                className="w-5 h-5 bg-slate-900 border-slate-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-300">
                Enable Auto Trading (Execute trades automatically without approval)
              </span>
            </label>

            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.enable_short_selling || false}
                onChange={(e) => handleInputChange('enable_short_selling', e.target.checked)}
                className="w-5 h-5 bg-slate-900 border-slate-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-300">
                Enable Short Selling
              </span>
            </label>
          </div>

          <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
            <p className="text-xs text-slate-400">
              <strong className="text-slate-300">Dynamic Position Sizing:</strong> Each new position is limited by the minimum of:
              (1) Max Position Size, (2) Max Position Exposure % of total exposure limit, and (3) fair share of remaining exposure budget divided by remaining position slots.
              This ensures room is left for other trades.
            </p>
          </div>
        </div>

        {/* Bot Scheduling Section */}
        <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700 mb-6">
          <div className="flex items-center mb-4">
            <ClockIcon className="h-6 w-6 text-purple-400 mr-2" />
            <h2 className="text-xl font-semibold text-white">Bot Scheduling</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Scan Interval (minutes)
              </label>
              <select
                value={formData.scan_interval_minutes || 5}
                onChange={(e) => handleInputChange('scan_interval_minutes', parseInt(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value={1}>Every 1 minute</option>
                <option value={2}>Every 2 minutes</option>
                <option value={5}>Every 5 minutes</option>
                <option value={10}>Every 10 minutes</option>
                <option value={15}>Every 15 minutes</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every 1 hour</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Current: Every {settings?.scan_interval_minutes || 5} minutes
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Minimum Confidence Threshold (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                step="5"
                value={formData.min_confidence_threshold || 70}
                onChange={(e) => handleInputChange('min_confidence_threshold', parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">
                Current: {settings?.min_confidence_threshold || 70}% - Only act on signals with higher confidence
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.close_positions_at_session_end || false}
                onChange={(e) => handleInputChange('close_positions_at_session_end', e.target.checked)}
                className="w-5 h-5 bg-slate-900 border-slate-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-300">
                Close All Positions at Market Close
              </span>
            </label>
            <p className="text-xs text-slate-500 ml-8">
              When enabled, all open positions will be automatically closed when the market closes for the day.
              This ensures you don't hold overnight positions.
            </p>

            <label className="flex items-center space-x-3 pt-2">
              <input
                type="checkbox"
                checked={formData.enable_ai_critique || false}
                onChange={(e) => handleInputChange('enable_ai_critique', e.target.checked)}
                className="w-5 h-5 bg-slate-900 border-slate-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-300">
                Enable AI Critique (Second Opinion)
              </span>
            </label>
            <p className="text-xs text-slate-500 ml-8">
              When enabled, a second AI call will critique each BUY/SELL recommendation before execution.
              The critique can lower confidence if it finds flaws in the reasoning. This doubles LLM API usage but improves decision quality.
            </p>
          </div>

          <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
            <p className="text-xs text-slate-400">
              <strong className="text-slate-300">How it works:</strong> The bot scans your watchlist at the specified interval during market hours.
              Only trading signals with confidence above the threshold will be considered. Lower intervals mean more frequent scans but higher API usage.
            </p>
          </div>
        </div>

        {/* Watchlist Section */}
        <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700 mb-6">
          <div className="flex items-center mb-4">
            <ChartBarIcon className="h-6 w-6 text-yellow-400 mr-2" />
            <h2 className="text-xl font-semibold text-white">Watchlist</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Symbols to Monitor (comma-separated)
            </label>
            <input
              type="text"
              value={formData.watchlist?.join(',') || ''}
              onChange={(e) => handleInputChange('watchlist', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              placeholder="AAPL,MSFT,GOOGL,TSLA"
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">
              Current: {settings?.watchlist?.join(', ') || 'None'}
            </p>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={fetchSettings}
            disabled={saving}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>
        </div>

        {/* Helpful Info */}
        <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <p className="text-slate-400 text-sm">
            <strong className="text-slate-300">Getting Started:</strong> Enter your API keys above and click Save, then Initialize System.
            After initialization, you can start the trading bot from the Dashboard.
          </p>
          <p className="text-slate-500 text-xs mt-2">
            Get your Alpaca API keys at <a href="https://alpaca.markets" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">alpaca.markets</a> and
            your Anthropic API key at <a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">console.anthropic.com</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
