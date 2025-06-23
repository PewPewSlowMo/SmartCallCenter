# 🔧 Smart Call Center - Руководство по установке и настройке

## 📋 Содержание
1. [Системные требования](#системные-требования)
2. [Подготовка окружения](#подготовка-окружения)
3. [Установка компонентов](#установка-компонентов)
4. [Настройка Asterisk](#настройка-asterisk)
5. [Конфигурация системы](#конфигурация-системы)
6. [Тестирование](#тестирование)
7. [Устранение неисправностей](#устранение-неисправностей)

---

## 💻 Системные требования

### Минимальные требования
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- **CPU**: 2 ядра, 2.5 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB свободного места
- **Network**: 100 Mbps

### Рекомендуемые требования
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 ядра, 3.0 GHz
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps

### Программные зависимости
- **Node.js**: 18+ LTS
- **Python**: 3.9+
- **MongoDB**: 5.0+
- **Asterisk**: 18+ или 20+ (опционально)

---

## ⚙️ Подготовка окружения

### Ubuntu/Debian
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых пакетов
sudo apt install -y curl wget git build-essential

# Установка Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Установка Yarn
npm install -g yarn

# Установка Python 3.9+
sudo apt install -y python3 python3-pip python3-venv

# Установка MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt update
sudo apt install -y mongodb-org

# Запуск MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

### CentOS/RHEL
```bash
# Обновление системы
sudo yum update -y

# Установка EPEL и базовых пакетов
sudo yum install -y epel-release
sudo yum groupinstall -y "Development Tools"
sudo yum install -y curl wget git

# Установка Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Установка Yarn
npm install -g yarn

# Установка Python 3.9
sudo yum install -y python39 python39-pip

# Установка MongoDB
sudo tee /etc/yum.repos.d/mongodb-org-5.0.repo << EOF
[mongodb-org-5.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/8/mongodb-org/5.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-5.0.asc
EOF

sudo yum install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Windows
```powershell
# Установка через Chocolatey (рекомендуется)
# Сначала установить Chocolatey: https://chocolatey.org/install

# Установка компонентов
choco install nodejs python mongodb git -y

# Установка Yarn
npm install -g yarn

# Запуск MongoDB как сервис
net start MongoDB
```

---

## 🚀 Установка компонентов

### 1. Клонирование репозитория
```bash
# Клонирование проекта
git clone https://github.com/PewPewSlowMo/SmartCallCenter.git
cd SmartCallCenter

# Проверка структуры
ls -la
# Должны быть: backend/, frontend/, docs/, etc.
```

### 2. Настройка Backend
```bash
cd backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Создание конфигурационного файла
cp .env.example .env
```

**Редактирование .env файла:**
```bash
nano .env
```

```env
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=callcenter

# JWT Configuration
JWT_SECRET_KEY=generate-secure-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
DEBUG=False
LOG_LEVEL=INFO

# Asterisk Configuration (опционально)
DEFAULT_ASTERISK_HOST=192.168.1.100
DEFAULT_ASTERISK_PORT=8088
```

**Генерация секретного ключа:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Настройка Frontend
```bash
cd ../frontend

# Установка зависимостей
yarn install

# Создание локального конфига
cp .env.example .env.local
```

**Редактирование .env.local:**
```bash
nano .env.local
```

```env
# Backend URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Development Settings
WDS_SOCKET_PORT=3000
FAST_REFRESH=true
GENERATE_SOURCEMAP=false
```

### 4. Инициализация базы данных
```bash
# Проверка подключения к MongoDB
mongo --eval "db.adminCommand('ismaster')"

# Создание базы данных (выполнится автоматически при первом запуске)
cd ../backend
python3 -c "
import asyncio
from server import initialize_default_data
from database import DatabaseManager
import os
from dotenv import load_dotenv

async def init_db():
    load_dotenv()
    db = DatabaseManager()
    await db.connect()
    await initialize_default_data(db)
    await db.disconnect()
    print('✅ База данных инициализирована')

asyncio.run(init_db())
"
```

---

## ☎️ Настройка Asterisk

### Установка Asterisk (опционально)

**Ubuntu/Debian:**
```bash
# Установка Asterisk
sudo apt install -y asterisk

# Или компиляция из исходников для последней версии
cd /usr/src
sudo wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz
sudo tar -xzf asterisk-20-current.tar.gz
cd asterisk-20.*/

# Установка зависимостей
sudo contrib/scripts/install_prereq install

# Конфигурация и компиляция
sudo ./configure
sudo make menuselect  # Выбрать нужные модули
sudo make -j$(nproc)
sudo make install
sudo make samples
sudo make config
```

### Конфигурация ARI

#### 1. Настройка http.conf
```bash
sudo nano /etc/asterisk/http.conf
```

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
prefix = asterisk

; Для продакшн - ограничить доступ
; bindaddr = 127.0.0.1
```

#### 2. Настройка ari.conf
```bash
sudo nano /etc/asterisk/ari.conf
```

```ini
[general]
enabled = yes
; Для безопасности в продакшн
; allowmultiplelogin = no

[callcenter_admin]
type = user
read_only = no
password = CallCenter2025!
; Полные права для администрирования

[callcenter_readonly]
type = user
read_only = yes
password = ReadOnly2025!
; Только чтение для мониторинга
```

#### 3. Настройка extensions.conf
```bash
sudo nano /etc/asterisk/extensions.conf
```

```ini
; Контекст для Smart Call Center
[smart-callcenter]
; Входящие звонки передаются в Stasis приложение
exten => _X.,1,NoOp(Smart Call Center: ${CALLERID(num)} -> ${EXTEN})
 same => n,Set(CHANNEL(hangup_handler_wipe)=stasis_hangup,s,1)
 same => n,Stasis(smart-call-center,${EXTEN},${CALLERID(num)})
 same => n,Hangup()

; Обработчик завершения вызова
[stasis_hangup]
exten => s,1,NoOp(Call hangup: ${CHANNEL})

; Внутренние extensions
[internal]
exten => 1001,1,Dial(PJSIP/1001,30,tT)
 same => n,Goto(smart-callcenter,${EXTEN},1)

exten => 1002,1,Dial(PJSIP/1002,30,tT)
 same => n,Goto(smart-callcenter,${EXTEN},1)

exten => 1003,1,Dial(PJSIP/1003,30,tT)
 same => n,Goto(smart-callcenter,${EXTEN},1)

; Включение контекстов
include => smart-callcenter
```

#### 4. Настройка pjsip.conf (для SIP endpoints)
```bash
sudo nano /etc/asterisk/pjsip.conf
```

```ini
[transport-udp]
type = transport
protocol = udp
bind = 0.0.0.0

; Шаблон для операторов
[operator-template](!)
type = endpoint
transport = transport-udp
context = internal
disallow = all
allow = ulaw,alaw,g722
auth = operator-auth
aors = operator-aor

[operator-auth](!)
type = auth
auth_type = userpass

[operator-aor](!)
type = aor
max_contacts = 1

; Операторы
[1001](operator-template)
auth = 1001-auth
aors = 1001-aor

[1001-auth](operator-auth)
password = operator1001
username = 1001

[1001-aor](operator-aor)

[1002](operator-template)
auth = 1002-auth
aors = 1002-aor

[1002-auth](operator-auth)
password = operator1002
username = 1002

[1002-aor](operator-aor)

[1003](operator-template)
auth = 1003-auth
aors = 1003-aor

[1003-auth](operator-auth)
password = operator1003
username = 1003

[1003-aor](operator-aor)
```

#### 5. Перезапуск Asterisk
```bash
# Проверка конфигурации
sudo asterisk -T -c
> dialplan reload
> module reload res_http_websocket.so
> module reload res_ari.so
> ari show apps
> exit

# Перезапуск сервиса
sudo systemctl restart asterisk
sudo systemctl enable asterisk

# Проверка статуса
sudo systemctl status asterisk
```

### Проверка ARI доступности

```bash
# Тест доступности ARI
curl -u callcenter_admin:CallCenter2025! \
  http://localhost:8088/ari/asterisk/info

# Должен вернуть JSON с информацией о системе
```

---

## 🔧 Конфигурация системы

### 1. Запуск Backend
```bash
cd backend
source venv/bin/activate

# Проверка подключения к БД
python3 -c "
import asyncio
from database import DatabaseManager

async def test_db():
    db = DatabaseManager()
    await db.connect()
    print('✅ MongoDB доступна')
    await db.disconnect()

asyncio.run(test_db())
"

# Запуск в режиме разработки
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Или запуск в продакшн режиме
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### 2. Запуск Frontend
```bash
# В новом терминале
cd frontend

# Запуск dev сервера
yarn start

# Сборка для продакшн
yarn build
# Файлы будут в build/
```

### 3. Первоначальная настройка через веб-интерфейс

1. **Открыть приложение**
   ```
   http://localhost:3000
   ```

2. **Авторизация администратора**
   ```
   Логин: admin
   Пароль: admin
   ```

3. **Смена пароля администратора**
   ```
   1. Перейти в профиль
   2. Сменить пароль на безопасный
   3. Сохранить изменения
   ```

4. **Настройка Asterisk подключения**
   ```
   1. Админ панель → Настройки системы
   2. Раздел "Конфигурация Asterisk":
      - Host: IP адрес Asterisk (или localhost)
      - Port: 8088
      - Username: callcenter_admin
      - Password: CallCenter2025!
      - Protocol: ARI
   3. Нажать "Тестировать соединение"
   4. При успехе нажать "Сохранить настройки"
   ```

5. **Создание операторов**
   ```
   1. Админ панель → Управление пользователями
   2. Создать операторов с extensions:
      - operator1 / extension: 1001
      - operator2 / extension: 1002
      - operator3 / extension: 1003
   3. Создать менеджеров и супервайзеров по необходимости
   ```

---

## 🧪 Тестирование

### 1. Проверка компонентов

**Backend API:**
```bash
# Проверка health endpoint
curl http://localhost:8001/api/

# Проверка авторизации
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "новый_пароль"}'
```

**Frontend:**
```bash
# Проверка доступности
curl http://localhost:3000

# Проверка загрузки статических файлов
curl -I http://localhost:3000/static/js/main.js
```

**MongoDB:**
```bash
# Проверка подключения
mongo --eval "db.runCommand({connectionStatus : 1})"

# Проверка данных
mongo callcenter --eval "db.users.find().pretty()"
```

### 2. Функциональное тестирование

**Тест авторизации:**
1. Открыть http://localhost:3000
2. Войти как admin
3. Проверить доступ к админ панели
4. Выйти и войти как оператор

**Тест Asterisk интеграции:**
1. Настроить подключение к Asterisk
2. Протестировать соединение
3. Проверить загрузку extensions
4. Проверить загрузку очередей

**Тест управления пользователями:**
1. Создать тестового оператора
2. Назначить extension
3. Проверить появление в списке
4. Войти под новым пользователем

### 3. Нагрузочное тестирование

**Простой тест производительности:**
```bash
# Установка Apache Bench
sudo apt install apache2-utils

# Тест авторизации (100 запросов, 10 одновременно)
ab -n 100 -c 10 -T 'application/json' \
  -p login_data.json \
  http://localhost:8001/api/auth/login

# Где login_data.json содержит:
echo '{"username": "admin", "password": "пароль"}' > login_data.json
```

**Мониторинг ресурсов:**
```bash
# Мониторинг в реальном времени
htop

# Использование памяти
free -h

# Дисковое пространство
df -h

# Сетевые подключения
netstat -tulpn | grep :8001
netstat -tulpn | grep :3000
```

---

## 🚨 Устранение неисправностей

### Проблемы с Backend

**Ошибка: "ModuleNotFoundError"**
```bash
# Решение: Переустановка зависимостей
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Ошибка: "Connection refused MongoDB"**
```bash
# Проверка статуса MongoDB
sudo systemctl status mongod

# Перезапуск
sudo systemctl restart mongod

# Проверка логов
sudo journalctl -u mongod -f
```

**Ошибка: "Port 8001 already in use"**
```bash
# Найти процесс на порту
sudo lsof -i :8001

# Убить процесс
sudo kill -9 PID

# Или изменить порт в команде запуска
uvicorn server:app --host 0.0.0.0 --port 8002 --reload
```

### Проблемы с Frontend

**Ошибка: "EADDRINUSE: port 3000 already in use"**
```bash
# Найти и убить процесс
sudo lsof -i :3000
sudo kill -9 PID

# Или запустить на другом порту
PORT=3001 yarn start
```

**Ошибка: "Cannot connect to backend"**
```bash
# Проверить .env.local файл
cat frontend/.env.local

# Убедиться что backend запущен
curl http://localhost:8001/api/

# Проверить CORS настройки в backend/server.py
```

**Ошибка: "Module not found" при сборке**
```bash
# Очистить кеш и переустановить
cd frontend
rm -rf node_modules package-lock.json yarn.lock
yarn install
```

### Проблемы с Asterisk

**Ошибка: "ARI connection failed"**
```bash
# Проверка доступности ARI
curl -u callcenter_admin:CallCenter2025! \
  http://localhost:8088/ari/asterisk/info

# Проверка конфигурации
sudo asterisk -rx "ari show apps"
sudo asterisk -rx "http show status"

# Перезагрузка модулей
sudo asterisk -rx "module reload res_ari.so"
sudo asterisk -rx "module reload res_http_websocket.so"
```

**Ошибка: "Authentication failed"**
```bash
# Проверка пользователей ARI
sudo asterisk -rx "ari show users"

# Проверка конфигурации
sudo cat /etc/asterisk/ari.conf

# Перезагрузка конфигурации
sudo asterisk -rx "reload"
```

### Проблемы с производительностью

**Высокое потребление CPU**
```bash
# Проверка процессов
top -p $(pgrep -d',' -f "uvicorn\|node")

# Оптимизация MongoDB
mongo callcenter --eval "db.runCommand({listCollections:1})"
mongo callcenter --eval "db.calls.getIndexes()"

# Добавление недостающих индексов
mongo callcenter --eval "
db.calls.createIndex({'start_time': -1});
db.calls.createIndex({'operator_id': 1, 'start_time': -1});
"
```

**Высокое потребление памяти**
```bash
# Анализ памяти Python процессов
sudo apt install python3-psutil
python3 -c "
import psutil
for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
    if 'python' in proc.info['name']:
        print(f'{proc.info[\"pid\"]}: {proc.info[\"memory_info\"].rss / 1024 / 1024:.1f} MB')
"

# Оптимизация Node.js
export NODE_OPTIONS="--max-old-space-size=2048"
```

### Логирование и диагностика

**Включение отладочного режима:**
```bash
# Backend
cd backend
export DEBUG=True
export LOG_LEVEL=DEBUG
uvicorn server:app --host 0.0.0.0 --port 8001 --reload --log-level debug

# Frontend
cd frontend
REACT_APP_DEBUG=true yarn start
```

**Просмотр логов:**
```bash
# Системные логи
sudo journalctl -u mongod -f
sudo journalctl -u asterisk -f

# Логи приложения
tail -f backend/app.log
tail -f /var/log/asterisk/messages
```

**Создание отчета о проблеме:**
```bash
# Скрипт сбора диагностической информации
cat > diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== Smart Call Center Diagnostic Report ==="
echo "Date: $(date)"
echo ""
echo "=== System Info ==="
uname -a
cat /etc/os-release
echo ""
echo "=== Service Status ==="
systemctl status mongod --no-pager
systemctl status asterisk --no-pager
echo ""
echo "=== Port Usage ==="
netstat -tulpn | grep -E ':(3000|8001|8088|27017)'
echo ""
echo "=== Disk Space ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Process List ==="
ps aux | grep -E '(python|node|mongod|asterisk)' | grep -v grep
EOF

chmod +x diagnostic.sh
./diagnostic.sh > diagnostic_report.txt
```

---

## 📋 Контрольный список установки

### ✅ Предварительная подготовка
- [ ] Проверены системные требования
- [ ] Установлены все зависимости (Node.js, Python, MongoDB)
- [ ] Создан пользователь для приложения (рекомендуется)
- [ ] Настроены права доступа к каталогам

### ✅ Backend
- [ ] Клонирован репозиторий
- [ ] Создано виртуальное окружение Python
- [ ] Установлены Python зависимости
- [ ] Создан и настроен .env файл
- [ ] Сгенерирован JWT секретный ключ
- [ ] Проверено подключение к MongoDB
- [ ] Инициализирована база данных
- [ ] Backend запускается без ошибок

### ✅ Frontend
- [ ] Установлены Node.js зависимости
- [ ] Создан .env.local файл
- [ ] Настроен URL backend сервера
- [ ] Frontend компилируется без ошибок
- [ ] Frontend подключается к backend

### ✅ Asterisk (опционально)
- [ ] Asterisk установлен и запущен
- [ ] Настроен http.conf
- [ ] Настроен ari.conf с пользователями
- [ ] Настроен extensions.conf для Stasis
- [ ] Настроены SIP endpoints в pjsip.conf
- [ ] ARI доступен по HTTP
- [ ] Проверено подключение из приложения

### ✅ Интеграция
- [ ] Создан admin пользователь
- [ ] Настроено подключение к Asterisk через UI
- [ ] Протестировано соединение с Asterisk
- [ ] Созданы тестовые операторы
- [ ] Проверена авторизация под разными ролями
- [ ] Проверена загрузка extensions из Asterisk

### ✅ Продакшн готовность
- [ ] Изменен пароль администратора
- [ ] Настроен Nginx/Apache (если используется)
- [ ] Настроен SSL сертификат
- [ ] Созданы systemd сервисы
- [ ] Настроено автоматическое резервное копирование
- [ ] Настроен мониторинг и логирование

---

**Поздравляем! Smart Call Center успешно установлен и готов к использованию! 🎉**

Для получения дополнительной помощи обратитесь к основной документации или создайте issue в репозитории проекта.