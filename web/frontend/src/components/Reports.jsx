import React, { useState, useEffect } from 'react';
import {
  DocumentChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  CameraIcon,
} from '@heroicons/react/24/outline';
import apiClient from '../utils/api';
import { formatCurrency, formatPercent } from '../utils/formatters';
import DateSelector from './reports/DateSelector';
import PortfolioComparison from './reports/PortfolioComparison';
import DailyTradesTable from './reports/DailyTradesTable';

const Reports = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [capturingSnapshot, setCapturingSnapshot] = useState(false);

  // Get today's date string
  const today = new Date().toISOString().split('T')[0];

  // Fetch list of available reports
  const fetchReportsList = async () => {
    try {
      const response = await apiClient.getReports();
      const dates = response.reports?.map(r => r.date) || [];

      // Always include today
      if (!dates.includes(today)) {
        dates.unshift(today);
      }

      setAvailableDates(dates);

      // Select today by default if no date selected
      if (!selectedDate) {
        setSelectedDate(today);
      }
    } catch (err) {
      console.error('Error fetching reports list:', err);
      // Still set today as available
      setAvailableDates([today]);
      setSelectedDate(today);
    }
  };

  // Fetch report for selected date
  const fetchReport = async (date) => {
    if (!date) return;

    setLoading(true);
    setError(null);

    try {
      let response;
      if (date === today) {
        response = await apiClient.getTodayReport();
      } else {
        response = await apiClient.getReport(date);
      }
      setReport(response.report);
    } catch (err) {
      console.error('Error fetching report:', err);
      if (err.response?.status === 404) {
        // No report for this date - show empty state
        setReport(null);
        setError(null);
      } else {
        setError(err.message || 'Failed to fetch report');
      }
    } finally {
      setLoading(false);
    }
  };

  // Capture manual snapshot
  const handleCaptureSnapshot = async (type = 'manual') => {
    setCapturingSnapshot(true);
    try {
      await apiClient.captureSnapshot(type);
      // Refresh report to show new snapshot
      await fetchReport(selectedDate);
    } catch (err) {
      console.error('Error capturing snapshot:', err);
      setError(err.message || 'Failed to capture snapshot');
    } finally {
      setCapturingSnapshot(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchReportsList();
  }, []);

  // Fetch report when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchReport(selectedDate);
    }
  }, [selectedDate]);

  // Auto-refresh for today's report
  useEffect(() => {
    if (selectedDate === today) {
      const interval = setInterval(() => {
        fetchReport(today);
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [selectedDate, today]);

  // Summary card component
  const SummaryCard = ({ title, value, subValue, icon: Icon, trend, color = 'blue' }) => {
    const colorClasses = {
      blue: 'text-blue-400',
      green: 'text-green-400',
      red: 'text-red-400',
      yellow: 'text-yellow-400',
    };

    return (
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-400">{title}</p>
            <p className={`text-2xl font-bold mt-1 ${trend != null ? (trend >= 0 ? 'text-green-400' : 'text-red-400') : 'text-white'}`}>
              {value}
            </p>
            {subValue && (
              <p className="text-sm text-slate-500 mt-1">{subValue}</p>
            )}
          </div>
          {Icon && (
            <div className={`p-2 rounded-lg bg-slate-700/50 ${colorClasses[color]}`}>
              <Icon className="h-6 w-6" />
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render loading state
  if (loading && !report) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-slate-400">Loading reports...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white flex items-center">
            <DocumentChartBarIcon className="h-8 w-8 mr-3 text-blue-400" />
            Daily Trading Reports
          </h1>
          <p className="text-slate-400 mt-2">
            Track your trading performance day by day
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-900 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Date selector */}
        <div className="mb-6">
          <DateSelector
            selectedDate={selectedDate}
            availableDates={availableDates}
            onDateChange={setSelectedDate}
            onTodayClick={() => setSelectedDate(today)}
          />
        </div>

        {/* Manual snapshot button (only for today) */}
        {selectedDate === today && (
          <div className="mb-6 flex justify-end">
            <button
              onClick={() => handleCaptureSnapshot('manual')}
              disabled={capturingSnapshot}
              className="flex items-center px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              <CameraIcon className="h-5 w-5 mr-2" />
              {capturingSnapshot ? 'Capturing...' : 'Capture Snapshot'}
            </button>
          </div>
        )}

        {/* Report content */}
        {report ? (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <SummaryCard
                title="Total P&L"
                value={formatCurrency(report.total_pnl || 0)}
                subValue={`Realized: ${formatCurrency(report.realized_pnl || 0)}`}
                icon={CurrencyDollarIcon}
                trend={report.total_pnl}
                color={report.total_pnl >= 0 ? 'green' : 'red'}
              />
              <SummaryCard
                title="Trades Executed"
                value={report.trades?.length || 0}
                subValue={`${report.blocked_trades?.length || 0} blocked`}
                icon={ChartBarIcon}
                color="blue"
              />
              <SummaryCard
                title="Win Rate"
                value={report.win_count + report.loss_count > 0
                  ? formatPercent((report.win_count / (report.win_count + report.loss_count)) * 100)
                  : 'N/A'}
                subValue={`${report.win_count || 0}W / ${report.loss_count || 0}L`}
                icon={report.win_count >= report.loss_count ? ArrowTrendingUpIcon : ArrowTrendingDownIcon}
                color={report.win_count >= report.loss_count ? 'green' : 'red'}
              />
              <SummaryCard
                title="Signals Analyzed"
                value={report.signals_analyzed || 0}
                subValue={`${report.signals_actioned || 0} actioned`}
                icon={DocumentChartBarIcon}
                color="yellow"
              />
            </div>

            {/* Portfolio comparison */}
            <div className="mb-8">
              <PortfolioComparison
                openSnapshot={report.market_open_snapshot}
                closeSnapshot={report.market_close_snapshot}
              />
            </div>

            {/* Trades table */}
            <div className="mb-8">
              <DailyTradesTable
                trades={report.trades || []}
                blockedTrades={report.blocked_trades || []}
              />
            </div>
          </>
        ) : (
          <div className="bg-slate-800 rounded-lg p-12 border border-slate-700 text-center">
            <DocumentChartBarIcon className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">No Report Data</h3>
            <p className="text-slate-400">
              {selectedDate === today
                ? "No trading activity recorded yet today. Start the bot to begin tracking."
                : "No report data is available for this date."
              }
            </p>
            {selectedDate === today && (
              <button
                onClick={() => handleCaptureSnapshot('manual')}
                disabled={capturingSnapshot}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                <CameraIcon className="h-5 w-5 inline mr-2" />
                {capturingSnapshot ? 'Capturing...' : 'Capture Starting Snapshot'}
              </button>
            )}
          </div>
        )}

        {/* Report metadata */}
        {report && (
          <div className="text-xs text-slate-500 text-right">
            Created: {report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'} |
            Updated: {report.updated_at ? new Date(report.updated_at).toLocaleString() : 'N/A'}
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;
