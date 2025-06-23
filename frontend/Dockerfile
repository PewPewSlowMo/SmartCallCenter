FROM node:20-alpine

WORKDIR /app

# Копирование package.json и yarn.lock
COPY package.json yarn.lock ./

# Установка зависимостей
RUN yarn install

# Копирование исходного кода
COPY . .

# Открытие порта
EXPOSE 3000

# Команда запуска
CMD ["yarn", "start"]