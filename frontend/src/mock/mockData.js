// Mock data for call center analytics
export const mockUsers = [
  {
    id: '1',
    username: 'admin@callcenter.com',
    password: 'admin123',
    name: 'Администратор',
    role: 'admin',
    groupId: null
  },
  {
    id: '2',
    username: 'manager@callcenter.com',
    password: 'manager123',
    name: 'Менеджер Иван',
    role: 'manager',
    groupId: null
  },
  {
    id: '3',
    username: 'supervisor@callcenter.com',
    password: 'supervisor123',
    name: 'Супервайзер Анна',
    role: 'supervisor',
    groupId: '1'
  },
  {
    id: '4',
    username: 'operator@callcenter.com',
    password: 'operator123',
    name: 'Оператор Петр',
    role: 'operator',
    groupId: '1'
  }
];

export const mockGroups = [
  { id: '1', name: 'Группа поддержки' },
  { id: '2', name: 'Группа продаж' },
  { id: '3', name: 'VIP группа' }
];

export const mockQueues = [
  { id: '1', name: 'Основная очередь' },
  { id: '2', name: 'Техподдержка' },
  { id: '3', name: 'Продажи' },
  { id: '4', name: 'VIP клиенты' }
];

export const mockOperators = [
  { id: '1', name: 'Петр Иванов', groupId: '1', status: 'online' },
  { id: '2', name: 'Мария Сидорова', groupId: '1', status: 'busy' },
  { id: '3', name: 'Алексей Смирнов', groupId: '2', status: 'online' },
  { id: '4', name: 'Елена Козлова', groupId: '2', status: 'offline' },
  { id: '5', name: 'Дмитрий Попов', groupId: '3', status: 'online' }
];

// Generate mock calls data
export const generateMockCalls = (days = 7) => {
  const calls = [];
  const now = new Date();
  
  for (let i = 0; i < days; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    // Generate 50-200 calls per day
    const callsPerDay = Math.floor(Math.random() * 150) + 50;
    
    for (let j = 0; j < callsPerDay; j++) {
      const startTime = new Date(date);
      startTime.setHours(Math.floor(Math.random() * 10) + 8); // 8-18 hours
      startTime.setMinutes(Math.floor(Math.random() * 60));
      startTime.setSeconds(Math.floor(Math.random() * 60));
      
      const waitTime = Math.floor(Math.random() * 300); // 0-5 minutes wait
      const talkTime = Math.floor(Math.random() * 1800) + 60; // 1-30 minutes talk
      const status = Math.random() > 0.15 ? 'answered' : 'missed'; // 85% answered rate
      
      const endTime = new Date(startTime);
      endTime.setSeconds(endTime.getSeconds() + waitTime + (status === 'answered' ? talkTime : 0));
      
      calls.push({
        id: `call_${i}_${j}`,
        callerNumber: `+7${Math.floor(Math.random() * 9000000000) + 1000000000}`,
        startTime: startTime.toISOString(),
        endTime: endTime.toISOString(),
        waitTime,
        talkTime: status === 'answered' ? talkTime : 0,
        queueId: mockQueues[Math.floor(Math.random() * mockQueues.length)].id,
        agentId: status === 'answered' ? mockOperators[Math.floor(Math.random() * mockOperators.length)].id : null,
        status,
        result: status === 'answered' ? ['resolved', 'escalated', 'callback_requested'][Math.floor(Math.random() * 3)] : null
      });
    }
  }
  
  return calls;
};

export const mockCalls = generateMockCalls(30);

// KPI calculations
export const calculateKPIs = (calls, period = 'today') => {
  const now = new Date();
  let filteredCalls = calls;
  
  switch (period) {
    case 'today':
      filteredCalls = calls.filter(call => {
        const callDate = new Date(call.startTime);
        return callDate.toDateString() === now.toDateString();
      });
      break;
    case 'yesterday':
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      filteredCalls = calls.filter(call => {
        const callDate = new Date(call.startTime);
        return callDate.toDateString() === yesterday.toDateString();
      });
      break;
    case 'week':
      const weekAgo = new Date(now);
      weekAgo.setDate(weekAgo.getDate() - 7);
      filteredCalls = calls.filter(call => new Date(call.startTime) >= weekAgo);
      break;
    case 'month':
      const monthAgo = new Date(now);
      monthAgo.setMonth(monthAgo.getMonth() - 1);
      filteredCalls = calls.filter(call => new Date(call.startTime) >= monthAgo);
      break;
  }
  
  const totalCalls = filteredCalls.length;
  const answeredCalls = filteredCalls.filter(call => call.status === 'answered');
  const missedCalls = filteredCalls.filter(call => call.status === 'missed');
  
  const avgWaitTime = filteredCalls.length > 0 
    ? Math.round(filteredCalls.reduce((sum, call) => sum + call.waitTime, 0) / filteredCalls.length)
    : 0;
    
  const avgTalkTime = answeredCalls.length > 0
    ? Math.round(answeredCalls.reduce((sum, call) => sum + call.talkTime, 0) / answeredCalls.length)
    : 0;
    
  const serviceLevel = totalCalls > 0
    ? Math.round((filteredCalls.filter(call => call.waitTime <= 20).length / totalCalls) * 100)
    : 0;
    
  const answerRate = totalCalls > 0
    ? Math.round((answeredCalls.length / totalCalls) * 100)
    : 0;
  
  return {
    totalCalls,
    answeredCalls: answeredCalls.length,
    missedCalls: missedCalls.length,
    avgWaitTime,
    avgTalkTime,
    serviceLevel,
    answerRate,
    operatorLoad: Math.floor(Math.random() * 30) + 60 // Mock 60-90%
  };
};

// Chart data generators
export const generateChartData = (calls, type = 'hourly') => {
  const now = new Date();
  const today = new Date(now.toDateString());
  
  if (type === 'hourly') {
    const hourlyData = Array.from({ length: 24 }, (_, hour) => ({
      hour: `${hour.toString().padStart(2, '0')}:00`,
      calls: 0,
      answered: 0,
      missed: 0
    }));
    
    calls.filter(call => {
      const callDate = new Date(call.startTime);
      return callDate >= today && callDate < new Date(today.getTime() + 24 * 60 * 60 * 1000);
    }).forEach(call => {
      const hour = new Date(call.startTime).getHours();
      hourlyData[hour].calls++;
      if (call.status === 'answered') {
        hourlyData[hour].answered++;
      } else {
        hourlyData[hour].missed++;
      }
    });
    
    return hourlyData;
  }
  
  if (type === 'daily') {
    const dailyData = Array.from({ length: 7 }, (_, i) => {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      return {
        date: date.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit', month: '2-digit' }),
        calls: 0,
        answered: 0,
        missed: 0
      };
    }).reverse();
    
    calls.forEach(call => {
      const callDate = new Date(call.startTime);
      const dayIndex = Math.floor((now - callDate) / (24 * 60 * 60 * 1000));
      if (dayIndex >= 0 && dayIndex < 7) {
        const dataIndex = 6 - dayIndex;
        dailyData[dataIndex].calls++;
        if (call.status === 'answered') {
          dailyData[dataIndex].answered++;
        } else {
          dailyData[dataIndex].missed++;
        }
      }
    });
    
    return dailyData;
  }
};

// Generate reports data
export const generateOperatorReport = (calls, operatorId = null) => {
  const operators = mockOperators.map(op => {
    const operatorCalls = calls.filter(call => call.agentId === op.id);
    const answered = operatorCalls.filter(call => call.status === 'answered');
    
    return {
      id: op.id,
      name: op.name,
      group: mockGroups.find(g => g.id === op.groupId)?.name || 'Без группы',
      totalCalls: operatorCalls.length,
      answeredCalls: answered.length,
      missedCalls: operatorCalls.length - answered.length,
      avgTalkTime: answered.length > 0 
        ? Math.round(answered.reduce((sum, call) => sum + call.talkTime, 0) / answered.length)
        : 0,
      efficiency: operatorCalls.length > 0 
        ? Math.round((answered.length / operatorCalls.length) * 100)
        : 0
    };
  });
  
  return operatorId ? operators.find(op => op.id === operatorId) : operators;
};