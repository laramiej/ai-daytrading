import React from 'react';
import { getConfidenceLevel } from '../utils/formatters';

/**
 * ConfidenceBadge - Displays confidence level as a styled badge
 *
 * @param {number} confidence - Confidence score (0-100)
 * @param {boolean} showPercent - Whether to show the percentage (default: true)
 * @param {string} size - Size variant: 'sm', 'md', 'lg' (default: 'md')
 */
const ConfidenceBadge = ({ confidence, showPercent = true, size = 'md' }) => {
  const level = getConfidenceLevel(confidence);

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const displayText = showPercent && confidence != null && !isNaN(confidence)
    ? `${level.label} (${Math.round(confidence)}%)`
    : level.label;

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${sizeClasses[size]} ${level.color} ${level.bgColor} ${level.borderColor}`}
      title={`Confidence: ${confidence != null ? `${Math.round(confidence)}%` : 'N/A'}`}
    >
      {displayText}
    </span>
  );
};

export default ConfidenceBadge;
