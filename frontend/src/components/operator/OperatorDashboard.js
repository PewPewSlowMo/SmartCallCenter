import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import CallModal from './CallModal';
import { useToast } from '../../hooks/use-toast';
import { 
  Phone, 
  PhoneCall, 
  PhoneOff, 
  Clock, 
  CheckCircle,
  XCircle,
  Users,
  TrendingUp,
  Bell,
  Activity,
  Headphones
} from 'lucide-react';

const OperatorDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [operatorStatus, setOperatorStatus] = useState('available'); // available, busy, break, offline
  const [incomingCall, setIncomingCall] = useState(null);
  const [isCallModalOpen, setIsCallModalOpen] = useState(false);
  const [todayStats, setTodayStats] = useState({
    totalCalls: 0,
    answeredCalls: 0,
    missedCalls: 0,
    avgCallDuration: 0,
    totalTalkTime: 0
  });
  const [recentCalls, setRecentCalls] = useState([]);

  // Simulate incoming calls for demo
  useEffect(() => {
    if (operatorStatus === 'available') {
      const interval = setInterval(() => {
        if (Math.random() < 0.3 && !incomingCall) { // 30% chance of incoming call
          simulateIncomingCall();
        }
      }, 10000); // Check every 10 seconds

      return () => clearInterval(interval);
    }
  }, [operatorStatus, incomingCall]);

  // Load operator stats
  useEffect(() => {
    loadOperatorStats();
  }, []);

  const simulateIncomingCall = () => {
    const mockCallData = {
      id: Date.now().toString(),
      callerNumber: `+7${Math.floor(Math.random() * 9000000000) + 1000000000}`,
      queueName: ['Основная очередь', 'Техподдержка', 'Продажи'][Math.floor(Math.random() * 3)],
      region: ['Москва', 'СПб', 'Екатеринбург', 'Новосибирск'][Math.floor(Math.random() * 4)],
      customerInfo: {
        name: ['Иван Петров', 'Мария Сидорова', 'Алексей Козлов', 'Елена Смирнова'][Math.floor(Math.random() * 4)],
        email: 'customer@example.com',
        vip: Math.random() < 0.2 // 20% chance of VIP
      },
      callHistory: [
        { date: new Date(Date.now() - 86400000), reason: 'Вопрос по услуге' },
        { date: new Date(Date.now() - 172800000), reason: 'Техническая поддержка' }
      ]
    };

    setIncomingCall(mockCallData);
    setIsCallModalOpen(true);

    // Play notification sound (mock)
    toast({
      title: "Входящий звонок",
      description: `Звонок от ${mockCallData.callerNumber}`,
      duration: 5000,
    });
  };

  const loadOperatorStats = () => {
    // Mock operator statistics for today
    setTodayStats({
      totalCalls: Math.floor(Math.random() * 50) + 20,
      answeredCalls: Math.floor(Math.random() * 45) + 18,
      missedCalls: Math.floor(Math.random() * 5) + 1,
      avgCallDuration: Math.floor(Math.random() * 300) + 180, // 3-8 minutes
      totalTalkTime: Math.floor(Math.random() * 7200) + 3600 // 1-3 hours
    });

    // Mock recent calls
    const mockRecentCalls = Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      time: new Date(Date.now() - i * 1800000), // 30 minutes ago each
      number: `+7${Math.floor(Math.random() * 9000000000) + 1000000000}`,
      duration: Math.floor(Math.random() * 600) + 60,
      status: Math.random() > 0.2 ? 'answered' : 'missed',
      category: ['Техподдержка', 'Продажи', 'Информация', 'Жалоба'][Math.floor(Math.random() * 4)]
    }));

    setRecentCalls(mockRecentCalls);
  };

  const handleStatusChange = (newStatus) => {
    setOperatorStatus(newStatus);
    
    const statusMessages = {
      available: 'Вы доступны для приема звонков',
      busy: 'Статус изменен на "Занят"',
      break: 'Вы ушли на перерыв',
      offline: 'Вы офлайн'
    };

    toast({
      title: "Статус изменен",
      description: statusMessages[newStatus],
    });
  };

  const handleCallSave = (callData) => {
    // Save call data (mock)
    setTodayStats(prev => ({
      ...prev,
      totalCalls: prev.totalCalls + 1,
      answeredCalls: prev.answeredCalls + 1,
      totalTalkTime: prev.totalTalkTime + callData.duration
    }));

    // Add to recent calls
    const newCall = {
      id: Date.now(),
      time: new Date(),
      number: callData.callerNumber,
      duration: callData.duration,
      status: 'answered',
      category: callData.category || 'Прочее'
    };

    setRecentCalls(prev => [newCall, ...prev.slice(0, 9)]);
    setIncomingCall(null);
  };

  const handleCloseCallModal = () => {
    setIsCallModalOpen(false);
    setIncomingCall(null);
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      available: { variant: 'default', label: 'Доступен', color: 'bg-green-500' },
      busy: { variant: 'destructive', label: 'Занят', color: 'bg-red-500' },
      break: { variant: 'secondary', label: 'Перерыв', color: 'bg-yellow-500' },
      offline: { variant: 'outline', label: 'Офлайн', color: 'bg-gray-500' }
    };
    return statusConfig[status] || statusConfig.offline;
  };

  const statusConfig = getStatusBadge(operatorStatus);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Рабочее место оператора
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Добро пожаловать, {user?.name}!
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${statusConfig.color}`}></div>
            <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => simulateIncomingCall()}
            disabled={incomingCall}
          >
            <Bell className="w-4 h-4 mr-2" />
            Тест звонка
          </Button>
        </div>
      </div>

      {/* Status Control */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>Статус оператора</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={operatorStatus === 'available' ? 'default' : 'outline'}
              onClick={() => handleStatusChange('available')}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Доступен</span>
            </Button>
            <Button
              variant={operatorStatus === 'busy' ? 'default' : 'outline'}
              onClick={() => handleStatusChange('busy')}
              className="flex items-center space-x-2"
            >
              <Phone className="w-4 h-4" />
              <span>Занят</span>
            </Button>
            <Button
              variant={operatorStatus === 'break' ? 'default' : 'outline'}
              onClick={() => handleStatusChange('break')}
              className="flex items-center space-x-2"
            >
              <Clock className="w-4 h-4" />
              <span>Перерыв</span>
            </Button>
            <Button
              variant={operatorStatus === 'offline' ? 'default' : 'outline'}
              onClick={() => handleStatusChange('offline')}
              className="flex items-center space-x-2"
            >
              <PhoneOff className="w-4 h-4" />
              <span>Офлайн</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Today's Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Phone className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Всего звонков</p>
                <p className="text-2xl font-bold">{todayStats.totalCalls}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Отвечено</p>
                <p className="text-2xl font-bold">{todayStats.answeredCalls}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Пропущено</p>
                <p className="text-2xl font-bold">{todayStats.missedCalls}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Ср. длительность</p>
                <p className="text-2xl font-bold">{formatDuration(todayStats.avgCallDuration)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Headphones className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Время разговоров</p>
                <p className="text-2xl font-bold">{formatDuration(todayStats.totalTalkTime)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Calls */}
      <Card>
        <CardHeader>
          <CardTitle>Последние звонки</CardTitle>
          <CardDescription>История ваших звонков за сегодня</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Время</TableHead>
                  <TableHead>Номер</TableHead>
                  <TableHead>Длительность</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Категория</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentCalls.map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="text-sm">
                      {call.time.toLocaleTimeString('ru-RU')}
                    </TableCell>
                    <TableCell className="font-mono">
                      {call.number}
                    </TableCell>
                    <TableCell>
                      {formatDuration(call.duration)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={call.status === 'answered' ? 'default' : 'destructive'}>
                        {call.status === 'answered' ? 'Отвечен' : 'Пропущен'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{call.category}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {recentCalls.length === 0 && (
            <div className="text-center py-12">
              <Phone className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">
                Пока нет звонков за сегодня
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Call Modal */}
      <CallModal
        isOpen={isCallModalOpen}
        onClose={handleCloseCallModal}
        callData={incomingCall}
        onSaveCall={handleCallSave}
      />
    </div>
  );
};

export default OperatorDashboard;