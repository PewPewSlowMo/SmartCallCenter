import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { useToast } from '../../hooks/use-toast';
import { adminAPI } from '../../services/api';
import { 
  Settings, 
  Server, 
  Database, 
  Phone, 
  Shield,
  Save,
  TestTube,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Network,
  Users,
  Lock
} from 'lucide-react';

const AdminSettings = () => {
  const [asteriskConfig, setAsteriskConfig] = useState({
    host: '',
    port: '5038',
    username: '',
    password: '',
    protocol: 'AMI',
    timeout: '30'
  });

  const [databaseConfig, setDatabaseConfig] = useState({
    host: 'localhost',
    port: '27017',
    database: 'callcenter',
    username: '',
    password: '',
    connectionString: ''
  });

  const [systemSettings, setSystemSettings] = useState({
    callRecording: true,
    autoAnswerDelay: '3',
    maxCallDuration: '3600',
    queueTimeout: '300',
    callbackEnabled: true,
    smsNotifications: false,
    emailNotifications: true
  });

  const [connectionStatus, setConnectionStatus] = useState({
    asterisk: 'disconnected', // connected, disconnected, testing
    database: 'connected',
    api: 'connected'
  });

  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    
    try {
      const result = await adminAPI.getSystemSettings();
      if (result.success && result.data) {
        const settings = result.data;
        
        // Update asterisk config
        if (settings.asterisk_config) {
          setAsteriskConfig({
            host: settings.asterisk_config.host,
            port: settings.asterisk_config.port.toString(),
            username: settings.asterisk_config.username,
            password: '••••••••', // Don't show real password
            protocol: settings.asterisk_config.protocol,
            timeout: settings.asterisk_config.timeout.toString()
          });
        }
        
        // Update system settings
        setSystemSettings({
          callRecording: settings.call_recording,
          autoAnswerDelay: settings.auto_answer_delay.toString(),
          maxCallDuration: settings.max_call_duration.toString(),
          queueTimeout: settings.queue_timeout.toString(),
          callbackEnabled: settings.callback_enabled,
          smsNotifications: settings.sms_notifications,
          emailNotifications: settings.email_notifications
        });
      }
    } catch (error) {
      toast({
        title: "Ошибка загрузки",
        description: "Не удалось загрузить настройки системы",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const testAsteriskConnection = async () => {
    setConnectionStatus(prev => ({ ...prev, asterisk: 'testing' }));
    
    try {
      const result = await adminAPI.testAsteriskConnection({
        host: asteriskConfig.host,
        port: parseInt(asteriskConfig.port),
        username: asteriskConfig.username,
        password: asteriskConfig.password,
        protocol: asteriskConfig.protocol,
        timeout: parseInt(asteriskConfig.timeout)
      });
      
      const success = result.success && result.data && result.data.success;
      
      setConnectionStatus(prev => ({ 
        ...prev, 
        asterisk: success ? 'connected' : 'disconnected' 
      }));
      
      toast({
        title: success ? "Соединение установлено" : "Ошибка соединения",
        description: success 
          ? result.data.message 
          : result.data?.message || "Не удалось подключиться к серверу Asterisk",
        variant: success ? "default" : "destructive"
      });
    } catch (error) {
      setConnectionStatus(prev => ({ ...prev, asterisk: 'disconnected' }));
      toast({
        title: "Ошибка соединения",
        description: "Не удалось протестировать соединение с Asterisk",
        variant: "destructive"
      });
    }
  };

  const testDatabaseConnection = async () => {
    try {
      const result = await adminAPI.getSystemInfo();
      if (result.success && result.data) {
        toast({
          title: "База данных",
          description: `Соединение активно. Пользователей: ${result.data.users}, Звонков сегодня: ${result.data.calls_today}`,
        });
      } else {
        toast({
          title: "База данных",
          description: "Ошибка подключения к базе данных",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "База данных", 
        description: "Ошибка тестирования соединения с БД",
        variant: "destructive"
      });
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    
    try {
      const settingsToSave = {
        call_recording: systemSettings.callRecording,
        auto_answer_delay: parseInt(systemSettings.autoAnswerDelay),
        max_call_duration: parseInt(systemSettings.maxCallDuration),
        queue_timeout: parseInt(systemSettings.queueTimeout),
        callback_enabled: systemSettings.callbackEnabled,
        sms_notifications: systemSettings.smsNotifications,
        email_notifications: systemSettings.emailNotifications,
        asterisk_config: {
          host: asteriskConfig.host,
          port: parseInt(asteriskConfig.port),
          username: asteriskConfig.username,
          password: asteriskConfig.password,
          protocol: asteriskConfig.protocol,
          timeout: parseInt(asteriskConfig.timeout),
          enabled: asteriskConfig.host && asteriskConfig.username
        }
      };
      
      const result = await adminAPI.updateSystemSettings(settingsToSave);
      
      if (result.success) {
        toast({
          title: "Настройки сохранены",
          description: "Конфигурация системы успешно обновлена",
        });
      } else {
        throw new Error(result.error || "Ошибка сохранения настроек");
      }
    } catch (error) {
      toast({
        title: "Ошибка сохранения",
        description: error.message || "Не удалось сохранить настройки",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'testing':
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      case 'disconnected':
      default:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'connected':
        return <Badge variant="default">Подключено</Badge>;
      case 'testing':
        return <Badge variant="secondary">Тестирование...</Badge>;
      case 'disconnected':
      default:
        return <Badge variant="destructive">Отключено</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Smart Колл Центр
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Конфигурация интеграции с Asterisk и системных параметров
          </p>
        </div>
        <Button onClick={saveSettings} disabled={loading}>
          <Save className="w-4 h-4 mr-2" />
          {loading ? 'Сохранение...' : 'Сохранить настройки'}
        </Button>
      </div>

      {/* Connection Status Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="w-5 h-5" />
            <span>Статус подключений</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="flex items-center space-x-3">
                <Phone className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium">Asterisk</p>
                  <p className="text-xs text-slate-500">AMI соединение</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(connectionStatus.asterisk)}
                {getStatusBadge(connectionStatus.asterisk)}
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-green-500" />
                <div>
                  <p className="font-medium">База данных</p>
                  <p className="text-xs text-slate-500">MongoDB</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(connectionStatus.database)}
                {getStatusBadge(connectionStatus.database)}
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div className="flex items-center space-x-3">
                <Server className="w-5 h-5 text-purple-500" />
                <div>
                  <p className="font-medium">API</p>
                  <p className="text-xs text-slate-500">Backend сервис</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(connectionStatus.api)}
                {getStatusBadge(connectionStatus.api)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Asterisk Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Phone className="w-5 h-5" />
            <span>Конфигурация Asterisk</span>
          </CardTitle>
          <CardDescription>
            Настройки подключения к серверу Asterisk через AMI (Asterisk Manager Interface)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="asterisk-host">Хост сервера</Label>
              <Input
                id="asterisk-host"
                placeholder="192.168.1.100 или asterisk.company.com"
                value={asteriskConfig.host}
                onChange={(e) => setAsteriskConfig({...asteriskConfig, host: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="asterisk-port">Порт AMI</Label>
              <Input
                id="asterisk-port"
                placeholder="5038"
                value={asteriskConfig.port}
                onChange={(e) => setAsteriskConfig({...asteriskConfig, port: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="asterisk-username">Пользователь AMI</Label>
              <Input
                id="asterisk-username"
                placeholder="admin"
                value={asteriskConfig.username}
                onChange={(e) => setAsteriskConfig({...asteriskConfig, username: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="asterisk-password">Пароль AMI</Label>
              <Input
                id="asterisk-password"
                type="password"
                placeholder="••••••••"
                value={asteriskConfig.password}
                onChange={(e) => setAsteriskConfig({...asteriskConfig, password: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="asterisk-protocol">Протокол</Label>
              <Select
                value={asteriskConfig.protocol}
                onValueChange={(value) => setAsteriskConfig({...asteriskConfig, protocol: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="AMI">AMI (Asterisk Manager Interface)</SelectItem>
                  <SelectItem value="ARI">ARI (Asterisk REST Interface)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="asterisk-timeout">Таймаут (сек)</Label>
              <Input
                id="asterisk-timeout"
                placeholder="30"
                value={asteriskConfig.timeout}
                onChange={(e) => setAsteriskConfig({...asteriskConfig, timeout: e.target.value})}
              />
            </div>
          </div>

          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={testAsteriskConnection}
              disabled={!asteriskConfig.host || !asteriskConfig.username || connectionStatus.asterisk === 'testing'}
            >
              <TestTube className="w-4 h-4 mr-2" />
              Тестировать соединение
            </Button>
          </div>

          {connectionStatus.asterisk === 'disconnected' && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Не удается подключиться к Asterisk. Проверьте настройки подключения и убедитесь, что AMI включен в конфигурации Asterisk.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Database Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="w-5 h-5" />
            <span>Конфигурация базы данных</span>
          </CardTitle>
          <CardDescription>
            Настройки подключения к MongoDB для хранения данных колл-центра
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="db-host">Хост</Label>
              <Input
                id="db-host"
                value={databaseConfig.host}
                onChange={(e) => setDatabaseConfig({...databaseConfig, host: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="db-port">Порт</Label>
              <Input
                id="db-port"
                value={databaseConfig.port}
                onChange={(e) => setDatabaseConfig({...databaseConfig, port: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="db-name">База данных</Label>
              <Input
                id="db-name"
                value={databaseConfig.database}
                onChange={(e) => setDatabaseConfig({...databaseConfig, database: e.target.value})}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="db-connection">Строка подключения (опционально)</Label>
            <Input
              id="db-connection"
              placeholder="mongodb://username:password@host:port/database"
              value={databaseConfig.connectionString}
              onChange={(e) => setDatabaseConfig({...databaseConfig, connectionString: e.target.value})}
            />
          </div>

          <Button
            variant="outline"
            onClick={testDatabaseConnection}
          >
            <TestTube className="w-4 h-4 mr-2" />
            Тестировать соединение
          </Button>
        </CardContent>
      </Card>

      {/* System Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="w-5 h-5" />
            <span>Системные настройки</span>
          </CardTitle>
          <CardDescription>
            Основные параметры работы системы колл-центра
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Call Settings */}
          <div className="space-y-4">
            <h4 className="font-medium flex items-center space-x-2">
              <Phone className="w-4 h-4" />
              <span>Настройки звонков</span>
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="auto-answer-delay">Задержка автоответа (сек)</Label>
                <Input
                  id="auto-answer-delay"
                  value={systemSettings.autoAnswerDelay}
                  onChange={(e) => setSystemSettings({...systemSettings, autoAnswerDelay: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="max-call-duration">Максимальная длительность (сек)</Label>
                <Input
                  id="max-call-duration"
                  value={systemSettings.maxCallDuration}
                  onChange={(e) => setSystemSettings({...systemSettings, maxCallDuration: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="queue-timeout">Таймаут очереди (сек)</Label>
                <Input
                  id="queue-timeout"
                  value={systemSettings.queueTimeout}
                  onChange={(e) => setSystemSettings({...systemSettings, queueTimeout: e.target.value})}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={systemSettings.callRecording}
                  onChange={(e) => setSystemSettings({...systemSettings, callRecording: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Запись звонков</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={systemSettings.callbackEnabled}
                  onChange={(e) => setSystemSettings({...systemSettings, callbackEnabled: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Обратный звонок</span>
              </label>
            </div>
          </div>

          <Separator />

          {/* Notification Settings */}
          <div className="space-y-4">
            <h4 className="font-medium flex items-center space-x-2">
              <Shield className="w-4 h-4" />
              <span>Уведомления</span>
            </h4>
            
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={systemSettings.emailNotifications}
                  onChange={(e) => setSystemSettings({...systemSettings, emailNotifications: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Email уведомления</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={systemSettings.smsNotifications}
                  onChange={(e) => setSystemSettings({...systemSettings, smsNotifications: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">SMS уведомления</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queue Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5" />
            <span>Управление очередями</span>
          </CardTitle>
          <CardDescription>
            Создание и настройка очередей обслуживания
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 mb-4">
              Управление очередями будет реализовано в backend версии
            </p>
            <Button variant="outline" disabled>
              <Settings className="w-4 h-4 mr-2" />
              Настроить очереди
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lock className="w-5 h-5" />
            <span>Безопасность</span>
          </CardTitle>
          <CardDescription>
            Настройки безопасности и доступа к системе
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Lock className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 mb-4">
              Настройки безопасности будут реализованы в backend версии
            </p>
            <Button variant="outline" disabled>
              <Shield className="w-4 h-4 mr-2" />
              Настроить безопасность
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminSettings;