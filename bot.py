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
from flask import Flask, request, jsonify
from db import (
    init_db, load_from_db, save_hryak_to_db, save_stats_to_db, save_warns_to_db,
    save_spam_to_db, save_manual_users_to_db, get_hryak_from_db,
    get_user_currency, update_user_currency, add_coins, add_xp,
    get_daily_quests, update_daily_quest, reset_daily_quests,
    get_lottery, update_lottery,
    get_team_duel, create_team_duel, update_team_duel_status,
    get_daily_bonus, update_daily_bonus,
    get_user_stats, update_user_stats, increment_user_stat, update_casino_quest,
    get_shop_items, get_item, add_to_inventory, remove_from_inventory, has_item, get_item_effect,
    get_trachen_stats, get_last_trachen_time, add_trachen_record,
    get_pregnancy, create_pregnancy, claim_pregnancy,
    get_children, add_child, get_all_pregnancies,
    create_tournament, get_tournament, get_active_tournament, join_tournament,
    get_tournament_participants, update_tournament_status, eliminate_participant,
    get_user_tournament_stats,
    create_guild, get_guild, get_guild_by_name, get_user_guild, get_guild_members,
    join_guild, leave_guild, get_guild_rank, update_guild_xp, add_guild_contribution,
    get_all_guilds, get_user_guild_stats, transfer_guild_owner, delete_guild,
    get_all_skins, get_skin, get_skin_by_name, get_user_skins, get_user_equipped_skin, get_user_inventory,
    buy_skin, equip_skin, has_skin, get_skin_bonus,
    get_active_boss, spawn_boss, attack_boss, get_boss_participants, get_user_boss_stats,
    get_active_events, get_all_events, get_user_event_progress, update_event_progress, claim_event_reward,
    get_user_language, set_user_language,
    rename_child, get_child, get_top_children, sacrifice_child, marry_children
)

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

# ============================================
# МУЛЬТИ-МОВНІСТЬ - СЛОВНИКИ ПЕРЕКЛАДУ
# ============================================
LANGUAGES = {
    'uk': '🇺🇦 Українська',
    'en': '🇬🇧 English',
    'ru': '🇷🇺 Русский'
}

TRANSLATIONS = {
    'uk': {
        'welcome': '🤖 Ласкаво просимо до TRASH BOT!',
        'no_hryak': '❌ У тебе ще немає хряка! Введи /grow',
        'feed_success': '✅ Хряк наївся!\nВага: {old} → {new} кг ({change:+d})',
        'feed_cooldown': '⏳ Ще рано! Залишилось {hours} год {minutes} хв',
        'duel_win': '🎉 Перемога! Твій хряк важить {weight} кг',
        'duel_lose': '😞 Поразка... Спробуй ще раз!',
        'balance': '💰 Твій баланс: {coins} монет, {xp} XP (Рівень {level})',
        'help_text': '📜 **ПОВНИЙ СПИСОК КОМАНД:**\n\n',
        'menu_button': '📋 Меню',
        'close_button': '❌ Закрити',
        'back_button': '⬅️ Назад',
        'confirm_button': '✅ Підтвердити',
        'cancel_button': '❌ Скасувати',
        'error': '❌ Помилка: {error}',
        'loading': '⏳ Завантаження...',
        'event_active': '🎉 Активний івент: {name}\n{description}',
        'no_active_events': '📭 Наразі немає активних івентів',
        'lang_changed': '✅ Мову змінено на {lang}',
        'lang_select': '🌍 Оберіть мову:',
    },
    'en': {
        'welcome': '🤖 Welcome to TRASH BOT!',
        'no_hryak': '❌ You do not have a hryak yet! Use /grow',
        'feed_success': '✅ Your hryak ate!\nWeight: {old} → {new} kg ({change:+d})',
        'feed_cooldown': '⏳ Too early! {hours}h {minutes}m left',
        'duel_win': '🎉 Victory! Your hryak weighs {weight} kg',
        'duel_lose': '😞 Defeat... Try again!',
        'balance': '💰 Your balance: {coins} coins, {xp} XP (Level {level})',
        'help_text': '📜 **COMMAND LIST:**\n\n',
        'menu_button': '📋 Menu',
        'close_button': '❌ Close',
        'back_button': '⬅️ Back',
        'confirm_button': '✅ Confirm',
        'cancel_button': '❌ Cancel',
        'error': '❌ Error: {error}',
        'loading': '⏳ Loading...',
        'event_active': '🎉 Active event: {name}\n{description}',
        'no_active_events': '📭 No active events',
        'lang_changed': '✅ Language changed to {lang}',
        'lang_select': '🌍 Select language:',
    },
    'ru': {
        'welcome': '🤖 Добро пожаловать в TRASH BOT!',
        'no_hryak': '❌ У тебя еще нет хряка! Введи /grow',
        'feed_success': '✅ Хряк наелся!\nВес: {old} → {new} кг ({change:+d})',
        'feed_cooldown': '⏳ Еще рано! Осталось {hours} ч {minutes} мин',
        'duel_win': '🎉 Победа! Твой хряк весит {weight} кг',
        'duel_lose': '😞 Поражение... Попробуй еще раз!',
        'balance': '💰 Твой баланс: {coins} монет, {xp} XP (Уровень {level})',
        'help_text': '📜 **СПИСОК КОМАНД:**\n\n',
        'menu_button': '📋 Меню',
        'close_button': '❌ Закрыть',
        'back_button': '⬅️ Назад',
        'confirm_button': '✅ Подтвердить',
        'cancel_button': '❌ Отмена',
        'error': '❌ Ошибка: {error}',
        'loading': '⏳ Загрузка...',
        'event_active': '🎉 Активное событие: {name}\n{description}',
        'no_active_events': '📭 Нет активных событий',
        'lang_changed': '✅ Язык изменен на {lang}',
        'lang_select': '🌍 Выберите язык:',
    }
}

def get_text(user_id, key, **kwargs):
    """Отримує текст для користувача на його мові"""
    lang = get_user_language(user_id)
    if lang not in TRANSLATIONS:
        lang = 'uk'
    
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['uk'].get(key, key))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text

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
    # Трахензебітен досягнення
    'first_trachen': {'name': 'Перший раз 💕', 'desc': 'Перший трахензебітен', 'condition': lambda h, ts: ts.get('total_times', 0) >= 1},
    'donzhuan': {'name': 'Донжуан 😎', 'desc': '10 унікальних партнерів', 'condition': lambda h, ts: ts.get('unique_partners', 0) >= 10},
    'plodovytyy': {'name': 'Плодовитий 🐷', 'desc': '50+ трахензебітенів', 'condition': lambda h, ts: ts.get('total_times', 0) >= 50},
    'important': {'name': 'Важливий 💼', 'desc': '100+ трахензебітенів', 'condition': lambda h, ts: ts.get('total_times', 0) >= 100},
    # Турнірні досягнення
    'tournament_first': {'name': 'Дебютант 🏆', 'desc': 'Перший турнір', 'condition': lambda h, ts, t: t.get('tournaments_joined', 0) >= 1},
    'tournament_winner': {'name': 'Чемпіон 🥇', 'desc': 'Виграти турнір', 'condition': lambda h, ts, t: t.get('tournaments_won', 0) >= 1},
    'tournament_legend': {'name': 'Легенда 🏅', 'desc': '10 перемог в турнірах', 'condition': lambda h, ts, t: t.get('tournaments_won', 0) >= 10},
    # Гільдійні досягнення
    'guild_first': {'name': 'Член гільдії 🏰', 'desc': 'Вступити в гільдію', 'condition': lambda h, ts, t, g: g.get('guilds_joined', 0) >= 1},
    'guild_contributor': {'name': 'Меценат 💰', 'desc': 'Внесок 1000+ монет', 'condition': lambda h, ts, t, g: g.get('total_contribution', 0) >= 1000},
    'guild_leader': {'name': 'Лідер 👑', 'desc': 'Створити гільдію', 'condition': lambda h, ts, t, g: g.get('guilds_joined', 0) >= 1 and g.get('is_owner', False)},
}

# ============================================
# ЩОДЕННІ КВЕСТИ
# ============================================
DAILY_QUESTS = {
    'feed_3_times': {
        'name': 'Годувальник 🍽️',
        'desc': 'Нагодуй хряка 3 рази за день',
        'target': 3,
        'reward_coins': 50,
        'reward_xp': 10
    },
    'win_2_duels': {
        'name': 'Дуелянт ⚔️',
        'desc': 'Виграй 2 дуелі',
        'target': 2,
        'reward_coins': 100,
        'reward_xp': 25
    },
    'lose_10kg': {
        'name': 'Схуднення 📉',
        'desc': 'Схудни на 10 кг за раз',
        'target': 1,
        'reward_coins': 75,
        'reward_xp': 15
    },
    'gain_20kg': {
        'name': 'Набір маси 📈',
        'desc': 'Набери +20 кг за раз',
        'target': 1,
        'reward_coins': 100,
        'reward_xp': 20
    },
    'chat_active': {
        'name': 'Балакун 💬',
        'desc': 'Напиши 50 повідомлень в чаті',
        'target': 50,
        'reward_coins': 30,
        'reward_xp': 10
    },
    'feed_friends': {
        'name': 'Дружній 🐷',
        'desc': 'Нагодуй хряка коли є 3+ гравці в чаті',
        'target': 1,
        'reward_coins': 60,
        'reward_xp': 15
    }
}

# ============================================
# КАЗИНО - РУЛЕТКА
# ============================================
ROULETTE_NUMBERS = {
    0: 'green',
    1: 'red', 2: 'black', 3: 'red', 4: 'black', 5: 'red', 6: 'black',
    7: 'red', 8: 'black', 9: 'red', 10: 'black', 11: 'red', 12: 'black',
    13: 'red', 14: 'black'
}

# ============================================
# ЛОТЕРЕЯ - ШАНСИ
# ============================================
LOTTERY_CHANCES = {
    'nothing': 60,      # Нічого
    'refund': 30,       # Повернення
    'small': 8,         # Малий виграш (20 кг)
    'medium': 1.9,      # Середній виграш (50 кг)
    'jackpot': 0.1      # Джекпот (100 кг)
}

# ============================================
# МАГАЗИН - ПРЕДМЕТИ
# ============================================
SHOP_ITEMS = {
    'vitamins': {'name': '🍎 Вітаміни', 'desc': '+5 кг до наступного годування', 'price': 50, 'effect': 'weight_bonus', 'value': 5},
    'trainer': {'name': '💪 Тренажер', 'desc': '+10% до проворності на 24 год', 'price': 100, 'effect': 'agility_bonus', 'value': 10},
    'shield': {'name': '🛡️ Щит', 'desc': 'Захист від -10% ваги в дуелі', 'price': 75, 'effect': 'shield', 'value': 10},
    'energy': {'name': '⚡ Енергетик', 'desc': 'Зняти кулдаун з /feed', 'price': 30, 'effect': 'remove_cooldown', 'value': 1},
    'lucky_charm': {'name': '🍀 Підкова', 'desc': '+5% шанс на перемогу в дуелі', 'price': 200, 'effect': 'luck_bonus', 'value': 5}
}

# ============================================
# ОБРАЗИ ДЛЯ ПРОВИННИХ
# ============================================
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

        # Нагорода за годування
        add_coins(user_id, chat_id, 5)
        add_xp(user_id, chat_id, 2)

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
💰 Нагорода: +5 монет, +2 XP

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

        # Оновлюємо прогрес квестів
        quests = get_daily_quests(user_id, chat_id)
        quest_progress = {q['quest_id']: q for q in quests}
        
        # Квест: нагодуй 3 рази
        feed_quest = quest_progress.get('feed_3_times', {'progress': 0, 'target': 3})
        new_feed_progress = min(feed_quest['progress'] + 1, feed_quest['target'])
        feed_completed = new_feed_progress >= feed_quest['target']
        update_daily_quest(user_id, chat_id, 'feed_3_times', new_feed_progress, 3, completed=feed_completed)
        
        # Квест: набір 20 кг
        if actual_change == 20:
            gain_quest = quest_progress.get('gain_20kg', {'progress': 0, 'target': 1})
            new_gain_progress = min(gain_quest['progress'] + 1, gain_quest['target'])
            gain_completed = new_gain_progress >= gain_quest['target']
            update_daily_quest(user_id, chat_id, 'gain_20kg', new_gain_progress, 1, completed=gain_completed)
        
        # Квест: схуднення на 10 кг
        if actual_change <= -10:
            lose_quest = quest_progress.get('lose_10kg', {'progress': 0, 'target': 1})
            lose_completed = True
            update_daily_quest(user_id, chat_id, 'lose_10kg', 1, 1, completed=lose_completed)

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
        trachen_stats = get_trachen_stats(user_id, chat_id) or {}
        tournament_stats = get_user_tournament_stats(user_id, chat_id) or {}
        guild_stats = get_user_guild_stats(user_id, chat_id) or {}
        user_guild = get_user_guild(user_id, chat_id)
        
        # Додаємо інформацію чи є власником гільдії
        if user_guild:
            guild_stats['is_owner'] = user_guild['owner_user_id'] == user_id
        else:
            guild_stats['is_owner'] = False

        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return

        text = "🏆 **Твої досягнення:**\n\n"

        unlocked_count = 0
        for ach_id, ach in ACHIEVEMENTS.items():
            try:
                # Перевіряємо які параметри потрібні для досягнення
                code = ach['condition'].__code__
                params = code.co_varnames[:code.co_argcount]
                
                if len(params) == 4:  # h, ts, t, g
                    unlocked = ach['condition'](hryak, trachen_stats, tournament_stats, guild_stats)
                elif len(params) == 3:  # h, ts, t
                    unlocked = ach['condition'](hryak, trachen_stats, tournament_stats)
                elif len(params) == 2:  # h, ts
                    unlocked = ach['condition'](hryak, trachen_stats)
                else:  # h only
                    unlocked = ach['condition'](hryak)
                
                if unlocked:
                    text += f"✅ {ach['name']} - {ach['desc']}\n"
                    unlocked_count += 1
                else:
                    text += f"🔒 {ach['name']} - {ach['desc']}\n"
            except Exception as e:
                logger.debug(f"Досягнення {ach_id} помилка: {e}")
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

    # Оновлюємо квести за перемогу в дуелі
    if winner == 1:
        winner_user_id = challenger_id
    elif winner == 2:
        winner_user_id = opponent_id
    else:
        winner_user_id = None
    
    if winner_user_id:
        quests = get_daily_quests(winner_user_id, chat_id)
        quest_progress = {q['quest_id']: q for q in quests}
        duel_quest = quest_progress.get('win_2_duels', {'progress': 0, 'target': 2})
        new_progress = min(duel_quest['progress'] + 1, 2)
        completed = new_progress >= 2
        update_daily_quest(winner_user_id, chat_id, 'win_2_duels', new_progress, 2, completed=completed)

    # Редагуємо повідомлення з дуеллю
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"🥊 **ВИКЛИК НА ДУЕЛЬ!**\n\nПрийняв: {opponent_name}\n\n{result_text}",
        parse_mode="Markdown"
    )


# ============================================
# КОМАНДИ ЩОДЕННИХ КВЕСТІВ
# ============================================

@bot.message_handler(commands=['quests'])
def quests_cmd(message):
    """Показати доступні квести"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        quests = get_daily_quests(user_id, chat_id)
        quest_progress = {q['quest_id']: q for q in quests}
        
        text = "📋 **ЩОДЕННІ КВЕСТИ**\n\n"

        for quest_id, quest_info in DAILY_QUESTS.items():
            progress_data = quest_progress.get(quest_id, {'progress': 0, 'completed': False, 'claimed': False})
            progress = progress_data['progress']
            target = quest_info['target']
            completed = progress_data['completed']
            claimed = progress_data['claimed']

            if claimed:
                status = "✅ Забрано"
            elif completed:
                status = "🎁 Готово до нагороди!"
            else:
                status = f"📊 {progress}/{target}"

            text += f"**{quest_info['name']}** - {quest_info['desc']}\n"
            text += f"  _Нагорода: {quest_info['reward_coins']} монет, {quest_info['reward_xp']} XP_\n"
            text += f"  {status}\n\n"

        text += "\n_Використовуй:_ `/questclaim <quest_id>` - забрати нагороду\n\n"
        text += "**Доступні квести:**\n"
        text += "• `feed_3_times` - Годувальник\n"
        text += "• `win_2_duels` - Дуелянт\n"
        text += "• `lose_10kg` - Схуднення\n"
        text += "• `gain_20kg` - Набір маси\n"
        text += "• `chat_active` - Балакун\n"
        text += "• `feed_friends` - Дружній"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /quests: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['questclaim'])
def questclaim_cmd(message):
    """Забрати нагороду за квест"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Вкажіть ID квесту!\nПриклад: /questclaim feed_3_times")
            return
        
        quest_id = parts[1]
        
        if quest_id not in DAILY_QUESTS:
            bot.reply_to(message, f"❌ Квест '{quest_id}' не знайдено!")
            return
        
        quests = get_daily_quests(user_id, chat_id)
        quest_progress = {q['quest_id']: q for q in quests}
        progress_data = quest_progress.get(quest_id, {'progress': 0, 'completed': False, 'claimed': False})
        
        if progress_data.get('claimed', False):
            bot.reply_to(message, "❌ Нагороду вже забрано!")
            return
        
        if not progress_data.get('completed', False):
            bot.reply_to(message, f"❌ Квест не виконано! Прогрес: {progress_data['progress']}/{DAILY_QUESTS[quest_id]['target']}")
            return
        
        # Видаємо нагороду
        quest_info = DAILY_QUESTS[quest_id]
        add_coins(user_id, chat_id, quest_info['reward_coins'])
        add_xp(user_id, chat_id, quest_info['reward_xp'])
        
        # Позначаємо як забране
        update_daily_quest(user_id, chat_id, quest_id, progress_data['progress'], quest_info['target'], completed=True, claimed=True)
        
        text = f"""🎉 **НАГОРОДА ОТРИМАНА!**

Квест: {quest_info['name']}
💰 Монет: +{quest_info['reward_coins']}
⭐ XP: +{quest_info['reward_xp']}"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /questclaim: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# КОМАНДИ КАЗИНО
# ============================================

@bot.message_handler(commands=['roulette'])
def roulette_cmd(message):
    """Рулетка - ставки на вагу"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Приклад: /roulette 10 red\nВаріанти: red/black, even/odd, number, over/under")
            return
        
        try:
            amount = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Сума має бути числом!")
            return
        
        choice = parts[2].lower()
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        # Перевіряємо вагу хряка
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ Спочатку отримай хряка (/grow)!")
            return
        
        if hryak['weight'] < amount:
            bot.reply_to(message, f"❌ Недостатньо ваги! У тебе {hryak['weight']} кг")
            return
        
        # Крутимо рулетку
        result_number = random.randint(0, 14)
        result_color = ROULETTE_NUMBERS[result_number]
        
        win = False
        win_amount = 0
        
        # Перевіряємо виграш
        if choice in ['red', 'black']:
            if result_color == choice:
                win = True
                win_amount = amount * 2
        elif choice in ['even', 'odd']:
            if (choice == 'even' and result_number % 2 == 0) or (choice == 'odd' and result_number % 2 == 1):
                win = True
                win_amount = amount * 2
        elif choice == 'number':
            if len(parts) > 3:
                try:
                    num = int(parts[3])
                    if num == result_number:
                        win = True
                        win_amount = amount * 14
                except:
                    pass
        elif choice in ['over', 'under']:
            if (choice == 'over' and result_number > 7) or (choice == 'under' and result_number < 7):
                win = True
                win_amount = amount * 2
            elif result_number == 7:
                win_amount = amount  # Повернення при 7
        
        # Оновлюємо вагу
        if win:
            hryak['weight'] += win_amount - amount  # Додаємо виграш мінус ставка
            result_text = f"✅ ВИГРАШ!"
            
            # Оновлюємо статистику казино
            increment_user_stat(user_id, chat_id, 'casino_wins')
            # Оновлюємо квести казино
            update_casino_quest(user_id, chat_id, True)
        else:
            hryak['weight'] -= amount
            result_text = f"❌ ПРОГРАШ!"
            
            # Оновлюємо статистику казино
            increment_user_stat(user_id, chat_id, 'casino_losses')
            update_casino_quest(user_id, chat_id, False)

        save_hryaky()
        
        text = f"""🎰 **РУЛЕТКА**

Випало: {result_color.upper()} {result_number}
Твій вибір: {choice}
Ставка: {amount} кг
{result_text}

Нова вага: {hryak['weight']} кг"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /roulette: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['lottery'])
def lottery_cmd(message):
    """Лотерея - квиток за 5 кг"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ Спочатку отримай хряка (/grow)!")
            return
        
        ticket_cost = 5
        if hryak['weight'] < ticket_cost:
            bot.reply_to(message, f"❌ Недостатньо ваги! Потрібно {ticket_cost} кг")
            return
        
        # Знімаємо вагу
        hryak['weight'] -= ticket_cost
        
        # Отримуємо лотерею
        lottery = get_lottery(chat_id)
        
        # Додаємо до джекпоту 10%
        jackpot_contribution = int(ticket_cost * 0.1)
        lottery['jackpot'] += jackpot_contribution
        
        # Визначаємо виграш
        rand = random.random() * 100
        win_amount = 0
        win_type = ""
        
        if rand < LOTTERY_CHANCES['nothing']:
            win_type = "nothing"
            win_amount = 0
        elif rand < LOTTERY_CHANCES['nothing'] + LOTTERY_CHANCES['refund']:
            win_type = "refund"
            win_amount = ticket_cost
        elif rand < LOTTERY_CHANCES['nothing'] + LOTTERY_CHANCES['refund'] + LOTTERY_CHANCES['small']:
            win_type = "small"
            win_amount = 20
        elif rand < LOTTERY_CHANCES['nothing'] + LOTTERY_CHANCES['refund'] + LOTTERY_CHANCES['small'] + LOTTERY_CHANCES['medium']:
            win_type = "medium"
            win_amount = 50
        else:
            win_type = "jackpot"
            win_amount = lottery['jackpot']
            lottery['jackpot'] = 1000  # Скидаємо джекпот
        
        # Додаємо виграш
        hryak['weight'] += win_amount
        
        # Оновлюємо лотерею
        update_lottery(chat_id, lottery['jackpot'], int(time.time()), lottery['participants'])
        save_hryaky()
        
        win_texts = {
            'nothing': "❌ Нічого",
            'refund': "🔄 Повернення",
            'small': "✅ Малий виграш",
            'medium': "🎉 Середній виграш",
            'jackpot': "🎰🎉 ДЖЕКПОТ!"
        }
        
        text = f"""🎰 **ЛОТЕРЕЯ**

Квиток: {ticket_cost} кг
{win_texts[win_type]}!
Виграш: +{win_amount} кг

Джекпот: {lottery['jackpot']} кг
Нова вага: {hryak['weight']} кг"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /lottery: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# КОМАНДНІ ДУЕЛІ (2v2, 3v3)
# ============================================

@bot.message_handler(commands=['duelteambattle'])
def duelteambattle_cmd(message):
    """Створити командну дуель"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ Спочатку отримай хряка (/grow)!")
            return
        
        text = f"""⚔️ **КОМАНДНА ДУЕЛЬ**

🐗 {hryak['name']} ({hryak['weight']} кг) створює команду!

Щоб приєднатися, натисни кнопку нижче.
Перший до 3 гравців формує команду 1.
"""
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔥 Приєднатися до команди 1", callback_data=f"team1_join_{user_id}"))
        
        msg = bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)
        
        # Зберігаємо дуель
        duel_id = f"team_{chat_id}_{int(time.time())}"
        create_team_duel(duel_id, chat_id, [{'user_id': user_id, 'hryak': hryak}], [], status='waiting')
        
    except Exception as e:
        logger.error(f"❌ Помилка /duelteambattle: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('team1_join_'))
def team1_join_callback(call):
    """Приєднання до команди 1"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.answer_callback_query(call.id, "❌ У тебе немає хряка!", show_alert=True)
            return
        
        # Знаходимо дуель
        duel_id = f"team_{chat_id}_{call.message.message_id}"
        duel = get_team_duel(duel_id)
        
        if not duel:
            bot.answer_callback_query(call.id, "❌ Дуель не знайдено!", show_alert=True)
            return
        
        if len(duel['team1']) >= 3:
            bot.answer_callback_query(call.id, "❌ Команда 1 повна!", show_alert=True)
            return
        
        # Додаємо до команди
        duel['team1'].append({'user_id': user_id, 'hryak': hryak})
        
        text = f"""⚔️ **КОМАНДНА ДУЕЛЬ**

Команда 1 ({len(duel['team1'])}/3):
"""
        for player in duel['team1']:
            text += f"🐗 {player['hryak']['name']} ({player['hryak']['weight']} кг)\n"
        
        text += "\nКоманда 2 (0/3):\n"
        text += "Натисни кнопку щоб приєднатися!\n"
        
        markup = types.InlineKeyboardMarkup()
        if len(duel['team1']) < 3:
            markup.add(types.InlineKeyboardButton("🔥 Приєднатися до команди 1", callback_data=f"team1_join_{user_id}"))
        markup.add(types.InlineKeyboardButton("⚔️ Створити команду 2", callback_data=f"team2_create_{call.message.message_id}"))
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ Приєднано до команди 1!")
        
    except Exception as e:
        logger.error(f"❌ Помилка team1_join: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "❌ Помилка!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('team2_create_'))
def team2_create_callback(call):
    """Створення команди 2"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.answer_callback_query(call.id, "❌ У тебе н������має хряка!", show_alert=True)
            return
        
        msg_id = call.data.split('_')[-1]
        duel_id = f"team_{chat_id}_{msg_id}"
        duel = get_team_duel(duel_id)
        
        if not duel:
            bot.answer_callback_query(call.id, "❌ Дуель не знайдено!", show_alert=True)
            return
        
        if len(duel['team1']) < 2:
            bot.answer_callback_query(call.id, "❌ Потрібно мінімум 2 гравці в команді 1!", show_alert=True)
            return
        
        # Додаємо до команди 2
        duel['team2'].append({'user_id': user_id, 'hryak': hryak})
        
        text = f"""⚔️ **КОМАНДНА ДУЕЛЬ**

Команда 1 ({len(duel['team1'])}):
"""
        for player in duel['team1']:
            text += f"🐗 {player['hryak']['name']} ({player['hryak']['weight']} кг)\n"
        
        text += f"\nКоманда 2 ({len(duel['team2'])}/3):\n"
        text += f"🐗 {hryak['name']} ({hryak['weight']} кг)\n"
        text += "\nНатисни кнопку щоб приєднатися до команди 2!\n"
        
        markup = types.InlineKeyboardMarkup()
        if len(duel['team2']) < 3:
            markup.add(types.InlineKeyboardButton("🔥 Приєднатися до команди 2", callback_data=f"team2_join_{user_id}"))
        markup.add(types.InlineKeyboardButton("⚔️ ПОЧАТИ БИТВУ!", callback_data=f"team_battle_start_{msg_id}"))
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ Команду 2 створено!")
        
    except Exception as e:
        logger.error(f"❌ Помилка team2_create: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "❌ Помилка!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('team2_join_'))
def team2_join_callback(call):
    """Приєднання до команди 2"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.answer_callback_query(call.id, "❌ У тебе немає хряка!", show_alert=True)
            return
        
        msg_id = call.data.split('_')[-1]
        duel_id = f"team_{chat_id}_{msg_id}"
        duel = get_team_duel(duel_id)
        
        if not duel:
            bot.answer_callback_query(call.id, "❌ Дуель не знайдено!", show_alert=True)
            return
        
        if len(duel['team2']) >= 3:
            bot.answer_callback_query(call.id, "❌ Команда 2 повна!", show_alert=True)
            return
        
        duel['team2'].append({'user_id': user_id, 'hryak': hryak})
        
        text = f"""⚔️ **КОМАНДНА ДУЕЛЬ**

Команда 1 ({len(duel['team1'])}):
"""
        for player in duel['team1']:
            text += f"🐗 {player['hryak']['name']} ({player['hryak']['weight']} кг)\n"
        
        text += f"\nКоманда 2 ({len(duel['team2'])}/3):\n"
        for player in duel['team2']:
            text += f"🐗 {player['hryak']['name']} ({player['hryak']['weight']} кг)\n"
        
        markup = types.InlineKeyboardMarkup()
        if len(duel['team2']) < 3:
            markup.add(types.InlineKeyboardButton("🔥 Приєднатися до команди 2", callback_data=f"team2_join_{user_id}"))
        if len(duel['team2']) >= 2:
            markup.add(types.InlineKeyboardButton("⚔️ ПОЧАТИ БИТВУ!", callback_data=f"team_battle_start_{msg_id}"))
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ Приєднано до команди 2!")
        
    except Exception as e:
        logger.error(f"❌ Помилка team2_join: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "❌ Помилка!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('team_battle_start_'))
def team_battle_start_callback(call):
    """Початок командної битви"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    try:
        msg_id = call.data.split('_')[-1]
        duel_id = f"team_{chat_id}_{msg_id}"
        duel = get_team_duel(duel_id)
        
        if not duel:
            bot.answer_callback_query(call.id, "❌ Дуель не знайдено!", show_alert=True)
            return
        
        if len(duel['team1']) < 2 or len(duel['team2']) < 2:
            bot.answer_callback_query(call.id, "❌ Потрібно мінімум 2 гравці в кожній команді!", show_alert=True)
            return
        
        # Розраховуємо силу команд
        team1_weight = sum(p['hryak']['weight'] for p in duel['team1'])
        team2_weight = sum(p['hryak']['weight'] for p in duel['team2'])
        team1_agility = sum(p['hryak'].get('feed_count', 0) for p in duel['team1']) / len(duel['team1'])
        team2_agility = sum(p['hryak'].get('feed_count', 0) for p in duel['team2']) / len(duel['team2'])
        
        team1_power = team1_weight * 0.6 + team1_agility * 0.4 + random.randint(0, 50)
        team2_power = team2_weight * 0.6 + team2_agility * 0.4 + random.randint(0, 50)
        
        # Критичний удар (15% шанс)
        team1_crit = random.random() < 0.15
        team2_crit = random.random() < 0.15
        if team1_crit:
            team1_power *= 1.5
        if team2_crit:
            team2_power *= 1.5
        
        # Визначаємо переможця
        if team1_power > team2_power:
            winner = 1
            winner_text = "Команда 1"
            loser_team = duel['team2']
            winner_team = duel['team1']
        elif team2_power > team1_power:
            winner = 2
            winner_text = "Команда 2"
            loser_team = duel['team1']
            winner_team = duel['team2']
        else:
            winner = 0
            winner_text = "Нічия"
        
        # Оновлюємо вагу
        for player in winner_team:
            player['hryak']['weight'] = int(player['hryak']['weight'] * 1.1)  # +10%
            save_hryak_to_db(f"{chat_id}_{player['user_id']}", player['hryak'])
        
        for player in loser_team:
            player['hryak']['weight'] = int(player['hryak']['weight'] * 0.95)  # -5%
            save_hryak_to_db(f"{chat_id}_{player['user_id']}", player['hryak'])
        
        # Оновлюємо квести за перемогу в дуелі
        for player in winner_team:
            quests = get_daily_quests(player['user_id'], chat_id)
            quest_progress = {q['quest_id']: q for q in quests}
            duel_quest = quest_progress.get('win_2_duels', {'progress': 0, 'target': 2})
            new_progress = min(duel_quest['progress'] + 1, 2)
            completed = new_progress >= 2
            update_daily_quest(player['user_id'], chat_id, 'win_2_duels', new_progress, 2, completed=completed)
        
        text = f"""⚔️ **РЕЗУЛЬТАТИ КОМАНДНОЇ БИТВИ!**

{winner_text} перемогла!

💪 Сила Команди 1: {team1_power:.1f}
💪 Сила Команди 2: {team2_power:.1f}
{"⚡️ КРИТИЧНИЙ УДАР Команди 1!" if team1_crit else ""}
{"⚡️ КРИТИЧНИЙ УДАР Команди 2!" if team2_crit else ""}

🏆 Переможці отримали +10% до ваги!
💀 Програвші втратили -5% ваги!
"""
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id, f"⚔️ {winner_text} перемогла!")
        
    except Exception as e:
        logger.error(f"❌ Помилка team_battle: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "❌ Помилка!", show_alert=True)


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
        types.InlineKeyboardButton("⚔️ Дуель", callback_data="duel_create"),
        types.InlineKeyboardButton("👥 Командна", callback_data="menu_teambattle"),
        types.InlineKeyboardButton("🏅 Досягнення", callback_data="menu_achievements"),
        types.InlineKeyboardButton("📋 Квести", callback_data="menu_quests"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="menu_balance"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="menu_mystats"),
        types.InlineKeyboardButton("🏪 Магазин", callback_data="menu_shop"),
        types.InlineKeyboardButton("🎒 Інвентар", callback_data="menu_inventory"),
        types.InlineKeyboardButton("🎁 Daily", callback_data="menu_daily"),
        types.InlineKeyboardButton("🎰 Рулетка", callback_data="menu_roulette"),
        types.InlineKeyboardButton("🎯 Лотерея", callback_data="menu_lottery"),
        types.InlineKeyboardButton("💕 Трахен", callback_data="menu_trachen"),
        types.InlineKeyboardButton("👶 Діти", callback_data="menu_children"),
        types.InlineKeyboardButton("🤰 Вагітні", callback_data="menu_pregnancies"),
        types.InlineKeyboardButton("🏆 Турнір", callback_data="menu_tournament"),
        types.InlineKeyboardButton("🎯 Підор", callback_data="menu_pidor"),
        types.InlineKeyboardButton("🔥 Roast", callback_data="menu_roast"),
        types.InlineKeyboardButton("🔮 Fortune", callback_data="menu_fortune"),
        types.InlineKeyboardButton("⭐ Оцінка", callback_data="menu_rate")
    )

    bot.reply_to(message,
        "������������ **МЕНЮ КОМАНД**\n\nОбери кнопку:",
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

    elif command == 'quests':
        text = "📋 **Квести**\n\nНапиши /quests щоб побачити доступні квести!"

    elif command == 'balance':
        currency = get_user_currency(user_id, chat_id)
        if currency:
            text = f"""💰 **БАЛАНС**

💵 Монети: {currency['coins']}
⭐ XP: {currency['xp']}/{100}
🏆 Рівень: {currency['level']}"""
        else:
            text = "💰 **БАЛАНС**\n\n💵 Монети: 0\n⭐ XP: 0/100\n🏆 Рівень: 1"

    elif command == 'roulette':
        text = "🎰 **Рулетка**\n\nНапиши /roulette <сума> <вибір>\nПриклад: /roulette 10 red"

    elif command == 'lottery':
        text = "🎯 **Лотерея**\n\nНапиши /lottery щоб спробувати удачу за 5 кг!"

    elif command == 'trachen':
        text = "💕 **Трахензебітен**\n\nНапиши /trachen щоб спарувати хряка!\nКулдаун: 12 годин\nШанс вагітності: 10%"

    elif command == 'children':
        text = "👶 **Діти**\n\nНапиши /children щоб побачити своїх дітей!"

    elif command == 'pregnancies':
        text = "🤰 **Вагітності**\n\nНапиши /pregnancies щоб побачити вагітних хряків!"

    elif command == 'tournament':
        text = "🏆 **Турніри**\n\nНапиши /tournament щоб створити або приєднатися!"

    elif command == 'teambattle':
        text = "👥 **Командна дуель**\n\nНапиши /duelteambattle щоб створити командну битву!"

    elif command == 'shop':
        text = "🏪 **Магазин**\n\nНапиши /shop щоб побачити товари!"

    elif command == 'inventory':
        text = "🎒 **Інвентар**\n\nНапиши /inventory щоб побачити свої предмети!"

    elif command == 'daily':
        text = "🎁 **Щоденний бонус**\n\nНапиши /daily щоб отримати нагороду!"

    elif command == 'mystats':
        text = "📊 **Статистика**\n\nНапиши /mystats щоб побачити свою статистику!"

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
    8: "8/10. Ти сьогодні виглядаєш як людина, а не ��к помилка.",
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
    "🔥 ВИБУХ! 🔥 Я зараз ��озірвуся від емоцій!",
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
    "��и знаєш що це нічого не змінить?",
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
    text = (
        "📜 ПОВНИЙ СПИСОК КОМАНД:\n\n"
        "🎯 Образливі:\n"
        "/pidor /roast /insult /hardinsult /slap\n\n"
        "🔮 Передбачення:\n"
        "/fortune /whosgay /rate\n\n"
        "🤯 Розваги:\n"
        "/fact /choose /top /такні\n\n"
        "🐷 Гра Вирости Хряка:\n"
        "/grow /feed /my /name /hryaketop\n"
        "/globaltop /achievements /duel /duelteambattle\n\n"
        "📋 Квести:\n"
        "/quests /questclaim\n\n"
        "🎰 Казино:\n"
        "/roulette /lottery\n\n"
        "💰 Економіка:\n"
        "/balance /shop /buy /inventory /use /daily\n\n"
        "📊 Статистика:\n"
        "/mystats /stats /leaderboard /activity\n\n"
        "👥 Чат:\n"
        "/members /adduser /removeuser /clearcache\n"
        "/random /kickme\n\n"
        "🔇 Мут (адміни):\n"
        "/mute /unmute\n\n"
        "😈 Провини (адміни):\n"
        "/provin /unprovin /provinlist\n\n"
        "⚠️ Попередження (адміни):\n"
        "/warn /warnings /clearwarns\n\n"
        "🚫 Бан (адміни):\n"
        "/ban /unban\n\n"
        "📌 Інше (адміни):\n"
        "/del /pin /unpin /spam\n\n"
        "💕 Трахензебітен:\n"
        "/trachen /children /pregnancies /claimchildren\n"
        "/childinfo /renamechild /childtop /sacrificechild /childmarry\n\n"
        "🏆 Турніри:\n"
        "/tournament\n\n"
        "🏰 Гільдії:\n"
        "/createguild /guild /guildjoin /guildleave\n"
        "/guildtop /contribute /transferguild /deleteguild\n\n"
        "🎨 Скіни:\n"
        "/skins /buyskin /equipskin\n\n"
        "🐲 Бос-дуелі:\n"
        "/boss /boss attack /boss info\n\n"
        "🎉 Івенти:\n"
        "/events /eventsclaim\n\n"
        "🌍 Мова:\n"
        "/lang\n\n"
        "⚙️ Інше:\n"
        "/start /menu /help\n\n"
        "Всі команди працюють з рандомом!"
    )
    bot.reply_to(message, text)


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
/my — показат�������� хряка
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

# ============================================
# МАГАЗИН ТА ІНВЕНТАР
# ============================================

@bot.message_handler(commands=['shop'])
def shop_cmd(message):
    """Показати магазин"""
    try:
        items = get_shop_items()
        
        text = "🏪 **МАГАЗИН**\n\n"
        for item in items:
            text += f"`{item['item_id']}` - {item['name']} - {item['description']}\n"
            text += f"  _Ціна: {item['price']} {item['price_currency']}_\n\n"

        text += "**Команди:**\n"
        text += "/buy <item_id> - купити предмет\n"
        text += "/inventory - твій інвентар\n"
        text += "/use <item_id> - використати предмет\n\n"
        text += "**Приклад:** `/buy vitamins`"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /shop: {e}", exc_info=True)
        bot.reply_to(message, f"❌ П����милка: {e}")


@bot.message_handler(commands=['buy'])
def buy_cmd(message):
    """Купити предмет"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Вкажіть предмет!\nПриклад: /buy vitamins")
            return
        
        item_id = parts[1]
        item = get_item(item_id)
        
        if not item:
            bot.reply_to(message, f"❌ Предмет '{item_id}' не знайдено!")
            return
        
        currency = get_user_currency(user_id, chat_id)
        if not currency:
            bot.reply_to(message, "❌ Помилка отримання балансу!")
            return
        
        if item['price_currency'] == 'coins':
            if currency['coins'] < item['price']:
                bot.reply_to(message, f"❌ Недостатньо монет! Потрібно {item['price']}")
                return
            add_coins(user_id, chat_id, -item['price'])
        elif item['price_currency'] == 'xp':
            if currency['xp'] < item['price']:
                bot.reply_to(message, f"❌ Недостатньо XP! Потрібно {item['price']}")
                return
            update_user_currency(user_id, chat_id, xp=currency['xp'] - item['price'])
        
        # Додаємо до інвентарю
        add_to_inventory(user_id, chat_id, item_id, 1, item['duration'])
        
        text = f"""✅ **КУПЛЕНО!**

{item['name']}
Витрачено: {item['price']} {item['price_currency']}"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /buy: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['inventory'])
def inventory_cmd(message):
    """Показати інвентар"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        inventory = get_user_inventory(user_id, chat_id)
        items = get_shop_items()
        items_dict = {i['item_id']: i for i in items}
        
        if not inventory:
            bot.reply_to(message, "🎒 ІНВЕНТАР\n\nПорожньо!")
            return
        
        text = "🎒 **ІНВЕНТАР**\n\n"
        for inv_item in inventory:
            item = items_dict.get(inv_item['item_id'])
            if item:
                text += f"`{inv_item['item_id']}` - {item['name']} x{inv_item['quantity']}\n"
                if inv_item['expires_at']:
                    expires = inv_item['expires_at'] - int(time.time())
                    hours = expires // 3600
                    text += f"  _⏰ Ще {hours} год_\n"
                text += "\n"

        text += "**Команди:**\n"
        text += "/use <item_id> - використати предмет\n\n"
        text += "**Приклад:** `/use vitamins`"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /inventory: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['use'])
def use_cmd(message):
    """Використати предмет"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Вкажіть предмет!\nПриклад: /use vitamins")
            return
        
        item_id = parts[1]
        
        if not has_item(user_id, chat_id, item_id):
            bot.reply_to(message, "❌ У тебе немає цього предмету!")
            return
        
        item = get_item(item_id)
        if not item:
            bot.reply_to(message, "❌ Предмет не знайдено!")
            return
        
        # Використовуємо предмет
        if item_id == 'energy':
            # Зняти кулдаун з годування
            hryak = get_hryak(user_id, chat_id)
            if hryak:
                hryak['last_feed'] = 0
                save_hryak_to_db(f"{chat_id}_{user_id}", hryak)
                text = "⚡ **Енергетик використано!**\n\nТепер можна годувати хряка!"
            else:
                text = "❌ У тебе немає хряка!"
        elif item_id == 'vitamins':
            # Бонус до ваги
            hryak = get_hryak(user_id, chat_id)
            if hryak:
                hryak['weight'] += item['value']
                save_hryak_to_db(f"{chat_id}_{user_id}", hryak)
                text = f"🍎 **Вітаміни ��икористано!**\n\nВага збільшена на +{item['value']} кг!"
            else:
                text = "❌ У тебе немає хряка!"
        else:
            text = f"✅ **{item['name']} використано!**\n\nЕфект: {item['desc']}"
        
        # Видаляємо предмет
        remove_from_inventory(user_id, chat_id, item_id, 1)
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /use: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ОСОБИСТА СТАТИСТИКА
# ============================================

@bot.message_handler(commands=['mystats'])
def mystats_cmd(message):
    """Особиста статистика"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        stats = get_user_stats(user_id, chat_id)
        currency = get_user_currency(user_id, chat_id)
        hryak = get_hryak(user_id, chat_id)
        trachen_stats = get_trachen_stats(user_id, chat_id)
        tournament_stats = get_user_tournament_stats(user_id, chat_id)
        guild_stats = get_user_guild_stats(user_id, chat_id)
        user_guild = get_user_guild(user_id, chat_id)
        boss_stats = get_user_boss_stats(user_id, chat_id)

        text = f"""📊 **ТВОЯ СТАТИСТИКА**

💰 **Економіка:**
  Монети: {currency['coins'] if currency else 0}
  XP: {currency['xp'] if currency else 0}/{100}
  Рівень: {currency['level'] if currency else 1}

⚔️ **Дуелі:**
  Перемог: {stats['duels_won']}
  Поразок: {stats['duels_lost']}
  Всього ігор: {stats['duels_won'] + stats['duels_lost']}

📋 **Квести:**
  Виконано: {stats['quests_completed']}

🎰 **Казино:**
  Виграшів: {stats['casino_wins']}
  Програшів: {stats['casino_losses']}

💕 **Трахензебітен:**
  Разів: {trachen_stats['total_times'] if trachen_stats else 0}
  Унікальних партнерів: {trachen_stats['unique_partners'] if trachen_stats else 0}
  Зміна ваги: {trachen_stats['total_weight_change'] if trachen_stats else 0:+d} кг

🏆 **Турніри:**
  Участь: {tournament_stats['tournaments_joined'] if tournament_stats else 0}
  Перемоги: {tournament_stats['tournaments_won'] if tournament_stats else 0}

🏰 **Гільдії:**
  Внесок: {guild_stats['total_contribution'] if guild_stats else 0}
  Гільдія: {user_guild['name'] if user_guild else "Немає"}

🐲 **Бос-дуелі:**
  Битв: {boss_stats['bosses_fought'] if boss_stats else 0}
  Всього шкоди: {boss_stats['total_damage'] if boss_stats else 0}
  Вбито босів: {boss_stats['bosses_defeated'] if boss_stats else 0}

🐷 **Хряк:**"""

        if hryak:
            text += f"""
  Ім'я: {hryak['name']}
  Вага: {hryak['weight']} кг
  Нагодовано: {hryak['feed_count']} разів
  Набрано всього: {stats['total_weight_gained']} кг"""
        else:
            text += "\n  Немає хряка! Введи /grow"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /mystats: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ЩОДЕННИЙ БОНУС
# ============================================

@bot.message_handler(commands=['daily'])
def daily_cmd(message):
    """Щоденний бонус"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        bonus = get_daily_bonus(user_id, chat_id)
        now = int(time.time())
        day = 86400  # 24 години в секундах
        
        time_since_last = now - bonus['last_claim'] if bonus['last_claim'] > 0 else day
        
        if time_since_last < day:
            hours_left = int((day - time_since_last) / 3600)
            minutes_left = int(((day - time_since_last) % 3600) / 60)
            text = f"⏳ **Ще рано!**\n\nЗалишилось: {hours_left} год {minutes_left} хв"
        else:
            # Визначаємо стрік
            if time_since_last < day * 2:
                new_streak = bonus['streak'] + 1
            else:
                new_streak = 1
            
            # Нагорода збільшується зі стріком
            base_coins = 10
            base_xp = 5
            coins = base_coins + (new_streak * 2)
            xp = base_xp + (new_streak // 3)
            
            add_coins(user_id, chat_id, coins)
            add_xp(user_id, chat_id, xp)
            update_daily_bonus(user_id, chat_id, now, new_streak)
            
            text = f"""🎁 **ЩОДЕННИЙ БОНУС!**

💵 Монет: +{coins}
⭐ XP: +{xp}
🔥 Стрік: {new_streak} днів поспіль!

Продовжуй заходити щодня для більших нагород!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /daily: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    """Показати баланс монет та XP"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        currency = get_user_currency(user_id, chat_id)
        
        if not currency:
            bot.reply_to(message, "❌ Помилка отримання балансу!")
            return
        
        text = f"""💰 **БАЛАНС**

💵 Монети: {currency['coins']}
⭐ XP: {currency['xp']}/{100}
🏆 Рівень: {currency['level']}

Як отримати:
• /feed - +5 монет, +2 XP
• /quests - до 100 монет, 25 XP
• /roulette - ризикни!
• /lottery - спробуй удачу!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /balance: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


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


# ============================================
# ТРАХЕНЗЕБІТЕН - СПАРЮВАННЯ ХРЯКІВ
# ============================================

TRACHEN_COOLDOWN = 43200  # 12 годин в секундах
TRACHEN_ENERGY_COST = 10
TRACHEN_PREGNANCY_CHANCE = 0.1  # 10% шанс вагітності

@bot.message_handler(commands=['trachen'])
def trachen_cmd(message):
    """Трахензебітен - спарювання хряків"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        # Перевіряємо чи є хряк
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return
        
        # Перевіряємо кулдаун
        last_trachen_time = get_last_trachen_time(user_id, chat_id)
        now = int(time.time())
        time_since_last = now - last_trachen_time
        
        if last_trachen_time > 0 and time_since_last < TRACHEN_COOLDOWN:
            hours_left = int((TRACHEN_COOLDOWN - time_since_last) / 3600)
            minutes_left = int(((TRACHEN_COOLDOWN - time_since_last) % 3600) / 60)
            bot.reply_to(message, f"⏳ Ще рано! Трахензебітен доступний раз на 12 годин.\n\nЗалишилось: {hours_left} год {minutes_left} хв")
            return
        
        # Витрачаємо енергію
        energy = TRACHEN_ENERGY_COST
        
        # Перевіряємо чи є партнер
        partner_id = None
        partner_hryak = None
        
        # Якщо є згадка користувача
        if message.reply_to_message and message.reply_to_message.from_user:
            partner_id = message.reply_to_message.from_user.id
            partner_hryak = get_hryak(partner_id, chat_id)
            if not partner_hryak:
                bot.reply_to(message, "❌ У цього користувача немає хряка!")
                return
            if partner_id == user_id:
                bot.reply_to(message, "❌ Не можна з самим собою!")
                return
        
        # Якщо немає партнера - вибираємо випадкового
        if not partner_id:
            # Отримуємо всіх гравців з хряками
            all_hryaky = []
            for key, h in hryaky_data.items():
                if h.get('chat_id') == chat_id and h.get('user_id') != user_id:
                    all_hryaky.append(h)
            
            if not all_hryaky:
                bot.reply_to(message, "❌ Немає інших гравців з хряками в чаті!")
                return
            
            partner_hryak = random.choice(all_hryaky)
            partner_id = partner_hryak['user_id']
        
        # Розраховуємо зміну ваги (від -15 до +25 кг)
        weight_change = random.randint(-15, 25)
        
        # Шанс вагітності (10%)
        is_pregnant = random.random() < TRACHEN_PREGNANCY_CHANCE
        children_count = 0
        
        if is_pregnant:
            # Вагітність може настати у будь-якого з партнерів (50/50)
            pregnant_user = user_id if random.random() < 0.5 else partner_id
            pregnant_hryak_name = hryak['name'] if pregnant_user == user_id else partner_hryak['name']
            other_user = partner_id if pregnant_user == user_id else user_id
            other_hryak_name = partner_hryak['name'] if pregnant_user == user_id else hryak['name']
            
            # Кількість дітей (1-3)
            children_count = random.randint(1, 3)
            
            # Створюємо вагітність
            create_pregnancy(
                pregnant_user, chat_id,
                other_user, other_hryak_name,
                pregnant_hryak_name, children_count
            )
        
        # Записуємо трахензебітен
        add_trachen_record(user_id, chat_id, partner_id, partner_hryak['name'], weight_change, energy)
        
        # Оновлюємо вагу хряка
        old_weight = hryak['weight']
        hryak['weight'] = max(1, hryak['weight'] + weight_change)
        if hryak['weight'] > hryak['max_weight']:
            hryak['max_weight'] = hryak['weight']
        save_hryak_to_db(f"{chat_id}_{user_id}", hryak)
        
        # Формуємо повідомлення
        emoji = "💕" if weight_change > 0 else "😔"
        pregnancy_emoji = "🤰" if is_pregnant else ""
        
        text = f"""{emoji} **Трахензебітен відбувся!**

🐷 Твій хряк: {hryak['name']}
💑 Партнер: {partner_hryak['name']}
⚖️ Зміна ваги: {weight_change:+d} кг ({old_weight} → {hryak['weight']})
💪 Витрачено енергії: {energy}

{pregnancy_emoji}{"🎉 Вітаємо! Хтось вагітний!" if is_pregnant else ""}"""
        
        if is_pregnant:
            text += f"\n👶 Кількість дітей: {children_count}"
            text += f"\n⏳ Час до пологів: 10 хвилин"
        
        text += f"\n\n⏰ Наступний трахензебітен через 12 годин"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /trachen: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['children'])
def children_cmd(message):
    """Показати дітей користувача"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        children_list = get_children(user_id, chat_id)
        
        if not children_list:
            bot.reply_to(message, "👶 У тебе ще немає дітей!\n\nЗаведи дітей через /trachen")
            return
        
        text = "👶 **Твої діти:**\n\n"

        for i, child in enumerate(children_list, 1):
            born_date = time.strftime('%d.%m.%Y', time.localtime(child['born_at']))
            text += f"{i}. `{child['id']}` - **{child['name']}**\n"
            text += f"   ⚖️ Вага: {child['weight']} кг\n"
            text += f"   🎂 Народжений: {born_date}\n"
            text += f"   🧬 Особливість: {child['inherited_trait'] or 'Немає'}\n\n"

        text += f"\n**Команди:**\n"
        text += "/childinfo <ID> - інформація\n"
        text += "/renamechild <ID> <ім'я> - перейменувати\n"
        text += "/sacrificechild <ID> - жертва\n"
        text += "/childmarry <ID1> <ID2> - одружити\n\n"
        text += "**Приклад:** `/childinfo 123`"

        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /children: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childinfo'])
def child_info_cmd(message):
    """Інформація про дитину"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /childinfo <ID дитини>\n\nДізнайся ID командою /children")
            return
        
        child_id = int(parts[1])
        child = get_child(child_id, chat_id)
        
        if not child:
            bot.reply_to(message, "❌ Дитину не знайдено!")
            return
        
        # Перевіряємо чи це дитина користувача
        if child['user_id'] != user_id:
            bot.reply_to(message, "❌ Це не твоя дитина!")
            return
        
        born_date = time.strftime('%d.%m.%Y %H:%M', time.localtime(child['born_at']))
        
        text = f"""👶 **ІНФОРМАЦІЯ ПРО ДИТИНУ**

**ID:** {child['id']}
**Ім'я:** {child['name']}
**Вага:** {child['weight']} кг
**Особливість:** {child['inherited_trait'] or 'Немає'}

**Батьки:**
👨 Батько: ID {child['father_user_id']}
👩 Мати: ID {child['mother_user_id']}

**Народжений:** {born_date}
**Вік:** {int((time.time() - child['born_at']) / 86400)} дн.

**Команди:**
/renamechild {child_id} <нове ім'я> - перейменувати
/sacrificechild {child_id} - жертва (монети + XP)"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /childinfo: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['renamechild'])
def rename_child_cmd(message):
    """Перейменувати дитину"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /renamechild <ID> <нове ім'я>")
            return
        
        child_id = int(parts[1])
        new_name = parts[2][:32]  # Макс 32 символи
        
        # Перевіряємо чи це дитина користувача
        child = get_child(child_id, chat_id)
        if not child or child['user_id'] != user_id:
            bot.reply_to(message, "❌ Це не твоя дитина!")
            return
        
        # Перейменовуємо
        if rename_child(child_id, user_id, chat_id, new_name):
            bot.reply_to(message, f"✅ Дитину перейменовано на **{new_name}**!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Помилка перейменування!")
    
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /renamechild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childtop'])
def child_top_cmd(message):
    """Топ дітей за вагою"""
    chat_id = message.chat.id
    
    try:
        children = get_top_children(chat_id, limit=10)
        
        if not children:
            bot.reply_to(message, "👶 **ТОП ДІТЕЙ**\n\nВ чаті ще немає дітей!")
            return
        
        text = "🏆 **ТОП ДІТЕЙ ЗА ВАГОЮ**\n\n"
        
        for i, child in enumerate(children, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            trait_emoji = f" ({child['inherited_trait']})" if child['inherited_trait'] else ""
            text += f"{medal} **{child['name']}** - {child['weight']} кг{trait_emoji}\n"
            text += f"   Батьки: {child['father_name'][:15]} + {child['mother_name'][:15]}\n\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"❌ Помилка /childtop: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['sacrificechild'])
def sacrifice_child_cmd(message):
    """Жертва дитини для бонусів"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /sacrificechild <ID дитини>")
            return
        
        child_id = int(parts[1])
        
        # Перевіряємо чи це дитина користувача
        child = get_child(child_id, chat_id)
        if not child or child['user_id'] != user_id:
            bot.reply_to(message, "❌ Це не твоя дитина!")
            return
        
        # Жертвуємо
        result = sacrifice_child(child_id, user_id, chat_id)
        
        if result:
            add_coins(user_id, chat_id, result['coins'])
            add_xp(user_id, chat_id, result['xp'])
            
            bot.reply_to(message, f"""🔥 **ЖЕРТВА ПРИЙНЯТА!**

Дитина **{child['name']}** пожертвована!

💰 Отримано: +{result['coins']} монет
⭐ Отримано: +{result['xp']} XP

Вага дитини: {result['weight']} кг""", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Помилка жертви!")
    
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /sacrificechild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childmarry'])
def child_marry_cmd(message):
    """Одруження дітей"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /childmarry <ID1> <ID2>\n\nОдружити двох дітей (створити онука)")
            return
        
        child1_id = int(parts[1])
        child2_id = int(parts[2])
        
        # Перевіряємо чи це діти користувача
        child1 = get_child(child1_id, chat_id)
        child2 = get_child(child2_id, chat_id)
        
        if not child1 or child1['user_id'] != user_id:
            bot.reply_to(message, "❌ Перша дитина не твоя!")
            return
        
        if not child2 or child2['user_id'] != user_id:
            bot.reply_to(message, "❌ Друга дитина не твоя!")
            return
        
        # Одружуємо
        result = marry_children(child1_id, child2_id, user_id, chat_id)
        
        if result:
            bot.reply_to(message, f"""💕 **ВЕСІЛЛЯ ВІДБУЛОСЯ!**

{child1['name']} + {child2['name']}

👶 Народився онук: **{child1['name'][:3]}-{child2['name'][:3]}-F1**
⚖️ Вага онука: {result['weight']} кг

Тепер ти можеш виховувати онука!""")
        else:
            bot.reply_to(message, "❌ Помилка одруження! Можливо діти однакові?")
    
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /childmarry: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['pregnancies'])
def pregnancies_cmd(message):
    """Показати вагітності в чаті"""
    chat_id = message.chat.id
    
    try:
        pregnancies_list = get_all_pregnancies(chat_id)
        
        if not pregnancies_list:
            bot.reply_to(message, "🤰 Наразі немає вагітних хряків в чаті!")
            return
        
        text = "🤰 **Вагітні хряки:**\n\n"
        now = int(time.time())
        
        for i, preg in enumerate(pregnancies_list, 1):
            time_left = preg['due_date'] - now
            if time_left > 0:
                minutes_left = int(time_left / 60)
                hours_left = int(minutes_left / 60)
                mins = minutes_left % 60
                time_str = f"{hours_left} год {mins} хв" if hours_left > 0 else f"{mins} хв"
            else:
                time_str = "Готовий до пологів!"
            
            text += f"{i}. 🐷 {preg['mother_hryak_name']}\n"
            text += f"   👨 Батько: {preg['father_hryak_name']}\n"
            text += f"   👶 Дітей: {preg['children_count']}\n"
            text += f"   ⏳ Час до пологів: {time_str}\n\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /pregnancies: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['claimchildren'])
def claim_children_cmd(message):
    """Забрати дітей після пологів"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        pregnancy = get_pregnancy(user_id, chat_id)
        
        if not pregnancy:
            bot.reply_to(message, "❌ У тебе немає активної вагітності!")
            return
        
        if pregnancy.get('claimed', False):
            bot.reply_to(message, "❌ Ти вже забрав дітей!")
            return
        
        now = int(time.time())
        if now < pregnancy['due_date']:
            time_left = int((pregnancy['due_date'] - now) / 60)
            bot.reply_to(message, f"⏳ Ще рано! До пологів залишилось {time_left} хвилин.")
            return
        
        # Народжуємо дітей
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ У тебе немає хряка!")
            return
        
        father_hryak = get_hryak(pregnancy['father_user_id'], chat_id)
        father_name = father_hryak['name'] if father_hryak else "Невідомий"
        
        children_names = []
        for i in range(pregnancy['children_count']):
            # Генеруємо ім'я дитини
            child_name = f"{hryak['name'][:3]}-{father_name[:3]}-{i+1}"
            # Вага дитини (середнє між батьками + рандом)
            father_weight = father_hryak['weight'] if father_hryak else 10
            child_weight = max(1, int((hryak['weight'] + father_weight) / 2) + random.randint(-5, 5))
            
            # Спадкова ознака
            traits = ['Швидкий', 'Сильний', 'Розумний', 'Хитрий', 'Великий', 'Малий']
            inherited_trait = random.choice(traits) if random.random() < 0.3 else ''
            
            # Додаємо дитину
            add_child(
                user_id, chat_id,
                pregnancy['father_user_id'], user_id,
                child_name, child_weight, inherited_trait
            )
            children_names.append(child_name)
        
        # Позначаємо вагітність як виконану
        claim_pregnancy(pregnancy['id'])
        
        # Нагорода за дітей
        reward_coins = pregnancy['children_count'] * 50
        reward_xp = pregnancy['children_count'] * 25
        add_coins(user_id, chat_id, reward_coins)
        add_xp(user_id, chat_id, reward_xp)
        
        text = f"""🎉 **Пологи відбулися!**

🐷 {hryak['name']} народив {pregnancy['children_count']} дітей:
{', '.join(children_names)}

💰 Нагорода: +{reward_coins} монет, +{reward_xp} XP

Використовуй /children щоб побачити дітей!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /claimchildren: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ТУРНІРИ
# ============================================

@bot.message_handler(commands=['tournament'])
def tournament_cmd(message):
    """Турніри - створити або приєднатися"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        # Якщо немає аргументів - показуємо інфо
        if len(parts) < 2:
            active_tournament = get_active_tournament(chat_id)
            
            if not active_tournament:
                text = """🏆 **ТУРНІРИ**

Вхідний внесок: 10 кг
Призовий фонд: 70% від збору
Друге місце: 20% від збору
Організатор: 10%

**Команди:**
/tournament create <назва> - створити турнір
/tournament join - приєднатися до турніру
/tournament start - почати турнір (адмін)
/tournament info - інформація про активний турнір

**Формат:** Олімпійська система (на вибування)
Переможець визначається за вагою хряка!"""
            else:
                participants = get_tournament_participants(active_tournament['id'])
                text = f"""🏆 **ТУРНІР: {active_tournament['name']}**

Вхідний внесок: {active_tournament['entry_fee']} кг
Призовий фонд: {active_tournament['prize_pool']} кг
Учасників: {len(participants)}
Статус: {active_tournament['status']}

**Учасники:**
"""
                for i, p in enumerate(participants, 1):
                    hryak = get_hryak(p['user_id'], chat_id)
                    name = hryak['name'] if hryak else "Невідомо"
                    text += f"{i}. {name} - {p['hryak_weight']} кг\n"
                
                text += "\n**Команди:**\n/tournament join - приєднатися\n/tournament start - почати (адмін)"
            
            bot.reply_to(message, text, parse_mode="Markdown")
            return
        
        action = parts[1].lower()
        
        # Створення турніру
        if action == 'create':
            # Перевіряємо чи вже є активний турнір
            active_tournament = get_active_tournament(chat_id)
            if active_tournament:
                bot.reply_to(message, "❌ Вже є активний турнір! Зачекайте завершення.")
                return
            
            # Отримуємо назву турніру
            tournament_name = ' '.join(parts[2:]) if len(parts) > 2 else f"Турнір #{int(time.time()) % 10000}"
            
            # Створюємо турнір
            tournament_id = create_tournament(chat_id, tournament_name, entry_fee=10)
            
            if tournament_id:
                text = f"""🏆 **ТУРНІР СТВОРЕНО!**

Назва: {tournament_name}
Вхідний внесок: 10 кг
ID турніру: {tournament_id}

Напиши /tournament join щоб приєднатися!
Мінімум 4 учасники для старту."""
                bot.reply_to(message, text, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Помилка створення турніру!")
        
        # Приєднання до турніру
        elif action == 'join':
            active_tournament = get_active_tournament(chat_id)
            
            if not active_tournament:
                bot.reply_to(message, "❌ Немає активного турніру!")
                return
            
            if active_tournament['status'] != 'waiting':
                bot.reply_to(message, "❌ Турнір вже почався!")
                return
            
            # Перевіряємо чи вже в турнірі
            participants = get_tournament_participants(active_tournament['id'])
            for p in participants:
                if p['user_id'] == user_id:
                    bot.reply_to(message, "✅ Ти вже в турнірі!")
                    return
            
            # Перевіряємо чи є хряк
            hryak = get_hryak(user_id, chat_id)
            if not hryak:
                bot.reply_to(message, "❌ У тебе немає хряка! Введи /grow")
                return
            
            # Перевіряємо баланс
            currency = get_user_currency(user_id, chat_id)
            if currency['coins'] < active_tournament['entry_fee']:
                bot.reply_to(message, f"❌ Недостатньо монет! Потрібно {active_tournament['entry_fee']} кг")
                return
            
            # Знімаємо вхідний внесок
            update_user_currency(user_id, chat_id, coins=currency['coins'] - active_tournament['entry_fee'])
            
            # Приєднуємо до турніру
            if join_tournament(active_tournament['id'], user_id, chat_id, hryak['weight']):
                bot.reply_to(message, f"✅ Ти приєднався до турніру!\nХряк: {hryak['name']} ({hryak['weight']} кг)")
            else:
                bot.reply_to(message, "❌ Помилка приєднання!")
        
        # Початок турніру
        elif action == 'start':
            active_tournament = get_active_tournament(chat_id)
            
            if not active_tournament:
                bot.reply_to(message, "❌ Немає активного турніру!")
                return
            
            # Перевіряємо чи адмін
            if not is_admin(chat_id, user_id):
                bot.reply_to(message, "❌ Тільки адміни можуть почати турнір!")
                return
            
            participants = get_tournament_participants(active_tournament['id'])
            
            if len(participants) < 2:
                bot.reply_to(message, "❌ Потрібно мінімум 2 учасники!")
                return
            
            # Починаємо турнір
            update_tournament_status(active_tournament['id'], 'in_progress')
            
            # Визначаємо переможця (найбільша вага)
            winner = max(participants, key=lambda x: x['hryak_weight'])
            
            # Розподіл призу
            prize_pool = active_tournament['prize_pool']
            winner_prize = int(prize_pool * 0.7)
            second_prize = int(prize_pool * 0.2) if len(participants) > 1 else 0
            
            # Нагороджуємо переможця
            add_coins(winner['user_id'], chat_id, winner_prize)
            add_xp(winner['user_id'], chat_id, 50)
            
            # Нагороджуємо другого (якщо є)
            if second_prize > 0 and len(participants) > 1:
                participants.remove(winner)
                second = max(participants, key=lambda x: x['hryak_weight'])
                add_coins(second['user_id'], chat_id, second_prize)
                add_xp(second['user_id'], chat_id, 25)
            
            # Завершуємо турнір
            update_tournament_status(active_tournament['id'], 'finished', winner['user_id'])
            
            winner_hryak = get_hryak(winner['user_id'], chat_id)
            
            text = f"""🏆 **ТУРНІР ЗАВЕРШЕНО!**

🥇 Переможець: <a href="tg://user?id={winner['user_id']}">{winner_hryak['name'] if winner_hryak else 'Unknown'}</a>
💰 Нагорода: +{winner_prize} монет, +50 XP

🥈 Друге місце: +{second_prize} монет, +25 XP

Всього учасників: {len(participants)}
Призовий фонд: {prize_pool} кг"""
            
            bot.reply_to(message, text, parse_mode="HTML")
        
        # Інформація про турнір
        elif action == 'info':
            active_tournament = get_active_tournament(chat_id)
            
            if not active_tournament:
                bot.reply_to(message, "❌ Немає активного турніру!")
                return
            
            participants = get_tournament_participants(active_tournament['id'])
            
            text = f"""🏆 **ІНФОРМАЦІЯ ПРО ТУРНІР**

Назва: {active_tournament['name']}
Вхідний внесок: {active_tournament['entry_fee']} кг
Призовий фонд: {active_tournament['prize_pool']} кг
Статус: {active_tournament['status']}
Учасників: {len(participants)}

**Учасники:**
"""
            for i, p in enumerate(participants, 1):
                hryak = get_hryak(p['user_id'], chat_id)
                name = hryak['name'] if hryak else "Невідомо"
                text += f"{i}. {name} - {p['hryak_weight']} кг\n"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        
        else:
            bot.reply_to(message, "❌ Невідома дія! Використовуй /tournament для інфо.")
    
    except Exception as e:
        logger.error(f"❌ Помилка /tournament: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ГІЛЬДІЇ ХРЯКІВ
# ============================================

GUILD_CREATE_COST = 100  # Вартість створення гільдії

@bot.message_handler(commands=['createguild'])
def create_guild_cmd(message):
    """Створити гільдію"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 2:
            bot.reply_to(message, """🏰 **СТВОРЕННЯ ГІЛЬДІЇ**

Вартість: 100 монет
Використання: /createguild <назва> [опис]

Приклад: /createguild Сильні Хряки Найкраща гільдія""", parse_mode="Markdown")
            return
        
        guild_name = parts[1]
        description = parts[2] if len(parts) > 2 else ""
        
        # Перевіряємо довжину назви
        if len(guild_name) < 3 or len(guild_name) > 32:
            bot.reply_to(message, "❌ Назва має бути від 3 до 32 символів!")
            return
        
        # Перевіряємо чи вже в гільдії
        user_guild = get_user_guild(user_id, chat_id)
        if user_guild:
            bot.reply_to(message, f"❌ Ти вже в гільдії \"{user_guild['name']}\"!")
            return
        
        # Перевіряємо баланс
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < GUILD_CREATE_COST:
            bot.reply_to(message, f"❌ Недостатньо монет! Потрібно {GUILD_CREATE_COST} монет")
            return
        
        # Перевіряємо чи існує гільдія з такою назвою
        existing_guild = get_guild_by_name(guild_name)
        if existing_guild:
            bot.reply_to(message, "❌ Гільдія з такою назвою вже існує!")
            return
        
        # Знімаємо кошти
        update_user_currency(user_id, chat_id, coins=currency['coins'] - GUILD_CREATE_COST)
        
        # Створюємо гільдію
        guild_id = create_guild(chat_id, guild_name, user_id, description)
        
        if guild_id:
            bot.reply_to(message, f"""🏰 **ГІЛЬДІЯ СТВОРЕНА!**

Назва: {guild_name}
Опис: {description or "Не вказано"}
Власник: <a href="tg://user?id={user_id}">{message.from_user.first_name}</a>

Використовуй /guild щоб побачити інформацію про гільдію!
Запроси друзів командою /guildjoin""", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ Помилка створення гільдії!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /createguild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild'])
def guild_cmd(message):
    """Інфор��ація про гільдію"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        # Якщо є назва гільдії - показуємо інформацію про неї
        if len(parts) > 1:
            guild_name = parts[1]
            guild = get_guild_by_name(guild_name)
            
            if not guild:
                bot.reply_to(message, "❌ Гільдію не знайдено!")
                return
            
            members = get_guild_members(guild['id'])
            
            text = f"""🏰 **{guild['name']}**

📝 Опис: {guild['description'] or "Не вказано"}
👑 Власник: ID {guild['owner_user_id']}
📊 Рівень: {guild['level']}
⭐ XP: {guild['xp']}
💰 Скарбниця: {guild['coins']} м��нет
👥 Учасників: {guild['member_count']}

**Топ учасників:**
"""
            for i, member in enumerate(members[:5], 1):
                role_emoji = "👑" if member['role'] == 'owner' else "🔷" if member['role'] == 'officer' else "▫️"
                text += f"{i}. {role_emoji} ID {member['user_id']} - {member['contribution']} внеску\n"
            
            bot.reply_to(message, text, parse_mode="Markdown")
            return
        
        # Показуємо гільдію користувача
        user_guild = get_user_guild(user_id, chat_id)
        
        if not user_guild:
            bot.reply_to(message, """🏰 **ГІЛЬДІЇ**

Ти не в гільдії!

**Команди:**
/createguild <назва> [опис] - створити гільдію (100 монет)
/guildjoin <назва> - приєднатися до гільдії
/guildtop - рейтинг гільдій

**Переваги гільдій:**
- Спільна скарбниця
- Бонуси до XP (+10% за рівень гільдії)
- Гільдійні війни (в розробці)
- Рейтинг гільдій""", parse_mode="Markdown")
            return
        
        members = get_guild_members(user_guild['id'])
        user_rank = get_guild_rank(user_guild['id'], user_id)
        
        text = f"""🏰 **{user_guild['name']}**

📝 Опис: {user_guild['description'] or "Не вказано"}
👑 Власник: ID {user_guild['owner_user_id']}
📊 Рівень: {user_guild['level']}
⭐ XP: {user_guild['xp']}
💰 Скарбниця: {user_guild['coins']} монет
👥 Учасників: {user_guild['member_count']}

**Твоя роль:** {user_rank['role'].upper()}
**Твій внесок:** {user_rank['contribution']}

**Учасники:**
"""
        for i, member in enumerate(members, 1):
            role_emoji = "👑" if member['role'] == 'owner' else "🔷" if member['role'] == 'officer' else "▫️"
            text += f"{i}. {role_emoji} ID {member['user_id']} - {member['contribution']} внеску\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"❌ Помилка /guild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guildjoin'])
def guild_join_cmd(message):
    """Приєднатися до гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guildjoin <назва гільдії>")
            return
        
        guild_name = parts[1]
        guild = get_guild_by_name(guild_name)
        
        if not guild:
            bot.reply_to(message, "❌ Гільдію не знайдено!")
            return
        
        # Перевіряємо чи вже в гільдії
        user_guild = get_user_guild(user_id, chat_id)
        if user_guild:
            bot.reply_to(message, f"❌ Ти вже в гільдії \"{user_guild['name']}\"!")
            return
        
        # Приєднуємося
        if join_guild(guild['id'], user_id, chat_id):
            bot.reply_to(message, f"""✅ Ти приєднався до гільдії "{guild['name']}"!

Використовуй /guild щоб побачити інформацію.""")
        else:
            bot.reply_to(message, "❌ Помилка вступу до гільдії!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /guildjoin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guildleave'])
def guild_leave_cmd(message):
    """Вийти з гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        
        if not user_guild:
            bot.reply_to(message, "❌ Ти не в гільдії!")
            return
        
        # Перевіряємо чи не власник
        if user_guild['owner_user_id'] == user_id:
            bot.reply_to(message, """❌ Власник не може вийти з гільдії!

**Команди:**
/transferguild <user_id> - передати володіння
/deleteguild - видалити гільдію""")
            return
        
        # Виходимо
        if leave_guild(user_guild['id'], user_id):
            bot.reply_to(message, f"✅ Ти вийшов з гільдії \"{user_guild['name']}\"!")
        else:
            bot.reply_to(message, "❌ Помилка виходу з гільдії!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /guildleave: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guildtop'])
def guild_top_cmd(message):
    """Рейтинг гільдій"""
    chat_id = message.chat.id
    
    try:
        guilds = get_all_guilds(chat_id)
        
        if not guilds:
            bot.reply_to(message, "🏰 **ГІЛЬДІЇ**\n\nВ чаті ще немає гільдій!\n\nСтвори свою: /createguild <назва>")
            return
        
        text = "🏆 **ТОП ГІЛЬДІЙ**\n\n"
        
        for i, guild in enumerate(guilds[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} **{guild['name']}** - {guild['level']} рівень, {guild['xp']} XP, {guild['member_count']} учасників\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"❌ Помилка /guildtop: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['transferguild'])
def transfer_guild_cmd(message):
    """Передати володіння гільдією"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /transferguild <user_id>")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        
        if not user_guild:
            bot.reply_to(message, "❌ Ти не в гільдії!")
            return
        
        if user_guild['owner_user_id'] != user_id:
            bot.reply_to(message, "❌ Тільки власник може передати володіння!")
            return
        
        new_owner_id = int(parts[1])
        
        # Перевіряємо чи є новий власник в гільдії
        members = get_guild_members(user_guild['id'])
        member_ids = [m['user_id'] for m in members]
        
        if new_owner_id not in member_ids:
            bot.reply_to(message, "❌ Цей користувач не в гільдії!")
            return
        
        if new_owner_id == user_id:
            bot.reply_to(message, "❌ Ти вже власник!")
            return
        
        # Передаємо володіння
        if transfer_guild_owner(user_guild['id'], new_owner_id):
            bot.reply_to(message, f"✅ Ти передав володіння гільдією \"{user_guild['name']}\" користувачу ID {new_owner_id}!")
        else:
            bot.reply_to(message, "❌ Помилка передачі володіння!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /transferguild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['deleteguild'])
def delete_guild_cmd(message):
    """Видалити гільдію"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        
        if not user_guild:
            bot.reply_to(message, "❌ ��и не в гільдії!")
            return
        
        if user_guild['owner_user_id'] != user_id:
            bot.reply_to(message, "❌ Тільки власник може видалити г������������������льдію!")
            return
        
        # Видаляємо гільдію
        if delete_guild(user_guild['id']):
            bot.reply_to(message, f"✅ Гільдія \"{user_guild['name']}\" видалена!")
        else:
            bot.reply_to(message, "❌ Помилка видалення гільдії!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /deleteguild: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['contribute'])
def contribute_cmd(message):
    """Внести внесок до гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /contribute <сума>")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        
        if not user_guild:
            bot.reply_to(message, "❌ Ти не в гільдії!")
            return
        
        amount = int(parts[1])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        # Перевіряємо баланс
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < amount:
            bot.reply_to(message, "❌ Недостатньо монет!")
            return
        
        # Знімаємо кошти і додаємо до гільдії
        update_user_currency(user_id, chat_id, coins=currency['coins'] - amount)
        
        # Додаємо до скарбниці гільдії (тут поки просто оновлюємо XP)
        update_guild_xp(user_guild['id'], amount)
        add_guild_contribution(user_guild['id'], user_id, amount)
        
        bot.reply_to(message, f"""✅ Внесок: {amount} монет
Твій загальний внесок: {get_guild_rank(user_guild['id'], user_id)['contribution']}
XP гільдії: +{amount}""")
    
    except ValueError:
        bot.reply_to(message, "❌ Невірна сума!")
    except Exception as e:
        logger.error(f"❌ Помилка /contribute: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# СКІНИ ДЛЯ ХРЯКІВ
# ============================================

@bot.message_handler(commands=['skins'])
def skins_cmd(message):
    """Показати скіни"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        # Якщо є аргумент - показуємо інформацію про скін
        if len(parts) > 1:
            skin_name = parts[1]
            skin = get_skin_by_name(skin_name)
            
            if not skin:
                # Спробуємо за ID
                try:
                    skin_id = int(skin_name)
                    skin = get_skin(skin_id)
                except:
                    pass
            
            if not skin:
                bot.reply_to(message, "❌ Скін не знайдено!")
                return
            
            rarity_emoji = "⚪" if skin['rarity'] == 'common' else "🟢" if skin['rarity'] == 'rare' else "🔵" if skin['rarity'] == 'epic' else "🟣" if skin['rarity'] == 'legendary' else "🟡"
            
            text = f"""{skin['icon']} **{skin['display_name']}**

{skin['description']}
💰 Ціна: {skin['price']} монет
⭐ Рідкість: {skin['rarity'].upper()} {rarity_emoji}"""
            
            if skin['bonus_type']:
                text += f"\n🎁 Бонус: +{skin['bonus_value']}% до {skin['bonus_type']}"
            
            # Перевіряємо чи має користувач цей скін
            user_has = has_skin(user_id, chat_id, skin['id'])
            if user_has:
                text += "\n\n✅ У тебе є цей скін!"
            
            bot.reply_to(message, text, parse_mode="Markdown")
            return
        
        # Показуємо всі скіни або скіни користувача
        action = parts[1] if len(parts) > 1 else 'all'
        
        if action == 'me':
            user_skins = get_user_skins(user_id, chat_id)
            
            if not user_skins:
                bot.reply_to(message, "🎨 **ТВОЇ СКІНИ**\n\nУ тебе ще немає скінів!\n\nКупи в /shop або використай /skins <назва>")
                return
            
            text = "🎨 **ТВОЇ СКІНИ**\n\n"
            for skin in user_skins:
                equipped = "✅ " if skin['equipped'] else ""
                text += f"{equipped}{skin['icon']} **{skin['display_name']}** - {skin['description']}\n"
            
            text += "\n**Використання:**\n/equipskin <назва> - одягнути скін"
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            all_skins = get_all_skins()
            
            text = "🎨 **МАГАЗИН СКІНІВ**\n\n"
            for skin in all_skins:
                rarity_emoji = "⚪" if skin['rarity'] == 'common' else "🟢" if skin['rarity'] == 'rare' else "🔵" if skin['rarity'] == 'epic' else "🟣" if skin['rarity'] == 'legendary' else "🟡"
                text += f"{skin['icon']} **{skin['display_name']}** - {skin['price']} монет {rarity_emoji}\n"
                text += f"  _{skin['description']}_\n\n"
            
            text += "**Купити:** /buyskin <назва>\n**Одягнути:** /equipskin <назва>"
            bot.reply_to(message, text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"❌ Помилка /skins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['buyskin'])
def buy_skin_cmd(message):
    """Купити скін"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /buyskin <назва скіну>")
            return
        
        skin_name = parts[1]
        skin = get_skin_by_name(skin_name)
        
        if not skin:
            bot.reply_to(message, "❌ Скін не знайдено!")
            return
        
        # Перевіряємо чи вже має
        if has_skin(user_id, chat_id, skin['id']):
            bot.reply_to(message, "✅ У тебе вже є цей скін!")
            return
        
        # Перевіряємо баланс
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < skin['price']:
            bot.reply_to(message, f"❌ Недостатньо монет! Потрібно {skin['price']}")
            return
        
        # Купуємо
        if buy_skin(user_id, chat_id, skin['id']):
            update_user_currency(user_id, chat_id, coins=currency['coins'] - skin['price'])
            bot.reply_to(message, f"✅ Куплено скін: {skin['display_name']}!\n\nОдягни: /equipskin {skin['name']}")
        else:
            bot.reply_to(message, "❌ Помилка купівлі!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /buyskin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['equipskin'])
def equip_skin_cmd(message):
    """Одягнути скін"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /equipskin <назва скіну>")
            return
        
        skin_name = parts[1]
        skin = get_skin_by_name(skin_name)
        
        if not skin:
            bot.reply_to(message, "❌ Скін не знайдено!")
            return
        
        # Перевіряємо чи має скін
        if not has_skin(user_id, chat_id, skin['id']):
            bot.reply_to(message, "❌ У тебе немає цього скіну!")
            return
        
        # Одягаємо
        if equip_skin(user_id, chat_id, skin['id']):
            bot.reply_to(message, f"✅ Одягнуто скін: {skin['display_name']}!\n\nТвій хряк тепер виглядає як {skin['icon']}")
        else:
            bot.reply_to(message, "❌ Помилка одягання!")
    
    except Exception as e:
        logger.error(f"❌ Помилка /equipskin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# БОС-ДУЕЛІ (PvE)
# ============================================

@bot.message_handler(commands=['boss'])
def boss_cmd(message):
    """Бос-дуель"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        # Отримуємо активного боса
        boss = get_active_boss()
        
        if not boss:
            bot.reply_to(message, """🐲 **БОС-ДУЕЛІ**

Наразі немає активного боса!
Бос з'явиться найближчим часом...

**Як бити боса:**
/boss attack - атакувати боса
/boss info - інформація про боса""")
            return
        
        # Якщо є аргумент
        if len(parts) > 1:
            action = parts[1].lower()
            
            if action == 'info':
                hp_percent = int((boss['health'] / boss['max_health']) * 100)
                hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)
                
                participants = get_boss_participants(boss['id'])
                
                text = f"""🐲 **{boss['name']}**

⭐ Рівень: {boss['level']}
❤️ Здоров'я: {boss['health']}/{boss['max_health']}
{hp_bar} {hp_percent}%
⚔️ Шкода: {boss['damage']}
💰 Нагорода: {boss['reward_coins']} монет, {boss['reward_xp']} XP

**Топ гравців:**
"""
                for i, p in enumerate(participants[:5], 1):
                    text += f"{i}. ID {p['user_id']} - {p['damage_dealt']} шкоди\n"
                
                bot.reply_to(message, text, parse_mode="Markdown")
            
            elif action == 'attack':
                hryak = get_hryak(user_id, chat_id)
                if not hryak:
                    bot.reply_to(message, "❌ У тебе немає хряка! Введи /grow")
                    return

                # Розраховуємо шкоду (вага хряка + рандом)
                base_damage = hryak['weight'] * 2
                random_damage = random.randint(-10, 20)

                # Бонус від скіну
                skin_bonus = get_skin_bonus(user_id, chat_id, 'weight_bonus')
                total_damage = max(1, int((base_damage + random_damage) * (1 + skin_bonus / 100)))

                # Атакуємо
                result = attack_boss(boss['id'], user_id, chat_id, total_damage)

                if result and result.get('defeated'):
                    # Бос переможений!
                    participants = get_boss_participants(boss['id'])

                    # Розподіл нагороди
                    total_damage = sum(p['damage_dealt'] for p in participants)

                    for p in participants:
                        share = p['damage_dealt'] / total_damage if total_damage > 0 else 0
                        coins_reward = int(boss['reward_coins'] * share)
                        xp_reward = int(boss['reward_xp'] * share)

                        if coins_reward > 0:
                            add_coins(p['user_id'], chat_id, coins_reward)
                        if xp_reward > 0:
                            add_xp(p['user_id'], chat_id, xp_reward)

                    # Оголошуємо перемогу
                    defeated_by = result.get('defeated_by_user_id') if result else None
                    winner_hryak = get_hryak(defeated_by or user_id, chat_id)
                    winner_name = winner_hryak['name'] if winner_hryak else "Невідомо"

                    bot.reply_to(message, f"""🎉 **БОСА ПЕРЕМОЖЕНО!**

{boss['name']} загинув від рук героїв!
Останній удар: {winner_name}

**Нагороди розподілено:**
Кожен учасник отримав монети та XP пропорційно до шкоди!

Новий бос з'явиться найближчим часом...""")
                elif result and not result.get('defeated'):
                    # Бос ще жив - використовуємо дані з result
                    remaining = result.get('remaining_health', boss['health'])
                    max_health = result.get('max_health', boss['max_health'])
                    
                    hp_percent = int((remaining / max_health) * 100)
                    hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

                    bot.reply_to(message, f"""⚔️ **АТАКА!**

Твій хряк {hryak['name']} завдав {total_damage} шкоди!

🐲 {boss['name']}
❤️ {remaining}/{max_health} ({hp_percent}%)
{hp_bar}

Продовжуй атакувати командою /boss attack!""")
                else:
                    bot.reply_to(message, "❌ Помилка атаки! Спробуй ще раз.")
        else:
            # Показуємо інформацію про боса
            hp_percent = int((boss['health'] / boss['max_health']) * 100)
            hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

            text = f"""🐲 **{boss['name']}**

⭐ Рівень: {boss['level']}
❤️ Здоров'я: {boss['health']}/{boss['max_health']}
{hp_bar} {hp_percent}%
⚔️ Шкода: {boss['damage']}
💰 Нагорода: {boss['reward_coins']} монет, {boss['reward_xp']} XP

**Команди:**
/boss attack - атакувати боса
/boss info - детальна інформація

**Як це працює:**
1. Кожен гравець може атакувати боса
2. Шкода = вага хряка × 2 + рандом
3. Нагорода розподіляється пропорційно до шкоди
4. Той хто нанесе останній удар - отримає бонус!"""

            bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /boss: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# СЕЗОННІ ІВЕНТИ
# ============================================

@bot.message_handler(commands=['events'])
def events_cmd(message):
    """Показати сезонні івенти"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        events = get_all_events()
        
        if not events:
            bot.reply_to(message, get_text(user_id, 'no_active_events'))
            return
        
        text = "🎉 **СЕЗОННІ ІВЕНТИ**\n\n"
        now = int(time.time())
        
        for event in events:
            status_emoji = "✅" if event['is_active'] and event['start_date'] <= now <= event['end_date'] else "⏳" if event['start_date'] > now else "❌"
            
            # Прогрес користувача
            progress = get_user_event_progress(user_id, event['id'])
            progress_text = f" (Твій прогрес: {progress['progress']})" if progress else ""
            
            time_left = event['end_date'] - now if event['end_date'] > now else 0
            days_left = time_left // 86400 if time_left > 0 else 0
            
            text += f"""{status_emoji} **{event['name']}**
{event['description']}{progress_text}
🎁 Нагорода: {event['special_reward_coins']} монет, {event['special_reward_xp']} XP
⏳ Закінчується через: {days_left} дн.

"""
        
        text += "**Команди:**\n/eventsclaim <event_id> - забрати нагороду"
        
        bot.reply_to(message, text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"❌ Помилка /events: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['eventsclaim'])
def claim_events_cmd(message):
    """Забрати нагороду за івент"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /eventsclaim <event_id>")
            return
        
        event_id = int(parts[1])
        
        # Перевіряємо івент
        events = get_all_events()
        event = next((e for e in events if e['id'] == event_id), None)
        
        if not event:
            bot.reply_to(message, "❌ Івент не знайдено!")
            return
        
        # Перевіряємо прогрес
        progress = get_user_event_progress(user_id, event_id)
        
        if not progress:
            bot.reply_to(message, "❌ Ти не брав участі в цьому івенті!")
            return
        
        if progress['reward_claimed']:
            bot.reply_to(message, "❌ Ти вже забрав нагороду!")
            return
        
        # Забираємо нагороду
        claim_event_reward(user_id, event_id)
        add_coins(user_id, chat_id, event['special_reward_coins'])
        add_xp(user_id, chat_id, event['special_reward_xp'])
        
        bot.reply_to(message, f"""🎉 **Нагороду отримано!**

+{event['special_reward_coins']} монет
+{event['special_reward_xp']} XP

Дякуємо за участь в {event['name']}!""")
    
    except Exception as e:
        logger.error(f"❌ Помилка /eventsclaim: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['webapp'])
def webapp_cmd(message):
    """Відкрити Web App"""
    chat_id = message.chat.id
    
    # Отримуємо Render URL
    render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://trashbot-n0nd.onrender.com')
    webapp_url = f"{render_url}/webapp"
    
    # Створюємо inline кнопку
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎮 Відкрити Web App", web_app=types.WebAppInfo(webapp_url)))
    
    bot.send_message(chat_id, f"""🎮 **Web App готовий!**

Відкрий сучасний інтерфейс бота:
- 🐷 Профіль хряка
- 🏪 Магазин скінів
- 🎒 Інвентар
- 🏆 Лідерборди

Натисни кнопку нижче 👇""", 
    reply_markup=markup, parse_mode="Markdown")


# ============================================
# WEB APP DATA HANDLER
# ============================================

@bot.message_handler(content_types=['web_app_data'])
def webapp_data_handler(message):
    """Обробка даних з Web App"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        # Отримуємо дані з Web App
        data = json.loads(message.web_app_data.data)
        
        if data.get('type') == 'command':
            command = data.get('command')
            
            # Імітуємо виконання команди
            if command == 'grow':
                grow_hryak(message)
            elif command == 'daily':
                daily_cmd(message)
            elif command == 'quests':
                quests_cmd(message)
            elif command == 'achievements':
                achievements_cmd(message)
            elif command == 'menu':
                menu_cmd(message)
            elif command == 'help':
                help_cmd(message)
            elif command == 'boss':
                boss_cmd(message)
    except Exception as e:
        logger.error(f"❌ Помилка web_app_data: {e}")


# ============================================
# МУЛЬТИ-МОВНІСТЬ
# ============================================

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    """Вибір мови"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        # Створюємо inline клавіатуру з мовами
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for lang_code, lang_name in LANGUAGES.items():
            current_lang = get_user_language(user_id)
            is_current = lang_code == current_lang
            button_text = f"{'✅ ' if is_current else ''}{lang_name}"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"lang_{lang_code}"))
        
        bot.reply_to(message, get_text(user_id, 'lang_select'), reply_markup=markup)
    
    except Exception as e:
        logger.error(f"❌ Помилка /lang: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def lang_callback(call):
    """Обробка вибору мови"""
    user_id = call.from_user.id
    lang_code = call.data.split('_')[1]
    
    try:
        if lang_code in LANGUAGES:
            set_user_language(user_id, lang_code)
            bot.answer_callback_query(call.id, get_text(user_id, 'lang_changed', lang=LANGUAGES[lang_code]))
            
            # Оновлюємо повідомлення
            markup = types.InlineKeyboardMarkup(row_width=1)
            for code, name in LANGUAGES.items():
                is_current = code == lang_code
                markup.add(types.InlineKeyboardButton(f"{'✅ ' if is_current else ''}{name}", callback_data=f"lang_{code}"))
            
            bot.edit_message_text(
                get_text(user_id, 'lang_changed', lang=LANGUAGES[lang_code]),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"❌ Помилка lang_callback: {e}")
        bot.answer_callback_query(call.id, "Error")


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
    
    # Оновлюємо квест chat_active (напиши 50 повідомлень)
    quests = get_daily_quests(user_id, chat_id)
    quest_progress = {q['quest_id']: q for q in quests}
    chat_quest = quest_progress.get('chat_active', {'progress': 0, 'target': 50})
    new_chat_progress = min(chat_quest['progress'] + 1, 50)
    chat_completed = new_chat_progress >= 50
    update_daily_quest(user_id, chat_id, 'chat_active', new_chat_progress, 50, completed=chat_completed)


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


# ============================================
# WEB APP ROUTES
# ============================================

@flask_app.route('/webapp')
@flask_app.route('/webapp/')
def webapp_index():
    """Головна сторінка Web App"""
    return flask_app.send_static_file('webapp/index.html')

@flask_app.route('/static/webapp/style.css')
def webapp_style():
    """CSS для Web App"""
    return flask_app.send_static_file('webapp/style.css'), {'Content-Type': 'text/css'}

@flask_app.route('/static/webapp/app.js')
def webapp_app():
    """JS для Web App"""
    return flask_app.send_static_file('webapp/app.js'), {'Content-Type': 'application/javascript'}

# Додамо також простіші routes
@flask_app.route('/webapp/style.css')
def webapp_style_alt():
    """CSS для Web App (альтернативний route)"""
    return flask_app.send_static_file('webapp/style.css'), {'Content-Type': 'text/css'}

@flask_app.route('/webapp/app.js')
def webapp_app_alt():
    """JS для Web App (альтернативний route)"""
    return flask_app.send_static_file('webapp/app.js'), {'Content-Type': 'application/javascript'}


# ============================================
# WEB APP API ENDPOINTS
# ============================================

@flask_app.route('/api/webapp/user', methods=['GET'])
def api_get_user():
    """Отримати дані користувача"""
    try:
        user_id = int(request.args.get('user_id', 0))
        chat_id = int(request.args.get('chat_id', 0))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        # Get user data
        currency = get_user_currency(user_id, chat_id or -1)
        hryak = get_hryak(user_id, chat_id or -1)
        stats = get_user_stats(user_id, chat_id or -1)
        trachen_stats = get_trachen_stats(user_id, chat_id or -1)
        tournament_stats = get_user_tournament_stats(user_id, chat_id or -1)
        guild_stats = get_user_guild_stats(user_id, chat_id or -1)
        boss_stats = get_user_boss_stats(user_id, chat_id or -1)
        user_guild = get_user_guild(user_id, chat_id or -1)
        equipped_skin = get_user_equipped_skin(user_id, chat_id or -1)
        
        # Check if can feed
        can_feed = False
        if hryak:
            now = time.time()
            if hryak['last_feed'] == 0 or (now - hryak['last_feed']) >= 43200:
                can_feed = True
        
        return jsonify({
            'success': True,
            'data': {
                'coins': currency['coins'] if currency else 0,
                'xp': currency['xp'] if currency else 0,
                'level': currency['level'] if currency else 1,
                'hryak': {
                    'name': hryak['name'],
                    'weight': hryak['weight'],
                    'max_weight': hryak['max_weight'],
                    'feed_count': hryak['feed_count'],
                    'can_feed': can_feed
                } if hryak else None,
                'skin': equipped_skin,
                'stats': stats,
                'trachen_stats': trachen_stats,
                'tournament_stats': tournament_stats,
                'guild_stats': guild_stats,
                'boss_stats': boss_stats,
                'user_guild': user_guild
            }
        }), 200
    except Exception as e:
        logger.error(f"API /user error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/user-chats', methods=['GET'])
def api_get_user_chats():
    """Отримати чати користувача"""
    try:
        user_id = int(request.args.get('user_id', 0))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        # Get chats from hryaky_data
        chats = {}
        for key, h in hryaky_data.items():
            if h.get('user_id') == user_id:
                chat_id = h.get('chat_id')
                if chat_id and chat_id not in chats:
                    chats[chat_id] = {
                        'chat_id': chat_id,
                        'chat_name': f'Чат {chat_id}',
                        'hryak_name': h.get('name', 'Безіменний')
                    }
        
        return jsonify({
            'success': True,
            'data': list(chats.values())
        }), 200
    except Exception as e:
        logger.error(f"API /user-chats error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/shop', methods=['GET'])
def api_get_shop():
    """Отримати магазин"""
    try:
        items = get_shop_items()
        return jsonify({'success': True, 'data': items}), 200
    except Exception as e:
        logger.error(f"API /shop error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/skins', methods=['GET'])
def api_get_skins():
    """Отримати всі скіни"""
    try:
        skins = get_all_skins()
        return jsonify({'success': True, 'data': skins}), 200
    except Exception as e:
        logger.error(f"API /skins error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/inventory', methods=['GET'])
def api_get_inventory():
    """Отримати інвентар"""
    try:
        user_id = int(request.args.get('user_id', 0))
        chat_id = int(request.args.get('chat_id', 0))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        inventory = get_user_inventory(user_id, chat_id or -1)
        return jsonify({'success': True, 'data': inventory}), 200
    except Exception as e:
        logger.error(f"API /inventory error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/my-skins', methods=['GET'])
def api_get_my_skins():
    """Отримати скіни користувача"""
    try:
        user_id = int(request.args.get('user_id', 0))
        chat_id = int(request.args.get('chat_id', 0))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        skins = get_user_skins(user_id, chat_id or -1)
        return jsonify({'success': True, 'data': skins}), 200
    except Exception as e:
        logger.error(f"API /my-skins error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/leaderboard/chat', methods=['GET'])
def api_get_chat_leaderboard():
    """Топ хряків чату"""
    try:
        chat_id = int(request.args.get('chat_id', 0))

        # Get from hryaky_data cache
        chat_hryaky = []
        for key, h in hryaky_data.items():
            if chat_id and h.get('chat_id') != chat_id:
                continue
            chat_hryaky.append(h)

        chat_hryaky = sorted(chat_hryaky, key=lambda x: x['weight'], reverse=True)[:10]

        return jsonify({'success': True, 'data': chat_hryaky}), 200
    except Exception as e:
        logger.error(f"API /leaderboard/chat error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/leaderboard/global', methods=['GET'])
def api_get_global_leaderboard():
    """Глобальний топ хряків"""
    try:
        # Get all hryaks from cache
        all_hryaky = []
        for key, h in hryaky_data.items():
            all_hryaky.append(h)

        all_hryaky = sorted(all_hryaky, key=lambda x: x['weight'], reverse=True)[:10]

        return jsonify({'success': True, 'data': all_hryaky}), 200
    except Exception as e:
        logger.error(f"API /leaderboard/global error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/feed', methods=['POST'])
def api_feed_hryak():
    """Нагодувати хряка"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chat_id = data.get('chat_id', 0)
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        result, error = feed_hryak(user_id, chat_id)
        
        if error:
            return jsonify({'success': False, 'message': error}), 400
        
        # Add rewards
        add_coins(user_id, chat_id, 5)
        add_xp(user_id, chat_id, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'old_weight': result['old_weight'],
                'new_weight': result['new_weight'],
                'change': result['change'],
                'feed_count': result['feed_count']
            }
        }), 200
    except Exception as e:
        logger.error(f"API /feed error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/buy-item', methods=['POST'])
def api_buy_item():
    """Купити предмет"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        item_id = data.get('item_id')
        chat_id = data.get('chat_id', 0)
        
        if not user_id or not item_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Get item
        items = get_shop_items()
        item = next((i for i in items if i['item_id'] == item_id), None)
        
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        # Check balance
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < item['price']:
            return jsonify({'success': False, 'message': 'Not enough coins'}), 400
        
        # Buy item
        update_user_currency(user_id, chat_id, coins=currency['coins'] - item['price'])
        add_to_inventory(user_id, chat_id, item_id)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /buy-item error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/buy-skin', methods=['POST'])
def api_buy_skin():
    """Купити скін"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        skin_name = data.get('skin_name')
        chat_id = data.get('chat_id', 0)
        
        if not user_id or not skin_name:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Get skin
        skin = get_skin_by_name(skin_name)
        
        if not skin:
            return jsonify({'success': False, 'message': 'Skin not found'}), 404
        
        # Check balance
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < skin['price']:
            return jsonify({'success': False, 'message': 'Not enough coins'}), 400
        
        # Check if already has
        if has_skin(user_id, chat_id, skin['id']):
            return jsonify({'success': False, 'message': 'Already owned'}), 400
        
        # Buy skin
        update_user_currency(user_id, chat_id, coins=currency['coins'] - skin['price'])
        buy_skin(user_id, chat_id, skin['id'])
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /buy-skin error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/use-item', methods=['POST'])
def api_use_item():
    """Використати предмет"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        item_id = data.get('item_id')
        chat_id = data.get('chat_id', 0)
        
        if not user_id or not item_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # TODO: Implement item usage logic
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /use-item error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/execute', methods=['POST'])
def api_execute_command():
    """Виконати команду з Web App"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chat_id = data.get('chat_id')
        command = data.get('command')
        
        logger.info(f"WebApp execute: user_id={user_id}, chat_id={chat_id}, command={command}")
        
        if not user_id or not command:
            return jsonify({'success': False, 'message': 'Missing user_id or command'}), 400
        
        # Create a fake message object for command handlers
        class FakeMessage:
            def __init__(self, user_id, chat_id, text):
                self.from_user = type('obj', (object,), {'id': user_id, 'username': 'webapp'})
                self.chat = type('obj', (object,), {'id': chat_id})
                self.text = text
                self.message_id = 0
            
            def reply_to(self, text, **kwargs):
                # Just log the response
                logger.info(f"WebApp command response: {text}")
                return text
        
        fake_message = FakeMessage(user_id, chat_id, f'/{command}')
        
        # Execute command
        if command == 'grow':
            grow_hryak(fake_message)
            return jsonify({'success': True, 'message': 'Хряка отримано!'})
        elif command == 'daily':
            daily_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Бонус отримано!'})
        elif command == 'quests':
            quests_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Квести показані!'})
        elif command == 'achievements':
            achievements_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Досягнення показані!'})
        elif command == 'menu':
            menu_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Меню показане!'})
        elif command == 'help':
            help_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Допомога показана!'})
        elif command == 'boss':
            boss_cmd(fake_message)
            return jsonify({'success': True, 'message': 'Бос показаний!'})
        else:
            return jsonify({'success': False, 'message': f'Команда не підтримується: {command}'}), 400
            
    except Exception as e:
        logger.error(f"API /execute error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/equip-skin', methods=['POST'])
def api_equip_skin():
    """Одягнути скін"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        skin_name = data.get('skin_name')
        chat_id = data.get('chat_id', 0)

        if not user_id or not skin_name:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        # Get skin
        skin = get_skin_by_name(skin_name)

        if not skin:
            return jsonify({'success': False, 'message': 'Skin not found'}), 404

        # Check if has
        if not has_skin(user_id, chat_id, skin['id']):
            return jsonify({'success': False, 'message': 'You do not own this skin'}), 400

        # Equip
        equip_skin(user_id, chat_id, skin['id'])

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /equip-skin error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


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

# Запускаємо бота з retry logic
def run_bot_with_retry():
    """Запускає бота з автоматичним перезапуском при помилках"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🤖 Запуск бота (спроба {attempt + 1}/{max_retries})...")
            bot.polling(none_stop=True, interval=5, timeout=60)
            break
        except Exception as e:
            error_msg = str(e)
            if "terminated by other getUpdates request" in error_msg:
                logger.error("❌ Бот вже запущений в іншому місці! Зупинка...")
                break
            logger.error(f"❌ Помилка бота: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Перезапуск через {retry_delay} сек...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Максимальна кількість спроб вичерпана")
                raise

run_bot_with_retry()


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

⚔️ Натисни "Викл��к на дуель" щоб створити виклик!"""
    
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
    """Inline ��ля /globaltop"""
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
            description='Т��ої відкриті досягнення',
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

