import React from 'react';
import { LayoutDashboard, Users, HeartHandshake, Database } from './icons';
import { HealthResponse } from '../types/api';

export type TabKey = 'overview' | 'students' | 'interventions' | 'governance';

interface Props {
  currentTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  health: HealthResponse | null;
}

export const Navbar: React.FC<Props> = ({ currentTab, onSelectTab, health }) => {
  const tabs = [
    { key: 'overview', label: 'Overview', icon: LayoutDashboard },
    { key: 'students', label: 'Class View', icon: Users },
    { key: 'interventions', label: 'Interventions', icon: HeartHandshake },
    { key: 'governance', label: 'Data & Governance', icon: Database },
  ] as const;

  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-lg shadow-xs">
              SS
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 tracking-tight text-base">ShikshaSignal</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider bg-teal-50 text-teal-700 px-2 py-0.5 rounded-full border border-teal-200">
                  FLN Grades 1–3
                </span>
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                Learning-Gap Early Warning & Teacher Decision Support Layer
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = currentTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => onSelectTab(tab.key)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition ${
                    active
                      ? 'bg-slate-100 text-teal-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-teal-600' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status Indicator */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-slate-200 bg-slate-50">
              <span
                className={`w-2 h-2 rounded-full ${
                  isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span className="text-slate-600">
                {isHealthy ? 'Backend Connected' : 'Offline / Checking'}
              </span>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Demo: SCH-001
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
