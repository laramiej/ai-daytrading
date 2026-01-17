import React from 'react';
import { ChevronLeftIcon, ChevronRightIcon, CalendarIcon } from '@heroicons/react/24/outline';

const DateSelector = ({ selectedDate, availableDates, onDateChange, onTodayClick }) => {
  // Format date for display
  const formatDisplayDate = (dateStr) => {
    const date = new Date(dateStr + 'T12:00:00'); // Add time to avoid timezone issues
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Get today's date string
  const today = new Date().toISOString().split('T')[0];
  const isToday = selectedDate === today;

  // Find current date index in available dates
  const currentIndex = availableDates.indexOf(selectedDate);

  // Navigate to previous/next date
  const goToPrevious = () => {
    if (currentIndex < availableDates.length - 1) {
      onDateChange(availableDates[currentIndex + 1]);
    }
  };

  const goToNext = () => {
    if (currentIndex > 0) {
      onDateChange(availableDates[currentIndex - 1]);
    }
  };

  // Check if navigation is possible
  const canGoPrevious = currentIndex < availableDates.length - 1;
  const canGoNext = currentIndex > 0;

  return (
    <div className="flex items-center justify-between bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center space-x-4">
        {/* Navigation buttons */}
        <button
          onClick={goToPrevious}
          disabled={!canGoPrevious}
          className={`p-2 rounded-lg transition-colors ${
            canGoPrevious
              ? 'text-slate-300 hover:bg-slate-700 hover:text-white'
              : 'text-slate-600 cursor-not-allowed'
          }`}
          title="Previous day"
        >
          <ChevronLeftIcon className="h-5 w-5" />
        </button>

        {/* Date display */}
        <div className="flex items-center space-x-3">
          <CalendarIcon className="h-5 w-5 text-slate-400" />
          <div>
            <div className="text-white font-medium">
              {formatDisplayDate(selectedDate)}
            </div>
            {isToday && (
              <div className="text-xs text-green-400">Today (Live)</div>
            )}
          </div>
        </div>

        <button
          onClick={goToNext}
          disabled={!canGoNext}
          className={`p-2 rounded-lg transition-colors ${
            canGoNext
              ? 'text-slate-300 hover:bg-slate-700 hover:text-white'
              : 'text-slate-600 cursor-not-allowed'
          }`}
          title="Next day"
        >
          <ChevronRightIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Quick actions */}
      <div className="flex items-center space-x-2">
        {!isToday && (
          <button
            onClick={onTodayClick}
            className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Go to Today
          </button>
        )}

        {/* Date picker dropdown */}
        <select
          value={selectedDate}
          onChange={(e) => onDateChange(e.target.value)}
          className="bg-slate-700 text-white text-sm rounded-lg px-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {availableDates.map((date) => (
            <option key={date} value={date}>
              {date}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default DateSelector;
