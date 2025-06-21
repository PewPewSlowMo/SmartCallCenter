import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE_URL = `${BACKEND_URL}/api`;

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('callcenter_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('callcenter_token');
      localStorage.removeItem('callcenter_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password });
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Ошибка входа в систему' 
      };
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('callcenter_token');
      localStorage.removeItem('callcenter_user');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/me');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Dashboard API
export const dashboardAPI = {
  getStats: async (params = {}) => {
    try {
      const response = await api.get('/dashboard/stats', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getRealtimeData: async () => {
    try {
      const response = await api.get('/dashboard/realtime');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getChartData: async (type = 'hourly', period = 'today') => {
    try {
      const response = await api.get('/dashboard/chart-data', {
        params: { type, period }
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getOperatorActivity: async () => {
    try {
      const response = await api.get('/dashboard/operator-activity');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Calls API
export const callsAPI = {
  getCalls: async (params = {}) => {
    try {
      const response = await api.get('/calls/', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getMyCalls: async (params = {}) => {
    try {
      const response = await api.get('/calls/my', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getCall: async (callId) => {
    try {
      const response = await api.get(`/calls/${callId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  createCall: async (callData) => {
    try {
      const response = await api.post('/calls/', callData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateCall: async (callId, updateData) => {
    try {
      const response = await api.put(`/calls/${callId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  saveCallDetails: async (callId, callDetails) => {
    try {
      const response = await api.post(`/calls/${callId}/details`, callDetails);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getCallStats: async (params = {}) => {
    try {
      const response = await api.get('/calls/stats/summary', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getMissedCalls: async (params = {}) => {
    try {
      const response = await api.get('/calls/missed', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Operators API
export const operatorsAPI = {
  getOperators: async (groupId = null) => {
    try {
      const params = groupId ? { group_id: groupId } : {};
      const response = await api.get('/operators/', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getMyOperatorInfo: async () => {
    try {
      const response = await api.get('/operators/me');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateMyStatus: async (status) => {
    try {
      const response = await api.put('/operators/me/status', { status });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getOperatorStats: async (params = {}) => {
    try {
      const response = await api.get('/operators/stats', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getOperator: async (operatorId) => {
    try {
      const response = await api.get(`/operators/${operatorId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateOperatorStatus: async (operatorId, status) => {
    try {
      const response = await api.put(`/operators/${operatorId}/status`, { status });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Queues API
export const queuesAPI = {
  getQueues: async () => {
    try {
      const response = await api.get('/queues/');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getQueue: async (queueId) => {
    try {
      const response = await api.get(`/queues/${queueId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getQueueStats: async (params = {}) => {
    try {
      const response = await api.get('/queues/stats/summary', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  createQueue: async (queueData) => {
    try {
      const response = await api.post('/queues/', queueData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateQueue: async (queueId, updateData) => {
    try {
      const response = await api.put(`/queues/${queueId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  deleteQueue: async (queueId) => {
    try {
      const response = await api.delete(`/queues/${queueId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Admin API
export const adminAPI = {
  getUsers: async (skip = 0, limit = 100) => {
    try {
      const response = await api.get('/admin/users', { 
        params: { skip, limit } 
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getUser: async (userId) => {
    try {
      const response = await api.get(`/admin/users/${userId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  createUser: async (userData) => {
    try {
      const response = await api.post('/admin/users', userData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateUser: async (userId, updateData) => {
    try {
      const response = await api.put(`/admin/users/${userId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  deleteUser: async (userId) => {
    try {
      const response = await api.delete(`/admin/users/${userId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getGroups: async () => {
    try {
      const response = await api.get('/admin/groups');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  createGroup: async (groupData) => {
    try {
      const response = await api.post('/admin/groups', groupData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getSystemSettings: async () => {
    try {
      const response = await api.get('/admin/settings');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  updateSystemSettings: async (settings) => {
    try {
      const response = await api.put('/admin/settings', settings);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  testAsteriskConnection: async (asteriskConfig) => {
    try {
      const response = await api.post('/admin/settings/asterisk/test', asteriskConfig);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getUserOperatorInfo: async (userId) => {
    try {
      const response = await api.get(`/admin/users/${userId}/operator`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getSystemInfo: async () => {
    try {
      const response = await api.get('/admin/system/info');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Health check
export const healthAPI = {
  check: async () => {
    try {
      const response = await api.get('/health');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

export default api;