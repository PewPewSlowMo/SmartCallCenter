FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Открытие порта
EXPOSE 8001

# Команда запуска
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]