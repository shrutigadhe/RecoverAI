import React, { useState } from 'react';
import { FlaskConical, Play, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';
import { runBatchEvaluation } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function BatchEvaluation() {
  const [running, setRunning] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  const handleRunEvaluation = async () => {
    setRunning(true);
    try {
      const data = await runBatchEvaluation();
      setEvalResult(data);
    } catch (err) {
      alert(`Batch evaluation error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-indigo-400" />
            <span>Synthetic Dataset Batch Evaluation</span>
          </h2>
          <p className="text-sm text-slate-400">
            Run the entire closed-loop recovery agent workflow over 100 synthetic payment failure records.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={running}
          className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white px-5 py-2.5 rounded-lg text-sm font-semibold shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition-all"
        >
          <Play className={`w-4 h-4 fill-current ${running ? 'animate-spin' : ''}`} />
          <span>{running ? 'Evaluating 100 Cases...' : 'Run Batch Evaluation (100 Cases)'}</span>
        </button>
      </div>

      {/* Dynamic Results Summary Cards */}
      {evalResult && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-4 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Total Revenue At Risk</span>
            <p className="text-2xl font-bold text-rose-400">
              ₹{evalResult.total_revenue_at_risk?.toLocaleString('en-IN')}
            </p>
            <span className="text-xs text-slate-500">{evalResult.total_cases} synthetic test cases</span>
          </div>

          <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-4 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Recovered Revenue</span>
            <p className="text-2xl font-bold text-emerald-400">
              ₹{evalResult.total_recovered_revenue?.toLocaleString('en-IN')}
            </p>
            <span className="text-xs text-slate-500">
              {evalResult.successful_recoveries} successful recoveries
            </span>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Recovery Rate</span>
            <p className="text-2xl font-bold text-indigo-400">
              {evalResult.recovery_rate_percentage}%
            </p>
            <span className="text-xs text-slate-500">
              {evalResult.recovery_attempts} recovery attempts
            </span>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Escalation & Rejection</span>
            <p className="text-2xl font-bold text-amber-400">
              {evalResult.escalation_rate_percentage}%
            </p>
            <span className="text-xs text-slate-500">
              Policy Rejection Rate: {evalResult.policy_rejection_rate_percentage}%
            </span>
          </div>
        </div>
      )}

      {/* Results Table */}
      {evalResult && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100">Batch Evaluation Cases Result</h3>
            <span className="text-xs text-slate-400 font-mono">100 / 100 Processed</span>
          </div>

          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/80 text-xs uppercase text-slate-400 font-semibold sticky top-0 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Payment ID</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Failure Reason</th>
                  <th className="py-3 px-4">Diagnosis</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Policy</th>
                  <th className="py-3 px-4">Final Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {evalResult.cases.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-4 text-indigo-300">{c.payment_id}</td>
                    <td className="py-2.5 px-4 font-bold text-slate-200">₹{c.amount}</td>
                    <td className="py-2.5 px-4 font-sans text-slate-400 max-w-xs truncate">{c.failure_reason}</td>
                    <td className="py-2.5 px-4 font-sans text-indigo-300 max-w-xs truncate">{c.diagnosis}</td>
                    <td className="py-2.5 px-4 font-bold text-indigo-400">{c.recommended_action}</td>
                    <td className="py-2.5 px-4 font-sans">
                      {c.policy_approved ? (
                        <span className="text-emerald-400 font-semibold">APPROVED</span>
                      ) : (
                        <span className="text-rose-400 font-semibold">REJECTED</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-sans">
                      <StatusBadge status={c.final_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
