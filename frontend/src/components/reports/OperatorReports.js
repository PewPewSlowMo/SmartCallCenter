import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { 
  Users, 
  Download, 
  Search, 
  TrendingUp,
  TrendingDown,
  Phone,
  Clock,
  CheckCircle,
  XCircle,
  Filter
} from 'lucide-react';
import { generateOperatorReport, mockGroups, mockCalls } from '../../mock/mockData';

const OperatorReports = () => {
  const { user, hasPermission } = useAuth();
  const [reportData, setReportData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('all');
  const [sortBy, setSortBy] = useState('totalCalls');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    loadReportData();
  }, []);

  useEffect(() => {
    filterAndSortData();
  }, [reportData, searchTerm, selectedGroup, sortBy, sortOrder]);

  const loadReportData = () => {
    setLoading(true);
    setTimeout(() => {
      const data = generateOperatorReport(mockCalls);
      setReportData(data);
      setLoading(false);
    }, 500);
  };

  const filterAndSortData = () => {
    let filtered = [...reportData];

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(operator => 
        operator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        operator.group.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by group
    if (selectedGroup !== 'all') {
      const groupName = mockGroups.find(g => g.id === selectedGroup)?.name;
      filtered = filtered.filter(operator => operator.group === groupName);
    }

    // Sort data
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredData(filtered);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleExport = (format) => {
    // Mock export functionality
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `operator_report_${timestamp}.${format}`;
    
    if (format === 'csv') {
      const headers = ['Имя', 'Группа', 'Всего звонков', 'Отвечено', 'Пропущено', 'Ср. время разговора', 'Эффективность'];
      const csvContent = [
        headers.join(','),
        ...filteredData.map(op => [
          op.name,
          op.group,
          op.totalCalls,
          op.answeredCalls,
          op.missedCalls,
          formatTime(op.avgTalkTime),
          `${op.efficiency}%`
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
      // Mock PDF export
      alert(`Экспорт в PDF: ${filename}\nФункция будет реализована в backend версии`);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEfficiencyBadge = (efficiency) => {
    if (efficiency >= 85) return 'default';
    if (efficiency >= 70) return 'secondary';
    return 'destructive';
  };

  const SortableHeader = ({ field, children }) => (
    <TableHead 
      className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        {sortBy === field && (
          sortOrder === 'asc' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />
        )}
      </div>
    </TableHead>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Отчеты по операторам
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Производительность и статистика работы операторов
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
                  placeholder="Поиск по имени или группе..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            {hasPermission('supervisor') && (
              <div className="space-y-2">
                <Select value={selectedGroup} onValueChange={setSelectedGroup}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Выберите группу" />
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
          </div>
        </CardContent>
      </Card>

      {/* Report Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Всего операторов</p>
                <p className="text-2xl font-bold">{filteredData.length}</p>
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
                  {filteredData.reduce((sum, op) => sum + op.totalCalls, 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Отвечено звонков</p>
                <p className="text-2xl font-bold">
                  {filteredData.reduce((sum, op) => sum + op.answeredCalls, 0)}
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
                <p className="text-sm text-slate-600 dark:text-slate-400">Средняя эффективность</p>
                <p className="text-2xl font-bold">
                  {filteredData.length > 0 
                    ? Math.round(filteredData.reduce((sum, op) => sum + op.efficiency, 0) / filteredData.length)
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
          <CardTitle>Детальная статистика операторов</CardTitle>
          <CardDescription>
            Показано {filteredData.length} из {reportData.length} операторов
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
                    <SortableHeader field="name">Имя оператора</SortableHeader>
                    <SortableHeader field="group">Группа</SortableHeader>
                    <SortableHeader field="totalCalls">Всего звонков</SortableHeader>
                    <SortableHeader field="answeredCalls">Отвечено</SortableHeader>
                    <SortableHeader field="missedCalls">Пропущено</SortableHeader>
                    <SortableHeader field="avgTalkTime">Ср. время разговора</SortableHeader>
                    <SortableHeader field="efficiency">Эффективность</SortableHeader>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.map((operator) => (
                    <TableRow key={operator.id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-xs font-semibold">
                              {operator.name.charAt(0)}
                            </span>
                          </div>
                          <span>{operator.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{operator.group}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Phone className="w-4 h-4 text-slate-400" />
                          <span>{operator.totalCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>{operator.answeredCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <XCircle className="w-4 h-4 text-red-500" />
                          <span>{operator.missedCalls}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Clock className="w-4 h-4 text-slate-400" />
                          <span>{formatTime(operator.avgTalkTime)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getEfficiencyBadge(operator.efficiency)}>
                          {operator.efficiency}%
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
              <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">
                {searchTerm || selectedGroup !== 'all' 
                  ? 'Нет операторов, соответствующих выбранным фильтрам'
                  : 'Нет данных для отображения'
                }
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default OperatorReports;