import telebot
import random
import time
import json
import os
import logging
import sqlite3
from threading import Thread
from telebot import types
from dotenv import load_dotenv
from flask import Flask
from db import init_db, load_from_db, save_hryak_to_db, save_stats_to_db, save_warns_to_db, save_spam_to_db, save_manual_users_to_db, get_hryak_from_db

# Налаштування логгера (ПОВИННО БУТИ ПЕРШИМ!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Завантажуємо змінні середовища з .env файлу (для локальної розробки)
load_dotenv()

# Отримуємо токен зі змінних середовища
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ ПОМИЛКА: BOT_TOKEN не знайдено в змінних середовища!")
    logger.error("Додай змінну середовища BOT_TOKEN з токеном бота")
    exit(1)

# Ініціалізація бази даних
init_db()
logger.info("✅ База даних підключена")

logger.info("=" * 50)
logger.info("🚀 ЗАПУСК БОТА...")
logger.info("=" * 50)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# Дозволити відповідати без повідомлення (уникає помилок 400)
bot.enable_save_next_step_handlers()

logger.info(f"✅ Бот ініціалізований з токеном: {BOT_TOKEN[:20]}...")



# ============================================
# РУЧНИЙ СПИСОК ЮЗЕРНЕЙМІВ (додай своїх друзів)
# ============================================
DEFAULT_USERS = [
    "@skyfidon79",
    "@Turiozka",
    "@terchizz",
    "@Freezers32"
]
# ============================================

# Кеш учасників чату
chat_members_cache = {}

# Ручний список юзернеймів для кожного чату (можна додавати командами)
manual_users = {}

# Замушені користувачі (реальний мут): {chat_id: {user_id: expire_time}}
muted_users = {}

# Провинні користувачі (образи у відповідь): {chat_id: {user_id: expire_time}}
provin_users = {}

# ============================================
# СТАТИСТИКА ЧАТУ - повідомлення
# ============================================
STATS_FILE = "stats.json"

# Завантажуємо статистику
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        stats_data = json.load(f)
else:
    stats_data = {}

def save_stats():
    """Зберігає статистику в БД"""
    try:
        save_stats_to_db(stats_data)
    except Exception as e:
        logger.error(f"❌ Помилка збереження статистики: {e}")

def add_message(chat_id, user_id, username):
    """Додає повідомлення до статистики"""
    key = f"{chat_id}_{user_id}"
    if key not in stats_data:
        stats_data[key] = {
            'user_id': user_id,
            'chat_id': chat_id,
            'username': username,
            'count': 0,
            'first_message': int(time.time()),
            'last_message': int(time.time())
        }
    stats_data[key]['count'] += 1
    stats_data[key]['last_message'] = int(time.time())
    stats_data[key]['username'] = username
    save_stats()

def get_chat_stats(chat_id):
    """Отримує статистику чату"""
    chat_stats = []
    for key, data in stats_data.items():
        if data.get('chat_id') == chat_id:
            chat_stats.append(data)
    return sorted(chat_stats, key=lambda x: x['count'], reverse=True)

# ============================================
# ПОПЕРЕДЖЕННЯ - warn система
# ============================================
WARNS_FILE = "warns.json"

# Завантажуємо попередження
if os.path.exists(WARNS_FILE):
    with open(WARNS_FILE, 'r', encoding='utf-8') as f:
        warns_data = json.load(f)
else:
    warns_data = {}

def save_warns():
    """Зберігає попередження в БД"""
    try:
        save_warns_to_db(warns_data)
    except Exception as e:
        logger.error(f"❌ Помилка збереження попереджень: {e}")

def add_warn(chat_id, user_id, username, reason):
    """Додає попередження"""
    key = f"{chat_id}_{user_id}"
    if key not in warns_data:
        warns_data[key] = {
            'user_id': user_id,
            'chat_id': chat_id,
            'username': username,
            'warns': [],
            'banned': False
        }
    
    warns_data[key]['warns'].append({
        'reason': reason,
        'time': int(time.time()),
        'by': 'admin'
    })
    save_warns()
    return len(warns_data[key]['warns'])

def get_warns(chat_id, user_id):
    """Отримує попередження користувача"""
    key = f"{chat_id}_{user_id}"
    if key not in warns_data:
        return []
    return warns_data[key]['warns']

def clear_warns(chat_id, user_id):
    """Очищає попередження"""
    key = f"{chat_id}_{user_id}"
    if key in warns_data:
        warns_data[key]['warns'] = []
        save_warns()

def is_banned(chat_id, user_id):
    """Перевіряє чи забанений"""
    key = f"{chat_id}_{user_id}"
    if key not in warns_data:
        return False
    return warns_data[key].get('banned', False)

def ban_user(chat_id, user_id):
    """Банить користувача"""
    key = f"{chat_id}_{user_id}"
    if key not in warns_data:
        warns_data[key] = {'warns': [], 'banned': False}
    warns_data[key]['banned'] = True
    save_warns()

def unban_user(chat_id, user_id):
    """Розбанює користувача"""
    key = f"{chat_id}_{user_id}"
    if key in warns_data:
        warns_data[key]['banned'] = False
        save_warns()

# ============================================
# СПАМ КОНТРОЛЬ
# ============================================
SPAM_FILE = "spam.json"

if os.path.exists(SPAM_FILE):
    with open(SPAM_FILE, 'r', encoding='utf-8') as f:
        spam_data = json.load(f)
else:
    spam_data = {}

def save_spam():
    """Зберігає спам дані в БД"""
    try:
        save_spam_to_db(spam_data)
    except Exception as e:
        logger.error(f"❌ Помилка збереження спаму: {e}")

def check_spam(chat_id, user_id):
    """Перевіряє на спам (5 повідомлень за 10 секунд)"""
    key = f"{chat_id}_{user_id}"
    now = int(time.time())

    if key not in spam_data:
        spam_data[key] = {'messages': [], 'muted': False, 'mute_until': 0}

    # Очищаємо старі повідомлення (старше 10 сек)
    spam_data[key]['messages'] = [t for t in spam_data[key]['messages'] if now - t < 10]
    spam_data[key]['messages'].append(now)

    # Якщо більше 5 повідомлень за 10 сек
    if len(spam_data[key]['messages']) >= 5:
        spam_data[key]['muted'] = True
        spam_data[key]['mute_until'] = now + 60  # Мут на 1 хвилину
        save_spam()
        return True

    save_spam()
    return False

def is_spam_muted(chat_id, user_id):
    """Перевіряє чи замучений за спам"""
    key = f"{chat_id}_{user_id}"
    if key not in spam_data:
        return False, 0

    now = int(time.time())
    if spam_data[key].get('muted') and now < spam_data[key].get('mute_until', 0):
        return True, int(spam_data[key]['mute_until'] - now)

    # Знімаємо мут
    if spam_data[key].get('muted'):
        spam_data[key]['muted'] = False
        save_spam()

    return False, 0

# ============================================
# ДУЕЛІ ХРЯКІВ
# ============================================
DUELS_FILE = "duels.json"

# Завантажуємо дуелі
if os.path.exists(DUELS_FILE):
    with open(DUELS_FILE, 'r', encoding='utf-8') as f:
        duels_data = json.load(f)
else:
    duels_data = {}

def save_duels():
    """Зберігає дуелі у файл"""
    try:
        with open(DUELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(duels_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Помилка збереження дуелей: {e}")

def create_duel(chat_id, challenger_id, challenger_hryak):
    """Створює дуель"""
    duel_id = f"{chat_id}_{challenger_id}_{int(time.time())}"
    duels_data[duel_id] = {
        'chat_id': chat_id,
        'challenger_id': challenger_id,
        'challenger_hryak': challenger_hryak,
        'opponent_id': None,
        'opponent_hryak': None,
        'status': 'waiting',  # waiting, accepted, finished
        'message_id': None,
        'created_at': int(time.time())
    }
    save_duels()
    return duel_id

def calculate_duel_result(hryak1, hryak2):
    """Розраховує результат дуелі"""
    # Масса впливає на силу (60%)
    mass_factor1 = hryak1['weight'] * 0.6
    mass_factor2 = hryak2['weight'] * 0.6
    
    # Проворність - рандом + досвід (40%)
    agility1 = random.randint(1, 20) + (hryak1['feed_count'] * 0.1)
    agility2 = random.randint(1, 20) + (hryak2['feed_count'] * 0.1)
    
    power1 = mass_factor1 + agility1
    power2 = mass_factor2 + agility2
    
    # Критичний удар (10% шанс)
    crit1 = random.random() < 0.1
    crit2 = random.random() < 0.1
    
    if crit1:
        power1 *= 2
    if crit2:
        power2 *= 2
    
    # Нокаут (5% шанс для слабшого)
    knockout = False
    if random.random() < 0.05:
        knockout = True
    
    return {
        'power1': power1,
        'power2': power2,
        'crit1': crit1,
        'crit2': crit2,
        'knockout': knockout,
        'winner': 1 if power1 > power2 else (2 if power2 > power1 else 0)
    }
HRYAK_FILE = "hryaky.json"

# Завантажуємо дані з файлу
if os.path.exists(HRYAK_FILE):
    try:
        with open(HRYAK_FILE, 'r', encoding='utf-8') as f:
            hryaky_data = json.load(f)
        logger.info(f"📦 Завантажено {len(hryaky_data)} хряків з {HRYAK_FILE}")
    except Exception as e:
        logger.error(f"❌ Помилка завантаження: {e}")
        hryaky_data = {}
else:
    logger.warning(f"📁 Файл {HRYAK_FILE} не знайдено, створюємо новий")
    hryaky_data = {}

def save_hryaky():
    """Зберігає всі зміни хряків в БД"""
    try:
        for key, hryak in hryaky_data.items():
            save_hryak_to_db(key, hryak)
        logger.debug(f"💾 Збережено {len(hryaky_data)} хряків в БД")
    except Exception as e:
        logger.error(f"❌ Помилка збереження: {e}")

def get_hryak(user_id, chat_id):
    """Отримує хряка користувача"""
    key = f"{chat_id}_{user_id}"
    hryak = get_hryak_from_db(key)
    if hryak:
        logger.debug(f"🐗 Знайдено хряка для {key}: {hryak['name']}")
        # Зберігаємо в кеш
        hryaky_data[key] = hryak
    else:
        logger.debug(f"❌ Не знайдено хряка для {key}")
    return hryak

def create_hryak(user_id, chat_id, username):
    """Створює нового хряка"""
    key = f"{chat_id}_{user_id}"
    weight = random.randint(1, 20)
    hryak = {
        'user_id': user_id,
        'chat_id': chat_id,
        'username': username,
        'name': 'Безіменний Хряк',
        'weight': weight,
        'last_feed': 0,
        'feed_count': 0,
        'max_weight': weight,
        'created_at': int(time.time())
    }
    # Зберігаємо в БД
    save_hryak_to_db(key, hryak)
    # Додаємо в кеш
    hryaky_data[key] = hryak
    logger.info(f"✅ Створено хряка: {key}, вага={weight}")
    return hryak

def feed_hryak(user_id, chat_id):
    """Годує хряка (раз на 12 годин)"""
    key = f"{chat_id}_{user_id}"
    logger.debug(f"🍽️ Спроба годування: {key}")

    # Отримуємо хряка з БД (не з кешу!)
    hryak = get_hryak(user_id, chat_id)
    
    if not hryak:
        logger.warning(f"❌ Немає хряка для {key}")
        return None, "У тебе ще немає хряка! Введи /grow щоб отримати."
    
    now = time.time()

    # Перевіряємо чи пройшло 12 годин (або це перше годування)
    if hryak['last_feed'] > 0 and now - hryak['last_feed'] < 43200:  # 12 годин = 43200 секунд
        hours_left = int((43200 - (now - hryak['last_feed'])) / 3600)
        logger.info(f"⏳ Ще рано для {key}, залишилось {hours_left} год")
        return None, f"Ще рано! Годувати можна раз на 12 годин. Залишилось {hours_left} год."

    # Годуємо
    hryak['last_feed'] = now
    hryak['feed_count'] += 1

    # Зміна ваги (від -20 до +20 кг)
    change = random.randint(-20, 20)
    old_weight = hryak['weight']
    hryak['weight'] = max(1, hryak['weight'] + change)

    # Оновлюємо максимальну вагу
    if hryak['weight'] > hryak['max_weight']:
        hryak['max_weight'] = hryak['weight']

    save_hryaky()

    result = {
        'old_weight': old_weight,
        'new_weight': hryak['weight'],
        'change': change,
        'feed_count': hryak['feed_count'],
        'hryak': hryak
    }
    logger.info(f"✅ Нагодовано {key}: {old_weight} → {hryak['weight']} кг ({change:+d})")
    return result, None

# Досягнення
ACHIEVEMENTS = {
    'oy': {'name': 'Ой... 😳', 'desc': 'Вперше схуднути', 'condition': lambda h: h.get('has_lost_weight', False)},
    'kamasutra': {'name': 'Камасутра 🧘‍♂️❤️', 'desc': 'Набрати 69 кг', 'condition': lambda h: h['weight'] >= 69},
    'monster': {'name': 'MONSTER GROW 🦖🌱', 'desc': 'Отримати +20 кг за раз', 'condition': lambda h: h.get('max_gain', 0) >= 20},
    'ded_electric': {'name': 'Дед був электриком ⚡️⚡️', 'desc': 'Набрати 1488 кг', 'condition': lambda h: h['weight'] >= 1488},
    'sotochka': {'name': 'Соточка 💯', 'desc': 'Набрати 100+ кг', 'condition': lambda h: h['weight'] >= 100},
    '5_metrov': {'name': '5 метрів сала 🥓📏', 'desc': 'Набрати 500+ кг', 'condition': lambda h: h['weight'] >= 500},
    'hryakotonna': {'name': 'Хрякотонна 🐷⚖️', 'desc': 'Набрати 1000+ кг', 'condition': lambda h: h['weight'] >= 1000},
    'dzhackpot': {'name': 'Джекпот 🎰💎', 'desc': 'Набрати 777 кг', 'condition': lambda h: h['weight'] >= 777},
    'kormilets': {'name': 'Кормилець року 🍽️🏆', 'desc': '5 разів по +20 кг', 'condition': lambda h: h.get('max_gains_20', 0) >= 5},
    '7_piatnyts': {'name': '7 п\'ятниць в тиждень 🍺📅', 'desc': 'Набрати вагу 7 днів поспіль', 'condition': lambda h: h.get('week_gain_streak', 0) >= 7},
    'kryak_dnya': {'name': 'Кряк дня 🐗🌞', 'desc': 'Стати хрячком дня', 'condition': lambda h: h.get('is_hryak_day', False)},
    'nova_nadiya': {'name': 'Нова надія 🌌✨', 'desc': 'Нагодувати 1 числа', 'condition': lambda h: h.get('fed_on_1st', False)},
}

# Образи для провинних користувачів
PROVIN_INSULTS = [
    "ти хто такий щоб писати?",
    "іди лісом",
    "не сци я тут головний",
    "ти вже замучив всіх",
    "навіщо ти це написав?",
    "мовчав би краще",
    "ти серйозно?",
    "це було непотрібно",
    "іди їж борщ",
]


# Відповіді для !такні
TAKNI_ANSWERS = [
    "Так",
    "Ні",
    "Звісно так",
    "Звісно ні",
    "Можливо",
    "Навряд чи",
    "Без сумніву так",
    "Ніколи в житті",
    "Швидше так",
    "Швидше ні",
]


# ============================================
# КОМАНДИ ГРИ "ВИРОСТИ ХРЯКА"
# ============================================

@bot.message_handler(commands=['grow'])
def grow_hryak(message):
    """Отримати хряка для вирощування"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    logger.info(f"🐷 /grow: chat_id={chat_id}, user_id={user_id}, username={username}")
    
    try:
        hryak = get_hryak(user_id, chat_id)
        
        if hryak:
            text = f"""🐷 **Твій хряк:**
            
Ім'я: {hryak['name']}
Вага: {hryak['weight']} кг
Максимальна вага: {hryak['max_weight']} кг
Нагодовано разів: {hryak['feed_count']}

Використовуй /feed щоб нагодувати!"""
        else:
            # Створюємо нового хряка
            hryak = create_hryak(user_id, chat_id, username)
            text = f"""🎉 **Ти отримав хряка!**

🐷 {hryak['name']}
⚖️ Вага: {hryak['weight']} кг

Тепер ти можеш його годувати раз на 12 годин командою /feed
Вирости найбільшого хряка в чаті!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
        logger.info(f"✅ /grow успішно для {user_id}")
    except Exception as e:
        logger.error(f"❌ Помилка /grow: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['feed'])
def feed_hryak_cmd(message):
    """Нагодувати хряка"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"🐷 /feed: chat_id={chat_id}, user_id={user_id}")
    
    try:
        result, error = feed_hryak(user_id, chat_id)
        
        if error:
            logger.warning(f"❌ /feed помилка: {error}")
            bot.reply_to(message, f"❌ {error}")
            return
        
        logger.info(f"✅ Результат годування: {result}")

        # Формуємо повідомлення
        actual_change = result['new_weight'] - result['old_weight']
        
        if actual_change > 0:
            emoji = "📈"
            title = "**Хряк наївся!**"
            text_change = f"+{actual_change} кг"
        elif actual_change < 0:
            emoji = "📉"
            title = "**Хряк схуд!**"
            text_change = f"{actual_change} кг"
        else:
            emoji = "➡️"
            title = "**Вага не змінилась!**"
            text_change = "0 кг"

        text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів

🐷 {result['hryak']['name']}"""
        
        # Перевіряємо досягнення
        unlocked = []
        hryak = result['hryak']

        if actual_change < 0 and not hryak.get('has_lost_weight'):
            hryak['has_lost_weight'] = True
            unlocked.append('oy')

        if actual_change == 20:
            hryak['max_gain'] = max(hryak.get('max_gain', 0), 20)
            if hryak.get('max_gain', 0) >= 20:
                unlocked.append('monster')
        
        if actual_change == 20:
            hryak['max_gains_20'] = hryak.get('max_gains_20', 0) + 1
            if hryak['max_gains_20'] >= 5:
                unlocked.append('kormilets')
        
        import datetime
        now = datetime.datetime.now()
        if now.day == 1:
            hryak['fed_on_1st'] = True
            unlocked.append('nova_nadiya')
        
        if unlocked:
            save_hryaky()
            text += "\n\n🏆 **Отримано досягнення:**\n"
            for ach in unlocked:
                text += f"• {ACHIEVEMENTS[ach]['name']}\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        logger.info(f"✅ /feed успішно для {user_id}")
    except Exception as e:
        logger.error(f"❌ Помилка /feed: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['my'])
def my_hryak(message):
    """Показати свого хряка"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"🐷 /my: chat_id={chat_id}, user_id={user_id}")
    
    try:
        hryak = get_hryak(user_id, chat_id)
        
        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return

        # Час до наступного годування
        now = time.time()
        # Якщо last_feed = 0, значить ще не годував
        if hryak['last_feed'] == 0:
            feed_status = "✅ Можна годувати!"
        else:
            time_left = 43200 - (now - hryak['last_feed'])  # 12 годин
            if time_left <= 0:
                feed_status = "✅ Можна годувати!"
            else:
                hours = int(time_left / 3600)
                minutes = int((time_left % 3600) / 60)
                feed_status = f"⏳ Ще {hours} год {minutes} хв"

        text = f"""🐷 **{hryak['name']}**

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів
🕐 Годування: {feed_status}

/feed - нагодувати (раз на 12 год)
/name - змінити ім'я"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /my: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['name'])
def name_hryak(message):
    """Змінити ім'я хряка"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"🐷 /name: chat_id={chat_id}, user_id={user_id}")
    
    try:
        hryak = get_hryak(user_id, chat_id)
        
        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return
        
        # Отримуємо нове ім'я
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, f"❌ Потрібно ім'я!\nПриклад: /name {hryak['name']}")
            return
        
        new_name = parts[1][:64]  # Макс 64 символи
        hryak['name'] = new_name
        save_hryaky()
        
        bot.reply_to(message, f"✅ Хряка перейменовано на **{new_name}**", parse_mode="Markdown")
        logger.info(f"✅ /name успішно: {new_name}")
    except Exception as e:
        logger.error(f"❌ Помилка /name: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['hryaketop'])
def top_hryaky(message):
    """Топ хряків чату"""
    chat_id = message.chat.id

    logger.info(f"🐷 /hryaketop: chat_id={chat_id}")

    try:
        # Отримуємо всіх хряків з БД і фільтруємо по chat_id
        chat_hryaky = []
        for key, hryak in hryaky_data.items():
            if hryak.get('chat_id') == chat_id:
                chat_hryaky.append(hryak)

        # Якщо в кеші немає, пробуємо завантажити з БД
        if not chat_hryaky:
            # Завантажуємо всі хряки з БД і фільтруємо
            from db import get_connection
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key FROM hryaky WHERE chat_id = %s', (chat_id,))
                rows = cursor.fetchall()
                for row in rows:
                    key = row[0]
                    hryak = get_hryak_from_db(key)
                    if hryak:
                        chat_hryaky.append(hryak)
                        hryaky_data[key] = hryak  # Додаємо в кеш
                cursor.close()
                conn.close()

        if not chat_hryaky:
            bot.reply_to(message, "📭 У цьому чаті ще немає хряків!")
            return

        # Сортуємо за вагою
        chat_hryaky.sort(key=lambda x: x['weight'], reverse=True)

        # Беремо топ 10
        top_count = min(10, len(chat_hryaky))

        text = "🏆 **ТОП ХРЯКІВ ЧАТУ**\n\n"
        emojis = ["🥇", "🥈", "🥉"]

        for i, hryak in enumerate(chat_hryaky[:top_count]):
            if i < 3:
                emoji = emojis[i]
            else:
                emoji = f"{i+1}."

            name = hryak['name'][:20]
            text += f"{emoji} {name} - {hryak['weight']} кг\n"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /hryaketop: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['globaltop'])
def global_top_hryaky(message):
    """Глобальний топ хряків (всі чати)"""
    chat_id = message.chat.id

    logger.info(f"🌍 /globaltop: chat_id={chat_id}")

    try:
        # Завантажуємо всіх хряків з БД
        all_hryaky = []
        from db import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key FROM hryaky')
            rows = cursor.fetchall()
            for row in rows:
                key = row[0]
                hryak = get_hryak_from_db(key)
                if hryak:
                    all_hryaky.append(hryak)
                    hryaky_data[key] = hryak  # Додаємо в кеш
            cursor.close()
            conn.close()

        if not all_hryaky:
            bot.reply_to(message, "📭 Ще немає хряків ніде!")
            return

        # Сортуємо за вагою
        all_hryaky.sort(key=lambda x: x['weight'], reverse=True)

        # Беремо топ 10
        top_count = min(10, len(all_hryaky))

        text = "🌍 **ГЛОБАЛЬНИЙ ТОП ХРЯКІВ**\n\n"
        emojis = ["🥇", "🥈", "🥉"]

        for i, hryak in enumerate(all_hryaky[:top_count]):
            if i < 3:
                emoji = emojis[i]
            else:
                emoji = f"{i+1}."

            name = hryak['name'][:20]
            chat_info = f"(чат {hryak.get('chat_id', '???')})"
            text += f"{emoji} {name} - {hryak['weight']} кг {chat_info}\n"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /globaltop: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['achievements'])
def achievements_cmd(message):
    """Показати досягнення"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"🏆 /achievements: chat_id={chat_id}, user_id={user_id}")
    
    try:
        hryak = get_hryak(user_id, chat_id)
        
        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return
        
        text = "🏆 **Твої досягнення:**\n\n"
        
        unlocked_count = 0
        for ach_id, ach in ACHIEVEMENTS.items():
            try:
                if ach['condition'](hryak):
                    text += f"✅ {ach['name']} - {ach['desc']}\n"
                    unlocked_count += 1
                else:
                    text += f"🔒 {ach['name']} - {ach['desc']}\n"
            except:
                text += f"🔒 {ach['name']} - {ach['desc']}\n"
        
        text += f"\n📊 Відкрито: {unlocked_count}/{len(ACHIEVEMENTS)}"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /achievements: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['duel'])
def duel_cmd(message):
    """Виклик на дуель через inline"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚔️ Виклик на дуель", callback_data="duel_start"),
        types.InlineKeyboardButton("📜 Правила", callback_data="duel_rules")
    )
    
    bot.reply_to(message, 
        f"🥊 **ДУЕЛІ ХРЯКІВ**\n\n"
        f"Натисни кнопку щоб почати!",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in ['duel_start', 'duel_rules', 'duel_create'])
def duel_menu_callback(call):
    """Обробка кнопок меню дуелей"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data in ['duel_start', 'duel_create']:
        bot.answer_callback_query(call.id)
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.send_message(chat_id, "❌ Спочатку отримай хряка (/grow)!", parse_mode="Markdown")
            return

        # Створюємо виклик на дуель
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            text=f"🐗 {hryak['name']} ({hryak['weight']} кг) - Прийняти виклик!",
            callback_data=f"duel_accept_{user_id}_{hryak['weight']}"
        )
        markup.add(btn)

        bot.send_message(
            chat_id,
            f'🥊 **ВИКЛИК НА ДУЕЛЬ!**\n\n'
            f'🐗 {hryak["name"]} ({hryak["weight"]} кг) викликає на дуель!\n'
            f'Хто прийме виклик?\n\n'
            f'⚔️ На кону: 10-50% маси програвшого!',
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif call.data == 'duel_rules':
        bot.answer_callback_query(call.id)
        text = """⚔️ **ПРАВИЛА ДУЕЛЕЙ**

• Маса хряка = 60% сили
• Проворність = 40% сили
• 10% шанс на крит (x2 сила)
• 5% шанс на нокаут
• Програвший втрачає 10-50% маси
• Переможець отримує 50% від втраченого

🏆 Натисни "Виклик на дуель" щоб почати!"""
        bot.send_message(chat_id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith('duel_accept_'))
def duel_accept_callback(call):
    """Прийняття дуелі"""
    chat_id = call.message.chat.id
    opponent_id = call.from_user.id
    opponent_name = call.from_user.first_name

    # Парсим дані з callback_data
    try:
        parts = call.data.split('_')
        challenger_id = int(parts[2])
        challenger_weight = int(parts[3])
    except:
        bot.answer_callback_query(call.id, "❌ Помилка дуелі!", show_alert=True)
        return

    # Перевіряємо що це не той самий гравець
    if opponent_id == challenger_id:
        bot.answer_callback_query(call.id, "❌ Не можна битися з самим собою!", show_alert=True)
        return

    # Отримуємо хряків
    challenger_hryak = get_hryak(challenger_id, chat_id)
    opponent_hryak = get_hryak(opponent_id, chat_id)

    if not opponent_hryak:
        bot.answer_callback_query(call.id, "❌ У тебе немає хряка! Напиши /grow", show_alert=True)
        return

    if not challenger_hryak:
        bot.answer_callback_query(call.id, "❌ Хряк викликача зник!", show_alert=True)
        return

    # Розраховуємо результат
    result = calculate_duel_result(challenger_hryak, opponent_hryak)

    # Визначаємо переможця
    if result['knockout']:
        winner = 2 if result['winner'] == 1 else 1
        knockout_text = "🥊 НОКАУТ!"
    else:
        winner = result['winner']
        knockout_text = ""

    loss_percent = random.randint(10, 50) / 100

    if winner == 1:
        winner_hryak = challenger_hryak
        loser_hryak = opponent_hryak
        winner_name = challenger_hryak['name']
        loser_name = opponent_hryak['name']
    elif winner == 2:
        winner_hryak = opponent_hryak
        loser_hryak = challenger_hryak
        winner_name = opponent_hryak['name']
        loser_name = challenger_hryak['name']
    else:
        winner_name = "Нічия"
        loser_name = ""

    if winner != 0:
        loss = int(loser_hryak['weight'] * loss_percent)
        gain = int(loss * 0.5)

        loser_hryak['weight'] = max(1, loser_hryak['weight'] - loss)
        winner_hryak['weight'] += gain

        save_hryaky()

        result_text = f"""
🥊 **РЕЗУЛЬТАТИ ДУЕЛІ!** {knockout_text}

🏆 Переможець: {winner_name}
💀 Програвший: {loser_name}

📉 {loser_name} втратив {loss} кг ({int(loss_percent*100)}%)
📈 {winner_name} отримав {gain} кг

💪 Сила переможця: {result['power1'] if winner == 1 else result['power2']:.1f}
💪 Сила програвшого: {result['power1'] if winner == 2 else result['power2']:.1f}
{"⚡️ КРИТИЧНИЙ УДАР!" if result["crit1"] or result["crit2"] else ""}
"""
    else:
        result_text = f"""
🤝 **НІЧИЯ!**

Обидва хряки показали однакову силу!

💪 Сила challenger: {result['power1']:.1f}
💪 Сила opponent: {result['power2']:.1f}
"""

    bot.answer_callback_query(call.id, "⚔️ Дуель завершена!")
    
    # Редагуємо повідомлення з дуеллю
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"🥊 **ВИКЛИК НА ДУЕЛЬ!**\n\nПрийняв: {opponent_name}\n\n{result_text}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['menu'])
def menu_cmd(message):
    """Показати inline меню"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🐷 Хряк", callback_data="menu_grow"),
        types.InlineKeyboardButton("🍽️ Годувати", callback_data="menu_feed"),
        types.InlineKeyboardButton("📊 Мій", callback_data="menu_my"),
        types.InlineKeyboardButton("✏️ Ім'я", callback_data="menu_name"),
        types.InlineKeyboardButton("🏆 Топ чату", callback_data="menu_top"),
        types.InlineKeyboardButton("🌍 Глоб топ", callback_data="menu_globaltop"),
        types.InlineKeyboardButton("⚔️ Створити дуель", callback_data="duel_create"),
        types.InlineKeyboardButton("🏅 Досягнення", callback_data="menu_achievements"),
        types.InlineKeyboardButton("🎯 Підор", callback_data="menu_pidor"),
        types.InlineKeyboardButton("🔥 Roast", callback_data="menu_roast"),
        types.InlineKeyboardButton("🔮 Fortune", callback_data="menu_fortune"),
        types.InlineKeyboardButton("⭐ Оцінка", callback_data="menu_rate")
    )

    bot.reply_to(message,
        "📋 **МЕНЮ КОМАНД**\n\nОбери кнопку:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def menu_callback(call):
    """Обробка кнопок меню"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    command = call.data.split('_')[1]
    
    # Відповідаємо на callback
    bot.answer_callback_query(call.id)
    
    if command == 'grow':
        hryak = get_hryak(user_id, chat_id)
        if hryak:
            text = f"""🐷 **Вже маєш хряка!**

Ім'я: {hryak['name']}
Вага: {hryak['weight']} кг
Нагодовано: {hryak['feed_count']} разів"""
        else:
            text = """🎉 **Отримай хряка!**

Напиши /grow в чаті!"""
    
    elif command == 'feed':
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            text = "❌ Спочатку отримай хряка (/grow)!"
        else:
            now = time.time()
            
            # Якщо last_feed = 0, значить ще не годував — можна годувати
            if hryak['last_feed'] == 0:
                # Годуємо хряка
                result, error = feed_hryak(user_id, chat_id)
                if result:
                    change = result['new_weight'] - result['old_weight']
                    if change > 0:
                        emoji = "📈"
                        title = "**Хряк наївся!**"
                        text_change = f"+{change} кг"
                    elif change < 0:
                        emoji = "📉"
                        title = "**Хряк схуд!**"
                        text_change = f"{change} кг"
                    else:
                        emoji = "➡️"
                        title = "**Вага не змінилась!**"
                        text_change = "0 кг"
                    
                    text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів

🐷 {result['hryak']['name']}"""
                else:
                    text = "❌ Помилка годування!"
            else:
                time_left = 43200 - (now - hryak['last_feed'])
                if time_left <= 0:
                    # Годуємо хряка
                    result, error = feed_hryak(user_id, chat_id)
                    if result:
                        change = result['new_weight'] - result['old_weight']
                        if change > 0:
                            emoji = "📈"
                            title = "**Хряк наївся!**"
                            text_change = f"+{change} кг"
                        elif change < 0:
                            emoji = "📉"
                            title = "**Хряк схуд!**"
                            text_change = f"{change} кг"
                        else:
                            emoji = "➡️"
                            title = "**Вага не змінилась!**"
                            text_change = "0 кг"
                        
                        text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів

🐷 {result['hryak']['name']}"""
                    else:
                        text = "❌ Помилка годування!"
                else:
                    hours = int(time_left / 3600)
                    minutes = int((time_left % 3600) / 60)
                    text = f"⏳ **Ще рано!**\n\nЗалишилось: {hours} год {minutes} хв\n\n🐷 {hryak['name']}"
    
    elif command == 'my':
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            text = "❌ У тебе немає хряка! Напиши /grow"
        else:
            now = time.time()
            # Якщо last_feed = 0, значить ще не годував
            if hryak['last_feed'] == 0:
                feed_status = "✅ Можна годувати!"
            else:
                time_left = 43200 - (now - hryak['last_feed'])
                if time_left <= 0:
                    feed_status = "✅ Можна годувати!"
                else:
                    hours = int(time_left / 3600)
                    minutes = int((time_left % 3600) / 60)
                    feed_status = f"⏳ Ще {hours} год {minutes} хв"
            
            text = f"""🐷 **{hryak['name']}**

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів
🕐 Годування: {feed_status}

/feed - нагодувати (раз на 12 год)
/name - змінити ім'я"""
    
    elif command == 'top':
        chat_hryaky = sorted(hryaky_data.values(), key=lambda x: x['weight'], reverse=True)[:5]
        if not chat_hryaky:
            text = "📭 Ще немає хряків!"
        else:
            text = "🏆 **ТОП ХРЯКІВ ЧАТУ**\n\n"
            for i, h in enumerate(chat_hryaky):
                text += f"{i+1}. {h['name']} - {h['weight']} кг\n"

    elif command == 'globaltop':
        # Завантажуємо всіх хряків з БД
        all_hryaky = []
        from db import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key FROM hryaky')
            rows = cursor.fetchall()
            for row in rows:
                key = row[0]
                hryak = get_hryak_from_db(key)
                if hryak:
                    all_hryaky.append(hryak)
            cursor.close()
            conn.close()
        
        all_hryaky.sort(key=lambda x: x['weight'], reverse=True)
        top_count = min(5, len(all_hryaky))
        
        if not all_hryaky:
            text = "📭 Ще немає хряків ніде!"
        else:
            text = "🌍 **ГЛОБАЛЬНИЙ ТОП ХРЯКІВ**\n\n"
            for i, h in enumerate(all_hryaky[:top_count]):
                text += f"{i+1}. {h['name']} - {h['weight']} кг\n"

    elif command == 'name':
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            text = "❌ У тебе немає хряка! Напиши /grow"
        else:
            text = f"""✏️ **Змінити ім'я хряка**

Поточне ім'я: {hryak['name']}

Напиши /name НовеІм'я
Приклад: /name СуперХряк"""

    elif command == 'duel':
        text = "⚔️ **Дуелі**\n\nНатисни /duel або /menu щоб створити дуель!"

    elif command == 'achievements':
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            text = "❌ Спочатку отримай хряка!"
        else:
            text = "🏆 **Досягнення:**\n\n"
            for ach_id, ach in ACHIEVEMENTS.items():
                try:
                    if ach['condition'](hryak):
                        text += f"✅ {ach['name']}\n"
                    else:
                        text += f"🔒 {ach['name']}\n"
                except:
                    text += f"🔒 {ach['name']}\n"
    
    elif command == 'pidor':
        text = "🎯 **Підор**\n\nНапиши /pidor в чаті!"
    
    elif command == 'roast':
        text = "🔥 **Roast**\n\nНапиши /roast в чаті!"
    
    elif command == 'fortune':
        text = "🔮 **Fortune**\n\nНапиши /fortune в чаті!"
    
    elif command == 'rate':
        text = "⭐ **Rate**\n\nНапиши /rate в чаті!"
    
    else:
        text = "❌ Невідома команда"
    
    # Редагуємо повідомлення або відправляємо нове
    bot.send_message(chat_id, text, parse_mode="Markdown")


def is_admin(chat_id, user_id):
    """Перевіряє чи користувач є адміном"""
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id:
                return True
        return False
    except:
        return False


def get_user_from_text(message):
    """Отримує юзернейм або user_id з тексту або reply"""
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        return user.id, f"@{user.username}" if user.username else user.first_name

    if message.text and len(message.text.split()) > 1:
        text = message.text.split()[1]
        if text.startswith('@'):
            # Шукаємо серед адміністраторів
            try:
                members = bot.get_chat_administrators(message.chat.id)
                for member in members:
                    if member.user.username and f"@{member.user.username}" == text:
                        return member.user.id, text
            except:
                pass
            
            # Шукаємо в кеші учасників
            chat_id = message.chat.id
            if chat_id in chat_members_cache:
                for i, u in enumerate(chat_members_cache[chat_id]):
                    if u == text:
                        # Не маємо user_id для юзернеймів, повертаємо тільки ім'я
                        return None, text
            
            return None, text
        return None, text

    return None, None


def get_chat_members(message):
    """Отримує всіх учасників чату"""
    chat_id = message.chat.id

    # Перевіряємо кеш
    if chat_id in chat_members_cache and chat_members_cache[chat_id]:
        return chat_members_cache[chat_id]

    users = []
    try:
        if message.chat.type in ['group', 'supergroup']:
            # Отримуємо адміністраторів
            admins = bot.get_chat_administrators(chat_id)
            for admin in admins:
                user = admin.user
                if not user.is_bot:
                    if user.username:
                        users.append(f"@{user.username}")
                    else:
                        users.append(f"{user.first_name}")

            # Додаємо стандартних юзернеймів з коду
            for u in DEFAULT_USERS:
                if u not in users:
                    users.append(u)

            # Додаємо ручних юзернеймів для цього чату
            if chat_id in manual_users:
                for u in manual_users[chat_id]:
                    if u not in users:
                        users.append(u)

            # Додаємо того хто написав команду (якщо не бот)
            current_user = message.from_user
            if not current_user.is_bot:
                current_name = f"@{current_user.username}" if current_user.username else current_user.first_name
                if current_name not in users:
                    users.append(current_name)

            # Зберігаємо в кеш
            chat_members_cache[chat_id] = users
            print(f"✅ Завантажено {len(users)} учасників для чату {chat_id}")
            return users
    except Exception as e:
        print(f"❌ Помилка отримання учасників: {e}")

    # Додаємо стандартних юзернеймів навіть якщо адміністраторів не вдалося отримати
    users.extend(DEFAULT_USERS)

    # Додаємо ручних юзернеймів навіть якщо адміністраторів не вдалося отримати
    if chat_id in manual_users:
        users.extend(manual_users[chat_id])

    # Якщо не вдалося - повертаємо дефолтний список
    if not users:
        print(f"⚠️ Не вдалося отримати учасників, використовую дефолт")
        return ["@default_user"]
    return users


def get_random_user(message, exclude_bot=True):
    """Отримує випадкового користувача з чату"""
    users = get_chat_members(message)

    # Виключаємо тільки бота
    if exclude_bot:
        bot_name = f"@{bot.get_me().username}"
        if bot_name in users and len(users) > 1:
            users = [u for u in users if u != bot_name]

    if users:
        return random.choice(users)
    return "@unknown"


def get_user_from_message(message):
    """Отримує юзернейм з повідомлення (reply) або випадкового"""
    # Якщо є reply на повідомлення
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if user.username:
            return f"@{user.username}"
        else:
            return f"{user.first_name}"
    
    # Якщо згадали когось в тексті (@username)
    if message.text and '@' in message.text:
        words = message.text.split()
        for word in words:
            if word.startswith('@') and len(word) > 1:
                return word.split('?')[0].split(',')[0].split('!')[0]
    
    # Випадковий з чату
    return get_random_user(message)


# Причини для /pidor
PIDOR_REASONS = [
    "бо він сам так сказав",
    "бо сьогодні його день",
    "бо він перший попався",
    "бо він це заслужив",
    "бо так вирішила доля",
    "бо він вчора щось зробив",
    "бо він дивно подивився",
    "бо він занадто голосно дихав",
    "бо він не відповів вчасно",
    "бо він неправильно народився",
    "бо він їсть борщ без сала",
    "бо він ходить в взутті вдома",
    "бо він лайкає пости в 3 ранку",
    "бо він пише 'спс' замість 'дякую'",
    "бо він носить штани завеликі",
    "бо він сміється як гієна",
    "бо він вкрав чужий стікер",
    "бо він пише з помилками",
    "бо він читає чужі повідомлення",
    "бо він заходить в чат і мовчить",
    "бо він відправляє голосові",
    "бо він не дивиться повідомлення",
]

# Жорсткі образи
HARD_INSULTS = [
    "ти гнида",
    "ти мразота",
    "ти відмудок",
    "ти виродок",
    "ти недоносок",
    "ти сміття",
    "ти покидьок",
    "ти гандон",
    "ти чмо",
    "ти шавка",
    "ти шакал",
    "ти падло",
    "ти стерво",
    "ти гадина",
    "ти зрада",
    "ти бидло",
    "ти бичара",
    "ти гопнік",
    "ти алкаш",
    "ти наркоман",
    "ти псих",
    "ти ідіот",
    "ти дебіл",
    "ти тупий",
    "ти кретин",
    "ти імбецил",
    "ти недоумок",
    "ти виродок природи",
    "ти помилка еволюції",
    "ти генетичний брак",
    "ти соціальне дно",
    "ти людський відстій",
    "ти розумом обділений",
    "ти совісті не маєш",
    "ти честь загубив",
    "ти гідність просрав",
    "ти совість пропив",
    "ти мізки проїв",
    "ти життя злив",
    "ти все просрав",
    "ти син шлюхи",
    "ти хуєсос"
]

# Ображання для /insult
INSULTS = [
    "ти виглядаєш як недосмажений беляш",
    "твій IQ впав нижче за твій зріст",
    "ти як та вічка — всім заважаєш і ніхто не знає навіщо ти тут",
    "ти розумний як пробка, гострий як м'ячик",
    "твоя голова пустіша за гаманець після п'ятниці",
    "ти як оновлення Windows — ніхто тебе не чекав",
    "ти виглядаєш як скріншот з чужого життя",
    "твій мозьк зараз курить в сторонці",
    "ти як та кнопочка 'Esc' — нікому не потрібен",
    "ти розумом не вийшов, зате вийшов із чату",
    "ти як та папка 'Інше' — незрозуміло і не потрібно",
    "твоя думка важлива, але ніхто не питає",
    "ти як той Wi-Fi — то є, то немає",
    "ти виглядаєш як помилка 404",
    "ти як та сіль — без тебе краще",
    "ти як той додаток — постійно висиш",
    "ти як та реклама — дратуєш всіх",
    "ти як той спам — ніхто не просив",
    "ти як той вірус — тебе б видалити",
    "ти як той смітник — повний відходів",
    "ти як та пліснява — розповсюджуєшся",
    "ти як той запах — неприємний",
    "ти як та пляма — не відмиваєшся",
    "ти як той шум — дратуєш",
    "ти як той біль — постійно нагадуєш",
]

# Приниження для /roast
ROASTS = [
    "ти як та кавова гуща — ніхто не знає що з тобою робити",
    "ти настільки тупий, що коли побачив 'хмару' подумав що це iCloud",
    "ти як та кнопка 'Any' — завжди не там де треба",
    "ти настільки страшний, що коли ти народився — лікарі плакали",
    "ти як та флешка на 128GB — повний, але ніхто не відкриває",
    "ти настільки бідний, що навіть думки бідні",
    "ти як той додаток — всі видаляють",
    "ти настільки самотній, що навіть твій телефон в режимі польоту",
    "ти як та піца без сиру — нікому не потрібен",
    "ти настільки тупий, що думаєш що Netflix це пральний порошок",
    "ти як той мем — смішно тільки перший раз",
    "ти настільки огидний, що навіть комарі тебе кусають з відстані",
    "ти як та кнопка 'Прийняти всі' — ніхто не читає",
    "ти настільки слабкий, що навіть твій пароль '123456'",
    "ти настільки тупий, що думаєш що Amazon це річка",
    "ти настільки страшний, що дзеркало відвертається",
    "ти настільки дурний, що думаєш що LinkedIn це соцмережа для бідних",
    "ти настільки бідний, що навіть тінь від тебе відійшла",
    "ти настільки огидний, що навіть тінь твоя смердить",
    "ти настільки тупий, що думаєш що Tesla це просто машина",
]

# Передбачення для /fortune
FORTUNES = [
    "Сьогодні тобі пощастить, але не сильно.",
    "Хтось сцить на тебе згори. Тримай парасольку.",
    "Не їж сьогодні жовте — погана прикмета.",
    "Твій день буде нормальним, на відміну від тебе.",
    "Зараз би пива, але тобі не можна.",
    "Сьогодні ідеальний день щоб нічого не робити.",
    "Хтось думає про тебе. Сподіваємось це не податкова.",
    "Твоя удача сьогодні як твій баланс — на нулі.",
    "Зірки кажуть: ляж і леж.",
    "Сьогодні день великих можливостей. Але не для тебе.",
    "Твоє щастя вже близько. Але ще не сьогодні.",
    "Якщо сьогодні п'ятниця — тобі пощастить. Якщо ні — сци.",
    "Тобі сьогодні пощастить знайти проблеми.",
    "Хтось хоче тебе побити. Тримайся подалі.",
    "Сьогодні не твій день. Завтра теж ні.",
]

# Оцінки для /rate
RATE_COMMENTS = {
    1: "1/10. Ти як та пляма — ніхто не знає звідки ти взявся.",
    2: "2/10. Навіть двійка — це занадто багато для тебе.",
    3: "3/10. Ти старався, але не дуже.",
    4: "4/10. Хоча б не одиниця, вже добре.",
    5: "5/10. Золота середина для сірої мишки.",
    6: "6/10. Нормально, але могл�� б бути гірше.",
    7: "7/10. Ого, ти майже людина!",
    8: "8/10. Ти сьогодні виглядаєш як людина, а не як помилка.",
    9: "9/10. Майже ідеал, але до ідеалу ще далеко.",
    10: "10/10. Ти сьогодні виглядаєш краще ніж зазвичай. Не звикай.",
}

# Команда /whosgay
GAY_REASONS = [
    "бо він носить рожеві шкарпетки",
    "бо він слухає Брітні Спірс",
    "бо він вміє готувати",
    "бо він ходить в душ щодня",
    "бо він знає що таке skincare",
    "бо він не пахне як підвал",
    "бо він вміє одягатися",
    "бо він не ходить в майці-алкоголичці",
    "бо він дивиться російські серіали",
    "бо він любить піци з ананасами",
    "бо він пише з великої літери",
    "бо він ходить в спортзал",
]

# Команда /bomba
BOMBA_PHRASES = [
    "🚨 БУМ! 🚨 Твій мозьк щойно вибухнув від цієї інформації!",
    "💥 БАБАХ! 💥 Ти це серйозно запитав?",
    "🧨 БОМБА! 🧨 Я зараз вибухну від сміху!",
    "💣 КАБУМ! 💣 Твоє питання — це просто щось!",
    "🔥 ВИБУХ! 🔥 Я зараз розірвуся від емоцій!",
    "💢 ГРИБ! 💢 Це було занадто сильно!",
]

# Команда /crazy
CRAZY_FACTS = [
    "ти коли-небудь думав що ти якось живеш?",
    "ти знаєш що ти дихаєш прямо зараз?",
    "ти усвідомлюєш що ти існуєш?",
    "ти коли-небудь бачив себе ззаду?",
    "ти знаєш що ти моргаєш кожні 5 секунд?",
    "ти розумієш що ти читаєш це зараз?",
    "ти знаєш що ти вже прочитав це?",
]

# Команда /shower
SHOWER_THOUGHTS = [
    "а що як ти насправді ніхто?",
    "а що як всі твої друзі це боти?",
    "а що як ти живеш в симуляції?",
    "а що як ти вже помер?",
    "а що як ти ніколи не існував?",
    "а що як це все сон?",
]

# Команда /kickme
KICKME_PHRASES = [
    "Якби я міг, я б тебе вже вигнав з цього чату.",
    "Ти серйозно хочеш щоб тебе вигнали? Ну тримайся.",
    "Я б вигнав, але мені ліньки. Сам йди.",
    "Вигнати? Та ти ж тут найсмачніший!",
    "Я не виганяю, я просто ігнорую.",
]

# Команда /slap
SLAP_PHRASES = [
    "отримай ляпаса і не сци!",
    "ось тобі по пиці!",
    "тримай стусана!",
    "на тобі копняка!",
    "ось тобі піджопника!",
    "тримай ляща!",
    "на тобі стусана по пиці!",
    "ось тобі доброго ранку в пицю!",
]

# Команда /fact
FACTS = [
    "ти коли-небудь замислювався що ти ніхто?",
    "ти знаєш що ніхто не читає ці факти?",
    "ти розумієш що це просто текст?",
    "ти усвідомлюєш що ти витрачаєш час?",
    "ти знаєш що це нічого не змінить?",
]

# Команда /top
TOP_CATEGORIES = [
    "найбільший підор",
    "найбільший гей",
    "найбільший лох",
    "на��������більший бич",
    "найбільший алкаш",
    "найбільший наркоман",
    "найбільший псих",
    "найбільший ідіот",
    "найбільший дебіл",
    "найбільший чмошник",
]


@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"📍 /start отримано від {message.from_user.id}")
    text = """🔥 **TRASH BOT** — твій новий улюблений бот для трешу!

Я автоматично бачу всіх учасників чату і можу ображати кожного з них!

**Команди:**
/pidor — хто сьогодні підор
/roast — жорстке приниження
/insult — образливе слово
/hardinsult — дуже жорсткі образи
/rate — оцінка людини
/fortune — передбачення
/whosgay — хто гей сьогодні
/kickme — хочу вигнати себе
/slap — дати ляпаса
/fact — випадковий факт
/choose — обрати когось
/такні — питання Так/Ні

🐷 **Гра "Вирости Хряка":**
/grow — отримати хряка
/feed — нагодувати (раз на 12 год)
/my — показати хряка
/name — змінити ім'я
/hryaketop — топ хряків
/achievements — досягнення
/duel — виклик на дуель (inline)

📊 **Статистика:**
/stats — статистика чату
/leaderboard — топ за тиждень
/activity — активність

/members — показати учасників
/clearcache — очистити кеш
/mute — замути (адміни)
/provin — дати провину (адміни)
/warn — попередження (адміни)
/ban — забанити (адміни)
/del — видалити (адміни)
/pin — закріпити (адміни)
/help — всі команди
/menu — inline меню

**Як використовувати:**
- Просто напиши команду в чаті
- Або відповідай на повідомлення командою
- Або згадай когось @username

Додай мене в чат і я автоматично побачу всіх учасників!"""
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = """📜 **ПОВНИЙ СПИСОК КОМАНД:**

🎯 **Образливі:**
/pidor — хто сьогодні підор
/roast — жорстке приниження
/insult — образити когось
/hardinsult — дуже жорсткі образи
/slap — дати ляпаса комусь

🔮 **Передбачення:**
/fortune — передбачення на день
/whosgay — хто гей сьогодні
/rate — оцінка тебе від бота

🤯 **Розваги:**
/fact — випадковий факт
/choose — обрати когось
/top — рейтинг чату
/такні — питання Так/Ні

🐷 **Гра "Вирости Хряка":**
/grow — отримати хряка
/feed — нагодувати хряка (раз на 12 год)
/my — показати свого хряка
/name — змінити ім'я хряка
/hryaketop — топ хряків чату
/globaltop — глобальний топ хряків (всі чати)
/achievements — досягнення
/duel — виклик на дуель (inline) чату

📊 **Статистика:**
/stats — статистика чату
/leaderboard — топ балакунів за тиждень
/activity — активність користувачів

👥 **Чат:**
/members — показати всіх учасників
/adduser — додати юзернейма
/removeuser — видалити юзернейма
/clearcache — очистити кеш
/random — випадковий юзер
/kickme — хочу вигнати себе

🔇 **Мут (адміни):**
/mute — замути (відповідь + /mute 10)
/unmute — розмутити

😈 **Провини (адміни):**
/provin — дати провину (відповідь + /provin 10)
/unprovin — зняти провину
/provinlist — список провинних

⚠️ **Попередження (адміни):**
/warn — видати попередження (відповідь + /warn причина)
/warnings — показати попередження
/clearwarns — очистити попередження

🚫 **Бан (адміни):**
/ban — забанити назавжди (відповідь)
/unban — розбанити (відповідь)

📌 **Інше (адміни):**
/del — видалити повідомлення (відповідь)
/pin — закріпити повідомлення (відповідь)
/unpin — відкріпити
/spam — інфо про спам контроль

⚙️ **Інше:**
/start — привітання
/help — ця допомога

**Як використовувати:**
1. Відповідай на повідомлення — команда буде до тієї людини
2. Згадай @username в повідомленні
3. Просто напиши команду — обере випадкового з чату
4. Використовуй /adduser щоб додати друзів в список
5. **Inline меню:** Напиши /menu або натисни на рядок і введи @bot (пробіл)

⚠️ Всі команди працюють з рандомом. Не сприймай серйозно!"""
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['members'])
def show_members(message):
    """Показати всіх учасників чату"""
    users = get_chat_members(message)
    if len(users) <= 20:
        text = "👥 Учасники чату:\n" + "\n".join(users)
    else:
        text = f"👥 Учасники чату ({len(users)} осіб):\n" + "\n".join(users[:20]) + f"\n... і ще {len(users) - 20}"
    bot.reply_to(message, text)


@bot.message_handler(commands=['clearcache'])
def clear_cache(message):
    """Очистити кеш учасників"""
    chat_id = message.chat.id
    if chat_id in chat_members_cache:
        del chat_members_cache[chat_id]
        bot.reply_to(message, "✅ Кеш учасників очищено! Тепер я завантажу новий список.")
    else:
        bot.reply_to(message, "✅ Кеш і так чистий. Завантажую свіжий список учасників...")
        get_chat_members(message)


@bot.message_handler(commands=['adduser'])
def add_user(message):
    """Додати юзернейма в список чату"""
    chat_id = message.chat.id
    
    # Отримуємо юзернейм з reply або з тексту
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if user.username:
            username = f"@{user.username}"
        else:
            username = user.first_name
    elif message.text and len(message.text.split()) > 1:
        username = message.text.split()[1]
        if not username.startswith('@'):
            username = f"@{username}"
    else:
        bot.reply_to(message, "❌ Використовуй: /adduser @username або відповідай на повідомлення")
        return
    
    # Ініціалізуємо список якщо немає
    if chat_id not in manual_users:
        manual_users[chat_id] = []
    
    # Додаємо якщо ще немає
    if username not in manual_users[chat_id]:
        manual_users[chat_id].append(username)
        bot.reply_to(message, f"✅ {username} додано в список чату!")
        
        # Зб��рігаємо в БД
        save_manual_users_to_db()
        
        # Оновлюємо кеш
        if chat_id in chat_members_cache:
            if username not in chat_members_cache[chat_id]:
                chat_members_cache[chat_id].append(username)
    else:
        bot.reply_to(message, f"⚠️ {username} вже в списку")


@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    """Видалити юзернейма зі списку чату"""
    chat_id = message.chat.id
    
    if message.text and len(message.text.split()) > 1:
        username = message.text.split()[1]
        if not username.startswith('@'):
            username = f"@{username}"
    else:
        bot.reply_to(message, "❌ Використовуй: /removeuser @username")
        return
    
    if chat_id in manual_users and username in manual_users[chat_id]:
        manual_users[chat_id].remove(username)
        bot.reply_to(message, f"✅ {username} видалено зі списку!")
        
        # Зберігаємо в БД
        save_manual_users_to_db()
        
        # Оновлюємо кеш
        if chat_id in chat_members_cache and username in chat_members_cache[chat_id]:
            chat_members_cache[chat_id].remove(username)
    else:
        bot.reply_to(message, f"⚠️ {username} не знайдено в списку")


@bot.message_handler(commands=['mute'])
def mute_user(message):
    """Замутити користувача (реальний мут, тільки для адмінів)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Перевіряємо чи адмін
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    # Отримуємо к��ристувача з reply
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        target_id = user.id
        target_name = f"@{user.username}" if user.username else user.first_name
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення з командою /mute!\n\nПриклад:\n/mute 10 (відповідь на повідомлення)")
        return

    # Не можна замутити самого себе або бота
    if target_id == user_id:
        bot.reply_to(message, "❌ Не можна замутити самого себе!")
        return

    bot_me = bot.get_me()
    if target_id == bot_me.id:
        bot.reply_to(message, "❌ Не можна замутити бота!")
        return

    # Отримуємо час муту з тексту (друге слово після команди)
    try:
        parts = message.text.split()
        if len(parts) > 1 and parts[1].isdigit():
            minutes = int(parts[1])
        else:
            minutes = 10  # За замовчуванням 10 хв
    except (ValueError, IndexError):
        minutes = 10

    # Реальний мут через Telegram API
    try:
        bot.restrict_chat_member(
            chat_id,
            target_id,
            until_date=int(time.time() + (minutes * 60)),
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.reply_to(message, f"🔇 {target_name} замучено на {minutes} хв! Тепер не може писати в чаті!")
    except Exception as e:
        bot.reply_to(message, f"❌ Не вдалося замутити: {e}")


@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    """Розмутити користувача (реальний мут, тільки для адмінів)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Перевіряємо чи адмін
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    # Отримуємо користувача з reply
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        target_id = user.id
        target_name = f"@{user.username}" if user.username else user.first_name
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення з командою /unmute!")
        return

    # Не можна розмутити самого себе або бота
    if target_id == user_id:
        bot.reply_to(message, "❌ Не можна розмутити самого себе!")
        return

    bot_me = bot.get_me()
    if target_id == bot_me.id:
        bot.reply_to(message, "❌ Не можна розмутити бота!")
        return

    # Знімаємо мут через API
    try:
        bot.restrict_chat_member(
            chat_id,
            target_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.reply_to(message, f"✅ {target_name} розмучено! Тепер може писати (але краще б подумав)")
    except Exception as e:
        bot.reply_to(message, f"❌ Не вдалося розмутити: {e}")


@bot.message_handler(commands=['provin'])
def provin_user(message):
    """Провина - бот ��ідповідає образою на кожне повідомлення (тільки для адмінів)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Перевіряємо чи адмін
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    # Отримуємо користувача з reply
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        target_id = user.id
        target_name = f"@{user.username}" if user.username else user.first_name
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення з командою /provin!\n\nПриклад:\n/provin 10 (відповідь на повідомлення)")
        return

    # Не можна дати провину самому собі або боту
    if target_id == user_id:
        bot.reply_to(message, "❌ Не можна дати провину самому собі!")
        return

    bot_me = bot.get_me()
    if target_id == bot_me.id:
        bot.reply_to(message, "❌ Не можна дати провину боту!")
        return

    # Отримуємо час провини з тексту (друге слово після команди)
    try:
        parts = message.text.split()
        if len(parts) > 1 and parts[1].isdigit():
            minutes = int(parts[1])
        else:
            minutes = 10  # За замовчуванням 10 хв
    except (ValueError, IndexError):
        minutes = 10

    # Встановлюємо провину
    if chat_id not in provin_users:
        provin_users[chat_id] = {}

    expire_time = time.time() + (minutes * 60)
    provin_users[chat_id][target_id] = expire_time

    bot.reply_to(message, f"😈 {target_name} отримав провину на {minutes} хв! Тепер кожне його повідомлення буде образою!")


@bot.message_handler(commands=['unprovin'])
def unprovin_user(message):
    """Зняти провину (тільки для адмінів)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Перевіряємо чи адмін
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    # Отримуємо користувача з reply
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        target_id = user.id
        target_name = f"@{user.username}" if user.username else user.first_name
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення з командою /unprovin!")
        return

    # Знімаємо провину
    if chat_id in provin_users and target_id in provin_users[chat_id]:
        del provin_users[chat_id][target_id]
        bot.reply_to(message, f"✅ {target_name} знято провину! Радій бо ти вільний")
    else:
        bot.reply_to(message, f"⚠️ {target_name} не має провини")


@bot.message_handler(commands=['provinlist'])
def list_provin(message):
    """Показати список провинних"""
    chat_id = message.chat.id

    if chat_id not in provin_users or not provin_users[chat_id]:
        bot.reply_to(message, "📭 Немає провинних в цьому чаті")
        return

    text = "😈 Провинні:\n"
    current_time = time.time()

    for uid, expire_time in list(provin_users[chat_id].items()):
        if expire_time > current_time:
            remaining = int((expire_time - current_time) / 60)
            text += f"• {uid} (ще {remaining} хв)\n"
        else:
            del provin_users[chat_id][uid]

    bot.reply_to(message, text)


@bot.message_handler(commands=['pidor'])
def pidor(message):
    who = get_user_from_message(message)
    reason = random.choice(PIDOR_REASONS)
    bot.reply_to(message, f"🎯 Сьогодні підор — {who} {reason} 🎉")


@bot.message_handler(commands=['roast'])
def roast(message):
    who = get_user_from_message(message)
    roast_text = random.choice(ROASTS)
    bot.reply_to(message, f"🔥 {who}, {roast_text} 🔥")


@bot.message_handler(commands=['insult'])
def insult(message):
    who = get_user_from_message(message)
    insult_text = random.choice(INSULTS)
    bot.reply_to(message, f"💢 {who}, {insult_text} 💢")


@bot.message_handler(commands=['hardinsult'])
def hard_insult(message):
    who = get_user_from_message(message)
    insult_text = random.choice(HARD_INSULTS)
    bot.reply_to(message, f"🖕 {who}, {insult_text} 🖕")


@bot.message_handler(commands=['rate'])
def rate(message):
    rating = random.randint(1, 10)
    comment = RATE_COMMENTS[rating]
    who = get_user_from_message(message)
    bot.reply_to(message, f"⭐ {who}: {comment}")


@bot.message_handler(commands=['fortune'])
def fortune(message):
    who = get_user_from_message(message)
    bot.reply_to(message, f"🔮 {who}, {random.choice(FORTUNES)}")


@bot.message_handler(commands=['whosgay'])
def whosgay(message):
    who = get_user_from_message(message)
    reason = random.choice(GAY_REASONS)
    bot.reply_to(message, f"🏳️‍🌈 {who} — гей сьогодні, {reason} 🏳️‍🌈")


@bot.message_handler(commands=['random'])
def random_user(message):
    user = get_random_user(message)
    bot.reply_to(message, f"🎲 Випадковий юзер: {user}")


@bot.message_handler(commands=['kickme'])
def kickme(message):
    bot.reply_to(message, random.choice(KICKME_PHRASES))


@bot.message_handler(commands=['slap'])
def slap(message):
    who = get_user_from_message(message)
    bot.reply_to(message, f"👋 {who}, {random.choice(SLAP_PHRASES)}")


@bot.message_handler(commands=['fact'])
def fact(message):
    bot.reply_to(message, f"📌 {random.choice(FACTS)}")


@bot.message_handler(commands=['choose'])
def choose(message):
    who = get_random_user(message)
    bot.reply_to(message, f"🎲 Я обираю {who}!")


@bot.message_handler(commands=['такні'])
def takni(message):
    """Команда !такні - бот обирає випадкового юзера і каже Так чи Ні"""
    who = get_random_user(message)
    answer = random.choice(TAKNI_ANSWERS)
    bot.reply_to(message, f"🎲 {who}: {answer}")


@bot.message_handler(commands=['top'])
def top(message):
    """Створює рейтинг чату"""
    users = get_chat_members(message)
    if len(users) < 2:
        bot.reply_to(message, "😕 В чаті замало людей для рейтингу")
        return
    
    category = random.choice(TOP_CATEGORIES)
    top3 = random.sample(users, min(3, len(users)))
    
    text = f"🏆 **ТОП: {category}**\n\n"
    emojis = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top3):
        text += f"{emojis[i]} {user}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


# Обробник додавання бота в чат
@bot.my_chat_member_handler()
def on_chat_member_update(message):
    """Привітання коли бота додають в новий чат"""
    if message.new_chat_member.status in ['member', 'administrator', 'creator']:
        chat_id = message.chat.id
        # Очищаємо кеш для цього чату
        if chat_id in chat_members_cache:
            del chat_members_cache[chat_id]

        # Завантажуємо адміністраторів
        try:
            admins = bot.get_chat_administrators(chat_id)
            users = []
            for admin in admins:
                user = admin.user
                if not user.is_bot:
                    if user.username:
                        users.append(f"@{user.username}")
                    else:
                        users.append(f"{user.first_name}")

            # Додаємо стандартних юзернеймів з коду
            for u in DEFAULT_USERS:
                if u not in users:
                    users.append(u)

            # Додаємо ручних юзернеймів якщо є
            if chat_id in manual_users:
                for u in manual_users[chat_id]:
                    if u not in users:
                        users.append(u)

            chat_members_cache[chat_id] = users
            print(f"✅ Завантажено {len(users)} учасників для чату {chat_id}")
        except Exception as e:
            print(f"❌ Помилка завантаження учасників: {e}")

        # Привітальне повідомлення
        welcome_text = """🔥 **TRASH BOT** тепер у цьому чаті!

Привіт, я бот для розваг і трешу! 😈

📜 **Мої команди:**

🎯 **Образливі:**
/pidor — хто сьогодні підор
/roast — жорстке приниження
/insult — образливе слово
/hardinsult — дуже жорсткі образи
/slap — дати ляпаса

🔮 **Передбачення:**
/fortune — передбачення
/whosgay — хто гей сьогодні
/rate — оцінка людини

🤯 **Розваги:**
/fact — випадковий факт
/choose — обрати когось
/такні — питання Так/Ні

🐷 **Гра "Вирости Хряка":**
/grow — отримати хряка
/feed — нагодувати (раз на 12 год)
/my — показати хряка
/name — змінити ім'я
/hryaketop — топ хряків
/achievements — досягнення
/duel — виклик на дуель (inline)

📊 **Статистика:**
/stats — статистика чату
/leaderboard — топ за тиждень
/activity — активність

👥 **Чат:**
/members — показати учасників
/adduser — додати юзернейма
/removeuser — видалити юзернейма

🔇 **Мут (адміни):**
/mute — замути на X хв (/mute 10)
/unmute — розмутити

😈 **Провина (адміни):**
/provin — дати провину (/provin 10)
/unprovin — зняти провину

⚠️ **Попередження (адміни):**
/warn — видати попередження
/warnings — показати попередження

🚫 **Бан (адміни):**
/ban — забанити назавжди
/unban — розбанити

📌 **Інше (адміни):**
/del — видалити повідомлення
/pin — закріпити повідомлення
/spam — спам контроль

⚙️ **Допомога:**
/help — повна інструкція

**Як використовувати:**
- Просто напиши команду
- Або відповідай на повідомлення
- Або згадай @username
- Адміни можуть мутити командою /mute
- Адміни можуть дати провину командою /provin

⚠️ Не сприймай серйозно, це просто розвага!"""

        bot.send_message(chat_id, welcome_text, parse_mode="Markdown")


logger.info("=" * 50)
logger.info("🚀 TRASH BOT ЗАПУЩЕНИЙ...")
logger.info("=" * 50)
logger.info("💡 Додай бота в чат і зроби адміном для повного функціоналу!")
logger.info("📝 Назва: TRASH BOT")
logger.info("📄 Опис: Бот для розваг в чатах.")
logger.info("=" * 50)

# ============================================
# СТАТИСТИКА ЧАТУ
# ============================================

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    """Статистика чату"""
    chat_id = message.chat.id
    
    chat_stats = get_chat_stats(chat_id)
    
    if not chat_stats:
        bot.reply_to(message, "📭 Ще немає статистики в цьому чаті!")
        return
    
    total_messages = sum(s['count'] for s in chat_stats)
    top_count = min(10, len(chat_stats))
    
    text = f"📊 **Статистика чату**\n\n"
    text += f"Всього повідомлень: {total_messages}\n"
    text += f"Активних користувачів: {len(chat_stats)}\n\n"
    text += f"**Топ балакунів:**\n"
    
    emojis = ["🥇", "🥈", "🥉"]
    for i, stat in enumerate(chat_stats[:top_count]):
        if i < 3:
            emoji = emojis[i]
        else:
            emoji = f"{i+1}."
        
        username = stat.get('username', 'Unknown')
        if not username.startswith('@'):
            username = f"@{username}" if username else "Анонім"
        
        text += f"{emoji} {username} - {stat['count']} повід.\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['leaderboard'])
def leaderboard_cmd(message):
    """Топ балакунів за тиждень"""
    chat_id = message.chat.id
    
    chat_stats = get_chat_stats(chat_id)
    
    if not chat_stats:
        bot.reply_to(message, "📭 Ще немає статистики в цьому чаті!")
        return
    
    # Фільтруємо за тиждень (7 днів = 604800 сек)
    week_ago = time.time() - 604800
    week_stats = [s for s in chat_stats if s.get('last_message', 0) > week_ago]
    week_stats.sort(key=lambda x: x['count'], reverse=True)
    
    if not week_stats:
        bot.reply_to(message, "📭 За тиждень ніхто не писав!")
        return
    
    text = "🏆 **Лідерборд за тиждень**\n\n"
    
    emojis = ["🥇", "🥈", "🥉"]
    for i, stat in enumerate(week_stats[:10]):
        if i < 3:
            emoji = emojis[i]
        else:
            emoji = f"{i+1}."
        
        username = stat.get('username', 'Unknown')
        if not username.startswith('@'):
            username = f"@{username}" if username else "Анонім"
        
        text += f"{emoji} {username} - {stat['count']} повід.\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['activity'])
def activity_cmd(message):
    """Активність користувачів"""
    chat_id = message.chat.id
    
    chat_stats = get_chat_stats(chat_id)
    
    if not chat_stats:
        bot.reply_to(message, "📭 Ще немає статистики в цьому чаті!")
        return
    
    now = time.time()
    day_ago = now - 86400
    week_ago = now - 604800
    
    today_active = len([s for s in chat_stats if s.get('last_message', 0) > day_ago])
    week_active = len([s for s in chat_stats if s.get('last_message', 0) > week_ago])
    
    text = f"""📈 **Активність чату**

👥 Всього користувачів: {len(chat_stats)}
📍 Активні сьогодні: {today_active}
📍 Активні за тиждень: {week_active}

"""
    
    # Хто онлайн зараз (писав за останні 5 хв)
    five_min_ago = now - 300
    online = [s for s in chat_stats if s.get('last_message', 0) > five_min_ago]
    
    if online:
        text += "**Зараз онлайн:**\n"
        for stat in online[:5]:
            username = stat.get('username', 'Unknown')
            if not username.startswith('@'):
                username = f"@{username}" if username else "Анонім"
            text += f"• {username}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


# ============================================
# АДМІНСЬКІ КОМАНДИ
# ============================================

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    """Забанити користувача (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    logger.info(f"🚫 /ban: chat_id={chat_id}, user_id={user_id}")

    if not is_admin(chat_id, user_id):
        logger.warning(f"❌ /ban: користувач {user_id} не адмін")
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб забанити!")
        return

    if target.id == user_id:
        bot.reply_to(message, "❌ Не можна забанити самого себе!")
        return

    if target.is_bot:
        bot.reply_to(message, "❌ Не можна забанити бота!")
        return

    logger.info(f"🚫 Бан: {target.id} ({target.first_name})")
    ban_user(chat_id, target.id)

    try:
        bot.kick_chat_member(chat_id, target.id)
        bot.reply_to(message, f"✅ {target.first_name} забанено назавжди!")
        logger.info(f"✅ {target.first_name} забанено")
    except Exception as e:
        logger.error(f"❌ Помилка бану: {e}")
        bot.reply_to(message, f"❌ Не вдалося забанити: {e}")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    """Розбанити користувача (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб розбанити!")
        return
    
    unban_user(chat_id, target.id)
    bot.reply_to(message, f"✅ {target.first_name} розбанено!")


@bot.message_handler(commands=['warn'])
def warn_cmd(message):
    """Попередження (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    logger.info(f"⚠️ /warn: chat_id={chat_id}, user_id={user_id}")

    if not is_admin(chat_id, user_id):
        logger.warning(f"❌ /warn: користувач {user_id} не адмін")
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб видати попередження!")
        return

    if target.id == user_id:
        bot.reply_to(message, "❌ Не можна видати попередження самому собі!")
        return

    if target.is_bot:
        bot.reply_to(message, "❌ Не можна видати попередження боту!")
        return

    # Отримуємо причину
    parts = message.text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "Без причини"

    warn_count = add_warn(chat_id, target.id, target.username or target.first_name, reason)
    logger.info(f"⚠️ Попередження: {target.first_name} ({warn_count}/3)")

    if warn_count >= 3:
        # Автоматичний бан після 3 попереджень
        ban_user(chat_id, target.id)
        try:
            bot.kick_chat_member(chat_id, target.id)
            bot.reply_to(message, f"⚠️ {target.first_name} отримав 3 попередження і забанено!")
            logger.info(f"✅ {target.first_name} забанено після 3 попереджень")
        except:
            bot.reply_to(message, f"⚠️ {target.first_name} отримав 3 попередження! (не вдалося забанити)")
            logger.warning(f"⚠️ Не вдалося забанити {target.first_name}")
    else:
        bot.reply_to(message, f"⚠️ {target.first_name} отримав попередження ({warn_count}/3)!\nПричина: {reason}")


@bot.message_handler(commands=['warnings'])
def warnings_cmd(message):
    """Показати попередження користувача"""
    chat_id = message.chat.id
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user
    
    warns = get_warns(chat_id, target.id)
    
    if not warns:
        bot.reply_to(message, f"✅ У {target.first_name} немає попереджень!")
        return
    
    text = f"⚠️ **Попередження {target.first_name}:**\n\n"
    for i, warn in enumerate(warns, 1):
        warn_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(warn['time']))
        text += f"{i}. {warn['reason']} ({warn_time})\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['clearwarns'])
def clearwarns_cmd(message):
    """Очистити попередження (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб очистити попередження!")
        return
    
    clear_warns(chat_id, target.id)
    bot.reply_to(message, f"✅ Попередження {target.first_name} очищено!")


@bot.message_handler(commands=['del'])
def del_cmd(message):
    """Видалити повідомлення (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    if message.reply_to_message:
        try:
            bot.delete_message(chat_id, message.reply_to_message.message_id)
            bot.delete_message(chat_id, message.message_id)  # Видаляємо і команду
        except Exception as e:
            bot.reply_to(message, f"❌ Не вдалося видалити: {e}")
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб видалити!")


@bot.message_handler(commands=['pin'])
def pin_cmd(message):
    """Закріпити повідомлення (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    if message.reply_to_message:
        try:
            bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
            bot.reply_to(message, "✅ Повідомлення закріплено!")
        except Exception as e:
            bot.reply_to(message, f"❌ Не вдалося закріпити: {e}")
    else:
        bot.reply_to(message, "❌ Відповідай на повідомлення щоб закріпити!")


@bot.message_handler(commands=['unpin'])
def unpin_cmd(message):
    """Відкріпити повідомлення (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    try:
        bot.unpin_chat_message(chat_id)
        bot.reply_to(message, "✅ Повідомлення відкріплено!")
    except Exception as e:
        bot.reply_to(message, f"❌ Не вдалося відкріпити: {e}")


@bot.message_handler(commands=['spam'])
def spam_cmd(message):
    """Увімкнути/вимкнути спам контроль (тільки адміни)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адміністраторів!")
        return
    
    bot.reply_to(message, "📍 Спам контроль: 5 повідомлень за 10 секунд = мут на 1 хвилину\n\nБот автоматично мутить спаммерів!")


# Обробник спам контролю
@bot.message_handler(func=lambda m: True)
def spam_handler(message):
    """Перевірка на спам (ігнорує команди)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Ігноруємо команди - ПОВИННО БУТИ ПЕРШИМ!
    if message.text and message.text.startswith('/'):
        logger.debug(f"⏭️ Пропущено команду: {message.text}")
        return

    logger.debug(f"📨 Повідомлення: {message.text[:50] if message.text else 'no text'}")

    # Перевіряємо чи користувач в провині (образи у відповідь)
    if chat_id in provin_users and user_id in provin_users[chat_id]:
        expire_time = provin_users[chat_id][user_id]
        if time.time() < expire_time:
            logger.info(f"😈 Провина для {user_id}")
            bot.reply_to(message, random.choice(PROVIN_INSULTS))
            return
        else:
            del provin_users[chat_id][user_id]

    # Перевіряємо чи не адмін
    if is_admin(chat_id, user_id):
        return

    # Перевіряємо на спам
    if check_spam(chat_id, user_id):
        try:
            bot.restrict_chat_member(
                chat_id,
                user_id,
                until_date=int(time.time() + 60),
                can_send_messages=False
            )
            bot.reply_to(message, f"⚠️ {message.from_user.first_name} отримав мут за спам (1 хв)!")
        except:
            pass

    # Перевіряємо чи не замучений за спам
    is_muted, time_left = is_spam_muted(chat_id, user_id)
    if is_muted:
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        return

    # Додаємо повідомлення до статистики
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    add_message(chat_id, user_id, username)


logger.info("=" * 50)
logger.info("🚀 ПОЧАТОК POLLING...")
logger.info("=" * 50)

# Ініціалізація бази даних і завантаження даних
init_db()
load_from_db(hryaky_data, stats_data, warns_data, spam_data, manual_users)

# Встановлюємо кнопку меню для всіх нових чатів
try:
    bot.set_chat_menu_button(
        menu_button=types.MenuButtonWebApp(
            type="web_app",
            text="📋 Меню",
            web_app=types.WebAppInfo(url="https://t.me/trash1161_bot?start=menu")
        )
    )
    logger.info("✅ Кнопку меню встановлено")
except Exception as e:
    logger.warning(f"⚠️ Не вдалося встановити кнопку меню: {e}")

# АБО простіший варіант - Commands Menu (вбудоване меню Telegram)
try:
    # Встановлюємо список команд для BotFather
    bot.set_my_commands([
        types.BotCommand("start", "🚀 Запустити бота"),
        types.BotCommand("menu", "📋 Меню команд"),
        types.BotCommand("grow", "🐷 Отримати хряка"),
        types.BotCommand("feed", "🍽️ Нагодувати"),
        types.BotCommand("my", "📊 Мій хряк"),
        types.BotCommand("name", "✏️ Перейменувати хряка"),
        types.BotCommand("hryaketop", "🏆 Топ хряків чату"),
        types.BotCommand("globaltop", "🌍 Глобальний топ"),
        types.BotCommand("duel", "⚔️ Створити дуель"),
        types.BotCommand("achievements", "🏅 Досягнення"),
        types.BotCommand("pidor", "🎯 Хто підор"),
        types.BotCommand("roast", "🔥 Roast"),
        types.BotCommand("fortune", "🔮 Передбачення"),
        types.BotCommand("rate", "⭐ Оціпка"),
        types.BotCommand("help", "ℹ️ Допомога")
    ])
    logger.info("✅ Команди встановлено")
except Exception as e:
    logger.warning(f"⚠️ Не вдалося встановити команди: {e}")

# ============================================
# FLASK SERVER для Render (порт 10000)
# ============================================
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    """Головна сторінка"""
    return """
    <html>
        <head><title>TRASH BOT</title></head>
        <body>
            <h1>🤖 TRASH BOT is running!</h1>
            <p>Bot status: <strong>Online</strong></p>
            <p>Uptime: <span id="uptime"></span></p>
            <script>
                document.getElementById('uptime').innerText = new Date().toLocaleString();
            </script>
        </body>
    </html>
    """, 200

@flask_app.route('/health')
def health_check():
    """Health check для UptimeRobot"""
    return {"status": "ok", "timestamp": time.time()}, 200

@flask_app.route('/api/status')
def bot_status():
    """Статус бота"""
    return {
        "bot": "running",
        "flask": "ok",
        "polling": "active"
    }, 200

@flask_app.route('/ping')
def ping():
    """Ping для keep-alive"""
    return "pong", 200

def run_flask():
    """Запускає Flask сервер на порту Render"""
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# Запускаємо Flask в окремому потоці
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
logger.info(f"✅ Flask сервер запущено на порту {os.environ.get('PORT', 10000)}")

# ============================================
# KEEP-ALIVE: Періодичний ping для Render
# ============================================
def keep_alive():
    """Періодично робить запити щоб Render не присипав бота"""
    import urllib.request
    import urllib.error
    
    # Отримуємо URL з Render (пріоритети)
    render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
    
    # Якщо не знайдено, пробуємо сформувати з INTERNAL_PORT
    if not render_url:
        port = os.environ.get('PORT', '10000')
        render_url = f'http://0.0.0.0:{port}'
    
    logger.info(f"🌍 Render URL: {render_url}")
    logger.info(f"🔄 Keep-alive увімкнено (інтервал 2 хв)")
    
    ping_count = 0
    while True:
        try:
            # Робимо запит кожні 2 хвилини (менше ніж 5 хв таймаут Render)
            time.sleep(120)  # 2 хвилини
            ping_count += 1
            
            # Пробуємо різні ендпоінти
            endpoints = ['/ping', '/health', '/api/status']
            for endpoint in endpoints:
                try:
                    url = f"{render_url}{endpoint}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Render-KeepAlive/1.0'})
                    response = urllib.request.urlopen(req, timeout=5)
                    logger.info(f"💓 Keep-alive #{ping_count}: {endpoint} ✓ ({response.status})")
                    break
                except Exception as e:
                    logger.debug(f"⚠️ {endpoint} помилка: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Keep-alive помилка: {e}")

# Запускаємо keep-alive в окремому потоці
keep_alive_thread = Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

bot.polling(none_stop=True, interval=0)


# ============================================
# INLINE МЕНЮ
# ============================================

@bot.inline_handler(lambda query: query.query.lower().strip() == '')
def query_main_menu(inline_query):
    """Головне inline меню - показує хряка користувача"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id

    hryak = get_hryak(user_id, chat_type)

    # Створюємо inline кнопки
    markup = types.InlineKeyboardMarkup(row_width=3)

    # Кнопки гри
    btn_grow = types.InlineKeyboardButton("🐷 Отримати хряка", switch_inline_query="grow")
    btn_feed = types.InlineKeyboardButton("🍽️ Нагодувати", switch_inline_query="feed")
    btn_my = types.InlineKeyboardButton("📊 Мій хряк", switch_inline_query="my")
    btn_name = types.InlineKeyboardButton("✏️ Ім'я", switch_inline_query="name")
    btn_top = types.InlineKeyboardButton("🏆 Топ чату", switch_inline_query="top")
    btn_globaltop = types.InlineKeyboardButton("🌍 Глоб топ", switch_inline_query="globaltop")

    # Кнопки дуелей
    btn_duel = types.InlineKeyboardButton("⚔️ Дуель", switch_inline_query="duel")
    btn_achievements = types.InlineKeyboardButton("🏅 Досягнення", switch_inline_query="achievements")

    # Кнопки розваг
    btn_pidor = types.InlineKeyboardButton("🎯 Підор", switch_inline_query="pidor")
    btn_roast = types.InlineKeyboardButton("🔥 Roast", switch_inline_query="roast")
    btn_fortune = types.InlineKeyboardButton("🔮 Передбачення", switch_inline_query="fortune")
    btn_rate = types.InlineKeyboardButton("⭐ Оцінка", switch_inline_query="rate")

    markup.add(btn_grow, btn_feed, btn_my)
    markup.add(btn_name, btn_top, btn_globaltop)
    markup.add(btn_duel, btn_achievements)
    markup.add(btn_pidor, btn_roast)
    markup.add(btn_fortune, btn_rate)

    if hryak:
        header = f"🐷 Твій хряк: {hryak['name']} ({hryak['weight']} кг)\n\n"
    else:
        header = "❌ У тебе немає хряка! Отримай командою /grow\n\n"

    # Головна кнопка з хряком
    results = []

    if hryak:
        # Додаємо хряка як перший результат
        hryak_markup = types.InlineKeyboardMarkup()
        hryak_markup.add(types.InlineKeyboardButton("⚔️ Виклик на дуель", callback_data=f"duel_accept_{user_id}_{hryak['weight']}"))

        results.append(
            types.InlineQueryResultArticle(
                id='hryak',
                title=f'🐗 {hryak["name"]} ({hryak["weight"]} кг)',
                description='Натисни щоб відправити в чат',
                thumbnail_url='https://cdn-icons-png.flaticon.com/512/1998/1998610.png',
                input_message_content=types.InputTextMessageContent(
                    f"""🐷 **{hryak['name']}**

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів

⚔️ Натисни кнопку щоб викликати на дуель!""",
                    parse_mode="Markdown"
                ),
                reply_markup=hryak_markup
            )
        )

    results.append(
        types.InlineQueryResultArticle(
            id='1',
            title='📜 Головне меню TRASH BOT',
            description='Всі основні команди бота',
            thumbnail_url='https://cdn-icons-png.flaticon.com/512/1998/1998610.png',
            input_message_content=types.InputTextMessageContent(
                f"{header}📋 **МЕНЮ КОМАНД:**\n\n"
                "Обери команду нижче 👇",
                parse_mode="Markdown"
            ),
            reply_markup=markup
        )
    )

    bot.answer_inline_query(inline_query.id, results, cache_time=30)


@bot.inline_handler(lambda query: query.query.lower().strip() == 'grow')
def query_grow_inline(inline_query):
    """Inline для /grow"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id
    
    hryak = get_hryak(user_id, chat_type)
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔄 Оновити", switch_inline_query="my")
    markup.add(btn)
    
    if hryak:
        text = f"""🐷 **Вже маєш хряка!**

Ім'я: {hryak['name']}
Вага: {hryak['weight']} кг
Нагодовано: {hryak['feed_count']} разів

⏰ Годування доступне раз на 12 годин"""
    else:
        text = """🎉 **Отримай свого хряка!**

Напиши /grow в чаті щоб отримати першого хряка!

🐷 Вага: 1-20 кг (випадково)
🍽️ Годування: раз на 12 годин
⚔️ Дуелі: бийся з іншими!"""
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🐷 Отримати хряка',
            description='Створити свого першого хряка',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown"),
            reply_markup=markup
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'feed')
def query_feed_inline(inline_query):
    """Inline для /feed"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id
    
    hryak = get_hryak(user_id, chat_type)
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔄 Оновити", switch_inline_query="feed")
    markup.add(btn)
    
    if not hryak:
        text = "❌ Спочатку отримай хряка командою /grow!"
    else:
        now = time.time()
        time_left = 43200 - (now - hryak['last_feed'])
        if time_left <= 0:
            text = f"""🍽️ **Можна годувати!**

Напиши /feed в чаті щоб нагодувати хряка!

🐷 {hryak['name']}
⚖️ Поточна вага: {hryak['weight']} кг"""
        else:
            hours = int(time_left / 3600)
            minutes = int((time_left % 3600) / 60)
            text = f"""⏳ **Ще рано!**

Залишилось: {hours} год {minutes} хв

🐷 {hryak['name']}
⚖️ Поточна вага: {hryak['weight']} кг"""
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🍽️ Нагодувати хряка',
            description='Годування раз на 12 годин',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown"),
            reply_markup=markup
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'my')
def query_my_inline(inline_query):
    """Inline для /my"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id
    
    hryak = get_hryak(user_id, chat_type)
    
    markup = types.InlineKeyboardMarkup()
    btn_duel = types.InlineKeyboardButton("⚔️ Виклик на дуель", switch_inline_query="duel")
    btn_name = types.InlineKeyboardButton("✏️ Змінити ім'я", switch_inline_query="name")
    markup.add(btn_duel, btn_name)
    
    if not hryak:
        text = "❌ У тебе немає хряка! Напиши /grow"
    else:
        now = time.time()
        time_left = 43200 - (now - hryak['last_feed'])
        if time_left <= 0:
            feed_status = "✅ Можна годувати!"
        else:
            hours = int(time_left / 3600)
            minutes = int((time_left % 3600) / 60)
            feed_status = f"⏳ Ще {hours} год {minutes} хв"
        
        text = f"""🐷 **{hryak['name']}**

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів
🕐 Годування: {feed_status}

⚔️ Натисни "Виклик на дуель" щоб створити виклик!"""
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='📊 Мій хряк',
            description='Інформація про твого хряка',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown"),
            reply_markup=markup
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'top')
def query_top_inline(inline_query):
    """Inline для /hryaketop"""
    # Отримуємо з останнього чату де писав користувач
    chat_hryaky = []
    for key, hryak in hryaky_data.items():
        chat_hryaky.append(hryak)

    chat_hryaky.sort(key=lambda x: x['weight'], reverse=True)
    top_count = min(5, len(chat_hryaky))

    if not chat_hryaky:
        text = "📭 У цьому чаті ще немає хряків!"
    else:
        text = "🏆 **ТОП ХРЯКІВ ЧАТУ**\n\n"
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, hryak in enumerate(chat_hryaky[:top_count]):
            emoji = emojis[i] if i < 5 else f"{i+1}."
            text += f"{emoji} {hryak['name']} - {hryak['weight']} кг\n"

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔄 Оновити", switch_inline_query="top")
    markup.add(btn)

    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🏆 Топ хряків чату',
            description='Рейтинг хряків за вагою',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown"),
            reply_markup=markup
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'globaltop')
def query_globaltop_inline(inline_query):
    """Inline для /globaltop"""
    # Отримуємо всіх хряків з БД
    all_hryaky = []
    from db import get_connection
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key FROM hryaky')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            hryak = get_hryak_from_db(key)
            if hryak:
                all_hryaky.append(hryak)
        cursor.close()
        conn.close()

    all_hryaky.sort(key=lambda x: x['weight'], reverse=True)
    top_count = min(5, len(all_hryaky))

    if not all_hryaky:
        text = "📭 Ще немає хряків ніде!"
    else:
        text = "🌍 **ГЛОБАЛЬНИЙ ТОП ХРЯКІВ**\n\n"
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, hryak in enumerate(all_hryaky[:top_count]):
            emoji = emojis[i] if i < 5 else f"{i+1}."
            text += f"{emoji} {hryak['name']} - {hryak['weight']} кг\n"

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔄 Оновити", switch_inline_query="globaltop")
    markup.add(btn)

    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🌍 Глобальний топ',
            description='Рейтинг хряків всіх чатів',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown"),
            reply_markup=markup
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'achievements')
def query_achievements_inline(inline_query):
    """Inline для /achievements"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id
    
    hryak = get_hryak(user_id, chat_type)
    
    if not hryak:
        text = "❌ Спочатку отримай хряка!"
    else:
        text = "🏆 **Твої досягнення:**\n\n"
        unlocked_count = 0
        for ach_id, ach in ACHIEVEMENTS.items():
            try:
                if ach['condition'](hryak):
                    text += f"✅ {ach['name']}\n"
                    unlocked_count += 1
                else:
                    text += f"🔒 {ach['name']}\n"
            except:
                text += f"🔒 {ach['name']}\n"
        text += f"\n📊 Відкрито: {unlocked_count}/{len(ACHIEVEMENTS)}"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🏅 Досягнення',
            description='Твої відкриті досягнення',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'pidor')
def query_pidor_inline(inline_query):
    """Inline для /pidor"""
    text = "🎯 **ХТО СЬОГОДНІ ПІДОР?**\n\nНапиши /pidor в чаті щоб дізнатися!"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🎯 Підор',
            description='Дізнатися хто сьогодні підор',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'roast')
def query_roast_inline(inline_query):
    """Inline для /roast"""
    text = "🔥 **ЖОРСТКЕ ПРИНИЖЕННЯ**\n\nНапиши /roast в чаті!"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🔥 Roast',
            description='Жорстке приниження',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'fortune')
def query_fortune_inline(inline_query):
    """Inline для /fortune"""
    text = "🔮 **ПЕРЕДБАЧЕННЯ**\n\nНапиши /fortune в чаті!"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='🔮 Передбачення',
            description='Передбачення на день',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'rate')
def query_rate_inline(inline_query):
    """Inline для /rate"""
    text = "⭐ **ОЦІНКА**\n\nНапиши /rate в чаті щоб отримати оцінку!"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='⭐ Оцінка',
            description='Оцінка від бота',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])


@bot.inline_handler(lambda query: query.query.lower().strip() == 'name')
def query_name_inline(inline_query):
    """Inline для зміни імені"""
    text = "✏️ **ЗМІНИТИ ІМ'Я ХРЯКА**\n\nНапиши /name НовеІм'я в чаті!"
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title='✏️ Змінити ім\'я',
            description='Змінити ім\'я хряка',
            input_message_content=types.InputTextMessageContent(text, parse_mode="Markdown")
        )
    ])

@bot.inline_handler(lambda query: query.query.lower().strip() == 'duel')
def query_duel(inline_query):
    """Inline запит на дуель"""
    user_id = inline_query.from_user.id
    chat_type = inline_query.from_user.id
    
    hryak = get_hryak(user_id, chat_type)
    
    if not hryak:
        bot.answer_inline_query(inline_query.id, [
            types.InlineQueryResultArticle(
                id='1',
                title='❌ Немає хряка',
                description='Спочатку отримай хряка командою /grow',
                input_message_content=types.InputTextMessageContent(
                    '❌ У тебе немає хряка! Напиши /grow в чаті щоб отримати.'
                )
            )
        ])
        return
    
    # Створюємо inline кнопку з дуеллю
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        text=f"🐗 {hryak['name']} ({hryak['weight']} кг) - Виклик на дуель!",
        callback_data=f"duel_{user_id}_{hryak['weight']}"
    )
    markup.add(btn)
    
    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(
            id='1',
            title=f'🐗 {hryak["name"]} ({hryak["weight"]} кг)',
            description='Натисни щоб викликати на дуель!',
            input_message_content=types.InputTextMessageContent(
                f'🥊 **ВИКЛИК НА ДУЕЛЬ!**\n\n'
                f'🐗 {hryak["name"]} ({hryak["weight"]} кг) викликає на дуель!\n'
                f'Хто прийме виклик?\n\n'
                f'⚔️ На кону: 10-50% маси програвшого!',
                parse_mode="Markdown"
            ),
            reply_markup=markup
        )
    ])

