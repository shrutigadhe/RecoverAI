import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Play, RefreshCw, AlertOctagon } from 'lucide-react';
import { fetchRecoveryCases, runRecoveryWorkflow } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function FailedPayments() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [runningCaseId, setRunningCaseId] = useState(null);

  const loadCases = async () => {
    setLoading(true);
    try {
      const data = await fetchRecoveryCases();
      setCases(data);
    } catch (err) {
      console.error('Error fetching recovery cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleRunWorkflow = async (caseId) => {
    setRunningCaseId(caseId);
    try {
      await runRecoveryWorkflow(caseId);
      await loadCases();
    } catch (err) {
      alert(`Error running workflow: ${err.message}`);
    } finally {
      setRunningCaseId(null);
    }
  };

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.payment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.diagnosis && c.diagnosis.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="w-6 h-6 text-indigo-400" />
            <span>Failed Payments & Recovery Cases</span>
          </h2>
          <p className="text-sm text-slate-400">
            Inspect detected payment failures and trigger AI recovery workflows.
          </p>
        </div>

        <button
          onClick={loadCases}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg border border-slate-700 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by Case ID, Payment ID, or Diagnosis..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="QUEUED">QUEUED</option>
            <option value="ANALYZING">ANALYZING</option>
            <option value="RECOVERED">RECOVERED</option>
            <option value="ESCALATED">ESCALATED</option>
            <option value="STOPPED">STOPPED</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/80 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Case ID</th>
                <th className="py-3.5 px-4">Payment ID</th>
                <th className="py-3.5 px-4">Score</th>
                <th className="py-3.5 px-4">Diagnosis</th>
                <th className="py-3.5 px-4">Rec. Action</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-500">
                    Loading recovery cases...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-500">
                    No failed payment cases matching your criteria.
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-indigo-300 font-semibold">
                      {c.id.substring(0, 8)}...
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      {c.payment_id.substring(0, 8)}...
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-400">
                      {Math.round(c.recovery_score * 100)}%
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-300 max-w-xs truncate">
                      {c.diagnosis || 'Pending Diagnosis'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-indigo-400">
                      {c.recommended_action || 'PENDING'}
                    </td>
                    <td className="py-3.5 px-4 text-xs">
                      {Math.round(c.confidence * 100)}%
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleRunWorkflow(c.id)}
                        disabled={runningCaseId === c.id || c.status === 'RECOVERED'}
                        className="inline-flex items-center gap-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 px-2.5 py-1 rounded text-xs font-medium disabled:opacity-40 transition-colors"
                      >
                        <Play className={`w-3 h-3 ${runningCaseId === c.id ? 'animate-spin' : ''}`} />
                        <span>Run</span>
                      </button>
                      <Link
                        to={`/payments/${c.id}`}
                        className="text-xs text-slate-400 hover:text-slate-200 underline font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
