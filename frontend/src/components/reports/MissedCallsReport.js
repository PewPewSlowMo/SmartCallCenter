import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { 
  PhoneOff, 
  Download, 
  Search, 
  Clock, 
  Phone,
  Calendar,
  Filter,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { mockCalls, mockQueues } from '../../mock/mockData';

const MissedCallsReport = () => {
  const [reportData, setReportData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedQueue, setSelectedQueue] = useState('all');
  const [selectedPeriod, setSelectedPeriod] = useState('today');

  useEffect(() => {
    loadReportData();
  }, []);

  useEffect(() => {
    filterData();
  }, [reportData, searchTerm, selectedQueue, selectedPeriod]);

  const loadReportData = () => {
    setLoading(true);
    setTimeout(() => {
      const missedCalls = mockCalls
        .filter(call => call.status === 'missed')
        .map(call => {
          const queue = mockQueues.find(q => q.id === call.queueId);
          return {
            ...call,
            queueName: queue?.name || 'Неизвестная очередь',
            reason: getMissedCallReason(call)
          };
        })
        .sort((a, b) => new Date(b.startTime) - new Date(a.startTime));
      
      setReportData(missedCalls);
      setLoading(false);
    }, 500);
  };

  const getMissedCallReason = (call) => {
    const reasons = [
      'Превышено время ожидания',
      'Все операторы заняты',
      'Абонент отключился',
      'Системная ошибка',
      'Техническая проблема'
    ];
    return reasons[Math.floor(Math.random() * reasons.length)];
  };

  const filterData = () => {
    let filtered = [...reportData];
    const now = new Date();

    // Filter by period
    switch (selectedPeriod) {
      case 'today':
        filtered = filtered.filter(call => {
          const callDate = new Date(call.startTime);
          return callDate.toDateString() === now.toDateString();
        });
        break;
      case 'yesterday':
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        filtered = filtered.filter(call => {
          const callDate = new Date(call.startTime);
          return callDate.toDateString() === yesterday.toDateString();
        });
        break;
      case 'week':
        const weekAgo = new Date(now);
        weekAgo.setDate(weekAgo.getDate() - 7);
        filtered = filtered.filter(call => new Date(call.startTime) >= weekAgo);
        break;
      case 'month':
        const monthAgo = new Date(now);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        filtered = filtered.filter(call => new Date(call.startTime) >= monthAgo);
        break;
    }

    // Filter by queue
    if (selectedQueue !== 'all') {
      filtered = filtered.filter(call => call.queueId === selectedQueue);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(call => 
        call.callerNumber.includes(searchTerm) ||
        call.queueName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        call.reason.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredData(filtered);
  };

  const handleExport = (format) => {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `missed_calls_report_${timestamp}.${format}`;
    
    if (format === 'csv') {
      const headers = ['Номер телефона', 'Очередь', 'Дата и время', 'Время ожидания', 'Причина'];
      const csvContent = [
        headers.join(','),
        ...filteredData.map(call => [
          call.callerNumber,
          call.queueName,
          new Date(call.startTime).toLocaleString('ru-RU'),
          formatTime(call.waitTime),
          call.reason
        ].join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      alert(`Экспорт в PDF: ${filename}\nФункция будет реализована в backend версии`);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getReasonBadge = (reason) => {
    switch (reason) {
      case 'Превышено время ожидания':
        return 'destructive';
      case 'Все операторы заняты':
        return 'secondary';
      case 'Абонент отключился':
        return 'outline';
      default:
        return 'default';
    }
  };

  const getWaitTimeBadge = (waitTime) => {
    if (waitTime > 180) return 'destructive'; // > 3 minutes
    if (waitTime > 60) return 'secondary'; // > 1 minute
    return 'outline';
  };

  // Calculate summary statistics
  const totalMissedCalls = filteredData.length;
  const avgWaitTime = totalMissedCalls > 0 
    ? Math.round(filteredData.reduce((sum, call) => sum + call.waitTime, 0) / totalMissedCalls)
    : 0;
  const longestWaitTime = totalMissedCalls > 0 
    ? Math.max(...filteredData.map(call => call.waitTime))
    : 0;

  // Group by reason
  const reasonStats = filteredData.reduce((acc, call) => {
    acc[call.reason] = (acc[call.reason] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
            Пропущенные звонки
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Анализ пропущенных звонков и их причин
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
          >
            <Download className="w-4 h-4 mr-2" />
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
          >
            <Download className="w-4 h-4 mr-2" />
            PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="w-5 h-5" />
            <span>Фильтры и поиск</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Поиск по номеру, очереди или причине..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Select value={selectedQueue} onValueChange={setSelectedQueue}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Выберите очередь" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все очереди</SelectItem>
                  {mockQueues.map(queue => (
                    <SelectItem key={queue.id} value={queue.id}>
                      {queue.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Сегодня</SelectItem>
                  <SelectItem value="yesterday">Вчера</SelectItem>
                  <SelectItem value="week">Неделя</SelectItem>
                  <SelectItem value="month">Месяц</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <PhoneOff className="w-5 h-5 text-red-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Пропущенные звонки</p>
                <p className="text-2xl font-bold">{totalMissedCalls}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Среднее время ожидания</p>
                <p className="text-2xl font-bold">{formatTime(avgWaitTime)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Максимальное ожидание</p>
                <p className="text-2xl font-bold">{formatTime(longestWaitTime)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Основная причина</p>
                <p className="text-sm font-bold">
                  {Object.keys(reasonStats).length > 0 
                    ? Object.entries(reasonStats).sort(([,a], [,b]) => b - a)[0][0].split(' ')[0] + '...'
                    : 'Нет данных'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Детальный список пропущенных звонков</CardTitle>
          <CardDescription>
            Показано {filteredData.length} из {reportData.length} пропущенных звонков
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center space-y-4">
                <div className="w-8 h-8 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-slate-500 dark:text-slate-400">Загрузка данных...</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Номер телефона</TableHead>
                    <TableHead>Очередь</TableHead>
                    <TableHead>Дата и время</TableHead>
                    <TableHead>Время ожидания</TableHead>
                    <TableHead>Причина</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.map((call) => (
                    <TableRow key={call.id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-2">
                          <PhoneOff className="w-4 h-4 text-red-500" />
                          <span className="font-mono">{call.callerNumber}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{call.queueName}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Calendar className="w-4 h-4 text-slate-400" />
                          <span className="text-sm">
                            {new Date(call.startTime).toLocaleString('ru-RU')}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getWaitTimeBadge(call.waitTime)}>
                          {formatTime(call.waitTime)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getReasonBadge(call.reason)}>
                          {call.reason}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {filteredData.length === 0 && !loading && (
            <div className="text-center py-12">
              <PhoneOff className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">
                {searchTerm || selectedQueue !== 'all' 
                  ? 'Нет пропущенных звонков, соответствующих выбранным фильтрам'
                  : 'Нет данных для отображения'
                }
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reason Analysis */}
      {Object.keys(reasonStats).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Анализ причин пропуска звонков</CardTitle>
            <CardDescription>Распределение по основным причинам</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(reasonStats)
                .sort(([,a], [,b]) => b - a)
                .map(([reason, count]) => (
                  <div key={reason} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-sm font-medium">{reason}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">{count} звонков</Badge>
                      <span className="text-xs text-slate-500">
                        {Math.round((count / totalMissedCalls) * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MissedCallsReport;