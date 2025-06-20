import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
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
  BarChart3
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
import { mockCalls, calculateKPIs, generateChartData, mockOperators, mockGroups } from '../mock/mockData';

const Dashboard = () => {
  const { user, hasPermission } = useAuth();
  const [period, setPeriod] = useState('today');
  const [selectedGroup, setSelectedGroup] = useState('all');
  const [kpis, setKpis] = useState({});
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [period, selectedGroup]);

  const loadDashboardData = () => {
    setLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const filteredCalls = selectedGroup === 'all' 
        ? mockCalls 
        : mockCalls.filter(call => {
            const operator = mockOperators.find(op => op.id === call.agentId);
            return operator?.groupId === selectedGroup;
          });
      
      const kpiData = calculateKPIs(filteredCalls, period);
      const chartData = generateChartData(filteredCalls, period === 'today' ? 'hourly' : 'daily');
      
      setKpis(kpiData);
      setChartData(chartData);
      setLastUpdate(new Date());
      setLoading(false);
    }, 500);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getPercentageChange = () => {
    // Mock percentage changes
    return {
      totalCalls: Math.floor(Math.random() * 20) - 10,
      answeredCalls: Math.floor(Math.random() * 15) - 5,
      avgWaitTime: Math.floor(Math.random() * 30) - 15,
      serviceLevel: Math.floor(Math.random() * 10) - 5
    };
  };

  const percentageChanges = getPercentageChange();

  const KPICard = ({ title, value, icon: Icon, color, change, format = 'number' }) => {
    const isPositive = change > 0;
    const isNegative = change < 0;
    
    const formatValue = (val) => {
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
          <div className="text-2xl font-bold">{formatValue(value)}</div>
          {change !== undefined && (
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Дашборд аналитики
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Добро пожаловать, {user?.name}! Обзор ключевых метрик колл-центра
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            disabled={loading}
            className="transition-all duration-200"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
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
                <Select value={selectedGroup} onValueChange={setSelectedGroup}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все группы</SelectItem>
                    {mockGroups.map(group => (
                      <SelectItem key={group.id} value={group.id}>
                        {group.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex items-end">
              <div className="text-sm text-slate-500 dark:text-slate-400">
                <div className="flex items-center space-x-1">
                  <Activity className="w-4 h-4 text-green-500" />
                  <span>Обновлено: {lastUpdate.toLocaleTimeString('ru-RU')}</span>
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
          value={kpis.totalCalls || 0}
          icon={Phone}
          color="from-blue-500 to-blue-600"
          change={percentageChanges.totalCalls}
        />
        <KPICard
          title="Отвеченные звонки"
          value={kpis.answeredCalls || 0}
          icon={CheckCircle}
          color="from-green-500 to-green-600"
          change={percentageChanges.answeredCalls}
        />
        <KPICard
          title="Пропущенные звонки"
          value={kpis.missedCalls || 0}
          icon={XCircle}
          color="from-red-500 to-red-600"
        />
        <KPICard
          title="Уровень обслуживания"
          value={kpis.serviceLevel || 0}
          icon={TrendingUp}
          color="from-purple-500 to-purple-600"
          format="percentage"
          change={percentageChanges.serviceLevel}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KPICard
          title="Среднее время ожидания"
          value={kpis.avgWaitTime || 0}
          icon={Clock}
          color="from-orange-500 to-orange-600"
          format="time"
          change={percentageChanges.avgWaitTime}
        />
        <KPICard
          title="Среднее время разговора"
          value={kpis.avgTalkTime || 0}
          icon={Timer}
          color="from-cyan-500 to-cyan-600"
          format="time"
        />
        <KPICard
          title="Загрузка операторов"
          value={kpis.operatorLoad || 0}
          icon={Users}
          color="from-indigo-500 to-indigo-600"
          format="percentage"
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
              {chartData && chartData.length > 0 ? (
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
              {mockOperators.slice(0, 5).map(operator => (
                <div key={operator.id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-semibold">
                        {operator.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-sm">{operator.name}</p>
                      <p className="text-xs text-slate-500">
                        {mockGroups.find(g => g.id === operator.groupId)?.name}
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
              ))}
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
              <div className="text-2xl font-bold text-blue-600">{Math.round((kpis.answeredCalls / kpis.totalCalls) * 100) || 0}%</div>
              <div className="text-xs text-slate-500 mt-1">Процент ответов</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{mockOperators.filter(op => op.status === 'online').length}</div>
              <div className="text-xs text-slate-500 mt-1">Операторов онлайн</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{formatTime(kpis.avgWaitTime + kpis.avgTalkTime)}</div>
              <div className="text-xs text-slate-500 mt-1">Общее время обработки</div>
            </div>
            <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{mockOperators.filter(op => op.status === 'busy').length}</div>
              <div className="text-xs text-slate-500 mt-1">Операторов занято</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;