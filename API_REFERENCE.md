# Smart Call Center - API Reference

## Содержание
1. [Обзор API](#обзор-api)
2. [Авторизация](#авторизация)
3. [Модели данных](#модели-данных)
4. [Endpoints](#endpoints)
5. [WebSocket Events](#websocket-events)
6. [Коды ошибок](#коды-ошибок)
7. [Примеры использования](#примеры-использования)

---

## Обзор API

### Базовая информация
- **Base URL**: `{BACKEND_URL}/api`
- **Протокол**: HTTP/HTTPS
- **Формат данных**: JSON
- **Авторизация**: Bearer JWT Token
- **Версия API**: v1

### Структура URL
```
{BACKEND_URL}/api/{module}/{action}

Примеры:
GET  /api/auth/me
POST /api/admin/users
GET  /api/dashboard/stats
```

### Стандартные заголовки
```http
Content-Type: application/json
Authorization: Bearer {access_token}
Accept: application/json
```

---

## Авторизация

### Получение токена

**POST** `/api/auth/login`

Авторизация пользователя и получение JWT токена.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1440,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@callcenter.com",
    "name": "Системный администратор",
    "role": "admin",
    "group_id": null,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

### Использование токена

После получения токена, включите его в заголовок всех запросов:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Проверка токена

**GET** `/api/auth/me`

Получение информации о текущем пользователе.

**Headers:**
```http
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "email": "admin@callcenter.com",
  "name": "Системный администратор",
  "role": "admin",
  "group_id": null,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Выход из системы

**POST** `/api/auth/logout`

Выход из системы (токен должен быть удален на клиенте).

**Response:**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

---

## Модели данных

### User
```typescript
interface User {
  id: string;                    // UUID
  username: string;              // Уникальный логин
  email: string;                 // Email адрес
  name: string;                  // Полное имя
  role: "admin" | "manager" | "supervisor" | "operator";
  group_id?: string;             // ID группы (опционально)
  is_active: boolean;            // Активен ли пользователь
  created_at: string;            // ISO datetime
  updated_at: string;            // ISO datetime
}
```

### Operator
```typescript
interface Operator {
  id: string;                    // UUID
  user_id: string;               // Связь с User
  extension: string;             // Номер extension в Asterisk
  group_id?: string;             // ID группы
  status: "online" | "busy" | "offline";
  skills: string[];              // Навыки оператора
  max_concurrent_calls: number;  // Макс одновременных звонков
  current_calls: number;         // Текущие звонки
  last_activity: string;         // ISO datetime
  created_at: string;            // ISO datetime
}
```

### Call
```typescript
interface Call {
  id: string;                    // UUID
  channel_id: string;            // ID канала Asterisk
  caller_number: string;         // Номер звонящего
  called_number?: string;        // Вызываемый номер
  operator_id?: string;          // ID оператора (если назначен)
  queue_id?: string;             // ID очереди
  status: "incoming" | "answered" | "completed" | "missed";
  start_time: string;            // ISO datetime
  answer_time?: string;          // ISO datetime
  end_time?: string;             // ISO datetime
  duration?: number;             // Длительность в секундах
  recording_url?: string;        // URL записи
  notes?: string;                // Заметки оператора
  created_at: string;            // ISO datetime
}
```

### Queue
```typescript
interface Queue {
  id: string;                    // UUID
  name: string;                  // Название очереди
  description: string;           // Описание
  asterisk_name: string;         // Имя в Asterisk
  max_wait_time: number;         // Макс время ожидания (сек)
  priority: number;              // Приоритет очереди
  strategy: string;              // Стратегия распределения
  members: string[];             // Участники очереди
  is_active: boolean;
  created_at: string;            // ISO datetime
}
```

### SystemSettings
```typescript
interface SystemSettings {
  call_recording: boolean;
  auto_answer_delay: number;
  max_call_duration: number;
  queue_timeout: number;
  callback_enabled: boolean;
  sms_notifications: boolean;
  email_notifications: boolean;
  asterisk_config: {
    host: string;
    port: number;
    username: string;
    password: string;            // Зашифрован в БД
    protocol: string;
    timeout: number;
    enabled: boolean;
  };
  updated_by: string;            // ID пользователя
  updated_at: string;            // ISO datetime
}
```

---

## Endpoints

### Авторизация (`/api/auth/`)

#### POST `/api/auth/login`
Авторизация пользователя

**Roles**: Все  
**Body**: `{ username: string, password: string }`  
**Response**: JWT токен и информация о пользователе

#### GET `/api/auth/me`
Информация о текущем пользователе

**Roles**: Все (авторизованные)  
**Response**: Данные пользователя

#### POST `/api/auth/logout`
Выход из системы

**Roles**: Все (авторизованные)  
**Response**: Подтверждение выхода

---

### Администрирование (`/api/admin/`)

#### GET `/api/admin/users`
Получение списка пользователей

**Roles**: admin  
**Query Params**:
- `skip`: number = 0 - Пропустить записей
- `limit`: number = 100 - Ограничение записей
- `role`: string - Фильтр по роли

**Response**:
```json
[
  {
    "id": "uuid",
    "username": "operator1",
    "email": "operator1@company.com",
    "name": "Иван Петров",
    "role": "operator",
    "group_id": "group_uuid",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST `/api/admin/users`
Создание нового пользователя

**Roles**: admin  
**Body**:
```json
{
  "username": "operator1",
  "email": "operator1@company.com",
  "name": "Иван Петров",
  "password": "secure_password",
  "role": "operator",
  "group_id": "group_uuid",
  "extension": "1001"
}
```

**Validation**:
- `username`: Уникальный, 3-50 символов
- `email`: Валидный email, уникальный
- `password`: Минимум 6 символов
- `extension`: Обязателен для role = "operator", формат: 3-5 цифр

**Response**: Данные созданного пользователя

#### PUT `/api/admin/users/{user_id}`
Обновление пользователя

**Roles**: admin  
**Path Params**: `user_id` - UUID пользователя  
**Body**: Частичные данные пользователя (без password_hash)

#### DELETE `/api/admin/users/{user_id}`
Удаление пользователя

**Roles**: admin  
**Path Params**: `user_id` - UUID пользователя  
**Note**: Нельзя удалить последнего администратора

#### GET `/api/admin/users/{user_id}/operator`
Получение информации об операторе

**Roles**: admin  
**Path Params**: `user_id` - UUID пользователя  
**Response**: Данные оператора или null

#### GET `/api/admin/settings`
Получение системных настроек

**Roles**: admin  
**Response**: Объект SystemSettings

#### PUT `/api/admin/settings`
Обновление системных настроек

**Roles**: admin  
**Body**: Объект SystemSettings  
**Side Effects**: Автоматическая инициализация ARI клиента при включении Asterisk

#### POST `/api/admin/settings/asterisk/test`
Тестирование подключения к Asterisk

**Roles**: admin  
**Body**:
```json
{
  "host": "192.168.1.100",
  "port": 8088,
  "username": "callcenter_user",
  "password": "secure_password",
  "protocol": "ARI",
  "timeout": 30
}
```

**Response Success**:
```json
{
  "success": true,
  "message": "Успешное подключение к Asterisk 18.20.0",
  "data": {
    "asterisk_version": "18.20.0",
    "system": "Local Asterisk Server",
    "connection_details": {
      "host": "192.168.1.100",
      "port": 8088,
      "protocol": "ARI",
      "status": "Connected"
    }
  }
}
```

**Response Error**:
```json
{
  "success": false,
  "message": "Connection timeout: Не удалось подключиться к 192.168.1.100:8088",
  "data": {
    "error": "Connection timeout",
    "details": {
      "host": "192.168.1.100",
      "port": 8088,
      "possible_causes": [
        "Asterisk сервер не запущен",
        "Неверный порт",
        "Брандмауэр блокирует подключение"
      ]
    },
    "troubleshooting": [
      "Проверьте доступность Asterisk сервера",
      "Убедитесь в корректности учетных данных",
      "Проверьте настройки брандмауэра"
    ]
  }
}
```

#### GET `/api/admin/system/info`
Системная информация

**Roles**: admin  
**Response**:
```json
{
  "users": 15,
  "operators": 8,
  "calls_today": 156,
  "asterisk_connected": true,
  "database_status": "connected",
  "uptime": "2 days, 14:30:22"
}
```

---

### Dashboard (`/api/dashboard/`)

#### GET `/api/dashboard/stats`
Основная статистика

**Roles**: admin, manager, supervisor  
**Query Params**:
- `period`: "today" | "yesterday" | "week" | "month" = "today"
- `group_id`: string - Фильтр по группе (для supervisor)

**Response**:
```json
{
  "total_calls_today": 156,
  "answered_calls_today": 142,
  "missed_calls_today": 14,
  "average_wait_time": 45,
  "service_level": 91.2,
  "active_operators": 8,
  "total_operators": 12,
  "busiest_hour": "14:00",
  "call_trends": [
    {"hour": "09:00", "calls": 23, "answered": 21},
    {"hour": "10:00", "calls": 31, "answered": 29}
  ]
}
```

#### GET `/api/dashboard/realtime`
Данные реального времени

**Roles**: admin, manager, supervisor  
**Response**:
```json
{
  "active_calls": 5,
  "queue_waiting": 2,
  "operators_online": 8,
  "operators_busy": 3,
  "operators_offline": 1,
  "current_hour_calls": 45,
  "timestamp": "2025-01-01T14:30:00Z"
}
```

#### GET `/api/dashboard/call-analytics`
Аналитика звонков

**Roles**: admin, manager, supervisor  
**Query Params**:
- `period`: "today" | "yesterday" | "week" | "month" = "today"
- `group_id`: string

**Response**:
```json
{
  "hourly_distribution": [
    {"hour": "09:00", "incoming": 23, "answered": 21, "missed": 2}
  ],
  "queue_performance": [
    {
      "queue_name": "general",
      "calls": 89,
      "answered": 84,
      "avg_wait_time": 45,
      "service_level": 94.4
    }
  ],
  "operator_summary": [
    {
      "operator_name": "Иван Петров",
      "calls_handled": 34,
      "avg_talk_time": 185,
      "efficiency": 92.1
    }
  ]
}
```

#### GET `/api/dashboard/operator-activity`
Активность операторов

**Roles**: admin, manager, supervisor  
**Response**:
```json
[
  {
    "operator_id": "uuid",
    "name": "Иван Петров",
    "extension": "1001",
    "status": "busy",
    "current_call_duration": 125,
    "calls_today": 28,
    "last_activity": "2025-01-01T14:25:00Z"
  }
]
```

---

### Операторы (`/api/operators/`)

#### GET `/api/operators/`
Список операторов

**Roles**: admin, manager, supervisor  
**Query Params**:
- `group_id`: string - Фильтр по группе
- `status`: "online" | "busy" | "offline" - Фильтр по статусу

**Response**:
```json
[
  {
    "id": "uuid",
    "user_id": "user_uuid",
    "name": "Иван Петров",
    "extension": "1001",
    "status": "online",
    "group_id": "group_uuid",
    "current_calls": 0,
    "calls_today": 28,
    "last_activity": "2025-01-01T14:25:00Z"
  }
]
```

#### PUT `/api/operators/{operator_id}/status`
Изменение статуса оператора

**Roles**: admin, manager, supervisor, operator (свой статус)  
**Path Params**: `operator_id` - UUID оператора  
**Body**:
```json
{
  "status": "online" | "busy" | "offline"
}
```

#### GET `/api/operators/{operator_id}/stats`
Статистика оператора

**Roles**: admin, manager, supervisor, operator (своя статистика)  
**Path Params**: `operator_id` - UUID оператора  
**Query Params**:
- `period`: "today" | "yesterday" | "week" | "month" = "today"

**Response**:
```json
{
  "calls_handled": 34,
  "calls_missed": 2,
  "total_talk_time": 6290,
  "avg_talk_time": 185,
  "efficiency": 92.1,
  "first_call_resolution": 87.5,
  "customer_satisfaction": 4.3
}
```

---

### Звонки (`/api/calls/`)

#### GET `/api/calls/`
История звонков

**Roles**: admin, manager, supervisor, operator (свои звонки)  
**Query Params**:
- `skip`: number = 0
- `limit`: number = 50
- `operator_id`: string - Фильтр по оператору
- `status`: string - Фильтр по статусу
- `date_from`: string - Дата начала (ISO)
- `date_to`: string - Дата окончания (ISO)

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "channel_id": "channel-12345",
      "caller_number": "+79001234567",
      "called_number": "1001",
      "operator_id": "operator_uuid",
      "operator_name": "Иван Петров",
      "queue_id": "queue_uuid",
      "status": "completed",
      "start_time": "2025-01-01T14:25:00Z",
      "answer_time": "2025-01-01T14:25:05Z",
      "end_time": "2025-01-01T14:28:15Z",
      "duration": 190,
      "recording_url": "/recordings/call-12345.wav",
      "notes": "Клиент интересовался услугами"
    }
  ],
  "total": 1205,
  "page": 1,
  "pages": 25
}
```

#### POST `/api/calls/`
Создание записи звонка

**Roles**: admin, system (автоматически)  
**Body**:
```json
{
  "channel_id": "channel-12345",
  "caller_number": "+79001234567",
  "called_number": "1001",
  "queue_id": "queue_uuid",
  "status": "incoming"
}
```

#### PUT `/api/calls/{call_id}`
Обновление записи звонка

**Roles**: admin, operator (свои звонки)  
**Path Params**: `call_id` - UUID звонка  
**Body**: Частичные данные звонка

#### GET `/api/calls/{call_id}`
Детали звонка

**Roles**: admin, manager, supervisor, operator (свои звонки)  
**Path Params**: `call_id` - UUID звонка

#### GET `/api/calls/stats`
Статистика звонков

**Roles**: admin, manager, supervisor  
**Query Params**:
- `period`: "today" | "yesterday" | "week" | "month" = "today"
- `group_id`: string

**Response**:
```json
{
  "total_calls": 156,
  "answered_calls": 142,
  "missed_calls": 14,
  "average_duration": 185,
  "average_wait_time": 45,
  "service_level": 91.2,
  "peak_hour": "14:00",
  "busiest_operators": [
    {
      "operator_name": "Иван Петров",
      "calls_count": 34
    }
  ]
}
```

---

### Очереди (`/api/queues/`)

#### GET `/api/queues/`
Список очередей

**Roles**: admin, manager, supervisor  
**Response**:
```json
[
  {
    "id": "uuid",
    "name": "Основная очередь",
    "description": "Общие входящие звонки",
    "asterisk_name": "general",
    "max_wait_time": 300,
    "priority": 1,
    "strategy": "ringall",
    "members": ["1001", "1002", "1003"],
    "is_active": true,
    "current_calls": 2,
    "waiting_calls": 1
  }
]
```

#### POST `/api/queues/`
Создание очереди

**Roles**: admin  
**Body**:
```json
{
  "name": "VIP клиенты",
  "description": "Приоритетная очередь для VIP",
  "asterisk_name": "vip",
  "max_wait_time": 60,
  "priority": 5,
  "strategy": "leastrecent"
}
```

#### PUT `/api/queues/{queue_id}`
Обновление очереди

**Roles**: admin  
**Path Params**: `queue_id` - UUID очереди

#### DELETE `/api/queues/{queue_id}`
Удаление очереди

**Roles**: admin  
**Path Params**: `queue_id` - UUID очереди

#### GET `/api/queues/{queue_id}/stats`
Статистика очереди

**Roles**: admin, manager, supervisor  
**Path Params**: `queue_id` - UUID очереди  
**Query Params**:
- `period`: "today" | "yesterday" | "week" | "month" = "today"

**Response**:
```json
{
  "calls_entered": 89,
  "calls_answered": 84,
  "calls_abandoned": 5,
  "average_wait_time": 45,
  "max_wait_time": 185,
  "service_level": 94.4,
  "hourly_stats": [
    {
      "hour": "09:00",
      "calls": 12,
      "answered": 11,
      "avg_wait": 35
    }
  ]
}
```

---

### Asterisk интеграция (`/api/asterisk/`)

#### GET `/api/asterisk/extensions`
Список extensions из Asterisk

**Roles**: admin, manager  
**Response**:
```json
[
  {
    "extension": "1001",
    "technology": "PJSIP",
    "state": "NOT_INUSE",
    "contact_status": "Created",
    "contact_uri": "sip:1001@192.168.1.101:5060",
    "last_seen": "2025-01-01T14:30:00Z"
  }
]
```

#### GET `/api/asterisk/queues`
Информация об очередях Asterisk

**Roles**: admin, manager  
**Response**:
```json
[
  {
    "name": "general",
    "strategy": "ringall",
    "members_count": 3,
    "completed_calls": 156,
    "abandoned_calls": 8,
    "service_level": 92,
    "hold_time": 45,
    "talk_time": 235,
    "active_calls": 2,
    "members": [
      {
        "interface": "PJSIP/1001",
        "status": 1,
        "paused": false,
        "calls_taken": 45,
        "last_call": 1704110400
      }
    ]
  }
]
```

#### GET `/api/asterisk/realtime-data`
Данные реального времени от Asterisk

**Roles**: admin, manager, supervisor  
**Response**:
```json
{
  "connected": true,
  "asterisk_version": "18.20.0",
  "active_channels": 5,
  "active_calls": 3,
  "extensions": [
    {
      "name": "PJSIP/1001",
      "state": "NOT_INUSE",
      "class": "SIP"
    }
  ],
  "channels": [
    {
      "id": "channel-12345",
      "name": "PJSIP/79001234567-00000001",
      "state": "Up",
      "caller_number": "+79001234567",
      "duration": "00:03:45"
    }
  ],
  "timestamp": "2025-01-01T14:30:00Z"
}
```

#### POST `/api/asterisk/channels/{channel_id}/answer`
Ответ на звонок

**Roles**: admin, operator  
**Path Params**: `channel_id` - ID канала в Asterisk

#### POST `/api/asterisk/channels/{channel_id}/hangup`
Завершение звонка

**Roles**: admin, operator  
**Path Params**: `channel_id` - ID канала в Asterisk

#### POST `/api/asterisk/originate`
Инициация исходящего звонка

**Roles**: admin, operator  
**Body**:
```json
{
  "endpoint": "PJSIP/1001",
  "context": "internal",
  "extension": "79001234567",
  "priority": 1,
  "timeout": 30
}
```

---

## WebSocket Events

### Подключение
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/events');
ws.onopen = () => {
  console.log('Connected to WebSocket');
};
```

### Авторизация WebSocket
```javascript
// Отправка токена после подключения
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_jwt_token'
}));
```

### События звонков

#### call_started
```json
{
  "type": "call_started",
  "data": {
    "call_id": "uuid",
    "channel_id": "channel-12345",
    "caller_number": "+79001234567",
    "timestamp": "2025-01-01T14:30:00Z"
  }
}
```

#### call_answered
```json
{
  "type": "call_answered",
  "data": {
    "call_id": "uuid",
    "operator_id": "operator_uuid",
    "answer_time": "2025-01-01T14:30:05Z"
  }
}
```

#### call_ended
```json
{
  "type": "call_ended",
  "data": {
    "call_id": "uuid",
    "end_time": "2025-01-01T14:33:15Z",
    "duration": 190,
    "status": "completed"
  }
}
```

### События операторов

#### operator_status_changed
```json
{
  "type": "operator_status_changed",
  "data": {
    "operator_id": "uuid",
    "status": "busy",
    "timestamp": "2025-01-01T14:30:00Z"
  }
}
```

#### operator_logged_in
```json
{
  "type": "operator_logged_in",
  "data": {
    "operator_id": "uuid",
    "extension": "1001",
    "timestamp": "2025-01-01T08:00:00Z"
  }
}
```

---

## Коды ошибок

### HTTP статусы
- **200** - Успешный запрос
- **201** - Ресурс создан
- **400** - Неверный запрос
- **401** - Не авторизован
- **403** - Недостаточно прав
- **404** - Ресурс не найден
- **422** - Ошибка валидации
- **500** - Внутренняя ошибка сервера

### Стандартная структура ошибки
```json
{
  "detail": "Описание ошибки",
  "type": "validation_error",
  "code": "USER_001",
  "field": "username"
}
```

### Коды ошибок приложения

#### Авторизация (AUTH_*)
- **AUTH_001**: Неверные учетные данные
- **AUTH_002**: Токен истек
- **AUTH_003**: Недостаточно прав доступа
- **AUTH_004**: Пользователь неактивен

#### Пользователи (USER_*)
- **USER_001**: Логин уже существует
- **USER_002**: Email уже существует
- **USER_003**: Extension уже назначен
- **USER_004**: Пользователь не найден
- **USER_005**: Нельзя удалить последнего администратора

#### Asterisk (AST_*)
- **AST_001**: Таймаут подключения
- **AST_002**: Ошибка авторизации
- **AST_003**: Неверная конфигурация
- **AST_004**: ARI недоступен
- **AST_005**: Канал не найден

#### База данных (DB_*)
- **DB_001**: Ошибка подключения к БД
- **DB_002**: Запись не найдена
- **DB_003**: Ошибка валидации
- **DB_004**: Нарушение уникальности

### Детальные ошибки валидации
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    }
  ]
}
```

---

## Примеры использования

### JavaScript/TypeScript

#### Базовый API клиент
```typescript
class CallCenterAPI {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async login(username: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      return data;
    }
    throw new Error('Login failed');
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}/api${endpoint}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async getUsers() {
    return this.request('/admin/users');
  }

  async createUser(userData: any) {
    return this.request('/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async getDashboardStats(period = 'today') {
    return this.request(`/dashboard/stats?period=${period}`);
  }
}

// Использование
const api = new CallCenterAPI('http://localhost:8001');

async function example() {
  // Авторизация
  await api.login('admin', 'admin');

  // Получение статистики
  const stats = await api.getDashboardStats('today');
  console.log('Звонков сегодня:', stats.total_calls_today);

  // Создание оператора
  const newOperator = await api.createUser({
    username: 'operator1',
    email: 'operator1@company.com',
    name: 'Иван Петров',
    password: 'secure_password',
    role: 'operator',
    extension: '1001'
  });
}
```

#### React хук для API
```typescript
import { useState, useEffect } from 'react';

function useCallCenterAPI() {
  const [api] = useState(() => new CallCenterAPI(process.env.REACT_APP_BACKEND_URL));
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (username: string, password: string) => {
    try {
      await api.login(username, password);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  return { api, isAuthenticated, login };
}

// Компонент
function Dashboard() {
  const { api, isAuthenticated } = useCallCenterAPI();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      api.getDashboardStats().then(setStats);
    }
  }, [api, isAuthenticated]);

  return (
    <div>
      {stats && (
        <div>
          <h2>Статистика</h2>
          <p>Звонков: {stats.total_calls_today}</p>
          <p>Отвечено: {stats.answered_calls_today}</p>
        </div>
      )}
    </div>
  );
}
```

### Python

#### Пример клиента
```python
import asyncio
import aiohttp
from typing import Optional, Dict, Any

class CallCenterClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        data = {"username": username, "password": password}
        async with self.session.post(f"{self.base_url}/api/auth/login", json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                self.token = result["access_token"]
                return result
            else:
                raise Exception(f"Login failed: {resp.status}")

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async with self.session.request(
            method, f"{self.base_url}/api{endpoint}", headers=headers, **kwargs
        ) as resp:
            if resp.status >= 400:
                raise Exception(f"HTTP {resp.status}: {await resp.text()}")
            return await resp.json()

    async def get_dashboard_stats(self, period: str = "today") -> Dict[str, Any]:
        return await self.request("GET", f"/dashboard/stats?period={period}")

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.request("POST", "/admin/users", json=user_data)

# Использование
async def main():
    async with CallCenterClient("http://localhost:8001") as client:
        # Авторизация
        await client.login("admin", "admin")

        # Получение статистики
        stats = await client.get_dashboard_stats("today")
        print(f"Звонков сегодня: {stats['total_calls_today']}")

        # Создание оператора
        operator = await client.create_user({
            "username": "operator1",
            "email": "operator1@company.com",
            "name": "Иван Петров",
            "password": "secure_password",
            "role": "operator",
            "extension": "1001"
        })
        print(f"Создан оператор: {operator['name']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### cURL примеры

#### Авторизация
```bash
# Авторизация
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Сохранить токен
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')
```

#### Работа с пользователями
```bash
# Получение списка пользователей
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/admin/users

# Создание оператора
curl -X POST http://localhost:8001/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator1",
    "email": "operator1@company.com",
    "name": "Иван Петров",
    "password": "secure_password",
    "role": "operator",
    "extension": "1001"
  }'
```

#### Статистика
```bash
# Dashboard статистика
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/dashboard/stats?period=today"

# Статистика звонков
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/calls/stats?period=week"
```

#### Тестирование Asterisk
```bash
# Тест подключения к Asterisk
curl -X POST http://localhost:8001/api/admin/settings/asterisk/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.1.100",
    "port": 8088,
    "username": "callcenter_user",
    "password": "secure_password",
    "protocol": "ARI",
    "timeout": 30
  }'
```

---

## 🔧 Дополнительные ресурсы

### Swagger/OpenAPI документация
После запуска сервера доступна по адресу:
```
http://localhost:8001/docs
```

### Postman коллекция
Импортируйте коллекцию для быстрого тестирования:
```json
{
  "info": {
    "name": "Smart Call Center API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8001"
    },
    {
      "key": "token",
      "value": ""
    }
  ]
}
```

### Rate Limiting
API использует ограничения частоты запросов:
- **Авторизация**: 5 запросов в минуту
- **Общие API**: 100 запросов в минуту
- **Dashboard**: 60 запросов в минуту

### Версионирование
Текущая версия API: **v1**  
Все endpoints включают версию в пути: `/api/v1/...` (опционально)

---

**Smart Call Center API Reference v1.0**  
*Обновлено: 2025-01-01*
