import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Phone, 
  PhoneCall, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Users,
  Timer,
  CheckCircle,
  XCircle,
  Activity,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  BarChart3,
  AlertTriangle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import { useApi, useRealtimeApi } from '../hooks/useApi';
import { dashboardAPI, queuesAPI } from '../services/api';

const Dashboard = () => {
  const { user, hasPermission } = useAuth();
  const [period, setPeriod] = useState('today');
  const [selectedGroup, setSelectedGroup] = useState('all');

  // API hooks
  const {
    data: dashboardStats,
    loading: statsLoading,
    error: statsError,
    execute: refetchStats
  } = useApi(() => dashboardAPI.getStats({ period, group_id: selectedGroup !== 'all' ? selectedGroup : null }), [period, selectedGroup]);

  const {
    data: realtimeData,
    loading: realtimeLoading,
    error: realtimeError,
    lastUpdate,
    refresh: refreshRealtime
  } = useRealtimeApi(dashboardAPI.getRealtimeData, 30000);

  const {
    data: chartData,
    loading: chartLoading,
    execute: refetchChartData
  } = useApi(() => dashboardAPI.getChartData(period === 'today' ? 'hourly' : 'daily', period), [period]);

  const {
    data: queues,
    loading: queuesLoading
  } = useApi(queuesAPI.getQueues, []);

  const {
    data: operatorActivity,
    loading: operatorActivityLoading
  } = useApi(dashboardAPI.getOperatorActivity, []);

  const handleRefresh = async () => {
    await Promise.all([
      refetchStats(),
      refreshRealtime(),
      refetchChartData()
    ]);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getPercentageChange = (current, previous) => {
    if (!previous) return 0;
    return Math.round(((current - previous) / previous) * 100);
  };

  const KPICard = ({ title, value, icon: Icon, color, change, format = 'number', loading = false }) => {
    const isPositive = change > 0;
    const isNegative = change < 0;
    
    const formatValue = (val) => {
      if (loading || val === undefined || val === null) return '—';
      switch (format) {
        case 'time':
          return formatTime(val);
        case 'percentage':
          return `${val}%`;
        default:
          return val.toLocaleString();
      }
    };

    return (
      <Card className="relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:scale-105">
        <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-5`}></div>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <Icon className={`h-4 w-4 ${color.split(' ')[0].replace('from-', 'text-')}`} />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {loading ? (
              <div className="w-16 h-8 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
            ) : (
              formatValue(value)
            )}
          </div>
          {change !== undefined && !loading && (
            <div className="flex items-center space-x-1 mt-1">
              {isPositive && <TrendingUp className="h-4 w-4 text-green-500" />}
              {isNegative && <TrendingDown className="h-4 w-4 text-red-500" />}
              <span className={`text-xs ${
                isPositive ? 'text-green-500' : isNegative ? 'text-red-500' : 'text-gray-500'
              }`}>
                {Math.abs(change)}% за {period === 'today' ? 'час' : 'день'}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  // Show error if critical APIs fail
  if (statsError) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Ошибка загрузки данных дашборда: {statsError}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const callStats = dashboardStats?.call_stats || {};
  const operatorStats = dashboardStats?.operator_stats || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Smart Колл Центр
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Добро пожаловать, {user?.name}! Обзор ключевых метрик колл-центра
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={statsLoading}
            className="transition-all duration-200"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${statsLoading ? 'animate-spin' : ''}`} />
            Обновить
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Экспорт
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="w-5 h-5" />
            <span>Фильтры</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Период</label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Сегодня</SelectItem>
                  <SelectItem value="yesterday">Вчера</SelectItem>
                  <SelectItem value="week">Текущая неделя</SelectItem>
                  <SelectItem value="month">Текущий месяц</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hasPermission('supervisor') && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Группа операторов</label>
                <Select value={selectedGroup} onValueChange={setSelectedGroup} disabled={queuesLoading}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все группы</SelectItem>
                    {/* Note: This would need groups API to be implemented */}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex items-end">
              <div className="text-sm text-slate-500 dark:text-slate-400">
                <div className="flex items-center space-x-1">
                  <Activity className="w-4 h-4 text-green-500" />
                  <span>
                    Обновлено: {lastUpdate ? lastUpdate.toLocaleTimeString('ru-RU') : '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Всего звонков"
          value={callStats.total_calls}
          icon={Phone}
          color="from-blue-500 to-blue-600"
          loading={statsLoading}
        />
        <KPICard
          title="Отвеченные звонки"
          value={callStats.answered_calls}
          icon={CheckCircle}
          color="from-green-500 to-green-600"
          loading={statsLoading}
        />
        <KPICard
          title="Пропущенные звонки"
          value={callStats.missed_calls}
          icon={XCircle}
          color="from-red-500 to-red-600"
          loading={statsLoading}
        />
        <KPICard
          title="Уровень обслуживания"
          value={callStats.service_level}
          icon={TrendingUp}
          color="from-purple-500 to-purple-600"
          format="percentage"
          loading={statsLoading}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KPICard
          title="Среднее время ожидания"
          value={callStats.avg_wait_time}
          icon={Clock}
          color="from-orange-500 to-orange-600"
          format="time"
          loading={statsLoading}
        />
        <KPICard
          title="Среднее время разговора"
          value={callStats.avg_talk_time}
          icon={Timer}
          color="from-cyan-500 to-cyan-600"
          format="time"
          loading={statsLoading}
        />
        <KPICard
          title="Процент ответов"
          value={callStats.answer_rate}
          icon={Users}
          color="from-indigo-500 to-indigo-600"
          format="percentage"
          loading={statsLoading}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly/Daily Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Распределение звонков</CardTitle>
            <CardDescription>
              {period === 'today' ? 'По часам за сегодня' : 'По дням за выбранный период'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {chartLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="text-slate-500 dark:text-slate-400">Загрузка графика...</p>
                  </div>
                </div>
              ) : chartData && chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis 
                      dataKey={period === 'today' ? 'hour' : 'date'} 
                      stroke="#64748b"
                      fontSize={12}
                    />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Legend />
                    <Bar 
                      dataKey="answered" 
                      fill="#10b981"
                      name="Отвечено"
                      radius={[2, 2, 0, 0]}
                    />
                    <Bar 
                      dataKey="missed" 
                      fill="#ef4444"
                      name="Пропущено"
                      radius={[2, 2, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center bg-slate-50 dark:bg-slate-900 rounded-lg">
                  <div className="text-center space-y-2">
                    <BarChart3 className="w-12 h-12 text-slate-400 mx-auto" />
                    <p className="text-slate-500 dark:text-slate-400">
                      Нет данных для отображения
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Real-time Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Активность операторов</CardTitle>
            <CardDescription>Текущий статус команды</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {operatorActivityLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full animate-pulse"></div>
                      <div className="space-y-1">
                        <div className="w-24 h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
                        <div className="w-16 h-3 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
                      </div>
                    </div>
                    <div className="w-16 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
                  </div>
                ))
              ) : operatorActivity && operatorActivity.length > 0 ? (
                operatorActivity.slice(0, 5).map(operator => (
                  <div key={operator.operator_id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-semibold">
                          {operator.name?.charAt(0) || 'U'}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-sm">{operator.name}</p>
                        <p className="text-xs text-slate-500">
                          {operator.group || 'Без группы'}
                        </p>
                      </div>
                    </div>
                    <Badge 
                      variant={operator.status === 'online' ? 'default' : 
                               operator.status === 'busy' ? 'destructive' : 'secondary'}
                      className="text-xs"
                    >
                      {operator.status === 'online' ? 'Онлайн' :
                       operator.status === 'busy' ? 'Занят' : 'Офлайн'}
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-500 dark:text-slate-400">
                    Нет данных об операторах
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Быстрая статистика</CardTitle>
          <CardDescription>Дополнительные показатели эффективности</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {realtimeLoading ? '—' : realtimeData?.operators_online || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">Операторов онлайн</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {realtimeLoading ? '—' : realtimeData?.calls_today || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">Звонков сегодня</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {realtimeLoading ? '—' : realtimeData?.ongoing_calls || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">Активных звонков</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {realtimeLoading ? '—' : realtimeData?.operators_busy || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">Операторов занято</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;