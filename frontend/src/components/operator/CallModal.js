import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Separator } from '../ui/separator';
import { useToast } from '../../hooks/use-toast';
import { 
  Phone, 
  PhoneCall, 
  PhoneOff, 
  User, 
  Clock, 
  MapPin, 
  History,
  AlertTriangle,
  CheckCircle,
  Save,
  X
} from 'lucide-react';

const CallModal = ({ isOpen, onClose, callData, onSaveCall }) => {
  const [callDetails, setCallDetails] = useState({
    description: '',
    category: '',
    priority: 'medium',
    resolution: '',
    followUpRequired: false,
    customerSatisfaction: '',
    notes: ''
  });
  const [callDuration, setCallDuration] = useState(0);
  const [callStartTime] = useState(new Date());
  const { toast } = useToast();

  useEffect(() => {
    let interval;
    if (isOpen) {
      interval = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      setCallDetails({
        description: '',
        category: '',
        priority: 'medium',
        resolution: '',
        followUpRequired: false,
        customerSatisfaction: '',
        notes: ''
      });
      setCallDuration(0);
    }
  }, [isOpen]);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSave = () => {
    if (!callDetails.description.trim()) {
      toast({
        title: "Ошибка",
        description: "Пожалуйста, введите описание звонка",
        variant: "destructive"
      });
      return;
    }

    const finalCallData = {
      ...callData,
      ...callDetails,
      duration: callDuration,
      endTime: new Date(),
      startTime: callStartTime
    };

    onSaveCall(finalCallData);
    toast({
      title: "Звонок сохранен",
      description: "Информация о звонке успешно сохранена",
    });
    onClose();
  };

  const handleAnswerCall = () => {
    toast({
      title: "Звонок принят",
      description: `Соединение установлено с ${callData?.callerNumber}`,
    });
  };

  const handleDeclineCall = () => {
    toast({
      title: "Звонок отклонен",
      description: "Звонок был отклонен",
      variant: "destructive"
    });
    onClose();
  };

  if (!callData) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Phone className="w-5 h-5 text-blue-500" />
            <span>Входящий звонок</span>
            <Badge variant="outline" className="ml-2">
              {formatDuration(callDuration)}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Управление активным звонком и сбор информации
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Caller Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="w-5 h-5" />
                <span>Информация о звонящем</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-3">
                <Phone className="w-4 h-4 text-slate-500" />
                <div>
                  <Label className="text-sm text-slate-500">Номер телефона</Label>
                  <p className="font-mono font-semibold">{callData.callerNumber}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <MapPin className="w-4 h-4 text-slate-500" />
                <div>
                  <Label className="text-sm text-slate-500">Регион</Label>
                  <p>{callData.region || 'Не определен'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Clock className="w-4 h-4 text-slate-500" />
                <div>
                  <Label className="text-sm text-slate-500">Время звонка</Label>
                  <p>{callStartTime.toLocaleString('ru-RU')}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <History className="w-4 h-4 text-slate-500" />
                <div>
                  <Label className="text-sm text-slate-500">Очередь</Label>
                  <p>{callData.queueName || 'Основная'}</p>
                </div>
              </div>

              {callData.customerInfo && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Данные клиента</Label>
                    <div className="text-sm space-y-1">
                      <p><strong>Имя:</strong> {callData.customerInfo.name}</p>
                      <p><strong>Email:</strong> {callData.customerInfo.email}</p>
                      <p><strong>Статус:</strong> 
                        <Badge variant={callData.customerInfo.vip ? 'default' : 'secondary'} className="ml-2">
                          {callData.customerInfo.vip ? 'VIP' : 'Обычный'}
                        </Badge>
                      </p>
                    </div>
                  </div>
                </>
              )}

              {callData.callHistory && callData.callHistory.length > 0 && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">История звонков</Label>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {callData.callHistory.map((call, index) => (
                        <div key={index} className="text-xs p-2 bg-slate-50 dark:bg-slate-900 rounded">
                          <p>{new Date(call.date).toLocaleDateString('ru-RU')} - {call.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Call Details Form */}
          <Card>
            <CardHeader>
              <CardTitle>Детали звонка</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Описание звонка *</Label>
                <Textarea
                  id="description"
                  placeholder="Опишите суть обращения клиента..."
                  value={callDetails.description}
                  onChange={(e) => setCallDetails({...callDetails, description: e.target.value})}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Категория</Label>
                  <Select
                    value={callDetails.category}
                    onValueChange={(value) => setCallDetails({...callDetails, category: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите категорию" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="support">Техподдержка</SelectItem>
                      <SelectItem value="sales">Продажи</SelectItem>
                      <SelectItem value="complaint">Жалоба</SelectItem>
                      <SelectItem value="info">Информация</SelectItem>
                      <SelectItem value="billing">Биллинг</SelectItem>
                      <SelectItem value="other">Прочее</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Приоритет</Label>
                  <Select
                    value={callDetails.priority}
                    onValueChange={(value) => setCallDetails({...callDetails, priority: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Низкий</SelectItem>
                      <SelectItem value="medium">Средний</SelectItem>
                      <SelectItem value="high">Высокий</SelectItem>
                      <SelectItem value="urgent">Срочный</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="resolution">Решение/Результат</Label>
                <Textarea
                  id="resolution"
                  placeholder="Какое решение было предложено или предпринято..."
                  value={callDetails.resolution}
                  onChange={(e) => setCallDetails({...callDetails, resolution: e.target.value})}
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="satisfaction">Удовлетворенность клиента</Label>
                <Select
                  value={callDetails.customerSatisfaction}
                  onValueChange={(value) => setCallDetails({...callDetails, customerSatisfaction: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Оцените удовлетворенность" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="very_satisfied">Очень доволен</SelectItem>
                    <SelectItem value="satisfied">Доволен</SelectItem>
                    <SelectItem value="neutral">Нейтрально</SelectItem>
                    <SelectItem value="dissatisfied">Недоволен</SelectItem>
                    <SelectItem value="very_dissatisfied">Очень недоволен</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Дополнительные заметки</Label>
                <Textarea
                  id="notes"
                  placeholder="Любые дополнительные заметки о звонке..."
                  value={callDetails.notes}
                  onChange={(e) => setCallDetails({...callDetails, notes: e.target.value})}
                  rows={2}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="followup"
                  checked={callDetails.followUpRequired}
                  onChange={(e) => setCallDetails({...callDetails, followUpRequired: e.target.checked})}
                  className="rounded"
                />
                <Label htmlFor="followup" className="text-sm">
                  Требуется последующий контакт
                </Label>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter className="flex-col sm:flex-row space-y-2 sm:space-y-0">
          <div className="flex space-x-2 w-full sm:w-auto">
            <Button
              variant="default"
              onClick={handleAnswerCall}
              className="flex-1 sm:flex-none bg-green-600 hover:bg-green-700"
            >
              <PhoneCall className="w-4 h-4 mr-2" />
              Принять
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeclineCall}
              className="flex-1 sm:flex-none"
            >
              <PhoneOff className="w-4 h-4 mr-2" />
              Отклонить
            </Button>
          </div>
          
          <div className="flex space-x-2 w-full sm:w-auto">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 sm:flex-none"
            >
              <X className="w-4 h-4 mr-2" />
              Отмена
            </Button>
            <Button
              onClick={handleSave}
              className="flex-1 sm:flex-none"
            >
              <Save className="w-4 h-4 mr-2" />
              Сохранить
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CallModal;