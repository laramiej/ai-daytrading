import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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

  // Start bot
  startBot: async () => {
    const response = await api.post('/api/bot/start');
    return response.data;
  },

  // Stop bot
  stopBot: async () => {
    const response = await api.post('/api/bot/stop');
    return response.data;
  },
};

export default apiClient;
