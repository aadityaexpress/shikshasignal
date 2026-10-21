import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { OverviewResponse } from '../types/api';
import { StatCard } from '../components/StatCard';
import { LoadingState, ErrorState } from '../components/LoadingAndError';
import {
  Users,
  FileCheck2,
  AlertTriangle,
  AlertOctagon,
  CheckCircle,
  HelpCircle,
  RotateCcw,
  ShieldAlert,
  ArrowRight,
  BookOpen,
} from '../components/icons';

interface Props {
  onNavigateToStudents: (grade?: number, statusFilter?: string) => void;
  onNavigateToInterventions: () => void;
  onNavigateToGovernance: () => void;
}

export const OverviewScreen: React.FC<Props> = ({
  onNavigateToStudents,
  onNavigateToInterventions,
  onNavigateToGovernance,
}) => {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getOverview();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load overview metrics';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) return <LoadingState message="Aggregating school FLN outcome metrics..." />;
  if (error) return <ErrorState message={error} onRetry={fetchOverview} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Foundational Learning Overview
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Real-time decision support for Grades 1–3 foundational reading and numeracy.
            Every learning-gap flag is derived from transparent, verifiable classroom assessment checks.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            onClick={() => onNavigateToStudents()}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
          >
            <span>Open Class Matrix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Students"
          value={data.total_students}
          subtitle="Grades 1, 2, and 3 enrolled"
          icon={<Users className="w-5 h-5" />}
          onClick={() => onNavigateToStudents()}
        />
        <StatCard
          title="Total Assessments"
          value={data.total_assessments}
          subtitle="Valid skill evaluations"
          icon={<FileCheck2 className="w-5 h-5" />}
        />
        <StatCard
          title="Needs Teacher Review"
          value={data.review_flags_count}
          subtitle="Score ratio below 60% threshold"
          variant="amber"
          icon={<AlertTriangle className="w-5 h-5" />}
          onClick={() => onNavigateToStudents(undefined, 'needs_teacher_review')}
        />
        <StatCard
          title="Priority Review"
          value={data.priority_flags_count}
          subtitle="2 consecutive low scores"
          variant="rose"
          icon={<AlertOctagon className="w-5 h-5" />}
          onClick={() => onNavigateToStudents(undefined, 'priority_for_teacher_review')}
        />
      </div>

      {/* Secondary Metrics & Reassessment Loop */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Proficiency & Evidence Status
            </h3>
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Skills On Track:
              </span>
              <span className="font-semibold text-slate-900">{data.on_track_count}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-400" />
                Insufficient Evidence:
              </span>
              <span className="font-semibold text-slate-900">{data.insufficient_data_count}</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Reassessment Progress Loop
            </h3>
            <RotateCcw className="w-4 h-4 text-teal-600" />
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600">Reassessments Completed:</span>
              <span className="font-semibold text-teal-700">{data.reassessments_completed_count}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600">Pending Follow-up Check:</span>
              <span className="font-semibold text-amber-700">{data.reassessments_pending_count}</span>
            </div>
            <button
              onClick={onNavigateToInterventions}
              className="text-xs font-medium text-teal-600 hover:text-teal-800 flex items-center gap-1 mt-1"
            >
              Log or link follow-up assessment &rarr;
            </button>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Data Quality & Governance
            </h3>
            <ShieldAlert className="w-4 h-4 text-slate-500" />
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600">Validation Warnings:</span>
              <span className="font-semibold text-slate-900">{data.data_quality_warnings_count}</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Duplicates skipped and missing references logged with full audit trail.
            </p>
            <button
              onClick={onNavigateToGovernance}
              className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1 mt-1"
            >
              Inspect audit log & import CSV &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* Decision Rules Transparency Callout */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-teal-700 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Transparent Decision Rules & Governance Notice
            </h4>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              • <strong>Threshold Rule:</strong> Score ratio strictly &lt; 60% triggers "Needs Teacher Review". A score of 3/5 (60%) meets benchmark.
              <br />
              • <strong>Repeated Evidence:</strong> 2 consecutive below-threshold checks elevate status to "Priority Review".
              <br />
              • <strong>Comparability Guardrail:</strong> Only assessments with matching version and score scale are compared.
              <br />
              • <strong>Attendance Context:</strong> Attendance is strictly contextual metadata and never triggers learning-gap flags.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
