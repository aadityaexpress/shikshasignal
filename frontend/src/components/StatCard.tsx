import React, { ReactNode } from 'react';

interface Props {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: ReactNode;
  variant?: 'default' | 'amber' | 'rose' | 'emerald';
  onClick?: () => void;
}

export const StatCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default',
  onClick,
}) => {
  const borderVariants = {
    default: 'border-slate-200 hover:border-slate-300',
    amber: 'border-amber-200 bg-amber-50/30',
    rose: 'border-rose-200 bg-rose-50/30',
    emerald: 'border-emerald-200 bg-emerald-50/30',
  };

  const iconVariants = {
    default: 'bg-slate-100 text-slate-600',
    amber: 'bg-amber-100 text-amber-700',
    rose: 'bg-rose-100 text-rose-700',
    emerald: 'bg-emerald-100 text-emerald-700',
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border p-5 shadow-sm transition-all ${borderVariants[variant]} ${
        onClick ? 'cursor-pointer hover:shadow' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-lg ${iconVariants[variant]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};
