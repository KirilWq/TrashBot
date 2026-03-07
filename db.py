import psycopg
import os
import json
import time
import logging

logger = logging.getLogger(__name__)

# Отримуємо connection string зі змінних середовища
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Отримує з'єднання з базою"""
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL не знайдено!")
        return None
    
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Помилка підключення до БД: {e}")
        return None

def init_db():
    """Ініціалізація таблиць"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        # Таблиця хряків
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hryaky (
                key TEXT PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                username TEXT,
                name TEXT,
                weight BIGINT,
                last_feed BIGINT,
                feed_count BIGINT,
                max_weight BIGINT,
                created_at BIGINT,
                has_lost_weight BOOLEAN DEFAULT FALSE,
                max_gain BIGINT DEFAULT 0,
                max_gains_20 BIGINT DEFAULT 0,
                fed_on_1st BOOLEAN DEFAULT FALSE
            )
        ''')
        logger.info("✅ Таблиця hryaky створена/перевірена")

        # Міграція: конвертуємо REAL в BIGINT для існуючих даних
        try:
            cursor.execute('ALTER TABLE hryaky ALTER COLUMN created_at TYPE BIGINT USING CAST(created_at AS BIGINT)')
            cursor.execute('ALTER TABLE hryaky ALTER COLUMN last_feed TYPE BIGINT USING CAST(last_feed AS BIGINT)')
            logger.info("✅ Міграція hryaky завершена")
        except Exception as e:
            logger.debug(f"Міграція hryaky: {e}")

        # Таблиця статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                username TEXT,
                count BIGINT DEFAULT 0,
                first_message BIGINT,
                last_message BIGINT
            )
        ''')
        logger.info("✅ Таблиця stats створена/перевірена")

        # Міграція: конвертуємо REAL в BIGINT
        try:
            cursor.execute('ALTER TABLE stats ALTER COLUMN first_message TYPE BIGINT USING CAST(first_message AS BIGINT)')
            cursor.execute('ALTER TABLE stats ALTER COLUMN last_message TYPE BIGINT USING CAST(last_message AS BIGINT)')
            logger.info("✅ Міграція stats завершена")
        except Exception as e:
            logger.debug(f"Міграція stats: {e}")

        # Таблиця попереджень
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warns (
                key TEXT PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                username TEXT,
                warns_json TEXT,
                banned BOOLEAN DEFAULT FALSE
            )
        ''')
        logger.info("✅ Таблиця warns створена/перевірена")

        # Таблиця спаму
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spam (
                key TEXT PRIMARY KEY,
                messages_json TEXT,
                muted BOOLEAN DEFAULT FALSE,
                mute_until BIGINT
            )
        ''')
        logger.info("✅ Таблиця spam створена/перевірена")

        # Міграція: конвертуємо REAL в BIGINT
        try:
            cursor.execute('ALTER TABLE spam ALTER COLUMN mute_until TYPE BIGINT USING CAST(mute_until AS BIGINT)')
            logger.info("✅ Міграція spam завершена")
        except Exception as e:
            logger.debug(f"Міграція spam: {e}")

        # Таблиця ручних юзернеймів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manual_users (
                key TEXT PRIMARY KEY,
                chat_id BIGINT,
                users_json TEXT
            )
        ''')
        logger.info("✅ Таблиця manual_users створена/перевірена")

        conn.commit()
        logger.info("✅ База даних ініціалізована")
    except Exception as e:
        logger.error(f"❌ Помилка ініціалізації БД: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# Функції для хряків
def get_hryak_from_db(key):
    """Отримує хряка з БД"""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM hryaky WHERE key = %s', (key,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'user_id': row[1],
            'chat_id': row[2],
            'username': row[3],
            'name': row[4],
            'weight': row[5],
            'last_feed': row[6],
            'feed_count': row[7],
            'max_weight': row[8],
            'created_at': row[9],
            'has_lost_weight': row[10] or False,
            'max_gain': row[11] or 0,
            'max_gains_20': row[12] or 0,
            'fed_on_1st': row[13] or False
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання хряка: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def save_hryak_to_db(key, hryak):
    """Зберігає хряка в БД"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO hryaky (key, user_id, chat_id, username, name, weight, last_feed, feed_count, max_weight, created_at, has_lost_weight, max_gain, max_gains_20, fed_on_1st)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                weight = EXCLUDED.weight,
                last_feed = EXCLUDED.last_feed,
                feed_count = EXCLUDED.feed_count,
                max_weight = EXCLUDED.max_weight,
                has_lost_weight = EXCLUDED.has_lost_weight,
                max_gain = EXCLUDED.max_gain,
                max_gains_20 = EXCLUDED.max_gains_20,
                fed_on_1st = EXCLUDED.fed_on_1st
        ''', (
            key, int(hryak['user_id']), int(hryak['chat_id']), hryak['username'], hryak['name'],
            int(hryak['weight']), int(hryak['last_feed']), int(hryak['feed_count']), int(hryak['max_weight']),
            int(hryak['created_at']), bool(hryak.get('has_lost_weight', False)), int(hryak.get('max_gain', 0)),
            int(hryak.get('max_gains_20', 0)), bool(hryak.get('fed_on_1st', False))
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка збереження хряка: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def load_from_db(hryaky_data, stats_data, warns_data, spam_data, manual_users):
    """Завантажує всі дані з бази в пам'ять"""
    global logger
    import logging
    logger = logging.getLogger(__name__)
    
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Завантажуємо хряків
        cursor.execute('SELECT key, user_id, chat_id, username, name, weight, last_feed, feed_count, max_weight, created_at, has_lost_weight, max_gain, max_gains_20, fed_on_1st FROM hryaky')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            hryaky_data[key] = {
                'user_id': row[1],
                'chat_id': row[2],
                'username': row[3],
                'name': row[4],
                'weight': row[5],
                'last_feed': row[6],
                'feed_count': row[7],
                'max_weight': row[8],
                'created_at': row[9],
                'has_lost_weight': row[10] or False,
                'max_gain': row[11] or 0,
                'max_gains_20': row[12] or 0,
                'fed_on_1st': row[13] or False
            }
        logger.info(f"📦 Завантажено {len(hryaky_data)} хряків з БД")
        
        # Завантажуємо статистику
        cursor.execute('SELECT key, user_id, chat_id, username, count, first_message, last_message FROM stats')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            stats_data[key] = {
                'user_id': row[1],
                'chat_id': row[2],
                'username': row[3],
                'count': row[4],
                'first_message': row[5],
                'last_message': row[6]
            }
        logger.info(f"📊 Завантажено {len(stats_data)} записів статистики з БД")
        
        # Завантажуємо попередження
        cursor.execute('SELECT key, user_id, chat_id, username, warns_json, banned FROM warns')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            warns_data[key] = {
                'user_id': row[1],
                'chat_id': row[2],
                'username': row[3],
                'warns': json.loads(row[4]) if row[4] else [],
                'banned': bool(row[5])
            }
        logger.info(f"⚠️ Завантажено {len(warns_data)} записів попереджень з БД")
        
        # Завантажуємо спам
        cursor.execute('SELECT key, messages_json, muted, mute_until FROM spam')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            spam_data[key] = {
                'messages': json.loads(row[1]) if row[1] else [],
                'muted': bool(row[2]),
                'mute_until': row[3] if row[3] else 0
            }
        logger.info(f"🛡️ Завантажено {len(spam_data)} записів спаму з БД")
        
        # Завантажуємо ручних юзернеймів
        cursor.execute('SELECT key, chat_id, users_json FROM manual_users')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            chat_id = row[1]
            manual_users[chat_id] = json.loads(row[2]) if row[2] else []
        logger.info(f"👥 Завантажено {len(manual_users)} чатів з ручними юзернеймами")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження з БД: {e}")
    finally:
        cursor.close()
        conn.close()

# Функції для статистики
def save_stats_to_db(stats_data):
    """Зберігає статистику в БД"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        for key, data in stats_data.items():
            cursor.execute('''
                INSERT INTO stats (key, user_id, chat_id, username, count, first_message, last_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    count = EXCLUDED.count,
                    last_message = EXCLUDED.last_message,
                    username = EXCLUDED.username
            ''', (key, int(data['user_id']), int(data['chat_id']), data['username'],
                  int(data['count']), int(data['first_message']), int(data['last_message'])))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка збереження статистики: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Функції для попереджень
def save_warns_to_db(warns_data):
    """Зберігає попередження в БД"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        for key, data in warns_data.items():
            cursor.execute('''
                INSERT INTO warns (key, user_id, chat_id, username, warns_json, banned)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    warns_json = EXCLUDED.warns_json,
                    banned = EXCLUDED.banned
            ''', (key, int(data['user_id']), int(data['chat_id']), data['username'],
                  json.dumps(data['warns']), bool(data['banned'])))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка збереження попереджень: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Функції для спаму
def save_spam_to_db(spam_data):
    """Зберігає спам дані в БД"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        for key, data in spam_data.items():
            cursor.execute('''
                INSERT INTO spam (key, messages_json, muted, mute_until)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    messages_json = EXCLUDED.messages_json,
                    muted = EXCLUDED.muted,
                    mute_until = EXCLUDED.mute_until
            ''', (key, json.dumps(data['messages']), bool(data['muted']), int(data['mute_until']) if data.get('mute_until') else None))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка збереження спаму: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Функції для ручних юзернеймів
def save_manual_users_to_db(manual_users):
    """Зберігає ручних юзернеймів в БД"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        for chat_id, users in manual_users.items():
            key = f"manual_{chat_id}"
            cursor.execute('''
                INSERT INTO manual_users (key, chat_id, users_json)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    users_json = EXCLUDED.users_json
            ''', (key, int(chat_id), json.dumps(users)))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка збереження юзернеймів: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
