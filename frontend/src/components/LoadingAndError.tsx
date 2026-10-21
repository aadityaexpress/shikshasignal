import React from 'react';
import { AlertCircle, RefreshCw } from './icons';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading assessment signals...' }) => (
  <div className="py-16 text-center">
    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-teal-600 mb-3" />
    <p className="text-sm text-slate-500 font-medium">{message}</p>
  </div>
);

export const ErrorState: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Failed to load data', message, onRetry }) => (
  <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center max-w-xl mx-auto my-8">
    <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
    <h3 className="text-base font-semibold text-rose-900">{title}</h3>
    <p className="text-sm text-rose-700 mt-1 mb-4">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
      >
        <RefreshCw className="w-3.5 h-3.5" /> Retry Request
      </button>
    )}
  </div>
);

export const EmptyState: React.FC<{
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}> = ({ title, description, actionText, onAction }) => (
  <div className="border border-dashed border-slate-300 rounded-xl p-12 text-center my-6 bg-white">
    <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
      📋
    </div>
    <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
    <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">{description}</p>
    {actionText && onAction && (
      <button
        onClick={onAction}
        className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium rounded-lg transition"
      >
        {actionText}
      </button>
    )}
  </div>
);
