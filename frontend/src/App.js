import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Toaster } from "./components/ui/toaster";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./components/Login";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import OperatorReports from "./components/reports/OperatorReports";
import QueueReports from "./components/reports/QueueReports";
import MissedCallsReport from "./components/reports/MissedCallsReport";
import OperatorDashboard from "./components/operator/OperatorDashboard";
import AdminPanel from "./components/admin/AdminPanel";

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="operator" element={
                <ProtectedRoute requiredRole="operator">
                  <OperatorDashboard />
                </ProtectedRoute>
              } />
              <Route path="reports/operators" element={
                <ProtectedRoute requiredRole="supervisor">
                  <OperatorReports />
                </ProtectedRoute>
              } />
              <Route path="reports/queues" element={
                <ProtectedRoute requiredRole="supervisor">
                  <QueueReports />
                </ProtectedRoute>
              } />
              <Route path="reports/missed-calls" element={
                <ProtectedRoute requiredRole="supervisor">
                  <MissedCallsReport />
                </ProtectedRoute>
              } />
              <Route path="analytics" element={
                <ProtectedRoute requiredRole="manager">
                  <div className="text-center py-20">
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                      Расширенная аналитика
                    </h2>
                    <p className="text-slate-600 dark:text-slate-400">
                      Этот раздел будет реализован в backend версии
                    </p>
                  </div>
                </ProtectedRoute>
              } />
              <Route path="admin" element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPanel />
                </ProtectedRoute>
              } />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster />
      </div>
    </AuthProvider>
  );
}

export default App;