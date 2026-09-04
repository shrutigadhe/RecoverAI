import React from 'react';

const statusConfig = {
  RECOVERED: { label: 'RECOVERED', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  ACTION_EXECUTED: { label: 'RECOVERED', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  RECOVERING: { label: 'RECOVERING', bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/20' },
  ANALYZING: { label: 'ANALYZING', bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  ACTION_PROPOSED: { label: 'PROPOSED', bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
  ESCALATED: { label: 'ESCALATED', bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  BLOCKED: { label: 'BLOCKED', bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
  FAILED: { label: 'FAILED', bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
  STOPPED: { label: 'STOPPED', bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20' },
  QUEUED: { label: 'QUEUED', bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20' },
};

export default function StatusBadge({ status }) {
  const cfg = statusConfig[status] || {
    label: status || 'UNKNOWN',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.text} ${cfg.border}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5"></span>
      {cfg.label}
    </span>
  );
}
