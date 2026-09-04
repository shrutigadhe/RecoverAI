import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  IndianRupee,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Play
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { fetchDashboardMetrics, sendRazorpayWebhook, runRecoveryWorkflow } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#64748b'];

export default function Overview() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scenarioRunning, setScenarioRunning] = useState(false);
  const [scenarioLog, setScenarioLog] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const triggerDemoScenario = async (scenarioNum) => {
    setScenarioRunning(true);
    setScenarioLog(`Running Scenario ${scenarioNum}...`);
    try {
      let payload;
      if (scenarioNum === 1) {
        // Successful recovery: ₹3,500, bank error, 0 retries
        payload = {
          event: 'payment.failed',
          payload: {
            payment: {
              entity: {
                id: `pay_scen1_${Date.now()}`,
                amount: 350000,
                method: 'upi',
                error_description: 'Temporary bank server error',
                email: 'rahul.sharma@example.com',
                contact: 'Rahul Sharma',
              },
            },
          },
        };
      } else if (scenarioNum === 2) {
        // Retry blocked: retry_count = 1
        payload = {
          event: 'payment.failed',
          payload: {
            payment: {
              entity: {
                id: `pay_scen2_${Date.now()}`,
                amount: 200000,
                method: 'upi',
                error_description: 'Temporary bank server error',
                email: 'priya.shah@example.com',
                contact: 'Priya Shah',
              },
            },
          },
        };
      } else if (scenarioNum === 3) {
        // Low confidence: unknown failure
        payload = {
          event: 'payment.failed',
          payload: {
            payment: {
              entity: {
                id: `pay_scen3_${Date.now()}`,
                amount: 320000,
                method: 'netbanking',
                error_description: 'Unknown gateway failure code 999',
                email: 'amit.patil@example.com',
                contact: 'Amit Patil',
              },
            },
          },
        };
      } else if (scenarioNum === 4) {
        // High-value payment: ₹25,000 (> ₹5,000)
        payload = {
          event: 'payment.failed',
          payload: {
            payment: {
              entity: {
                id: `pay_scen4_${Date.now()}`,
                amount: 2500000,
                method: 'card',
                error_description: 'Temporary bank server error',
                email: 'enterprise@corp.com',
                contact: 'Enterprise Corp',
              },
            },
          },
        };
      } else if (scenarioNum === 5) {
        // Already successful payment
        payload = {
          event: 'payment.captured',
          payload: {
            payment: {
              entity: {
                id: `pay_scen5_${Date.now()}`,
                amount: 350000,
                method: 'upi',
                email: 'captured.cust@example.com',
                contact: 'Captured Customer',
              },
            },
          },
        };
      }

      // Step 1: Webhook
      const webhookRes = await sendRazorpayWebhook(payload);
      if (webhookRes.recovery_case_id) {
        // Step 2: Auto-run recovery workflow
        const runRes = await runRecoveryWorkflow(webhookRes.recovery_case_id);
        setScenarioLog(
          `Scenario ${scenarioNum} Complete! Status: ${runRes.status} | Action: ${runRes.recommended_action || 'N/A'} | Recovered: ₹${runRes.recovered_amount}`
        );
      } else {
        setScenarioLog(`Webhook Result: ${webhookRes.message}`);
      }

      await loadData();
    } catch (err) {
      setScenarioLog(`Scenario execution error: ${err.message}`);
    } finally {
      setScenarioRunning(false);
    }
  };

  const chartData = [
    { name: 'Revenue at Risk', amount: metrics?.total_revenue_at_risk || 0 },
    { name: 'Recovered Revenue', amount: metrics?.total_revenue_recovered || 0 },
  ];

  const pieData = [
    { name: 'Temporary Bank Error', value: 45 },
    { name: 'Network Timeout', value: 25 },
    { name: 'Insufficient Funds', value: 15 },
    { name: 'Unknown Failure', value: 15 },
  ];

  return (
    <div className="space-y-6">
      {/* Title & Refresh Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Revenue Recovery Dashboard</h2>
          <p className="text-sm text-slate-400">
            Real-time tracking of failed payment detection, policy guardrails, and automated recovery.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg border border-slate-700 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Revenue At Risk</span>
            <IndianRupee className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-rose-400">
            ₹{metrics?.total_revenue_at_risk?.toLocaleString('en-IN') || '0'}
          </p>
          <span className="text-xs text-slate-500">From detected payment failures</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Revenue Recovered</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400">
            ₹{metrics?.total_revenue_recovered?.toLocaleString('en-IN') || '0'}
          </p>
          <span className="text-xs text-slate-500">Successfully captured</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Recovery Rate</span>
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-indigo-400">
            {metrics?.recovery_rate_percentage || 0}%
          </p>
          <span className="text-xs text-slate-500">Recovery efficiency</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Failed Payments</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-slate-200">
            {metrics?.total_failed_payments || 0}
          </p>
          <span className="text-xs text-slate-500">Total detected cases</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Recovery Attempts</span>
            <RefreshCw className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-slate-200">
            {metrics?.total_recovery_attempts || 0}
          </p>
          <span className="text-xs text-slate-500">Bounded retries executed</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Escalated Cases</span>
            <XCircle className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-400">
            {metrics?.total_escalated_cases || 0}
          </p>
          <span className="text-xs text-slate-500">Sent to merchant support</span>
        </div>
      </div>

      {/* Interactive Demo Scenarios Panel */}
      <div className="bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-indigo-500/30 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Play className="w-5 h-5 text-indigo-400 fill-indigo-400/20" />
            <h3 className="text-base font-bold text-slate-100">Simulate Live Demo Scenarios</h3>
          </div>
          <span className="text-xs text-indigo-300 font-mono">DEMO_MODE=true</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <button
            onClick={() => triggerDemoScenario(1)}
            disabled={scenarioRunning}
            className="p-3 bg-slate-900/80 hover:bg-indigo-900/30 border border-emerald-500/30 rounded-lg text-left transition text-xs space-y-1"
          >
            <div className="font-semibold text-emerald-400">1. Successful Recovery</div>
            <div className="text-slate-400">₹3,500 • Bank Error • RETRY → RECOVERED</div>
          </button>

          <button
            onClick={() => triggerDemoScenario(2)}
            disabled={scenarioRunning}
            className="p-3 bg-slate-900/80 hover:bg-indigo-900/30 border border-amber-500/30 rounded-lg text-left transition text-xs space-y-1"
          >
            <div className="font-semibold text-amber-400">2. Retry Blocked</div>
            <div className="text-slate-400">₹2,000 • Retry = 1 → ESCALATED</div>
          </button>

          <button
            onClick={() => triggerDemoScenario(3)}
            disabled={scenarioRunning}
            className="p-3 bg-slate-900/80 hover:bg-indigo-900/30 border border-purple-500/30 rounded-lg text-left transition text-xs space-y-1"
          >
            <div className="font-semibold text-purple-400">3. Low Confidence</div>
            <div className="text-slate-400">₹3,200 • Unknown Error → ESCALATED</div>
          </button>

          <button
            onClick={() => triggerDemoScenario(4)}
            disabled={scenarioRunning}
            className="p-3 bg-slate-900/80 hover:bg-indigo-900/30 border border-rose-500/30 rounded-lg text-left transition text-xs space-y-1"
          >
            <div className="font-semibold text-rose-400">4. High Value Payment</div>
            <div className="text-slate-400">₹25,000 (&gt;₹5k) → ESCALATED</div>
          </button>

          <button
            onClick={() => triggerDemoScenario(5)}
            disabled={scenarioRunning}
            className="p-3 bg-slate-900/80 hover:bg-indigo-900/30 border border-cyan-500/30 rounded-lg text-left transition text-xs space-y-1"
          >
            <div className="font-semibold text-cyan-400">5. Already Captured</div>
            <div className="text-slate-400">Payment Captured → STOP</div>
          </button>
        </div>

        {scenarioLog && (
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-indigo-300">
            {scenarioLog}
          </div>
        )}
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-base font-bold text-slate-200">Revenue at Risk vs Recovered</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                  formatter={(val) => [`₹${val.toLocaleString('en-IN')}`, 'Amount']}
                />
                <Bar dataKey="amount" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-base font-bold text-slate-200">Payment Failure Reason Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-200">Recent Recovery Cases</h3>
          <Link
            to="/payments"
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
          >
            <span>View All Payments</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/60 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">Payment ID</th>
                <th className="py-3 px-4">Score</th>
                <th className="py-3 px-4">Rec. Action</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {metrics?.recent_cases?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-6 text-center text-slate-500">
                    No recovery cases recorded yet. Run a scenario above to test!
                  </td>
                </tr>
              ) : (
                metrics?.recent_cases?.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-indigo-300">{c.id.substring(0, 8)}...</td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">{c.payment_id.substring(0, 8)}...</td>
                    <td className="py-3 px-4 font-semibold text-emerald-400">{Math.round(c.recovery_score * 100)}%</td>
                    <td className="py-3 px-4 font-mono text-xs text-indigo-400">{c.recommended_action || 'N/A'}</td>
                    <td className="py-3 px-4">{Math.round(c.confidence * 100)}%</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/payments/${c.id}`}
                        className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium"
                      >
                        Details
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
