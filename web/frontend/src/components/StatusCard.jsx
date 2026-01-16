import React from 'react';
import { formatCurrency, formatPercent, getPnlColor } from '../utils/formatters';

const StatusCard = ({ title, value, subValue, icon: Icon, trend }) => {
  return (
    <div className="bg-slate-800 rounded-lg p-6 shadow-lg border border-slate-700">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
          {subValue && (
            <p className={`mt-1 text-sm font-medium ${getPnlColor(trend || 0)}`}>
              {subValue}
            </p>
          )}
        </div>
        {Icon && (
          <div className="ml-4">
            <Icon className="h-12 w-12 text-slate-500" />
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusCard;
