# Smart Call Center - Архитектура и Логика Обработки Звонков

## 📋 Обзор Системы

Smart Call Center использует **гибридный подход** для обработки звонков, сочетающий надежность стандартных очередей Asterisk с гибкостью кастомной логики через ARI (Asterisk REST Interface).

## 🏗️ Архитектурные Компоненты

### 1. **Гибридная Архитектура (Вариант В)**

```
Входящий звонок → Stasis(SmartCallCenter) → Анализ контекста
                                           ↓
                          ┌─────────────────┼─────────────────┐
                          ↓                 ↓                 ↓
                    Queue/Direct      IVR/Service      Error Handling
                         ↓                 ↓                 ↓
                 Asterisk Queue    Custom Logic        Fallback
                         ↓                 ↓                 ↓
                   Real-time         WebSocket         Database
                  Monitoring        Notifications        Logging
```

**Преимущества этого подхода:**
- ✅ Лучшее из двух миров (Asterisk + кастомная логика)
- ✅ Надежность стандартных очередей Asterisk
- ✅ Гибкость кастомного управления
- ✅ Детальная аналитика и мониторинг
- ✅ Возможность переключения между стратегиями

### 2. **Основные Модули**

- **`call_flow_logic.py`** - Вся бизнес-логика маршрутизации
- **`asterisk_event_handler.py`** - Обработка событий ARI в реальном времени
- **`asterisk_database.py`** - Интеграция с asteriskcdrdb
- **`websocket_manager.py`** - Real-time уведомления операторам

## 📞 Логика Обработки Звонков

### **Алгоритм Маршрутизации**

```python
async def determine_call_routing(call_data):
    """
    1. Анализ входящего номера (DID)
    2. Проверка рабочего времени
    3. Определение типа звонка (прямой/очередь/сервисный)
    4. Проверка доступности операторов
    5. Выбор стратегии обработки
    6. Маршрутизация звонка
    """
```

### **Типы Звонков**

| Тип | Описание | Обработка |
|-----|----------|-----------|
| **Direct Extension** | Прямой звонок на extension оператора | Stasis → Dial напрямую |
| **Queue Number** | Звонок в очередь | Stasis → Asterisk Queue |
| **Service Number** | IVR, автоответчик | Stasis → Custom Logic |
| **Unknown** | Неизвестный номер | Стандартная очередь |

### **Стратегии Очередей**

#### **🎯 Рекомендованная: `leastrecent`**
```ini
[queue-support]
strategy = leastrecent
timeout = 25
retry = 3
autopause = yes
ringinuse = no
```

**Почему `leastrecent`:**
- ✅ **Справедливое распределение** - звонит тому, кто дольше всех не получал звонки
- ✅ **Предотвращение выгорания** - равномерная нагрузка на всех операторов
- ✅ **Хорошая мотивация** - операторы знают, что работа распределяется честно
- ✅ **Простая статистика** - легко отслеживать KPI

#### **Альтернативные стратегии:**
- **`fewestcalls`** - для выравнивания количества звонков
- **`linear`** - для разноуровневых команд (junior → senior)
- **`ringall`** - для критически важных линий (VIP)

## 📊 Система Статистики и KPI

### **Логика KPI для Операторов**

**Сценарий:** Звонок в очередь → Оператор1 (не ответил) → Оператор2 (ответил)

**Результат:**
```
Оператор1 KPI:
├── offered_calls: +1    (QueueMemberRingging)
├── answered_calls: 0
└── missed_calls: +1     (таймаут без ответа)

Оператор2 KPI:
├── offered_calls: +1    (QueueMemberRingging)  
├── answered_calls: +1   (BridgeEnter)
└── missed_calls: 0

Общая статистика:
├── total_calls: 1
├── answered_calls: 1    
├── wait_time: X секунд  (QueueCallerJoin → QueueCallerLeave)
└── answer_rate: 100%
```

### **События Asterisk для Статистики**

| Событие | Назначение | Данные |
|---------|------------|--------|
| **QueueCallerJoin** | Старт времени ожидания | `caller_number`, `queue_name`, `position` |
| **QueueCallerLeave** | Завершение ожидания | `reason` (timeout/transfer/hangup) |
| **QueueMemberRingging** | Предложенный звонок оператору | `interface`, `queue_name` → offered_calls++ |
| **BridgeEnter** | Звонок соединен | → answered_calls++ |
| **QueueMemberPause/Unpause** | Статус оператора | Время работы/паузы |

## 🗄️ Гибридная Модель Данных

### **Источники Данных**

```
┌─────────────────┬──────────────────┬─────────────────┐
│   Источник      │    Данные        │   Назначение    │
├─────────────────┼──────────────────┼─────────────────┤
│ SmartCallCenter │ • Детальная      │ • Операторы     │
│ MongoDB         │   статистика     │ • Очереди       │
│                 │ • События ARI    │ • Real-time     │
│                 │ • Комментарии    │ • WebSocket     │
├─────────────────┼──────────────────┼─────────────────┤
│ Asterisk CDR    │ • Базовые        │ • Биллинг       │
│ (asteriskcdrdb) │   телефонные     │ • Совместимость │
│                 │   метрики        │ • Стандарты     │
│                 │ • Совместимость  │ • Интеграции    │
└─────────────────┴──────────────────┴─────────────────┘
```

### **Синхронизация Данных**

1. **Real-time:** События ARI → SmartCallCenter DB
2. **Batch:** Периодическая синхронизация с CDR
3. **Гибридные отчеты:** Объединение данных из обеих источников

## 🔄 Real-time Обработка Событий

### **WebSocket Архитектура**

```
Asterisk ARI ──WebSocket──→ Event Handler ──→ Business Logic
     ↓                           ↓                    ↓
 ARI Events              Call Flow Logic      Database Update
     ↓                           ↓                    ↓
WebSocket Stream        Routing Decision    WebSocket Notifications
     ↓                           ↓                    ↓
Smart Call Center       Execute Action        Frontend Update
```

### **Поток Обработки Звонка**

1. **StasisStart** → Анализ контекста → Решение о маршрутизации
2. **QueueCallerJoin** → Запись в БД → Уведомление супервизорам
3. **QueueMemberRingging** → offered_calls++ → Уведомление оператору
4. **BridgeEnter** → answered_calls++ → Карточка клиента
5. **ChannelStateChange** → Обновление статуса → Real-time метрики
6. **QueueCallerLeave** → Финальная статистика → Отчеты

## 🛠️ Конфигурация Asterisk

### **Файлы Конфигурации**

#### **extensions.conf**
```ini
[internal]
; Все входящие звонки направляются в Stasis
exten => _X.,1,Stasis(SmartCallCenter,${EXTEN})

[from-trunk]  
; Внешние звонки
exten => _X.,1,Set(CALLERID(name)=External Call)
same => n,Goto(internal,${EXTEN},1)
```

#### **queues.conf**
```ini
[support]
strategy = leastrecent
timeout = 25
retry = 3
autopause = yes
ringinuse = no
announce-frequency = 60
announce-position = yes
```

#### **ari.conf**
```ini
[smart-call-center]
type = user
read_only = no
password = Almaty20252025
```

### **Настройка Extensions**

```ini
[pjsip.conf]
[0001]
type=endpoint
auth=0001
aors=0001
context=internal

[0777]
type=endpoint  
auth=0777
aors=0777
context=internal
```

## 📈 Метрики и Производительность

### **Операторские Метрики**

```python
class OperatorKPI:
    offered_calls: int      # QueueMemberRingging
    answered_calls: int     # BridgeEnter
    missed_calls: int       # Timeout без ответа
    avg_talk_time: float    # Среднее время разговора
    online_time: int        # Время в статусе available
    pause_time: int         # Время на паузе
    efficiency: float       # answered/offered * 100
```

### **Очередные Метрики**

```python
class QueueKPI:
    total_calls: int        # QueueCallerJoin
    answered_calls: int     # Successful transfers
    abandoned_calls: int    # QueueCallerLeave(reason=timeout)
    avg_wait_time: float    # Join→Leave time
    service_level: float    # % answered within SLA
    answer_rate: float      # answered/total * 100
```

## 🔧 Настройка Системы

### **1. Базовая Настройка**

```bash
# 1. Настройка Asterisk
systemctl restart asterisk

# 2. Проверка endpoints
asterisk -rx "pjsip show endpoints"

# 3. Проверка ARI
asterisk -rx "ari show users"

# 4. Проверка очередей
asterisk -rx "queue show"
```

### **2. Настройка Smart Call Center**

```python
# config.py
DEFAULT_ASTERISK_HOST = "92.46.62.34"
DEFAULT_ASTERISK_PORT = 8088
DEFAULT_ASTERISK_USERNAME = "smart-call-center"
DEFAULT_ASTERISK_PASSWORD = "Almaty20252025"
PRODUCTION_MODE = True
DISABLE_VIRTUAL_ARI = True
```

### **3. Настройка БД Asterisk**

```python
# Админ панель → Настройки → Asterisk Database
{
    "host": "localhost",
    "port": 3306,
    "username": "asterisk", 
    "password": "password",
    "database": "asteriskcdrdb",
    "db_type": "mysql",
    "enabled": True
}
```

## 🎯 Режимы Работы

### **Продакшн Режим**

- ✅ Подключение к реальному Asterisk (92.46.62.34:8088)
- ✅ Обработка реальных звонков
- ✅ Сохранение в обе БД (SmartCallCenter + CDR)
- ✅ Real-time уведомления операторам
- ✅ Полная статистика и аналитика

### **Тестовый Режим**

- 🧪 Виртуальный ARI для разработки
- 🧪 Имитация событий звонков
- 🧪 Тестирование логики без реального Asterisk

## 📚 API Endpoints

### **Asterisk Integration**
- `GET /api/asterisk/extensions` - Список extensions
- `GET /api/asterisk/realtime-data` - Real-time данные
- `POST /api/asterisk/connect` - Подключение к ARI

### **Database Integration**  
- `GET /api/admin/settings/asterisk-database` - Настройки БД
- `POST /api/admin/settings/asterisk-database/test` - Тест подключения
- `GET /api/admin/reports/cdr-data` - CDR данные
- `GET /api/admin/reports/hybrid-statistics` - Гибридная статистика

### **Setup Wizard**
- `POST /api/setup/asterisk/scan` - Сканирование Asterisk
- `POST /api/setup/operators/migrate` - Миграция операторов
- `POST /api/setup/complete` - Завершение настройки

## 🚀 Запуск в Продакшн

### **Checklist**

1. ✅ **Asterisk настроен** с Stasis приложением SmartCallCenter
2. ✅ **Extensions созданы** для всех операторов  
3. ✅ **Очереди настроены** со стратегией leastrecent
4. ✅ **ARI пользователь** smart-call-center создан
5. ✅ **Smart Call Center** подключен к реальному Asterisk
6. ✅ **База данных** asteriskcdrdb настроена (опционально)
7. ✅ **Операторы созданы** через мастер настройки
8. ✅ **WebSocket соединения** работают
9. ✅ **Тестовые звонки** проходят корректно

### **Мониторинг**

- 📊 **Dashboard** - Real-time метрики системы
- 📈 **Analytics** - Детальная статистика операторов
- 🔍 **Logs** - События ARI и системные логи
- ⚠️ **Alerts** - Уведомления о проблемах

## 🔍 Устранение Неполадок

### **Частые Проблемы**

1. **ARI не подключается**
   - Проверить доступность 92.46.62.34:8088
   - Проверить логин/пароль smart-call-center
   - Проверить настройки HTTP в Asterisk

2. **События не приходят**
   - Проверить Stasis приложение SmartCallCenter
   - Проверить WebSocket соединение
   - Проверить логи `/var/log/supervisor/backend.*.log`

3. **Операторы не получают звонки**
   - Проверить extensions в PJSIP
   - Проверить принадлежность к очередям
   - Проверить статус операторов в системе

### **Логи и Диагностика**

```bash
# Asterisk логи
tail -f /var/log/asterisk/messages

# Smart Call Center логи  
tail -f /var/log/supervisor/backend.*.log

# Состояние очередей
asterisk -rx "queue show"

# Активные каналы
asterisk -rx "core show channels"
```

## 📖 Заключение

Данная архитектура обеспечивает:

- **Надежность** - проверенные очереди Asterisk
- **Гибкость** - кастомная логика через ARI
- **Масштабируемость** - поддержка роста нагрузки
- **Аналитику** - детальная статистика из множественных источников
- **Real-time** - мгновенные уведомления и обновления

Система готова к продакшн использованию и может обрабатывать реальные звонки с полной статистикой и мониторингом.