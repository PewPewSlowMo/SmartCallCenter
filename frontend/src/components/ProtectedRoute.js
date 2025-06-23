import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-slate-600 dark:text-slate-400">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const roleHierarchy = {
      'admin': 4,
      'manager': 3,
      'supervisor': 2,
      'operator': 1
    };

    if (roleHierarchy[user.role] < roleHierarchy[requiredRole]) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center">
              <span className="text-red-600 text-2xl">⚠️</span>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Доступ запрещен</h2>
            <p className="text-slate-600 dark:text-slate-400">У вас нет прав для просмотра этой страницы</p>
          </div>
        </div>
      );
    }
  }

  return children;
};

export default ProtectedRoute;