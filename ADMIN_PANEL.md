# 🛡️ Адмін-панель для бота

## 📋 Налаштування

### **Крок 1: Дізнайся Свій ID**

Напиши в боті:
```
/userinfo
```

Або додай тимчасову команду в bot.py:

```python
@bot.message_handler(commands=['myid'])
def myid_cmd(message):
    bot.reply_to(message, f"Твій ID: {message.from_user.id}")
```

### **Крок 2: Додай Свій ID в .env**

Створи/редагуй `.env`:
```env
# Токен бота
BOT_TOKEN=your_token

# Твій ID (адмін)
ADMIN_ID=5699432128

# Database URL
DATABASE_URL=your_database_url
```

### **Крок 3: Імпорт в bot.py**

Додай в початок bot.py:
```python
import os

# Отримуємо адмін ID
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

# Функція перевірки адміна
def is_admin(user_id):
    return user_id == ADMIN_ID
```

---

## 🎯 Адмін Команди

### **Керування Хряками:**
```
/admin_weight <user_id> <вага> - змінити вагу хряка
/admin_addweight <user_id> <кг> - додати вагу
/admin_removeweight <user_id> <кг> - відняти вагу
/admin_reset_hryak <user_id> - скинути хряка
```

### **Керування Предметами:**
```
/admin_additem <user_id> <предмет> <кількість> - додати предмет
/admin_removeitem <user_id> <предмет> - видалити предмет
/admin_clear_inventory <user_id> - очистити інвентар
```

### **Керування Гільдіями:**
```
/admin_guild_addcoins <guild_id> <сума> - додати монети гільдії
/admin_guild_removcoins <guild_id> <сума> - відняти монети
/admin_guild_addxp <guild_id> <сума> - додати XP
```

### **Керування Балансом:**
```
/admin_addcoins <user_id> <сума> - додати монети
/admin_removecoins <user_id> <сума> - відняти монети
/admin_addxp <user_id> <сума> - додати XP
```

### **Інше:**
```
/admin_stats - статистика бота
/admin_broadcast <повідомлення> - розсилка всім
/admin_restart - перезапуск бота
```

---

## 📁 Файли

### **admin_panel.py** (новий файл):
```python
import os
from db import *

# Отримуємо адмін ID
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

def is_admin(user_id):
    """Перевірка чи користувач адмін"""
    return user_id == ADMIN_ID

def check_admin(func):
    """Декоратор для перевірки адміна"""
    def wrapper(message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        return func(message, *args, **kwargs)
    return wrapper
```

---

## 🚀 Використання

### **Приклад 1: Змінити Вагу**
```
/admin_weight 123456789 500
✅ Вагу хряка користувача 123456789 змінено на 500 кг
```

### **Приклад 2: Додати Предмет**
```
/admin_additem 123456789 Меч 5
✅ Додано предмет "Меч" x5 користувачу 123456789
```

### **Приклад 3: Додати Монети**
```
/admin_addcoins 123456789 10000
✅ Додано 10000 монет користувачу 123456789
```

---

## ⚠️ Безпека

1. **Ніколи не ділись ADMIN_ID**
2. **Зберігай .env в таємниці**
3. **Не додавай ADMIN_ID в git**
4. **Використовуй тільки ти**

---

## 📝 Додаткові Функції

### **Логування Адмін Дій:**
```python
import logging

admin_logger = logging.getLogger('admin_actions')

def log_admin_action(admin_id, action, target_id, details):
    admin_logger.info(f"ADMIN {admin_id}: {action} on {target_id} - {details}")
```

### **Обмеження Команд:**
```python
# Максимальна вага
MAX_WEIGHT = 10000

# Максимальна кількість монет
MAX_COINS = 1000000
```

---

**Готово!** 🎉
