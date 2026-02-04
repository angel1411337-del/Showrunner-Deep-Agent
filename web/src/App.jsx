import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, FileText, Activity, Search, Settings, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dashboard } from './components/Dashboard';
import { Entities } from './components/Entities';
import { Dossier } from './components/Dossier';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [events, setEvents] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [obligations, setObligations] = useState([]);

  useEffect(() => {
    // Global pre-fetch for wiki integration
    Promise.all([
      fetch('http://localhost:8000/api/wiki/events').then(res => res.json().catch(() => [])),
      fetch('http://localhost:8000/api/wiki/relationships').then(res => res.json().catch(() => [])),
      fetch('http://localhost:8000/api/obligations').then(res => res.json().catch(() => []))
    ]).then(([evData, relData, oblData]) => {
      setEvents(evData);
      setRelationships(relData);
      setObligations(oblData);
    });
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'dossier', label: 'Dossier', icon: FileText },
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

            <button className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-purple-500/20 transition-all active:scale-95">
              <Play size={16} fill="currentColor" />
              <span>Run Agent</span>
            </button>
          </div>
        </header>

        {/* Content View */}
        <div className="flex-1 glass-panel rounded-2xl p-6 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'dossier' && <Dossier filterResolved={true} />}
              {activeTab === 'entities' && <Entities events={events} relationships={relationships} obligations={obligations} />}
              {activeTab === 'all-obligations' && <Dossier filterResolved={false} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
