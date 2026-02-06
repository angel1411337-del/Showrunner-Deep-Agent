import React, { useEffect, useState } from 'react';
import { Activity, Users, AlertCircle, CheckCircle } from 'lucide-react';

export function Dashboard({ environmentId }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const query = environmentId && environmentId !== 'default' ? `?environment_id=${environmentId}` : '';
        setLoading(true);
        fetch(`http://localhost:8000/api/stats${query}`)
            .then(res => res.json())
            .then(data => {
                setStats(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch stats", err);
                setLoading(false);
            });
    }, [environmentId]);

    if (loading) return <div className="p-6 text-slate-400">Loading mission data...</div>;
    if (!stats) return <div className="p-6 text-red-400">System Offline: Cannot connect to Showrunner API</div>;

    const cards = [
        { label: 'Total Obligations', value: stats.total_obligations, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10' },
        { label: 'Open Threads', value: stats.open_threads, icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
        { label: 'Key Entities', value: stats.key_entities, icon: Users, color: 'text-purple-400', bg: 'bg-purple-500/10' },
        { label: 'High Confidence', value: stats.high_confidence_events, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards.map((card, i) => (
                <div key={i} className="glass-panel p-6 rounded-2xl flex items-center gap-4 hover:bg-white/10 transition-colors cursor-default">
                    <div className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center`}>
                        <card.icon className={card.color} size={24} />
                    </div>
                    <div>
                        <p className="text-slate-400 text-sm font-medium">{card.label}</p>
                        <p className="text-2xl font-bold text-white">{card.value}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
