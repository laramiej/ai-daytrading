/**
 * Format a number as USD currency
 */
export const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format a number as a percentage
 */
export const formatPercent = (value, decimals = 2) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

/**
 * Format a number with comma separators
 */
export const formatNumber = (value, decimals = 2) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format a timestamp to local time
 */
export const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * Format a timestamp to date and time
 */
export const formatDateTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Get color class based on P&L value
 */
export const getPnlColor = (value) => {
  if (value > 0) return 'text-trading-green';
  if (value < 0) return 'text-trading-red';
  return 'text-gray-400';
};

/**
 * Get background color class based on P&L value
 */
export const getPnlBgColor = (value) => {
  if (value > 0) return 'bg-green-900/20';
  if (value < 0) return 'bg-red-900/20';
  return 'bg-gray-800/20';
};
