import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { InterventionItem, ReassessmentLinkResponse } from '../types/api';
import { LoadingState, ErrorState, EmptyState } from '../components/LoadingAndError';
import {
  HeartHandshake,
  PlusCircle,
  Link as LinkIcon,
  CheckCircle,
  Clock,
  ArrowRight,
  Filter,
} from '../components/icons';

interface Props {
  presetStudentId?: string;
  presetSkillCode?: string;
}

const SKILL_OPTIONS = [
  { code: 'letter_recognition', label: 'Letter Recognition' },
  { code: 'word_reading', label: 'Word Reading' },
  { code: 'sentence_reading', label: 'Sentence Reading' },
  { code: 'reading_comprehension', label: 'Reading Comprehension' },
  { code: 'number_recognition', label: 'Number Recognition' },
  { code: 'place_value', label: 'Place Value' },
  { code: 'addition', label: 'Addition' },
  { code: 'subtraction', label: 'Subtraction' },
];

export const InterventionsScreen: React.FC<Props> = ({
  presetStudentId = '',
  presetSkillCode = 'word_reading',
}) => {
  const [interventions, setInterventions] = useState<InterventionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [studentId, setStudentId] = useState(presetStudentId);
  const [skillCode, setSkillCode] = useState(presetSkillCode);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [type, setType] = useState('guided_micro_practice');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Reassessment link states
  const [selectedIntvId, setSelectedIntvId] = useState<string>('');
  const [followupEventId, setFollowupEventId] = useState<string>('');
  const [linking, setLinking] = useState(false);
  const [linkResult, setLinkResult] = useState<ReassessmentLinkResponse | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);

  const fetchInterventions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getInterventions();
      setInterventions(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load interventions';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterventions();
  }, []);

  const handleCreateIntervention = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim()) {
      setFormError('Student ID is required.');
      return;
    }
    setSubmitting(true);
    setFormSuccess(null);
    setFormError(null);
    try {
      await api.createIntervention({
        student_id: studentId.trim(),
        skill_code: skillCode,
        intervention_date: date,
        intervention_type: type,
        teacher_note_non_identifying: note.trim() || 'Completed targeted practice session.',
        followup_assessment_id: null,
      });
      setFormSuccess(`Intervention recorded successfully for ${studentId}.`);
      setNote('');
      fetchInterventions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to record intervention';
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLinkReassessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIntvId || !followupEventId.trim()) {
      setLinkError('Both intervention and follow-up assessment ID are required.');
      return;
    }
    setLinking(true);
    setLinkResult(null);
    setLinkError(null);
    try {
      const res = await api.linkReassessment({
        intervention_id: selectedIntvId,
        followup_assessment_id: followupEventId.trim(),
      });
      setLinkResult(res);
      fetchInterventions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to link follow-up assessment';
      setLinkError(msg);
    } finally {
      setLinking(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">
          Teacher Intervention & Progress Tracking
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Record small-group or individual classroom remediation and connect follow-up assessment checks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Log New Intervention Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <PlusCircle className="w-4 h-4 text-teal-700" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Record New Remediation
            </h2>
          </div>

          {formSuccess && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-800">
              {formSuccess}
            </div>
          )}
          {formError && (
            <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-800">
              {formError}
            </div>
          )}

          <form onSubmit={handleCreateIntervention} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-600 font-semibold mb-1">Student ID (Pseudonymous)</label>
              <input
                type="text"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                placeholder="e.g. STU-0001"
                className="w-full px-3 py-1.5 border border-slate-300 rounded-md font-mono focus:ring-1 focus:ring-teal-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Target Skill</label>
              <select
                value={skillCode}
                onChange={(e) => setSkillCode(e.target.value)}
                className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white focus:ring-1 focus:ring-teal-500 focus:outline-none"
              >
                {SKILL_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label} ({opt.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Date Delivered</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Activity Category</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded-md bg-white focus:ring-1 focus:ring-teal-500 focus:outline-none"
                >
                  <option value="guided_micro_practice">Guided Practice</option>
                  <option value="flashcard_phonics_drill">Phonics Drill</option>
                  <option value="concrete_manipulatives">Manipulatives Math</option>
                  <option value="paired_peer_reading">Paired Reading</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Teacher Pedagogical Note (Non-identifying)</label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Brief pedagogical observations, e.g. Practiced 3-letter word cards with slider."
                rows={3}
                className="w-full px-3 py-1.5 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-500 focus:outline-none"
              />
              <p className="text-[10px] text-slate-400 mt-0.5">
                Do not include student personal names or identifying details.
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-semibold rounded-lg shadow-xs transition"
            >
              {submitting ? 'Saving Record...' : 'Record Intervention'}
            </button>
          </form>

          {/* Reassessment Linker Form */}
          <div className="pt-4 border-t border-slate-100 space-y-3 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-800 uppercase tracking-wide">
              <LinkIcon className="w-3.5 h-3.5 text-teal-700" />
              <span>Link Follow-up Assessment</span>
            </div>

            {linkResult && (
              <div
                className={`p-2.5 rounded-lg border text-xs ${
                  linkResult.comparable
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}
              >
                {linkResult.message}
              </div>
            )}
            {linkError && (
              <div className="bg-rose-50 border border-rose-200 rounded p-2 text-xs text-rose-800">
                {linkError}
              </div>
            )}

            <form onSubmit={handleLinkReassessment} className="space-y-2">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Target Intervention</label>
                <select
                  value={selectedIntvId}
                  onChange={(e) => setSelectedIntvId(e.target.value)}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded-md bg-white focus:ring-1 focus:ring-teal-500 focus:outline-none font-mono text-[11px]"
                >
                  <option value="">Select intervention record...</option>
                  {interventions.map((i) => (
                    <option key={i.intervention_id} value={i.intervention_id}>
                      {i.student_id} - {i.skill_code} ({i.intervention_date})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Follow-up Assessment Event ID</label>
                <input
                  type="text"
                  value={followupEventId}
                  onChange={(e) => setFollowupEventId(e.target.value)}
                  placeholder="e.g. ASMT-0200"
                  className="w-full px-2 py-1.5 border border-slate-300 rounded-md font-mono text-xs focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={linking}
                className="w-full py-1.5 bg-slate-800 hover:bg-slate-900 disabled:bg-slate-300 text-white font-medium rounded-md transition"
              >
                {linking ? 'Verifying Comparability...' : 'Verify & Link Follow-up'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Interventions History Table */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Intervention History & Reassessment Loop ({interventions.length})
            </h2>
            <button
              onClick={fetchInterventions}
              className="text-xs text-teal-600 hover:text-teal-800 font-semibold"
            >
              Refresh Log
            </button>
          </div>

          {loading ? (
            <LoadingState message="Loading intervention records..." />
          ) : error ? (
            <ErrorState message={error} onRetry={fetchInterventions} />
          ) : interventions.length === 0 ? (
            <EmptyState
              title="No Interventions Logged"
              description="No teacher interventions have been recorded yet. Use the form on the left to document classroom remediation."
            />
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {interventions.map((intv) => (
                <div
                  key={intv.intervention_id}
                  className="border border-slate-200 rounded-lg p-4 bg-slate-50/40 text-xs space-y-2 hover:bg-slate-50 transition"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900">{intv.student_id}</span>
                      <span className="px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-medium text-[11px] border border-teal-200">
                        {intv.skill_code}
                      </span>
                      <span className="text-slate-500 font-medium">{intv.intervention_type}</span>
                    </div>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {intv.intervention_date}
                    </span>
                  </div>

                  <p className="text-slate-700 italic">"{intv.teacher_note}"</p>

                  <div className="pt-2 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    {intv.has_reassessment && intv.followup_details ? (
                      <div className="flex items-center gap-1.5 text-emerald-700 font-medium">
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>
                          Reassessed on {intv.followup_details.date}: Score{' '}
                          <strong>{intv.followup_details.score}/{intv.followup_details.max_score}</strong> ({(intv.followup_details.score_ratio * 100).toFixed(0)}%)
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-amber-700 font-medium">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Pending Follow-up Check</span>
                      </div>
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
    </div>
  );
};
