import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Default timeout for most operations
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// Longer timeout for LLM operations (bot start, initialization)
const LLM_TIMEOUT = 120000; // 2 minutes

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
export const apiClient = {
  // Health check
  health: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Get configuration status
  getConfigStatus: async () => {
    const response = await api.get('/api/config/status');
    return response.data;
  },

  // Initialize trading system after config changes (may involve LLM validation)
  initializeSystem: async () => {
    const response = await api.post('/api/config/initialize', {}, { timeout: LLM_TIMEOUT });
    return response.data;
  },

  // Get account status and portfolio overview
  getStatus: async () => {
    const response = await api.get('/api/status');
    return response.data;
  },

  // Get all positions
  getPositions: async () => {
    const response = await api.get('/api/positions');
    return response.data;
  },

  // Get settings
  getSettings: async () => {
    const response = await api.get('/api/settings');
    return response.data;
  },

  // Update settings
  updateSettings: async (settings) => {
    const response = await api.put('/api/settings', settings);
    return response.data;
  },

  // Start bot (involves LLM for trading analysis)
  startBot: async () => {
    const response = await api.post('/api/bot/start', {}, { timeout: LLM_TIMEOUT });
    return response.data;
  },

  // Stop bot
  stopBot: async () => {
    const response = await api.post('/api/bot/stop');
    return response.data;
  },

  // Get pending trades awaiting approval
  getPendingTrades: async () => {
    const response = await api.get('/api/pending-trades');
    return response.data;
  },

  // Approve a pending trade
  approveTrade: async (tradeId) => {
    const response = await api.post(`/api/pending-trades/${tradeId}/approve`, {}, { timeout: LLM_TIMEOUT });
    return response.data;
  },

  // Reject a pending trade
  rejectTrade: async (tradeId) => {
    const response = await api.post(`/api/pending-trades/${tradeId}/reject`);
    return response.data;
  },

  // Clear all pending trades
  clearPendingTrades: async () => {
    const response = await api.post('/api/pending-trades/clear');
    return response.data;
  },

  // ============================================
  // Daily Reports
  // ============================================

  // Get list of available reports
  getReports: async () => {
    const response = await api.get('/api/reports');
    return response.data;
  },

  // Get today's report (in-progress)
  getTodayReport: async () => {
    const response = await api.get('/api/reports/today');
    return response.data;
  },

  // Get report for a specific date
  getReport: async (date) => {
    const response = await api.get(`/api/reports/${date}`);
    return response.data;
  },

  // Manually capture a portfolio snapshot
  captureSnapshot: async (snapshotType = 'manual') => {
    const response = await api.post('/api/reports/snapshot', { snapshot_type: snapshotType });
    return response.data;
  },
};

export default apiClient;
