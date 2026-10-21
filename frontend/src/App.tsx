import React, { useState, useEffect } from 'react';
import { Navbar, TabKey } from './components/Navbar';
import { OverviewScreen } from './screens/OverviewScreen';
import { StudentsScreen } from './screens/StudentsScreen';
import { StudentProfileScreen } from './screens/StudentProfileScreen';
import { InterventionsScreen } from './screens/InterventionsScreen';
import { GovernanceScreen } from './screens/GovernanceScreen';
import { api } from './services/api';
import { HealthResponse } from './types/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<TabKey>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);

  // Drilldown states
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [presetGrade, setPresetGrade] = useState<number | undefined>(undefined);
  const [presetStatus, setPresetStatus] = useState<string | undefined>(undefined);
  const [interventionStudentId, setInterventionStudentId] = useState<string>('');
  const [interventionSkillCode, setInterventionSkillCode] = useState<string>('word_reading');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
      } catch {
        setHealth(null);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigateToStudents = (grade?: number, statusFilter?: string) => {
    setPresetGrade(grade);
    setPresetStatus(statusFilter);
    setSelectedStudentId(null);
    setCurrentTab('students');
  };

  const handleSelectStudent = (studentId: string) => {
    setSelectedStudentId(studentId);
  };

  const handleRecordIntervention = (studentId: string, skillCode: string) => {
    setInterventionStudentId(studentId);
    setInterventionSkillCode(skillCode);
    setCurrentTab('interventions');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setSelectedStudentId(null);
          setCurrentTab(tab);
        }}
        health={health}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentTab === 'overview' && (
          <OverviewScreen
            onNavigateToStudents={handleNavigateToStudents}
            onNavigateToInterventions={() => {
              setInterventionStudentId('');
              setCurrentTab('interventions');
            }}
            onNavigateToGovernance={() => setCurrentTab('governance')}
          />
        )}

        {currentTab === 'students' && !selectedStudentId && (
          <StudentsScreen
            initialGrade={presetGrade}
            initialStatus={presetStatus}
            onSelectStudent={handleSelectStudent}
          />
        )}

        {currentTab === 'students' && selectedStudentId && (
          <StudentProfileScreen
            studentId={selectedStudentId}
            onBack={() => setSelectedStudentId(null)}
            onRecordIntervention={handleRecordIntervention}
          />
        )}

        {currentTab === 'interventions' && (
          <InterventionsScreen
            presetStudentId={interventionStudentId}
            presetSkillCode={interventionSkillCode}
          />
        )}

        {currentTab === 'governance' && <GovernanceScreen />}
      </main>

      {/* Footer & Governance Disclaimer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div>
            <p className="font-semibold text-slate-700">
              ShikshaSignal — Theme 2: Foundational Learning Outcomes
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Techfest IIT Bombay Challenge 2026–27 Prototype • Configured for School SCH-001 (Grades 1–3)
            </p>
          </div>
          <p className="text-[11px] text-slate-400 max-w-md">
            Decision-support aid for teachers. All thresholds are synthetic demonstration assumptions. Does not replace statutory government systems (UDISE+, DIKSHA, PARAKH).
          </p>
        </div>
      </footer>
    </div>
  );
};
