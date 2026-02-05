import React, { useEffect, useMemo, useState } from 'react';
import { FileText, Table, GitBranch } from 'lucide-react';

const OUTLINE_URL = 'http://localhost:8000/api/exports/outline';
const REVEALS_URL = 'http://localhost:8000/api/exports/reveals';
const TWISTS_URL = 'http://localhost:8000/api/exports/twists';

function parseCsvLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  values.push(current.trim());
  return values;
}

function parseCsv(text) {
  const normalized = text.trim();
  if (!normalized) {
    return { headers: [], rows: [] };
  }

  const lines = normalized.split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) {
    return { headers: [], rows: [] };
  }

  const headers = parseCsvLine(lines[0]);
  const rows = lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return headers.map((header, index) => ({
      header,
      value: values[index] ?? '',
    }));
  });

  return { headers, rows };
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}`);
  }
  return response.text();
}

function SectionCard({ icon: Icon, title, children }) {
  return (
    <section className="glass-panel rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
          {React.createElement(Icon, { size: 18, className: 'text-slate-200' })}
        </div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export function PlanningOutputs() {
  const [outline, setOutline] = useState('');
  const [revealsCsv, setRevealsCsv] = useState('');
  const [twists, setTwists] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadPlanningExports() {
      try {
        const [outlineText, revealsText, twistsText] = await Promise.all([
          fetchText(OUTLINE_URL),
          fetchText(REVEALS_URL),
          fetchText(TWISTS_URL),
        ]);
        setOutline(outlineText);
        setRevealsCsv(revealsText);
        setTwists(twistsText);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error loading planning exports.';
        setError(message);
      } finally {
        setLoading(false);
      }
    }

    loadPlanningExports();
  }, []);

  const reveals = useMemo(() => parseCsv(revealsCsv), [revealsCsv]);

  if (loading) {
    return <div className="p-6 text-slate-400">Loading planning outputs...</div>;
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar pr-2 space-y-6 pb-20">
      {error && (
        <div className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {error}
        </div>
      )}

      <SectionCard icon={FileText} title="Master Outline">
        {outline.trim() ? (
          <pre className="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap font-mono bg-black/20 border border-white/10 rounded-xl p-4">
            {outline}
          </pre>
        ) : (
          <p className="text-slate-400">No outline export found.</p>
        )}
      </SectionCard>

      <SectionCard icon={Table} title="Reveal Ledger">
        {reveals.rows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm border border-white/10 rounded-xl overflow-hidden">
              <thead className="bg-white/5">
                <tr>
                  {reveals.headers.map((header) => (
                    <th key={header} className="text-left px-3 py-2 text-slate-200 font-medium border-b border-white/10">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {reveals.rows.map((row, index) => (
                  <tr key={index} className="border-b border-white/5 last:border-b-0">
                    {row.map((cell) => (
                      <td key={`${index}-${cell.header}`} className="px-3 py-2 text-slate-300">
                        {cell.value}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-slate-400">No reveal ledger export found.</p>
        )}
      </SectionCard>

      <SectionCard icon={GitBranch} title="Twist Bank">
        {twists.trim() ? (
          <pre className="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap font-mono bg-black/20 border border-white/10 rounded-xl p-4">
            {twists}
          </pre>
        ) : (
          <p className="text-slate-400">No twist bank export found.</p>
        )}
      </SectionCard>
    </div>
  );
}
