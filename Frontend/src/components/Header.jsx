import React from 'react';
import { ShieldCheck, Zap, AlertTriangle, LogOut, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-slate-900/80 backdrop-blur border-b border-slate-800 sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="bg-indigo-600/20 p-2 rounded-lg border border-indigo-500/30">
          <Zap className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            RecoverAI
          </h1>
          <p className="text-xs text-slate-400">Autonomous AI Revenue Recovery Agent</p>
        </div>
      </div>

      {/* DEMO / TEST MODE BANNER */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 rounded-full text-xs font-semibold text-amber-300">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>DEMO / TEST MODE</span>
          <span className="hidden md:inline font-normal text-amber-400/80">
            • Razorpay Sandbox & Bounded Policy Guardrails Active
          </span>
        </div>

        {user && (
          <div className="flex items-center gap-3 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-full text-xs text-slate-300">
            <div className="flex items-center gap-1.5 font-medium text-slate-200">
              <User className="w-3.5 h-3.5 text-indigo-400" />
              <span>{user.name}</span>
            </div>
            <button
              onClick={logout}
              className="text-slate-400 hover:text-rose-400 transition-colors p-0.5"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
