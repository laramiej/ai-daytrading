import React, { useState, useEffect } from 'react';
import {
  Cog6ToothIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  KeyIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import apiClient from '../utils/api';
import { formatCurrency } from '../utils/formatters';

const Settings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
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

      setSuccessMessage('Settings saved successfully! Changes will take effect on next bot restart.');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
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

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Anthropic API Key
              </label>
              <input
                type="password"
                value={formData.anthropic_api_key || ''}
                onChange={(e) => handleInputChange('anthropic_api_key', e.target.value)}
                placeholder="Enter your Anthropic API key"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                OpenAI API Key (Optional)
              </label>
              <input
                type="password"
                value={formData.openai_api_key || ''}
                onChange={(e) => handleInputChange('openai_api_key', e.target.value)}
                placeholder="Enter your OpenAI API key"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
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
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Default LLM Provider
              </label>
              <select
                value={formData.default_llm_provider || 'anthropic'}
                onChange={(e) => handleInputChange('default_llm_provider', e.target.value)}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openai">OpenAI (GPT)</option>
                <option value="google">Google (Gemini)</option>
              </select>
            </div>
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

        {/* Warning */}
        <div className="mt-6 bg-yellow-900/20 border border-yellow-900 rounded-lg p-4">
          <p className="text-yellow-400 text-sm">
            <strong>Note:</strong> API credentials and some settings changes require restarting the bot to take effect.
            Stop the bot before making changes and restart it after saving.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
