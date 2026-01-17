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

/**
 * Confidence level definitions
 * Maps numeric confidence scores to semantic levels
 */
export const CONFIDENCE_LEVELS = {
  VERY_LOW: { min: 0, max: 39, label: 'Very Low', color: 'text-red-400', bgColor: 'bg-red-900/30', borderColor: 'border-red-700' },
  LOW: { min: 40, max: 54, label: 'Low', color: 'text-orange-400', bgColor: 'bg-orange-900/30', borderColor: 'border-orange-700' },
  MODERATE: { min: 55, max: 69, label: 'Moderate', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30', borderColor: 'border-yellow-700' },
  HIGH: { min: 70, max: 84, label: 'High', color: 'text-green-400', bgColor: 'bg-green-900/30', borderColor: 'border-green-700' },
  VERY_HIGH: { min: 85, max: 100, label: 'Very High', color: 'text-emerald-400', bgColor: 'bg-emerald-900/30', borderColor: 'border-emerald-700' },
};

/**
 * Get confidence level info from a numeric score
 * @param {number} confidence - Confidence score (0-100)
 * @returns {object} Level object with label, color, bgColor, borderColor
 */
export const getConfidenceLevel = (confidence) => {
  if (confidence == null || isNaN(confidence)) {
    return { label: 'N/A', color: 'text-slate-400', bgColor: 'bg-slate-700', borderColor: 'border-slate-600' };
  }

  const score = Math.max(0, Math.min(100, confidence));

  if (score <= 39) return CONFIDENCE_LEVELS.VERY_LOW;
  if (score <= 54) return CONFIDENCE_LEVELS.LOW;
  if (score <= 69) return CONFIDENCE_LEVELS.MODERATE;
  if (score <= 84) return CONFIDENCE_LEVELS.HIGH;
  return CONFIDENCE_LEVELS.VERY_HIGH;
};

/**
 * Format confidence as a display string with level
 * @param {number} confidence - Confidence score (0-100)
 * @param {boolean} showPercent - Whether to include the percentage
 * @returns {string} Formatted string like "High (75%)" or just "High"
 */
export const formatConfidence = (confidence, showPercent = true) => {
  const level = getConfidenceLevel(confidence);
  if (showPercent && confidence != null && !isNaN(confidence)) {
    return `${level.label} (${Math.round(confidence)}%)`;
  }
  return level.label;
};
