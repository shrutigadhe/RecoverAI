import axios from 'axios';

// Connect to live Render backend URL in production, or /api proxy in local development
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app'))
  ? 'https://recoverai-backend-ej3i.onrender.com/api'
  : '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchDashboardMetrics = async () => {
  const res = await api.get('/dashboard/metrics');
  return res.data;
};

export const fetchPayments = async () => {
  const res = await api.get('/payments');
  return res.data;
};

export const fetchRecoveryCases = async (status = null) => {
  const res = await api.get('/recovery/cases', {
    params: status ? { status } : {},
  });
  return res.data;
};

export const fetchCaseDetail = async (caseId) => {
  const res = await api.get(`/recovery/cases/${caseId}`);
  return res.data;
};

export const runRecoveryWorkflow = async (caseId) => {
  const res = await api.post(`/recovery/cases/${caseId}/run`);
  return res.data;
};

export const approveRecoveryCase = async (caseId, notes = '') => {
  const res = await api.post(`/recovery/cases/${caseId}/approve`, null, {
    params: { notes },
  });
  return res.data;
};

export const escalateRecoveryCase = async (caseId, reason = '') => {
  const res = await api.post(`/recovery/cases/${caseId}/escalate`, null, {
    params: { reason },
  });
  return res.data;
};

export const fetchAuditLogs = async (params = {}) => {
  const res = await api.get('/audit-logs', { params });
  return res.data;
};

export const runBatchEvaluation = async () => {
  const res = await api.post('/evaluation/run');
  return res.data;
};

export const sendRazorpayWebhook = async (payload) => {
  const res = await api.post('/webhook/razorpay', payload, {
    headers: {
      'X-Razorpay-Signature': 'demo_signature',
    },
  });
  return res.data;
};

export default api;
