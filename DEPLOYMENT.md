# 🚀 Smart Call Center - Локальное развертывание

## 📋 Требования
- Node.js 16+
- Python 3.8+
- MongoDB 4.4+

## ⚙️ Настройка Backend

1. **Установка зависимостей:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Настройка .env файла:**
```bash
cp .env.example .env
```
Отредактируйте `.env`:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=callcenter
JWT_SECRET_KEY=your-secret-key-here
```

3. **Запуск MongoDB:**
```bash
# Linux/macOS
sudo systemctl start mongod

# Windows
net start MongoDB
```

4. **Запуск Backend:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## 🌐 Настройка Frontend

1. **Установка зависимостей:**
```bash
cd frontend
yarn install
```

2. **Настройка .env.local:**
```bash
cp .env.local.example .env.local
```
Файл `.env.local`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
```

3. **Запуск Frontend:**
```bash
yarn start
```

## 🔐 Первый вход

- **Пользователь:** `admin`
- **Пароль:** `admin`

## 🔌 Настройка Asterisk (опционально)

### Для тестирования с виртуальным Asterisk:
1. В админ панели используйте хост: `demo.asterisk.com`
2. Система автоматически переключится на виртуальный ARI

### Для подключения к реальному Asterisk:
1. Настройте ARI в `/etc/asterisk/ari.conf`:
```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088

[smart-call-center]
type = user
read_only = no
password = your-ari-password
```

2. В админ панели укажите:
   - Host: IP адрес Asterisk сервера
   - Port: 8088
   - Username: smart-call-center
   - Password: your-ari-password

## 🛠️ Устранение неисправностей

### WebSocket ошибки:
- Убедитесь что в `.env.local` установлен `WDS_SOCKET_PORT=3000`
- Перезапустите frontend после изменения .env

### Backend не запускается:
- Проверьте подключение к MongoDB
- Убедитесь что порт 8001 свободен
- Проверьте правильность зависимостей Python

### Проблемы авторизации:
- Проверьте что MongoDB работает
- Убедитесь что база данных инициализирована
- Используйте `admin`/`admin` для первого входа

## 📊 Проверка работы системы

После успешного запуска:
1. Откройте http://localhost:3000
2. Войдите как admin/admin
3. Перейдите в админ панель
4. Создайте тестового оператора
5. Настройте подключение к Asterisk

## 🚀 Готово!

Система готова к использованию. Все операторы и данные создаются через админ панель.