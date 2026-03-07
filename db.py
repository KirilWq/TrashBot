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
        # Видаляємо старі таблиці для чистої міграції (тільки якщо існують)
        cursor.execute("DROP TABLE IF EXISTS user_inventory CASCADE")
        cursor.execute("DROP TABLE IF EXISTS shop_items CASCADE")
        cursor.execute("DROP TABLE IF EXISTS user_stats CASCADE")
        cursor.execute("DROP TABLE IF EXISTS daily_bonus CASCADE")
        cursor.execute("DROP TABLE IF EXISTS team_duels CASCADE")
        cursor.execute("DROP TABLE IF EXISTS lottery CASCADE")
        cursor.execute("DROP TABLE IF EXISTS daily_quests CASCADE")
        cursor.execute("DROP TABLE IF EXISTS user_currencies CASCADE")
        cursor.execute("DROP TABLE IF EXISTS manual_users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS spam CASCADE")
        cursor.execute("DROP TABLE IF EXISTS warns CASCADE")
        cursor.execute("DROP TABLE IF EXISTS stats CASCADE")
        cursor.execute("DROP TABLE IF EXISTS hryaky CASCADE")
        cursor.execute("DROP TABLE IF EXISTS boss_battle_participants CASCADE")
        # Не видаляємо skins, bosses, seasonal_events, guilds, tournaments - там вже є дані
        logger.info("🗑️ Старі таблиці видалено")

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
        logger.info("✅ Таблиця hryaky створена")

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
        logger.info("✅ Таблиця stats створена")

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
        logger.info("✅ Таблиця warns створена")

        # Таблиця спаму
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spam (
                key TEXT PRIMARY KEY,
                messages_json TEXT,
                muted BOOLEAN DEFAULT FALSE,
                mute_until BIGINT
            )
        ''')
        logger.info("✅ Таблиця spam створена")

        # Таблиця ручних юзернеймів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manual_users (
                key TEXT PRIMARY KEY,
                chat_id BIGINT,
                users_json TEXT
            )
        ''')
        logger.info("✅ Таблиця manual_users створена")

        # Таблиця валют (монети/XP)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_currencies (
                user_id BIGINT,
                chat_id BIGINT,
                coins BIGINT DEFAULT 0,
                xp BIGINT DEFAULT 0,
                level BIGINT DEFAULT 1,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця user_currencies створена")

        # Таблиця щоденних квестів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_quests (
                user_id BIGINT,
                chat_id BIGINT,
                quest_id TEXT,
                progress BIGINT DEFAULT 0,
                target BIGINT,
                completed BOOLEAN DEFAULT FALSE,
                claimed BOOLEAN DEFAULT FALSE,
                reset_date DATE,
                PRIMARY KEY (user_id, chat_id, quest_id)
            )
        ''')
        logger.info("✅ Таблиця daily_quests створена")

        # Таблиця лотереї
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lottery (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                jackpot BIGINT DEFAULT 1000,
                last_draw BIGINT,
                participants_json TEXT
            )
        ''')
        logger.info("✅ Таблиця lottery створена")

        # Таблиця командних дуелей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_duels (
                duel_id TEXT PRIMARY KEY,
                chat_id BIGINT,
                team1_json TEXT,
                team2_json TEXT,
                status TEXT DEFAULT 'waiting',
                created_at BIGINT,
                started_at BIGINT,
                finished_at BIGINT,
                winner_team INTEGER
            )
        ''')
        logger.info("✅ Таблиця team_duels створена")

        # Таблиця щоденного бонусу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_bonus (
                user_id BIGINT,
                chat_id BIGINT,
                last_claim BIGINT,
                streak BIGINT DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця daily_bonus створена")

        # Таблиця статистики користувача
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id BIGINT,
                chat_id BIGINT,
                duels_won BIGINT DEFAULT 0,
                duels_lost BIGINT DEFAULT 0,
                quests_completed BIGINT DEFAULT 0,
                total_weight_gained BIGINT DEFAULT 0,
                casino_wins BIGINT DEFAULT 0,
                casino_losses BIGINT DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця user_stats створена")

        # Таблиця магазину
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                item_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                price BIGINT,
                price_currency TEXT DEFAULT 'coins',
                effect_type TEXT,
                effect_value BIGINT,
                duration BIGINT DEFAULT 0
            )
        ''')
        logger.info("✅ Таблиця shop_items створена")

        # Таблиця інвентарю
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                user_id BIGINT,
                chat_id BIGINT,
                item_id TEXT,
                quantity BIGINT DEFAULT 1,
                expires_at BIGINT,
                PRIMARY KEY (user_id, chat_id, item_id)
            )
        ''')
        logger.info("✅ Таблиця user_inventory створена")

        # Таблиця трахензебітену (спарювань)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trachenzebiten (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                partner_user_id BIGINT,
                partner_hryak_name TEXT,
                weight_change BIGINT,
                energy_used BIGINT DEFAULT 10,
                created_at BIGINT,
                UNIQUE(user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця trachenzebiten створена")

        # Таблиця вагітностей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pregnancies (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                father_user_id BIGINT,
                father_hryak_name TEXT,
                mother_hryak_name TEXT,
                is_pregnant BOOLEAN DEFAULT TRUE,
                pregnancy_start BIGINT,
                due_date BIGINT,
                children_count INTEGER DEFAULT 0,
                claimed BOOLEAN DEFAULT FALSE
            )
        ''')
        logger.info("✅ Таблиця pregnancies створена")

        # Таблиця дітей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS children (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                father_user_id BIGINT,
                mother_user_id BIGINT,
                name TEXT,
                weight INTEGER,
                inherited_trait TEXT,
                born_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця children створена")

        # Таблиця турнірів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                name TEXT,
                entry_fee BIGINT DEFAULT 10,
                status TEXT DEFAULT 'waiting',
                participants_json TEXT,
                winner_id BIGINT,
                prize_pool BIGINT DEFAULT 0,
                created_at BIGINT,
                started_at BIGINT,
                finished_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця tournaments створена")

        # Таблиця учасників турніру
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER,
                user_id BIGINT,
                chat_id BIGINT,
                hryak_weight BIGINT,
                eliminated BOOLEAN DEFAULT FALSE,
                eliminated_round INTEGER,
                joined_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця tournament_participants створена")

        # Таблиця учасників бос-дуелей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boss_battle_participants (
                id SERIAL PRIMARY KEY,
                boss_id INTEGER,
                user_id BIGINT,
                chat_id BIGINT,
                damage_dealt BIGINT DEFAULT 0,
                joined_at BIGINT,
                UNIQUE(boss_id, user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця boss_battle_participants створена")

        # Таблиця гільдій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                name TEXT UNIQUE,
                owner_user_id BIGINT,
                description TEXT,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                member_count INTEGER DEFAULT 1,
                created_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця guilds створена")

        # Таблиця членів гільдії
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_members (
                id SERIAL PRIMARY KEY,
                guild_id INTEGER,
                user_id BIGINT,
                chat_id BIGINT,
                role TEXT DEFAULT 'member',
                joined_at BIGINT,
                contribution INTEGER DEFAULT 0,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_members створена")

        # Таблиця скінів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skins (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                display_name TEXT,
                description TEXT,
                price INTEGER DEFAULT 0,
                rarity TEXT DEFAULT 'common',
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                icon TEXT
            )
        ''')
        logger.info("✅ Таблиця skins створена")

        # Таблиця скінів користувача
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_skins (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                skin_id INTEGER,
                equipped BOOLEAN DEFAULT FALSE,
                obtained_at BIGINT,
                FOREIGN KEY (skin_id) REFERENCES skins(id) ON DELETE CASCADE,
                UNIQUE(user_id, chat_id, skin_id)
            )
        ''')
        logger.info("✅ Таблиця user_skins створена")

        # Таблиця босів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bosses (
                id SERIAL PRIMARY KEY,
                name TEXT,
                level INTEGER,
                health BIGINT,
                max_health BIGINT,
                damage BIGINT,
                reward_coins INTEGER,
                reward_xp INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                spawn_date BIGINT,
                defeat_date BIGINT,
                defeated_by_user_id BIGINT
            )
        ''')
        logger.info("✅ Таблиця bosses створена")

        # Таблиця участі в бос-дуелях
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boss_battle_participants (
                id SERIAL PRIMARY KEY,
                boss_id INTEGER,
                user_id BIGINT,
                chat_id BIGINT,
                damage_dealt BIGINT DEFAULT 0,
                joined_at BIGINT,
                FOREIGN KEY (boss_id) REFERENCES bosses(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця boss_battle_participants створена")

        # Додаємо першого боса
        now = int(time.time())
        cursor.execute('''
            INSERT INTO bosses (name, level, health, max_health, damage, reward_coins, reward_xp, spawn_date)
            VALUES ('🐲 Древній Дракон', 1, 1000, 1000, 50, 500, 250, %s)
        ''', (now,))
        logger.info("✅ Перший бос додано")

        # Таблиця сезонних івентів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_events (
                id SERIAL PRIMARY KEY,
                name TEXT,
                event_type TEXT,
                start_date BIGINT,
                end_date BIGINT,
                is_active BOOLEAN DEFAULT TRUE,
                special_reward_coins INTEGER DEFAULT 0,
                special_reward_xp INTEGER DEFAULT 0,
                description TEXT
            )
        ''')
        logger.info("✅ Таблиця seasonal_events створена")

        # Таблиця участі в івентах
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_participation (
                id SERIAL PRIMARY KEY,
                event_id INTEGER,
                user_id BIGINT,
                chat_id BIGINT,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                reward_claimed BOOLEAN DEFAULT FALSE,
                participated_at BIGINT,
                FOREIGN KEY (event_id) REFERENCES seasonal_events(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця event_participation створена")

        # Таблиця мов користувачів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_languages (
                user_id BIGINT PRIMARY KEY,
                language TEXT DEFAULT 'uk',
                updated_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця user_languages створена")

        # Додаємо тестовий івент
        now = int(time.time())
        cursor.execute('''
            INSERT INTO seasonal_events (name, event_type, start_date, end_date, is_active, special_reward_coins, special_reward_xp, description)
            VALUES 
            ('🎄 Різдвяний Івент', 'christmas', %s, %s, FALSE, 100, 50, 'Збері 10 сніжинок та отримай нагороду!'),
            ('🎃 Хелловін 2026', 'halloween', %s, %s, FALSE, 150, 75, 'Переможи 5 гарбузів-босів!'),
            ('🐰 Великодній Івент', 'easter', %s, %s, TRUE, 80, 40, 'Знайди 20 великодніх яєць!')
        ''', (
            now - 86400*30, now - 86400*23,  # Різдво (минуле)
            now - 86400*60, now - 86400*53,  # Хелловін (минуле)
            now, now + 86400*14  # Великдень (активний 14 днів)
        ))
        logger.info("✅ Сезонні івенти додано")

        # Додаємо скіни в базу (якщо не існують)
        skins_data = [
            ('classic', '🐷 Класичний', 'Звичайний хряк', 0, 'common', None, 0, '🐷'),
            ('wild', '🐗 Дикий кабан', 'Міцний як дуб', 100, 'rare', 'weight_bonus', 5, '🐗'),
            ('golden', '✨ Золотий', 'Багатий хряк', 500, 'epic', 'luck_bonus', 10, '✨'),
            ('rainbow', '🌈 Веселка', 'Яскравий як мрія', 1000, 'legendary', 'xp_bonus', 15, '🌈'),
            ('cyber', '🤖 Кіберхряк', 'Майбутнє вже тут', 2000, 'legendary', 'all_bonus', 20, '🤖'),
            ('royal', '👑 Королівський', 'Для обраних', 5000, 'mythic', 'all_bonus', 30, '👑')
        ]
        
        for skin in skins_data:
            cursor.execute('''
                INSERT INTO skins (name, display_name, description, price, rarity, bonus_type, bonus_value, icon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            ''', skin)
        logger.info("✅ Скіни додано в базу")

        # Додаємо першого боса (якщо не існує)
        now = int(time.time())
        cursor.execute('''
            INSERT INTO bosses (name, level, health, max_health, damage, reward_coins, reward_xp, spawn_date)
            SELECT '🐲 Древній Дракон', 1, 1000, 1000, 50, 500, 250, %s
            WHERE NOT EXISTS (SELECT 1 FROM bosses WHERE name = '🐲 Древній Дракон')
        ''', (now,))
        logger.info("✅ Перший бос додано")

        # Додаємо предмети в магазин (якщо не існують)
        shop_items_data = [
            ('vitamins', '🍎 Вітаміни', '+5 кг до наступного годування', 50, 'coins', 'weight_bonus', 5, 0),
            ('trainer', '💪 Тренажер', '+10% до проворності на 24 год', 100, 'coins', 'agility_bonus', 10, 86400),
            ('shield', '🛡️ Щит', 'Захист від -10% ваги в дуелі', 75, 'coins', 'shield', 10, 0),
            ('energy', '⚡ Енергетик', 'Зняти кулдаун з /feed', 30, 'coins', 'remove_cooldown', 0, 0),
            ('lucky_charm', '🍀 Підкова', '+5% шанс на перемогу в дуелі', 200, 'coins', 'luck_bonus', 5, 86400)
        ]
        
        for item in shop_items_data:
            cursor.execute('''
                INSERT INTO shop_items (item_id, name, description, price, price_currency, effect_type, effect_value, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_id) DO NOTHING
            ''', item)
        conn.commit()
        logger.info("✅ Предмети додано в магазин")

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
            'user_id': int(row[1]) if row[1] else None,
            'chat_id': int(row[2]) if row[2] else None,
            'username': row[3],
            'name': row[4],
            'weight': int(row[5]) if row[5] else 0,
            'last_feed': int(row[6]) if row[6] else 0,
            'feed_count': int(row[7]) if row[7] else 0,
            'max_weight': int(row[8]) if row[8] else 0,
            'created_at': int(row[9]) if row[9] else int(time.time()),
            'has_lost_weight': bool(row[10]) if row[10] is not None else False,
            'max_gain': int(row[11]) if row[11] is not None else 0,
            'max_gains_20': int(row[12]) if row[12] is not None else 0,
            'fed_on_1st': bool(row[13]) if row[13] is not None else False
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
                username = EXCLUDED.username,
                name = EXCLUDED.name,
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
                'user_id': int(row[1]) if row[1] else None,
                'chat_id': int(row[2]) if row[2] else None,
                'username': row[3],
                'name': row[4],
                'weight': int(row[5]) if row[5] else 0,
                'last_feed': int(row[6]) if row[6] else 0,
                'feed_count': int(row[7]) if row[7] else 0,
                'max_weight': int(row[8]) if row[8] else 0,
                'created_at': int(row[9]) if row[9] else int(time.time()),
                'has_lost_weight': bool(row[10]) if row[10] is not None else False,
                'max_gain': int(row[11]) if row[11] is not None else 0,
                'max_gains_20': int(row[12]) if row[12] is not None else 0,
                'fed_on_1st': bool(row[13]) if row[13] is not None else False
            }
        logger.info(f"📦 Завантажено {len(hryaky_data)} хряків з БД")

        # Завантажуємо статистику
        cursor.execute('SELECT key, user_id, chat_id, username, count, first_message, last_message FROM stats')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            stats_data[key] = {
                'user_id': int(row[1]) if row[1] else None,
                'chat_id': int(row[2]) if row[2] else None,
                'username': row[3],
                'count': int(row[4]) if row[4] else 0,
                'first_message': int(row[5]) if row[5] else 0,
                'last_message': int(row[6]) if row[6] else 0
            }
        logger.info(f"📊 Завантажено {len(stats_data)} записів статистики з БД")

        # Завантажуємо попередження
        cursor.execute('SELECT key, user_id, chat_id, username, warns_json, banned FROM warns')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            warns_data[key] = {
                'user_id': int(row[1]) if row[1] else None,
                'chat_id': int(row[2]) if row[2] else None,
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
                'mute_until': int(row[3]) if row[3] else 0
            }
        logger.info(f"🛡️ Завантажено {len(spam_data)} записів спаму з БД")

        # Завантажуємо ручних юзернеймів
        cursor.execute('SELECT key, chat_id, users_json FROM manual_users')
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            chat_id = int(row[1]) if row[1] else None
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


# ============================================
# ФУНКЦІЇ ДЛЯ ВАЛЮТИ (МОНЕТИ/XP)
# ============================================

def get_user_currency(user_id, chat_id):
    """Отримує валюту користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT coins, xp, level FROM user_currencies WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            # Створюємо новий запис
            cursor.execute('INSERT INTO user_currencies (user_id, chat_id, coins, xp, level) VALUES (%s, %s, 0, 0, 1)', (user_id, chat_id))
            conn.commit()
            return {'coins': 0, 'xp': 0, 'level': 1}
        return {'coins': int(row[0]), 'xp': int(row[1]), 'level': int(row[2])}
    except Exception as e:
        logger.error(f"❌ Помилка отримання валюти: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_user_currency(user_id, chat_id, coins=None, xp=None, level=None):
    """Оновлює валюту користувача"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        current = get_user_currency(user_id, chat_id)
        if not current:
            return

        new_coins = coins if coins is not None else current['coins']
        new_xp = xp if xp is not None else current['xp']
        new_level = level if level is not None else current['level']

        cursor.execute('''
            INSERT INTO user_currencies (user_id, chat_id, coins, xp, level)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                coins = EXCLUDED.coins,
                xp = EXCLUDED.xp,
                level = EXCLUDED.level
        ''', (user_id, chat_id, new_coins, new_xp, new_level))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення валюти: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def add_coins(user_id, chat_id, amount):
    """Додає монети"""
    current = get_user_currency(user_id, chat_id)
    if current:
        update_user_currency(user_id, chat_id, coins=current['coins'] + amount)

def add_xp(user_id, chat_id, amount):
    """Додає XP"""
    current = get_user_currency(user_id, chat_id)
    if current:
        new_xp = current['xp'] + amount
        # Level up кожні 100 XP
        new_level = current['level'] + (new_xp // 100)
        new_xp = new_xp % 100
        update_user_currency(user_id, chat_id, xp=new_xp, level=new_level)


# ============================================
# ФУНКЦІЇ ДЛЯ ЩОДЕННИХ КВЕСТІВ
# ============================================

def get_daily_quests(user_id, chat_id):
    """Отримує всі квести користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT quest_id, progress, target, completed, claimed, reset_date FROM daily_quests WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        rows = cursor.fetchall()
        quests = []
        for row in rows:
            quests.append({
                'quest_id': row[0],
                'progress': int(row[1]),
                'target': int(row[2]),
                'completed': bool(row[3]),
                'claimed': bool(row[4]),
                'reset_date': row[5]
            })
        return quests
    except Exception as e:
        logger.error(f"❌ Помилка отримання квестів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_daily_quest(user_id, chat_id, quest_id, progress, target, completed=False, claimed=False):
    """Оновлює прогрес квесту"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        today = time.strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO daily_quests (user_id, chat_id, quest_id, progress, target, completed, claimed, reset_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id, quest_id) DO UPDATE SET
                progress = EXCLUDED.progress,
                target = EXCLUDED.target,
                completed = EXCLUDED.completed,
                claimed = EXCLUDED.claimed,
                reset_date = EXCLUDED.reset_date
        ''', (user_id, chat_id, quest_id, progress, target, completed, claimed, today))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення квесту: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def reset_daily_quests(user_id, chat_id):
    """Скидає всі квести користувача"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        today = time.strftime('%Y-%m-%d')
        cursor.execute('UPDATE daily_quests SET progress = 0, completed = FALSE, claimed = FALSE, reset_date = %s WHERE user_id = %s AND chat_id = %s', (today, user_id, chat_id))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка скидання квестів: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ЛОТЕРЕЇ
# ============================================

def get_lottery(chat_id):
    """Отримує дані лотереї"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT jackpot, last_draw, participants_json FROM lottery WHERE chat_id = %s ORDER BY id DESC LIMIT 1', (chat_id,))
        row = cursor.fetchone()
        if not row:
            # Створюємо нову лотерею
            cursor.execute('INSERT INTO lottery (chat_id, jackpot, last_draw, participants_json) VALUES (%s, 1000, 0, %s)', (chat_id, '[]'))
            conn.commit()
            return {'jackpot': 1000, 'last_draw': 0, 'participants': []}
        return {'jackpot': int(row[0]), 'last_draw': int(row[1]), 'participants': json.loads(row[2]) if row[2] else []}
    except Exception as e:
        logger.error(f"❌ Помилка отримання лотереї: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_lottery(chat_id, jackpot, last_draw, participants):
    """Оновлює дані лотереї"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO lottery (chat_id, jackpot, last_draw, participants_json)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET
                jackpot = EXCLUDED.jackpot,
                last_draw = EXCLUDED.last_draw,
                participants_json = EXCLUDED.participants_json
        ''', (chat_id, jackpot, last_draw, json.dumps(participants)))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення лотереї: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ КОМАНДНИХ ДУЕЛЕЙ
# ============================================

def get_team_duel(duel_id):
    """Отримує дані дуелі"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT chat_id, team1_json, team2_json, status, created_at, started_at, finished_at, winner_team FROM team_duels WHERE duel_id = %s', (duel_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'duel_id': duel_id,
            'chat_id': int(row[0]),
            'team1': json.loads(row[1]) if row[1] else [],
            'team2': json.loads(row[2]) if row[2] else [],
            'status': row[3],
            'created_at': int(row[4]),
            'started_at': int(row[5]) if row[5] else None,
            'finished_at': int(row[6]) if row[6] else None,
            'winner_team': int(row[7]) if row[7] else None
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання дуелі: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_team_duel(duel_id, chat_id, team1, team2, status='waiting'):
    """Створює нову дуель"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO team_duels (duel_id, chat_id, team1_json, team2_json, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (duel_id, chat_id, json.dumps(team1), json.dumps(team2), status, now))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка створення дуелі: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def update_team_duel_status(duel_id, status, winner_team=None):
    """Оновлює статус дуелі"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        now = int(time.time())
        if status == 'started':
            cursor.execute('UPDATE team_duels SET status = %s, started_at = %s WHERE duel_id = %s', (status, now, duel_id))
        elif status == 'finished':
            cursor.execute('UPDATE team_duels SET status = %s, finished_at = %s, winner_team = %s WHERE duel_id = %s', (status, now, winner_team, duel_id))
        else:
            cursor.execute('UPDATE team_duels SET status = %s WHERE duel_id = %s', (status, duel_id))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення дуелі: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ЩОДЕННОГО БОНУСУ
# ============================================

def get_daily_bonus(user_id, chat_id):
    """Отримує дані щоденного бонусу"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT last_claim, streak FROM daily_bonus WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            cursor.execute('INSERT INTO daily_bonus (user_id, chat_id, last_claim, streak) VALUES (%s, %s, 0, 0)', (user_id, chat_id))
            conn.commit()
            return {'last_claim': 0, 'streak': 0}
        return {'last_claim': int(row[0]), 'streak': int(row[1])}
    except Exception as e:
        logger.error(f"❌ Помилка отримання бонусу: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_daily_bonus(user_id, chat_id, last_claim, streak):
    """Оновлює дані щоденного бонусу"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO daily_bonus (user_id, chat_id, last_claim, streak)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                last_claim = EXCLUDED.last_claim,
                streak = EXCLUDED.streak
        ''', (user_id, chat_id, last_claim, streak))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення бонусу: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ СТАТИСТИКИ КОРИСТУВАЧА
# ============================================

def get_user_stats(user_id, chat_id):
    """Отримує статистику користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT duels_won, duels_lost, quests_completed, total_weight_gained, casino_wins, casino_losses FROM user_stats WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            cursor.execute('INSERT INTO user_stats (user_id, chat_id) VALUES (%s, %s)', (user_id, chat_id))
            conn.commit()
            return {'duels_won': 0, 'duels_lost': 0, 'quests_completed': 0, 'total_weight_gained': 0, 'casino_wins': 0, 'casino_losses': 0}
        return {
            'duels_won': int(row[0]),
            'duels_lost': int(row[1]),
            'quests_completed': int(row[2]),
            'total_weight_gained': int(row[3]),
            'casino_wins': int(row[4]),
            'casino_losses': int(row[5])
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_user_stats(user_id, chat_id, stats):
    """Оновлює статистику користувача"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_stats (user_id, chat_id, duels_won, duels_lost, quests_completed, total_weight_gained, casino_wins, casino_losses)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                duels_won = EXCLUDED.duels_won,
                duels_lost = EXCLUDED.duels_lost,
                quests_completed = EXCLUDED.quests_completed,
                total_weight_gained = EXCLUDED.total_weight_gained,
                casino_wins = EXCLUDED.casino_wins,
                casino_losses = EXCLUDED.casino_losses
        ''', (user_id, chat_id, stats.get('duels_won', 0), stats.get('duels_lost', 0),
              stats.get('quests_completed', 0), stats.get('total_weight_gained', 0),
              stats.get('casino_wins', 0), stats.get('casino_losses', 0)))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка оновлення статистики: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def increment_user_stat(user_id, chat_id, stat_name, amount=1):
    """Збільшує статистику на значення"""
    stats = get_user_stats(user_id, chat_id)
    if stats:
        stats[stat_name] = stats.get(stat_name, 0) + amount
        update_user_stats(user_id, chat_id, stats)

def update_casino_quest(user_id, chat_id, is_win):
    """Оновлює квести казино"""
    quests = get_daily_quests(user_id, chat_id)
    quest_progress = {q['quest_id']: q for q in quests}
    
    # Квест: виграти в казино (потрібно 3 перемоги)
    if is_win:
        casino_quest = quest_progress.get('casino_wins', {'progress': 0, 'target': 3})
        new_progress = min(casino_quest['progress'] + 1, 3)
        completed = new_progress >= 3
        update_daily_quest(user_id, chat_id, 'casino_wins', new_progress, 3, completed=completed)


# ============================================
# ФУНКЦІЇ ДЛЯ МАГАЗИНУ
# ============================================

def get_shop_items():
    """Отримує всі предмети магазину"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT item_id, name, description, price, price_currency, effect_type, effect_value, duration FROM shop_items')
        rows = cursor.fetchall()
        items = []
        for row in rows:
            items.append({
                'item_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': int(row[3]),
                'price_currency': row[4],
                'effect_type': row[5],
                'effect_value': int(row[6]),
                'duration': int(row[7])
            })
        return items
    except Exception as e:
        logger.error(f"❌ Помилка отримання магазину: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_item(item_id):
    """Отримує предмет за ID"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT item_id, name, description, price, price_currency, effect_type, effect_value, duration FROM shop_items WHERE item_id = %s', (item_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'item_id': row[0],
            'name': row[1],
            'description': row[2],
            'price': int(row[3]),
            'price_currency': row[4],
            'effect_type': row[5],
            'effect_value': int(row[6]),
            'duration': int(row[7])
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання предмету: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ІНВЕНТАРЮ
# ============================================

def add_to_inventory(user_id, chat_id, item_id, quantity=1, duration=0):
    """Додає предмет в інвентар"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        now = int(time.time())
        expires_at = now + duration if duration > 0 else None
        cursor.execute('''
            INSERT INTO user_inventory (user_id, chat_id, item_id, quantity, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id, item_id) DO UPDATE SET
                quantity = user_inventory.quantity + EXCLUDED.quantity,
                expires_at = EXCLUDED.expires_at
        ''', (user_id, chat_id, item_id, quantity, expires_at))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Помилка додавання до інвентарю: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def remove_from_inventory(user_id, chat_id, item_id, quantity=1):
    """Видаляє предмет з інвентарю"""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = %s AND chat_id = %s AND item_id = %s', (user_id, chat_id, item_id))
        row = cursor.fetchone()
        if row and row[0] >= quantity:
            if row[0] == quantity:
                cursor.execute('DELETE FROM user_inventory WHERE user_id = %s AND chat_id = %s AND item_id = %s', (user_id, chat_id, item_id))
            else:
                cursor.execute('UPDATE user_inventory SET quantity = quantity - %s WHERE user_id = %s AND chat_id = %s AND item_id = %s', (quantity, user_id, chat_id, item_id))
            conn.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Помилка видалення з інвентарю: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def has_item(user_id, chat_id, item_id):
    """Перевіряє наявність предмету"""
    inventory = get_user_inventory(user_id, chat_id)
    for item in inventory:
        if item['item_id'] == item_id and item['quantity'] > 0:
            return True
    return False

def get_item_effect(user_id, chat_id, effect_type):
    """Отримує ефект предмету"""
    inventory = get_user_inventory(user_id, chat_id)
    items = get_shop_items()
    total_effect = 0
    now = int(time.time())

    for inv_item in inventory:
        if inv_item['expires_at'] is None or inv_item['expires_at'] > now:
            for item in items:
                if item['item_id'] == inv_item['item_id'] and item['effect_type'] == effect_type:
                    total_effect += item['effect_value'] * inv_item['quantity']

    return total_effect


# ============================================
# ФУНКЦІЇ ДЛЯ ТРАХЕНЗЕБІТЕНУ (СПАРЮВАННЯ)
# ============================================

def get_trachen_stats(user_id, chat_id):
    """Отримує статистику трахензебітену користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_times,
                COUNT(DISTINCT partner_user_id) as unique_partners,
                SUM(weight_change) as total_weight_change
            FROM trachenzebiten 
            WHERE user_id = %s AND chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return {'total_times': 0, 'unique_partners': 0, 'total_weight_change': 0}
        return {
            'total_times': int(row[0]) if row[0] else 0,
            'unique_partners': int(row[1]) if row[1] else 0,
            'total_weight_change': int(row[2]) if row[2] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики трахензебітену: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_last_trachen_time(user_id, chat_id):
    """Отримує час останнього трахензебітену"""
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT created_at FROM trachenzebiten WHERE user_id = %s AND chat_id = %s ORDER BY id DESC LIMIT 1', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return 0
        return int(row[0])
    except Exception as e:
        logger.error(f"❌ Помилка отримання часу трахензебітену: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def add_trachen_record(user_id, chat_id, partner_user_id, partner_hryak_name, weight_change, energy_used=10):
    """Додає запис про трахензебітен"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO trachenzebiten (user_id, chat_id, partner_user_id, partner_hryak_name, weight_change, energy_used, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                partner_user_id = EXCLUDED.partner_user_id,
                partner_hryak_name = EXCLUDED.partner_hryak_name,
                weight_change = EXCLUDED.weight_change,
                energy_used = EXCLUDED.energy_used,
                created_at = EXCLUDED.created_at
        ''', (user_id, chat_id, partner_user_id, partner_hryak_name, weight_change, energy_used, int(time.time())))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка додавання запису трахензебітену: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_pregnancy(user_id, chat_id):
    """Отримує вагітність користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM pregnancies 
            WHERE user_id = %s AND chat_id = %s AND is_pregnant = TRUE 
            ORDER BY id DESC LIMIT 1
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'user_id': int(row[1]),
            'chat_id': int(row[2]),
            'father_user_id': int(row[3]),
            'father_hryak_name': row[4],
            'mother_hryak_name': row[5],
            'is_pregnant': bool(row[6]),
            'pregnancy_start': int(row[7]) if row[7] else 0,
            'due_date': int(row[8]) if row[8] else 0,
            'children_count': int(row[9]) if row[9] else 0,
            'claimed': bool(row[10])
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання вагітності: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_pregnancy(user_id, chat_id, father_user_id, father_hryak_name, mother_hryak_name, children_count=1):
    """Створює вагітність"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        due_date = now + (10 * 60)  # 10 хвилин для тестування (можна змінити на 24*60*60 для 24 годин)
        cursor.execute('''
            INSERT INTO pregnancies (user_id, chat_id, father_user_id, father_hryak_name, mother_hryak_name, pregnancy_start, due_date, children_count, is_pregnant, claimed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, FALSE)
        ''', (user_id, chat_id, father_user_id, father_hryak_name, mother_hryak_name, now, due_date, children_count))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка створення вагітності: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def claim_pregnancy(pregnancy_id):
    """Позначає вагітність як виконану"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE pregnancies SET is_pregnant = FALSE, claimed = TRUE WHERE id = %s', (pregnancy_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення вагітності: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_children(user_id, chat_id):
    """Отримує всіх дітей користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM children 
            WHERE (user_id = %s OR mother_user_id = %s OR father_user_id = %s) AND chat_id = %s
            ORDER BY born_at DESC
        ''', (user_id, user_id, user_id, chat_id))
        rows = cursor.fetchall()
        children = []
        for row in rows:
            children.append({
                'id': int(row[0]),
                'user_id': int(row[1]),
                'chat_id': int(row[2]),
                'father_user_id': int(row[3]),
                'mother_user_id': int(row[4]),
                'name': row[5],
                'weight': int(row[6]) if row[6] else 0,
                'inherited_trait': row[7],
                'born_at': int(row[8]) if row[8] else 0
            })
        return children
    except Exception as e:
        logger.error(f"❌ Помилка отримання дітей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def add_child(user_id, chat_id, father_user_id, mother_user_id, name, weight, inherited_trait=''):
    """Додає дитину"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO children (user_id, chat_id, father_user_id, mother_user_id, name, weight, inherited_trait, born_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, chat_id, father_user_id, mother_user_id, name, weight, inherited_trait, int(time.time())))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка додавання дитини: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_pregnancies(chat_id):
    """Отримує всі вагітності в чаті"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM pregnancies 
            WHERE chat_id = %s AND is_pregnant = TRUE 
            ORDER BY due_date ASC
        ''', (chat_id,))
        rows = cursor.fetchall()
        pregnancies = []
        for row in rows:
            pregnancies.append({
                'id': int(row[0]),
                'user_id': int(row[1]),
                'chat_id': int(row[2]),
                'father_user_id': int(row[3]),
                'father_hryak_name': row[4],
                'mother_hryak_name': row[5],
                'is_pregnant': bool(row[6]),
                'pregnancy_start': int(row[7]) if row[7] else 0,
                'due_date': int(row[8]) if row[8] else 0,
                'children_count': int(row[9]) if row[9] else 0,
                'claimed': bool(row[10])
            })
        return pregnancies
    except Exception as e:
        logger.error(f"❌ Помилка отримання вагітностей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ТУРНІРІВ
# ============================================

def create_tournament(chat_id, name, entry_fee=10):
    """Створює новий турнір"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO tournaments (chat_id, name, entry_fee, status, prize_pool, created_at)
            VALUES (%s, %s, %s, 'waiting', 0, %s)
            RETURNING id
        ''', (chat_id, name, entry_fee, now))
        tournament_id = cursor.fetchone()[0]
        conn.commit()
        return tournament_id
    except Exception as e:
        logger.error(f"❌ Помилка створення турніру: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_tournament(tournament_id):
    """Отримує турнір"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM tournaments WHERE id = %s', (tournament_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'chat_id': int(row[1]),
            'name': row[2],
            'entry_fee': int(row[3]) if row[3] else 10,
            'status': row[4],
            'participants_json': row[5],
            'winner_id': int(row[6]) if row[6] else None,
            'prize_pool': int(row[7]) if row[7] else 0,
            'created_at': int(row[8]) if row[8] else 0,
            'started_at': int(row[9]) if row[9] else 0,
            'finished_at': int(row[10]) if row[10] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання турніру: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_active_tournament(chat_id):
    """Отримує активний турнір в чаті"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM tournaments 
            WHERE chat_id = %s AND status IN ('waiting', 'in_progress') 
            ORDER BY id DESC LIMIT 1
        ''', (chat_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'chat_id': int(row[1]),
            'name': row[2],
            'entry_fee': int(row[3]) if row[3] else 10,
            'status': row[4],
            'participants_json': row[5],
            'winner_id': int(row[6]) if row[6] else None,
            'prize_pool': int(row[7]) if row[7] else 0,
            'created_at': int(row[8]) if row[8] else 0,
            'started_at': int(row[9]) if row[9] else 0,
            'finished_at': int(row[10]) if row[10] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання активного турніру: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def join_tournament(tournament_id, user_id, chat_id, hryak_weight):
    """Додає учасника до турніру"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO tournament_participants (tournament_id, user_id, chat_id, hryak_weight, joined_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (tournament_id, user_id, chat_id, hryak_weight, now))
        
        # Оновлюємо призовий фонд
        cursor.execute('SELECT entry_fee FROM tournaments WHERE id = %s', (tournament_id,))
        fee = cursor.fetchone()[0]
        cursor.execute('''
            UPDATE tournaments 
            SET prize_pool = prize_pool + %s 
            WHERE id = %s
        ''', (fee, tournament_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка вступу до турніру: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_tournament_participants(tournament_id):
    """Отримує учасників турніру"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM tournament_participants 
            WHERE tournament_id = %s AND eliminated = FALSE
            ORDER BY hryak_weight DESC
        ''', (tournament_id,))
        rows = cursor.fetchall()
        participants = []
        for row in rows:
            participants.append({
                'id': int(row[0]),
                'tournament_id': int(row[1]),
                'user_id': int(row[2]),
                'chat_id': int(row[3]),
                'hryak_weight': int(row[4]) if row[4] else 0,
                'eliminated': bool(row[5]),
                'eliminated_round': int(row[6]) if row[6] else 0,
                'joined_at': int(row[7]) if row[7] else 0
            })
        return participants
    except Exception as e:
        logger.error(f"❌ Помилка отримання учасників: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_tournament_status(tournament_id, status, winner_id=None):
    """Оновлює статус турніру"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        if status == 'in_progress':
            cursor.execute('''
                UPDATE tournaments SET status = %s, started_at = %s WHERE id = %s
            ''', (status, now, tournament_id))
        elif status == 'finished':
            cursor.execute('''
                UPDATE tournaments 
                SET status = %s, finished_at = %s, winner_id = %s 
                WHERE id = %s
            ''', (status, now, winner_id, tournament_id))
        else:
            cursor.execute('''
                UPDATE tournaments SET status = %s WHERE id = %s
            ''', (status, tournament_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення статусу турніру: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def eliminate_participant(participant_id, round_num):
    """Вибування учасника"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE tournament_participants 
            SET eliminated = TRUE, eliminated_round = %s 
            WHERE id = %s
        ''', (round_num, participant_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка вибуття учасника: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_tournament_stats(user_id, chat_id):
    """Отримує статистику турнірів користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as tournaments_joined,
                SUM(CASE WHEN t.winner_id = %s THEN 1 ELSE 0 END) as tournaments_won,
                COALESCE(SUM(tp.hryak_weight), 0) as total_weight
            FROM tournament_participants tp
            JOIN tournaments t ON tp.tournament_id = t.id
            WHERE tp.user_id = %s AND tp.chat_id = %s
        ''', (user_id, user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return {'tournaments_joined': 0, 'tournaments_won': 0, 'total_weight': 0}
        return {
            'tournaments_joined': int(row[0]) if row[0] else 0,
            'tournaments_won': int(row[1]) if row[1] else 0,
            'total_weight': int(row[2]) if row[2] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики турнірів: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ГІЛЬДІЙ
# ============================================

def create_guild(chat_id, name, owner_user_id, description=""):
    """Створює нову гільдію"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO guilds (chat_id, name, owner_user_id, description, member_count, created_at)
            VALUES (%s, %s, %s, %s, 1, %s)
            RETURNING id
        ''', (chat_id, name, owner_user_id, description, now))
        guild_id = cursor.fetchone()[0]
        
        # Додаємо власника як члена
        cursor.execute('''
            INSERT INTO guild_members (guild_id, user_id, chat_id, role, joined_at, contribution)
            VALUES (%s, %s, %s, 'owner', %s, 0)
        ''', (guild_id, owner_user_id, chat_id, now))
        
        conn.commit()
        return guild_id
    except Exception as e:
        logger.error(f"❌ Помилка створення гільдії: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_guild(guild_id):
    """Отримує гільдію"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM guilds WHERE id = %s', (guild_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'chat_id': int(row[1]),
            'name': row[2],
            'owner_user_id': int(row[3]),
            'description': row[4],
            'level': int(row[5]) if row[5] else 1,
            'xp': int(row[6]) if row[6] else 0,
            'coins': int(row[7]) if row[7] else 0,
            'member_count': int(row[8]) if row[8] else 1,
            'created_at': int(row[9]) if row[9] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання гільдії: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_guild_by_name(name):
    """Отримує гільдію за назвою"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM guilds WHERE name = %s', (name,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'chat_id': int(row[1]),
            'name': row[2],
            'owner_user_id': int(row[3]),
            'description': row[4],
            'level': int(row[5]) if row[5] else 1,
            'xp': int(row[6]) if row[6] else 0,
            'coins': int(row[7]) if row[7] else 0,
            'member_count': int(row[8]) if row[8] else 1,
            'created_at': int(row[9]) if row[9] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання гільдії за назвою: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_guild(user_id, chat_id):
    """Отримує гільдію користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT g.* FROM guilds g
            JOIN guild_members gm ON g.id = gm.guild_id
            WHERE gm.user_id = %s AND gm.chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'chat_id': int(row[1]),
            'name': row[2],
            'owner_user_id': int(row[3]),
            'description': row[4],
            'level': int(row[5]) if row[5] else 1,
            'xp': int(row[6]) if row[6] else 0,
            'coins': int(row[7]) if row[7] else 0,
            'member_count': int(row[8]) if row[8] else 1,
            'created_at': int(row[9]) if row[9] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання гільдії користувача: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_guild_members(guild_id):
    """Отримує членів гільдії"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM guild_members 
            WHERE guild_id = %s 
            ORDER BY 
                CASE WHEN role = 'owner' THEN 1 
                     WHEN role = 'officer' THEN 2 
                     ELSE 3 END,
                contribution DESC
        ''', (guild_id,))
        rows = cursor.fetchall()
        members = []
        for row in rows:
            members.append({
                'id': int(row[0]),
                'guild_id': int(row[1]),
                'user_id': int(row[2]),
                'chat_id': int(row[3]),
                'role': row[4],
                'joined_at': int(row[5]) if row[5] else 0,
                'contribution': int(row[6]) if row[6] else 0
            })
        return members
    except Exception as e:
        logger.error(f"❌ Помилка отримання членів гільдії: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def join_guild(guild_id, user_id, chat_id):
    """Приєднується до гільдії"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO guild_members (guild_id, user_id, chat_id, role, joined_at, contribution)
            VALUES (%s, %s, %s, 'member', %s, 0)
        ''', (guild_id, user_id, chat_id, now))
        
        cursor.execute('''
            UPDATE guilds SET member_count = member_count + 1 WHERE id = %s
        ''', (guild_id,))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка вступу до гільдії: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def leave_guild(guild_id, user_id):
    """Виходить з гільдії"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Перевіряємо чи не власник
        cursor.execute('SELECT owner_user_id FROM guilds WHERE id = %s', (guild_id,))
        row = cursor.fetchone()
        if row and row[0] == user_id:
            logger.error("❌ Власник не може вийти з гільдії, має передати володіння")
            return False
        
        cursor.execute('DELETE FROM guild_members WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        cursor.execute('''
            UPDATE guilds SET member_count = member_count - 1 WHERE id = %s
        ''', (guild_id,))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка виходу з гільдії: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_guild_rank(guild_id, user_id):
    """Отримує роль користувача в гільдії"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT role, contribution FROM guild_members 
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'role': row[0],
            'contribution': int(row[1]) if row[1] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання ролі в гільдії: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_guild_xp(guild_id, xp):
    """Оновлює XP гільдії"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE guilds SET xp = xp + %s, level = level + FLOOR((xp + %s) / 1000) 
            WHERE id = %s
        ''', (xp, xp, guild_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення XP гільдії: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def add_guild_contribution(guild_id, user_id, contribution):
    """Додає внесок користувача"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE guild_members SET contribution = contribution + %s 
            WHERE guild_id = %s AND user_id = %s
        ''', (contribution, guild_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення внеску: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_guilds(chat_id):
    """Отримує всі гільдії в чаті"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM guilds 
            WHERE chat_id = %s 
            ORDER BY xp DESC
        ''', (chat_id,))
        rows = cursor.fetchall()
        guilds = []
        for row in rows:
            guilds.append({
                'id': int(row[0]),
                'chat_id': int(row[1]),
                'name': row[2],
                'owner_user_id': int(row[3]),
                'description': row[4],
                'level': int(row[5]) if row[5] else 1,
                'xp': int(row[6]) if row[6] else 0,
                'coins': int(row[7]) if row[7] else 0,
                'member_count': int(row[8]) if row[8] else 1,
                'created_at': int(row[9]) if row[9] else 0
            })
        return guilds
    except Exception as e:
        logger.error(f"❌ Помилка отримання всіх гільдій: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_guild_stats(user_id, chat_id):
    """Отримує статистику гільдій користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as guilds_joined,
                COALESCE(SUM(gm.contribution), 0) as total_contribution
            FROM guild_members gm
            JOIN guilds g ON gm.guild_id = g.id
            WHERE gm.user_id = %s AND gm.chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return {'guilds_joined': 0, 'total_contribution': 0}
        return {
            'guilds_joined': int(row[0]) if row[0] else 0,
            'total_contribution': int(row[1]) if row[1] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики гільдій: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def transfer_guild_owner(guild_id, new_owner_user_id):
    """Передає володіння гільдією"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Змінюємо роль старого власника
        cursor.execute('''
            UPDATE guild_members SET role = 'member' 
            WHERE guild_id = %s AND role = 'owner'
        ''', (guild_id,))
        
        # Призначаємо нового власника
        cursor.execute('''
            UPDATE guild_members SET role = 'owner' 
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, new_owner_user_id))
        
        # Оновлюємо власника в гільдії
        cursor.execute('''
            UPDATE guilds SET owner_user_id = %s WHERE id = %s
        ''', (new_owner_user_id, guild_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка передачі володіння: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_guild(guild_id):
    """Видаляє гільдію"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM guilds WHERE id = %s', (guild_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка видалення гільдії: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ СКІНІВ
# ============================================

def get_all_skins():
    """Отримує всі скіни"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM skins ORDER BY price ASC')
        rows = cursor.fetchall()
        skins = []
        for row in rows:
            skins.append({
                'id': int(row[0]),
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'price': int(row[4]) if row[4] else 0,
                'rarity': row[5],
                'bonus_type': row[6],
                'bonus_value': int(row[7]) if row[7] else 0,
                'icon': row[8]
            })
        return skins
    except Exception as e:
        logger.error(f"❌ Помилка отримання скінів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_skin(skin_id):
    """Отримує скін за ID"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM skins WHERE id = %s', (skin_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'name': row[1],
            'display_name': row[2],
            'description': row[3],
            'price': int(row[4]) if row[4] else 0,
            'rarity': row[5],
            'bonus_type': row[6],
            'bonus_value': int(row[7]) if row[7] else 0,
            'icon': row[8]
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання скіну: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_skin_by_name(name):
    """Отримує скін за назвою"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM skins WHERE name = %s', (name,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'name': row[1],
            'display_name': row[2],
            'description': row[3],
            'price': int(row[4]) if row[4] else 0,
            'rarity': row[5],
            'bonus_type': row[6],
            'bonus_value': int(row[7]) if row[7] else 0,
            'icon': row[8]
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання скіну за назвою: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_skins(user_id, chat_id):
    """Отримує скіни користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT s.*, us.equipped 
            FROM user_skins us
            JOIN skins s ON us.skin_id = s.id
            WHERE us.user_id = %s AND us.chat_id = %s
            ORDER BY us.equipped DESC, s.price DESC
        ''', (user_id, chat_id))
        rows = cursor.fetchall()
        skins = []
        for row in rows:
            skins.append({
                'id': int(row[0]),
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'price': int(row[4]) if row[4] else 0,
                'rarity': row[5],
                'bonus_type': row[6],
                'bonus_value': int(row[7]) if row[7] else 0,
                'icon': row[8],
                'equipped': bool(row[9])
            })
        return skins
    except Exception as e:
        logger.error(f"❌ Помилка отримання скінів користувача: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_equipped_skin(user_id, chat_id):
    """Отримує активний скін користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT s.* FROM user_skins us
            JOIN skins s ON us.skin_id = s.id
            WHERE us.user_id = %s AND us.chat_id = %s AND us.equipped = TRUE
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'name': row[1],
            'display_name': row[2],
            'description': row[3],
            'price': int(row[4]) if row[4] else 0,
            'rarity': row[5],
            'bonus_type': row[6],
            'bonus_value': int(row[7]) if row[7] else 0,
            'icon': row[8]
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання активного скіну: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_inventory(user_id, chat_id):
    """Отримує інвентар користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT ui.item_id, ui.quantity, ui.expires_at, s.name, s.description, s.effect_type
            FROM user_inventory ui
            LEFT JOIN shop_items s ON ui.item_id = s.item_id
            WHERE ui.user_id = %s AND ui.chat_id = %s
        ''', (user_id, chat_id))
        rows = cursor.fetchall()
        inventory = []
        now = int(time.time())
        for row in rows:
            # Check if not expired
            expires_at = int(row[2]) if row[2] else None
            if expires_at is None or expires_at > now:
                # Get icon based on effect_type
                icon_map = {
                    'weight_bonus': '🍎',
                    'agility_bonus': '💪',
                    'shield': '🛡️',
                    'remove_cooldown': '⚡',
                    'luck_bonus': '🍀'
                }
                icon = icon_map.get(row[5], '📦')
                
                inventory.append({
                    'item_id': row[0],
                    'quantity': int(row[1]) if row[1] else 0,
                    'expires_at': expires_at,
                    'name': row[3] or row[0],
                    'description': row[4] or '',
                    'icon': icon
                })
        return inventory
    except Exception as e:
        logger.error(f"❌ Помилка отримання інвентарю: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def buy_skin(user_id, chat_id, skin_id):
    """Купує скін"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO user_skins (user_id, chat_id, skin_id, equipped, obtained_at)
            VALUES (%s, %s, %s, FALSE, %s)
            ON CONFLICT (user_id, chat_id, skin_id) DO NOTHING
        ''', (user_id, chat_id, skin_id, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка купівлі скіну: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def equip_skin(user_id, chat_id, skin_id):
    """Одягає скін"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Знімаємо всі одягнені скіни
        cursor.execute('''
            UPDATE user_skins SET equipped = FALSE 
            WHERE user_id = %s AND chat_id = %s
        ''', (user_id, chat_id))
        
        # Одягаємо новий
        cursor.execute('''
            UPDATE user_skins SET equipped = TRUE 
            WHERE user_id = %s AND chat_id = %s AND skin_id = %s
        ''', (user_id, chat_id, skin_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка одягання скіну: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def has_skin(user_id, chat_id, skin_id):
    """Перевіряє чи має користувач скін"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 1 FROM user_skins 
            WHERE user_id = %s AND chat_id = %s AND skin_id = %s
        ''', (user_id, chat_id, skin_id))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        logger.error(f"❌ Помилка перевірки скіну: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_skin_bonus(user_id, chat_id, bonus_type):
    """Отримує бонус від скіну"""
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT s.bonus_value FROM user_skins us
            JOIN skins s ON us.skin_id = s.id
            WHERE us.user_id = %s AND us.chat_id = %s 
            AND us.equipped = TRUE 
            AND (s.bonus_type = %s OR s.bonus_type = 'all_bonus')
        ''', (user_id, chat_id, bonus_type))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.error(f"❌ Помилка отримання бонусу скіну: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ БОС-ДУЕЛЕЙ
# ============================================

def get_active_boss():
    """Отримує активного боса"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM bosses 
            WHERE is_active = TRUE 
            ORDER BY id DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'name': row[1],
            'level': int(row[2]),
            'health': int(row[3]),
            'max_health': int(row[4]),
            'damage': int(row[5]),
            'reward_coins': int(row[6]),
            'reward_xp': int(row[7]),
            'is_active': bool(row[8]),
            'spawn_date': int(row[9]) if row[9] else 0,
            'defeat_date': int(row[10]) if row[10] else 0,
            'defeated_by_user_id': int(row[11]) if row[11] else None
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання боса: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_last_boss():
    """Отримує останнього боса (активного або переможеного)"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM bosses 
            ORDER BY id DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'name': row[1],
            'level': int(row[2]),
            'health': int(row[3]),
            'max_health': int(row[4]),
            'damage': int(row[5]),
            'reward_coins': int(row[6]),
            'reward_xp': int(row[7]),
            'is_active': bool(row[8]),
            'spawn_date': int(row[9]) if row[9] else 0,
            'defeat_date': int(row[10]) if row[10] else 0,
            'defeated_by_user_id': int(row[11]) if row[11] else None
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання останнього боса: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def spawn_boss(name, level, health, damage, reward_coins, reward_xp):
    """Створює нового боса"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO bosses (name, level, health, max_health, damage, reward_coins, reward_xp, spawn_date, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id
        ''', (name, level, health, health, damage, reward_coins, reward_xp, now))
        boss_id = cursor.fetchone()[0]
        conn.commit()
        return boss_id
    except Exception as e:
        logger.error(f"❌ Помилка створення боса: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def attack_boss(boss_id, user_id, chat_id, damage):
    """Атакує боса"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Додаємо шкоду до учасника
        cursor.execute('''
            INSERT INTO boss_battle_participants (boss_id, user_id, chat_id, damage_dealt, joined_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (boss_id, user_id, chat_id) DO UPDATE SET
                damage_dealt = boss_battle_participants.damage_dealt + %s
        ''', (boss_id, user_id, chat_id, damage, int(time.time()), damage))

        # Отримуємо поточне здоров'я боса
        cursor.execute('SELECT health, max_health FROM bosses WHERE id = %s', (boss_id,))
        boss_row = cursor.fetchone()
        
        if not boss_row:
            return None
        
        current_health = boss_row[0] if boss_row[0] else 0
        max_health = boss_row[1] if boss_row[1] else 1000
        
        # Зменшуємо здоров'я боса
        new_health = max(0, current_health - damage)
        cursor.execute('''
            UPDATE bosses SET health = %s WHERE id = %s
        ''', (new_health, boss_id))

        # Перевіряємо чи переможено
        if new_health <= 0:
            # Бос переможений
            cursor.execute('''
                UPDATE bosses SET is_active = FALSE, defeat_date = %s, defeated_by_user_id = %s
                WHERE id = %s
            ''', (int(time.time()), user_id, boss_id))
            conn.commit()
            return {'defeated': True, 'boss_id': boss_id, 'defeated_by_user_id': user_id}

        conn.commit()
        return {'defeated': False, 'boss_id': boss_id, 'remaining_health': new_health, 'max_health': max_health}
    except Exception as e:
        logger.error(f"❌ Помилка атаки боса: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_boss_participants(boss_id):
    """Отримує учасників бою з босом"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM boss_battle_participants 
            WHERE boss_id = %s 
            ORDER BY damage_dealt DESC
        ''', (boss_id,))
        rows = cursor.fetchall()
        participants = []
        for row in rows:
            participants.append({
                'id': int(row[0]),
                'boss_id': int(row[1]),
                'user_id': int(row[2]),
                'chat_id': int(row[3]),
                'damage_dealt': int(row[4]) if row[4] else 0,
                'joined_at': int(row[5]) if row[5] else 0
            })
        return participants
    except Exception as e:
        logger.error(f"❌ Помилка отримання учасників: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_boss_stats(user_id, chat_id):
    """Отримує статистику бос-дуелей користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT bbp.boss_id) as bosses_fought,
                COALESCE(SUM(bbp.damage_dealt), 0) as total_damage,
                COUNT(DISTINCT b.defeated_by_user_id) as bosses_defeated
            FROM boss_battle_participants bbp
            LEFT JOIN bosses b ON bbp.boss_id = b.id
            WHERE bbp.user_id = %s AND bbp.chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return {'bosses_fought': 0, 'total_damage': 0, 'bosses_defeated': 0}
        return {
            'bosses_fought': int(row[0]) if row[0] else 0,
            'total_damage': int(row[1]) if row[1] else 0,
            'bosses_defeated': int(row[2]) if row[2] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики босів: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_last_boss_attack_time(user_id, chat_id):
    """Отримує час останньої атаки боса"""
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT joined_at FROM boss_battle_participants 
            WHERE user_id = %s AND chat_id = %s 
            ORDER BY joined_at DESC LIMIT 1
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.error(f"❌ Помилка отримання часу атаки: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def save_boss_attack_time(user_id, chat_id, timestamp):
    """Зберігає час атаки боса"""
    # Already saved in attack_boss function
    pass


# ============================================
# ФУНКЦІЇ ДЛЯ ДІТЕЙ
# ============================================

def rename_child(child_id, user_id, chat_id, new_name):
    """Перейменувати дитину"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE children SET name = %s 
            WHERE id = %s AND user_id = %s AND chat_id = %s
        ''', (new_name, child_id, user_id, chat_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"❌ Помилка перейменування дитини: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_child(child_id, chat_id):
    """Отримує інформацію про дитину"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM children WHERE id = %s AND chat_id = %s', (child_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'user_id': int(row[1]),
            'chat_id': int(row[2]),
            'father_user_id': int(row[3]),
            'mother_user_id': int(row[4]),
            'name': row[5],
            'weight': int(row[6]) if row[6] else 0,
            'inherited_trait': row[7],
            'born_at': int(row[8]) if row[8] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання дитини: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_top_children(chat_id, limit=10):
    """Топ дітей за вагою"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT c.*, 
                   (SELECT name FROM hryaky WHERE key = %s || '_' || c.father_user_id) as father_name,
                   (SELECT name FROM hryaky WHERE key = %s || '_' || c.mother_user_id) as mother_name
            FROM children c
            WHERE c.chat_id = %s
            ORDER BY c.weight DESC
            LIMIT %s
        ''', (chat_id, chat_id, chat_id, limit))
        rows = cursor.fetchall()
        children = []
        for row in rows:
            children.append({
                'id': int(row[0]),
                'user_id': int(row[1]),
                'chat_id': int(row[2]),
                'father_user_id': int(row[3]),
                'mother_user_id': int(row[4]),
                'name': row[5],
                'weight': int(row[6]) if row[6] else 0,
                'inherited_trait': row[7],
                'born_at': int(row[8]) if row[8] else 0,
                'father_name': row[9] or 'Невідомо',
                'mother_name': row[10] or 'Невідомо'
            })
        return children
    except Exception as e:
        logger.error(f"❌ Помилка отримання топу дітей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def sacrifice_child(child_id, user_id, chat_id):
    """Жертва дитини для бонусів"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Отримуємо дитину
        cursor.execute('SELECT * FROM children WHERE id = %s AND user_id = %s AND chat_id = %s', 
                      (child_id, user_id, chat_id))
        child = cursor.fetchone()
        
        if not child:
            return None
        
        # Розраховуємо бонуси на основі ваги дитини
        weight = int(child[6]) if child[6] else 0
        coins_reward = weight * 2
        xp_reward = weight
        
        # Видаляємо дитину
        cursor.execute('DELETE FROM children WHERE id = %s', (child_id,))
        conn.commit()
        
        return {
            'coins': coins_reward,
            'xp': xp_reward,
            'weight': weight
        }
    except Exception as e:
        logger.error(f"❌ Помилка жертви дитини: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def marry_children(child1_id, child2_id, user_id, chat_id):
    """Одруження дітей (створення онуків)"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Отримуємо обох дітей
        cursor.execute('SELECT * FROM children WHERE id = %s AND chat_id = %s', (child1_id, chat_id))
        child1 = cursor.fetchone()
        
        cursor.execute('SELECT * FROM children WHERE id = %s AND chat_id = %s', (child2_id, chat_id))
        child2 = cursor.fetchone()
        
        if not child1 or not child2:
            return None
        
        # Перевіряємо що це різні діти
        if child1[0] == child2[0]:
            return None
        
        # Створюємо онука
        now = int(time.time())
        child_weight = max(1, int((child1[6] + child2[6]) / 2) + random.randint(-3, 3))
        
        cursor.execute('''
            INSERT INTO children (user_id, chat_id, father_user_id, mother_user_id, 
                                name, weight, inherited_trait, born_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, chat_id, child1[3], child2[3], 
              f"{child1[5][:3]}-{child2[5][:3]}-F1", child_weight, '', now))
        
        grandchild_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            'grandchild_id': grandchild_id,
            'weight': child_weight
        }
    except Exception as e:
        logger.error(f"❌ Помилка одруження дітей: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ СЕЗОННИХ ІВЕНТІВ
# ============================================

def get_active_events():
    """Отримує активні івенти"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            SELECT * FROM seasonal_events 
            WHERE is_active = TRUE AND start_date <= %s AND end_date >= %s
            ORDER BY start_date DESC
        ''', (now, now))
        rows = cursor.fetchall()
        events = []
        for row in rows:
            events.append({
                'id': int(row[0]),
                'name': row[1],
                'event_type': row[2],
                'start_date': int(row[3]) if row[3] else 0,
                'end_date': int(row[4]) if row[4] else 0,
                'is_active': bool(row[5]),
                'special_reward_coins': int(row[6]) if row[6] else 0,
                'special_reward_xp': int(row[7]) if row[7] else 0,
                'description': row[8]
            })
        return events
    except Exception as e:
        logger.error(f"❌ Помилка отримання активних івентів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_all_events():
    """Отримує всі івенти"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM seasonal_events ORDER BY start_date DESC')
        rows = cursor.fetchall()
        events = []
        for row in rows:
            events.append({
                'id': int(row[0]),
                'name': row[1],
                'event_type': row[2],
                'start_date': int(row[3]) if row[3] else 0,
                'end_date': int(row[4]) if row[4] else 0,
                'is_active': bool(row[5]),
                'special_reward_coins': int(row[6]) if row[6] else 0,
                'special_reward_xp': int(row[7]) if row[7] else 0,
                'description': row[8]
            })
        return events
    except Exception as e:
        logger.error(f"❌ Помилка отримання всіх івентів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_event_progress(user_id, event_id):
    """Отримує прогрес користувача в івенті"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM event_participation 
            WHERE user_id = %s AND event_id = %s
        ''', (user_id, event_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'event_id': int(row[1]),
            'user_id': int(row[2]),
            'chat_id': int(row[3]),
            'progress': int(row[4]) if row[4] else 0,
            'completed': bool(row[5]),
            'reward_claimed': bool(row[6]),
            'participated_at': int(row[7]) if row[7] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання прогресу івенту: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_event_progress(user_id, event_id, chat_id, progress_add=1):
    """Оновлює прогрес в івенті"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO event_participation (event_id, user_id, chat_id, progress, participated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_id, user_id) DO UPDATE SET
                progress = event_participation.progress + %s
        ''', (event_id, user_id, chat_id, progress_add, now, progress_add))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення прогресу івенту: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def claim_event_reward(user_id, event_id):
    """Забрати нагороду за івент"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE event_participation 
            SET reward_claimed = TRUE, completed = TRUE
            WHERE user_id = %s AND event_id = %s
        ''', (user_id, event_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка отримання нагороди івенту: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ МУЛЬТИ-МОВНОСТІ
# ============================================

def get_user_language(user_id):
    """Отримує мову користувача"""
    conn = get_connection()
    if not conn:
        return 'uk'

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT language FROM user_languages WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        if not row:
            return 'uk'
        return row[0]
    except Exception as e:
        logger.error(f"❌ Помилка отримання мови: {e}")
        return 'uk'
    finally:
        cursor.close()
        conn.close()

def set_user_language(user_id, language):
    """Встановлює мову користувача"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO user_languages (user_id, language, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                language = EXCLUDED.language,
                updated_at = EXCLUDED.updated_at
        ''', (user_id, language, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка встановлення мови: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
