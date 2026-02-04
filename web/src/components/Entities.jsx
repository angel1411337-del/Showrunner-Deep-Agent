import React, { useEffect, useState } from 'react';
import { User, MapPin, Box, Users, Truck } from 'lucide-react';

const TYPE_ICONS = {
    person: User,
    place: MapPin,
    artifact: Box,
    group: Users,
    vehicle: Truck
};

export function Entities() {
    const [entities, setEntities] = useState([]);
    const [loading, setLoading] = useState(true);


    useEffect(() => {
        Promise.all([
            fetch('http://localhost:8000/api/entities').then(res => res.json()),
            fetch('http://localhost:8000/api/aliases').then(res => res.json())
        ]).then(([entitiesData, aliasesData]) => {
            // Map aliases to entities
            const aliasMap = {};
            aliasesData.forEach(a => {
                if (!aliasMap[a.entity_id]) aliasMap[a.entity_id] = [];
                aliasMap[a.entity_id].push(a.alias);
            });

            // Attach aliases to entities
            const enriched = entitiesData.map(e => ({
                ...e,
                aliases: aliasMap[e.entity_id] || []
            }));

            setEntities(enriched);
            setLoading(false);
        }).catch(err => console.error(err));
    }, []);

    if (loading) return <div className="p-6 text-slate-400">Scanning knowledge base...</div>;

    return (
        <div className="space-y-4 h-full overflow-y-auto pr-2 custom-scrollbar">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {entities.map((entity) => {
                    const Icon = TYPE_ICONS[entity.entity_type] || User;
                    return (
                        <div key={entity.entity_id} className="glass-panel p-4 rounded-xl space-y-3 hover:bg-white/10 transition-all border border-white/5 hover:border-white/20 group">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                                        <Icon size={20} className="text-slate-300 group-hover:text-white" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-100">{entity.canonical_name}</h3>
                                        <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">{entity.entity_type}</span>
                                    </div>
                                </div>
                                {entity.is_important && (
                                    <span className="bg-purple-500/20 text-purple-300 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wide">Key</span>
                                )}
                            </div>

                            {/* Aliases */}
                            {entity.aliases && entity.aliases.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {entity.aliases.slice(0, 3).map(alias => (
                                        <span key={alias} className="text-[10px] text-slate-400 bg-white/5 px-1.5 py-0.5 rounded border border-white/5">
                                            {alias}
                                        </span>
                                    ))}
                                    {entity.aliases.length > 3 && (
                                        <span className="text-[10px] text-slate-500 px-1">+{entity.aliases.length - 3}</span>
                                    )}
                                </div>
                            )}

                            <p className="text-sm text-slate-400 line-clamp-2">
                                {entity.description || "No description available in dossier."}
                            </p>

                            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
                                <span>Mentions: {entity.mention_count}</span>
                                {entity.first_seen_passage && (
                                    <span className="font-mono">Ref: {entity.first_seen_passage.split(':')[0]}</span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
