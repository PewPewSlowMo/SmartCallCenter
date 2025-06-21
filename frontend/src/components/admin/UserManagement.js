import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { useToast } from '../../hooks/use-toast';
import { adminAPI } from '../../services/api';
import { 
  Users, 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  Phone, 
  UserPlus,
  Shield,
  Eye,
  EyeOff
} from 'lucide-react';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [operatorExtensions, setOperatorExtensions] = useState({}); // Хранение extensions операторов
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    name: '',
    password: '',
    role: 'operator',
    group_id: '',
    extension: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadUsers();
    loadGroups();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const result = await adminAPI.getUsers();
      if (result.success) {
        setUsers(result.data);
        
        // Загружаем extensions для операторов
        const extensions = {};
        for (const user of result.data) {
          if (user.role === 'operator') {
            const operatorResult = await adminAPI.getUserOperatorInfo(user.id);
            if (operatorResult.success && operatorResult.data) {
              extensions[user.id] = operatorResult.data.extension;
            }
          }
        }
        setOperatorExtensions(extensions);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      toast({
        title: "Ошибка загрузки",
        description: "Не удалось загрузить список пользователей",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadGroups = async () => {
    try {
      const result = await adminAPI.getGroups();
      if (result.success) {
        setGroups(result.data);
      }
    } catch (error) {
      console.error("Failed to load groups:", error);
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      name: '',
      password: '',
      role: 'operator',
      group_id: '',
      extension: ''
    });
    setEditingUser(null);
    setShowCreateForm(false);
    setShowPassword(false);
  };

  const handleCreateUser = async () => {
    if (!formData.username || !formData.email || !formData.name || !formData.password) {
      toast({
        title: "Ошибка валидации",
        description: "Заполните все обязательные поля",
        variant: "destructive"
      });
      return;
    }

    // Валидация extension для операторов
    if (formData.role === 'operator' && !formData.extension) {
      toast({
        title: "Ошибка валидации",
        description: "Для операторов обязательно указание внутреннего номера",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const userData = { ...formData };
      if (formData.role !== 'operator') {
        delete userData.extension; // Убираем extension для не-операторов
      }

      const result = await adminAPI.createUser(userData);
      if (result.success) {
        toast({
          title: "Пользователь создан",
          description: `Пользователь ${formData.name} успешно создан`,
        });
        resetForm();
        loadUsers();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      toast({
        title: "Ошибка создания",
        description: error.message || "Не удалось создать пользователя",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user) => {
    setFormData({
      username: user.username,
      email: user.email,
      name: user.name,
      password: '',
      role: user.role,
      group_id: user.group_id || '',
      extension: '' // Extension загрузится отдельно
    });
    setEditingUser(user);
    setShowCreateForm(true);
  };

  const handleUpdateUser = async () => {
    if (!formData.username || !formData.email || !formData.name) {
      toast({
        title: "Ошибка валидации",
        description: "Заполните все обязательные поля",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const updateData = {
        username: formData.username,
        email: formData.email,
        name: formData.name,
        role: formData.role,
        group_id: formData.group_id || null
      };

      if (formData.password) {
        updateData.password = formData.password;
      }

      const result = await adminAPI.updateUser(editingUser.id, updateData);
      if (result.success) {
        toast({
          title: "Пользователь обновлен",
          description: `Данные пользователя ${formData.name} успешно обновлены`,
        });
        resetForm();
        loadUsers();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      toast({
        title: "Ошибка обновления",
        description: error.message || "Не удалось обновить пользователя",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Вы уверены, что хотите удалить пользователя ${user.name}?`)) {
      return;
    }

    setLoading(true);
    try {
      const result = await adminAPI.deleteUser(user.id);
      if (result.success) {
        toast({
          title: "Пользователь удален",
          description: `Пользователь ${user.name} успешно удален`,
        });
        loadUsers();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      toast({
        title: "Ошибка удаления",
        description: error.message || "Не удалось удалить пользователя",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getRoleBadge = (role) => {
    const roleConfig = {
      admin: { label: 'Администратор', variant: 'destructive' },
      manager: { label: 'Менеджер', variant: 'default' },
      supervisor: { label: 'Супервайзер', variant: 'secondary' },
      operator: { label: 'Оператор', variant: 'outline' }
    };

    const config = roleConfig[role] || { label: role, variant: 'outline' };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getGroupName = (groupId) => {
    const group = groups.find(g => g.id === groupId);
    return group ? group.name : 'Не назначена';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Управление пользователями
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Создание и управление пользователями системы
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} disabled={loading}>
          <UserPlus className="w-4 h-4 mr-2" />
          Создать пользователя
        </Button>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <UserPlus className="w-5 h-5" />
              <span>{editingUser ? 'Редактировать пользователя' : 'Создать пользователя'}</span>
            </CardTitle>
            <CardDescription>
              {editingUser ? 'Изменение данных пользователя' : 'Создание нового пользователя системы'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">Логин пользователя *</Label>
                <Input
                  id="username"
                  placeholder="admin, operator1, manager"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="user@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Полное имя *</Label>
                <Input
                  id="name"
                  placeholder="Иван Петров"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Пароль {editingUser ? '' : '*'}</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder={editingUser ? "Оставьте пустым для сохранения текущего" : "Введите пароль"}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="role">Роль *</Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({...formData, role: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="operator">Оператор</SelectItem>
                    <SelectItem value="supervisor">Супервайзер</SelectItem>
                    <SelectItem value="manager">Менеджер</SelectItem>
                    <SelectItem value="admin">Администратор</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="group">Группа</Label>
                <Select
                  value={formData.group_id}
                  onValueChange={(value) => setFormData({...formData, group_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите группу" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Без группы</SelectItem>
                    {groups.map(group => (
                      <SelectItem key={group.id} value={group.id}>
                        {group.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {formData.role === 'operator' && (
              <div className="space-y-2">
                <Label htmlFor="extension" className="flex items-center space-x-2">
                  <Phone className="w-4 h-4" />
                  <span>Внутренний номер (Extension) *</span>
                </Label>
                <Input
                  id="extension"
                  placeholder="1001, 1002, 2001"
                  value={formData.extension}
                  onChange={(e) => setFormData({...formData, extension: e.target.value})}
                />
                <p className="text-xs text-slate-500">
                  Номер extension в конфигурации Asterisk для данного оператора
                </p>
              </div>
            )}

            <div className="flex space-x-2 pt-4">
              <Button 
                onClick={editingUser ? handleUpdateUser : handleCreateUser} 
                disabled={loading}
              >
                <Save className="w-4 h-4 mr-2" />
                {editingUser ? 'Обновить' : 'Создать'}
              </Button>
              <Button variant="outline" onClick={resetForm}>
                <X className="w-4 h-4 mr-2" />
                Отмена
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Users List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5" />
            <span>Пользователи системы</span>
          </CardTitle>
          <CardDescription>
            Список всех пользователей с их ролями и параметрами
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2 text-slate-500">Загрузка пользователей...</p>
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 mb-4">Пользователи не найдены</p>
              <Button onClick={() => setShowCreateForm(true)}>
                <UserPlus className="w-4 h-4 mr-2" />
                Создать первого пользователя
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-medium">Пользователь</th>
                    <th className="text-left p-3 font-medium">Роль</th>
                    <th className="text-left p-3 font-medium">Группа</th>
                    <th className="text-left p-3 font-medium">Extension</th>
                    <th className="text-left p-3 font-medium">Статус</th>
                    <th className="text-left p-3 font-medium">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b hover:bg-slate-50 dark:hover:bg-slate-900">
                      <td className="p-3">
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-slate-500">{user.email}</div>
                          <div className="text-xs text-slate-400">@{user.username}</div>
                        </div>
                      </td>
                      <td className="p-3">
                        {getRoleBadge(user.role)}
                      </td>
                      <td className="p-3 text-sm">
                        {getGroupName(user.group_id)}
                      </td>
                      <td className="p-3">
                        {user.role === 'operator' ? (
                          <div className="flex items-center space-x-1">
                            <Phone className="w-3 h-3 text-blue-500" />
                            <span className="text-sm font-mono">
                              {operatorExtensions[user.id] || "Не назначен"}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-sm">N/A</span>
                        )}
                      </td>
                      <td className="p-3">
                        <Badge variant={user.is_active ? "default" : "destructive"}>
                          {user.is_active ? "Активен" : "Неактивен"}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditUser(user)}
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                          {user.role !== 'admin' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteUser(user)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default UserManagement;