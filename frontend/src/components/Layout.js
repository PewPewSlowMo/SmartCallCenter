import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { 
  BarChart3, 
  Users, 
  FileText, 
  Settings, 
  LogOut, 
  Menu,
  X,
  Sun,
  Moon,
  Home,
  Phone,
  Clock,
  TrendingUp,
  Headphones
} from 'lucide-react';

const Layout = () => {
  const { user, logout, hasPermission } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };



  const filteredMenuItems = menuItems.filter(item => 
    item.roles.includes(user?.role)
  );

  const getRoleLabel = (role) => {
    const labels = {
      'admin': 'Администратор',
      'manager': 'Менеджер',
      'supervisor': 'Супервайзер',
      'operator': 'Оператор'
    };
    return labels[role] || role;
  };

  const getRoleBadgeVariant = (role) => {
    const variants = {
      'admin': 'destructive',
      'manager': 'default',
      'supervisor': 'secondary',
      'operator': 'outline'
    };
    return variants[role] || 'outline';
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 ${darkMode ? 'dark' : ''}`}>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full w-64 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-300 ease-in-out z-50 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900 dark:text-white">CallCenter</h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">Analytics</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* User info */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">
                {user?.name?.charAt(0) || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {user?.name}
              </p>
              <Badge variant={getRoleBadgeVariant(user?.role)} className="text-xs mt-1">
                {getRoleLabel(user?.role)}
              </Badge>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Button
                key={item.path}
                variant={isActive ? "default" : "ghost"}
                className={`w-full justify-start space-x-3 h-12 transition-all duration-200 ${
                  isActive 
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg' 
                    : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
                onClick={() => {
                  navigate(item.path);
                  setSidebarOpen(false);
                }}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Button>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="absolute bottom-4 left-4 right-4 space-y-2">
          <Button
            variant="ghost"
            className="w-full justify-start space-x-3 h-12"
            onClick={toggleTheme}
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            <span>{darkMode ? 'Светлая тема' : 'Темная тема'}</span>
          </Button>
          
          <Button
            variant="ghost"
            className="w-full justify-start space-x-3 h-12 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            onClick={handleLogout}
          >
            <LogOut className="w-5 h-5" />
            <span>Выйти</span>
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </Button>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-slate-600 dark:text-slate-400">
                Последнее обновление: {new Date().toLocaleTimeString('ru-RU')}
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;