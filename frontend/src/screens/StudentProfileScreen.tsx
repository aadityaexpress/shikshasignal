import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StudentProfileResponse, TeacherActionCard } from '../types/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingState, ErrorState } from '../components/LoadingAndError';
import {
  ArrowLeft,
  Calendar,
  AlertCircle,
  Lightbulb,
  Clock,
  ShieldAlert,
  PlusCircle,
  CheckCircle,
  History,
  BookOpen,
} from '../components/icons';

interface Props {
  studentId: string;
  onBack: () => void;
  onRecordIntervention: (studentId: string, skillCode: string) => void;
}

export const StudentProfileScreen: React.FC<Props> = ({
  studentId,
  onBack,
  onRecordIntervention,
}) => {
  const [profile, setProfile] = useState<StudentProfileResponse | null>(null);
  const [actions, setActions] = useState<TeacherActionCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfileAndActions = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profData, actData] = await Promise.all([
        api.getStudentProfile(studentId),
        api.getStudentActions(studentId),
      ]);
      setProfile(profData);
      setActions(actData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load student profile';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileAndActions();
  }, [studentId]);

  if (loading) return <LoadingState message={`Compiling skill profile for ${studentId}...`} />;
  if (error) return <ErrorState message={error} onRetry={fetchProfileAndActions} />;
  if (!profile) return null;

  return (
    <div className="space-y-6">
      {/* Top Navigation & Student Header */}
      <div>
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 mb-3 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Class Matrix
        </button>

        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold font-mono text-slate-900 tracking-tight">
                {profile.student.student_id}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
                Grade {profile.student.grade}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                {profile.student.school_id}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Foundational Literacy & Numeracy Skill Evidence Profile
            </p>
          </div>

          {/* Contextual Attendance Metadata Callout */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs max-w-md">
            <div className="flex items-center gap-1.5 font-semibold text-slate-700 mb-0.5">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Attendance Context (Non-Causal)</span>
            </div>
            <p className="text-[11px] text-slate-600 leading-tight">
              {profile.attendance_context}
            </p>
          </div>
        </div>
      </div>

      {/* Screen D: Teacher Action Cards (if flagged skills exist) */}
      {actions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                Teacher Decision Support Cards ({actions.length})
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Suggested micro-activities mapped to flagged skills to support immediate classroom instruction.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {actions.map((card) => (
              <div
                key={card.card_id}
                className="bg-white border-2 border-amber-200 rounded-xl p-5 shadow-xs space-y-4"
              >
                {/* Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{card.skill_name}</span>
                    <span className="font-mono text-xs text-slate-400">({card.skill_code})</span>
                    <StatusBadge status={card.status} size="sm" />
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-200">
                    Rule Triggered: {card.triggering_rule}
                  </div>
                </div>

                {/* Evidence Trail */}
                <div className="bg-slate-50 rounded-lg p-3 text-xs border border-slate-200">
                  <p className="font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-slate-500" /> Assessment Evidence Base:
                  </p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {card.evidence.map((ev) => (
                      <span
                        key={ev.record_id}
                        className="bg-white px-2.5 py-1 rounded border border-slate-200 text-slate-700 font-mono text-[11px]"
                      >
                        {ev.assessment_date}: <strong>{ev.score}/{ev.max_score}</strong> ({(ev.score_ratio * 100).toFixed(0)}%) [Form {ev.assessment_version}]
                      </span>
                    ))}
                  </div>
                </div>

                {/* Suggested Pedagogical Micro-Activity */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-teal-800 uppercase tracking-wide flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-teal-700" />
                    Suggested Teacher Micro-Activity: {card.suggested_activity_title}
                  </h4>
                  <div className="bg-teal-50/50 border border-teal-100 rounded-lg p-3 text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                    {card.suggested_activity_steps}
                  </div>
                  <p className="text-[11px] text-slate-500 italic">
                    <strong>Rationale:</strong> {card.activity_rationale}
                  </p>
                </div>

                {/* Follow-up Prompt & Action Button */}
                <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-amber-800 font-medium">
                    <Clock className="w-3.5 h-3.5 text-amber-600" />
                    <span>Follow-up prompt: {card.followup_prompt}</span>
                  </div>

                  <button
                    onClick={() => onRecordIntervention(studentId, card.skill_code)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Log Delivered Intervention
                  </button>
                </div>

                {/* Non-Diagnostic Disclaimer */}
                <div className="bg-amber-50/60 rounded px-3 py-1.5 text-[10px] text-amber-900/80 border border-amber-200/60">
                  {card.teacher_guidance_disclaimer}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Screen C: Comprehensive Skill History Matrix */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">
            Competency Skill Profile & Evaluation History
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent breakdown of every grade-appropriate FLN skill, decision rules, and longitudinal evidence.
          </p>
        </div>

        <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
          {profile.skills.map((sig) => (
            <div key={sig.skill_code} className="p-4 hover:bg-slate-50/50 transition space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-slate-900">{sig.skill_name}</span>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">[{sig.domain}]</span>
                  <StatusBadge status={sig.status} size="sm" />
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  Rule: {sig.triggering_rule}
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {sig.explanation}
              </p>

              {sig.comparability_notes && (
                <div className="bg-amber-50 border border-amber-200 rounded p-2 text-[11px] text-amber-800">
                  {sig.comparability_notes}
                </div>
              )}

              {/* Assessment history chips */}
              {sig.evidence_history.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap pt-1">
                  <span className="text-[10px] font-medium text-slate-400 uppercase">Assessment History:</span>
                  {sig.evidence_history.map((ev) => (
                    <span
                      key={ev.record_id}
                      className="px-2 py-0.5 bg-slate-100 rounded text-[11px] font-mono text-slate-700 border border-slate-200"
                    >
                      {ev.assessment_date}: {ev.score}/{ev.max_score} ({(ev.score_ratio * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Intervention Log for this Student */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Recorded Interventions & Progress</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Closed-loop log of targeted support delivered to this student.
            </p>
          </div>
          <button
            onClick={() => onRecordIntervention(studentId, profile.skills[0]?.skill_code || 'word_reading')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            Add Intervention
          </button>
        </div>

        {profile.interventions.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            No remediation activities recorded yet for this student.
          </p>
        ) : (
          <div className="space-y-3">
            {profile.interventions.map((intv) => (
              <div
                key={intv.intervention_id}
                className="border border-slate-200 rounded-lg p-3.5 text-xs space-y-2 bg-slate-50/50"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900">
                    {intv.intervention_type} • <span className="font-mono">{intv.skill_code}</span>
                  </span>
                  <span className="text-slate-500 font-mono text-[11px]">
                    Delivered on {intv.intervention_date}
                  </span>
                </div>
                <p className="text-slate-600 italic">"{intv.teacher_note}"</p>

                {/* Follow-up Reassessment Status */}
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between">
                  {intv.has_reassessment && intv.followup_details ? (
                    <span className="inline-flex items-center gap-1.5 text-emerald-700 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Reassessed on {intv.followup_details.date}: Score{' '}
                      <strong>{intv.followup_details.score}/{intv.followup_details.max_score}</strong> ({(intv.followup_details.score_ratio * 100).toFixed(0)}%)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
                      <Clock className="w-3.5 h-3.5" />
                      Pending follow-up assessment check
                    </span>
                  )}
                  <span className="text-[10px] font-mono text-slate-400">
                    ID: {intv.intervention_id}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
