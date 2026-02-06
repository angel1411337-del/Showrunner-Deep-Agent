import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, FileText, Activity, Search, Settings, Play, GitMerge, ChevronDown, Star, Plus } from 'lucide-react';
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

  // Environment State
  const [activeEnvId, setActiveEnvId] = useState('default');
  const [availableEnvs, setAvailableEnvs] = useState([]);

  // Environment Name State (Display only now)
  const [envName, setEnvName] = useState('Showrunner Project');
  const [isEditingName, setIsEditingName] = useState(false); // Reuse for dropdown toggle

  const refreshEnvs = () => {
    fetch('http://localhost:8000/api/environments')
      .then(res => res.json())
      .then(data => setAvailableEnvs(data))
      .catch(console.error);
  };

  const handleSwitchEnv = (envId) => {
    setActiveEnvId(envId);
    setIsEditingName(false);
    // Data refresh happens in useEffect when activeEnvId changes
  };

  const handleSetDefault = async (envId) => {
    try {
      await fetch('http://localhost:8000/api/environments/default', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ environment_id: envId })
      });
      refreshEnvs();
    } catch (e) {
      console.error(e);
    }
  };

  const [isCreatingEnv, setIsCreatingEnv] = useState(false);
  const [newEnvName, setNewEnvName] = useState('');

  const handleCreateEnv = async () => {
    if (!newEnvName.trim()) return;
    try {
      const res = await fetch('http://localhost:8000/api/environments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newEnvName })
      });
      if (res.ok) {
        const data = await res.json();
        await refreshEnvs();
        setActiveEnvId(data.id);
        setIsCreatingEnv(false);
        setNewEnvName('');
        setIsEditingName(false); // Close dropdown
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchData = (envId) => {
    // If we have an explicit ID we use it, otherwise let backend decide based on default
    const query = envId && envId !== 'default' ? `?environment_id=${envId}` : '';

    Promise.all([
      fetch(`http://localhost:8000/api/wiki/events${query}`).then(res => res.json().catch(() => [])),
      fetch(`http://localhost:8000/api/wiki/relationships${query}`).then(res => res.json().catch(() => [])),
      fetch(`http://localhost:8000/api/obligations${query}`).then(res => res.json().catch(() => [])),
      fetch(`http://localhost:8000/api/status${query}`).then(res => res.json().catch(() => null))
    ]).then(([evData, relData, oblData, statusData]) => {
      setEvents(evData);
      setRelationships(relData);
      setObligations(oblData);

      if (statusData) {
        setEnvName(statusData.environment_name);
        if (statusData.active_environment_id) {
          // Only update if not already set or it was initial load
          // This syncs the UI with what the backend says is active
          if (!envId) setActiveEnvId(statusData.active_environment_id);
        }
      }
    });

    refreshEnvs();
  };

  useEffect(() => {
    // Initial load without ID -> Backend chooses default
    fetchData(null);
  }, []);

  useEffect(() => {
    if (activeEnvId) {
      fetchData(activeEnvId);
    }
  }, [activeEnvId]);

  const handleRunAgent = async () => {
    try {
      setIsRunning(true);
      setRunMessage('Starting...');
      setRunProgress(0);

      const body = activeEnvId !== 'default' ? { environment_id: activeEnvId } : {};

      const res = await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
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
      {/* Sidebar - Higher z-index for dropdowns */}
      <aside className="w-64 glass-panel rounded-2xl flex flex-col p-4 relative z-50">
        <div className="flex items-center gap-3 px-2 mb-8 mt-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center font-bold text-white">
            SR
          </div>
          <div className="flex-1 min-w-0 relative">
            <div
              className="group flex items-center gap-2 cursor-pointer"
              onClick={() => setIsEditingName(!isEditingName)}
            >
              <div className="flex flex-col">
                <span className="font-semibold text-lg tracking-tight truncate" title={envName}>
                  {envName}
                </span>
                <span className="text-xs text-slate-500 font-mono flex items-center gap-1">
                  {availableEnvs.find(e => e.id === activeEnvId)?.is_global_default && (
                    <span className="text-yellow-500/80">★</span>
                  )}
                  {activeEnvId === 'default' ? 'Root' : activeEnvId}
                </span>
              </div>
              <ChevronDown size={14} className={`text-slate-500 transition-transform ${isEditingName ? 'rotate-180' : ''}`} />
            </div>

            {isEditingName && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-[#1a1b26] border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden backdrop-blur-xl">
                <div className="p-2 border-b border-white/5">
                  <div className="flex items-center gap-2 px-2 py-1 bg-white/5 rounded-lg">
                    <Search size={14} className="text-slate-400" />
                    <input
                      type="text"
                      placeholder="Find environment..."
                      className="bg-transparent text-sm w-full outline-none text-white placeholder:text-slate-600"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>

                <div className="max-h-64 overflow-y-auto py-1">
                  {availableEnvs.map((env) => (
                    <div
                      key={env.id}
                      className={`group flex items-center justify-between px-3 py-2 mx-1 rounded-lg cursor-pointer transition-colors ${activeEnvId === env.id ? 'bg-purple-500/20 text-white' : 'hover:bg-white/5 text-slate-400'
                        }`}
                      onClick={() => handleSwitchEnv(env.id)}
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <div className={`w-2 h-2 rounded-full ${env.id === 'default' ? 'bg-blue-400' : 'bg-slate-600'}`} />
                        <span className="truncate text-sm">{env.name}</span>
                      </div>

                      {env.id !== availableEnvs.find(e => e.is_global_default)?.id && (
                        <button
                          className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-yellow-400 transition-all p-1"
                          title="Make Default"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSetDefault(env.id);
                          }}
                        >
                          <Star size={12} className="group-hover:fill-current" />
                        </button>
                      )}
                      {env.is_global_default && <Star size={12} className="text-yellow-500 fill-yellow-500" />}
                    </div>
                  ))}
                </div>

                <div className="p-2 border-t border-white/5 bg-white/2">
                  {isCreatingEnv ? (
                    <div className="flex flex-col gap-2 p-1">
                      <input
                        type="text"
                        placeholder="New environment name..."
                        className="bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white outline-none focus:border-purple-500/50"
                        autoFocus
                        value={newEnvName}
                        onChange={(e) => setNewEnvName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleCreateEnv();
                          if (e.key === 'Escape') setIsCreatingEnv(false);
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="flex items-center gap-1">
                        <button
                          className="flex-1 bg-purple-600 hover:bg-purple-500 text-white text-[10px] uppercase font-bold py-1 rounded-md transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateEnv();
                          }}
                        >
                          Create
                        </button>
                        <button
                          className="flex-1 bg-white/5 hover:bg-white/10 text-slate-400 text-[10px] uppercase font-bold py-1 rounded-md transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsCreatingEnv(false);
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      className="w-full flex items-center justify-center gap-2 text-xs py-1.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-all"
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsCreatingEnv(true);
                      }}
                    >
                      <Plus size={12} />
                      <span>Create Environment</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
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
              {activeTab === 'dashboard' && <Dashboard environmentId={activeEnvId} />}
              {activeTab === 'dossier' && <Dossier filterResolved={true} environmentId={activeEnvId} />}
              {activeTab === 'planning' && <PlanningOutputs environmentId={activeEnvId} />}
              {activeTab === 'entities' && <Entities events={events} relationships={relationships} obligations={obligations} />}
              {activeTab === 'all-obligations' && <Dossier filterResolved={false} environmentId={activeEnvId} />}
            </Motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
