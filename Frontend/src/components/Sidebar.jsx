import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertOctagon,
  FileSpreadsheet,
  BarChart3,
  FlaskConical,
  ShieldCheck
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/payments', label: 'Failed Payments', icon: AlertOctagon },
  { path: '/audit', label: 'Audit Trail', icon: FileSpreadsheet },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/evaluation', label: 'Batch Evaluation', icon: FlaskConical },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-61px)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Recovery Dashboard
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="bg-slate-800/50 rounded-xl p-3.5 border border-slate-700/60 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          <span>Guardrail Status</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          AI recommendation bounded by deterministic policy checks before action execution.
        </p>
      </div>
    </aside>
  );
}
