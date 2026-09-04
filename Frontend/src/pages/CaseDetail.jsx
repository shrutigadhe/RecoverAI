import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ShieldCheck,
  Zap,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  XCircle,
  Clock,
  Play,
  FileText
} from 'lucide-react';
import { fetchCaseDetail, runRecoveryWorkflow, approveRecoveryCase, escalateRecoveryCase } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function CaseDetail() {
  const { caseId } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionRunning, setActionRunning] = useState(false);

  const loadCase = async () => {
    setLoading(true);
    try {
      const data = await fetchCaseDetail(caseId);
      setCaseData(data);
    } catch (err) {
      console.error('Error fetching case detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [caseId]);

  const handleRunWorkflow = async () => {
    setActionRunning(true);
    try {
      await runRecoveryWorkflow(caseId);
      await loadCase();
    } catch (err) {
      alert(`Error running workflow: ${err.message}`);
    } finally {
      setActionRunning(false);
    }
  };

  const handleApprove = async () => {
    setActionRunning(true);
    try {
      await approveRecoveryCase(caseId, 'Merchant manually approved recovery retry');
      await loadCase();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setActionRunning(false);
    }
  };

  const handleEscalate = async () => {
    setActionRunning(true);
    try {
      await escalateRecoveryCase(caseId, 'Merchant manually escalated case');
      await loadCase();
    } catch (err) {
      alert(`Escalation error: ${err.message}`);
    } finally {
      setActionRunning(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading recovery case details...</div>;
  }

  if (!caseData) {
    return <div className="p-8 text-center text-rose-400">Case not found.</div>;
  }

  const { payment, customer, actions } = caseData;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back link */}
      <Link
        to="/payments"
        className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Failed Payments</span>
      </Link>

      {/* Case Overview Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-100 font-mono">Case #{caseData.id.substring(0, 8)}</h2>
            <StatusBadge status={caseData.status} />
            {payment.is_demo && (
              <span className="bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs px-2.5 py-0.5 rounded-full">
                SIMULATED DEMO EVENT
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Payment ID: <span className="font-mono text-slate-300">{payment.id}</span> • Customer:{' '}
            <span className="text-slate-200 font-medium">{customer.name} ({customer.email})</span>
          </p>
        </div>

        {/* Human in the loop actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunWorkflow}
            disabled={actionRunning || caseData.status === 'RECOVERED'}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-2 rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${actionRunning ? 'animate-spin' : ''}`} />
            <span>Run AI Recovery Workflow</span>
          </button>

          <button
            onClick={handleApprove}
            disabled={actionRunning || caseData.status === 'RECOVERED'}
            className="flex items-center gap-1.5 bg-emerald-600/20 border border-emerald-500/30 hover:bg-emerald-600/30 text-emerald-300 px-3.5 py-2 rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Merchant Approve</span>
          </button>

          <button
            onClick={handleEscalate}
            disabled={actionRunning || caseData.status === 'ESCALATED'}
            className="flex items-center gap-1.5 bg-amber-600/20 border border-amber-500/30 hover:bg-amber-600/30 text-amber-300 px-3.5 py-2 rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Escalate</span>
          </button>
        </div>
      </div>

      {/* Grid Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: AI Diagnosis & Explainability (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Explainability Card */}
          <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-indigo-500/30 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-slate-100">AI Agent Diagnosis & Explainability</h3>
              </div>
              <div className="text-xs font-mono text-indigo-300">
                Confidence: <span className="font-bold text-emerald-400">{Math.round(caseData.confidence * 100)}%</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500 font-medium uppercase">1. What Happened?</span>
                <p className="text-sm text-slate-200 font-semibold">{payment.failure_reason || 'Payment failed'}</p>
                <p className="text-xs text-slate-400">Amount: ₹{payment.amount.toLocaleString('en-IN')} via {payment.payment_method}</p>
              </div>

              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500 font-medium uppercase">2. Why Did It Happen?</span>
                <p className="text-sm text-indigo-300 font-semibold">{caseData.diagnosis || 'Analysis pending'}</p>
              </div>

              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500 font-medium uppercase">3. Recommended Action</span>
                <p className="text-sm text-emerald-400 font-bold font-mono">{caseData.recommended_action || 'N/A'}</p>
                <p className="text-xs text-slate-400">Recovery Score: {Math.round(caseData.recovery_score * 100)}%</p>
              </div>

              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500 font-medium uppercase">4. Policy Decision</span>
                <p className="text-sm text-amber-400 font-semibold">
                  {caseData.escalation_reason ? 'REJECTED / ESCALATED' : 'APPROVED'}
                </p>
                <p className="text-xs text-slate-400">{caseData.escalation_reason || 'Action complies with all policy rules'}</p>
              </div>
            </div>
          </div>

          {/* Interactive Recovery Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-400" />
              <span>Closed Loop Recovery Timeline</span>
            </h3>

            <div className="relative border-l-2 border-slate-800 ml-4 space-y-6 pl-6 py-2">
              <div className="relative">
                <span className="absolute -left-[31px] top-0 bg-indigo-600 text-white rounded-full p-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                </span>
                <h4 className="text-xs font-semibold text-slate-200">1. Payment Failure Detected</h4>
                <p className="text-xs text-slate-400">Razorpay webhook received • ₹{payment.amount} failure recorded</p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-0 bg-indigo-600 text-white rounded-full p-1">
                  <Zap className="w-3.5 h-3.5" />
                </span>
                <h4 className="text-xs font-semibold text-slate-200">2. LangGraph AI Diagnosis</h4>
                <p className="text-xs text-slate-400">{caseData.diagnosis || 'Analyzing failure cause...'}</p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-0 bg-indigo-600 text-white rounded-full p-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                </span>
                <h4 className="text-xs font-semibold text-slate-200">3. Policy Engine Evaluation</h4>
                <p className="text-xs text-slate-400">
                  {caseData.escalation_reason || 'Policy Engine checked amount limit, retry count & confidence.'}
                </p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-0 bg-emerald-600 text-white rounded-full p-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </span>
                <h4 className="text-xs font-semibold text-slate-200">4. Action & Verification Outcome</h4>
                <p className="text-xs text-emerald-400 font-semibold">
                  Status: {caseData.status} • Recovered Amount: ₹{caseData.recovered_amount}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Customer & Payment Context */}
        <div className="space-y-6">
          {/* Customer History Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
              Customer Payment History
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Name:</span>
                <span className="text-slate-200 font-medium">{customer.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Email:</span>
                <span className="text-slate-200 font-mono">{customer.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Payments:</span>
                <span className="text-slate-200 font-semibold">{customer.total_payments}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Successful:</span>
                <span className="text-emerald-400 font-semibold">{customer.successful_payments}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Failed:</span>
                <span className="text-rose-400 font-semibold">{customer.failed_payments}</span>
              </div>
            </div>
          </div>

          {/* Action Log Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
              Executed Actions Log
            </h3>
            <div className="space-y-2 text-xs">
              {actions?.length === 0 ? (
                <p className="text-slate-500 italic">No execution attempts recorded yet.</p>
              ) : (
                actions.map((act) => (
                  <div key={act.id} className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-1">
                    <div className="flex justify-between font-mono text-indigo-400">
                      <span>{act.action}</span>
                      <span>Attempt #{act.attempt_number}</span>
                    </div>
                    <p className="text-slate-400">Status: {act.status}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
