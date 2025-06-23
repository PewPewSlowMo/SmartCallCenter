const Config = {
  BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000',
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api',
  ENVIRONMENT: process.env.NODE_ENV || 'development',
  DEBUG: process.env.NODE_ENV === 'development',
  WEBSOCKET_URL: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:5000/ws',
  DASHBOARD_REFRESH_INTERVAL: 5000,
  TOKEN_STORAGE_KEY: 'authToken',
  USER_STORAGE_KEY: 'userData'
};

// Именованные экспорты для обратной совместимости
export const BACKEND_URL = Config.BACKEND_URL;
export const API_BASE_URL = Config.API_BASE_URL;
export const ENVIRONMENT_NAME = Config.ENVIRONMENT;
export const DEBUG_MODE = Config.DEBUG;
export const WEBSOCKET_URL = Config.WEBSOCKET_URL;
export const DASHBOARD_REFRESH_INTERVAL = Config.DASHBOARD_REFRESH_INTERVAL;
export const TOKEN_STORAGE_KEY = Config.TOKEN_STORAGE_KEY;
export const USER_STORAGE_KEY = Config.USER_STORAGE_KEY;

export default Config;