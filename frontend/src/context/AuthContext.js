import React, { createContext, useContext, useState, useEffect } from 'react';
import { mockUsers } from '../mock/mockData';

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
    // Check for saved session
    const savedUser = localStorage.getItem('callcenter_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const foundUser = mockUsers.find(
        u => u.username === username && u.password === password
      );
      
      if (foundUser) {
        const { password: _, ...userWithoutPassword } = foundUser;
        setUser(userWithoutPassword);
        localStorage.setItem('callcenter_user', JSON.stringify(userWithoutPassword));
        return { success: true };
      } else {
        return { success: false, error: 'Неверные учетные данные' };
      }
    } catch (error) {
      return { success: false, error: 'Ошибка входа в систему' };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('callcenter_user');
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
    if (user.role === 'supervisor') return user.groupId === groupId;
    return false;
  };

  const canViewOperator = (operatorId) => {
    if (!user) return false;
    if (user.role === 'admin' || user.role === 'manager') return true;
    if (user.role === 'supervisor') {
      // Check if operator belongs to supervisor's group
      return true; // Mock implementation
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
    canViewOperator
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};