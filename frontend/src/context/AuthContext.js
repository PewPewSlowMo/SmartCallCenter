import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('callcenter_token');
      const savedUser = localStorage.getItem('callcenter_user');
      
      if (token && savedUser) {
        // Verify token with backend
        const result = await authAPI.getCurrentUser();
        if (result.success) {
          setUser(result.data);
        } else {
          // Token invalid, clear storage
          localStorage.removeItem('callcenter_token');
          localStorage.removeItem('callcenter_user');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('callcenter_token');
      localStorage.removeItem('callcenter_user');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      setLoading(true);
      const result = await authAPI.login(username, password);
      
      if (result.success) {
        const { access_token, user: userData } = result.data;
        
        // Store token and user data
        localStorage.setItem('callcenter_token', access_token);
        localStorage.setItem('callcenter_user', JSON.stringify(userData));
        
        setUser(userData);
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: 'Ошибка входа в систему' };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('callcenter_token');
      localStorage.removeItem('callcenter_user');
    }
  };

  const hasPermission = (requiredRole) => {
    if (!user) return false;
    
    const roleHierarchy = {
      'admin': 4,
      'manager': 3,
      'supervisor': 2,
      'operator': 1
    };
    
    return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
  };

  const canViewGroup = (groupId) => {
    if (!user) return false;
    if (user.role === 'admin' || user.role === 'manager') return true;
    if (user.role === 'supervisor') return user.group_id === groupId;
    return false;
  };

  const canViewOperator = (operatorId) => {
    if (!user) return false;
    if (user.role === 'admin' || user.role === 'manager') return true;
    if (user.role === 'supervisor') {
      // Would need to check if operator belongs to supervisor's group
      return true; // Simplified for now
    }
    if (user.role === 'operator') return user.id === operatorId;
    return false;
  };

  const value = {
    user,
    loading,
    login,
    logout,
    hasPermission,
    canViewGroup,
    canViewOperator,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};