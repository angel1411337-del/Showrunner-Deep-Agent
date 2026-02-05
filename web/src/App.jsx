import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, FileText, Activity, Search, Settings, Play, GitMerge } from 'lucide-react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { Dashboard } from './components/Dashboard';
import { Entities } from './components/Entities';
import { Dossier } from './components/Dossier';
import { PlanningOutputs } from './components/PlanningOutputs';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [events, setEvents] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [obligations, setObligations] = useState([]);

  // Run Agent State
  const [isRunning, setIsRunning] = useState(false);
  const [runMessage, setRunMessage] = useState('');
  const [runProgress, setRunProgress] = useState(0);

  const fetchData = () => {
    Promise.all([
      fetch('http://localhost:8000/api/wiki/events').then(res => res.json().catch(() => [])),
      fetch('http://localhost:8000/api/wiki/relationships').then(res => res.json().catch(() => [])),
      fetch('http://localhost:8000/api/obligations').then(res => res.json().catch(() => []))
    ]).then(([evData, relData, oblData]) => {
      setEvents(evData);
      setRelationships(relData);
      setObligations(oblData);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunAgent = async () => {
    try {
      setIsRunning(true);
      setRunMessage('Starting...');
      setRunProgress(0);

      const res = await fetch('http://localhost:8000/api/run', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to start run');

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch('http://localhost:8000/api/run/status');
          const status = await statusRes.json();

          setRunMessage(status.message);
          setRunProgress(status.progress);

          if (!status.is_running) {
            clearInterval(pollInterval);
            setIsRunning(false);
            if (!status.error) {
              fetchData(); // Refresh data on success
            }
          }
        } catch (e) {
          console.error('Poll failed', e);
        }
      }, 1000);

    } catch (e) {
      console.error(e);
      setIsRunning(false);
      setRunMessage('Error starting agent');
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'dossier', label: 'Dossier', icon: FileText },
    { id: 'planning', label: 'Planning Outputs', icon: GitMerge },
    { id: 'entities', label: 'Entities', icon: Users },
    { id: 'all-obligations', label: 'All Obligations', icon: Activity },
  ];

  return (
    <div className="flex h-screen w-screen p-4 gap-4">
      {/* Sidebar */}
      <aside className="w-64 glass-panel rounded-2xl flex flex-col p-4">
        <div className="flex items-center gap-3 px-2 mb-8 mt-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center font-bold text-white">
            SR
          </div>
          <span className="font-semibold text-lg tracking-tight">Showrunner</span>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${activeTab === item.id
                ? 'bg-white/10 text-white shadow-lg shadow-purple-500/10 border border-white/10'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
            >
              <item.icon size={18} />
              <span className="text-sm font-medium">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="pt-4 border-t border-white/5 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-all">
            <Settings size={18} />
            <span className="text-sm font-medium">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 gap-4">
        {/* Top Header */}
        <header className="h-16 glass-panel rounded-2xl flex items-center justify-between px-6">
          <h1 className="text-xl font-semibold capitalize bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            {activeTab.replace('_', ' ')}
          </h1>

          <div className="flex items-center gap-4">
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-purple-400 transition-colors" size={16} />
              <input
                type="text"
                placeholder="Search corpus..."
                className="bg-black/20 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 w-64 transition-all"
              />
            </div>

            {isRunning && (
              <div className="flex flex-col items-end mr-2">
                <span className="text-xs text-slate-300 font-mono">{runMessage}</span>
                <div className="w-32 h-1 bg-white/10 rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full bg-purple-500 transition-all duration-300"
                    style={{ width: `${runProgress * 100}%` }}
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleRunAgent}
              disabled={isRunning}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium shadow-lg transition-all active:scale-95 ${isRunning
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-purple-500/20'
                }`}
            >
              <Play size={16} fill="currentColor" className={isRunning ? "animate-pulse" : ""} />
              <span>{isRunning ? 'Running...' : 'Run Agent'}</span>
            </button>
          </div>
        </header>

        {/* Content View */}
        <div className="flex-1 glass-panel rounded-2xl p-6 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <Motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'dossier' && <Dossier filterResolved={true} />}
              {activeTab === 'planning' && <PlanningOutputs />}
              {activeTab === 'entities' && <Entities events={events} relationships={relationships} obligations={obligations} />}
              {activeTab === 'all-obligations' && <Dossier filterResolved={false} />}
            </Motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
