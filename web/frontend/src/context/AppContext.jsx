import React, { createContext, useContext, useState, useCallback } from 'react';

// Create the context
const AppContext = createContext(null);

// Provider component
export const AppProvider = ({ children }) => {
  // Persistent state that survives navigation
  const [activities, setActivities] = useState([]);
  const [botStartTime, setBotStartTime] = useState(null);
  const [lastScanTime, setLastScanTime] = useState(null);

  // Add activity with deduplication
  const addActivity = useCallback((message) => {
    if (!message.type) return;

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
  }, []);

  // Clear activities (e.g., when bot stops)
  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  // Update bot start time
  const updateBotStartTime = useCallback((time) => {
    setBotStartTime(time);
  }, []);

  // Update last scan time
  const updateLastScanTime = useCallback((time) => {
    setLastScanTime(time);
  }, []);

  // Reset bot state (when bot stops)
  const resetBotState = useCallback(() => {
    setBotStartTime(null);
    setLastScanTime(null);
  }, []);

  const value = {
    // State
    activities,
    botStartTime,
    lastScanTime,
    // Actions
    addActivity,
    clearActivities,
    updateBotStartTime,
    updateLastScanTime,
    resetBotState,
    setActivities,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext;
