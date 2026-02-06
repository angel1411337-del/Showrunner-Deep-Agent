import React, { useEffect, useState } from 'react';
import { CheckCircle2, Circle, AlertOctagon, HelpCircle } from 'lucide-react';

const CATEGORY_STYLES = {
    plot_thread: { color: 'text-blue-400', bg: 'bg-blue-500/10', label: 'Plot Thread' },
    chekhov_gun: { color: 'text-amber-400', bg: 'bg-amber-500/10', label: 'Chekhov Gun' },
    prophecy_vision: { color: 'text-purple-400', bg: 'bg-purple-500/10', label: 'Prophecy' },
    mystery: { color: 'text-pink-400', bg: 'bg-pink-500/10', label: 'Mystery' },
};


function EvidenceChip({ id }) {
    const [text, setText] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);

    const handleMouseEnter = () => {
        if (text || loading || error) return;
        setLoading(true);
        fetch(`http://localhost:8000/api/passages/${id}`)
            .then(res => {
                if (!res.ok) throw new Error('Not found');
                return res.json();
            })
            .then(data => {
                setText(data.text);
                setLoading(false);
            })
            .catch(() => {
                setError(true);
                setLoading(false);
            });
    };

    return (
        <div className="relative group/chip" onMouseEnter={handleMouseEnter}>
            <span className="px-2 py-1 rounded text-[10px] font-mono bg-white/5 text-slate-400 border border-white/5 truncate max-w-[150px] cursor-help hover:bg-white/10 hover:text-white transition-colors block">
                {id}
            </span>

            {/* Tooltip */}
            <div className="absolute bottom-full left-0 mb-2 w-64 bg-slate-900/90 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-xl opacity-0 group-hover/chip:opacity-100 transition-opacity pointer-events-none z-50">
                {loading && <span className="text-xs text-slate-400">Loading passage...</span>}
                {error && <span className="text-xs text-red-400">Evidence missing in canon.</span>}
                {text && (
                    <p className="text-xs text-slate-200 italic leading-relaxed">
                        "{text.slice(0, 150)}{text.length > 150 ? '...' : ''}"
                    </p>
                )}
            </div>
        </div>
    );
}

export function Dossier({ filterResolved = false, environmentId }) {
    const [obligations, setObligations] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const query = environmentId && environmentId !== 'default' ? `?environment_id=${environmentId}` : '';
        setLoading(true);
        fetch(`http://localhost:8000/api/obligations${query}`)
            .then(res => res.json())
            .then(data => {
                setObligations(data);
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, [environmentId]);

    if (loading) return <div className="p-6 text-slate-400">Decrypting dossier...</div>;

    const filtered = filterResolved
        ? obligations.filter(o => !o.is_resolved)
        : obligations;

    return (
        <div className="space-y-4 h-full overflow-y-auto pr-2 custom-scrollbar pb-20">
            {filtered.map((item) => {
                const style = CATEGORY_STYLES[item.category] || CATEGORY_STYLES.plot_thread;

                return (
                    <div key={item.obligation_id} className="glass-panel p-5 rounded-xl flex gap-5 group hover:bg-white/10 transition-all">
                        <div className="flex flex-col items-center gap-2 pt-1">
                            <div className={`p-2 rounded-lg ${style.bg} ${style.color}`}>
                                <AlertOctagon size={20} />
                            </div>
                            <div className="h-full w-px bg-white/5 group-hover:bg-white/10" />
                        </div>

                        <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs font-bold uppercase tracking-wider ${style.color}`}>
                                            {style.label}
                                        </span>
                                        <span className="text-slate-600 text-xs">•</span>
                                        <span className="text-slate-500 text-xs font-mono">{item.obligation_id}</span>
                                    </div>
                                    <h3 className="text-lg font-medium text-slate-100 leading-tight">
                                        {item.description}
                                    </h3>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-black/20 px-2 py-1 rounded">
                                        <span>CONF:</span>
                                        <span className={item.confidence > 0.8 ? "text-emerald-400" : "text-amber-400"}>
                                            {(item.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Evidence / Context */}
                            {item.evidence_anchor_ids && item.evidence_anchor_ids.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-3">
                                    {item.evidence_anchor_ids.map(id => (
                                        <EvidenceChip key={id} id={id} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
