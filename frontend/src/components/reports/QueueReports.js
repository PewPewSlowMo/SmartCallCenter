import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { 
  Phone, 
  Download, 
  Clock, 
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  XCircle,
  Timer
} from 'lucide-react';
import { mockQueues, mockCalls } from '../../mock/mockData';

const QueueReports = () => {
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReportData();
  }, []);

  const loadReportData = () => {
    setLoading(true);
    setTimeout(() => {
      const data = mockQueues.map(queue => {
        const queueCalls = mockCalls.filter(call => call.queueId === queue.id);
        const answeredCalls = queueCalls.filter(call => call.status === 'answered');
        const missedCalls = queueCalls.filter(call => call.status === 'missed');
        
        const avgWaitTime = queueCalls.length > 0 
          ? Math.round(queueCalls.reduce((sum, call) => sum + call.waitTime, 0) / queueCalls.length)
          : 0;
          
        const avgTalkTime = answeredCalls.length > 0
          ? Math.round(answeredCalls.reduce((sum, call) => sum + call.talkTime, 0) / answeredCalls.length)
          : 0;
          
        const serviceLevel = queueCalls.length > 0
          ? Math.round((queueCalls.filter(call => call.waitTime <= 20).length / queueCalls.length) * 100)
          : 0;

        return {
          id: queue.id,
          name: queue.name,
          totalCalls: queueCalls.length,
          answeredCalls: answeredCalls.length,
          missedCalls: missedCalls.length,
          avgWaitTime,
          avgTalkTime,
          serviceLevel,
          answerRate: queueCalls.length > 0 ? Math.round((answeredCalls.length / queueCalls.length) * 100) : 0
        };
      });
      
      setReportData(data);
      setLoading(false);
    }, 500);
  };

  const handleExport = (format) => {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `queue_report_${timestamp}.${format}`;
    
    if (format === 'csv') {
      const headers = ['Очередь', 'Всего звонков', 'Отвечено', 'Пропущено', 'Ср. время ожидания', 'Ср. время разговора', 'Уровень обслуживания', 'Процент ответов'];
      const csvContent = [
        headers.join(','),
        ...reportData.map(queue => [
          queue.name,
          queue.totalCalls,
          queue.answeredCalls,
          queue.missedCalls,
          formatTime(queue.avgWaitTime),
          formatTime(queue.avgTalkTime),
          `${queue.serviceLevel}%`,
          `${queue.answerRate}%`
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

  const getServiceLevelBadge = (level) => {
    if (level >= 80) return 'default';
    if (level >= 60) return 'secondary';
    return 'destructive';
  };

  const getAnswerRateBadge = (rate) => {
    if (rate >= 90) return 'default';
    if (rate >= 75) return 'secondary';
    return 'destructive';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Отчеты по очередям
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Статистика работы очередей и распределение звонков
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Phone className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Всего очередей</p>
                <p className="text-2xl font-bold">{reportData.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Phone className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Общее количество звонков</p>
                <p className="text-2xl font-bold">
                  {reportData.reduce((sum, queue) => sum + queue.totalCalls, 0)}
                </p>
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
                <p className="text-2xl font-bold">
                  {reportData.length > 0 
                    ? formatTime(Math.round(reportData.reduce((sum, queue) => sum + queue.avgWaitTime, 0) / reportData.length))
                    : '0:00'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Средний уровень обслуживания</p>
                <p className="text-2xl font-bold">
                  {reportData.length > 0 
                    ? Math.round(reportData.reduce((sum, queue) => sum + queue.serviceLevel, 0) / reportData.length)
                    : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Детальная статистика очередей</CardTitle>
          <CardDescription>
            Показаны все {reportData.length} очереди
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center space-y-4">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-slate-500 dark:text-slate-400">Загрузка данных...</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название очереди</TableHead>
                    <TableHead>Всего звонков</TableHead>
                    <TableHead>Отвечено</TableHead>
                    <TableHead>Пропущено</TableHead>
                    <TableHead>Ср. время ожидания</TableHead>
                    <TableHead>Ср. время разговора</TableHead>
                    <TableHead>Уровень обслуживания</TableHead>
                    <TableHead>Процент ответов</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.map((queue) => (
                    <TableRow key={queue.id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                            <Phone className="w-4 h-4 text-white" />
                          </div>
                          <span>{queue.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Phone className="w-4 h-4 text-slate-400" />
                          <span>{queue.totalCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>{queue.answeredCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <XCircle className="w-4 h-4 text-red-500" />
                          <span>{queue.missedCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Clock className="w-4 h-4 text-orange-500" />
                          <span>{formatTime(queue.avgWaitTime)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Timer className="w-4 h-4 text-blue-500" />
                          <span>{formatTime(queue.avgTalkTime)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getServiceLevelBadge(queue.serviceLevel)}>
                          {queue.serviceLevel}%
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getAnswerRateBadge(queue.answerRate)}>
                          {queue.answerRate}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {reportData.length === 0 && !loading && (
            <div className="text-center py-12">
              <Phone className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">
                Нет данных для отображения
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Queue Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Сравнение производительности очередей</CardTitle>
          <CardDescription>Визуализация ключевых метрик по очередям</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-center space-y-2">
              <TrendingUp className="w-12 h-12 text-slate-400 mx-auto" />
              <p className="text-slate-500 dark:text-slate-400">
                График производительности
              </p>
              <p className="text-xs text-slate-400">
                Интеграция Chart.js будет добавлена в backend версии
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QueueReports;