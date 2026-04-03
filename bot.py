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
from quiz_questions import QUIZ_QUESTIONS
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
    get_children, add_child, get_all_pregnancies, get_children_count,
    create_tournament, get_tournament, get_active_tournament, join_tournament,
    get_tournament_participants, update_tournament_status, eliminate_participant,
    get_user_tournament_stats,
    create_guild, get_guild, get_guild_by_name, get_user_guild, get_guild_members,
    join_guild, leave_guild, get_guild_rank, update_guild_xp, add_guild_contribution,
    get_all_guilds, get_user_guild_stats, transfer_guild_owner, delete_guild,
    promote_guild_member, demote_guild_member,
    get_all_skins, get_skin, get_skin_by_name, get_user_skins, get_user_equipped_skin, get_user_inventory,
    buy_skin, equip_skin, has_skin, get_skin_bonus,
    get_active_boss, spawn_boss, attack_boss, get_boss_participants, get_user_boss_stats, get_last_boss_attack_time, save_boss_attack_time, get_last_boss, get_boss_defeat_time, get_random_boss_variety,
    get_active_events, get_all_events, get_user_event_progress, update_event_progress, claim_event_reward, cleanup_duplicate_events,
    rename_child, get_child, get_top_children, sacrifice_child, marry_children,
    get_crypto_balance, convert_game_to_crypto, get_conversion_info, CONVERSION_RATE, MIN_CONVERT, MAX_DAILY_WITHDRAW,
    record_crypto_transaction, update_transaction_status, get_user_transactions,
    create_trade, accept_trade, cancel_trade, get_pending_trades,
    get_user_quiz_progress, record_quiz_answer, get_quiz_stats,
    get_hryak_genes, create_hryak_genes, breed_hryaks, get_genetic_compatibility,
    get_children_bonuses, train_child, send_child_on_raid, get_child_power, get_active_child_raid, claim_child_raid, get_child_stamina, upgrade_child_stamina,
    # Guild wars functions
    create_territory, get_all_territories, get_territory, capture_territory, collect_territory_income,
    donate_to_chest, get_guild_chest, withdraw_from_chest,
    declare_war, join_war, add_war_contribution, end_war, get_active_wars,
    spawn_guild_boss, attack_guild_boss, get_guild_boss_participants, get_active_guild_boss,
    get_last_guild_boss_attack_time, save_guild_boss_attack_time,
    # Guild warriors and items
    buy_warrior, get_guild_warriors, get_total_warrior_power, station_warriors, get_territory_defense,
    remove_warriors_from_guild, record_territory_battle,
    WARRIOR_TYPES,
    # Items and trades
    add_item_to_user, get_user_items, get_user_total_bonuses, remove_user_item,
    create_item_trade, get_item_trade, accept_item_trade, cancel_item_trade, get_pending_trades,
    withdraw_guild_item_to_user, use_item,
    # Private casinos
    create_casino, get_casino, get_user_casino, deposit_to_casino, withdraw_from_casino,
    set_casino_limits, play_casino_game, get_casino_stats,
    get_all_casinos_in_chat, get_casino_by_id,
    ITEM_RARITIES, ITEM_TYPES,
    GENE_RARITIES, BONUS_TYPES, COLOR_TYPES, TERRITORY_TYPES
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

# Завантажуємо змінні середовища з .env файлу (для локальної розробки)
load_dotenv()

# Отримуємо токен зі змінних середовища
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))  # Твій ID для адмінки

# ПРИМУСОВО для terchizz (якщо .env не працює)
if ADMIN_ID == 0:
    ADMIN_ID = 1044325356  # terchizz user ID
    logger.warning("⚠️ ADMIN_ID не знайдено в .env! Використовується примусове значення: 1044325356")

logger.info(f"🔑 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
logger.info(f"🛡️ ADMIN_ID: {ADMIN_ID}")
logger.info(f"👤 Твій user_id (terchizz): 1044325356")
logger.info(f"✅ Адмін-команди доступні: {ADMIN_ID == 1044325356}")

if not BOT_TOKEN:
    logger.error("❌ ПОМИЛКА: BOT_TOKEN не знайдено в змінних середовища!")
    logger.error("Додай змінну середовища BOT_TOKEN з токеном бота")
    exit(1)

if ADMIN_ID == 0:
    logger.warning("⚠️ ADMIN_ID не встановлено! Адмін-команди не працюватимуть.")
    logger.warning("Додай ADMIN_ID=1044325356 в .env файл")

# Функція перевірки адміна
def is_admin(user_id):
    """Перевірка чи користувач адмін"""
    return user_id == ADMIN_ID

# Декоратор для адмін команд
def admin_only(func):
    """Декоратор для перевірки адміна"""
    def wrapper(message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return None  # Додав повернення
        return func(message, *args, **kwargs)  # Додав повернення результату
    return wrapper

def escape_markdown(text):
    """Екранує спеціальні символи MarkdownV2 в тексті"""
    if not isinstance(text, str):
        text = str(text)
    # Екрануємо спеціальні символи MarkdownV2
    # Повний список: _ * [ ] ( ) ~ > # + - = | { } . \ !
    # ВАЖЛИВО: Спочатку екрануємо backslash, потім інші символи!
    text = text.replace('\\', '\\\\')  # ПЕРШИМ!
    text = text.replace('_', '\\_')
    text = text.replace('*', '\\*')
    text = text.replace('`', '\\`')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = text.replace('(', '\\(')
    text = text.replace(')', '\\)')
    text = text.replace('~', '\\~')
    text = text.replace('>', '\\>')
    text = text.replace('#', '\\#')
    text = text.replace('+', '\\+')
    text = text.replace('-', '\\-')
    text = text.replace('=', '\\=')
    text = text.replace('|', '\\|')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('.', '\\.')
    text = text.replace('!', '\\!')
    return text

# Ініціалізація бази даних
init_db()
logger.info("✅ База даних підключена")

# Очищаємо дублікати івентів
cleanup_duplicate_events()
logger.info("✅ Дублікати івентів видалено")

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

# Кеш user_id для учасників чату {chat_id: {username: user_id}}
chat_member_ids = {}

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

def calculate_duel_result(hryak1, hryak2, user1_id=None, user2_id=None, chat_id=None):
    """Розраховує результат дуелі з урахуванням бонусів скінів"""
    # Масса впливає на силу (60%)
    mass_factor1 = hryak1['weight'] * 0.6
    mass_factor2 = hryak2['weight'] * 0.6

    # Проворність - рандом + досвід (40%)
    agility1 = random.randint(1, 20) + (hryak1['feed_count'] * 0.1)
    agility2 = random.randint(1, 20) + (hryak2['feed_count'] * 0.1)

    power1 = mass_factor1 + agility1
    power2 = mass_factor2 + agility2

    # Отримуємо бонуси удачі від скінів (впливають на шанс крита)
    luck1 = 0
    luck2 = 0
    if user1_id and chat_id:
        luck1 = get_skin_bonus(user1_id, chat_id, 'luck_bonus')
        all1 = get_skin_bonus(user1_id, chat_id, 'all_bonus')
        luck1 = luck1 + all1
    if user2_id and chat_id:
        luck2 = get_skin_bonus(user2_id, chat_id, 'luck_bonus')
        all2 = get_skin_bonus(user2_id, chat_id, 'all_bonus')
        luck2 = luck2 + all2

    # Критичний удар (10% + бонус удачі, кожен % удачі = +0.5% крита)
    crit_chance1 = 0.1 + (luck1 * 0.5 / 100)
    crit_chance2 = 0.1 + (luck2 * 0.5 / 100)
    
    crit1 = random.random() < crit_chance1
    crit2 = random.random() < crit_chance2

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

    # Додаємо класичний скін (name='classic')
    try:
        # Get classic skin ID by name
        classic_skin = get_skin_by_name('classic')
        if classic_skin:
            buy_skin(user_id, chat_id, classic_skin['id'])
            logger.info(f"✅ Додано класичний скін (id={classic_skin['id']}) для {key}")
        else:
            logger.error(f"❌ Класичний скін не знайдений в базі!")
    except Exception as e:
        logger.error(f"❌ Помилка додавання скіну: {e}")

    # Створюємо базові гени для нового хряка
    try:
        # Визначаємо випадковий колір на основі ймовірностей
        rand = random.random() * 100
        cumulative = 0
        color_type = 'normal'
        for color, data in COLOR_TYPES.items():
            cumulative += data['chance']
            if rand <= cumulative:
                color_type = color
                break
        
        create_hryak_genes(user_id, chat_id, gene_rarity='C', bonus_type=None, bonus_value=0, color_type=color_type)
        logger.info(f"✅ Створено гени для {key}, колір={color_type}")
    except Exception as e:
        logger.error(f"❌ Помилка створення генів: {e}")

    logger.info(f"✅ Створено хряка: {key}, вага={weight}")
    return hryak

def grow_hryak(message):
    """Отримати хряка для вирощування"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    logger.info(f"🐷 /grow: chat_id={chat_id}, user_id={user_id}, username={username}")

    try:
        hryak = get_hryak(user_id, chat_id)

        if hryak:
            # Екрануємо спеціальні символи в імені хряка
            hryak_name = escape_markdown(hryak['name'])
            text = f"""🐷 **Вже маєш хряка!**

Ім'я: {hryak_name}
Вага: {hryak['weight']} кг
Нагодовано: {hryak['feed_count']} разів

Використовуй /feed щоб нагодувати!"""
        else:
            # Створюємо нового хряка
            hryak = create_hryak(user_id, chat_id, username)
            # Екрануємо спеціальні символи в імені хряка
            hryak_name = escape_markdown(hryak['name'])
            text = f"""🎉 **Ти отримав хряка!**

🐷 {hryak_name}
⚖️ Вага: {hryak['weight']} кг

Тепер ти можеш його годувати раз на 12 годин командою /feed
Вирости найбільшого хряка в чаті!

🎁 Тобі додано класичний скін 🐷!"""

        bot.reply_to(message, text, parse_mode="Markdown")
        logger.info(f"✅ /grow успішно для {user_id}")
    except Exception as e:
        logger.error(f"❌ Помилка /grow: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")

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

    # Логуємо для дебагу
    logger.info(f"🔍 last_feed з БД: {hryak['last_feed']}, now: {now}, різниця: {now - hryak['last_feed']} сек")

    # Перевіряємо чи пройшло 12 годин (або це перше годування)
    if hryak['last_feed'] > 0 and now - hryak['last_feed'] < 43200:  # 12 годин = 43200 секунд
        hours_left = int((43200 - (now - hryak['last_feed'])) / 3600)
        logger.info(f"⏳ Ще рано для {key}, залишилось {hours_left} год")
        return None, f"Ще рано! Годувати можна раз на 12 годин. Залишилось {hours_left} год."

    # Годуємо
    hryak['last_feed'] = now
    hryak['feed_count'] += 1

    logger.info(f"💾 Оновлено last_feed={now} для {key}")

    # Зміна ваги (від -10 до +30 кг) - зміщено вгору для кращих шансів
    change = random.randint(-10, 30)

    # Отримуємо бонуси від скіну
    skin_weight_bonus = get_skin_bonus(user_id, chat_id, 'weight_bonus')
    skin_all_bonus = get_skin_bonus(user_id, chat_id, 'all_bonus')
    total_bonus = skin_weight_bonus + skin_all_bonus

    # Бонус застосовується до ВСІХ змін ваги (і позитивних, і негативних)
    if total_bonus > 0:
        bonus = int(abs(change) * total_bonus / 100)
        if change > 0:
            change += bonus  # Підсилюємо набір ваги
        else:
            change -= bonus  # Зменшуємо втрату (робимо менш негативним)
            change = max(-20, change)  # Максимальна втрата -20 кг
        logger.info(f"🎨 Скін бонус: weight={skin_weight_bonus}% + all={skin_all_bonus}% = {change:+d} кг")

    # Баф для @terchizz - кращі шанси на набір ваги
    if user_id == 1044325356:  # terchizz user ID
        # Додатковий баф: від -5 до +35 замість -10 до +30
        change = random.randint(-5, 35)
        logger.info(f"🎁 @terchizz баф активовано: change={change}")

    old_weight = hryak['weight']
    hryak['weight'] = max(1, hryak['weight'] + change)

    # Оновлюємо максимальну вагу
    if hryak['weight'] > hryak['max_weight']:
        hryak['max_weight'] = hryak['weight']

    save_hryaky()

    logger.info(f"✅ save_hryaky() викликано для {key}")

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
        'reward_coins': 25,
        'reward_xp': 5
    },
    'win_2_duels': {
        'name': 'Дуелянт ⚔️',
        'desc': 'Виграй 2 дуелі',
        'target': 2,
        'reward_coins': 50,
        'reward_xp': 12
    },
    'lose_10kg': {
        'name': 'Схуднення 📉',
        'desc': 'Схудни на 10 кг за раз',
        'target': 1,
        'reward_coins': 37,
        'reward_xp': 7
    },
    'gain_20kg': {
        'name': 'Набір маси 📈',
        'desc': 'Набери +20 кг за раз',
        'target': 1,
        'reward_coins': 50,
        'reward_xp': 10
    },
    'chat_active': {
        'name': 'Балакун 💬',
        'desc': 'Напиши 50 повідомлень в чаті',
        'target': 50,
        'reward_coins': 15,
        'reward_xp': 5
    },
    'feed_friends': {
        'name': 'Дружній 🐷',
        'desc': 'Нагодуй хряка коли є 3+ гравці в чаті',
        'target': 1,
        'reward_coins': 30,
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
    'energy': {'name': '⚡ Енергетик', 'desc': 'Зняти кулдаун з /feed', 'price': 50, 'effect': 'remove_cooldown', 'value': 1},
    'lucky_charm': {'name': '🍀 Підкова', 'desc': '+5% шанс на перемогу в дуелі', 'price': 200, 'effect': 'luck_bonus', 'value': 5},
    'spermobak': {'name': '🧪 Спермобак', 'desc': 'Зняти кулдаун з /trachen та /breed', 'price': 100, 'effect': 'remove_trachen_cooldown', 'value': 1},
    'pastors_milk': {'name': '🥛 Молочко пастора', 'desc': 'Зняти кулдаун з тренування дітей', 'price': 100, 'effect': 'remove_child_train_cooldown', 'value': 1}
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

        # Екрануємо спеціальні символи в імені хряка
        hryak_name = escape_markdown(result['hryak']['name'])

        text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів
💰 Нагорода: +5 монет, +2 XP

🐷 {hryak_name}"""

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

        # 🐰 ІВЕНТ: Великдень - годування = пошук яєць
        add_event_progress(user_id, chat_id, 'easter', 1)
        check_event_random_drop(user_id, chat_id, 'easter', 'годування хряка')

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

        # Екрануємо спеціальні символи в імені
        hryak_name = hryak['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

        text = f"""🐷 {hryak_name}

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів
🕐 Годування: {feed_status}

/feed - нагодувати (раз на 12 год)
/name - змінити ім'я"""

        bot.reply_to(message, text)
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

        text = "🏆 ТОП ХРЯКІВ ЧАТУ\n\n"
        emojis = ["🥇", "🥈", "🥉"]

        for i, hryak in enumerate(chat_hryaky[:top_count]):
            if i < 3:
                emoji = emojis[i]
            else:
                emoji = f"{i+1}."

            # Екрануємо спеціальні символи в імені
            name = hryak['name'][:20].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            text += f"{emoji} {name} - {hryak['weight']} кг\n"

        bot.reply_to(message, text)
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

    # Розраховуємо результат з урахуванням бонусів скінів
    result = calculate_duel_result(
        challenger_hryak, 
        opponent_hryak,
        user1_id=challenger_id,
        user2_id=opponent_id,
        chat_id=chat_id
    )

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

        # 🐰 ІВЕНТ: Великдень - перемога в дуелі = прогрес
        add_event_progress(winner_user_id, chat_id, 'easter', 1)
        check_event_random_drop(winner_user_id, chat_id, 'easter', 'дуелі хряків')

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

        # Перевіряємо виграш ЗАЛЕЖНО ВІД РЕЗУЛЬТАТУ
        if choice in ['red', 'black']:
            if result_color == choice:
                win = True
                win_amount = amount * 2
        elif choice in ['even', 'odd']:
            if result_number == 0:
                win = False  # 0 програш для парне/непарне
            elif (choice == 'even' and result_number % 2 == 0) or (choice == 'odd' and result_number % 2 == 1):
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
            if result_number == 0:
                win = False  # 0 програш для більше/менше
            elif (choice == 'over' and result_number > 7) or (choice == 'under' and result_number < 7):
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

        text = f"""🎰 РУЛЕТКА

Випало: {result_color.upper()} {result_number}
Твій вибір: {choice}
Ставка: {amount} кг
{result_text}

Нова вага: {hryak['weight']} кг"""

        bot.reply_to(message, text)
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

🐗 {hryak['name']} ({hryak['weight']} кг) створює к����������манду!

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
        
        # Додаємо до ко��������анди
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

        # Бонуси удачі від скінів (середній по команді)
        team1_luck = sum(get_skin_bonus(p['user_id'], chat_id, 'luck_bonus') + 
                        get_skin_bonus(p['user_id'], chat_id, 'all_bonus') 
                        for p in duel['team1']) / len(duel['team1'])
        team2_luck = sum(get_skin_bonus(p['user_id'], chat_id, 'luck_bonus') + 
                        get_skin_bonus(p['user_id'], chat_id, 'all_bonus') 
                        for p in duel['team2']) / len(duel['team2'])

        # Критичний удар (15% + бонус удачі, кожен % = +0.5% крита)
        team1_crit_chance = 0.15 + (team1_luck * 0.5 / 100)
        team2_crit_chance = 0.15 + (team2_luck * 0.5 / 100)
        
        team1_crit = random.random() < team1_crit_chance
        team2_crit = random.random() < team2_crit_chance
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
    """Показати головне inline меню з 3 категоріями"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("\U0001f437 Хряк та Рейтинг", callback_data="submenu_hryak"),
        types.InlineKeyboardButton("\u2694\ufe0f Битви та Гільдії", callback_data="submenu_battles"),
        types.InlineKeyboardButton("\U0001f3b0 Розваги та Економіка", callback_data="submenu_fun"),
        types.InlineKeyboardButton("\U0001f3af Підор", callback_data="menu_pidor"),
        types.InlineKeyboardButton("\U0001f525 Roast", callback_data="menu_roast"),
        types.InlineKeyboardButton("\U0001f52e Fortune", callback_data="menu_fortune"),
        types.InlineKeyboardButton("\u2b50 Оцінка", callback_data="menu_rate")
    )
    bot.reply_to(message, "\U0001f4cb **МЕНЮ КОМАНД**\n\nОбери категорію:", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('submenu_'))
def submenu_callback(call):
    """Обробка підменю"""
    submenu = call.data.split('_')[1]
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if submenu == 'hryak':
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("\U0001f437 Отримати", callback_data="menu_grow"),
            types.InlineKeyboardButton("\U0001f37d\ufe0f Годувати", callback_data="menu_feed"),
            types.InlineKeyboardButton("\U0001f4ca Мій", callback_data="menu_my"),
            types.InlineKeyboardButton("\u270f\ufe0f Ім'я", callback_data="menu_name"),
            types.InlineKeyboardButton("\U0001f3c6 Топ чату", callback_data="menu_top"),
            types.InlineKeyboardButton("\U0001f30d Глоб топ", callback_data="menu_globaltop"),
            types.InlineKeyboardButton("\U0001f3c5 Досягнення", callback_data="menu_achievements")
        )
        markup.add(types.InlineKeyboardButton("\u25c0\ufe0f Назад", callback_data="menu_back"))
        bot.edit_message_text("\U0001f437 **ХРЯК ТА РЕЙТИНГ**\n\nОбери дію:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif submenu == 'battles':
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("\u2694\ufe0f Дуель", callback_data="duel_create"),
            types.InlineKeyboardButton("\U0001f465 Командна", callback_data="menu_teambattle"),
            types.InlineKeyboardButton("\U0001f432 Бос", callback_data="menu_boss"),
            types.InlineKeyboardButton("\U0001f3f0 Гільдія", callback_data="menu_guild"),
            types.InlineKeyboardButton("\u2694\ufe0f Бос гільдії", callback_data="menu_guild_boss"),
            types.InlineKeyboardButton("\U0001f6e1\ufe0f Війни", callback_data="menu_guild_wars")
        )
        markup.add(types.InlineKeyboardButton("\u25c0\ufe0f Назад", callback_data="menu_back"))
        bot.edit_message_text("\u2694\ufe0f **БИТВИ ТА ГІЛЬДІЇ**\n\nОбери дію:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif submenu == 'fun':
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("\U0001f4b0 Баланс", callback_data="menu_balance"),
            types.InlineKeyboardButton("\U0001f4ca Статистика", callback_data="menu_mystats"),
            types.InlineKeyboardButton("\U0001f381 Daily", callback_data="menu_daily"),
            types.InlineKeyboardButton("\U0001f4cb Квести", callback_data="menu_quests"),
            types.InlineKeyboardButton("\U0001f3b0 Рулетка", callback_data="menu_roulette"),
            types.InlineKeyboardButton("\U0001f3af Лотерея", callback_data="menu_lottery"),
            types.InlineKeyboardButton("\U0001f3af Квіз", callback_data="menu_quiz"),
            types.InlineKeyboardButton("\U0001f3ea Магазин", callback_data="menu_shop"),
            types.InlineKeyboardButton("\U0001f392 Інвентар", callback_data="menu_inventory"),
            types.InlineKeyboardButton("\U0001f495 Трахен", callback_data="menu_trachen"),
            types.InlineKeyboardButton("\U0001f476 Діти", callback_data="menu_children"),
            types.InlineKeyboardButton("\U0001f3c6 Турнір", callback_data="menu_tournament"),
            types.InlineKeyboardButton("\U0001f4b1 Трейд", callback_data="menu_trade")
        )
        markup.add(types.InlineKeyboardButton("\u25c0\ufe0f Назад", callback_data="menu_back"))
        bot.edit_message_text("\U0001f3b0 **РОЗВАГИ ТА ЕКОНОМІКА**\n\nОбери дію:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif submenu == 'back':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("\U0001f437 Хряк та Рейтинг", callback_data="submenu_hryak"),
            types.InlineKeyboardButton("\u2694\ufe0f Битви та Гільдії", callback_data="submenu_battles"),
            types.InlineKeyboardButton("\U0001f3b0 Розваги та Економіка", callback_data="submenu_fun"),
            types.InlineKeyboardButton("\U0001f3af Підор", callback_data="menu_pidor"),
            types.InlineKeyboardButton("\U0001f525 Roast", callback_data="menu_roast"),
            types.InlineKeyboardButton("\U0001f52e Fortune", callback_data="menu_fortune"),
            types.InlineKeyboardButton("\u2b50 Оцінка", callback_data="menu_rate")
        )
        bot.edit_message_text("\U0001f4cb **МЕНЮ КОМАНД**\n\nОбери категорію:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)


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

                    # Add rewards
                    add_coins(user_id, chat_id, 5)
                    add_xp(user_id, chat_id, 2)

                    # Екрануємо спеціальні символи в імені хряка
                    hryak_name = escape_markdown(result['hryak']['name'])

                    text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів
💰 Нагорода: +5 монет, +2 XP

🐷 {hryak_name}"""
                    
                    # Update quests
                    quests = get_daily_quests(user_id, chat_id)
                    quest_progress = {q['quest_id']: q for q in quests}
                    feed_quest = quest_progress.get('feed_3_times', {'progress': 0, 'target': 3})
                    new_feed_progress = min(feed_quest['progress'] + 1, 3)
                    feed_completed = new_feed_progress >= 3
                    update_daily_quest(user_id, chat_id, 'feed_3_times', new_feed_progress, 3, completed=feed_completed)
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

                        # Add rewards
                        add_coins(user_id, chat_id, 5)
                        add_xp(user_id, chat_id, 2)

                        # Екрануємо спеціальні символи в імені хряка
                        hryak_name = escape_markdown(result['hryak']['name'])

                        text = f"""{emoji} {title}

Вага: {result['old_weight']} → {result['new_weight']} кг ({text_change})
Всього нагодовано: {result['feed_count']} разів
💰 Нагорода: +5 монет, +2 XP

🐷 {hryak_name}"""
                        
                        # Update quests
                        quests = get_daily_quests(user_id, chat_id)
                        quest_progress = {q['quest_id']: q for q in quests}
                        feed_quest = quest_progress.get('feed_3_times', {'progress': 0, 'target': 3})
                        new_feed_progress = min(feed_quest['progress'] + 1, 3)
                        feed_completed = new_feed_progress >= 3
                        update_daily_quest(user_id, chat_id, 'feed_3_times', new_feed_progress, 3, completed=feed_completed)
                    else:
                        text = "❌ Помилка годування!"
                else:
                    hours = int(time_left / 3600)
                    minutes = int((time_left % 3600) / 60)
                    # Екрануємо спеціальні символи в імені хряка
                    hryak_name = escape_markdown(hryak['name'])
                    text = f"⏳ **Ще рано!**\n\nЗалишилось: {hours} год {minutes} хв\n\n🐷 {hryak_name}"

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

            # Екрануємо спеціальні символи в імені хряка
            hryak_name = escape_markdown(hryak['name'])
            text = f"""🐷 **{hryak_name}**

⚖️ Вага: {hryak['weight']} кг
🏆 Максимальна: {hryak['max_weight']} кг
🍽️ Нагодовано: {hryak['feed_count']} разів
🕐 Годування: {feed_status}

/feed - нагодувати (раз на 12 год)
/name - змінити ім'я"""
    
    elif command == 'top':
        # Отримуємо хряків тільки з поточного чату
        chat_hryaky = []
        from db import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key FROM hryaky')
            rows = cursor.fetchall()
            for row in rows:
                key = row[0]
                hryak = get_hryak_from_db(key)
                if hryak and hryak.get('chat_id') == chat_id:
                    chat_hryaky.append(hryak)
            cursor.close()
            conn.close()

        chat_hryaky.sort(key=lambda x: x['weight'], reverse=True)
        top_hryaky = chat_hryaky[:5]

        if not top_hryaky:
            text = "📭 Ще немає хряків у цьому чаті!"
        else:
            text = "🏆 **ТОП ХРЯКІВ ЧАТУ**\n\n"
            for i, h in enumerate(top_hryaky):
                hryak_name = escape_markdown(h['name'])
                text += f"{i+1}. {hryak_name} - {h['weight']} кг\n"

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
                hryak_name = escape_markdown(h['name'])
                text += f"{i+1}. {hryak_name} - {h['weight']} кг\n"

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

    elif command == 'trade':
        text = "💱 **Трейд**\n\nНапиши /trade щоб створити трейд!"

    elif command == 'quiz':
        text = "🎯 **Квіз**\n\nНапиши /quiz щоб почати вікторину!"

    elif command == 'boss':
        text = "🐲 **Бос**\n\nНапиши /boss щоб побачити боса!"

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

    elif command == 'guild':
        text = "🏰 **ГІЛЬДІЯ**\n\n"
        text += "/guild_create <назва> - створити гільдію\n"
        text += "/guild_join <назва> - приєднатися\n"
        text += "/guild_info - інформація\n"
        text += "/guild_members - учасники\n"
        text += "/guild_spawn <ім'я> <рівень> - спавн боса\n"
        text += "/guild_attack - атакувати боса\n"
        text += "/guild_warriors - воїни гільдії\n"
        text += "/guild_territories - території"

    elif command == 'guild_boss':
        text = "⚔️ **БОС ГІЛЬДІЇ**\n\n"
        text += "/guild_boss_spawn <ім'я> <рівень> - спавнити боса\n"
        text += "/guild_boss_attack - атакувати боса\n"
        text += "/guild_boss_info - статус боса"

    elif command == 'guild_wars':
        text = "🛡️ **ВІЙНИ ГІЛЬДІЙ**\n\n"
        text += "/guild_war_declare <гільдія> - оголосити війну\n"
        text += "/guild_war_join - приєднатися до війни\n"
        text += "/guild_war_battle - битися (щодня)\n"
        text += "/guild_war_status - статус воєн"

    elif command == 'back':
        # Повернутися до головного меню
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🐷 Хряк та Рейтинг", callback_data="submenu_hryak"),
            types.InlineKeyboardButton("⚔️ Битви та Гільдії", callback_data="submenu_battles"),
            types.InlineKeyboardButton("🎰 Розваги та Економіка", callback_data="submenu_fun"),
            types.InlineKeyboardButton("🎯 Підор", callback_data="menu_pidor"),
            types.InlineKeyboardButton("🔥 Roast", callback_data="menu_roast"),
            types.InlineKeyboardButton("🔮 Fortune", callback_data="menu_fortune"),
            types.InlineKeyboardButton("⭐ Оцінка", callback_data="menu_rate")
        )
        bot.edit_message_text("📋 **МЕНЮ КОМАНД**\n\nОбери категорію:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        return  # Не надсилаємо текст нижче

    else:
        text = "❌ Невідома команда"

    # Відправляємо повідомлення
    bot.send_message(chat_id, text, parse_mode="Markdown")


def is_chat_admin(chat_id, user_id):
    """Перевіряє чи користувач є адміном чату"""
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


def fetch_all_chat_members(message, progress_callback=None):
    """
    Автоматично додає всіх учасників чату в кеш.
    Отримує адміністраторів та зберігає їхні user_id.
    
    Args:
        message: повідомлення з чату
        progress_callback: функція для відображення прогресу (optional)
    
    Returns:
        list: список всіх учасників
    """
    chat_id = message.chat.id
    chat_title = message.chat.title
    
    users = set()
    user_ids = {}  # Додатково зберігаємо user_id для адміністраторів
    
    try:
        # Отримуємо адміністраторів - це єдині кого можемо отримати через API
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            user = admin.user
            if not user.is_bot:
                if user.username:
                    username = f"@{user.username}"
                    users.add(username)
                    user_ids[username.lower()] = user.id  # Зберігаємо user_id
                else:
                    username = f"{user.first_name}"
                    users.add(username)
        
        # Додаємо стандартних юзернеймів
        for u in DEFAULT_USERS:
            users.add(u)
        
        # Додаємо ручних юзернеймів
        if chat_id in manual_users:
            for u in manual_users[chat_id]:
                users.add(u)
        
        # Додаємо того хто написав команду
        current_user = message.from_user
        if not current_user.is_bot:
            current_name = f"@{current_user.username}" if current_user.username else current_user.first_name
            users.add(current_name)
            if current_user.username:
                user_ids[f"@{current_user.username}".lower()] = current_user.id
        
        # Зберігаємо в кеш
        users_list = list(users)
        chat_members_cache[chat_id] = users_list
        
        # Зберігаємо user_id в окремий кеш для швидкого доступу
        if chat_id not in chat_member_ids:
            chat_member_ids[chat_id] = {}
        chat_member_ids[chat_id].update(user_ids)
        
        print(f"✅ Завантажено {len(users_list)} учасників для чату {chat_title}")
        print(f"   Збережено {len(user_ids)} user_id: {list(user_ids.items())[:5]}...")
        return users_list
        
    except Exception as e:
        print(f"❌ Помилка отримання учасників: {e}")
        return list(users) if users else ["@default_user"]


@bot.message_handler(commands=['fetch_all_members'])
def fetch_all_members_cmd(message):
    """
    Команда для автоматичного додавання всіх учасників чату.
    Доступна тільки адмінам.
    """
    # Перевірка адміна
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title
    
    # Надсилаємо повідомлення про початок процесу
    status_msg = bot.reply_to(message, f"⏳ Завантажую учасників чату '{chat_title}'...\n\nЦе може зайняти деякий час.")
    
    try:
        # Отримуємо всіх учасників
        users = fetch_all_chat_members(message)
        
        # Оновлюємо повідомлення з результатом
        bot.edit_message_text(
            f"✅ Учасників завантажено!\n\n"
            f"Чат: {chat_title}\n"
            f"Всього учасників: {len(users)}\n\n"
            f"📋 Перші 20 учасників:\n" + 
            "\n".join(f"  • {u}" for u in users[:20]) +
            (f"\n  ... і ще {len(users) - 20}" if len(users) > 20 else ""),
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ Помилка завантаження учасників: {e}",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )


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
    "ти знаєш що це нічого не змінить?",
]

# Команда /top
TOP_CATEGORIES = [
    "найбільший підор",
    "найбільший гей",
    "найбільший лох",
    "найбільший бич",
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
    # Отримуємо URL з змінних середовища
    commands_url = os.environ.get('COMMANDS_URL', 'https://trashbot-commands.onrender.com')
    
    text = f"""📜 **ПОВНИЙ СПИСОК КОМАНД:**

🎯 Меню:
/guild_menu /warriors_menu /items_menu /genetics_menu /trade_menu

🐷 Хряки:
/grow /feed /my /name /duel /achievements

💰 Економіка:
/balance /shop /daily /inventory

🎰 Казино:
/roulette /lottery /casino_create /casino_play

🎓 Квіз:
/quiz /quizstats

👥 Чат:
/members /userinfo <ID>

💕 Генетика:
/breed /genes /children /childbonus

🏰 Гільдії:
/createguild /guild /guildjoin /guildtop
/contribute /promote /demote

⚔️ Війни:
/guild_territories /guild_capture /guild_income
/guild_warriors /guild_buy_warrior /guild_defend
/guild_attack /guild_defense_info
/guild_war_declare /guild_war_battle /guild_war_status
/guild_boss_spawn /guild_boss_attack

🎒 Предмети:
/inventory /use_item /guild_items /guild_claim_item
/item_trade /item_trades /item_accept /item_cancel

🏆 Турніри:
/tournament create /join /start

🎨 Скіни:
/skins /buyskin /equipskin

🐲 Боси:
/boss /boss attack /boss info

⚙️ Інше:
/start /menu /help

📁 **Повні інструкції онлайн:**
{commands_url}

**Всі команди з підкресленнями (_)!**"""
    
    # Створюємо inline кнопку
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📋 Відкрити всі команди",
        url=commands_url
    ))
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=['members'])
def show_members(message):
    """Показати всіх учасників чату"""
    users = get_chat_members(message)
    if len(users) <= 20:
        text = "👥 Учасники чату:\n" + "\n".join(users)
    else:
        text = f"👥 Учасники чату ({len(users)} осіб):\n" + "\n".join(users[:20]) + f"\n... і ще {len(users) - 20}"
    bot.reply_to(message, text)


@bot.message_handler(commands=['userinfo'])
def userinfo_cmd(message):
    """Отримати інформацію про користувача за ID"""
    global stats_data, chat_members_cache

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """ℹ️ **ІНФОРМАЦІЯ ПРО КОРИСТУВАЧА**

Використання: /userinfo <ID>

Де знайти ID:
1. /members - показати всіх учасників
2. Знайти ID потрібного користувача
3. /userinfo <ID> - отримати інформацію

Приклад: /userinfo 123456789""")
            return

        user_id = int(parts[1])
        chat_id = message.chat.id

        # Шукаємо користувача в статистиці
        user_info = None
        for key, data in stats_data.items():
            # Перевіряємо чи це словник
            if isinstance(data, dict):
                if data.get('user_id') == user_id and data.get('chat_id') == chat_id:
                    user_info = data
                    break

        if not user_info:
            # Шукаємо в кеші учасників
            if chat_id in chat_members_cache:
                for member in chat_members_cache[chat_id]:
                    if isinstance(member, dict) and member.get('user_id') == user_id:
                        user_info = member
                        break

        if not user_info:
            bot.reply_to(message, f"❌ Користувача з ID {user_id} не знайдено в цьому чаті!")
            return

        username = user_info.get('username', 'Немає')
        first_name = user_info.get('first_name', user_info.get('username', 'Невідомо'))
        count = user_info.get('count', 0)
        first_message = user_info.get('first_message', 0)

        # Форматуємо дату
        if first_message and first_message > 0:
            first_msg_date = time.strftime('%d.%m.%Y %H:%M', time.localtime(first_message))
        else:
            first_msg_date = 'Невідомо'

        text = f"""👤 **ІНФОРМАЦІЯ ПРО КОРИСТУВАЧА**

**ID:** `{user_id}`
**Юзернейм:** {username if username != 'Немає' else 'Не вказано'}
**Ім'я:** {first_name}

**Статистика в чаті:**
📝 Повідомлень: {count}
📅 Перше повідомлення: {first_msg_date}

**Команди:**
/userinfo <ID> - інформація про користувача
/members - список усіх учасників"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except ValueError:
        bot.reply_to(message, "❌ Невірний формат ID! ID має бути числом.")
    except Exception as e:
        logger.error(f"❌ Помилка /userinfo: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['id'])
def get_id_cmd(message):
    """Отримати ID користувача"""
    try:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        # Якщо є reply - показуємо ID іншого користувача
        if message.reply_to_message:
            reply_user = message.reply_to_message.from_user
            reply_id = reply_user.id
            reply_username = f"@{reply_user.username}" if reply_user.username else reply_user.first_name
            
            text = f"""🆔 ID КОРИСТУВАЧІВ

**Ваш ID:**
ID: `{user_id}`
Юзернейм: {username}

**ID користувача з reply:**
ID: `{reply_id}`
Юзернейм: {reply_username}

**Команди:**
/id - дізнатися свій ID
/id (у відповідь) - дізнатися ID іншого"""
        else:
            text = f"""🆔 ВАШ ID

**ID:** `{user_id}`
**Юзернейм:** {username}

**Команди:**
/id - дізнатися свій ID
/id (у відповідь) - дізнатися ID іншого
/userinfo <ID> - інформація про користувача"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /id: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['clearcache'])
def clear_cache(message):
    """Очистити кеш учасників і завантажити наново"""
    chat_id = message.chat.id
    if chat_id in chat_members_cache:
        del chat_members_cache[chat_id]
        if chat_id in chat_member_ids:
            del chat_member_ids[chat_id]
        bot.reply_to(message, "✅ Кеш учасників очищено! Тепер я завантажу новий список.")
    else:
        bot.reply_to(message, "✅ Кеш і так чистий. Завантажую свіжий список учасників...")

    # Завантажуємо всіх учасників автоматично
    try:
        fetch_all_chat_members(message)
        print(f"✅ Оновлено кеш учасників для чату {chat_id}")
    except Exception as e:
        print(f"❌ Помилка завантаження учасників: {e}")


@bot.message_handler(commands=['debug_cache'])
def debug_cache_cmd(message):
    """Показати вміст кешу для діагностики (адмін)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
        return
    
    chat_id = message.chat.id
    
    text = f"🔍 **Кеш для чату {chat_id}**:\n\n"
    
    # Показуємо chat_members_cache
    if chat_id in chat_members_cache:
        members = chat_members_cache[chat_id]
        text += f"👥 Учасники ({len(members)}):\n"
        for m in members[:10]:
            text += f"  • {m}\n"
        if len(members) > 10:
            text += f"  ... і ще {len(members) - 10}\n"
    else:
        text += "❌ Учасники не завантажені\n"
    
    text += "\n"
    
    # Показуємо chat_member_ids
    if chat_id in chat_member_ids:
        ids = chat_member_ids[chat_id]
        text += f"🆔 User IDs ({len(ids)}):\n"
        for username, uid in list(ids.items())[:10]:
            text += f"  • {username}: `{uid}`\n"
        if len(ids) > 10:
            text += f"  ... і ще {len(ids) - 10}\n"
    else:
        text += "❌ User IDs не збережені\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")


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

        # Завантажуємо всіх учасників автоматично
        try:
            fetch_all_chat_members(message)
            print(f"✅ Автоматично завантажено учасників для чату {chat_id}")
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
/members — показати у��асників
/adduser — додати юзернейма
/removeuser — видалити юзернейма

🔇 **Мут (адміни):**
/mute — замути на X хв (/mute 10)
/unmute — розмутити

😈 **Провина (адміни):**
/provin — дати провину (/provin 10)
/unprovin — зняти провину

⚠️ **попередження (адміни):**
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
            # При покупці бонуси не застосовуються
            add_coins(user_id, chat_id, -item['price'], apply_skin_bonus=False)
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
        # Отримуємо предмети з обох систем
        inventory = get_user_inventory(user_id, chat_id)  # Shop items
        user_items = get_user_items(user_id, chat_id)  # Loot/traded items
        items = get_shop_items()
        items_dict = {i['item_id']: i for i in items}

        # Get user's skins
        skins = get_user_skins(user_id, chat_id)

        if not inventory and not user_items and not skins:
            bot.reply_to(message, "🎒 ІНВЕНТАР\n\nПорожньо!")
            return

        text = "🎒 *ІНВЕНТАР*\n\n"

        # Show user_items (loot/traded items)
        if user_items:
            text += "\\*Предмети:\\*\n"
            rarity_emojis = {'mythic': '🔴', 'legendary': '🟡', 'epic': '🟣', 'rare': '🔵', 'common': '⚪'}
            type_names = {'weapon': 'Зброя', 'armor': 'Броня', 'accessory': 'Аксесуар', 'consumable': 'Споживне', 'special': 'Особливе', 'item': 'Предмет'}

            for item in user_items[:20]:
                rarity_emoji = rarity_emojis.get(item['rarity'], '⚪')
                type_name = type_names.get(item['item_type'], 'Предмет')
                item_name_safe = escape_markdown(item['item_name'])
                type_name_safe = escape_markdown(type_name)

                text += "{} \\*{}\\* \\({}\\) x{}\n".format(rarity_emoji, item_name_safe, type_name_safe, item['quantity'])
                if item.get('bonus_type'):
                    bonus_text = "+{} {}".format(item['bonus_value'], item['bonus_type'])
                    text += "   {}\n".format(escape_markdown(bonus_text))
            text += "\n"

        # Show shop items
        if inventory:
            text += "\\*Предмети з магазину:\\*\n"
            for inv_item in inventory:
                item = items_dict.get(inv_item['item_id'])
                if item:
                    text += "\\- {} x{}\n".format(escape_markdown(item['name']), inv_item['quantity'])
                    if inv_item['expires_at']:
                        expires = inv_item['expires_at'] - int(time.time())
                        hours = expires // 3600
                        text += "  \\(Ще {} год\\)\n".format(hours)
                    text += "\n"

        # Show skins
        if skins:
            text += "\\*Скіни:\\*\n"
            for skin in skins:
                equipped = "\\(Одягнуто\\)" if skin['equipped'] else ""
                display_name = escape_markdown(skin['display_name'])
                skin_name_safe = escape_markdown(skin['name'])
                text += "{} {} {} \\/{}\n".format(skin['icon'], display_name, equipped, skin_name_safe)
            text += "\n"

        text += "\\*Команди:\\*\n"
        text += "/use \\<item_id\\> \\- використати предмет\n"
        text += "/equipskin \\<назва\\> \\- одягнути скін\n"
        text += "/item_trade \\<предмет\\> \\<кількість\\> \\- трейд предметом\n\n"
        text += "Приклад: `/equipskin classic`"

        bot.reply_to(message, text, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"❌ Помилка /inventory: {e}", exc_info=True)
        bot.reply_to(message, "❌ Помилка: {}".format(escape_markdown(str(e))), parse_mode="MarkdownV2")


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
            # Перевіряємо також user_items (предмети з трейдів)
            user_items = get_user_items(user_id, chat_id)
            has_in_user_items = any(item['item_name'].lower() == item_id.lower() and item['quantity'] > 0 for item in user_items)
            if not has_in_user_items:
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
                hryak['weight'] += item['effect_value']
                save_hryak_to_db(user_id, chat_id, hryak)
                text = f"🍎 **Вітаміни використано!**\n\nВага збільшена на +{item['effect_value']} кг!"
            else:
                text = "❌ У тебе немає хряка!"
        elif item_id == 'spermobak':
            # Зняти кулдаун з трахену/breed
            from db import get_connection
            import time as time_module
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                old_time = int(time_module.time()) - 86400
                cursor.execute('''
                    UPDATE trachenzebiten
                    SET created_at = %s
                    WHERE user_id = %s AND chat_id = %s
                    AND id = (
                        SELECT id FROM trachenzebiten
                        WHERE user_id = %s AND chat_id = %s
                        ORDER BY id DESC LIMIT 1
                    )
                ''', (old_time, user_id, chat_id, user_id, chat_id))
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                if affected > 0:
                    text = f"🧪 **{item['name']} використано!**\n\nТепер можна /trachen та /breed!"
                else:
                    text = f"🧪 **{item['name']} використано!**\n\nНемає активного кулдауну."
            else:
                text = "❌ Помилка БД!"
        elif item_id == 'pastors_milk':
            # Зняти кулдаун з тренування дітей
            from db import get_connection
            import time as time_module
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                old_time = int(time_module.time()) - 86400
                cursor.execute('''
                    UPDATE hryak_genes
                    SET last_train = %s
                    WHERE user_id = %s
                ''', (old_time, user_id))
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                if affected > 0:
                    text = f"🥛 **{item['name']} використано!**\n\nТепер можна тренувати дітей!"
                else:
                    text = f"🥛 **{item['name']} використано!**\n\nНемає активного кулдауну."
            else:
                text = "❌ Помилка БД!"
        else:
            text = f"✅ **{item['name']} використано!**\n\nЕфект: {item['description']}"

        # Видаляємо предмет
        # Видаляємо предмет з тієї системи де він був
        if has_item(user_id, chat_id, item_id):
            remove_from_inventory(user_id, chat_id, item_id, 1)
        else:
            remove_user_item(user_id, chat_id, item_id, 1, item_type='item')
        
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
        
        # Get equipped skin
        equipped_skin = get_user_equipped_skin(user_id, chat_id)
        skin_text = equipped_skin['display_name'] if equipped_skin else "Немає"
        
        # Calculate level bonuses
        level = currency['level'] if currency else 1
        level_bonus_coins = (level - 1) * 5  # +5% монет за рівень
        level_bonus_xp = (level - 1) * 2  # +2% XP за рівень
        level_bonus_power = (level - 1) * 1  # +1% сили за рівень

        text = """📊 ТВОЯ СТАТИСТИКА

💰 Економіка:
  Монети: {}
  XP: {}/{}
  Рівень: {} (+{}% монет, +{}% XP, +{}% сили)

⚔️ Дуелі:
  Перемог: {}
  Поразок: {}
  Всього ігор: {}

📋 Квести:
  Виконано: {}

🎰 Казино:
  Виграшів: {}
  Програшів: {}

💕 Трахензебітен:
  Разів: {}
  Унікальних партнерів: {}
  Зміна ваги: {} кг

🏆 Турніри:
  Участь: {}
  Перемоги: {}

🏰 Гільдії:
  Внесок: {}
  Гільдія: {}

🐲 Бос-дуелі:
  Битв: {}
  Всього шкоди: {}
  Вбито босів: {}

🎨 Скін: {}

🐷 Хряк:""".format(
            currency['coins'] if currency else 0,
            currency['xp'] if currency else 0,
            100,
            currency['level'] if currency else 1,
            level_bonus_coins,
            level_bonus_xp,
            level_bonus_power,
            stats['duels_won'],
            stats['duels_lost'],
            stats['duels_won'] + stats['duels_lost'],
            stats['quests_completed'],
            stats['casino_wins'],
            stats['casino_losses'],
            trachen_stats['total_times'] if trachen_stats else 0,
            trachen_stats['unique_partners'] if trachen_stats else 0,
            trachen_stats['total_weight_change'] if trachen_stats else 0,
            tournament_stats['tournaments_joined'] if tournament_stats else 0,
            tournament_stats['tournaments_won'] if tournament_stats else 0,
            guild_stats['total_contribution'] if guild_stats else 0,
            user_guild['name'] if user_guild else "Немає",
            boss_stats['bosses_fought'] if boss_stats else 0,
            boss_stats['total_damage'] if boss_stats else 0,
            boss_stats['bosses_defeated'] if boss_stats else 0,
            skin_text
        )

        if hryak:
            text += """
  Ім'я: {}
  Вага: {} кг
  Нагодовано: {} разів
  Набрано всього: {} кг""".format(
                hryak['name'],
                hryak['weight'],
                hryak['feed_count'],
                stats['total_weight_gained']
            )
        else:
            text += "\n  Немає хряка! Введи /grow"

        bot.reply_to(message, text)
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

        text = """💰 **БАЛАНС**

💵 Монети: {}
⭐ XP: {}/100
🏆 Рівень: {}

**Як отримати:**
• /feed - +5 монет, +2 XP
• /quests - до 50 монет, 12 XP
• /boss attack - до 500 монет, 250 XP
• /roulette - ризикни!
• /lottery - спробуй удачу!
• /daily - щоденний бонус""".format(
            currency['coins'],
            currency['xp'],
            currency['level']
        )

        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ Помилка /balance: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['convert'])
def convert_cmd(message):
    """Конвертувати ігрові монети в CRYPTO"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, f"""💱 **КОНВЕРТАЦІЯ**

Використання: /convert <сума>

Приклад: /convert 10000

**Інформація:**
Курс: {CONVERSION_RATE} монет = 1 CRYPTO
Мінімум: {MIN_CONVERT} монет ({MIN_CONVERT // CONVERSION_RATE} CRYPTO)
Ліміт: {MAX_DAILY_WITHDRAW} монет/день

Твій баланс: /balance""")
            return
        
        try:
            amount = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Сума має бути числом!")
            return
        
        if amount < MIN_CONVERT:
            bot.reply_to(message, f"❌ Мінімум для конвертації: {MIN_CONVERT} монет ({MIN_CONVERT // CONVERSION_RATE} CRYPTO)")
            return
        
        # Конвертуємо
        result = convert_game_to_crypto(user_id, chat_id, amount)
        
        if result['success']:
            bot.reply_to(message, f"""✅ **КОНВЕРТАЦІЯ УСПІШНА!**

Списано: {result['game_coins_deducted']} монет
Отримано: {result['crypto_received']} CRYPTO
Новий баланс: {result['new_crypto_balance']} CRYPTO

Contract: `kQDlcflos1dKSPfhw17NoyUvwPrI_V-mLFG3wr3Xn2zPk0Yq`
Blockchain: TON Testnet""")
        else:
            bot.reply_to(message, f"❌ {result['message']}")
    except Exception as e:
        logger.error(f"❌ Помилка /convert: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['crypto'])
def crypto_cmd(message):
    """Інформація про крипто-монету"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        crypto_info = get_conversion_info(user_id, chat_id)
        
        if not crypto_info:
            bot.reply_to(message, "❌ Помилка отримання інформації!")
            return
        
        text = f"""🪙 **CRYPTO (TON Testnet)**

**Твій прогрес:**
💰 Ігрові монети: {crypto_info['game_coins']}
🪙 Crypto баланс: {crypto_info['crypto_coins']} CRYPTO
📊 Всього конвертовано: {crypto_info['total_converted']} монет

**Інформація про токен:**
Blockchain: TON Testnet
Contract: `kQDlcflos1dKSPfhw17NoyUvwPrI_V-mLFG3wr3Xn2zPk0Yq`
Supply: 1,000,000 CRYPTO
Decimals: 9

**Конвертація:**
Курс: {CONVERSION_RATE} монет = 1 CRYPTO
Мінімум: {MIN_CONVERT} монет
Ліміт: {MAX_DAILY_WITHDRAW} монет/день

**Команди:**
/convert <сума> - конвертувати монети
/balance - показати баланс

⚠️ **Увага:** Це тестова монета на TON Testnet!"""

        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ Помилка /crypto: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['resetdb'])
def reset_db_cmd(message):
    """Скинути базу даних (ТІЛЬКИ для адмінів чату!)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Перевірка чи це адмін чату
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Ця команда тільки для адмінів чату!")
        return

    try:
        # Перевірка чи дійсно хоче скинути
        parts = message.text.split()
        if len(parts) < 2 or parts[1] != 'CONFIRM':
            bot.reply_to(message, """⚠️ **УВАГА!**

Це видалить ВСІ дані в цьому чаті:
- Хряків
- Монети
- XP
- Гільдії
- Турніри
- Транзакції

Для підтвердження напишіть:
`/resetdb CONFIRM`

⚠️ Цю дію неможливо скасувати!""", parse_mode="Markdown")
            return

        # Скидання БД (тільки якщо CONFIRM)
        from db import init_db
        init_db()

        bot.reply_to(message, "✅ Базу даних скинуто! Всі дані видалено.\n\n⚠️ Перезапустіть бота для застосування змін.")
    except Exception as e:
        logger.error(f"❌ Помилка /resetdb: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['cleanevents'])
def clean_events_cmd(message):
    """Очистити дублікати івентів (адмін команда)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Перевіряємо чи адмін (тільки для власника)
        if user_id != message.from_user.id:  # Завжди true, можна змінити на перевірку по ID
            bot.reply_to(message, "❌ Ця команда доступна тільки власнику бота!")
            return

        deleted = cleanup_duplicate_events()

        if deleted:
            bot.reply_to(message, "✅ Дублікати івентів видалено!")
        else:
            bot.reply_to(message, "❌ Помилка видалення дублікатів або їх немає!")
    except Exception as e:
        logger.error(f"❌ Помилка /cleanevents: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['dbstatus'])
def db_status_cmd(message):
    """Перевірити статус бази даних"""
    try:
        from db import get_connection

        conn = get_connection()
        if not conn:
            bot.reply_to(message, "❌ Помилка підключення до БД!")
            return
        
        cursor = conn.cursor()

        # Перевірка кількості записів в таблицях
        tables = {
            'hryaky': 'Хряки',
            'user_currencies': 'Баланси',
            'guilds': 'Гільдії',
            'seasonal_events': 'Івенти'
        }

        text = "📊 **Статус бази даних:**\n\n"

        for table, name in tables.items():
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            text += f"{name}: {count} записів\n"

        cursor.close()
        conn.close()

        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ Помилка /dbstatus: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['trade'])
def trade_cmd(message):
    """Створити трейд з іншим гравцем"""
    chat_id = message.chat.id
    sender_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 3:
            bot.reply_to(message, """💱 ТРЕЙД

Використання: /trade @username <сума>

Приклад: /trade @skyfidon79 100

Команди:
/trade @username <сума> - створити трейд
/trades - показати активні трейди
/accept <id> - прийняти трейд
/cancel <id> - скасувати трейд""")
            return

        # Отримуємо отримувача
        receiver_username = parts[1].lower()  # Normalize username
        if not receiver_username.startswith('@'):
            bot.reply_to(message, "❌ Username має починатися з @")
            return

        try:
            amount = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ Сума має бути числом!")
            return

        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return

        # Перевіряємо баланс
        currency = get_user_currency(sender_id, chat_id)
        if currency['coins'] < amount:
            bot.reply_to(message, f"❌ Недостатньо монет! У тебе: {currency['coins']}")
            return

        # DEBUG: Логуємо пошук користувача
        print(f"🔍 Пошук користувача {receiver_username} в чаті {chat_id}")
        print(f"   chat_members_cache: {chat_id in chat_members_cache}")
        print(f"   chat_member_ids: {chat_id in chat_member_ids}")
        if chat_id in chat_member_ids:
            print(f"   Доступні user_id: {list(chat_member_ids[chat_id].keys())}")

        # Знаходимо отримувача по username в статистиці
        receiver_id = None

        # Спочатку шукаємо в stats_data
        for key, data in stats_data.items():
            if data.get('username', '').lower() == receiver_username and data.get('chat_id') == chat_id:
                receiver_id = data.get('user_id')
                break

        # Якщо не знайшли в stats_data, шукаємо в chat_member_ids (зберігається при fetch_all_members)
        if not receiver_id and chat_id in chat_member_ids:
            receiver_id = chat_member_ids[chat_id].get(receiver_username)
            if receiver_id:
                print(f"✅ Знайдено користувача {receiver_username} в chat_member_ids, ID: {receiver_id}")

        # Якщо не знайшли, шукаємо в chat_members_cache і тоді в stats_data
        if not receiver_id and chat_id in chat_members_cache:
            for member in chat_members_cache[chat_id]:
                member_username = f"{member}".lower()
                if member_username == receiver_username:
                    # Отримуємо user_id з stats_data по username
                    for key, data in stats_data.items():
                        if data.get('username', '').lower() == member_username:
                            receiver_id = data.get('user_id')
                            break
                    if receiver_id:
                        break

        # Якщо все ще не знайшли, пробуємо знайти серед адміністраторів (тільки для них працює)
        if not receiver_id:
            try:
                admins = bot.get_chat_administrators(chat_id)
                for admin in admins:
                    user = admin.user
                    admin_username = f"@{user.username}".lower() if user.username else None
                    if admin_username == receiver_username:
                        receiver_id = user.id
                        print(f"✅ Знайдено адміна {receiver_username} через API, ID: {receiver_id}")
                        # Зберігаємо в кеш для майбутнього
                        if chat_id not in chat_member_ids:
                            chat_member_ids[chat_id] = {}
                        chat_member_ids[chat_id][receiver_username] = receiver_id
                        break
            except Exception as e:
                print(f"⚠️ Не вдалося знайти користувача {receiver_username} серед адміністраторів: {e}")

        # Якщо все ще не знайшли, шукаємо в manual_users
        if not receiver_id:
            manual_key = f"{chat_id}"
            if manual_key in manual_users:
                for username, uid in manual_users[manual_key].items():
                    if username.lower() == receiver_username:
                        receiver_id = uid
                        break

        if not receiver_id:
            bot.reply_to(message, f"""❌ Користувач {receiver_username} не знайдений в чаті!

**Можливі причини:**
• Користувач ще не писав в чат
• Бот не бачить цього користувача

**Рішення:**
1. Нехай користувач напише повідомлення
2. Додайте бота в друзі
3. Спробуйте /members щоб побачити список""")
            return

        if receiver_id == sender_id:
            bot.reply_to(message, "❌ Не можна торгувати з самим собою!")
            return

        bot.reply_to(message, f"""💱 ТРЕЙД СТВОРЕНО!

Отримувач: {receiver_username}
Сума: {amount} монет

{receiver_username} має написати /accept <id> щоб прийняти трейд.

⏰ Трейд дійсний 24 години.""")

        # Створюємо трейд з правильним receiver_id
        trade_id = create_trade(sender_id, receiver_id, chat_id, amount)

        if trade_id:
            bot.reply_to(message, f"ID трейду: `{trade_id}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Помилка створення трейду!")
    except Exception as e:
        logger.error(f"❌ Помилка /trade: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['trades'])
def trades_cmd(message):
    """Показати активні трейди"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Отримуємо звичайні трейди (монетами)
        from db import get_pending_trades as get_pending_coin_trades
        trades = get_pending_coin_trades(user_id, chat_id)

        if not trades:
            bot.reply_to(message, "📭 Немає активних трейдів!")
            return

        text = "💱 **Активні трейди:**\n\n"

        for trade in trades:
            text += f"ID: `{trade['id']}`\n"
            text += f"Від: ID {trade['sender_id']}\n"
            text += f"Сума: {trade['coins_offered']} монет\n\n"

        text += "Використовуй /accept <id> щоб прийняти"

        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /trades: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['accept'])
def accept_trade_cmd(message):
    """Прийняти трейд"""
    chat_id = message.chat.id
    receiver_id = message.from_user.id

    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /accept <trade_id>")
            return
        
        try:
            trade_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ ID має бути числом!")
            return
        
        # Отримуємо трейд
        trades = get_pending_trades(receiver_id, chat_id)
        trade = next((t for t in trades if t['id'] == trade_id), None)
        
        if not trade:
            bot.reply_to(message, "❌ Трейд не знайдено!")
            return
        
        # Приймаємо трейд
        if accept_trade(trade_id, trade['sender_id'], receiver_id, chat_id):
            bot.reply_to(message, f"""✅ **ТРЕЙД ПРИЙНЯТО!**

Отримано: {trade['coins_offered']} монет
Від: ID {trade['sender_id']}""")
            
            # 🐰 ІВЕНТ: Великдень - прийняття трейду = прогрес
            add_event_progress(receiver_id, chat_id, 'easter', 2)
            check_event_random_drop(receiver_id, chat_id, 'easter', 'трейду')
        else:
            bot.reply_to(message, "❌ Помилка прийняття трейду! Перевірте баланс.")
    except Exception as e:
        logger.error(f"❌ Помилка /accept: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['cancel'])
def cancel_trade_cmd(message):
    """Скасувати трейд"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /cancel <trade_id>")
            return
        
        try:
            trade_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ ID має бути числом!")
            return
        
        # Скасовуємо трейд
        if cancel_trade(trade_id):
            bot.reply_to(message, "✅ Трейд скасовано!")
        else:
            bot.reply_to(message, "❌ Помилка скасування трейду!")
    except Exception as e:
        logger.error(f"❌ Помилка /cancel: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# КВІЗ - УКРАЇНСЬКА ВІКТОРИНА
# ============================================

@bot.message_handler(commands=['quiz'])
def quiz_cmd(message):
    """Почати квіз"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Перевіряємо скільки вже відповів сьогодні
        progress = get_user_quiz_progress(user_id, chat_id)
        today_count = len(progress)
        
        if today_count >= 10:
            bot.reply_to(message, """🎯 **КВІЗ**

Ти вже відповів на 10 питань сьогодні!
Повертайся завтра за новими питаннями.

📊 Статистика: /quizstats""")
            return
        
        # Знаходимо питання на які ще не відповідав ВЗАГАЛІ
        answered_ids = [p['question_id'] for p in progress]
        
        # Фільтруємо питання - беремо тільки ті на які не відповідав
        available_questions = []
        for i, q in enumerate(QUIZ_QUESTIONS):
            if i not in answered_ids:
                available_questions.append((i, q))
        
        if not available_questions:
            bot.reply_to(message, """🎯 **КВІЗ**

Ти відповів на ВСІ питання!
Чекай на оновлення бази питань.

📊 Статистика: /quizstats""")
            return
        
        # Обираємо випадкове питання з тих на які не відповідав
        import random
        question_id, question = random.choice(available_questions)

        # Створюємо клавіатуру
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i, option in enumerate(question['options']):
            # Додаємо user_id до callback_data для перевірки хто відповідає
            markup.add(types.InlineKeyboardButton(
                f"{i+1}. {option}",
                callback_data=f"quiz_{user_id}_{question_id}_{i}"
            ))

        text = f"""🎯 **КВІЗ - Питання #{today_count + 1}/10**

{question['question']}

Обери правильну відповідь:"""
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /quiz: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_'))
def quiz_callback(call):
    """Обробка відповіді на квіз"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    try:
        # Парсимо дані
        parts = call.data.split('_')
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Помилка формату питання!", show_alert=True)
            return
        
        quiz_user_id = int(parts[1])  # Хто отримав питання
        question_id = int(parts[2])
        answer_id = int(parts[3])

        # Перевіряємо чи це той самий користувач який отримав питання
        if quiz_user_id != user_id:
            bot.answer_callback_query(call.id, "❌ Це не твоє питання! Створи своє /quiz", show_alert=True)
            return

        # Перевіряємо скільки вже відповів сьогодні
        progress = get_user_quiz_progress(user_id, chat_id)
        today_count = len(progress)

        if today_count >= 10:
            bot.answer_callback_query(call.id, "❌ Ти вже відповів на 10 питань сьогодні!", show_alert=True)
            return

        # Перевіряємо чи вже відповідав на це питання
        answered_ids = [p['question_id'] for p in progress]
        if question_id in answered_ids:
            bot.answer_callback_query(call.id, "❌ Ти вже відповідав на це питання!", show_alert=True)
            return

        question = QUIZ_QUESTIONS[question_id]
        is_correct = (answer_id == question['correct'])

        # Записуємо відповідь
        record_quiz_answer(user_id, chat_id, question_id, is_correct)

        # Нагорода за правильну відповідь (збільшена за складність)
        if is_correct:
            add_coins(user_id, chat_id, 10)  # Збільшено з 5 до 10 монет
            add_xp(user_id, chat_id, 5)  # Додано XP

            # 🐰 ІВЕНТ: Великдень - правильна відповідь = прогрес
            add_event_progress(user_id, chat_id, 'easter', 1)
            check_event_random_drop(user_id, chat_id, 'easter', 'відповіді на квіз')

            text = f"""✅ **ПРАВИЛЬНО!**

+10 монет
+5 XP

Правильна відповідь: {question['options'][question['correct']]}

Натисни /quiz для наступного питання"""
        else:
            text = f"""❌ **НЕПРАВИЛЬНО!**

Правильна відповідь: {question['options'][question['correct']]}

Натисни /quiz для наступного питання"""

        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка quiz_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Помилка!")


@bot.message_handler(commands=['quizstats'])
def quiz_stats_cmd(message):
    """Статистика квізу"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        stats = get_quiz_stats(user_id, chat_id)
        
        total = stats['total']
        correct = stats['correct']
        today = stats['today']
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        text = f"""📊 **СТАТИСТИКА КВІЗУ**

📅 Сьогодні: {today}/10 питань

📈 Загалом:
• Всього відповідей: {total}
• Правильних: {correct}
• Неправильних: {total - correct}
• Точність: {accuracy:.1f}%

💰 Нагорода: 10 монет + 5 XP за правильну відповідь

Натисни /quiz щоб продовжити!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ Помилка /quizstats: {e}", exc_info=True)
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

        # Перевірка ліміту дітей (максимум 10)
        children_count = get_children_count(user_id, chat_id)
        if children_count >= 10:
            bot.reply_to(message, f"""❌ **ДОСЯГНУТО ЛІМІТ ДІТЕЙ!**

У тебе вже {children_count}/10 дітей.

**Що робити:**
• /sacrificechild - жертва дитини
• /childmarry - одружити дітей (створення онуків)

Після звільнення місця зможеш знову мати дітей!""")
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

        # Екрануємо спеціальні символи в іменах хряків
        hryak_name = escape_markdown(hryak['name'])
        partner_name = escape_markdown(partner_hryak['name'])

        text = f"""{emoji} **Трахензебітен відбувся!**

🐷 Твій хряк: {hryak_name}
💑 Партнер: {partner_name}
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


@bot.message_handler(commands=['breed'])
def breed_cmd(message):
    """Схрещування хряків - створення потомства з генетикою"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        # Перевіряємо чи є хряк у користувача
        father_hryak = get_hryak(user_id, chat_id)
        if not father_hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return

        # Перевірка ліміту дітей (максимум 10)
        children_count = get_children_count(user_id, chat_id)
        if children_count >= 10:
            bot.reply_to(message, f"""❌ **ДОСЯГНУТО ЛІМІТ ДІТЕЙ!**

У тебе вже {children_count}/10 дітей.

**Що робити:**
• /sacrificechild - жертва дитини
• /childmarry - одружити дітей (створення онуків)

Після звільнення місця зможеш знову мати дітей!""")
            return

        # Перевіряємо кулдаун (24 години)
        BREED_COOLDOWN = 86400
        last_breed_time = get_last_trachen_time(user_id, chat_id)  # Використовуємо той самий кулдаун
        now = int(time.time())
        time_since_last = now - last_breed_time

        if last_breed_time > 0 and time_since_last < BREED_COOLDOWN:
            hours_left = int((BREED_COOLDOWN - time_since_last) / 3600)
            minutes_left = int(((BREED_COOLDOWN - time_since_last) % 3600) / 60)
            bot.reply_to(message, f"⏳ Ще рано! Схрещування доступне раз на 24 години.\n\nЗалишилось: {hours_left} год {minutes_left} хв")
            return

        # Перевіряємо чи є партнер (reply на повідомлення)
        if not message.reply_to_message:
            bot.reply_to(message, """❌ Використання: /breed (у відповідь на повідомлення партнера)

**Схрещування** - це просунута версія /trachen:
• Потомство успадковує гени батьків
• Можливі рідкісні комбінації
• Шанс на мутації
• Дитина народжується відразу

⚠️ Вартість: 100 монет""")
            return

        # Отримуємо партнера
        partner_id = message.reply_to_message.from_user.id
        if partner_id == user_id:
            bot.reply_to(message, "❌ Не можна схрещувати з самим собою!")
            return

        mother_hryak = get_hryak(partner_id, chat_id)
        if not mother_hryak:
            bot.reply_to(message, "❌ У цього користувача немає хряка!")
            return

        # Перевіряємо чи вистачає монет
        user_currency = get_user_currency(user_id, chat_id)
        if not user_currency or user_currency.get('coins', 0) < 100:
            bot.reply_to(message, "❌ Недостатньо монет! Потрібно 100 монет.")
            return

        # Списуємо монети
        from db import update_user_currency
        new_coins = max(0, user_currency.get('coins', 0) - 100)
        update_user_currency(user_id, chat_id, coins=new_coins)

        # Схрещуємо
        result = breed_hryaks(user_id, partner_id, chat_id, father_hryak, mother_hryak)

        if not result.get('success'):
            bot.reply_to(message, f"❌ Помилка схрещування: {result.get('error', 'Невідома помилка')}")
            return

        child = result.get('child')

        # Отримуємо генетичну сумісність
        compatibility = get_genetic_compatibility(user_id, partner_id, chat_id)

        # Формуємо повідомлення
        rarity_emoji = GENE_RARITIES.get(child['gene_rarity'], {}).get('color', '⚪')
        color_emoji = COLOR_TYPES.get(child['color_type'], {}).get('emoji', '🐷')

        # Екрануємо всі динамічні тексти для Markdown
        child_name_safe = escape_markdown(child['name'])
        father_name_safe = escape_markdown(father_hryak['name'])
        mother_name_safe = escape_markdown(mother_hryak['name'])
        inherited_trait_safe = escape_markdown(child.get('inherited_trait') or '')
        rarity_name_safe = escape_markdown(GENE_RARITIES.get(child['gene_rarity'], {}).get('name', 'Звичайний'))
        if compatibility.get('compatibility') == 'unknown':
            compatibility_text = "Н/Д (гени не знайдено)"
        else:
            compatibility_text = compatibility['compatibility']
        compatibility_safe = escape_markdown(compatibility_text)

        text = "🎉 \\*ПОТОМСТВО СТВОРЕНО\\!\\*\n\n"
        text += f"👨 Батько: {father_name_safe} \\(ID: {user_id}\\)\n"
        text += f"👩 Мати: {mother_name_safe} \\(ID: {partner_id}\\)\n\n"
        text += "👶 \\*Дитина:\\*\n"
        text += f"{color_emoji} Ім'я: {child_name_safe}\n"
        text += f"⚖️ Вага: {child['weight']} кг\n"
        text += f"{rarity_emoji} Рідкість: {rarity_name_safe}\n\n"
        text += "🧬 \\*Особливості:\\*"

        if child['has_mutation']:
            text += "\n🔴 \\*МУТАЦІЯ\\!\\* Унікальна здібність\\!"
        elif child.get('inherited_trait'):
            text += f"\n✨ {inherited_trait_safe}"
        else:
            text += "\n⚪ Без особливих ознак"

        text += f"\n\n💞 Сумісність генів: {compatibility_safe}"
        text += "\n💰 Витрачено: 100 монет"
        text += "\n\n⏰ Наступне схрещування через 24 години"

        # Зберігаємо гени дитини
        try:
            # Отримуємо ID останньої дитини
            children = get_children(user_id, chat_id)
            if children:
                latest_child = children[0]
                update_child_genes(
                    latest_child['id'],
                    child['gene_rarity'],
                    child['bonus_type'],
                    child['bonus_value'],
                    child['color_type']
                )
        except Exception as e:
            logger.error(f"❌ Помилка збереження генів дитини: {e}")

        bot.reply_to(message, text, parse_mode="MarkdownV2")

    except Exception as e:
        logger.error(f"❌ Помилка /breed: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['genes'])
def genes_cmd(message):
    """Показати гени хряка користувача"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        hryak = get_hryak(user_id, chat_id)
        if not hryak:
            bot.reply_to(message, "❌ У тебе ще немає хряка! Введи /grow")
            return

        genes = get_hryak_genes(user_id, chat_id)

        rarity_emoji = GENE_RARITIES.get(genes['gene_rarity'] if genes else 'C', {}).get('color', '⚪')
        color_emoji = COLOR_TYPES.get(genes['color_type'] if genes else 'normal', {}).get('emoji', '🐷')

        text = f"""🧬 **ГЕНИ ХРЯКА**

🐷 {hryak['name']}
{color_emoji} Колір: {COLOR_TYPES.get(genes['color_type'] if genes else 'normal', {}).get('name', 'Звичайний')}
{rarity_emoji} Рідкість: {GENE_RARITIES.get(genes['gene_rarity'] if genes else 'C', {}).get('name', 'Звичайний')}

"""

        if genes and genes.get('bonus_type'):
            bonus_name = BONUS_TYPES.get(genes['bonus_type'], {}).get('name', 'Бонус')
            text += f"✨ Бонус: +{genes['bonus_value']}% {bonus_name}\n"
        else:
            text += "✨ Бонус: Відсутній\n"

        if genes:
            text += f"🔮 Шанс мутації: {genes.get('mutation_chance', 0.05) * 100:.1f}%\n"

        text += f"""
**Команди:**
/breed - схрещування з іншим гравцем
/children - перегляд дітей
/childtop - топ дітей за вагою

**Як працює генетика:**
• Рідкість: C ⚪ → R 🔵 → E 🟣 → L 🟡 → S 🔴
• Колір успадковується від батьків
• Бонуси можуть комбінуватися
• Мутації дають унікальні здібності"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /genes: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childmarry'])
def child_marry_cmd(message):
    """Одружити дітей (створити онуків)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        
        if len(parts) < 3:
            bot.reply_to(message, """💕 **ОДРУЖЕННЯ ДІТЕЙ**

Використання: /childmarry <child1_id> <child2_id>

Приклад: /childmarry 1 2

**Вимоги:**
• Обидві дитини мають належати тобі
• Мінімум 100 монет за весілля
• Створюється онук зі змішаними характеристиками""")
            return
        
        try:
            child1_id = int(parts[1])
            child2_id = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ ID мають бути числами!")
            return
        
        if child1_id == child2_id:
            bot.reply_to(message, "❌ Не можна одружити з самим собою!")
            return
        
        # Перевіряємо чи є діти
        children = get_children(user_id, chat_id)
        child1 = next((c for c in children if c['id'] == child1_id), None)
        child2 = next((c for c in children if c['id'] == child2_id), None)
        
        if not child1 or not child2:
            bot.reply_to(message, "❌ Діти не знайдені!")
            return
        
        # Перевіряємо баланс
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < 100:
            bot.reply_to(message, f"❌ Недостатньо монет! Потрібно 100")
            return
        
        # Знімаємо монети
        update_user_currency(user_id, chat_id, coins=currency['coins'] - 100)
        
        # Створюємо онука
        grandchild_weight = max(1, int((child1['weight'] + child2['weight']) / 2) + random.randint(-5, 5))
        grandchild_name = f"{child1['name'][:2]}-{child2['name'][:2]}-G1"
        
        # Визначаємо спадкову ознаку
        traits = ['Швидкий', 'Сильний', 'Розумний', 'Хитрий', 'Великий', 'Малий']
        inherited_trait = random.choice(traits)
        
        add_child(user_id, chat_id, user_id, user_id, grandchild_name, grandchild_weight, inherited_trait)
        
        bot.reply_to(message, f"""💕 **ВЕСІЛЛЯ ВІДБУЛОСЯ!**

{child1['name']} + {child2['name']}

👶 Народився онук: {grandchild_name}
⚖️ Вага: {grandchild_weight} кг
🧬 Особливість: {inherited_trait}

💰 Витрачено: 100 монет""")
    except Exception as e:
        logger.error(f"❌ Помилка /childmarry: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childtrain'])
def child_train_cmd(message):
    """Тренувати дитину"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """💪 **ТРЕНУВАННЯ ДИТИНИ**

Використання: /childtrain <child_id>

Вартість: 50 монет
Ефект: +5 до ваги дитини
Кулдаун: 12 годин""")
            return

        try:
            child_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ ID має бути числом!")
            return

        # Перевіряємо чи є дитина
        children = get_children(user_id, chat_id)
        child = next((c for c in children if c['id'] == child_id), None)

        if not child:
            bot.reply_to(message, "❌ Дитину не знайдено!")
            return

        # Перевіряємо кулдаун тренування
        from db import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT last_train FROM hryak_genes WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
            row = cursor.fetchone()
            last_train = int(row[0]) if row and row[0] else 0
            cursor.close()
            conn.close()

            CHILD_TRAIN_COOLDOWN = 43200  # 12 годин
            now = int(time.time())
            time_since_last = now - last_train if last_train > 0 else CHILD_TRAIN_COOLDOWN

            if last_train > 0 and time_since_last < CHILD_TRAIN_COOLDOWN:
                hours_left = int((CHILD_TRAIN_COOLDOWN - time_since_last) / 3600)
                minutes_left = int(((CHILD_TRAIN_COOLDOWN - time_since_last) % 3600) / 60)
                bot.reply_to(message, "⏳ **Ще рано!**\n\nЗалишилось: {} год {} хв".format(hours_left, minutes_left))
                return

        # Перевіряємо баланс
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < 50:
            bot.reply_to(message, f"❌ Недостатньо монет! Потрібно 50")
            return

        # Знімаємо монети
        update_user_currency(user_id, chat_id, coins=currency['coins'] - 50)

        # Збільшуємо вагу
        new_weight = child['weight'] + 5

        # Оновлюємо дитину і last_train
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE children SET weight = %s WHERE id = %s', (new_weight, child_id))
            # Оновлюємо last_train
            cursor.execute('''
                INSERT INTO hryak_genes (user_id, chat_id, last_train)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, chat_id) DO UPDATE SET last_train = %s
            ''', (user_id, chat_id, int(time.time()), int(time.time())))
            conn.commit()
            cursor.close()
            conn.close()

        # Екрануємо ім'я дитини
        child_name_safe = child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

        bot.reply_to(message, f"""💪 **ТРЕНУВАННЯ ВІДБУЛОСЯ!**

Дитина: {child_name_safe}
Вага: {child['weight']} → {new_weight} кг (+5)

💰 Витрачено: 50 монет
⏰ Наступне тренування через 12 годин""")
    except Exception as e:
        logger.error(f"❌ Помилка /childtrain: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childbonus'])
def child_bonus_cmd(message):
    """Показати бонуси від дітей"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        bonuses = get_children_bonuses(user_id, chat_id)

        if not bonuses.get('bonuses') or bonuses['children_count'] == 0:
            bot.reply_to(message, "👶 У тебе ще немає дітей!\n\nДіти дають бонуси до сили хряка!")
            return

        total_bonus = bonuses['total_bonus']

        text = f"""🎯 **БОНУСИ ВІД ДІТЕЙ**

👨‍👩‍👧‍👦 Всього дітей: {bonuses['children_count']}
✨ Загальний бонус: +{total_bonus:.1f}%

**Діти:**
"""
        for i, child_bonus in enumerate(bonuses['bonuses'][:10], 1):
            type_emoji = {'mutation': '🧬', 'legendary': '⭐', 'rare': '🔵', 'normal': '⚪'}.get(child_bonus['bonus_type'], '⚪')
            text += f"{i}. **{child_bonus['name']}** {type_emoji}\n"
            text += f"   ⚖️ Вага: {child_bonus['weight']} кг | Вік: {child_bonus['age_days']} дн.\n"
            text += f"   ✨ Бонус: +{child_bonus['bonus']:.1f}%\n\n"

        if len(bonuses['bonuses']) > 10:
            text += f"... і ще {len(bonuses['bonuses']) - 10} дітей\n"

        text += f"""
**Як працюють бонуси:**
• Бонус додається до сили твого хряка
• Діти з мутаціями дають 2x бонус
• Старші діти дають +10% за кожен день
• Максимальний вік для бонусу: 30 днів"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /childbonus: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childraid'])
def child_raid_cmd(message):
    """Відправити дитину в рейд"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """❌ **Використання:** /childraid <ID дитини> [тип]

**Типи рейдів:**
• coins - по монети (за замовчуванням)
• xp - по досвід
• items - по предмети

**Приклад:** `/childraid 123 coins`""")
            return

        child_id = int(parts[1])
        raid_type = parts[2].lower() if len(parts) > 2 else 'coins'

        if raid_type not in ['coins', 'xp', 'items']:
            bot.reply_to(message, "❌ Невірний тип рейду! Обирай: coins, xp, items")
            return

        # Отримуємо дитину
        children = get_children(user_id, chat_id)
        child = None
        for c in children:
            if c['id'] == child_id:
                child = c
                break

        if not child:
            bot.reply_to(message, "❌ Ця дитина не знайдена!")
            return

        # Перевіряємо чи є активний рейд
        active_raid = get_active_child_raid(child_id, chat_id)
        if active_raid:
            end_time = active_raid['end_time']
            now = int(time.time())
            if now < end_time:
                time_left = end_time - now
                minutes_left = int(time_left / 60)
                bot.reply_to(message, f"⏰ **Дитина вже в рейді!**\n\nЗалишилося: {minutes_left} хв.\n\nОтримати нагороду: /childclaim {active_raid['id']}")
                return

        # Відправляємо в рейд
        result = send_child_on_raid(child_id, user_id, chat_id, raid_type)

        if not result:
            bot.reply_to(message, "❌ Помилка відправки в рейд!")
            return

        # Перевіряємо чи не повернуто помилку
        if result.get('error') == 'cooldown':
            cooldown_left = int(result.get('cooldown_left', 0) / 60)
            bot.reply_to(message, f"⏰ **Зачекайте!**\n\nМинуло занадто мало часу з останнього рейду.\n\nЗалишилося: {cooldown_left} хв.")
            return

        if 'raid_time' not in result:
            bot.reply_to(message, "❌ Помилка: рейд не вдалося створити. Перевірте витривалість дитини.")
            return

        raid_time_minutes = int(result['raid_time'] / 60)
        reward_type = {'coins': '💰 монет', 'xp': '⭐ XP', 'items': '🎁 предметів'}.get(raid_type, '💰 монет')
        
        # Застосовуємо бонус від дітей
        bonuses = get_children_bonuses(user_id, chat_id)
        bonus_mult = 1 + (bonuses.get('total_bonus', 0) / 100)
        final_reward = int(result['reward'] * bonus_mult)

        # Екрануємо ім'я дитини
        child_name_safe = child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

        text = f"""🗡️ **РЕЙД ВІДПРАВЛЕНО!**

Дитина: {child_name_safe}
Тип рейду: {raid_type.upper()}
Очікувана нагорода: {final_reward} {reward_type}
(Бонус: +{bonuses.get('total_bonus', 0):.1f}%)
Час рейду: {raid_time_minutes} хв.

**ID рейду:** `{result['raid_id']}`
**По завершенню:**
Введи /childclaim {result['raid_id']} щоб отримати нагороду!"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /childraid: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childclaim'])
def child_claim_cmd(message):
    """Отримати нагороду за рейд"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """❌ **Використання:** /childclaim <ID рейду>

**Перевірити активні рейди:**
/children - показує всіх дітей
Якщо дитина в рейді, буде індикатор

**Приклад:** `/childclaim 123`""")
            return

        raid_id = int(parts[1])

        # Отримуємо нагороду
        result = claim_child_raid(raid_id, user_id, chat_id)

        if not result:
            bot.reply_to(message, "❌ Рейд не знайдено або ви не маєте прав!")
            return

        if result.get('error'):
            if 'ще не завершився' in result['error']:
                end_time = result.get('end_time', 0)
                now = int(time.time())
                time_left = end_time - now
                minutes_left = int(time_left / 60)
                bot.reply_to(message, f"⏰ **Рейд ще не завершився!**\n\nЗалишилося: {minutes_left} хв.\n\nСпробуйте пізніше.")
                return
            bot.reply_to(message, f"❌ Помилка: {result['error']}")
            return

        # Отримуємо нагороду
        reward = result['reward']
        raid_type = result['raid_type']
        child_id = result['child_id']

        # Застосовуємо бонус від дітей
        bonuses = get_children_bonuses(user_id, chat_id)
        bonus_mult = 1 + (bonuses.get('total_bonus', 0) / 100)
        final_reward = int(reward * bonus_mult)

        # Видаємо нагороду
        if raid_type == 'coins':
            add_coins(user_id, chat_id, final_reward)
            reward_text = f"💰 {final_reward} монет"
        elif raid_type == 'xp':
            add_xp(user_id, chat_id, final_reward)
            reward_text = f"⭐ {final_reward} XP"
        elif raid_type == 'items':
            # TODO: Реалізувати предмети
            add_coins(user_id, chat_id, final_reward)
            reward_text = f"💰 {final_reward} монет (предмети незабаром)"

        # Отримуємо дитину
        children = get_children(user_id, chat_id)
        child = next((c for c in children if c['id'] == child_id), None)
        child_name = child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`') if child else f"ID {child_id}"

        bot.reply_to(message, f"""✅ **РЕЙД ЗАВЕРШЕНО!**

Дитина: {child_name}
Нагорода: {reward_text}
Бонус: +{bonuses.get('total_bonus', 0):.1f}%

Дитина тепер може знову відправитись в рейд!
/childraid {child_id}""")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID рейду!")
    except Exception as e:
        logger.error(f"❌ Помилка /childclaim: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childstamina_upgrade'])
def child_stamina_upgrade_cmd(message):
    """Покращити витривалість дітей"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Отримуємо поточну витривалість
        stamina = get_child_stamina(user_id, chat_id)
        current_level = stamina['stamina_level']
        
        # Розрахунок вартості
        upgrade_cost = int(100 * (2 ** (current_level - 1)))
        new_max_time = min(120, (current_level + 1) * 5)
        
        # Перевірка балансу
        currency = get_user_currency(user_id, chat_id)
        if currency['coins'] < upgrade_cost:
            bot.reply_to(message, f"""❌ **Недостатньо монет!**

Вартість покращення: {upgrade_cost} монет
У вас: {currency['coins']} монет

Заробіть більше монет в рейдах!""")
            return
        
        # Списуємо монети
        update_user_currency(user_id, chat_id, coins=currency['coins'] - upgrade_cost)
        
        # Покращуємо витривалість
        result = upgrade_child_stamina(user_id, chat_id)
        
        if not result:
            bot.reply_to(message, "❌ Помилка покращення!")
            return
        
        bot.reply_to(message, f"""✅ **ВИТРИВАЛІСТЬ ПОКРАЩЕНО!**

Рівень: {current_level} → {result['new_level']}
Макс. час рейду: {min(120, current_level * 5)} → {new_max_time} хв
Вартість: {upgrade_cost} монет

Наступне покращення: {int(100 * (2 ** (result['new_level'] - 1)))} монет""")

    except Exception as e:
        logger.error(f"❌ Помилка /childstamina_upgrade: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['childduel'])
def child_duel_cmd(message):
    """Дуель дітей"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2 or not message.reply_to_message:
            bot.reply_to(message, """❌ **Використання:** /childduel <ID твоєї дитини>
(У відповідь на повідомлення суперника з його дитиною)

**Дуель дітей:**
• Переможець отримує 50% ваги дитини суперника
• Батьки отримують монети та XP
• Кулдаун: 6 годин""")
            return

        my_child_id = int(parts[1])
        opponent_id = message.reply_to_message.from_user.id

        # Отримуємо свою дитину
        my_children = get_children(user_id, chat_id)
        my_child = None
        for c in my_children:
            if c['id'] == my_child_id:
                my_child = c
                break

        if not my_child:
            bot.reply_to(message, "❌ Ця дитина не знайдена!")
            return

        # Отримуємо дитину суперника
        opponent_children = get_children(opponent_id, chat_id)
        if not opponent_children:
            bot.reply_to(message, "❌ У суперника немає дітей!")
            return

        # Беремо першу дитину суперника (або можна додати вибір)
        opponent_child = opponent_children[0]

        # Розраховуємо силу
        my_power = get_child_power(my_child_id, chat_id)
        opponent_power = get_child_power(opponent_child['id'], chat_id)

        if not my_power or not opponent_power:
            bot.reply_to(message, "❌ Помилка розрахунку сили!")
            return

        # Визначаємо переможця
        my_roll = random.uniform(0.8, 1.2) * my_power['power']
        opponent_roll = random.uniform(0.8, 1.2) * opponent_power['power']

        if my_roll > opponent_roll:
            winner = user_id
            weight_gain = int(opponent_child['weight'] * 0.5)
            coins_reward = 100
            xp_reward = 50
            # Екрануємо імена дітей
            my_child_name = my_child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            opponent_child_name = opponent_child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            text = f"""🏆 **ПЕРЕМОГА!**

Твоя дитина **{my_child_name}** перемогла!
⚖️ +{weight_gain} кг до ваги
💰 +{coins_reward} монет
⭐ +{xp_reward} XP"""

            # Оновлюємо вагу
            from db import get_connection, add_coins, add_xp
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE children SET weight = %s WHERE id = %s', 
                              (my_child['weight'] + weight_gain, my_child_id))
                conn.commit()
                cursor.close()
                conn.close()
            add_coins(user_id, chat_id, coins_reward)
            add_xp(user_id, chat_id, xp_reward)

        else:
            # Екрануємо імена дітей
            my_child_name = my_child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            opponent_child_name = opponent_child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            text = f"""💀 **ПОРАЗКА!**

Твоя дитина **{my_child_name}** програла дитині **{opponent_child_name}**.
Наступного разу пощастить!"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /childduel: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['children'])
def children_cmd(message):
    """Показати дітей користувача"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        children_list = get_children(user_id, chat_id)
        children_count = get_children_count(user_id, chat_id)

        if not children_list:
            bot.reply_to(message, "👶 У тебе ще немає дітей\\!\n\nЗаведи дітей через /trachen або /breed\n\n📊 Ліміт: {}/10".format(children_count), parse_mode="MarkdownV2")
            return

        text = "👶 *Твої діти:* \\({}/10\\)\n\n".format(children_count)

        for i, child in enumerate(children_list, 1):
            born_date = time.strftime('%d.%m.%Y', time.localtime(child['born_at']))
            # Екрануємо крапки в даті
            born_date = born_date.replace('.', '\\.')

            # Отримуємо гени дитини
            child_genes = get_hryak_genes(child['user_id'], chat_id)
            rarity_emoji = "⚪"
            if child_genes:
                rarity_emoji = GENE_RARITIES.get(child_genes.get('gene_rarity', 'C'), {}).get('color', '⚪')

            # Перевіряємо чи є співвласником
            ownership = ""
            if child.get('co_owner_id'):
                ownership = " 🤝 Спільно"
            elif child.get('user_id') != user_id:
                ownership = " 👥 Ви співвласник"

            # Перевіряємо чи дитина в рейді
            raid_status = ""
            active_raid = get_active_child_raid(child['id'], chat_id)
            if active_raid and not active_raid.get('claimed', True):
                now = int(time.time())
                if now < active_raid['end_time']:
                    time_left = active_raid['end_time'] - now
                    minutes_left = int(time_left / 60)
                    raid_status = " 🗡️ В рейді \\({} хв\\)".format(minutes_left)
                else:
                    raid_status = " ✅ Готовий до claim\\! \\(/childclaim {}\\)".format(active_raid['id'])

            # Екрануємо спеціальні символи в тексті
            child_name = escape_markdown(child['name'])
            inherited_trait = escape_markdown(child['inherited_trait'] or 'Немає')

            text += "{}\\. `{}` \\- *{}* {}{}{}\n".format(i, child['id'], child_name, rarity_emoji, ownership, raid_status)
            text += "   ⚖️ Вага: {} кг\n".format(child['weight'])
            text += "   🎂 Народжений: {}\n".format(born_date)
            text += "   🧬 Особливість: {}\n\n".format(inherited_trait)

        text += "\n*Команди:*\n"
        text += "/childinfo \\<ID\\> \\- інформація\n"
        text += "/renamechild \\<ID\\> \\<ім'я\\> \\- перейменувати\n"
        text += "/sacrificechild \\<ID\\> \\- жертва\n"
        text += "/childmarry \\<ID1\\> \\<ID2\\> \\- одружити\n"
        text += "/childtrain \\<ID\\> \\- тренувати\n"
        text += "/childraid \\<ID\\> \\[тип\\] \\- рейд\n"
        text += "/childclaim \\<ID рейду\\> \\- отримати нагороду\n"
        text += "/childstamina\\_upgrade \\- покращити витривалість\n"
        text += "/genes \\- гени твого хряка\n\n"
        text += "*Приклад:* `/childinfo 123`"

        bot.reply_to(message, text, parse_mode="MarkdownV2")

    except Exception as e:
        logger.error(f"❌ Помилка /children: {e}", exc_info=True)
        bot.reply_to(message, "❌ Помилка: {}".format(escape_markdown(str(e))), parse_mode="MarkdownV2")


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

        born_date_raw = time.strftime('%d.%m.%Y %H:%M', time.localtime(child['born_at']))
        born_date = escape_markdown(born_date_raw)

        # Отримуємо гени дитини
        child_genes = get_hryak_genes(child['user_id'], chat_id)
        rarity_emoji = "⚪"
        color_emoji = "🐷"

        if child_genes:
            rarity_emoji = GENE_RARITIES.get(child_genes.get('gene_rarity', 'C'), {}).get('color', '⚪')
            color_emoji = COLOR_TYPES.get(child_genes.get('color_type', 'normal'), {}).get('emoji', '🐷')

        # Екрануємо спеціальні символи
        child_name = escape_markdown(child['name'])
        inherited_trait = escape_markdown(child['inherited_trait'] or 'Немає')

        weight_text = escape_markdown(str(child['weight']))
        age_days = int((time.time() - child['born_at']) / 86400)
        father_id = escape_markdown(str(child['father_user_id']))
        mother_id = escape_markdown(str(child['mother_user_id']))

        text = "👶 \\*ІНФОРМАЦІЯ ПРО ДИТИНУ\\* {rarity_emoji}\n\n".format(rarity_emoji=rarity_emoji)
        text += "{color_emoji} \\*Ім'я:\\* {child_name}\n".format(color_emoji=color_emoji, child_name=child_name)
        text += "⚖️ \\*Вага:\\* {weight} кг\n".format(weight=weight_text)
        text += "🧬 \\*Особливість:\\* {trait}\n\n".format(trait=inherited_trait)
        text += "\\*Батьки:\\*\n"
        text += "👨 Батько: ID {fid}\n".format(fid=father_id)
        text += "👩 Мати: ID {mid}\n\n".format(mid=mother_id)
        text += "\\*Народжений:\\* {born}\n".format(born=born_date)
        text += "\\*Вік:\\* {age} дн\\.\n".format(age=age_days)

        if child_genes:
            rarity_name = escape_markdown(GENE_RARITIES.get(child_genes.get('gene_rarity', 'C'), {}).get('name', 'Звичайний'))
            color_name = escape_markdown(COLOR_TYPES.get(child_genes.get('color_type', 'normal'), {}).get('name', 'Звичайний'))
            text += "\n\\*Гени:\\*\n"
            text += "• Рідкість: {rarity} {emoji}\n".format(rarity=rarity_name, emoji=rarity_emoji)
            text += "• Колір: {color} {emoji}\n".format(color=color_name, emoji=color_emoji)

            if child_genes.get('bonus_type'):
                bonus_name = escape_markdown(BONUS_TYPES.get(child_genes['bonus_type'], {}).get('name', 'Бонус'))
                bonus_val = escape_markdown(str(child_genes['bonus_value']))
                text += "• Бонус: \\+{val}% {name}\n".format(val=bonus_val, name=bonus_name)

            mut_chance = escape_markdown("{:.1f}".format(child_genes.get('mutation_chance', 0.05) * 100))
            text += "• Шанс мутації: {val}%\n".format(val=mut_chance)

        child_id_text = escape_markdown(str(child_id))
        text += "\n\\*Команди:\\*\n"
        text += "/renamechild {id} \\<нове ім'я\\> \\- перейменувати\n".format(id=child_id_text)
        text += "/sacrificechild {id} \\- жертва \\(монети \\+ XP\\)".format(id=child_id_text)

        bot.reply_to(message, text, parse_mode="MarkdownV2")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID дитини!")
    except Exception as e:
        logger.error(f"❌ Помилка /childinfo: {e}", exc_info=True)
        bot.reply_to(message, "❌ Помилка: {}".format(escape_markdown(str(e))), parse_mode="MarkdownV2")


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
            bot.reply_to(message, "👶 ТОП ДІТЕЙ\n\nВ чаті ще немає дітей!")
            return

        text = "🏆 ТОП ДІТЕЙ ЗА ВАГОЮ\n\n"

        for i, child in enumerate(children, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            # Екрануємо спеціальні символи в імені
            child_name = child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            
            # Екрануємо спеціальні символи в особливості
            trait_text = ""
            if child['inherited_trait']:
                trait = child['inherited_trait'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                trait_text = f" ({trait})"
            
            # Обрізаємо імена батьків і екрануємо
            father_name = child['father_name'][:15].replace('_', '\\_').replace('*', '\\*') if child.get('father_name') else "Unknown"
            mother_name = child['mother_name'][:15].replace('_', '\\_').replace('*', '\\*') if child.get('mother_name') else "Unknown"
            
            text += f"{medal} {child_name} - {child['weight']} кг{trait_text}\n"
            text += f"   Батьки: {father_name} + {mother_name}\n\n"

        bot.reply_to(message, text)

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

            # Екрануємо ім'я дитини
            child_name_safe = child['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

            bot.reply_to(message, f"""🔥 **ЖЕРТВА ПРИЙНЯТА!**

Дитина **{child_name_safe}** пожертвована!

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
            # Екрануємо спеціальні символи
            child_name = child_name.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
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

Вхідний внесок: 10 монет
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

Вхідний внесок: {active_tournament['entry_fee']} монет
Призовий фонд: {active_tournament['prize_pool']} монет
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
Вхідний внесок: 10 монет
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
                bot.reply_to(message, f"❌ Недостатньо монет! Потрібно {active_tournament['entry_fee']} монет")
                return

            # Знімаємо вхідний внесок
            update_user_currency(user_id, chat_id, coins=currency['coins'] - active_tournament['entry_fee'])

            # Приєднуємо до турніру
            if join_tournament(active_tournament['id'], user_id, chat_id, hryak['weight']):
                bot.reply_to(message, f"✅ Ти приєднався до турніру!\nХряк: {hryak['name']} ({hryak['weight']} кг)\nВнесок: {active_tournament['entry_fee']} монет")
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
        
        # Перевіряємо довжину на����ви
        if len(guild_name) < 3 or len(guild_name) > 32:
            bot.reply_to(message, "❌ Назва ма�� бути від 3 до 32 символів!")
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
        
        # Показуємо гільдію к��ристувача
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
            role_emoji = "👑" if member['role'] == 'owner' else "��" if member['role'] == 'officer' else "▫️"
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


@bot.message_handler(commands=['promote'])
def promote_cmd(message):
    """Підвищити члена гільдії до офіцера"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """🎖️ **ПІДВИЩЕННЯ**

Використання: /promote <user_id>

Приклад: /promote 123456789

**Обмеження:**
• Максимум 5 офіцерів в гільдії
• Тільки власник або офіцер може підвищувати
• Власник може знижувати: /demote <user_id>""")
            return

        target_user_id = int(parts[1])

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ти не в гільдії!")
            return

        # Перевіряємо права
        members = get_guild_members(user_guild['id'])
        user_role = None
        for m in members:
            if m['user_id'] == user_id:
                user_role = m['role']
                break

        if not user_role or user_role not in ['owner', 'officer']:
            bot.reply_to(message, "❌ Тільки власник або офіцер може підвищувати!")
            return

        # Перевіряємо чи не власник
        if target_user_id == user_guild['owner_user_id']:
            bot.reply_to(message, "❌ Не можна підвищити власника!")
            return

        # Підвищуємо
        result = promote_guild_member(user_guild['id'], target_user_id, user_id)

        if result.get('success'):
            bot.reply_to(message, f"""🎉 **ПІДВИЩЕННЯ!**

Користувача ID {target_user_id} підвищено до офіцера!

👥 Офіцерів: {result.get('officer_count')}/5

**Команди:**
/demote <user_id> - знизити (тільки власник)""")
        else:
            error = result.get('error', 'Невідома помилка')
            bot.reply_to(message, f"❌ Помилка: {error}")

    except ValueError:
        bot.reply_to(message, "❌ Невірний формат ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /promote: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['demote'])
def demote_cmd(message):
    """Знизити офіцера до члена"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, """👎 **ЗНИЖЕННЯ**

Використання: /demote <user_id>

Приклад: /demote 123456789

**Обмеження:**
• Тільки власник може знижувати
• Можна знизити тільки офіцера""")
            return

        target_user_id = int(parts[1])

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ти не в гільдії!")
            return

        # Перевіряємо чи власник
        if user_guild['owner_user_id'] != user_id:
            bot.reply_to(message, "❌ Тільки власник може знижувати офіцерів!")
            return

        # Знижуємо
        result = demote_guild_member(user_guild['id'], target_user_id, user_id)

        if result.get('success'):
            bot.reply_to(message, f"""✅ **ЗНИЖЕННЯ!**

Користувача ID {target_user_id} знижено до члена гільдії.""")
        else:
            error = result.get('error', 'Невідома помилка')
            bot.reply_to(message, f"❌ Помилка: {error}")

    except ValueError:
        bot.reply_to(message, "❌ Невірний формат ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /demote: {e}", exc_info=True)
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
# ГІЛЬДІЙНІ ВІЙНИ - КОМАНДИ
# ============================================

@bot.message_handler(commands=['guild_territories'])
def guild_territories_cmd(message):
    """Показати всі території"""
    try:
        territories = get_all_territories()
        
        if not territories:
            bot.reply_to(message, "🗺️ **КАРТА ТЕРИТОРІЙ**\n\nНемає захоплених територій!\n\nЗахопи першу територію: /guild_capture <назва>")
            return
        
        text = "🗺️ **КАРТА ТЕРИТОРІЙ**\n\n"
        
        territory_emojis = {'mine': '🏭', 'forest': '🌲', 'castle': '🏰', 'temple': '⛩️', 'market': '🏪', 'fortress': '🏯'}
        
        for t in territories:
            owner = t['guild_name'] if t['guild_name'] else "🔳 Вільна"
            emoji = territory_emojis.get(t.get('bonus_type', ''), '📍')
            
            text += f"{emoji} **{t['name']}** ({owner})\n"
            text += f"   Бонус: +{t['bonus_value']} {t['bonus_type']}\n"
            text += f"   Дохід: {t['income_per_hour']}/год\n\n"
        
        text += "\n**Команди:**\n"
        text += "/guild_capture <назва> - захопити територію\n"
        text += "/guild_income - зібрати дохід"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_territories: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_capture'])
def guild_capture_cmd(message):
    """Захопити територію"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_capture <назва території>")
            return
        
        # Перевірка гільдії
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка рівня гільдії
        if user_guild.get('level', 1) < 3:
            bot.reply_to(message, "❌ Гільдія має бути 3+ рівня!")
            return
        
        # Знаходимо територію
        territories = get_all_territories()
        territory = None
        for t in territories:
            if t['name'].lower() == parts[1].lower():
                territory = t
                break
        
        if not territory:
            # Створюємо нову територію
            territory_name = parts[1]
            territory_type = 'mine'  # За замовчуванням
            
            # Визначаємо тип за назвою
            if 'ліс' in territory_name.lower() or 'forest' in territory_name.lower():
                territory_type = 'forest'
            elif 'замок' in territory_name.lower() or 'castle' in territory_name.lower():
                territory_type = 'castle'
            elif 'ринок' in territory_name.lower() or 'market' in territory_name.lower():
                territory_type = 'market'
            elif 'фортец' in territory_name.lower() or 'fortress' in territory_name.lower():
                territory_type = 'fortress'
            elif 'храм' in territory_name.lower() or 'temple' in territory_name.lower():
                territory_type = 'temple'
            
            territory_id = create_territory(territory_name, territory_type)
            if territory_id:
                territory = get_territory(territory_id)
        
        if not territory:
            bot.reply_to(message, "❌ Помилка створення території!")
            return
        
        # Захоплення
        if capture_territory(territory['id'], user_guild['id']):
            bot.reply_to(message, f"✅ {territory['name']} захоплено гільдією {user_guild['name']}!")
        else:
            bot.reply_to(message, "❌ Помилка захоплення!")
            
    except Exception as e:
        logger.error(f"❌ Помилка /guild_capture: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_income'])
def guild_income_cmd(message):
    """Зібрати дохід з територій"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        income = collect_territory_income(user_guild['id'])

        # Додаємо до скарбниці гільдії
        from db import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE guilds SET coins = coins + %s WHERE id = %s
            ''', (income['coins'], user_guild['id']))
            conn.commit()
            cursor.close()
            conn.close()

        text = f"💰 **ДОХІД ЗБРАНО!**\n\n"
        text += f"🪙 Монети: +{income['coins']} (в скарбницю гільдії)\n"
        text += f"⭐ XP: +{income['xp']} (власнику)\n"

        if income['coins'] > 0 or income['xp'] > 0:
            # XP йде власнику хто зібрав
            from db import update_user_currency
            current_currency = get_user_currency(user_id, chat_id)
            new_xp = current_currency.get('xp', 0) + income['xp']
            update_user_currency(user_id, chat_id, xp=new_xp)

            text += f"\n💰 Скарбниця гільдії: +{income['coins']}\n⭐ Твій XP: +{income['xp']}"

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /guild_income: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_withdraw_coins'])
def guild_withdraw_coins_cmd(message):
    """Вивести монети зі скарбниці гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_withdraw_coins <сума>")
            return

        amount = int(parts[1])
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        # Перевірка прав (тільки owner/officer)
        from db import get_guild_members
        members = get_guild_members(user_guild['id'])
        user_role = None
        for m in members:
            if m['user_id'] == user_id:
                user_role = m['role']
                break

        if user_role not in ['owner', 'officer']:
            bot.reply_to(message, "❌ Тільки owner або officer можуть виводити монети!")
            return

        # Перевірка скарбниці
        from db import get_connection
        conn = get_connection()
        if not conn:
            bot.reply_to(message, "❌ Помилка БД!")
            return

        cursor = conn.cursor()
        cursor.execute('SELECT coins FROM guilds WHERE id = %s', (user_guild['id'],))
        row = cursor.fetchone()
        guild_coins = int(row[0]) if row else 0

        if guild_coins < amount:
            bot.reply_to(message, f"❌ Недостатньо монет в скарбниці! Є: {guild_coins}")
            cursor.close()
            conn.close()
            return

        # Виводимо монети
        cursor.execute('''
            UPDATE guilds SET coins = coins - %s WHERE id = %s
        ''', (amount, user_guild['id']))

        # Додаємо гравцю
        current_currency = get_user_currency(user_id, chat_id)
        new_coins = current_currency.get('coins', 0) + amount
        update_user_currency(user_id, chat_id, coins=new_coins)

        conn.commit()
        cursor.close()
        conn.close()

        bot.reply_to(message, f"""✅ **ВИВЕДЕНО МОНЕТИ!**

💰 Виведено: {amount} монет
💵 Скарбниця гільдії: {guild_coins - amount} монет
💰 Твій баланс: +{amount} монет""")

    except ValueError:
        bot.reply_to(message, "❌ Невірна сума!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_withdraw_coins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_chest'])
def guild_chest_cmd(message):
    """Показати вміст гільдійної скриньки"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        items = get_guild_chest(user_guild['id'])
        
        if not items:
            bot.reply_to(message, "📦 **СКРИНЬКА ГІЛЬДІЇ**\n\nСкринька пуста!\n\nВнеси предмети: /guild_donate")
            return
        
        text = f"📦 **СКРИНЬКА ГІЛЬДІЇ** {user_guild['name']}\n\n"
        
        for item in items[:20]:
            text += f"• {item['item_name']} x{item['quantity']}\n"
            text += f"  Вніс: {item['donor_name'] or 'Невідомо'}\n\n"
        
        if len(items) > 20:
            text += f"... і ще {len(items) - 20} предметів\n"
        
        text += "\n**Команди:**\n"
        text += "/guild_donate <предмет> <кількість> - внести\n"
        text += "/guild_withdraw <ID> <кількість> - вивести"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_chest: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_items'])
def guild_items_cmd(message):
    """Показати предмети гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Оновлюємо username користувача
        username = message.from_user.username or message.from_user.first_name or str(user_id)
        from db import update_user_username
        update_user_username(user_id, username)

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        # Отримуємо предмети з нової таблиці guild_items
        from db import get_connection
        conn = get_connection()
        if not conn:
            bot.reply_to(message, "❌ Помилка БД!")
            return

        cursor = conn.cursor()
        # Тепер JOIN працює оскільки додано колонку username в user_languages
        cursor.execute('''
            SELECT gi.id, gi.guild_id, gi.item_type, gi.item_name, gi.rarity,
                   gi.bonus_type, gi.bonus_value, gi.quantity,
                   gi.donated_by_user_id, gi.donated_at,
                   u.username as donor_name
            FROM guild_items gi
            LEFT JOIN user_languages u ON gi.donated_by_user_id = u.user_id
            WHERE gi.guild_id = %s
            ORDER BY
                CASE gi.rarity
                    WHEN 'mythic' THEN 1
                    WHEN 'legendary' THEN 2
                    WHEN 'epic' THEN 3
                    WHEN 'rare' THEN 4
                    ELSE 5
                END,
                gi.bonus_value DESC
        ''', (user_guild['id'],))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            bot.reply_to(message, "🎒 ПРЕДМЕТИ ГІЛЬДІЇ\n\nНемає предметів!\n\nВнеси предмети: /guild_donate_item")
            return

        text = f"🎒 ПРЕДМЕТИ ГІЛЬДІЇ {user_guild['name']}\n\n"

        rarity_emojis = {'mythic': '🔴', 'legendary': '🟡', 'epic': '🟣', 'rare': '🔵', 'common': '⚪'}
        type_names = {'weapon': 'Зброя', 'armor': 'Броня', 'accessory': 'Аксесуар', 'consumable': 'Споживне', 'special': 'Особливе'}

        for i, row in enumerate(rows[:20], 1):
            item_id = int(row[0])
            item_name = row[3]
            rarity = row[4]
            bonus_type = row[5]
            bonus_value = int(row[6]) if row[6] else 0
            quantity = int(row[7]) if row[7] else 0
            donor_id = row[8]
            donor_name = row[10] or f"ID {donor_id}"

            emoji = rarity_emojis.get(rarity, '⚪')
            type_name = type_names.get(row[2], row[2])
            bonus_text = f"+{bonus_value} {bonus_type}" if bonus_type else ""

            text += f"{i}. {emoji} **{item_name}** ({type_name}) x{quantity}\n"
            text += f"   ID: `{item_id}` | Вніс: {donor_name}\n"
            if bonus_text:
                text += f"   {bonus_text}\n"
            text += "\n"

        if len(rows) > 20:
            text += f"... і ще {len(rows) - 20} предметів\n"

        text += "\nКоманди:\n"
        text += "/guild_claim_item <ID> <кількість> - вивести в інвентар\n"
        text += "/guild_donate_item <предмет> <кількість> - внести"

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /guild_items: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_claim_item'])
def guild_claim_item_cmd(message):
    """Вивести предмет з гільдійної скриньки в особистий інвентар"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_claim_item <ID предмета> [кількість]")
            return
        
        item_id = int(parts[1])
        quantity = int(parts[2]) if len(parts) > 2 else 1
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Виводимо предмет
        result = withdraw_guild_item_to_user(user_guild['id'], user_id, chat_id, item_id, quantity)
        
        if result.get('success'):
            item = result.get('item', {})
            rarity_emoji = ITEM_RARITIES.get(item.get('rarity'), {}).get('color', '⚪')
            
            text = f"✅ **ПРЕДМЕТ ОТРИМАНО!**\n\n"
            text += f"{rarity_emoji} {item.get('name')}\n"
            text += f"Тип: {item.get('type')}\n"
            text += f"Рідкість: {item.get('rarity')}\n"
            if item.get('bonus_type'):
                text += f"Бонус: +{item.get('bonus_value')} {item.get('bonus_type')}\n"
            text += f"Кількість: x{quantity}\n\n"
            text += f"Предмет додано до твого інвентарю!\n"
            text += f"Використай /inventory для перегляду"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Помилка: {result.get('error', 'Невідома помилка')}")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID або кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_claim_item: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['use_item'])
def use_item_cmd(message):
    """Використати предмет для бафу"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /use_item <ID предмета>")
            return

        item_id = parts[1]

        # Спочатку пробуємо знайти предмет в shop інвентарі (user_inventory)
        inventory = get_user_inventory(user_id, chat_id)
        inv_item = None
        for inv in inventory:
            if inv['item_id'] == item_id and inv['quantity'] > 0:
                inv_item = inv
                break

        if inv_item:
            # Це shop предмет — обробляємо вручну
            item = get_item(item_id)
            if not item:
                bot.reply_to(message, "❌ Предмет не знайдено!")
                return

            # Видаляємо з інвентарю
            remove_from_inventory(user_id, chat_id, item_id, 1)

            # Обробка ефекту предмета
            if item_id == 'energy':
                # Знімаємо кулдаун з годування
                hryak = get_hryak(user_id, chat_id)
                if hryak:
                    save_hryak_to_db(user_id, chat_id, {'last_feed': 0})
                    text = f"⚡ **{item['name']} використано!**\n\nТепер можна годувати хряка!"
                else:
                    text = "❌ У тебе немає хряка!"
            elif item_id == 'spermobak':
                # Знімаємо кулдаун з трахену
                from db import get_connection
                import time as time_module
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    old_time = int(time_module.time()) - 86400
                    cursor.execute('''
                        UPDATE trachenzebiten
                        SET created_at = %s
                        WHERE user_id = %s AND chat_id = %s
                        AND id = (
                            SELECT id FROM trachenzebiten
                            WHERE user_id = %s AND chat_id = %s
                            ORDER BY id DESC LIMIT 1
                        )
                    ''', (old_time, user_id, chat_id, user_id, chat_id))
                    affected = cursor.rowcount
                    conn.commit()
                    cursor.close()
                    conn.close()
                    if affected > 0:
                        text = f"🧪 **{item['name']} використано!**\n\nТепер можна використовувати /trachen та /breed!"
                    else:
                        text = f"🧪 **{item['name']} використано!**\n\nУ вас немає активного кулдауну."
                else:
                    text = "❌ Помилка БД!"
            elif item_id == 'pastors_milk':
                # Знімаємо кулдаун з тренування дітей
                from db import get_connection
                import time as time_module
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    old_time = int(time_module.time()) - 86400
                    cursor.execute('''
                        UPDATE hryak_genes
                        SET last_train = %s
                        WHERE user_id = %s
                    ''', (old_time, user_id))
                    affected = cursor.rowcount
                    conn.commit()
                    cursor.close()
                    conn.close()
                    if affected > 0:
                        text = f"🥛 **{item['name']} використано!**\n\nТепер можна тренувати дітей!"
                    else:
                        text = f"🥛 **{item['name']} використано!**\n\nУ вас немає активного кулдауну."
                else:
                    text = "❌ Помилка БД!"
            else:
                # Стандартний баф
                text = f"✅ **{item['name']} використано!**\n\n"
                text += f"✨ Ефект: {item['description']}"

            bot.reply_to(message, text, parse_mode="Markdown")

        else:
            # Пробуємо як user_items (loot/traded items)
            try:
                numeric_item_id = int(item_id)
            except ValueError:
                bot.reply_to(message, f"❌ Предмет '{item_id}' не знайдено в інвентарі!")
                return

            result = use_item(user_id, chat_id, numeric_item_id)

            if result.get('success'):
                bonus_type = result.get('bonus_type', '')
                item_name = result.get('item_name', '')

                if bonus_type == 'remove_cooldown':
                    hryak = get_hryak(user_id, chat_id)
                    if hryak:
                        save_hryak_to_db(user_id, chat_id, {'last_feed': 0})
                        text = f"⚡ **{item_name} використано!**\n\nТепер можна годувати хряка!"
                    else:
                        text = "❌ У тебе немає хряка!"
                elif bonus_type == 'remove_trachen_cooldown':
                    from db import get_connection
                    import time as time_module
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        old_time = int(time_module.time()) - 86400
                        cursor.execute('''
                            UPDATE trachenzebiten
                            SET created_at = %s
                            WHERE user_id = %s AND chat_id = %s
                            AND id = (
                                SELECT id FROM trachenzebiten
                                WHERE user_id = %s AND chat_id = %s
                                ORDER BY id DESC LIMIT 1
                            )
                        ''', (old_time, user_id, chat_id, user_id, chat_id))
                        affected = cursor.rowcount
                        conn.commit()
                        cursor.close()
                        conn.close()
                        if affected > 0:
                            text = f"🧪 **{item_name} використано!**\n\nТепер можна /trachen та /breed!"
                        else:
                            text = f"🧪 **{item_name} використано!**\n\nНемає активного кулдауну."
                    else:
                        text = "❌ Помилка БД!"
                elif bonus_type == 'remove_child_train_cooldown':
                    from db import get_connection
                    import time as time_module
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        old_time = int(time_module.time()) - 86400
                        cursor.execute('''
                            UPDATE hryak_genes
                            SET last_train = %s
                            WHERE user_id = %s
                        ''', (old_time, user_id))
                        affected = cursor.rowcount
                        conn.commit()
                        cursor.close()
                        conn.close()
                        if affected > 0:
                            text = f"🥛 **{item_name} використано!**\n\nТепер можна тренувати дітей!"
                        else:
                            text = f"🥛 **{item_name} використано!**\n\nНемає активного кулдауну."
                    else:
                        text = "❌ Помилка БД!"
                else:
                    duration_hours = result.get('duration', 3600) / 3600
                    text = f"✅ **ПРЕДМЕТ ВИКОРИСТАНО!**\n\n"
                    text += f"🎒 {item_name}\n"
                    text += f"✨ Ефект: {result.get('effect')}\n"
                    text += f"⏰ Тривалість: {duration_hours:.1f} год"

                bot.reply_to(message, text, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Помилка: {result.get('error', 'Предмет не знайдено')}")

    except Exception as e:
        logger.error(f"❌ Помилка /use_item: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_donate'])
def guild_donate_cmd(message):
    """Внести предмет до скриньки"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /guild_donate <предмет> <кількість>")
            return

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        item_name = parts[1]
        quantity = int(parts[2])

        if quantity <= 0:
            bot.reply_to(message, "❌ Кількість має бути додатною!")
            return

        username = message.from_user.username or message.from_user.first_name or str(user_id)
        if donate_to_chest(user_guild['id'], user_id, 'item', item_name, quantity, username):
            bot.reply_to(message, f"✅ Внесено {item_name} x{quantity} до скриньки!")
        else:
            bot.reply_to(message, "❌ Помилка внеску!")

    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_donate: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_withdraw'])
def guild_withdraw_cmd(message):
    """Вивести предмет з гільдійної скриньки"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /guild_withdraw <ID предмета> <кількість>")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка прав
        members = get_guild_members(user_guild['id'])
        is_leader = False
        for m in members:
            if m['user_id'] == user_id and m['role'] in ['owner', 'officer']:
                is_leader = True
                break
        
        if not is_leader:
            bot.reply_to(message, "❌ Тільки лідер або офіцер може виводити предмети!")
            return
        
        item_id = int(parts[1])
        quantity = int(parts[2])
        
        if withdraw_from_chest(user_guild['id'], item_id, quantity):
            bot.reply_to(message, f"✅ Виведено {quantity} предметів зі скриньки!")
        else:
            bot.reply_to(message, "❌ Помилка виводу або недостатньо предметів!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID або кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_withdraw: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ГІЛЬДІЙНІ ВІЙНИ - КОМАНДИ ВІЙН
# ============================================

@bot.message_handler(commands=['guild_war_declare'])
def guild_war_declare_cmd(message):
    """Оголосити війну"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_war_declare <гільдія>")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка що це лідер або офіцер
        members = get_guild_members(user_guild['id'])
        is_leader = False
        for m in members:
            if m['user_id'] == user_id and m['role'] in ['owner', 'officer']:
                is_leader = True
                break
        
        if not is_leader:
            bot.reply_to(message, "❌ Тільки лідер або офіцер може оголосити війну!")
            return
        
        # Знаходимо гільдію суперника
        enemy_guild = get_guild_by_name(parts[1])
        if not enemy_guild:
            bot.reply_to(message, "❌ Гільдію не знайдено!")
            return
        
        if enemy_guild['id'] == user_guild['id']:
            bot.reply_to(message, "❌ Не можна оголосити війну собі!")
            return
        
        # Перевірка на вже активну війну
        active_wars = get_active_wars(user_guild['id'])
        if len(active_wars) >= 3:
            bot.reply_to(message, "❌ Максимум 3 активні війни!")
            return
        
        # Оголошуємо війну
        war_id = declare_war(user_guild['id'], enemy_guild['id'])
        
        if war_id:
            text = f"⚔️ **ВІЙНА ОГОЛОШЕНА!**\n\n"
            text += f"🔴 {user_guild['name']} проти 🔵 {enemy_guild['name']}\n\n"
            text += f"ID війни: {war_id}\n"
            text += f"Тривалість: 7 днів\n\n"
            text += "Використовуйте /guild_war_join для приєднання!\n"
            text += "/guild_war_battle для битви!"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Помилка оголошення війни!")
            
    except Exception as e:
        logger.error(f"❌ Помилка /guild_war_declare: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_war_join'])
def guild_war_join_cmd(message):
    """Приєднатися до війни"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        wars = get_active_wars(user_guild['id'])
        
        if not wars:
            bot.reply_to(message, "⚔️ Немає активних воєн!")
            return
        
        text = "⚔️ **АКТИВНІ ВІЙНИ**\n\n"
        
        for war in wars:
            text += f"ID: {war['id']}\n"
            text += f"{war['attacker_name']} 🔴 vs 🔵 {war['defender_name']}\n"
            text += f"Рахунок: {war['attacker_score']} - {war['defender_score']}\n\n"
        
        # Автоматично приєднуємо до всіх воєн
        joined_count = 0
        for war in wars:
            if join_war(war['id'], user_id, user_guild['id']):
                joined_count += 1
        
        text += f"\n✅ Ви приєдналися до {joined_count} воєн!"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_war_join: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_war_battle'])
def guild_war_battle_cmd(message):
    """Битися у війні"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        wars = get_active_wars(user_guild['id'])
        
        if not wars:
            bot.reply_to(message, "⚔️ Немає активних воєн!")
            return
        
        # Отримуємо хряка для розрахунку внеску
        hryak = get_hryak(user_id, chat_id)
        
        if not hryak:
            bot.reply_to(message, "❌ У тебе немає хряка!")
            return
        
        # Битва в кожній війні
        total_contribution = 0
        
        for war in wars:
            # Розрахунок внеску (вага хряка * 2)
            contribution = hryak['weight'] * 2
            add_war_contribution(war['id'], user_id, user_guild['id'], contribution)
            total_contribution += contribution
        
        text = f"⚔️ **БИТВА ВІДБУЛАСЯ!**\n\n"
        text += f"Ваш внесок: {total_contribution} очок\n"
        
        if total_contribution > 0:
            add_coins(user_id, chat_id, 50)
            add_xp(user_id, chat_id, 25)
            text += "💰 +50 монет\n"
            text += "⭐ +25 XP\n"
        
        text += "\nКулдаун: 24 години"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_war_battle: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_war_status'])
def guild_war_status_cmd(message):
    """Показати статус воєн"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        wars = get_active_wars(user_guild['id'])
        
        if not wars:
            bot.reply_to(message, "⚔️ Немає активних воєн!")
            return
        
        text = "⚔️ **ВІЙНИ ГІЛЬДІЇ**\n\n"
        
        for war in wars:
            text += f"ID: {war['id']}\n"
            text += f"{war['attacker_name']} 🔴 vs 🔵 {war['defender_name']}\n"
            text += f"Рахунок: {war['attacker_score']} - {war['defender_score']}\n"
            
            # Рахуємо днів до кінця
            days_left = 7 - int((time.time() - war['started_at']) / 86400)
            text += f"Залишилось днів: {max(0, days_left)}\n\n"
        
        text += "\n**Команди:**\n"
        text += "/guild_war_battle - битися (щодня)\n"
        text += "/guild_war_join - приєднатися"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_war_status: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ГІЛЬДІЙНІ БОСИ - КОМАНДИ
# ============================================

@bot.message_handler(commands=['guild_boss_spawn'])
def guild_boss_spawn_cmd(message):
    """Спавнити боса гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /guild_boss_spawn <ім'я> <рівень>")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка прав
        members = get_guild_members(user_guild['id'])
        is_leader = False
        for m in members:
            if m['user_id'] == user_id and m['role'] in ['owner', 'officer']:
                is_leader = True
                break
        
        if not is_leader:
            bot.reply_to(message, "❌ Тільки лідер або офіцер може спавнити боса!")
            return
        
        boss_name = parts[1]
        boss_level = int(parts[2])
        
        if boss_level < 1 or boss_level > 100:
            bot.reply_to(message, "❌ Рівень має бути від 1 до 100!")
            return
        
        # Розрахунок статів
        health = boss_level * 1000
        damage = boss_level * 50
        reward_coins = boss_level * 500
        reward_xp = boss_level * 250
        
        # Перевірка вартості (1000 монет за спавн)
        currency = get_user_currency(user_id, chat_id)
        if currency.get('coins', 0) < 1000:
            bot.reply_to(message, "❌ Недостатньо монет! Потрібно 1000 монет.")
            return
        
        # Списуємо монети
        update_user_currency(user_id, chat_id, coins=currency['coins'] - 1000)
        
        boss_id = spawn_guild_boss(boss_name, boss_level, health, damage, reward_coins, reward_xp, user_guild['id'])
        
        if boss_id:
            text = f"🐲 **БОС СПАВНЕНИЙ!**\n\n"
            text += f"Ім'я: {boss_name}\n"
            text += f"⭐ Рівень: {boss_level}\n"
            text += f"❤️ Здоров'я: {health}\n"
            text += f"⚔️ Шкода: {damage}\n"
            text += f"💰 Нагорода: {reward_coins} монет + {reward_xp} XP\n\n"
            text += "Атакуйте: /guild_boss_attack"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Помилка спавну!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірний рівень!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_boss_spawn: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_boss_attack'])
def guild_boss_attack_cmd(message):
    """Атакувати боса гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        # Отримуємо хряка
        hryak = get_hryak(user_id, chat_id)

        if not hryak:
            bot.reply_to(message, "❌ У тебе немає хряка!")
            return

        # Знаходимо активного боса гільдії
        boss = get_active_guild_boss(user_guild['id'])

        if not boss:
            bot.reply_to(message, """🐲 **НЕМАЄ АКТИВНОГО БОСА**

Ваша гільдія ще не має активного боса.

**Спавнити боса:**
/guild_boss_spawn <ім'я> <рівень>

**Вартість:** 1000 монет""")
            return

        # Перевіряємо кулдаун (2 години між атаками)
        last_attack = get_last_guild_boss_attack_time(user_id, boss['id'])
        now = int(time.time())

        if last_attack and (now - last_attack) < 7200:
            hours_left = int((7200 - (now - last_attack)) / 3600)
            minutes_left = int((7200 - (now - last_attack)) / 60) % 60
            bot.reply_to(message, f"⏰ **КУЛДАУН**\n\nВи вже атакували цього боса!\n\nЗалишилося: {hours_left} год {minutes_left} хв")
            return

        # Розрахунок шкоди
        damage = hryak['weight'] * 2

        # Атакуємо боса
        result = attack_guild_boss(boss['id'], user_id, user_guild['id'], damage)

        if not result:
            bot.reply_to(message, "❌ Помилка атаки!")
            return

        # Зберігаємо час атаки
        save_guild_boss_attack_time(user_id, boss['id'], now)

        if result.get('defeated'):
            # Бос переможений - видаємо нагороди
            participants = get_guild_boss_participants(boss['id'])
            total_damage = sum(p['damage_dealt'] for p in participants)

            # Знаходимо хто завдав останнього удару
            top_participant = max(participants, key=lambda x: x['damage_dealt'])

            text = f"""🎉 **БОСА ПЕРЕМОЖЕНО!**

{boss['name']} загинув від рук героїв гільдії!
Останній удар: {top_participant.get('username', f'ID {top_participant["user_id"]}')}

🏆 **Топ гравців:**
"""
            sorted_participants = sorted(participants, key=lambda x: x['damage_dealt'], reverse=True)[:5]
            for i, p in enumerate(sorted_participants, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
                damage_percent = (p['damage_dealt'] / total_damage * 100) if total_damage > 0 else 0
                username = p.get('username', 'ID {}'.format(p['user_id']))
                text += "{} {}. {} - {:.1f}% ({} шкоди)\n".format(medal, i, username, damage_percent, p['damage_dealt'])

            # Видаємо нагороди
            for p in participants:
                if p['damage_dealt'] > 0:
                    reward_share = p['damage_dealt'] / total_damage
                    coins_reward = int(boss['reward_coins'] * reward_share)
                    xp_reward = int(boss['reward_xp'] * reward_share)

                    if coins_reward > 0:
                        add_coins(p['user_id'], chat_id, coins_reward)
                    if xp_reward > 0:
                        add_xp(p['user_id'], chat_id, xp_reward)

            text += f"""

💰 **Нагороди розподілено!**
Кожен отримав монети та XP за % урону.

🐲 **Новий бос:**
Спавніть нового боса: /guild_boss_spawn"""

            bot.reply_to(message, text, parse_mode="Markdown")

        else:
            # Бос ще живий
            remaining = result.get('remaining_health', boss['health'])
            max_health = result.get('max_health', boss['max_health'])
            hp_percent = int((remaining / max_health) * 100)
            hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

            bot.reply_to(message, f"""⚔️ **АТАКА!**

Твій хряк {hryak['name']} завдав {damage} шкоди!

🐲 {boss['name']}
❤️ {remaining}/{max_health} ({hp_percent}%)
{hp_bar}

⏰ Наступна атака через 2 години!

Продовжуй атакувати: /guild_boss_attack""")

    except Exception as e:
        logger.error(f"❌ Помилка /guild_boss_attack: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_boss_info'])
def guild_boss_info_cmd(message):
    """Інформація про боса гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        boss = get_active_guild_boss(user_guild['id'])

        if not boss:
            bot.reply_to(message, """🐲 **НЕМАЄ АКТИВНОГО БОСА**

Ваша гільдія ще не має активного боса.

**Спавнити боса:**
/guild_boss_spawn <ім'я> <рівень>

**Вартість:** 1000 монет""")
            return

        hp_percent = int((boss['health'] / boss['max_health']) * 100)
        hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

        participants = get_guild_boss_participants(boss['id'])

        text = f"""🐲 {boss['name']}

⭐ Рівень: {boss['level']}
🏆 Перемог: {boss.get('defeat_count', 0)}
❤️ Здоров'я: {boss['health']}/{boss['max_health']}
{hp_bar} {hp_percent}%
⚔️ Шкода: {boss['damage']}
💰 Нагорода: {boss['reward_coins']} монет + {boss['reward_xp']} XP

**Топ гравців:**
"""
        for i, p in enumerate(participants[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
            username = p.get('username', 'ID {}'.format(p['user_id']))
            text += "{} {}. {} - {} шкоди\n".format(medal, i, username, p['damage_dealt'])

        text += f"""

**Команди:**
/guild_boss_attack - атакувати боса
/guild_boss_info - інформація про боса

**Як це працює:**
1. Кожен гравець може атакувати боса
2. Шкода = вага хряка × 2
3. Кулдаун між атаками: 2 години
4. Нагороди розподіляються за % урону
5. Після перемоги можна спавнити нового боса"""

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /guild_boss_info: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ГІЛЬДІЙНІ ВОЇНИ - КОМАНДИ
# ============================================

@bot.message_handler(commands=['guild_warriors'])
def guild_warriors_cmd(message):
    """Показати всіх воїнів гільдії"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        warriors = get_guild_warriors(user_guild['id'])
        total = get_total_warrior_power(user_guild['id'])
        
        if not warriors:
            bot.reply_to(message, "🪖 **АРМІЯ ГІЛЬДІЇ**\n\nУ вас ще немає воїнів!\n\nКупіть воїнів: /guild_buy_warrior")
            return
        
        text = f"🪖 **АРМІЯ ГІЛЬДІЇ** {user_guild['name']}\n\n"
        text += f"💪 Загальна сила: {total['total_power']}\n"
        text += f"👥 Всього воїнів: {total['total_quantity']}\n\n"
        
        warrior_emojis = {'regular': '🐷', 'matochnik': '🐗', 'elite': '⚔️', 'legendary': '👑'}
        
        for w in warriors:
            emoji = warrior_emojis.get(w['warrior_type'], '🐷')
            name = WARRIOR_TYPES.get(w['warrior_type'], {}).get('name', 'Свинар')
            text += f"{emoji} **{name}** x{w['quantity']}\n"
            text += f"   Сила: {w['power']} ({w['power'] // w['quantity']} на воїна)\n\n"
        
        text += "\n**Команди:**\n"
        text += "/guild_buy_warrior <тип> <кількість> - купити\n"
        text += "/guild_defend <територія> <тип> <кількість> - захист"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_warriors: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_buy_warrior'])
def guild_buy_warrior_cmd(message):
    """Купити воїнів"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /guild_buy_warrior <тип> <кількість>\n\nТипи: regular, matochnik, elite, legendary")
            return

        warrior_type = parts[1].lower()
        quantity = int(parts[2])

        if warrior_type not in WARRIOR_TYPES:
            bot.reply_to(message, f"❌ Невірний тип! Доступні: {', '.join(WARRIOR_TYPES.keys())}")
            return

        if quantity <= 0 or quantity > 1000:
            bot.reply_to(message, "❌ Кількість має бути від 1 до 1000!")
            return

        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return

        # Перевірка прав (тільки owner/officer)
        from db import get_guild_members
        members = get_guild_members(user_guild['id'])
        user_role = None
        for m in members:
            if m['user_id'] == user_id:
                user_role = m['role']
                break

        if user_role not in ['owner', 'officer']:
            bot.reply_to(message, "❌ Тільки власник або офіцер можуть купувати воїнів!")
            return

        # Розрахунок вартості
        warrior_data = WARRIOR_TYPES.get(warrior_type, {})
        total_cost = warrior_data.get('cost', 100) * quantity

        # Перевірка балансу гільдії
        from db import get_connection
        conn = get_connection()
        if not conn:
            bot.reply_to(message, "❌ Помилка БД!")
            return
        
        cursor = conn.cursor()
        cursor.execute('SELECT coins FROM guilds WHERE id = %s', (user_guild['id'],))
        row = cursor.fetchone()
        guild_coins = int(row[0]) if row else 0

        if guild_coins < total_cost:
            bot.reply_to(message, f"❌ Недостатньо монет в гільдії! Потрібно {total_cost} монет.\nВ гільдії: {guild_coins} монет")
            cursor.close()
            conn.close()
            return

        # Списуємо монети з гільдії
        cursor.execute('''
            UPDATE guilds SET coins = coins - %s WHERE id = %s
        ''', (total_cost, user_guild['id']))
        conn.commit()
        cursor.close()
        conn.close()

        # Купуємо воїнів
        if buy_warrior(user_guild['id'], warrior_type, quantity):
            emoji = warrior_data.get('emoji', '🐷')
            name = warrior_data.get('name', 'Свинар')
            bot.reply_to(message, f"""✅ Куплено воїнів!

{quantity} x {emoji} {name}
💰 Витрачено: {total_cost} монет (з гільдії)
💵 Залишок гільдії: {guild_coins - total_cost} монет""")
        else:
            bot.reply_to(message, "❌ Помилка купівлі!")

    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_buy_warrior: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_defend'])
def guild_defend_cmd(message):
    """Розмістити воїнів на захист території"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ Використання: /guild_defend <територія> <тип> <кількість>")
            return
        
        territory_name = parts[1]
        warrior_type = parts[2].lower()
        warrior_count = int(parts[3])
        
        if warrior_type not in WARRIOR_TYPES:
            bot.reply_to(message, f"❌ Невірний тип! Доступні: {', '.join(WARRIOR_TYPES.keys())}")
            return
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка що воїни є
        warriors = get_guild_warriors(user_guild['id'])
        has_warriors = False
        for w in warriors:
            if w['warrior_type'] == warrior_type and w['quantity'] >= warrior_count:
                has_warriors = True
                break
        
        if not has_warriors:
            bot.reply_to(message, "❌ У вас немає стільки воїнів цього типу!")
            return
        
        # Знаходимо територію
        territories = get_all_territories()
        territory = None
        for t in territories:
            if t['name'].lower() == territory_name.lower():
                territory = t
                break
        
        if not territory:
            bot.reply_to(message, "❌ Територію не знайдено!")
            return
        
        # Перевірка що територія належить гільдії
        if territory.get('owner_guild_id') != user_guild['id']:
            bot.reply_to(message, "❌ Ця територія не належить вашій гільдії!")
            return
        
        # Розміщуємо воїнів
        if station_warriors(territory['id'], user_guild['id'], warrior_type, warrior_count):
            # Видаляємо воїнів з гільдії
            remove_warriors_from_guild(user_guild['id'], warrior_type, warrior_count)
            
            emoji = WARRIOR_TYPES.get(warrior_type, {}).get('emoji', '🐷')
            name = WARRIOR_TYPES.get(warrior_type, {}).get('name', 'Свинар')
            bot.reply_to(message, f"✅ {warrior_count} x {emoji} {name} розміщено на захист {territory_name}!")
        else:
            bot.reply_to(message, "❌ Помилка розміщення!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /guild_defend: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_defense_info'])
def guild_defense_info_cmd(message):
    """Показати інформацію про захист території"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_defense_info <територія>")
            return
        
        territory_name = parts[1]
        
        # Знаходимо територію
        territories = get_all_territories()
        territory = None
        for t in territories:
            if t['name'].lower() == territory_name.lower():
                territory = t
                break
        
        if not territory:
            bot.reply_to(message, "❌ Територію не знайдено!")
            return
        
        defense = get_territory_defense(territory['id'])
        
        text = f"🏰 **ЗАХИТ ТЕРИТОРІЇ** {territory['name']}\n\n"
        text += f"💪 Загальна сила захисту: {defense['total_power']}\n\n"
        
        if not defense['defense']:
            text += "⚠️ Територія не захищена!"
        else:
            warrior_emojis = {'regular': '🐷', 'matochnik': '🐗', 'elite': '⚔️', 'legendary': '👑'}
            
            for d in defense['defense']:
                emoji = warrior_emojis.get(d['warrior_type'], '🐷')
                text += f"{emoji} {d['guild_name']}: {d['warrior_count']} воїнів (сила: {d['defense_power']})\n"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /guild_defense_info: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['guild_attack'])
def guild_attack_cmd(message):
    """Атакувати територію"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /guild_attack <територія>")
            return
        
        territory_name = parts[1]
        
        user_guild = get_user_guild(user_id, chat_id)
        if not user_guild:
            bot.reply_to(message, "❌ Ви не в гільдії!")
            return
        
        # Перевірка що є воїни
        attackers = get_total_warrior_power(user_guild['id'])
        if attackers['total_power'] <= 0:
            bot.reply_to(message, "❌ У вас немає воїнів для атаки!")
            return
        
        # Знаходимо територію
        territories = get_all_territories()
        territory = None
        for t in territories:
            if t['name'].lower() == territory_name.lower():
                territory = t
                break
        
        if not territory:
            bot.reply_to(message, "❌ Територію не знайдено!")
            return
        
        # Перевірка що це не своя територія
        if territory.get('owner_guild_id') == user_guild['id']:
            bot.reply_to(message, "❌ Не можна атакувати свою територію!")
            return
        
        # Отримуємо захист
        defense = get_territory_defense(territory['id'])
        defender_power = defense['total_power']
        
        # Розрахунок битви
        attacker_power = attackers['total_power']
        
        # Якщо атакуючих більше - перемога
        if attacker_power > defender_power:
            # Втрачаємо частину воїнів (пропорційно до захисту)
            loss_percent = defender_power / attacker_power if attacker_power > 0 else 0
            warriors_lost = int(attackers['total_quantity'] * loss_percent * 0.5)  # 50% від пропорції
            
            # Захоплюємо територію
            capture_territory(territory['id'], user_guild['id'])
            
            # Записуємо битву
            record_territory_battle(
                territory['id'], user_guild['id'], territory.get('owner_guild_id', 0),
                attackers['total_quantity'], defense.get('total_quantity', 0),
                warriors_lost, 0, user_guild['id']
            )
            
            text = f"🎉 **ПЕРЕМОГА!**\n\n"
            text += f"Територія {territory['name']} захоплена!\n"
            text += f"💪 Сила атаки: {attacker_power}\n"
            text += f"🛡️ Сила захисту: {defender_power}\n"
            text += f"💀 Втрачено воїнів: {warriors_lost}\n\n"
            text += "Територія тепер належить вашій гільдії!"
            
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            # Поразка - втрачаємо всіх воїнів
            text = f"💀 **ПОРАЗКА!**\n\n"
            text += f"Атака відбита!\n"
            text += f"💪 Сила атаки: {attacker_power}\n"
            text += f"🛡️ Сила захисту: {defender_power}\n\n"
            text += "Всі ваші воїни загинули в бою!"
            
            bot.reply_to(message, text, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Помилка /guild_attack: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ПРЕДМЕТИ ТА ІНВЕНТАР - КОМАНДИ
# ============================================

@bot.message_handler(commands=['item_trade'])
def item_trade_cmd(message):
    """Створити трейд предметами"""
    chat_id = message.chat.id
    sender_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 3 or not message.reply_to_message:
            bot.reply_to(message, """💱 ТРЕЙД ПРЕДМЕТАМИ

Використання: /item_trade <предмет> <кількість> (у відповідь на повідомлення)

Приклад:
1. Відповідь на повідомлення отримувача
2. /item_trade vitamins 5

Команди:
/item_trade <предмет> <кількість> - створити трейд
/item_trades - показати активні трейди
/item_accept <id> - прийняти
/item_cancel <id> - скасувати

Примітка: Скіни не можна трейдити через цю команду!""")
            return

        item_name = parts[1]
        quantity = int(parts[2]) if len(parts) > 2 else 1

        # Отримуємо отримувача
        receiver_id = message.reply_to_message.from_user.id

        if receiver_id == sender_id:
            bot.reply_to(message, "❌ Не можна торгувати з самим собою!")
            return

        # Перевіряємо чи є предмет в user_items (предмети з івентів/рейду)
        items = get_user_items(sender_id, chat_id)
        total_quantity = 0
        for item in items:
            if item['item_name'].lower() == item_name.lower():
                total_quantity += item['quantity']
        
        # Перевіряємо чи є предмет в user_inventory (предмети з магазину)
        inventory = get_user_inventory(sender_id, chat_id)
        for inv_item in inventory:
            # Перевіряємо за item_id та name
            if inv_item['item_id'].lower() == item_name.lower() or inv_item['name'].lower() == item_name.lower():
                total_quantity += inv_item['quantity']
        
        has_the_item = total_quantity >= quantity

        # Перевіряємо чи є предмет (скіни) - але скіни не можна трейдити
        if not has_the_item:
            # Перевіряємо чи це скін
            from db import get_user_skins
            skins = get_user_skins(sender_id, chat_id)
            for skin in skins:
                if skin['name'].lower() == item_name.lower():
                    bot.reply_to(message, f"""❌ Скіни не можна трейдити через /item_trade!

Для скінів використовуйте:
/equipskin {skin['name']} - одягнути
/buyskin {skin['name']} - купити іншому""")
                    return

        if not has_the_item:
            bot.reply_to(message, f"❌ У тебе немає предмета '{item_name}' в такій кількості!")
            return

        # Створюємо трейд
        sender_items = [{'name': item_name, 'quantity': quantity}]
        trade_id = create_item_trade(sender_id, receiver_id, chat_id, sender_items=sender_items)

        if trade_id:
            bot.reply_to(message, f"""💱 ТРЕЙД СТВОРЕНО!

Отримувач: ID {receiver_id}
Предмет: {item_name} x{quantity}

Отримувач має написати /item_accept {trade_id} щоб прийняти трейд.

⏰ Трейд дійсний 24 години.""")
        else:
            bot.reply_to(message, "❌ Помилка створення трейду!")

    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /item_trade: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['skintrade'])
def skin_trade_cmd(message):
    """Створити трейд скінами"""
    chat_id = message.chat.id
    sender_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2 or not message.reply_to_message:
            bot.reply_to(message, """💱 ТРЕЙД СКІНАМИ

Використання: /skintrade <скін> (у відповідь на повідомлення)

Приклад:
1. Відповідь на повідомлення отримувача
2. /skintrade wild

Команди:
/skintrade <скін> - створити трейд скіном
/skintrades - показати активні трейди скінів
/skinaccept <id> - прийняти трейд скіном
/skincancel <id> - скасувати трейд скіном""")
            return

        skin_name = parts[1].lower()
        quantity = 1  # Скіни трейдяться по 1

        # Отримуємо отримувача
        receiver_id = message.reply_to_message.from_user.id

        if receiver_id == sender_id:
            bot.reply_to(message, "❌ Не можна торгувати з самим собою!")
            return

        # Перевіряємо чи є скін
        from db import get_user_skins
        skins = get_user_skins(sender_id, chat_id)
        has_skin = False
        skin_to_trade = None
        
        for skin in skins:
            if skin['name'].lower() == skin_name and not skin['equipped']:
                has_skin = True
                skin_to_trade = skin
                break
        
        if not has_skin:
            if skin_to_trade is None:
                skin_list = '\n'.join([f"{s['icon']} {s['display_name']} (/{s['name']})" for s in skins])
                bot.reply_to(message, f"""❌ У тебе немає скіну '{skin_name}'!

Твої скіни:
{skin_list}

Примітка: Не можна трейдити одягнутий скін!""")
            else:
                bot.reply_to(message, "❌ Цей скін одягнутий! Зніми його перед трейдом:\n/equipskin classic")
            return

        # Створюємо трейд
        sender_skins = [{'name': skin_name, 'quantity': 1, 'skin_id': skin_to_trade['id']}]
        
        # Імпортуємо функцію для трейду скінів
        from db import create_skin_trade
        trade_id = create_skin_trade(sender_id, receiver_id, chat_id, sender_skins=sender_skins)

        if trade_id:
            bot.reply_to(message, f"""💱 ТРЕЙД СКІНОМ СТВОРЕНО!

Отримувач: ID {receiver_id}
Скін: {skin_to_trade['icon']} {skin_to_trade['display_name']}

Отримувач має написати /skinaccept {trade_id} щоб прийняти трейд.

⏰ Трейд дійсний 24 години.""")
        else:
            bot.reply_to(message, "❌ Помилка створення трейду!")

    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість!")
    except Exception as e:
        logger.error(f"❌ Помилка /skintrade: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['skintrades'])
def skin_trades_cmd(message):
    """Показати активні трейди скінами"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        from db import get_pending_skin_trades
        trades = get_pending_skin_trades(user_id)

        if not trades:
            bot.reply_to(message, "📭 Немає активних трейдів скінами!")
            return

        text = "💱 Активні трейди скінами:\n\n"

        for trade in trades:
            sender = "Ви" if trade['sender_id'] == user_id else f"ID {trade['sender_id']}"
            receiver = "Ви" if trade['receiver_id'] == user_id else f"ID {trade['receiver_id']}"
            
            text += f"ID: `{trade['id']}`\n"
            text += f"Від: {sender} → До: {receiver}\n"
            text += f"Створено: {time.strftime('%d.%m %H:%M', time.localtime(trade['created_at']))}\n\n"

        text += "Команди:\n"
        text += "/skinaccept <id> - прийняти\n"
        text += "/skincancel <id> - скасувати"

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /skintrades: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['skinaccept'])
def skin_accept_cmd(message):
    """Прийняти трейд скінами"""
    chat_id = message.chat.id
    receiver_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /skinaccept <ID трейду>")
            return

        trade_id = int(parts[1])

        from db import get_skin_trade, accept_skin_trade
        trade = get_skin_trade(trade_id)

        if not trade:
            bot.reply_to(message, "❌ Трейд не знайдено!")
            return

        # Перевіряємо чи це отримувач
        if trade['receiver_id'] != receiver_id:
            bot.reply_to(message, "❌ Це не ваш трейд!")
            return

        if trade['status'] != 'pending':
            bot.reply_to(message, "❌ Трейд вже оброблено!")
            return

        # Приймаємо трейд
        if accept_skin_trade(trade_id):
            # Передаємо скіни
            transferred_skins = []
            for skin_data in trade.get('sender_skins', []):
                skin_name = skin_data.get('name')  # Наприклад 'wild'
                
                # Знаходимо ID скіну в таблиці skins
                from db import get_skin_by_name
                skin = get_skin_by_name(skin_name)
                if not skin:
                    logger.error(f"❌ Скін '{skin_name}' не знайдено!")
                    continue
                
                skin_def_id = skin['id']  # ID з таблиці skins
                
                # Знаходимо запис в user_skins
                from db import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                
                # Шукаємо скін у відправника (не одягнутий)
                cursor.execute('''
                    SELECT id FROM user_skins
                    WHERE user_id = %s AND chat_id = %s AND skin_id = %s AND equipped = FALSE
                    ORDER BY id DESC LIMIT 1
                ''', (trade['sender_id'], chat_id, skin_def_id))
                user_skin_row = cursor.fetchone()
                
                if user_skin_row:
                    user_skin_id = int(user_skin_row[0])
                    # Змінюємо власника
                    cursor.execute('''
                        UPDATE user_skins SET user_id = %s, equipped = FALSE
                        WHERE id = %s
                    ''', (receiver_id, user_skin_id))
                    conn.commit()
                    transferred_skins.append(skin_name)
                    logger.info(f"✅ Скін {skin_name} (ID: {user_skin_id}) передано!")
                else:
                    logger.error(f"❌ Скін {skin_name} не знайдено у відправника!")
                
                cursor.close()
                conn.close()

            if transferred_skins:
                bot.reply_to(message, f"✅ Трейд {trade_id} прийнято!\n\nОтримано скіни: {', '.join(transferred_skins)}")
            else:
                bot.reply_to(message, f"❌ Трейд {trade_id} прийнято, але скіни не передано!")
        else:
            bot.reply_to(message, "❌ Помилка прийняття трейду!")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /skinaccept: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['skincancel'])
def skin_cancel_cmd(message):
    """Скасувати трейд скінами"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /skincancel <ID трейду>")
            return

        trade_id = int(parts[1])

        from db import get_skin_trade, cancel_skin_trade
        trade = get_skin_trade(trade_id)

        if not trade:
            bot.reply_to(message, "❌ Трейд не знайдено!")
            return

        # Перевіряємо чи це відправник
        if trade['sender_id'] != user_id:
            bot.reply_to(message, "❌ Це не ваш трейд!")
            return

        if trade['status'] != 'pending':
            bot.reply_to(message, "❌ Трейд вже оброблено!")
            return

        # Скасовуємо трейд
        if cancel_skin_trade(trade_id):
            bot.reply_to(message, f"✅ Трейд {trade_id} скасовано!")
        else:
            bot.reply_to(message, "❌ Помилка скасування трейду!")

    except ValueError:
        bot.reply_to(message, "❌ Невірний ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /skincancel: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['item_trades'])
def item_trades_cmd(message):
    """Показати активні трейди предметами"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        trades = get_pending_trades(user_id)
        
        if not trades:
            bot.reply_to(message, "📭 Немає активних трейдів предметами!")
            return
        
        text = "💱 **Активні трейди предметами:**\n\n"
        
        for trade in trades:
            sender = "Ви" if trade['sender_id'] == user_id else f"ID {trade['sender_id']}"
            receiver = "Ви" if trade['receiver_id'] == user_id else f"ID {trade['receiver_id']}"
            
            text += f"ID: `{trade['id']}`\n"
            text += f"Від: {sender} → До: {receiver}\n"
            text += f"Створено: {time.strftime('%d.%m %H:%M', time.localtime(trade['created_at']))}\n\n"
        
        text += "**Команди:**\n"
        text += "/item_accept <id> - прийняти\n"
        text += "/item_cancel <id> - скасувати"
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /item_trades: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['item_accept'])
def item_accept_cmd(message):
    """Прийняти трейд предметами"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /item_accept <ID трейду>")
            return
        
        trade_id = int(parts[1])
        trade = get_item_trade(trade_id)
        
        if not trade:
            bot.reply_to(message, "❌ Трейд не знайдено!")
            return
        
        # Перевіряємо чи це отримувач
        if trade['receiver_id'] != user_id:
            bot.reply_to(message, "❌ Це не ваш трейд!")
            return
        
        if trade['status'] != 'pending':
            bot.reply_to(message, "❌ Трейд вже оброблено!")
            return
        
        # Приймаємо трейд
        if accept_item_trade(trade_id):
            # Передаємо предмети
            for item in trade.get('sender_items', []):
                item_name = item['name']
                item_quantity = item.get('quantity', 1)
                
                # Додаємо предмети отримувачу (в user_items)
                add_item_to_user(
                    user_id, chat_id,
                    'item', item_name,
                    rarity='common',
                    quantity=item_quantity
                )
                
                # Видаляємо предмети у відправника
                # Спочатку пробуємо видалити з user_items
                removed = remove_user_item(
                    trade['sender_id'], chat_id,
                    item_name,
                    quantity=item_quantity,
                    item_type='item'
                )
                
                # Якщо не видалено, пробуємо з user_inventory
                if not removed:
                    remove_from_inventory(
                        trade['sender_id'], chat_id,
                        item_name,
                        quantity=item_quantity
                    )

            bot.reply_to(message, f"✅ Трейд {trade_id} прийнято!\n\nПредмети додано до інвентарю!")
        else:
            bot.reply_to(message, "❌ Помилка прийняття трейду!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /item_accept: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['item_cancel'])
def item_cancel_cmd(message):
    """Скасувати трейд предметами"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /item_cancel <ID трейду>")
            return
        
        trade_id = int(parts[1])
        trade = get_item_trade(trade_id)
        
        if not trade:
            bot.reply_to(message, "❌ Трейд не знайдено!")
            return
        
        # Перевіряємо чи це відправник
        if trade['sender_id'] != user_id:
            bot.reply_to(message, "❌ Це не ваш трейд!")
            return
        
        if trade['status'] != 'pending':
            bot.reply_to(message, "❌ Трейд вже оброблено!")
            return
        
        # Скасовуємо трейд
        if cancel_item_trade(trade_id):
            bot.reply_to(message, f"✅ Трейд {trade_id} скасовано!")
        else:
            bot.reply_to(message, "❌ Помилка скасування!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірний ID!")
    except Exception as e:
        logger.error(f"❌ Помилка /item_cancel: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# ПРИВАТНІ КАЗИНО - КОМАНДИ
# ============================================

@bot.message_handler(commands=['casino_create'])
def casino_create_cmd(message):
    """Створити власне казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, """🎰 **СТВОРЕННЯ КАЗИНО**

Використання: /casino_create <назва> [початкові монети]

Приклад: /casino_create Моє Казино 5000

**Вимоги:**
• Початкові монети: мінімум 1000
• Вартість створення: 500 монет""")
            return
        
        casino_name = parts[1]
        initial_coins = int(parts[2]) if len(parts) > 2 else 1000
        
        if initial_coins < 1000:
            bot.reply_to(message, "❌ Мінімальна кількість монет: 1000!")
            return
        
        # Перевірка балансу
        currency = get_user_currency(user_id, chat_id)
        if currency.get('coins', 0) < 500:
            bot.reply_to(message, "❌ Недостатньо монет! Потрібно 500 монет.")
            return
        
        # Перевірка чи вже є казино
        existing_casino = get_user_casino(user_id, chat_id)
        if existing_casino:
            bot.reply_to(message, "❌ У тебе вже є казино!")
            return
        
        # Списуємо монети за створення
        update_user_currency(user_id, chat_id, coins=currency['coins'] - 500)
        
        # Створюємо казино
        casino_id = create_casino(user_id, chat_id, casino_name, initial_coins)
        
        if casino_id:
            bot.reply_to(message, f"""🎉 **КАЗИНО СТВОРЕНО!**

🎰 Назва: {casino_name}
💰 Початкові монети: {initial_coins}
🎲 Вартість створення: 500 монет

**Команди:**
/casino - інформація про казино
/casino_deposit <сума> - внести монети
/casino_withdraw <сума> - вивести монети
/casino_limits - налаштувати обмеження
/casino_play <сума> - грати
/casino_stats - статистика""")
        else:
            bot.reply_to(message, "❌ Помилка створення казино!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірна кількість монет!")
    except Exception as e:
        logger.error(f"❌ Помилка /casino_create: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino'])
def casino_cmd(message):
    """Інформація про казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        casino = get_user_casino(user_id, chat_id)

        if not casino:
            bot.reply_to(message, "🎰 КАЗИНО\n\nУ тебе ще немає казино!\n\nСтвори: /casino_create <назва>")
            return

        # Екрануємо спеціальні символи в назві
        casino_name = casino['name'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

        text = f"""🎰 КАЗИНО: {casino_name}

💰 Монети в казино: {casino['casino_coins']}
🎲 Ставки:
   Мін: {casino['min_bet']} монет
   Макс: {casino['max_bet']} монет
🎯 Шанс виграшу: {casino['win_chance'] * 100:.1f}%

Команди:
/casino_deposit <сума> - внести монети
/casino_withdraw <сума> - вивести монети
/casino_limits - налаштувати
/casino_play <сума> - грати
/casino_stats - статистика"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /casino: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino_deposit'])
def casino_deposit_cmd(message):
    """Внести монети до казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /casino_deposit <сума>")
            return
        
        amount = int(parts[1])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        casino = get_user_casino(user_id, chat_id)
        if not casino:
            bot.reply_to(message, "❌ У тебе немає казино!")
            return
        
        # Перевірка балансу
        currency = get_user_currency(user_id, chat_id)
        if currency.get('coins', 0) < amount:
            bot.reply_to(message, "❌ Недостатньо монет!")
            return
        
        # Списуємо монети
        update_user_currency(user_id, chat_id, coins=currency['coins'] - amount)
        
        # Вносимо до казино
        if deposit_to_casino(casino['id'], amount):
            bot.reply_to(message, f"""✅ **ВНЕСЕНО ДО КАЗИНО!**

💰 Внесено: {amount} монет
💵 Баланс казино: {casino['casino_coins'] + amount} монет""")
        else:
            bot.reply_to(message, "❌ Помилка внесення!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірна сума!")
    except Exception as e:
        logger.error(f"❌ Помилка /casino_deposit: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino_withdraw'])
def casino_withdraw_cmd(message):
    """Вивести монети з казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /casino_withdraw <сума>")
            return
        
        amount = int(parts[1])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        casino = get_user_casino(user_id, chat_id)
        if not casino:
            bot.reply_to(message, "❌ У тебе немає казино!")
            return
        
        if casino['casino_coins'] < amount:
            bot.reply_to(message, "❌ Недостатньо монет в казино!")
            return
        
        # Виводимо з казино
        if withdraw_from_casino(casino['id'], amount):
            # Додаємо монети гравцю
            currency = get_user_currency(user_id, chat_id)
            update_user_currency(user_id, chat_id, coins=currency['coins'] + amount)
            
            bot.reply_to(message, f"""✅ **ВИВЕДЕНО З КАЗИНО!**

💰 Виведено: {amount} монет
💵 Баланс казино: {casino['casino_coins'] - amount} монет""")
        else:
            bot.reply_to(message, "❌ Помилка виводу!")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірна сума!")
    except Exception as e:
        logger.error(f"❌ Помилка /casino_withdraw: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino_limits'])
def casino_limits_cmd(message):
    """Налаштувати обмеження казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        casino = get_user_casino(user_id, chat_id)
        
        if not casino:
            bot.reply_to(message, "❌ У тебе немає казино!")
            return
        
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, f"""⚙️ **ОБМЕЖЕННЯ КАЗИНО**

Поточні обмеження:
• Мін ставка: {casino['min_bet']} монет
• Макс ставка: {casino['max_bet']} монет
• Шанс виграшу: {casino['win_chance'] * 100:.1f}%

**Використання:**
/casino_limits min <сума> - мін ставка
/casino_limits max <сума> - макс ставка
/casino_limits chance <відсоток> - шанс виграшу

Приклад: /casino_limits min 50""")
            return
        
        setting = parts[1].lower()
        value = int(parts[2]) if len(parts) > 2 else 0
        
        if setting == 'min':
            if value < 1:
                bot.reply_to(message, "❌ Мін ставка має бути >= 1!")
                return
            set_casino_limits(casino['id'], min_bet=value)
            bot.reply_to(message, f"✅ Встановлено мін ставку: {value} монет")
            
        elif setting == 'max':
            if value < 1:
                bot.reply_to(message, "❌ Макс ставка має бути >= 1!")
                return
            set_casino_limits(casino['id'], max_bet=value)
            bot.reply_to(message, f"✅ Встановлено макс ставку: {value} монет")
            
        elif setting == 'chance':
            if value < 1 or value > 100:
                bot.reply_to(message, "❌ Шанс має бути від 1 до 100!")
                return
            set_casino_limits(casino['id'], win_chance=value / 100)
            bot.reply_to(message, f"✅ Встановлено шанс виграшу: {value}%")
            
        else:
            bot.reply_to(message, "❌ Невірна команда! Використовуй min, max або chance")
            
    except ValueError:
        bot.reply_to(message, "❌ Невірне значення!")
    except Exception as e:
        logger.error(f"❌ Помилка /casino_limits: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino_play'])
def casino_play_cmd(message):
    """Грати в казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=2)

        if len(parts) < 2:
            bot.reply_to(message, """🎰 **КАЗИНО**

Використання: /casino_play <сума> [ID казино]

**Доступні казино в чаті:**""")
            # Показуємо доступні казино
            casinos = get_all_casinos_in_chat(chat_id)
            if casinos:
                text = ""
                for casino in casinos:
                    owner_name = f"ID {casino['owner_user_id']}"
                    text += f"\n🏦 **{casino['name']}** (ID: {casino['id']})"
                    text += f"\n  Власник: {owner_name}"
                    text += f"\n  Баланс: {casino['casino_coins']} монет"
                    text += f"\n  Мін/Макс: {casino['min_bet']}-{casino['max_bet']} монет"
                    text += f"\n  Шанс виграшу: {int(casino['win_chance'] * 100)}%"
                text += "\n\n**Приклад:** `/casino_play 100 5` - грати 100 монет в казино ID 5"
                bot.reply_to(message, text, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ В цьому чаті ще немає казино!\nСтвори своє: /casino_create")
            return

        # Парсимо ставку та опціонально ID казино
        try:
            bet_amount = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Ставка має бути числом!")
            return

        if bet_amount <= 0:
            bot.reply_to(message, "❌ Ставка має бути додатною!")
            return

        # Визначаємо в якому казино грати
        casino = None
        if len(parts) > 2:
            # Гравець вказав ID казино
            try:
                casino_id = int(parts[2])
                casino = get_casino_by_id(casino_id)
                if not casino or casino['chat_id'] != chat_id:
                    bot.reply_to(message, f"❌ Казино з ID {casino_id} не знайдено в цьому чаті!")
                    return
            except ValueError:
                bot.reply_to(message, "❌ Невірний ID казино!")
                return
        else:
            # Гравець не вказав ID - шукаємо його власне казино
            casino = get_user_casino(user_id, chat_id)
            if not casino:
                # Якщо немає власного казино, пропонуємо вибрати з доступних
                casinos = get_all_casinos_in_chat(chat_id)
                if not casinos:
                    bot.reply_to(message, "❌ У тебе немає казино і в чаті немає інших казино!\nСтвори: /casino_create")
                    return
                else:
                    # Автоматично обираємо казино з найбільшим балансом
                    casino = casinos[0]
                    bot.reply_to(message, f"ℹ️ У тебе немає казино. Граєш в казино '{casino['name']}' (найбільший джекпот)")

        # Перевірка обмежень казино
        if bet_amount < casino['min_bet']:
            bot.reply_to(message, f"❌ Мінімальна ставка: {casino['min_bet']} монет")
            return

        if bet_amount > casino['max_bet']:
            bot.reply_to(message, f"❌ Максимальна ставка: {casino['max_bet']} монет")
            return

        # Перевірка балансу гравця
        currency = get_user_currency(user_id, chat_id)
        if currency.get('coins', 0) < bet_amount:
            bot.reply_to(message, "❌ Недостатньо монет!")
            return

        # Отримуємо бонус удачі від скіну (впливає на шанс виграшу)
        # all_bonus вже включає в себе всі бонуси, тому не потрібно додавати luck_bonus окремо
        total_luck = get_skin_bonus(user_id, chat_id, 'all_bonus')

        # Граємо
        logger.info(f"🎰 Casino play: user={user_id}, casino_id={casino['id']}, bet={bet_amount}, luck_bonus={total_luck}%")

        result = play_casino_game(casino['id'], user_id, bet_amount, total_luck)
        logger.info(f"🎰 Casino result: {result}")

        if not result:
            logger.error(f"❌ play_casino_game returned None for user {user_id}, casino {casino['id']}")
            bot.reply_to(message, "❌ Помилка гри! Перевірте логи.")
            return

        if result.get('result') == 'Недостатньо монет в казино':
            bot.reply_to(message, "❌ В казино недостатньо монет для виплати!\nПоповни казино: /casino_deposit")
            return

        # Оновлюємо баланс гравця
        if result.get('win'):
            new_coins = currency['coins'] - bet_amount + result['amount']
            update_user_currency(user_id, chat_id, coins=new_coins)

            text = f"""🎰 ГРА В КАЗИНО

🏦 Казино: {casino['name']}
Ставка: {bet_amount} монет
{result['result']}
💰 Виграш: +{result['amount']} монет!
🍀 Бонус удачі: +{total_luck}%"""

            # Власник казино отримує прибуток (якщо гравець програв - казино забирає)
            # Але тут гравець виграв, тому казино виплачує
            owner_id = casino['owner_user_id']
            if owner_id != user_id:  # Якщо гравець не власник
                # Власник нічого не отримує, гравець виграв з казино
                pass
        else:
            new_coins = currency['coins'] - bet_amount
            update_user_currency(user_id, chat_id, coins=new_coins)

            text = f"""🎰 ГРА В КАЗИНО

🏦 Казино: {casino['name']}
Ставка: {bet_amount} монет
{result['result']}
💸 Програш: -{bet_amount} монет
🍀 Бонус удачі: +{total_luck}%"""

            # Якщо гравець програв і він не власник - власник отримує прибуток
            owner_id = casino['owner_user_id']
            if owner_id != user_id:
                # Казино вже отримало монети в play_casino_game
                pass

        bot.reply_to(message, text)

    except ValueError:
        bot.reply_to(message, "❌ Невірна ставка!")
    except Exception as e:
        logger.error(f"❌ Помилка /casino_play: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['casino_stats'])
def casino_stats_cmd(message):
    """Статистика казино"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        casino = get_user_casino(user_id, chat_id)
        
        if not casino:
            bot.reply_to(message, "❌ У тебе немає казино!")
            return
        
        stats = get_casino_stats(casino['id'])
        
        if not stats:
            bot.reply_to(message, "❌ Помилка отримання статистики!")
            return
        
        win_rate = (stats['wins_count'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0
        profit = stats['total_bets'] - stats['total_wins']
        
        text = f"""📊 **СТАТИСТИКА КАЗИНО** {casino['name']}

🎮 Всього ігор: {stats['total_games']}
💰 Всього ставок: {stats['total_bets']} монет
🏆 Виплачено: {stats['total_wins']} монет
💵 Прибуток: {profit} монет

**Перемоги:**
• Всього перемог: {stats['wins_count']}
• Відсоток перемог: {win_rate:.1f}%

**Порада:**
Чим більше грають - тим більший прибуток!"""
        
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Помилка /casino_stats: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# МЕНЮ КОМАНД - ЗРУЧНИЙ ДОСТУП
# ============================================

@bot.message_handler(commands=['guild_menu'])
def guild_menu_cmd(message):
    """Головне меню гільдії"""
    try:
        text = """🏰 МЕНЮ ГІЛЬДІЇ

📊 Інформація:
/guild - інформація про гільдію
/guildtop - топ гільдій
/guild_chest - скринька гільдії

🗺️ Території:
/guild_territories - карта
/guild_capture - захопити
/guild_income - дохід
/guild_defense_info - захист

🪖 Армія:
/guild_warriors - воїни
/guild_buy_warrior - купити
/guild_defend - захист
/guild_attack - атака

⚔️ Війни:
/guild_war_declare - війна
/guild_war_battle - битва
/guild_war_status - статус

🐲 Боси:
/guild_boss_spawn - спавн
/guild_boss_attack - атака

🎒 Предмети:
/guild_items - предмети гільдії
/guild_claim_item - вивести предмет

Швидкі команди:
/warriors_menu - меню армії
/items_menu - меню предметів
/genetics_menu - генетика
/trade_menu - трейди"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /guild_menu: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['warriors_menu'])
def warriors_menu_cmd(message):
    """Меню воїнів"""
    try:
        text = """🪖 МЕНЮ ВОЇНІВ

Інформація:
/guild_warriors - список армії

Купівля:
/guild_buy_warrior regular 10 - 10 звичайних (100💰)
/guild_buy_warrior matochnik 5 - 5 маточників (2500💰)
/guild_buy_warrior elite 2 - 2 елітних (2000💰)
/guild_buy_warrior legendary 1 - 1 легендарний (5000💰)

Управління:
/guild_defend territory type count - на захист
/guild_attack territory - атака

Типи воїнів:
🐷 Свинар - 100💰, сила 10
🐗 Маточник - 500💰, сила 60
⚔️ Елітний - 1000💰, сила 150
👑 Легендарний - 5000💰, сила 1000"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /warriors_menu: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['items_menu'])
def items_menu_cmd(message):
    """Меню предметів"""
    try:
        text = """🎒 МЕНЮ ПРЕДМЕТІВ

Інформація:
/inventory - твій інвентар
/guild_items - предмети гільдії

Трейд:
/item_trade предмет - створити трейд
/item_trades - активні трейди
/item_accept id - прийняти
/item_cancel id - скасувати

Вивід з гільдії:
/guild_claim_item ID count - вивести

Використання:
/use_item ID - використати предмет

Рідкості:
⚪ Common - 1x бонус
🔵 Rare - 2x бонус
🟣 Epic - 3x бонус
🟡 Legendary - 5x бонус
🔴 Mythic - 10x бонус

Типи:
⚔️ Зброя - сила
🛡️ Броня - захист
🍀 Аксесуар - удача"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /items_menu: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['genetics_menu'])
def genetics_menu_cmd(message):
    """Меню генетики"""
    try:
        text = """🧬 МЕНЮ ГЕНЕТИКИ

Основні команди:
/genes - гени твого хряка
/breed - схрещування (100💰)
/children - діти
/childinfo ID - інфо дитини

Бонуси дітей:
/childbonus - бонуси від дітей
/childraid ID - рейд
/childduel ID - дуель
/childtrain ID - тренування (50💰)

Рідкості генів:
⚪ C (Common) - 70%
🔵 R (Rare) - 20%
🟣 E (Epic) - 7%
🟡 L (Legendary) - 2.5%
🔴 S (Special) - 0.5%

Кольори:
🐷 Звичайний - 60%
🐗 Дикий - 20%
✨ Золотий - 10%
🌈 Веселка - 5%
🤖 Кібер - 3%
👑 Королівський - 1.5%
🌑 Порожнеча - 0.5%"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /genetics_menu: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['trade_menu'])
def trade_menu_cmd(message):
    """Меню трейдів"""
    try:
        text = """💱 МЕНЮ ТРЕЙДІВ

Монети:
/trade @user сума - створити трейд
/trades - активні трейди
/accept id - прийняти
/cancel id - скасувати

Предмети:
/item_trade предмет count - трейд
/item_trades - активні трейди
/item_accept id - прийняти
/item_cancel id - скасувати

Поради:
1. Завжди перевіряй ID трейду
2. Не приймай трейди від незнайомців
3. Перевіряй предмети перед прийняттям
4. Скасовуй підозрілі трейди

Безпека:
• Трейд діє 24 години
• Можна скасувати до прийняття
• Предмети перевіряються автоматично"""

        bot.reply_to(message, text)

    except Exception as e:
        logger.error(f"❌ Помилка /trade_menu: {e}", exc_info=True)
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
            # Перевіряємо чи нещодавно бос був переможений
            last_boss = get_last_boss()
            now = int(time.time())

            if last_boss:
                defeat_date = last_boss.get('defeat_date')
                logger.info(f"Last boss defeat_date: {defeat_date}, now: {now}")
                
                if defeat_date and defeat_date > 0:
                    time_since_defeat = now - defeat_date
                    logger.info(f"Time since defeat: {time_since_defeat} seconds ({time_since_defeat / 3600:.1f} hours)")
                    
                    if time_since_defeat < 86400:  # 24 години
                        hours_left = int((86400 - time_since_defeat) / 3600)
                        bot.reply_to(message, f"""🐲 **БОС-ДУЕЛІ**

Бос щойно переможений!
Наступний бос з'явиться через {hours_left} год.

**Як бити боса:**
/boss attack - атакувати боса
/boss info - інформація про боса""")
                        return

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
                
                # Кулдаун збільшується з кожною перемогою
                base_cooldown = 2
                current_cooldown = base_cooldown + (boss.get('defeat_count', 0) * 2)

                text = f"""🐲 {boss['name']}

⭐ Рівень: {boss['level']}
🏆 Перемог гравців: {boss.get('defeat_count', 0)}
❤️ Здоров'я: {boss['health']}/{boss['max_health']}
{hp_bar} {hp_percent}%
⚔️ Шкода: {boss['damage']}
💰 Нагорода: 500 монет + 250 XP (розподіл за % урону)

**Топ гравців:**
"""
                for i, p in enumerate(participants[:5], 1):
                    text += f"{i}. ID {p['user_id']} - {p['damage_dealt']} шкоди\n"

                text += f"""
**Команди:**
/boss attack - атакувати боса (кулдаун {current_cooldown} год)
/boss info - детальна інформація

**Як це працює:**
1. Кожен гравець може атакувати боса
2. Шкода = вага хряка × 2 + рандом
3. Кулдаун між атаками: {current_cooldown} годин (зростає з перемогами)
4. Нагороди: 500 монет + 250 XP (розподіл за % урону)
5. Після перемоги бос не з'являється 24 години
6. Бос стає сильнішим з кожною перемогою!"""

                bot.reply_to(message, text)
            
            elif action == 'attack':
                # Перевіряємо чи бос ще активний
                if not boss.get('is_active', True):
                    bot.reply_to(message, "🐲 Бос вже переможений!\n\nНаступний з'явиться через 24 години.")
                    return

                # Перевіряємо кулдаун атаки (2 години + 2 години за кожну перемогу боса)
                base_cooldown = 7200  # 2 години
                boss_cooldown = base_cooldown + (boss.get('defeat_count', 0) * 7200)  # +2 години за перемогу

                last_attack = get_last_boss_attack_time(user_id, chat_id)
                now = int(time.time())
                if last_attack and (now - last_attack) < boss_cooldown:
                    hours_left = int((boss_cooldown - (now - last_attack)) / 3600)
                    minutes_left = int(((boss_cooldown - (now - last_attack)) % 3600) / 60)
                    bot.reply_to(message, f"⏳ Ще рано! Атакувати боса можна раз на {boss_cooldown // 3600} годин.\n\nЗалишилось: {hours_left} год {minutes_left} хв.")
                    return

                # Перевіряємо чи нещодавно бос був переможений (24 години блок)
                defeat_time = get_boss_defeat_time()
                if defeat_time and (now - defeat_time) < 86400:
                    hours_left = int((86400 - (now - defeat_time)) / 3600)
                    bot.reply_to(message, f"🐲 Бос щойно переможений!\n\nНаступний з'явиться через {hours_left} год.")
                    return

                hryak = get_hryak(user_id, chat_id)
                if not hryak:
                    bot.reply_to(message, "❌ У тебе немає хряка! Введи /grow")
                    return

                # Перевіряємо чи бос ще має HP
                if boss['health'] <= 0:
                    bot.reply_to(message, "🐲 Бос вже переможений!\n\nНаступний з'явиться через 24 години.")
                    return

                # Розраховуємо шкоду (вага хряка + рандом)
                base_damage = hryak['weight'] * 2
                random_damage = random.randint(-10, 20)

                # Бонус від скіну
                skin_bonus = get_skin_bonus(user_id, chat_id, 'weight_bonus')

                # Перевіряємо чи це @terchizz - даємо невеликий баф
                username = message.from_user.username or ''
                terchizz_bonus = 1.1 if username == 'terchizz' else 1.0  # +10% шкоди для терчіза

                total_damage = max(1, int((base_damage + random_damage) * (1 + skin_bonus / 100) * terchizz_bonus))

                logger.info(f"User {user_id} attacking boss {boss['id']} with {total_damage} damage (hryak weight: {hryak['weight']})")
                logger.info(f"Boss info: id={boss['id']}, health={boss['health']}, max_health={boss['max_health']}, is_active={boss.get('is_active', True)}")

                # Атакуємо
                try:
                    logger.info(f"Calling attack_boss with boss_id={boss['id']}, user_id={user_id}, chat_id={chat_id}, damage={total_damage}")
                    result = attack_boss(boss['id'], user_id, chat_id, total_damage)
                    logger.info(f"attack_boss returned: {result}")

                    if not result:
                        logger.error(f"❌ attack_boss повернув None для user {user_id}")
                        bot.reply_to(message, "❌ Помилка: attack_boss повернув None")
                        return
                    
                    # Перевіряємо чи сталася помилка
                    if result.get('error'):
                        logger.error(f"❌ Помилка від attack_boss: {result.get('error')}")
                        bot.reply_to(message, f"❌ Помилка: {result.get('error')}")
                        return
                    
                    # Перевіряємо чи бос вже був переможений
                    if result.get('already_defeated'):
                        bot.reply_to(message, "🐲 Бос вже переможений!\n\nНаступний з'явиться через 24 години.")
                        return
                    
                    # Перевіряємо чи бос був "зламаний" (HP <= 0 але активний)
                    if result.get('was_bugged'):
                        bot.reply_to(message, """🐲 **БОСА ПРИМУСОВО ПЕРЕМОЖЕНО!**

Бос мав HP <= 0 але був активний.
Виправлено! Наступний з'явиться через 24 години.""")
                        return
                        
                except Exception as e:
                    logger.error(f"❌ Exception during attack_boss: {e}", exc_info=True)
                    bot.reply_to(message, f"❌ Деталі помилки: {str(e)}")
                    return

                # Успішна атака
                if result and not result.get('defeated'):
                    # Бос ще жив - отримуємо АКТУАЛЬНІ дані з БД
                    updated_boss = get_active_boss()
                    if updated_boss:
                        remaining = updated_boss['health']
                        max_health = updated_boss['max_health']
                    else:
                        remaining = result.get('remaining_health', boss['health'])
                        max_health = result.get('max_health', boss['max_health'])

                    hp_percent = int((remaining / max_health) * 100)
                    hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

                    # Показуємо фактичну шкоду
                    actual_damage = total_damage if total_damage <= (boss['health'] - remaining) else boss['health'] - remaining

                    bot.reply_to(message, f"""⚔️ **АТАКА!**

Твій хряк {hryak['name']} завдав {actual_damage} шкоди!

🐲 {boss['name']}
❤️ {remaining}/{max_health} ({hp_percent}%)
{hp_bar}

Продовжуй атакувати командою /boss attack!""")
                    return

                if result and result.get('defeated'):
                    # Бос переможений!
                    participants = get_boss_participants(boss['id'])

                    # Фіксований пул нагород
                    TOTAL_COINS_POOL = 500
                    TOTAL_XP_POOL = 250
                    
                    # Рахуємо загальну шкоду
                    total_damage = sum(p['damage_dealt'] for p in participants)
                    
                    logger.info(f"Boss defeated! Total damage: {total_damage}, Participants: {len(participants)}")

                    # Розподіл нагороди за % урону
                    for p in participants:
                        # Розраховуємо % урону
                        damage_share = p['damage_dealt'] / total_damage if total_damage > 0 else 0
                        
                        # Розраховуємо нагороди
                        coins_reward = int(TOTAL_COINS_POOL * damage_share)
                        xp_reward = int(TOTAL_XP_POOL * damage_share)
                        
                        # Баф для @terchizz - +20% монет та XP
                        if p['user_id'] == 1044325356:  # terchizz user ID
                            coins_reward = int(coins_reward * 1.2)
                            xp_reward = int(xp_reward * 1.2)
                        
                        # Мінімальна нагорода 1 монета/1 XP якщо участвував
                        if coins_reward == 0 and p['damage_dealt'] > 0:
                            coins_reward = 1
                        if xp_reward == 0 and p['damage_dealt'] > 0:
                            xp_reward = 1
                        
                        logger.info(f"Player {p['user_id']}: damage={p['damage_dealt']} ({damage_share*100:.1f}%), coins={coins_reward}, xp={xp_reward}")

                        if coins_reward > 0:
                            add_coins(p['user_id'], chat_id, coins_reward)
                        if xp_reward > 0:
                            add_xp(p['user_id'], chat_id, xp_reward)

                    # Оголошуємо перемогу
                    defeated_by = result.get('defeated_by_user_id') if result else None
                    winner_hryak = get_hryak(defeated_by or user_id, chat_id)
                    winner_name = winner_hryak['name'] if winner_hryak else "Невідомо"

                    # Знаходимо топ 3 гравців за уроном
                    sorted_participants = sorted(participants, key=lambda x: x['damage_dealt'], reverse=True)[:3]
                    top_text = ""
                    for i, p in enumerate(sorted_participants, 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        damage_percent = (p['damage_dealt'] / total_damage * 100) if total_damage > 0 else 0
                        top_text += f"{medal} {i} місце: {damage_percent:.1f}% урону\n"

                    # Спавн нового боса який стає сильнішим!
                    new_boss_level = boss.get('level', 1) + 1
                    new_boss_health = boss.get('max_health', 1000) + (new_boss_level * 500)
                    new_boss_damage = boss.get('damage', 50) + (new_boss_level * 25)
                    
                    logger.info(f"🐲 Спавн нового боса: рівень {new_boss_level}, HP {new_boss_health}, шкода {new_boss_damage}")
                    
                    # Отримуємо випадкову назву боса з варіативності
                    boss_variety_name, _ = get_random_boss_variety(new_boss_level)
                    full_boss_name = f"🐲 {boss_variety_name}"

                    logger.info(f"🐲 Спавн нового боса: рівень {new_boss_level}, HP {new_boss_health}, школа {new_boss_damage}, назва: {full_boss_name}")

                    new_boss_id = spawn_boss(full_boss_name, new_boss_level, new_boss_health, new_boss_damage, 500, 250)
                    
                    if new_boss_id:
                        logger.info(f"✅ Новий бос створений: ID {new_boss_id}")

                    bot.reply_to(message, f"""🎉 БОСА ПЕРЕМОЖЕНО!

{boss['name']} загинув від рук героїв!
Останній удар: {winner_name}

🏆 Топ гравців за уроном:
{top_text}
💰 Загальний пул: {TOTAL_COINS_POOL} монет, {TOTAL_XP_POOL} XP
📊 Нагороди розподілено за % урону!

🐲 НОВИЙ БОС:
Рівень: {new_boss_level}
Здоров'я: {new_boss_health}
Шкода: {new_boss_damage}

⏰ Наступна атака через 2 години!""")
                elif result and not result.get('defeated'):
                    # Бос ще жив - отримуємо АКТУАЛЬНІ дані з БД
                    updated_boss = get_active_boss()
                    if updated_boss:
                        remaining = updated_boss['health']
                        max_health = updated_boss['max_health']
                    else:
                        remaining = result.get('remaining_health', boss['health'])
                        max_health = result.get('max_health', boss['max_health'])

                    hp_percent = int((remaining / max_health) * 100)
                    hp_bar = "🟩" * (hp_percent // 10) + "🟥" * (10 - hp_percent // 10)

                    bot.reply_to(message, f"""⚔️ АТАКА!

Твій хряк {hryak['name']} завдав {total_damage} шкоди!

🐲 {boss['name']}
❤️ {remaining}/{max_health} ({hp_percent}%)
{hp_bar}

⏰ Наступна атака через 2 години!

Продовжуй атакувати командою /boss attack!""")

                    # 🎃 ІВЕНТ: Хелловін - атака боса = прогрес
                    add_event_progress(user_id, chat_id, 'halloween', 1)
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
💰 Нагорода: 500 монет + 250 XP (розподіл за % урону)

**Команди:**
/boss attack - атакувати боса (кулдаун 2 год)
/boss info - детальна інформація

**Як це працює:**
1. Кожен гравець може атакувати боса
2. Шкода = вага хряка × 2 + рандом
3. Кулдаун між атаками: 2 години
4. Нагороди: 500 монет + 250 XP (розподіл за % урону)
5. Після перемоги бос не з'являється 24 години"""

            bot.reply_to(message, text)

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

        now = int(time.time())

        # Розбиваємо на частини щоб уникнути помилки 431
        parts_text = []
        current_text = "🎉 **СЕЗОННІ ІВЕНТИ**\n\n"

        for i, event in enumerate(events):
            status_emoji = "✅" if event['is_active'] and event['start_date'] <= now <= event['end_date'] else "⏳" if event['start_date'] > now else "❌"

            # Прогрес користувача
            progress = get_user_event_progress(user_id, event['id'])
            progress_text = f" (Твій прогрес: {progress['progress']})" if progress else ""

            time_left = event['end_date'] - now if event['end_date'] > now else 0
            days_left = time_left // 86400 if time_left > 0 else 0

            event_text = f"""{status_emoji} **{event['name']}** (ID: `{event['id']}`)
{event['description']}{progress_text}
🎁 Нагорода: {event['special_reward_coins']} монет, {event['special_reward_xp']} XP
⏳ Закінчується через: {days_left} дн.

"""

            # Якщо текст занадто великий, розбиваємо
            if len(current_text) + len(event_text) > 3000:
                parts_text.append(current_text)
                current_text = event_text
            else:
                current_text += event_text

        # Додаємо останню частину
        if current_text:
            parts_text.append(current_text)

        # Додаємо команди до останньої частини
        if parts_text:
            parts_text[-1] += """**Команди:**
/eventjoin <event_id> - приєднатися до івенту
/eventprogress - перевірити прогрес
/eventsclaim <event_id> - забрати нагороду"""

        # Надсилаємо частинами
        for i, part in enumerate(parts_text):
            if i == 0:
                bot.reply_to(message, part, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, part, parse_mode="Markdown")

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

        # Перевіряємо чи завершено івент
        target = 20  # За замовчуванням
        if 'easter' in event['event_type']:
            target = 20  # Знайди 20 яєць
        elif 'christmas' in event['event_type']:
            target = 10  # Збері 10 сніжинок
        elif 'halloween' in event['event_type']:
            target = 5  # Переможи 5 босів

        if progress['progress'] < target:
            bot.reply_to(message, f"❌ Івент ще не завершено! Твій прогрес: {progress['progress']}/{target}")
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


@bot.message_handler(commands=['eventjoin'])
def event_join_cmd(message):
    """Приєднатися до івенту"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        parts = message.text.split()

        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /eventjoin <event_id>")
            return

        event_id = int(parts[1])

        # Перевіряємо івент
        events = get_all_events()
        event = next((e for e in events if e['id'] == event_id), None)

        if not event:
            bot.reply_to(message, "❌ Івент не знайдено!")
            return

        now = int(time.time())
        if not event['is_active'] or not (event['start_date'] <= now <= event['end_date']):
            bot.reply_to(message, "❌ Цей івент ще не активний або вже завершився!")
            return

        # Перевіряємо чи вже бере участь
        progress = get_user_event_progress(user_id, event_id)
        if progress:
            bot.reply_to(message, f"✅ Ти вже береш участь в {event['name']}!")
            return

        # Додаємо участь
        update_event_progress(user_id, event_id, chat_id, 0)

        bot.reply_to(message, f"""🎉 **Ти приєднався до {event['name']}!**

{event['description']}

🎁 Нагорода: {event['special_reward_coins']} монет, {event['special_reward_xp']} XP

Використовуй /events щоб перевірити прогрес.""")

    except Exception as e:
        logger.error(f"❌ Помилка /eventjoin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['eventprogress'])
def event_progress_cmd(message):
    """Перевірити прогрес в івентах"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        events = get_all_events()
        now = int(time.time())

        text = "📊 **Твій прогрес в івентах:**\n\n"
        found = False

        for event in events:
            if event['is_active'] and event['start_date'] <= now <= event['end_date']:
                progress = get_user_event_progress(user_id, event['id'])
                if progress:
                    found = True
                    status_emoji = "✅" if progress['completed'] else "⏳"
                    claimed_emoji = "💰" if progress['reward_claimed'] else ""
                    
                    # Визначаємо ціль івенту
                    target = 20  # За замовчуванням
                    if 'easter' in event['event_type']:
                        target = 20  # Знайди 20 яєць
                    elif 'christmas' in event['event_type']:
                        target = 10  # Збері 10 сніжинок
                    elif 'halloween' in event['event_type']:
                        target = 5  # Переможи 5 босів
                    
                    text += f"{status_emoji} **{event['name']}**{claimed_emoji}\n"
                    text += f"Прогрес: {progress['progress']}/{target}\n"
                    text += f"Завершено: {'Так' if progress['completed'] else 'Ні'}\n"
                    text += f"Нагорода отримана: {'Так' if progress['reward_claimed'] else 'Ні'}\n\n"

        if not found:
            text = "📭 Ти ще не береш участь в активних івентах.\n\nВикористовуй /events щоб побачити доступні івенти та /eventjoin <id> щоб приєднатися."

        bot.reply_to(message, text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Помилка /eventprogress: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


def add_event_progress(user_id, chat_id, event_type, progress_amount=1):
    """Додає прогрес до активних івентів типу"""
    try:
        events = get_all_events()
        now = int(time.time())
        
        for event in events:
            # Перевіряємо чи івент активний і відповідає типу
            if event['is_active'] and event['start_date'] <= now <= event['end_date']:
                if event['event_type'] == event_type:
                    # Додаємо прогрес
                    update_event_progress(user_id, event['id'], chat_id, progress_amount)
                    logger.info(f"✅ Додано прогрес до івенту {event['name']}: +{progress_amount}")
    except Exception as e:
        logger.error(f"❌ Помилка додавання прогресу івенту: {e}")


def check_event_random_drop(user_id, chat_id, event_type, action_name):
    """Перевіряє випадковий дроп предметів івенту (10% шанс)"""
    try:
        events = get_all_events()
        now = int(time.time())
        
        for event in events:
            if event['is_active'] and event['start_date'] <= now <= event['end_date']:
                if event['event_type'] == event_type:
                    # 10% шанс знайти предмет івенту
                    if random.random() < 0.10:
                        # Додаємо бонусний прогрес
                        update_event_progress(user_id, event['id'], chat_id, 1)
                        
                        # Повідомлення про знахідку
                        if event_type == 'easter':
                            items = ['🥚 Великоднє яйце', '🐰 Золоте яйце', '🌷 Квітку', '🍫 Шоколадного зайця']
                            item = random.choice(items)
                            bot.send_message(chat_id, f"""🎁 **ТИ ЗНАЙШОВ {item.upper()}!**

Під час {action_name} ти помітив щось блискуче...
Це виявився {item}!

+1 до прогресу івенту "{event['name']}"!""", parse_mode="Markdown")
                        elif event_type == 'christmas':
                            items = ['❄️ Сніжинку', '🎄 Ялинкову іграшку', '🎅 Різдвяну шкарпетку', '🌟 Вифлеємську зірку']
                            item = random.choice(items)
                            bot.send_message(chat_id, f"""🎁 **ТИ ЗНАЙШОВ {item.upper()}!**

Під час {action_name} ти помітив щось святкове...
Це виявилась {item}!

+1 до прогресу івенту "{event['name']}"!""", parse_mode="Markdown")
                        elif event_type == 'halloween':
                            items = ['🎃 Гарбуз', '👻 Привид', '🍬 Цукерку', '🦇 Казана']
                            item = random.choice(items)
                            bot.send_message(chat_id, f"""🎁 **ТИ ЗНАЙШОВ {item.upper()}!**

Під час {action_name} ти помітив щось моторошне...
Це виявився {item}!

+1 до прогресу івенту "{event['name']}"!""", parse_mode="Markdown")
                        
                        return True
    except Exception as e:
        logger.error(f"❌ Помилка check_event_random_drop: {e}")
    return False


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


# Обробник спам контролю - ТІЛЬКИ для повідомлень (НЕ для команд!)
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def spam_handler(message):
    """Перевірка на спам (ігнорує команди)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

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
    if is_chat_admin(chat_id, user_id):
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
    chat_quest = quest_progress.get('chat_active', {'progress': 0, 'target': 50, 'completed': False, 'claimed': False})
    
    # Не оновлюємо якщо вже завершено і забрано
    if not chat_quest.get('claimed', False):
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
        user_id_str = request.args.get('user_id', '0')
        if not user_id_str or user_id_str.lower() == 'null':
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        user_id = int(user_id_str)
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
        user_id_str = request.args.get('user_id', '0')
        if not user_id_str or user_id_str.lower() == 'null':
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        user_id = int(user_id_str)

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
        user_id_str = request.args.get('user_id', '0')
        if not user_id_str or user_id_str.lower() == 'null':
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        user_id = int(user_id_str)
        chat_id = int(request.args.get('chat_id', 0))

        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400

        inventory = get_user_inventory(user_id, chat_id or -1)

        # Also get user_items (loot/traded items)
        user_items_list = get_user_items(user_id, chat_id or -1)

        # Add item_id as integer ID for loot items
        for item in user_items_list:
            item['is_loot'] = True

        return jsonify({
            'success': True,
            'data': inventory,
            'loot_items': user_items_list
        }), 200
    except Exception as e:
        logger.error(f"API /inventory error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/my-skins', methods=['GET'])
def api_get_my_skins():
    """Отримати скіни користувача"""
    try:
        user_id_str = request.args.get('user_id', '0')
        if not user_id_str or user_id_str.lower() == 'null':
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        user_id = int(user_id_str)
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
        
        logger.info(f"Leaderboard chat request: chat_id={chat_id}")

        # Get from hryaky_data cache
        chat_hryaky = []
        for key, h in hryaky_data.items():
            # Filter by chat_id - must match exactly
            if chat_id and h.get('chat_id') == chat_id:
                # Get equipped skin for this user
                equipped_skin = get_user_equipped_skin(h.get('user_id'), h.get('chat_id'))
                h['skin_icon'] = equipped_skin['icon'] if equipped_skin else '🐷'
                chat_hryaky.append(h)
            elif not chat_id or chat_id == 0:
                # No chat_id provided - skip
                continue

        chat_hryaky = sorted(chat_hryaky, key=lambda x: x['weight'], reverse=True)[:10]
        
        logger.info(f"Leaderboard chat result: {len(chat_hryaky)} players")

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
            # Get equipped skin for this user
            equipped_skin = get_user_equipped_skin(h.get('user_id'), h.get('chat_id'))
            h['skin_icon'] = equipped_skin['icon'] if equipped_skin else '🐷'
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
        chat_id = data.get('chat_id')
        
        # Fix chat_id - use -1 if 0, None, or missing
        if not chat_id or chat_id == 0:
            chat_id = -1
        
        logger.info(f"Buy item: user_id={user_id}, chat_id={chat_id}, item_id={item_id}")

        if not user_id or not item_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        # Get item
        items = get_shop_items()
        item = next((i for i in items if i['item_id'] == item_id), None)

        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404

        # Check balance
        currency = get_user_currency(user_id, chat_id)
        logger.info(f"User coins: {currency['coins']}, item price: {item['price']}")
        
        if currency['coins'] < item['price']:
            return jsonify({'success': False, 'message': 'Not enough coins'}), 400

        # Buy item
        update_user_currency(user_id, chat_id, coins=currency['coins'] - item['price'])
        add_to_inventory(user_id, chat_id, item_id)
        
        logger.info(f"Item purchased: {item_id}")

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
        chat_id = data.get('chat_id')
        
        # Fix chat_id - use -1 if 0, None, or missing
        if not chat_id or chat_id == 0:
            chat_id = -1

        logger.info(f"Buy skin: user_id={user_id}, chat_id={chat_id}, skin_name={skin_name}")

        if not user_id or not skin_name:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        # Get skin
        skin = get_skin_by_name(skin_name)

        if not skin:
            logger.error(f"Skin not found: {skin_name}")
            return jsonify({'success': False, 'message': 'Skin not found'}), 404

        # Check balance
        currency = get_user_currency(user_id, chat_id)
        logger.info(f"User coins: {currency['coins']}, skin price: {skin['price']}")
        
        if currency['coins'] < skin['price']:
            return jsonify({'success': False, 'message': 'Not enough coins'}), 400

        # Check if already has - use correct chat_id
        has = has_skin(user_id, chat_id, skin['id'])
        logger.info(f"Has skin {skin_name}: {has} (user_id={user_id}, chat_id={chat_id}, skin_id={skin['id']})")
        
        if has:
            return jsonify({'success': False, 'message': 'Already owned'}), 400

        # Buy skin
        update_user_currency(user_id, chat_id, coins=currency['coins'] - skin['price'])
        bought = buy_skin(user_id, chat_id, skin['id'])
        logger.info(f"Buy skin result: {bought}")
        
        # Verify the skin was added
        has_after = has_skin(user_id, chat_id, skin['id'])
        logger.info(f"Has skin after purchase: {has_after}")
        
        logger.info(f"Skin purchased: {skin_name}")

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /buy-skin error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/equip-skin', methods=['POST'])
def api_equip_skin():
    """Одягнути скін"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        skin_name = data.get('skin_name')
        chat_id = data.get('chat_id')
        
        # Fix chat_id - use -1 if 0, None, or missing
        if not chat_id or chat_id == 0:
            chat_id = -1
        
        logger.info(f"Equip skin: user_id={user_id}, chat_id={chat_id}, skin_name={skin_name}")

        if not user_id or not skin_name:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        # Get skin
        skin = get_skin_by_name(skin_name)

        if not skin:
            return jsonify({'success': False, 'message': 'Skin not found'}), 404

        # Check if has - use correct chat_id
        has = has_skin(user_id, chat_id, skin['id'])
        logger.info(f"Has skin {skin_name}: {has}")
        
        if not has:
            return jsonify({'success': False, 'message': 'You do not own this skin'}), 400

        # Equip
        equip_skin(user_id, chat_id, skin['id'])
        logger.info(f"Skin equipped: {skin_name}")

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"API /equip-skin error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# CRYPTO API ENDPOINTS
# ============================================

@flask_app.route('/api/webapp/crypto-info', methods=['GET'])
def api_crypto_info():
    """Get crypto balance and info"""
    try:
        user_id = int(request.args.get('user_id', 0))
        chat_id = int(request.args.get('chat_id', 0))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        crypto_info = get_conversion_info(user_id, chat_id)
        
        return jsonify({
            'success': True,
            'data': crypto_info or {
                'game_coins': 0,
                'crypto_coins': 0,
                'total_converted': 0,
                'last_withdrawal': 0
            }
        }), 200
    except Exception as e:
        logger.error(f"API /crypto-info error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/convert', methods=['POST'])
def api_convert():
    """Convert game coins to crypto"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chat_id = data.get('chat_id', 0)
        amount = int(data.get('amount', 0))
        
        if not user_id or not amount:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Fix chat_id
        if not chat_id or chat_id == 0:
            chat_id = -1
        
        logger.info(f"Convert request: user_id={user_id}, amount={amount}")
        
        # Convert
        result = convert_game_to_crypto(user_id, chat_id, amount)
        
        if result['success']:
            logger.info(f"Conversion successful: {amount} → {result['crypto_received']} CRYPTO")
            return jsonify({'success': True, 'data': result}), 200
        else:
            return jsonify({'success': False, 'message': result['message']}), 400
    except Exception as e:
        logger.error(f"API /convert error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/withdraw', methods=['POST'])
def api_withdraw():
    """Create withdrawal request"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chat_id = data.get('chat_id', 0)
        amount = int(data.get('amount', 0))
        wallet_address = data.get('wallet_address', '')
        
        if not user_id or not amount or not wallet_address:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Fix chat_id
        if not chat_id or chat_id == 0:
            chat_id = -1
        
        # Check crypto balance
        crypto_balance = get_crypto_balance(user_id, chat_id)
        
        if crypto_balance < amount:
            return jsonify({'success': False, 'message': f'Недостатньо CRYPTO. Баланс: {crypto_balance}'}), 400
        
        # Record transaction in database
        record_crypto_transaction(
            user_id=user_id,
            chat_id=chat_id,
            tx_type='withdraw',
            amount=amount,
            wallet_address=wallet_address
        )
        
        logger.info(f"Withdrawal request recorded: user_id={user_id}, amount={amount}, wallet={wallet_address}")
        
        # Deduct from balance
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_currencies 
                SET crypto_coins = crypto_coins - %s, last_withdrawal = %s
                WHERE user_id = %s AND chat_id = %s
            ''', (amount, int(time.time()), user_id, chat_id))
            conn.commit()
            cursor.close()
            conn.close()
        
        # TODO: In Phase 3, integrate with TON SDK to actually send tokens
        # For now, withdrawal is recorded and will be processed manually
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal request created',
            'data': {
                'amount': amount,
                'wallet': wallet_address,
                'status': 'pending',
                'note': 'Withdrawal will be processed within 24 hours'
            }
        }), 200
    except Exception as e:
        logger.error(f"API /withdraw error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/transactions', methods=['GET'])
def api_get_transactions():
    """Get user transaction history"""
    try:
        user_id = int(request.args.get('user_id', 0))
        chat_id = int(request.args.get('chat_id', 0))
        limit = int(request.args.get('limit', 20))
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        transactions = get_user_transactions(user_id, chat_id, limit)
        
        return jsonify({
            'success': True,
            'data': transactions
        }), 200
    except Exception as e:
        logger.error(f"API /transactions error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@flask_app.route('/api/webapp/use-item', methods=['POST'])
def api_use_item():
    """Використати предмет"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        item_id = data.get('item_id')
        chat_id = data.get('chat_id')

        # Fix chat_id - use -1 if 0, None, or missing
        if not chat_id or chat_id == 0:
            chat_id = -1

        logger.info(f"Use item: user_id={user_id}, chat_id={chat_id}, item_id={item_id}")

        if not user_id or not item_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        # Check if user has the item
        if not has_item(user_id, chat_id, item_id):
            return jsonify({'success': False, 'message': 'Item not found in inventory'}), 400

        # Get item
        item = get_item(item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404

        # Use item - handle each type
        if item_id == 'energy':
            # Remove feed cooldown
            hryak = get_hryak(user_id, chat_id)
            if hryak:
                save_hryak_to_db(user_id, chat_id, {'last_feed': 0})
                logger.info(f"Energy used: removed feed cooldown")
            else:
                return jsonify({'success': False, 'message': 'No hryak'}), 400
        elif item_id == 'spermobak':
            # Remove trachen/breed cooldown
            from db import get_connection
            import time as time_module
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                old_time = int(time_module.time()) - 86400
                cursor.execute('''
                    UPDATE trachenzebiten
                    SET created_at = %s
                    WHERE user_id = %s AND chat_id = %s
                    AND id = (
                        SELECT id FROM trachenzebiten
                        WHERE user_id = %s AND chat_id = %s
                        ORDER BY id DESC LIMIT 1
                    )
                ''', (old_time, user_id, chat_id, user_id, chat_id))
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"Spermobak used: affected {affected} rows")
            else:
                return jsonify({'success': False, 'message': 'DB error'}), 500
        elif item_id == 'pastors_milk':
            # Remove child train cooldown
            from db import get_connection
            import time as time_module
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                old_time = int(time_module.time()) - 86400
                cursor.execute('''
                    UPDATE hryak_genes
                    SET last_train = %s
                    WHERE user_id = %s
                ''', (old_time, user_id))
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"Pastors milk used: affected {affected} rows")
            else:
                return jsonify({'success': False, 'message': 'DB error'}), 500
        elif item_id == 'vitamins':
            # Weight bonus
            hryak = get_hryak(user_id, chat_id)
            if hryak:
                hryak['weight'] += item['effect_value']
                save_hryak_to_db(user_id, chat_id, hryak)
            else:
                return jsonify({'success': False, 'message': 'No hryak'}), 400

        # Remove item
        remove_from_inventory(user_id, chat_id, item_id, 1)
        logger.info(f"Item used: {item_id}")

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
            
            # Пробуємо різні ��ндпоінти
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

# Запускаємо keep-alive в ок��емому потоці
keep_alive_thread = Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

# ============================================
# АДМІН ПАНЕЛЬ - ТІЛЬКИ ДЛЯ ТЕБЕ
# ============================================

# Тестова команда для перевірки чи працюють команди
@bot.message_handler(commands=['test_admin'])
def test_admin_cmd(message):
    """Тест адмін команди"""
    logger.info(f"🧪 TEST ADMIN COMMAND called by {message.from_user.id}")
    logger.info(f"ADMIN_ID={ADMIN_ID}, is_admin={is_admin(message.from_user.id)}")
    
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
        return
    
    bot.reply_to(message, f"✅ TEST OK!\nADMIN_ID={ADMIN_ID}\nYour ID={message.from_user.id}\nIs Admin={is_admin(message.from_user.id)}")


@bot.message_handler(commands=['admin_weight'])
def admin_set_weight(message):
    """Змінити вагу хряка користувача"""
    try:
        # Перевірка адміна
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_weight <user_id> <вага>")
            return
        
        user_id = int(parts[1])
        new_weight = int(parts[2])
        
        hryak = get_hryak(user_id, message.chat.id)
        if not hryak:
            bot.reply_to(message, f"❌ У користувача {user_id} немає хряка!")
            return
        
        old_weight = hryak['weight']
        hryak['weight'] = new_weight
        save_hryaky()
        
        bot.reply_to(message, f"""✅ Вагу змінено!

Користувач: {user_id}
Стара вага: {old_weight} кг
Нова вага: {new_weight} кг""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_weight: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_addweight'])
def admin_add_weight(message):
    """Додати вагу хряку"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addweight <user_id> <кг>")
            return
        
        user_id = int(parts[1])
        add_kg = int(parts[2])
        
        hryak = get_hryak(user_id, message.chat.id)
        if not hryak:
            bot.reply_to(message, f"❌ У користувача {user_id} немає хряка!")
            return
        
        old_weight = hryak['weight']
        hryak['weight'] += add_kg
        save_hryaky()
        
        bot.reply_to(message, f"""✅ Додано вагу!

Користувач: {user_id}
Було: {old_weight} кг
Додано: +{add_kg} кг
Стало: {hryak['weight']} кг""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addweight: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_addcoins'])
def admin_add_coins(message):
    """Додати монети користувачу"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addcoins <user_id> <сума>")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        currency = get_user_currency(user_id, message.chat.id)
        old_coins = currency.get('coins', 0)
        
        update_user_currency(user_id, message.chat.id, coins=old_coins + amount)
        
        bot.reply_to(message, f"""✅ Додано монети!

Користувач: {user_id}
Було: {old_coins} монет
Додано: +{amount} монет
Стало: {old_coins + amount} монет""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addcoins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_addxp'])
def admin_add_xp(message):
    """Додати XP користувачу"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addxp <user_id> <сума>")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        currency = get_user_currency(user_id, message.chat.id)
        old_xp = currency.get('xp', 0)
        
        update_user_currency(user_id, message.chat.id, xp=old_xp + amount)
        
        bot.reply_to(message, f"""✅ Додано XP!

Користувач: {user_id}
Було: {old_xp} XP
Додано: +{amount} XP
Стало: {old_xp + amount} XP""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addxp: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_additem'])
def admin_add_item(message):
    """Додати предмет користувачу"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ Використання: /admin_additem <user_id> <предмет> <кількість>")
            return
        
        user_id = int(parts[1])
        item_name = parts[2]
        quantity = int(parts[3])
        
        add_item_to_user(user_id, message.chat.id, 'item', item_name, 'legendary', 'power', 100, quantity)
        
        bot.reply_to(message, f"""✅ Додано предмет!

Користувач: {user_id}
Предмет: {item_name}
Кількість: x{quantity}""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_additem: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_stats'])
def admin_stats(message):
    """Статистика бота"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Доступ заборонено! Тільки адмін.")
            return
        
        # Рахуємо користувачів
        total_users = len(stats_data)
        total_hryaky = len(hryaky_data)
        
        text = f"""📊 СТАТИСТИКА БОТА

👥 Всього користувачів: {total_users}
🐷 Всього хряків: {total_hryaky}

**Адмін:**
Твій ID: {message.from_user.id}
ADMIN_ID: {ADMIN_ID}"""
        
        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ Помилка /admin_stats: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@bot.message_handler(commands=['admin_help'])
def admin_help(message):
    """Допомога по адмін командам"""
    try:
        # Детальне логування
        user_id = message.from_user.id
        admin_id = ADMIN_ID
        
        logger.info(f"🛡️ Admin command: user_id={user_id}, ADMIN_ID={admin_id}")
        logger.info(f"is_admin check: {user_id} == {admin_id} = {user_id == admin_id}")
        
        # Перевірка адміна всередині функції
        if user_id != admin_id:
            logger.warning(f"❌ ACCESS DENIED: user {user_id} != admin {admin_id}")
            bot.reply_to(message, f"❌ Доступ заборонено! Тільки адмін.\n\nВаш ID: {user_id}\nAdmin ID: {admin_id}")
            return
        
        logger.info(f"✅ ACCESS GRANTED: user {user_id} == admin {admin_id}")
        
        text = f"""🛡️ АДМІН КОМАНДИ

**Хряки:**
/admin_weight <user_id> <вага> - змінити вагу
/admin_addweight <user_id> <кг> - додати вагу

**Валюта:**
/admin_addcoins <user_id> <сума> - додати монети
/admin_addxp <user_id> <сума> - додати XP

**Предмети:**
/admin_additem <user_id> <предмет> <кількість> - додати предмет

**Інше:**
/admin_stats - статистика бота
/admin_help - ця довідка

**Твій ID:** {user_id}
**ADMIN_ID:** {admin_id}"""
        
        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ Помилка /admin_help: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


# ============================================
# НОВІ АДМІН КОМАНДИ - РОЗШИРЕНІ
# ============================================

@admin_only
@bot.message_handler(commands=['admin_removecoins'])
def admin_remove_coins(message):
    """Відняти монети у гравця"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removecoins <user_id> <сума>")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        currency = get_user_currency(user_id, message.chat.id)
        old_coins = currency.get('coins', 0)
        
        if old_coins < amount:
            bot.reply_to(message, f"❌ У гравця недостатньо монет! Є: {old_coins}")
            return
        
        new_coins = old_coins - amount
        update_user_currency(user_id, message.chat.id, coins=new_coins)
        
        bot.reply_to(message, f"""✅ Віднято монети!

Гравець: {user_id}
Було: {old_coins} монет
Віднято: -{amount} монет
Стало: {new_coins} монет""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removecoins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_removexp'])
def admin_remove_xp(message):
    """Відняти XP у гравця"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removexp <user_id> <сума>")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        currency = get_user_currency(user_id, message.chat.id)
        old_xp = currency.get('xp', 0)
        
        if old_xp < amount:
            bot.reply_to(message, f"❌ У гравця недостатньо XP! Є: {old_xp}")
            return
        
        new_xp = old_xp - amount
        update_user_currency(user_id, message.chat.id, xp=new_xp)
        
        bot.reply_to(message, f"""✅ Віднято XP!

Гравець: {user_id}
Було: {old_xp} XP
Віднято: -{amount} XP
Стало: {new_xp} XP""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removexp: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_removeweight'])
def admin_remove_weight(message):
    """Відняти вагу хряка"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removeweight <user_id> <кг>")
            return
        
        user_id = int(parts[1])
        remove_kg = int(parts[2])
        
        if remove_kg <= 0:
            bot.reply_to(message, "❌ Кількість має бути додатною!")
            return
        
        hryak = get_hryak(user_id, message.chat.id)
        if not hryak:
            bot.reply_to(message, f"❌ У гравця {user_id} немає хряка!")
            return
        
        old_weight = hryak['weight']
        new_weight = max(1, old_weight - remove_kg)
        hryak['weight'] = new_weight
        save_hryaky()
        
        bot.reply_to(message, f"""✅ Віднято вагу!

Гравець: {user_id}
Було: {old_weight} кг
Віднято: -{remove_kg} кг
Стало: {new_weight} кг""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removeweight: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_removeitem'])
def admin_remove_item(message):
    """Видалити предмет у гравця"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removeitem <user_id> <предмет> [кількість]")
            return
        
        user_id = int(parts[1])
        item_name = parts[2]
        quantity = int(parts[3]) if len(parts) > 3 else 1
        
        if quantity <= 0:
            bot.reply_to(message, "❌ Кількість має бути додатною!")
            return
        
        chat_id = message.chat.id
        from db import remove_user_item
        if remove_user_item(user_id, chat_id, item_name, quantity):
            bot.reply_to(message, f"""✅ Видалено предмет!

Гравець: {user_id}
Предмет: {item_name}
Кількість: -{quantity}""")
        else:
            bot.reply_to(message, f"❌ У гравця немає предмета '{item_name}'!")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removeitem: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_clearinventory'])
def admin_clear_inventory(message):
    """Очистити інвентар гравця"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Використання: /admin_clearinventory <user_id>")
            return
        
        user_id = int(parts[1])
        chat_id = message.chat.id
        
        from db import get_user_items, remove_user_item
        items = get_user_items(user_id, chat_id)
        
        if not items:
            bot.reply_to(message, f"✅ Інвентар гравця {user_id} і так пустий!")
            return
        
        removed_count = 0
        for item in items:
            if remove_user_item(user_id, chat_id, item['item_name'], item['quantity']):
                removed_count += 1
        
        bot.reply_to(message, f"""✅ Інвентар очищено!

Гравець: {user_id}
Видалено предметів: {removed_count}""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_clearinventory: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_addskin'])
def admin_add_skin(message):
    """Додати скін гравцю"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addskin <user_id> <скін>")
            return
        
        user_id = int(parts[1])
        skin_name = parts[2]
        chat_id = message.chat.id
        
        from db import get_skin_by_name, buy_skin
        skin = get_skin_by_name(skin_name)
        
        if not skin:
            bot.reply_to(message, f"❌ Скін '{skin_name}' не знайдено!")
            return
        
        if buy_skin(user_id, chat_id, skin['id']):
            bot.reply_to(message, f"""✅ Додано скін!

Гравець: {user_id}
Скін: {skin['display_name']}
ID скіну: {skin['id']}""")
        else:
            bot.reply_to(message, "❌ Помилка додавання скіну!")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addskin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_removeskin'])
def admin_remove_skin(message):
    """Видалити скін у гравця"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removeskin <user_id> <скін>")
            return
        
        user_id = int(parts[1])
        skin_name = parts[2]
        chat_id = message.chat.id
        
        from db import get_skin_by_name, get_connection
        skin = get_skin_by_name(skin_name)
        
        if not skin:
            bot.reply_to(message, f"❌ Скін '{skin_name}' не знайдено!")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM user_skins
            WHERE user_id = %s AND chat_id = %s AND skin_id = %s
        ''', (user_id, chat_id, skin['id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        bot.reply_to(message, f"""✅ Видалено скін!

Гравець: {user_id}
Скін: {skin['display_name']}""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removeskin: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_addguildcoins'])
def admin_add_guild_coins(message):
    """Додати монети гільдії"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addguildcoins <guild_id> <сума>")
            return
        
        guild_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        from db import get_guild, get_connection
        guild = get_guild(guild_id)
        
        if not guild:
            bot.reply_to(message, f"❌ Гільдія {guild_id} не знайдена!")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE guilds SET coins = coins + %s WHERE id = %s
        ''', (amount, guild_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        bot.reply_to(message, f"""✅ Додано монети гільдії!

Гільдія: {guild['name']} (ID: {guild_id})
Додано: +{amount} монет
Було: {guild['coins']} монет
Стало: {guild['coins'] + amount} монет""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addguildcoins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_removeguildcoins'])
def admin_remove_guild_coins(message):
    """Відняти монети гільдії"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_removeguildcoins <guild_id> <сума>")
            return
        
        guild_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        from db import get_guild, get_connection
        guild = get_guild(guild_id)
        
        if not guild:
            bot.reply_to(message, f"❌ Гільдія {guild_id} не знайдена!")
            return
        
        if guild['coins'] < amount:
            bot.reply_to(message, f"❌ У гільдії недостатньо монет! Є: {guild['coins']}")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE guilds SET coins = coins - %s WHERE id = %s
        ''', (amount, guild_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        bot.reply_to(message, f"""✅ Віднято монети гільдії!

Гільдія: {guild['name']} (ID: {guild_id})
Віднято: -{amount} монет
Було: {guild['coins']} монет
Стало: {guild['coins'] - amount} монет""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_removeguildcoins: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


@admin_only
@bot.message_handler(commands=['admin_addguildxp'])
def admin_add_guild_xp(message):
    """Додати XP гільдії"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Використання: /admin_addguildxp <guild_id> <сума>")
            return
        
        guild_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сума має бути додатною!")
            return
        
        from db import get_guild, update_guild_xp
        guild = get_guild(guild_id)
        
        if not guild:
            bot.reply_to(message, f"❌ Гільдія {guild_id} не знайдена!")
            return
        
        update_guild_xp(guild_id, amount)
        
        bot.reply_to(message, f"""✅ Додано XP гільдії!

Гільдія: {guild['name']} (ID: {guild_id})
Додано: +{amount} XP
Було: {guild['xp']} XP
Стало: {guild['xp'] + amount} XP""")
    except Exception as e:
        logger.error(f"❌ Помилка /admin_addguildxp: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Помилка: {e}")


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
                logger.error("❌ Максимальна кіль��ість с�����об вичерпана")
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
    btn_achievements = types.InlineKeyboardButton("🏅 Досяг��ення", switch_inline_query="achievements")

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
            title='���️ Нагодувати хряка',
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

