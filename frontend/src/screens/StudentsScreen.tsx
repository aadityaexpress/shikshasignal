import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StudentSummary, DecisionStatus } from '../types/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingState, ErrorState, EmptyState } from '../components/LoadingAndError';
import { Search, Filter, ArrowRight } from '../components/icons';

interface Props {
  initialGrade?: number;
  initialStatus?: string;
  onSelectStudent: (studentId: string) => void;
}

export const StudentsScreen: React.FC<Props> = ({
  initialGrade,
  initialStatus,
  onSelectStudent,
}) => {
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [grade, setGrade] = useState<number | undefined>(initialGrade);
  const [statusFilter, setStatusFilter] = useState<string>(initialStatus || '');

  const fetchStudents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getStudents(grade, search, statusFilter);
      setStudents(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load student roster';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [grade, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStudents();
  };

  return (
    <div className="space-y-5">
      {/* Page Title & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Classroom Matrix</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Pseudonymous student cohort across Grades 1–3. Zero direct identifying personal child data.
          </p>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Grade filter */}
          <select
            value={grade || ''}
            onChange={(e) => setGrade(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 shadow-xs focus:ring-1 focus:ring-teal-500 focus:outline-none"
          >
            <option value="">All Grades</option>
            <option value="1">Grade 1</option>
            <option value="2">Grade 2</option>
            <option value="3">Grade 3</option>
          </select>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 shadow-xs focus:ring-1 focus:ring-teal-500 focus:outline-none"
          >
            <option value="">All Decision Statuses</option>
            <option value="priority_for_teacher_review">Priority Review</option>
            <option value="needs_teacher_review">Needs Review</option>
            <option value="on_track">On Track</option>
            <option value="insufficient_data">Insufficient Data</option>
          </select>
        </div>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearchSubmit} className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by pseudonymous ID (e.g. STU-0005) or school ID..."
          className="w-full pl-9 pr-24 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 placeholder-slate-400 shadow-xs focus:ring-1 focus:ring-teal-500 focus:outline-none"
        />
        <button
          type="submit"
          className="absolute right-1.5 top-1 px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white text-xs font-medium rounded-md transition"
        >
          Search
        </button>
      </form>

      {/* Table Content */}
      {loading ? (
        <LoadingState message="Filtering class records..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchStudents} />
      ) : students.length === 0 ? (
        <EmptyState
          title="No Students Found"
          description="No students matched your search criteria or active filters. Try clearing filters or searching for another ID."
          actionText="Reset Filters"
          onAction={() => {
            setSearch('');
            setGrade(undefined);
            setStatusFilter('');
          }}
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3.5">Student ID</th>
                  <th className="px-5 py-3.5">School</th>
                  <th className="px-5 py-3.5">Grade</th>
                  <th className="px-5 py-3.5">Overall Learning Alert</th>
                  <th className="px-5 py-3.5">Flagged Skills</th>
                  <th className="px-5 py-3.5">Last Assessed</th>
                  <th className="px-5 py-3.5 text-right">Decision Support</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {students.map((s) => (
                  <tr
                    key={s.student_id}
                    onClick={() => onSelectStudent(s.student_id)}
                    className="hover:bg-slate-50/80 cursor-pointer transition"
                  >
                    <td className="px-5 py-3.5 font-mono font-semibold text-slate-900">
                      {s.student_id}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600">{s.school_id}</td>
                    <td className="px-5 py-3.5">
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px]">
                        Grade {s.grade}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={s.overall_status} size="sm" />
                    </td>
                    <td className="px-5 py-3.5">
                      {s.flagged_skills_count > 0 ? (
                        <span className="font-semibold text-amber-700">
                          {s.flagged_skills_count} skill{s.flagged_skills_count > 1 ? 's' : ''} to review
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 font-mono text-[11px]">
                      {s.last_assessment_date || 'Unassessed'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectStudent(s.student_id);
                        }}
                        className="inline-flex items-center gap-1 text-teal-700 hover:text-teal-900 font-semibold"
                      >
                        Profile & Actions
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 border-t border-slate-100 text-[11px] text-slate-500 bg-slate-50/50 flex justify-between items-center">
            <span>Showing {students.length} student records</span>
            <span className="italic">Click any row to open student profile & action cards</span>
          </div>
        </div>
      )}
    </div>
  );
};
