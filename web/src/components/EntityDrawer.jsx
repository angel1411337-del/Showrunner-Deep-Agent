
import React from 'react';
import { X, Calendar, Link as LinkIcon, AlertTriangle } from 'lucide-react';
import { motion as Motion, AnimatePresence } from 'framer-motion';

export function EntityDrawer({ entity, isOpen, onClose, events = [], relationships = [], obligations = [] }) {
    if (!entity) return null;

    // Filter context for this entity
    const entityEvents = events.filter(e => e.participant_entity_ids.includes(entity.entity_id));
    const entityRels = relationships.filter(r =>
        r.source_entity_id === entity.entity_id || r.target_entity_id === entity.entity_id
    );
    const entityObligations = obligations.filter(o =>
        (o.related_entity_ids || []).includes(entity.entity_id)
    );

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <Motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
                    />
                    <Motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-slate-900 border-l border-white/10 shadow-2xl z-50 overflow-y-auto custom-scrollbar"
                    >
                        <div className="p-6 space-y-8">
                            {/* Header */}
                            <div className="flex items-start justify-between">
                                <div>
                                    <h2 className="text-2xl font-bold text-white">{entity.canonical_name}</h2>
                                    <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">{entity.entity_id}</span>
                                </div>
                                <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Relationships */}
                            <section>
                                <h3 className="flex items-center gap-2 text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                                    <LinkIcon size={14} /> Relationships
                                </h3>
                                {entityRels.length === 0 ? (
                                    <p className="text-sm text-slate-600 italic">No known relationships.</p>
                                ) : (
                                    <div className="space-y-3">
                                        {entityRels.map(rel => {
                                            const isSource = rel.source_entity_id === entity.entity_id;
                                            const otherId = isSource ? rel.target_entity_id : rel.source_entity_id;
                                            return (
                                                <div key={rel.relationship_id} className="bg-white/5 p-3 rounded-lg border border-white/5">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-xs font-mono text-purple-400 uppercase">{rel.relation_type}</span>
                                                        <span className="text-xs text-slate-500">{otherId}</span>
                                                    </div>
                                                    <p className="text-sm text-slate-300">{rel.description}</p>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </section>

                            {/* Events */}
                            <section>
                                <h3 className="flex items-center gap-2 text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                                    <Calendar size={14} /> Timeline
                                </h3>
                                {entityEvents.length === 0 ? (
                                    <p className="text-sm text-slate-600 italic">No events recorded.</p>
                                ) : (
                                    <div className="space-y-4 relative pl-4 border-l border-white/10">
                                        {entityEvents.map(evt => (
                                            <div key={evt.event_id} className="relative">
                                                <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-slate-700 border border-slate-900 ring-2 ring-slate-900" />
                                                <div className="mb-1">
                                                    <span className="text-xs font-mono text-slate-500">{evt.story_time?.time_label || 'Unknown Time'}</span>
                                                </div>
                                                <h4 className="text-slate-200 font-medium leading-tight mb-1">{evt.title}</h4>
                                                <p className="text-xs text-slate-400 leading-relaxed">{evt.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>

                            {/* Obligations */}
                            <section>
                                <h3 className="flex items-center gap-2 text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                                    <AlertTriangle size={14} /> Related Threads
                                </h3>
                                {entityObligations.length === 0 ? (
                                    <p className="text-sm text-slate-600 italic">No active obligations.</p>
                                ) : (
                                    <div className="space-y-2">
                                        {entityObligations.map(obl => (
                                            <div key={obl.obligation_id} className="flex items-start gap-3 bg-red-500/5 p-3 rounded-lg border border-red-500/10">
                                                <div className={`w-2 h-2 rounded-full mt-1.5 ${obl.is_resolved ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                                <div>
                                                    <p className="text-sm text-slate-200">{obl.description}</p>
                                                    <span className="text-[10px] font-mono text-slate-500">{obl.obligation_id}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        </div>
                    </Motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
