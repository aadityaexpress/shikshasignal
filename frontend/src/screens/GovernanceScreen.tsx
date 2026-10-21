import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ImportSummaryResponse, ValidationLogItem } from '../types/api';
import { LoadingState, ErrorState } from '../components/LoadingAndError';
import {
  Upload,
  Database,
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  FileWarning,
  RefreshCw,
  Info,
} from '../components/icons';

export const GovernanceScreen: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState('auto');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<ImportSummaryResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [logs, setLogs] = useState<ValidationLogItem[]>([]);
  const [logFilter, setLogFilter] = useState('');
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [logError, setLogError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoadingLogs(true);
    setLogError(null);
    try {
      const res = await api.getValidationLogs(100, logFilter || undefined);
      setLogs(res.logs);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load validation logs';
      setLogError(msg);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [logFilter]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setUploadError('Please select a .csv file to import.');
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const result = await api.importCsv(file, fileType);
      setUploadResult(result);
      setFile(null);
      fetchLogs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'CSV upload failed';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">
          Data Import & Audit Governance
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Ingest classroom assessment CSVs, audit data quality checks, and monitor referential integrity logs.
        </p>
      </div>

      {/* Synthetic Dataset Disclaimer Banner */}
      <div className="bg-slate-100 border border-slate-300 rounded-xl p-4 text-xs text-slate-700 flex items-start gap-3">
        <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-900">Synthetic Prototype Notice:</span> This demonstration prototype operates strictly on synthetic, fictional student data (~100 students in school SCH-001). No real child names, phone numbers, or government credentials are processed or scraped.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: CSV Import Box */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <Upload className="w-4 h-4 text-teal-700" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Import Assessment / Student CSV
            </h2>
          </div>

          {uploadError && (
            <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-800">
              {uploadError}
            </div>
          )}

          {uploadResult && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 text-xs space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-slate-900">
                <FileCheck2 className="w-4 h-4 text-teal-600" />
                <span>Import Summary: {uploadResult.file_name}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1 font-mono text-[11px]">
                <div className="bg-white p-1.5 rounded border border-slate-200">
                  <span className="block text-slate-400 text-[10px]">INSERTED</span>
                  <strong className="text-teal-700">{uploadResult.inserted_rows}</strong>
                </div>
                <div className="bg-white p-1.5 rounded border border-slate-200">
                  <span className="block text-slate-400 text-[10px]">DUPLICATES</span>
                  <strong className="text-amber-700">{uploadResult.duplicate_rows}</strong>
                </div>
                <div className="bg-white p-1.5 rounded border border-slate-200">
                  <span className="block text-slate-400 text-[10px]">REJECTED</span>
                  <strong className="text-rose-700">{uploadResult.rejected_rows}</strong>
                </div>
              </div>
              {uploadResult.issues.length > 0 && (
                <div className="pt-2 text-[11px] text-rose-700">
                  <p className="font-semibold mb-1">Validation Warnings / Errors ({uploadResult.issues.length}):</p>
                  <ul className="list-disc pl-4 space-y-0.5 max-h-28 overflow-y-auto">
                    {uploadResult.issues.slice(0, 5).map((iss, i) => (
                      <li key={i}>
                        Row {iss.row_id}: [{iss.issue_code}] {iss.issue_description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleUploadSubmit} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-600 font-semibold mb-1">Entity Schema</label>
              <select
                value={fileType}
                onChange={(e) => setFileType(e.target.value)}
                className="w-full px-2.5 py-1.5 border border-slate-300 rounded-md bg-white focus:ring-1 focus:ring-teal-500 focus:outline-none"
              >
                <option value="auto">Auto-detect from headers</option>
                <option value="students">Students Roster (students.csv)</option>
                <option value="assessments">Assessment Checks (assessments.csv)</option>
                <option value="attendance">Attendance Records (attendance.csv)</option>
                <option value="interventions">Interventions Log (interventions.csv)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Select CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer"
              />
            </div>

            <div className="bg-slate-50 rounded p-2.5 text-[11px] text-slate-500 leading-relaxed">
              • Raw upload copies are preserved in <code>data/raw/</code> for auditing.
              <br />
              • Duplicate rows are skipped without overwriting existing data.
            </div>

            <button
              type="submit"
              disabled={uploading || !file}
              className="w-full py-2 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-semibold rounded-lg shadow-xs transition"
            >
              {uploading ? 'Validating & Uploading...' : 'Upload & Validate CSV'}
            </button>
          </form>
        </div>

        {/* Right Column: Validation & Quality Audit Log */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-700" />
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Ingestion & Quality Audit Logs ({logs.length})
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value)}
                className="px-2 py-1 bg-white border border-slate-300 rounded text-xs text-slate-700 focus:outline-none"
              >
                <option value="">All Statuses</option>
                <option value="warning">Warnings Only</option>
                <option value="rejected">Rejections Only</option>
              </select>
              <button
                onClick={fetchLogs}
                className="p-1 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100"
                title="Refresh logs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {loadingLogs ? (
            <LoadingState message="Fetching validation log entries..." />
          ) : logError ? (
            <ErrorState message={logError} onRetry={fetchLogs} />
          ) : logs.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-6 text-center">
              No validation issues found. Data ingestion health is clean.
            </p>
          ) : (
            <div className="overflow-x-auto max-h-[500px]">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider text-[10px] sticky top-0">
                  <tr>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">File</th>
                    <th className="px-3 py-2">Row</th>
                    <th className="px-3 py-2">Issue Code</th>
                    <th className="px-3 py-2">Description</th>
                    <th className="px-3 py-2">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            log.validation_status === 'rejected'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {log.validation_status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-slate-600">{log.file_name}</td>
                      <td className="px-3 py-2 text-slate-500">{log.row_id}</td>
                      <td className="px-3 py-2 font-semibold text-slate-800">{log.issue_code}</td>
                      <td className="px-3 py-2 text-slate-600 font-sans">{log.issue_description}</td>
                      <td className="px-3 py-2 text-slate-400 text-[10px]">
                        {log.created_at.replace('T', ' ').slice(0, 19)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
