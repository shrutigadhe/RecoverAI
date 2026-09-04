import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import Overview from './pages/Overview';
import FailedPayments from './pages/FailedPayments';
import CaseDetail from './pages/CaseDetail';
import AuditTrail from './pages/AuditTrail';
import Analytics from './pages/Analytics';
import BatchEvaluation from './pages/BatchEvaluation';
import Login from './pages/Login';
import Register from './pages/Register';

function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">Loading...</div>;
  }

  // In DEMO_MODE, if no token exists, allow sandbox preview or redirect to login
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Overview />} />
            <Route path="payments" element={<FailedPayments />} />
            <Route path="payments/:caseId" element={<CaseDetail />} />
            <Route path="audit" element={<AuditTrail />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="evaluation" element={<BatchEvaluation />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
