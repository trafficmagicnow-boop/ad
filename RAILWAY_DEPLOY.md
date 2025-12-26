# Adw/Skro Integration - Railway Deployment Guide

## Шаг 1: Подготовка (уже сделано)
- ✅ requirements.txt создан
- ✅ Procfile создан  
- ✅ railway.toml создан
- ✅ server.py обновлен для Railway

## Шаг 2: Деплой на Railway

### Вариант А: Через GitHub (рекомендуется)

1. **Создай репозиторий на GitHub:**
   - Зайди на github.com
   - Нажми "New Repository"
   - Назови, например: `adw-skro-integration`
   - Нажми "Create"

2. **Загрузи файлы:**
   ```bash
   cd c:\Users\Karlo\.gemini\antigravity\playground\nascent-meteoroid
   git init
   git add server.py dashboard.html login.html requirements.txt Procfile railway.toml
   git commit -m "Deploy with Multi-User Auth"
   git remote add origin https://github.com/ТвойЮзернейм/adw-skro-integration.git
   git push -u origin main
   ```

3. **В Railway:**
   - Нажми "GitHub Repository"
   - Авторизуй GitHub
   - Выбери репозиторий `adw-skro-integration`
   - Railway автоматически задеплоит

### Вариант Б: Через Empty Project (быстрее, без GitHub)

1. **В Railway нажми "Empty Project"**

2. **Перейди в настройки проекта:**
   - Settings → Environment
   - Ничего добавлять не нужно (токены уже в коде)

3. **Загрузи файлы через Railway CLI:**
   
   Скачай Railway CLI: https://docs.railway.app/develop/cli
   
   Затем:
   ```bash
   cd c:\Users\Karlo\.gemini\antigravity\playground\nascent-meteoroid
   railway login
   railway link
   railway up
   ```

4. **Получи URL:**
   - В Railway перейди в Settings → Networking
   - Нажми "Generate Domain"
   - Скопируй URL (типа `adw-integration.railway.app`)

## После деплоя

Твой URL: `https://твой-проект.railway.app`

Отправь этот URL баеру - он откроет панель и сможет создавать ссылки!

## Важно

Railway бесплатно даёт:
- 500 часов работы/месяц
- $5 кредитов
- Этого хватит на месяц работы 24/7
