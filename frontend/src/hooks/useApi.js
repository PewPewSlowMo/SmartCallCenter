import { useState, useEffect, useCallback } from 'react';

// Generic hook for API calls
export const useApi = (apiFunction, dependencies = [], immediate = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...args);
      
      if (result.success) {
        setData(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (err) {
      const errorMessage = err.message || 'Произошла ошибка';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  useEffect(() => {
    if (immediate && apiFunction) {
      execute();
    }
  }, dependencies);

  return {
    data,
    loading,
    error,
    execute,
    refetch: execute
  };
};

// Hook for paginated data
export const usePaginatedApi = (apiFunction, initialParams = {}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [params, setParams] = useState({ skip: 0, limit: 20, ...initialParams });

  const loadData = useCallback(async (reset = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const currentParams = reset ? { ...params, skip: 0 } : params;
      const result = await apiFunction(currentParams);
      
      if (result.success) {
        const newData = result.data || [];
        
        if (reset) {
          setData(newData);
        } else {
          setData(prev => [...prev, ...newData]);
        }
        
        setHasMore(newData.length === params.limit);
        
        if (!reset) {
          setParams(prev => ({ ...prev, skip: prev.skip + prev.limit }));
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (err) {
      const errorMessage = err.message || 'Произошла ошибка';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction, params]);

  const refresh = useCallback(() => {
    setParams(prev => ({ ...prev, skip: 0 }));
    return loadData(true);
  }, [loadData]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      return loadData(false);
    }
  }, [loading, hasMore, loadData]);

  const updateParams = useCallback((newParams) => {
    setParams(prev => ({ ...prev, ...newParams, skip: 0 }));
  }, []);

  useEffect(() => {
    loadData(true);
  }, [params.limit, JSON.stringify(initialParams)]);

  return {
    data,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
    updateParams
  };
};

// Hook for real-time data with auto-refresh
export const useRealtimeApi = (apiFunction, interval = 30000, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      if (!loading) setLoading(true);
      setError(null);
      
      const result = await apiFunction();
      
      if (result.success) {
        setData(result.data);
        setLastUpdate(new Date());
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (err) {
      const errorMessage = err.message || 'Произошла ошибка';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction, loading]);

  useEffect(() => {
    fetchData();
    
    const intervalId = setInterval(fetchData, interval);
    
    return () => clearInterval(intervalId);
  }, dependencies);

  return {
    data,
    loading,
    error,
    lastUpdate,
    refresh: fetchData
  };
};

// Hook for form submissions
export const useFormApi = (apiFunction) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const submit = useCallback(async (formData) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);
      
      const result = await apiFunction(formData);
      
      if (result.success) {
        setSuccess(true);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (err) {
      const errorMessage = err.message || 'Произошла ошибка';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  const reset = useCallback(() => {
    setError(null);
    setSuccess(false);
  }, []);

  return {
    submit,
    loading,
    error,
    success,
    reset
  };
};

export default useApi;