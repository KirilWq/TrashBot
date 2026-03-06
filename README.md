# 🤖 TRASH BOT

Telegram бот для розваг в чатах з грою "Вирости Хряка" та дуелями!

## 🚀 Деплой на Render.com

### 1. Створи GitHub репозиторій
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/trashbot.git
git push -u origin main
```

### 2. Підключи Render
1. Зайди на https://render.com
2. Sign up через GitHub
3. New → **Web Service**
4. Обери свій репозиторій
5. Налаштування:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free

### 3. Додай змінні середовища

**Локально (для тестування):**
Створи файл `.env` з токеном:
```
BOT_TOKEN=1234567890:AAHb8rbzBqD8xpgFLAUSyTCsc6-uSdc1NkY
```

**На Render/Railway:**
Dashboard → Environment → Add Variable:
```
BOT_TOKEN=1234567890:AAHb8rbzBqD8xpgFLAUSyTCsc6-uSdc1NkY
```

### 4. Готово! 🎉

---

## 🚀 Деплой на Railway.app

### 1. Створи GitHub репозиторій
```bash
git init
git add .
git commit -m "Initial commit"
git push
```

### 2. Підключи Railway
1. Зайди на https://railway.app
2. Sign up через GitHub
3. New Project → Deploy from GitHub repo
4. Обери свій репозиторій

### 3. Додай змінні середовища
Variables → + New Variable:
```
BOT_TOKEN=your_bot_token_here
```

### 4. Готово! 🎉

---

## ⚙️ Налаштування

### Отримай токен бота
1. Відкрий @BotFather в Telegram
2. `/newbot`
3. Дотримуйся інструкцій
4. Скопіюй токен

### Додай змінні середовища
**Ніколи не зберігай токен в коді!**

На Render/Railway додай:
```
BOT_TOKEN=1234567890:AAHb8rbzBqD8xpgFLAUSyTCsc6-uSdc1NkY
```

В коді використовуй:
```python
import os
BOT_TOKEN = os.environ.get('BOT_TOKEN')
```

---

## 📋 Команди

| Команда | Опис |
|---------|------|
| `/start` | Привітання |
| `/menu` | Меню команд |
| `/grow` | Отримати хряка |
| `/feed` | Нагодувати (раз на 12 год) |
| `/my` | Мій хряк |
| `/hryaketop` | Топ хряків |
| `/duel` | Створити дуель |
| `/achievements` | Досягнення |
| `/pidor` | Хто підор |
| `/roast` | Roast |
| `/fortune` | Передбачення |
| `/rate` | Оцінка |

---

## 🎮 Гра "Вирости Хряка"

- Отримай хряка командою `/grow`
- Годуй раз на 12 годин (`/feed`)
- Вага змінюється від -20 до +20 кг
- Бийся в дуелях з іншими гравцями
- Збирай досягнення!

---

## 📁 Файли

- `bot.py` - основний код бота
- `requirements.txt` - залежності Python
- `Procfile` - команда запуску для Render
- `runtime.txt` - версія Python
- `.gitignore` - ігнорування файлів
- `bot_database.db` - база даних (створюється автоматично)
- `hryaky.json` - дані хряків (резервна копія)
- `bot.log` - логи бота

---

## 🆘 Підтримка

Якщо щось не працює:
1. Перевір логи на хостингу
2. Переконайся що токен правильний
3. Перевір чи бот є адміном в чаті

---

## 📝 Ліцензія

Бот створений для розваги! Не сприймай серйозно! 🎉
