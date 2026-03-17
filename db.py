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
        # НЕ видаляємо таблиці - зберігаємо дані між деплоями!
        # Видаляємо тільки якщо потрібно змінити структуру
        # cursor.execute("DROP TABLE IF EXISTS user_inventory CASCADE")
        # cursor.execute("DROP TABLE IF EXISTS shop_items CASCADE")
        # ... (інші DROP закомічені)
        logger.info("📊 Перевірка структури таблиць...")

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
                crypto_coins BIGINT DEFAULT 0,
                pending_withdrawal BIGINT DEFAULT 0,
                last_withdrawal BIGINT DEFAULT 0,
                total_converted BIGINT DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця user_currencies створена")

        # Таблиця крипто-транзакцій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                transaction_type TEXT,
                amount BIGINT,
                wallet_address TEXT,
                status TEXT DEFAULT 'pending',
                tx_hash TEXT,
                created_at BIGINT,
                completed_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця crypto_transactions створена")

        # Таблиця трейдів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                sender_id BIGINT,
                receiver_id BIGINT,
                chat_id BIGINT,
                coins_offered BIGINT DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at BIGINT,
                completed_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця trades створена")

        # Таблиця квіз-прогресу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_progress (
                user_id BIGINT,
                chat_id BIGINT,
                question_id INTEGER,
                answered_at BIGINT,
                correct BOOLEAN,
                PRIMARY KEY (user_id, chat_id, question_id)
            )
        ''')
        logger.info("✅ Таблиця quiz_progress створена")

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
                born_at BIGINT,
                gene_rarity TEXT DEFAULT 'C',
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                color_type TEXT DEFAULT 'normal'
            )
        ''')
        logger.info("✅ Таблиця children створена")

        # Таблиця генів хряка
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hryak_genes (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                gene_rarity TEXT DEFAULT 'C',
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                color_type TEXT DEFAULT 'normal',
                mutation_chance REAL DEFAULT 0.05,
                updated_at BIGINT,
                UNIQUE(user_id, chat_id)
            )
        ''')
        logger.info("✅ Таблиця hryak_genes створена")

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

        # Таблиця територій гільдій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_territories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                owner_guild_id INTEGER,
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                captured_at BIGINT,
                income_per_hour INTEGER DEFAULT 0,
                last_income_at BIGINT,
                FOREIGN KEY (owner_guild_id) REFERENCES guilds(id) ON DELETE SET NULL
            )
        ''')
        logger.info("✅ Таблиця guild_territories створена")

        # Таблиця гільдійних скриньок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_chests (
                id SERIAL PRIMARY KEY,
                guild_id INTEGER,
                item_type TEXT,
                item_name TEXT,
                quantity INTEGER DEFAULT 0,
                donated_by_user_id BIGINT,
                donated_at BIGINT,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_chests створена")

        # Таблиця гільдійних воєн
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_wars (
                id SERIAL PRIMARY KEY,
                attacker_guild_id INTEGER,
                defender_guild_id INTEGER,
                territory_id INTEGER,
                status TEXT DEFAULT 'active',
                started_at BIGINT,
                ended_at BIGINT,
                winner_guild_id INTEGER,
                attacker_score INTEGER DEFAULT 0,
                defender_score INTEGER DEFAULT 0,
                FOREIGN KEY (attacker_guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
                FOREIGN KEY (defender_guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
                FOREIGN KEY (territory_id) REFERENCES guild_territories(id) ON DELETE SET NULL
            )
        ''')
        logger.info("✅ Таблиця guild_wars створена")

        # Таблиця участі в гільдійних війнах
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_war_participants (
                id SERIAL PRIMARY KEY,
                war_id INTEGER,
                user_id BIGINT,
                guild_id INTEGER,
                contribution INTEGER DEFAULT 0,
                battles_fought INTEGER DEFAULT 0,
                battles_won INTEGER DEFAULT 0,
                joined_at BIGINT,
                FOREIGN KEY (war_id) REFERENCES guild_wars(id) ON DELETE CASCADE,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_war_participants створена")

        # Таблиця воїнів гільдії (свинарі)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_warriors (
                id SERIAL PRIMARY KEY,
                guild_id INTEGER,
                warrior_type TEXT DEFAULT 'regular',
                quantity INTEGER DEFAULT 0,
                power INTEGER DEFAULT 10,
                hired_at BIGINT,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_warriors створена")

        # Таблиця захисту територій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS territory_defense (
                id SERIAL PRIMARY KEY,
                territory_id INTEGER,
                guild_id INTEGER,
                warrior_type TEXT,
                warrior_count INTEGER DEFAULT 0,
                defense_power INTEGER DEFAULT 0,
                stationed_at BIGINT,
                FOREIGN KEY (territory_id) REFERENCES guild_territories(id) ON DELETE CASCADE,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця territory_defense створена")

        # Таблиця предметів з бонусами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_items (
                id SERIAL PRIMARY KEY,
                guild_id INTEGER,
                item_type TEXT,
                item_name TEXT,
                rarity TEXT DEFAULT 'common',
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 1,
                donated_by_user_id BIGINT,
                donated_at BIGINT,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_items створена")

        # Таблиця інвентарю користувача (предмети)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_items (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                chat_id BIGINT,
                item_type TEXT,
                item_name TEXT,
                rarity TEXT DEFAULT 'common',
                bonus_type TEXT,
                bonus_value INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 1,
                obtained_at BIGINT,
                UNIQUE(user_id, chat_id, item_type, item_name)
            )
        ''')
        logger.info("✅ Таблиця user_items створена")

        # Таблиця трейдів предметами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_trades (
                id SERIAL PRIMARY KEY,
                sender_id BIGINT,
                receiver_id BIGINT,
                chat_id BIGINT,
                sender_items_json TEXT,
                receiver_items_json TEXT,
                sender_coins INTEGER DEFAULT 0,
                receiver_coins INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at BIGINT,
                completed_at BIGINT
            )
        ''')
        logger.info("✅ Таблиця item_trades створена")

        # Таблиця історії битв за території
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS territory_battles (
                id SERIAL PRIMARY KEY,
                territory_id INTEGER,
                attacker_guild_id INTEGER,
                defender_guild_id INTEGER,
                attacker_warriors INTEGER,
                defender_warriors INTEGER,
                attacker_loss INTEGER,
                defender_loss INTEGER,
                winner_guild_id INTEGER,
                battle_date BIGINT,
                FOREIGN KEY (territory_id) REFERENCES guild_territories(id) ON DELETE SET NULL
            )
        ''')
        logger.info("✅ Таблиця territory_battles створена")

        # Таблиця приватних казино
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_casinos (
                id SERIAL PRIMARY KEY,
                owner_user_id BIGINT,
                chat_id BIGINT,
                name TEXT,
                casino_coins BIGINT DEFAULT 0,
                min_bet BIGINT DEFAULT 10,
                max_bet BIGINT DEFAULT 1000,
                win_chance REAL DEFAULT 0.35,
                created_at BIGINT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        logger.info("✅ Таблиця private_casinos створена")

        # Таблиця ігор в казино
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS casino_games (
                id SERIAL PRIMARY KEY,
                casino_id INTEGER,
                player_user_id BIGINT,
                bet_amount BIGINT,
                win_amount BIGINT DEFAULT 0,
                is_win BOOLEAN DEFAULT FALSE,
                game_result TEXT,
                played_at BIGINT,
                FOREIGN KEY (casino_id) REFERENCES private_casinos(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця casino_games створена")

        # Таблиця командних босів гільдій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_bosses (
                id SERIAL PRIMARY KEY,
                name TEXT,
                level INTEGER DEFAULT 1,
                health BIGINT,
                max_health BIGINT,
                damage BIGINT,
                reward_coins INTEGER,
                reward_xp INTEGER,
                reward_chest_items TEXT,
                owner_guild_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                spawn_date BIGINT,
                defeat_date BIGINT,
                defeated_by_guild_id INTEGER,
                defeat_count INTEGER DEFAULT 0,
                FOREIGN KEY (owner_guild_id) REFERENCES guilds(id) ON DELETE SET NULL
            )
        ''')
        logger.info("✅ Таблиця guild_bosses створена")

        # Таблиця участі в боях з босом
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_boss_participants (
                id SERIAL PRIMARY KEY,
                boss_id INTEGER,
                user_id BIGINT,
                guild_id INTEGER,
                damage_dealt BIGINT DEFAULT 0,
                joined_at BIGINT,
                FOREIGN KEY (boss_id) REFERENCES guild_bosses(id) ON DELETE CASCADE,
                FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
            )
        ''')
        logger.info("✅ Таблиця guild_boss_participants створена")

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
                level INTEGER DEFAULT 1,
                health BIGINT,
                max_health BIGINT,
                damage BIGINT,
                reward_coins INTEGER,
                reward_xp INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                spawn_date BIGINT,
                defeat_date BIGINT,
                defeated_by_user_id BIGINT,
                defeat_count INTEGER DEFAULT 0
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

        # Додаємо тестовий івент (якщо не існують)
        now = int(time.time())
        cursor.execute('''
            INSERT INTO seasonal_events (name, event_type, start_date, end_date, is_active, special_reward_coins, special_reward_xp, description)
            SELECT '🎄 Різдвяний Івент', 'christmas', %s, %s, FALSE, 100, 50, 'Збері 10 сніжинок та отримай нагороду!'
            WHERE NOT EXISTS (SELECT 1 FROM seasonal_events WHERE name = '🎄 Різдвяний Івент')
        ''', (now - 86400*30, now - 86400*23))  # Різдво (минуле)
        
        cursor.execute('''
            INSERT INTO seasonal_events (name, event_type, start_date, end_date, is_active, special_reward_coins, special_reward_xp, description)
            SELECT '🎃 Хелловін 2026', 'halloween', %s, %s, FALSE, 150, 75, 'Переможи 5 гарбузів-босів!'
            WHERE NOT EXISTS (SELECT 1 FROM seasonal_events WHERE name = '🎃 Хелловін 2026')
        ''', (now - 86400*60, now - 86400*53))  # Хелловін (минуле)
        
        cursor.execute('''
            INSERT INTO seasonal_events (name, event_type, start_date, end_date, is_active, special_reward_coins, special_reward_xp, description)
            SELECT '🐰 Великодній Івент', 'easter', %s, %s, TRUE, 80, 40, 'Знайди 20 великодніх яєць!'
            WHERE NOT EXISTS (SELECT 1 FROM seasonal_events WHERE name = '🐰 Великодній Івент')
        ''', (now, now + 86400*14))  # Великдень (активний 14 днів)
        
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
# ФУНКЦІЇ ДЛЯ КРИПТО-МОНЕТ (TON)
# ============================================

CONVERSION_RATE = 1000  # 1000 game coins = 1 CRYPTO
MIN_CONVERT = 10000  # 10,000 game coins (10 CRYPTO)
MAX_DAILY_WITHDRAW = 100000  # 100,000 game coins (100 CRYPTO)

def get_crypto_balance(user_id, chat_id):
    """Отримує крипто-баланс користувача"""
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT crypto_coins FROM user_currencies WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.error(f"❌ Помилка отримання crypto балансу: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def convert_game_to_crypto(user_id, chat_id, game_coins):
    """Конвертує ігрові монети в крипто"""
    if game_coins < MIN_CONVERT:
        return {'success': False, 'message': f'Мінімум для конвертації: {MIN_CONVERT} монет'}
    
    crypto_amount = game_coins // CONVERSION_RATE
    
    conn = get_connection()
    if not conn:
        return {'success': False, 'message': 'Помилка БД'}

    cursor = conn.cursor()
    try:
        # Перевіряємо баланс
        cursor.execute('SELECT coins, crypto_coins FROM user_currencies WHERE user_id = %s AND chat_id = %s', (user_id, chat_id))
        row = cursor.fetchone()
        
        if not row or row[0] < game_coins:
            return {'success': False, 'message': 'Недостатньо монет'}
        
        # Конвертуємо
        new_game_coins = row[0] - game_coins
        new_crypto = (row[1] if row[1] else 0) + crypto_amount
        
        cursor.execute('''
            UPDATE user_currencies 
            SET coins = %s, crypto_coins = %s, total_converted = COALESCE(total_converted, 0) + %s
            WHERE user_id = %s AND chat_id = %s
        ''', (new_game_coins, new_crypto, game_coins, user_id, chat_id))
        
        conn.commit()
        return {
            'success': True,
            'game_coins_deducted': game_coins,
            'crypto_received': crypto_amount,
            'new_crypto_balance': new_crypto
        }
    except Exception as e:
        logger.error(f"❌ Помилка конвертації: {e}")
        conn.rollback()
        return {'success': False, 'message': f'Помилка: {str(e)}'}
    finally:
        cursor.close()
        conn.close()

def get_conversion_info(user_id, chat_id):
    """Отримує інформацію про конвертацію"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT coins, crypto_coins, total_converted, last_withdrawal 
            FROM user_currencies 
            WHERE user_id = %s AND chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        
        if not row:
            return {
                'game_coins': 0,
                'crypto_coins': 0,
                'total_converted': 0,
                'last_withdrawal': 0
            }
        
        return {
            'game_coins': row[0] if row[0] else 0,
            'crypto_coins': row[1] if row[1] else 0,
            'total_converted': row[2] if row[2] else 0,
            'last_withdrawal': row[3] if row[3] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання інформації: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ КРИПТО-ТРАНЗАКЦІЙ
# ============================================

def record_crypto_transaction(user_id, chat_id, tx_type, amount, wallet_address='', tx_hash=''):
    """Записує крипто-транзакцію в БД"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO crypto_transactions 
            (user_id, chat_id, transaction_type, amount, wallet_address, status, tx_hash, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, chat_id, tx_type, amount, wallet_address, 'pending', tx_hash, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка запису транзакції: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_transaction_status(tx_id, status, tx_hash=''):
    """Оновлює статус транзакції"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        if tx_hash:
            cursor.execute('''
                UPDATE crypto_transactions 
                SET status = %s, tx_hash = %s, completed_at = %s
                WHERE id = %s
            ''', (status, tx_hash, int(time.time()), tx_id))
        else:
            cursor.execute('''
                UPDATE crypto_transactions 
                SET status = %s, completed_at = %s
                WHERE id = %s
            ''', (status, int(time.time()), tx_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення транзакції: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_transactions(user_id, chat_id, limit=20):
    """Отримує історію транзакцій користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM crypto_transactions 
            WHERE user_id = %s AND chat_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (user_id, chat_id, limit))
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            transactions.append({
                'id': int(row[0]),
                'user_id': int(row[1]),
                'chat_id': int(row[2]),
                'transaction_type': row[3],
                'amount': int(row[4]) if row[4] else 0,
                'wallet_address': row[5],
                'status': row[6],
                'tx_hash': row[7],
                'created_at': int(row[8]) if row[8] else 0,
                'completed_at': int(row[9]) if row[9] else 0
            })
        return transactions
    except Exception as e:
        logger.error(f"❌ Помилка отримання транзакцій: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ ТРЕЙДІВ
# ============================================

def create_trade(sender_id, receiver_id, chat_id, coins_offered):
    """Створює трейд"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO trades (sender_id, receiver_id, chat_id, coins_offered, status, created_at)
            VALUES (%s, %s, %s, %s, 'pending', %s)
            RETURNING id
        ''', (sender_id, receiver_id, chat_id, coins_offered, now))
        trade_id = cursor.fetchone()[0]
        conn.commit()
        return trade_id
    except Exception as e:
        logger.error(f"❌ Помилка створення трейду: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def accept_trade(trade_id, sender_id, receiver_id, chat_id):
    """Приймає трейд (отримувач приймає трейд від відправника)"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Отримуємо трейд
        cursor.execute('SELECT * FROM trades WHERE id = %s', (trade_id,))
        trade = cursor.fetchone()

        if not trade:
            logger.error(f"❌ Трейд {trade_id} не знайдено!")
            return False

        coins = int(trade[4]) if trade[4] else 0
        trade_sender_id = int(trade[1])  # Отримуємо реальний ID відправника з трейду

        # Перевіряємо баланс ВІДПРАВНИКА (той хто створив трейд)
        cursor.execute('SELECT coins FROM user_currencies WHERE user_id = %s AND chat_id = %s', (trade_sender_id, chat_id))
        sender_row = cursor.fetchone()

        if not sender_row or sender_row[0] < coins:
            logger.error(f"❌ У відправника (ID {trade_sender_id}) недостатньо монет! Є: {sender_row[0] if sender_row else 0}, потрібно: {coins}")
            return False

        # Переказ монет: від відправника до отримувача
        cursor.execute('UPDATE user_currencies SET coins = coins - %s WHERE user_id = %s AND chat_id = %s',
                      (coins, trade_sender_id, chat_id))
        cursor.execute('UPDATE user_currencies SET coins = coins + %s WHERE user_id = %s AND chat_id = %s',
                      (coins, receiver_id, chat_id))

        # Оновлюємо статус трейду
        cursor.execute('''
            UPDATE trades
            SET status = 'completed', completed_at = %s
            WHERE id = %s
        ''', (int(time.time()), trade_id))

        conn.commit()
        logger.info(f"✅ Трейд {trade_id} виконано: {trade_sender_id} -> {receiver_id}, сума: {coins} монет")
        return True
    except Exception as e:
        logger.error(f"❌ Помилка прийняття трейду: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def cancel_trade(trade_id):
    """Скасовує трейд"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE trades SET status = 'cancelled' WHERE id = %s
        ''', (trade_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка скасування трейду: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_pending_trades(user_id, chat_id):
    """Отримує активні трейди для користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM trades 
            WHERE receiver_id = %s AND chat_id = %s AND status = 'pending'
            ORDER BY created_at DESC
        ''', (user_id, chat_id))
        rows = cursor.fetchall()
        
        trades = []
        for row in rows:
            trades.append({
                'id': int(row[0]),
                'sender_id': int(row[1]),
                'receiver_id': int(row[2]),
                'chat_id': int(row[3]),
                'coins_offered': int(row[4]) if row[4] else 0,
                'status': row[5],
                'created_at': int(row[6]) if row[6] else 0,
                'completed_at': int(row[7]) if row[7] else 0
            })
        return trades
    except Exception as e:
        logger.error(f"❌ Помилка отримання трейдів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ФУНКЦІЇ ДЛЯ КВІЗУ
# ============================================

def get_user_quiz_progress(user_id, chat_id):
    """Отримує прогрес квізу користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        # Отримуємо питання за сьогодні
        today_start = int(time.time()) - (int(time.time()) % 86400)
        
        cursor.execute('''
            SELECT question_id, correct FROM quiz_progress 
            WHERE user_id = %s AND chat_id = %s AND answered_at >= %s
        ''', (user_id, chat_id, today_start))
        rows = cursor.fetchall()
        
        progress = []
        for row in rows:
            progress.append({
                'question_id': int(row[0]),
                'correct': bool(row[1])
            })
        return progress
    except Exception as e:
        logger.error(f"❌ Помилка отримання прогресу квізу: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def record_quiz_answer(user_id, chat_id, question_id, correct):
    """Записує відповідь на питання квізу"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO quiz_progress (user_id, chat_id, question_id, answered_at, correct)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id, question_id) DO UPDATE SET
                answered_at = EXCLUDED.answered_at,
                correct = EXCLUDED.correct
        ''', (user_id, chat_id, question_id, now, correct))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка запису відповіді квізу: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_quiz_stats(user_id, chat_id):
    """Отримує статистику квізу користувача"""
    conn = get_connection()
    if not conn:
        return {'total': 0, 'correct': 0, 'today': 0}

    cursor = conn.cursor()
    try:
        # Всього відповідей
        cursor.execute('''
            SELECT COUNT(*), SUM(CASE WHEN correct THEN 1 ELSE 0 END)
            FROM quiz_progress WHERE user_id = %s AND chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        
        total = int(row[0]) if row[0] else 0
        correct = int(row[1]) if row[1] else 0
        
        # Сьогодні
        today_start = int(time.time()) - (int(time.time()) % 86400)
        cursor.execute('''
            SELECT COUNT(*) FROM quiz_progress 
            WHERE user_id = %s AND chat_id = %s AND answered_at >= %s
        ''', (user_id, chat_id, today_start))
        today = cursor.fetchone()[0]
        
        return {'total': total, 'correct': correct, 'today': today}
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики квізу: {e}")
        return {'total': 0, 'correct': 0, 'today': 0}
    finally:
        cursor.close()
        conn.close()


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

def promote_guild_member(guild_id, user_id, promoter_user_id):
    """
    Підвищує члена гільдії до офіцера
    Повертає: {'success': bool, 'error': str, 'officer_count': int}
    """
    conn = get_connection()
    if not conn:
        return {'success': False, 'error': 'Помилка БД'}

    cursor = conn.cursor()
    try:
        # Перевіряємо хто підвищує (має бути owner або officer)
        cursor.execute('''
            SELECT role FROM guild_members
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, promoter_user_id))
        promoter_row = cursor.fetchone()
        
        if not promoter_row or promoter_row[0] not in ['owner', 'officer']:
            return {'success': False, 'error': 'Тільки власник або офіцер може підвищувати'}
        
        # Перевіряємо поточну роль того кого підвищують
        cursor.execute('''
            SELECT role FROM guild_members
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        member_row = cursor.fetchone()
        
        if not member_row:
            return {'success': False, 'error': 'Користувач не в гільдії'}
        
        if member_row[0] == 'officer':
            return {'success': False, 'error': 'Користувач вже є офіцером'}
        
        if member_row[0] == 'owner':
            return {'success': False, 'error': 'Неможливо підвищити власника'}
        
        # Рахуємо поточну кількість офіцерів
        cursor.execute('''
            SELECT COUNT(*) FROM guild_members
            WHERE guild_id = %s AND role = 'officer'
        ''', (guild_id,))
        officer_count = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Перевірка на максимальну кількість офіцерів (5)
        if officer_count >= 5:
            return {'success': False, 'error': 'Максимум 5 офіцерів в гільдії'}
        
        # Підвищуємо до офіцера
        cursor.execute('''
            UPDATE guild_members SET role = 'officer'
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        
        conn.commit()
        
        return {
            'success': True,
            'officer_count': officer_count + 1
        }
    except Exception as e:
        logger.error(f"❌ Помилка підвищення: {e}")
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def demote_guild_member(guild_id, user_id, demoter_user_id):
    """
    Знижує офіцера до члена
    Повертає: {'success': bool, 'error': str}
    """
    conn = get_connection()
    if not conn:
        return {'success': False, 'error': 'Помилка БД'}

    cursor = conn.cursor()
    try:
        # Перевіряємо хто знижує (має бути owner)
        cursor.execute('''
            SELECT role FROM guild_members
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, demoter_user_id))
        demoter_row = cursor.fetchone()
        
        if not demoter_row or demoter_row[0] != 'owner':
            return {'success': False, 'error': 'Тільки власник може знижувати офіцерів'}
        
        # Перевіряємо поточну роль
        cursor.execute('''
            SELECT role FROM guild_members
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        member_row = cursor.fetchone()
        
        if not member_row or member_row[0] != 'officer':
            return {'success': False, 'error': 'Користувач не є офіцером'}
        
        # Знижуємо до члена
        cursor.execute('''
            UPDATE guild_members SET role = 'member'
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        
        conn.commit()
        
        return {'success': True}
    except Exception as e:
        logger.error(f"❌ Помилка зниження: {e}")
        conn.rollback()
        return {'success': False, 'error': str(e)}
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
    logger.info(f"🗡️ Атака боса: boss_id={boss_id}, user_id={user_id}, chat_id={chat_id}, damage={damage}")
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("❌ Не вдалося підключитися до БД в attack_boss")
            return {'error': 'DB connection failed'}

        cursor = conn.cursor()
        now = int(time.time())

        # Отримуємо поточне здоров'я боса ПЕРЕД будь-яких дій
        logger.info(f"SELECT health, max_health, is_active FROM bosses WHERE id = {boss_id}")
        cursor.execute('SELECT health, max_health, is_active FROM bosses WHERE id = %s', (boss_id,))
        boss_row = cursor.fetchone()
        logger.info(f"Boss row: {boss_row}")

        if not boss_row:
            logger.error(f"❌ Бос {boss_id} не знайдений в БД!")
            return {'error': 'Boss not found'}

        current_health = int(boss_row[0]) if boss_row[0] else 0
        max_health = int(boss_row[1]) if boss_row[1] else 1000
        is_active = bool(boss_row[2])
        
        logger.info(f"📊 Бос: HP {current_health}/{max_health}, ваша шкода={damage}, active={is_active}")

        # Перевіряємо чи бос ще активний
        if not is_active:
            logger.info(f"⚠️ Бос вже переможений!")
            return {'defeated': True, 'boss_id': boss_id, 'already_defeated': True}

        # Перевіряємо чи бос вже мертвий (HP <= 0)
        if current_health <= 0:
            logger.error(f"❌ Бос має HP={current_health}! Примусово переможемо його.")
            # Примусово переможемо боса
            cursor.execute('''
                UPDATE bosses
                SET is_active = FALSE,
                    defeat_date = %s,
                    defeated_by_user_id = %s,
                    defeat_count = COALESCE(defeat_count, 0) + 1,
                    level = COALESCE(level, 1) + 1
                WHERE id = %s
            ''', (now, user_id, boss_id))
            conn.commit()
            return {'defeated': True, 'boss_id': boss_id, 'defeated_by_user_id': user_id, 'was_bugged': True}

        # Обмежуємо шкоду поточним HP боса (не можна завдати більше ніж у боса HP)
        actual_damage = min(damage, current_health)
        if damage > current_health:
            logger.info(f"⚠️ Шкода обмежена: {damage} → {actual_damage} (бос мав {current_health} HP)")
        
        new_health = current_health - actual_damage
        logger.info(f"💥 Нове HP боса: {current_health} - {actual_damage} = {new_health}")

        # Додаємо шкоду до учасника (оновлюємо joined_at для кулдауну)
        logger.info(f"INSERT/UPDATE boss_battle_participants")
        cursor.execute('''
            INSERT INTO boss_battle_participants (boss_id, user_id, chat_id, damage_dealt, joined_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (boss_id, user_id, chat_id) DO UPDATE SET
                damage_dealt = boss_battle_participants.damage_dealt + %s,
                joined_at = EXCLUDED.joined_at
        ''', (boss_id, user_id, chat_id, actual_damage, now, actual_damage))
        logger.info(f"✅ Додано шкоду в boss_battle_participants")

        # Оновлюємо здоров'я боса
        logger.info(f"UPDATE bosses SET health = {new_health} WHERE id = {boss_id}")
        cursor.execute('''
            UPDATE bosses SET health = %s WHERE id = %s
        ''', (new_health, boss_id))
        logger.info(f"✅ Оновлено HP боса: {current_health} → {new_health}")

        # Перевіряємо чи переможено
        if new_health <= 0:
            logger.info(f"🎉 Бос переможений!")
            # Бос переможений - збільшуємо рівень та силу
            cursor.execute('''
                UPDATE bosses
                SET is_active = FALSE,
                    defeat_date = %s,
                    defeated_by_user_id = %s,
                    defeat_count = COALESCE(defeat_count, 0) + 1,
                    level = COALESCE(level, 1) + 1,
                    health = 0  # Примусово ставимо 0 HP
                WHERE id = %s
            ''', (now, user_id, boss_id))
            conn.commit()
            logger.info(f"✅ Бос переможений, повертаємо result")
            return {'defeated': True, 'boss_id': boss_id, 'defeated_by_user_id': user_id}

        conn.commit()
        logger.info(f"✅ Атака успішна, бос живий: {new_health} HP, повертаємо result")
        return {'defeated': False, 'boss_id': boss_id, 'remaining_health': new_health, 'max_health': max_health}
    except Exception as e:
        logger.error(f"❌ Помилка атаки боса: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return {'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
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

def get_boss_defeat_time():
    """Отримує час останньої перемоги над босом (тільки якщо немає активного боса)"""
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        # Спочатку перевіряємо чи є активний бос
        cursor.execute('SELECT id FROM bosses WHERE is_active = TRUE LIMIT 1')
        active_boss = cursor.fetchone()
        
        # Якщо є активний бос - повертаємо 0 (немає блоку)
        if active_boss:
            return 0
        
        # Якщо немає активного боса - перевіряємо коли був переможений останній
        cursor.execute('''
            SELECT defeat_date FROM bosses 
            WHERE is_active = FALSE AND defeat_date IS NOT NULL
            ORDER BY id DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.error(f"❌ Помилка отримання часу перемоги: {e}")
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
# НОВІ ФУНКЦІЇ ДЛЯ БОНУСІВ ВІД ДІТЕЙ
# ============================================

def get_children_bonuses(user_id, chat_id):
    """
    Отримує бонуси від всіх дітей користувача
    Повертає: {'total_bonus': float, 'bonuses': list}
    """
    conn = get_connection()
    if not conn:
        return {'total_bonus': 0, 'bonuses': []}

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, name, weight, inherited_trait, born_at
            FROM children
            WHERE (user_id = %s OR father_user_id = %s OR mother_user_id = %s) 
            AND chat_id = %s
            ORDER BY weight DESC
        ''', (user_id, user_id, user_id, chat_id))
        rows = cursor.fetchall()

        bonuses = []
        total_bonus = 0

        for row in rows:
            child_id = int(row[0])
            name = row[1]
            weight = int(row[2]) if row[2] else 0
            trait = row[3] or ''
            born_at = int(row[4]) if row[4] else 0

            # Розрахунок бонусів на основі ваги та особливостей
            bonus = 0
            bonus_type = ''

            # Базовий бонус від ваги (1% за кожні 10 кг)
            base_bonus = weight / 10

            # Бонус за особливість
            if 'мутація' in trait.lower():
                bonus = base_bonus * 2  # Подвійний бонус за мутацію
                bonus_type = 'mutation'
            elif 'легендарний' in trait.lower() or '⭐' in trait:
                bonus = base_bonus * 1.5
                bonus_type = 'legendary'
            elif 'рідкісний' in trait.lower() or '🔵' in trait:
                bonus = base_bonus * 1.2
                bonus_type = 'rare'
            else:
                bonus = base_bonus
                bonus_type = 'normal'

            # Бонус за вік (старші діти дають +10% бонусу за кожен день)
            age_days = (time.time() - born_at) / 86400
            age_bonus = 1 + (min(age_days, 30) * 0.1)  # Макс +300% за 30 днів

            bonus = bonus * age_bonus
            total_bonus += bonus

            bonuses.append({
                'id': child_id,
                'name': name,
                'weight': weight,
                'bonus': bonus,
                'bonus_type': bonus_type,
                'age_days': int(age_days)
            })

        return {
            'total_bonus': total_bonus,
            'bonuses': bonuses,
            'children_count': len(bonuses)
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання бонусів дітей: {e}")
        return {'total_bonus': 0, 'bonuses': [], 'children_count': 0}
    finally:
        cursor.close()
        conn.close()


def train_child(child_id, user_id, chat_id, training_type='weight'):
    """
    Тренує дитину (покращує статистику)
    training_type: 'weight', 'genes', 'skills'
    Повертає: {'success': bool, 'new_weight': int, 'cost': int}
    """
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

        current_weight = int(child[6]) if child[6] else 0
        cost = 50  # Вартість тренування

        # Перевіряємо чи вистачає монет (це перевіряється в боті)
        # Тренування
        weight_gain = random.randint(2, 8)
        new_weight = current_weight + weight_gain

        # Оновлюємо вагу
        cursor.execute('''
            UPDATE children SET weight = %s WHERE id = %s
        ''', (new_weight, child_id))
        conn.commit()

        return {
            'success': True,
            'new_weight': new_weight,
            'weight_gain': weight_gain,
            'cost': cost
        }
    except Exception as e:
        logger.error(f"❌ Помилка тренування дитини: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def send_child_on_raid(child_id, user_id, chat_id, raid_type='coins'):
    """
    Відправляє дитину в рейд за ресурсами
    raid_type: 'coins', 'xp', 'items'
    Повертає: {'success': bool, 'reward': int, 'time': int}
    """
    import random
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

        weight = int(child[6]) if child[6] else 0

        # Розрахунок нагороди
        base_reward = weight * 5
        reward = random.randint(int(base_reward * 0.8), int(base_reward * 1.2))

        # Час рейду в секундах (залежить від ваги)
        raid_time = max(300, 3600 - (weight * 10))  # 5 хв - 1 год

        return {
            'success': True,
            'reward': reward,
            'raid_time': raid_time,
            'raid_type': raid_type
        }
    except Exception as e:
        logger.error(f"❌ Помилка рейду дитини: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_child_power(child_id, chat_id):
    """
    Розраховує силу дитини для дуелей
    Повертає: {'power': int, 'stats': dict}
    """
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM children WHERE id = %s AND chat_id = %s',
                      (child_id, chat_id))
        child = cursor.fetchone()

        if not child:
            return None

        weight = int(child[6]) if child[6] else 0
        trait = child[7] or ''

        # Отримуємо гени дитини
        cursor.execute('SELECT * FROM hryak_genes WHERE user_id = %s AND chat_id = %s',
                      (child[1], chat_id))
        genes = cursor.fetchone()

        # Базова сила = вага * 2
        power = weight * 2

        # Бонус від генів
        if genes:
            gene_rarity = genes[3] or 'C'
            rarity_mult = {'C': 1, 'R': 1.5, 'E': 2, 'L': 3, 'S': 5}.get(gene_rarity, 1)
            power *= rarity_mult

            bonus_type = genes[4]
            bonus_value = int(genes[5]) if genes[5] else 0

            if bonus_type == 'strength':
                power *= (1 + bonus_value / 100)

        # Бонус від особливості
        if 'мутація' in trait.lower():
            power *= 2
        elif 'легендарний' in trait.lower():
            power *= 1.5

        return {
            'power': int(power),
            'weight': weight,
            'trait': trait,
            'has_genes': genes is not None
        }
    except Exception as e:
        logger.error(f"❌ Помилка розрахунку сили дитини: {e}")
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
    """Отримує всі івенти (тільки унікальні за назвою)"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        # Отримуємо тільки унікальні івенти (останній запис для кожної назви)
        cursor.execute('''
            SELECT DISTINCT ON (name) *
            FROM seasonal_events
            ORDER BY name, start_date DESC
        ''')
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

def cleanup_duplicate_events():
    """Видаляє дублікати івентів з бази даних"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Видаляємо дублікати, залишаючи тільки останній запис для кожної назви
        cursor.execute('''
            DELETE FROM seasonal_events
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM seasonal_events
                GROUP BY name
            )
        ''')
        deleted = cursor.rowcount
        conn.commit()
        logger.info(f"✅ Видалено {deleted} дублікатів івентів")
        return True
    except Exception as e:
        logger.error(f"❌ Помилка видалення дублікатів: {e}")
        conn.rollback()
        return False
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

def get_level_bonuses(level):
    """Отримує бонуси за рівень"""
    return {
        'coins_bonus': (level - 1) * 5,  # +5% монет за рівень
        'xp_bonus': (level - 1) * 2,  # +2% XP за рівень
        'power_bonus': (level - 1) * 1,  # +1% сили за рівень
        'duel_bonus': (level - 1) * 0.5  # +0.5% до дуелей за рівень
    }

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


# ============================================
# ГЕНЕТИКА - НОВІ ФУНКЦІЇ
# ============================================

# Рідкості генів
GENE_RARITIES = {
    'C': {'name': 'Звичайний', 'color': '⚪', 'chance': 70, 'bonus_mult': 1},
    'R': {'name': 'Рідкісний', 'color': '🔵', 'chance': 20, 'bonus_mult': 2},
    'E': {'name': 'Епічний', 'color': '🟣', 'chance': 7, 'bonus_mult': 3},
    'L': {'name': 'Легендарний', 'color': '🟡', 'chance': 2.5, 'bonus_mult': 5},
    'S': {'name': 'Особливий', 'color': '🔴', 'chance': 0.5, 'bonus_mult': 10}
}

# Типи бонусів
BONUS_TYPES = {
    'weight_gain': {'name': 'Приріст ваги', 'desc': '+X% до приросту ваги'},
    'strength': {'name': 'Сила', 'desc': '+X% до сили в дуелі'},
    'luck': {'name': 'Удача', 'desc': '+X% шанс критичного удару'},
    'xp_bonus': {'name': 'Досвід', 'desc': '+X% до отриманого XP'},
    'coin_bonus': {'name': 'Монети', 'desc': '+X% до отриманих монет'},
    'mutation': {'name': 'Мутація', 'desc': 'Унікальна здібність'}
}

# Кольори хряків
COLOR_TYPES = {
    'normal': {'name': 'Звичайний', 'emoji': '🐷', 'chance': 60},
    'wild': {'name': 'Дикий', 'emoji': '🐗', 'chance': 20},
    'golden': {'name': 'Золотий', 'emoji': '✨', 'chance': 10},
    'rainbow': {'name': 'Веселка', 'emoji': '🌈', 'chance': 5},
    'cyber': {'name': 'Кібер', 'emoji': '🤖', 'chance': 3},
    'royal': {'name': 'Королівський', 'emoji': '👑', 'chance': 1.5},
    'void': {'name': 'Порожнеча', 'emoji': '🌑', 'chance': 0.5}
}


def get_hryak_genes(user_id, chat_id):
    """Отримує гени хряка користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM hryak_genes
            WHERE user_id = %s AND chat_id = %s
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': int(row[0]),
            'user_id': int(row[1]),
            'chat_id': int(row[2]),
            'gene_rarity': row[3] or 'C',
            'bonus_type': row[4],
            'bonus_value': int(row[5]) if row[5] else 0,
            'color_type': row[6] or 'normal',
            'mutation_chance': float(row[7]) if row[7] else 0.05,
            'updated_at': int(row[8]) if row[8] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання генів: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def create_hryak_genes(user_id, chat_id, gene_rarity='C', bonus_type=None, bonus_value=0, color_type='normal'):
    """Створює гени для хряка"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO hryak_genes (user_id, chat_id, gene_rarity, bonus_type, bonus_value, color_type, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                gene_rarity = EXCLUDED.gene_rarity,
                bonus_type = EXCLUDED.bonus_type,
                bonus_value = EXCLUDED.bonus_value,
                color_type = EXCLUDED.color_type,
                updated_at = EXCLUDED.updated_at
        ''', (user_id, chat_id, gene_rarity, bonus_type, bonus_value, color_type, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка створення генів: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def calculate_offspring_genes(father_genes, mother_genes):
    """
    Розраховує гени потомства на основі генів батьків
    Повертає: gene_rarity, bonus_type, bonus_value, color_type, has_mutation
    """
    import random
    
    # Визначаємо рідкість гена потомства
    father_rarity = father_genes.get('gene_rarity', 'C') if father_genes else 'C'
    mother_rarity = mother_genes.get('gene_rarity', 'C') if mother_genes else 'C'
    
    # Шанс на підвищення рідкості (5% на кожну рідкість вище)
    rarity_upgrade_chance = 0.05
    if father_rarity != mother_rarity:
        rarity_upgrade_chance += 0.03  # Бонус за різні гени
    
    # Визначаємо базову рідкість (середня або краща)
    rarity_order = ['C', 'R', 'E', 'L', 'S']
    father_idx = rarity_order.index(father_rarity) if father_rarity in rarity_order else 0
    mother_idx = rarity_order.index(mother_rarity) if mother_rarity in rarity_order else 0
    
    # Базова рідкість - середня або краща з шансом
    if random.random() < 0.6:  # 60% шанс взяти кращий ген
        base_rarity_idx = max(father_idx, mother_idx)
    else:  # 40% шанс середнього
        base_rarity_idx = (father_idx + mother_idx) // 2
    
    # Перевірка на підвищення рідкості
    if random.random() < rarity_upgrade_chance and base_rarity_idx < len(rarity_order) - 1:
        base_rarity_idx += 1
    
    offspring_rarity = rarity_order[base_rarity_idx]
    
    # Визначаємо тип бонусу (успадковується від одного з батьків)
    bonus_type = None
    bonus_value = 0
    
    father_bonus = father_genes.get('bonus_type') if father_genes else None
    mother_bonus = mother_genes.get('bonus_type') if mother_genes else None
    
    if father_bonus and mother_bonus:
        # Обидва мають бонус - обираємо випадково або комбінуємо
        if random.random() < 0.5:
            bonus_type = father_bonus
            bonus_value = father_genes.get('bonus_value', 0)
        else:
            bonus_type = mother_bonus
            bonus_value = mother_genes.get('bonus_value', 0)
    elif father_bonus:
        bonus_type = father_bonus
        bonus_value = father_genes.get('bonus_value', 0)
    elif mother_bonus:
        bonus_type = mother_bonus
        bonus_value = mother_genes.get('bonus_value', 0)
    
    # Розраховуємо значення бонусу на основі рідкості
    if bonus_type:
        rarity_mult = GENE_RARITIES.get(offspring_rarity, {}).get('bonus_mult', 1)
        bonus_value = int(bonus_value * rarity_mult * random.uniform(0.8, 1.2))
    
    # Визначаємо колір потомства
    father_color = father_genes.get('color_type', 'normal') if father_genes else 'normal'
    mother_color = mother_genes.get('color_type', 'normal') if mother_genes else 'normal'
    
    # 70% шанс успадкувати один з батьківських кольорів
    if random.random() < 0.7:
        offspring_color = random.choice([father_color, mother_color])
    else:
        # 30% шанс на новий колір на основі ймовірностей
        rand = random.random() * 100
        cumulative = 0
        offspring_color = 'normal'
        for color, data in COLOR_TYPES.items():
            cumulative += data['chance']
            if rand <= cumulative:
                offspring_color = color
                break
    
    # Перевірка на мутацію (1-5% залежно від генів)
    father_mutation_chance = father_genes.get('mutation_chance', 0.05) if father_genes else 0.05
    mother_mutation_chance = mother_genes.get('mutation_chance', 0.05) if mother_genes else 0.05
    mutation_chance = (father_mutation_chance + mother_mutation_chance) / 2
    
    has_mutation = random.random() < mutation_chance
    
    return {
        'gene_rarity': offspring_rarity,
        'bonus_type': bonus_type,
        'bonus_value': bonus_value,
        'color_type': offspring_color,
        'has_mutation': has_mutation
    }


def breed_hryaks(father_user_id, mother_user_id, chat_id, father_hryak, mother_hryak):
    """
    Схрещує двох хряків та створює потомство
    Повертає: {'success': bool, 'child': dict, 'error': str}
    """
    import random
    
    # Отримуємо гени батьків
    father_genes = get_hryak_genes(father_user_id, chat_id)
    mother_genes = get_hryak_genes(mother_user_id, chat_id)
    
    # Розраховуємо гени потомства
    offspring_genes = calculate_offspring_genes(father_genes, mother_genes)
    
    # Розраховуємо вагу потомства (середня батьків + рандом)
    father_weight = father_hryak.get('weight', 10) if father_hryak else 10
    mother_weight = mother_hryak.get('weight', 10) if mother_hryak else 10
    
    # Вага = середня + генетичний бонус + рандом
    base_weight = (father_weight + mother_weight) // 2
    gene_bonus = GENE_RARITIES.get(offspring_genes['gene_rarity'], {}).get('bonus_mult', 1) * 2
    random_variance = random.randint(-5, 10)
    child_weight = max(1, base_weight + gene_bonus + random_variance)
    
    # Визначаємо назву особливості
    inherited_trait = ""
    if offspring_genes['has_mutation']:
        inherited_trait = "🧬 Мутація!"
    elif offspring_genes['gene_rarity'] in ['L', 'S']:
        inherited_trait = f"⭐ {GENE_RARITIES[offspring_genes['gene_rarity']]['name']}"
    elif offspring_genes['bonus_type']:
        bonus_name = BONUS_TYPES.get(offspring_genes['bonus_type'], {}).get('name', 'Бонус')
        inherited_trait = f"+{offspring_genes['bonus_value']}% {bonus_name}"
    
    # Створюємо запис про дитину
    child_name = f"Нащадок {father_hryak['name'][:10]} та {mother_hryak['name'][:10]}"
    
    # Генеруємо унікальне ім'я на основі кольору
    color_emoji = COLOR_TYPES.get(offspring_genes['color_type'], {}).get('emoji', '🐷')
    child_name = f"{color_emoji} {offspring_genes['gene_rarity']}-{random.randint(1, 999)}"
    
    success = add_child(
        user_id=father_user_id,  # Власник = батько
        chat_id=chat_id,
        father_user_id=father_user_id,
        mother_user_id=mother_user_id,
        name=child_name,
        weight=child_weight,
        inherited_trait=inherited_trait
    )
    
    if not success:
        return {'success': False, 'error': 'Не вдалося створити потомство'}
    
    # Зберігаємо гени дитини (для майбутнього використання)
    # Note: add_child повертає ID дитини, але нам потрібно оновити з генами
    
    return {
        'success': True,
        'child': {
            'name': child_name,
            'weight': child_weight,
            'gene_rarity': offspring_genes['gene_rarity'],
            'bonus_type': offspring_genes['bonus_type'],
            'bonus_value': offspring_genes['bonus_value'],
            'color_type': offspring_genes['color_type'],
            'has_mutation': offspring_genes['has_mutation'],
            'inherited_trait': inherited_trait
        }
    }


def update_child_genes(child_id, gene_rarity, bonus_type=None, bonus_value=0, color_type='normal'):
    """Оновлює гени дитини (використовується при народженні)"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Отримуємо user_id та chat_id з дитини
        cursor.execute('SELECT user_id, chat_id FROM children WHERE id = %s', (child_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        user_id, chat_id = int(row[0]), int(row[1])
        now = int(time.time())
        
        cursor.execute('''
            INSERT INTO hryak_genes (user_id, chat_id, gene_rarity, bonus_type, bonus_value, color_type, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                gene_rarity = EXCLUDED.gene_rarity,
                bonus_type = EXCLUDED.bonus_type,
                bonus_value = EXCLUDED.bonus_value,
                color_type = EXCLUDED.color_type,
                updated_at = EXCLUDED.updated_at
        ''', (user_id, chat_id, gene_rarity, bonus_type, bonus_value, color_type, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка оновлення генів дитини: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_genetic_compatibility(father_user_id, mother_user_id, chat_id):
    """
    Перевіряє генетичну сумісність пари
    Повертає: {'compatibility': str, 'bonus_chance': float, 'mutation_chance': float}
    """
    father_genes = get_hryak_genes(father_user_id, chat_id)
    mother_genes = get_hryak_genes(mother_user_id, chat_id)
    
    if not father_genes or not mother_genes:
        return {'compatibility': 'unknown', 'bonus_chance': 0.5, 'mutation_chance': 0.05}
    
    # Сумісність за рідкістю
    father_rarity = father_genes.get('gene_rarity', 'C')
    mother_rarity = mother_genes.get('gene_rarity', 'C')
    
    rarity_order = ['C', 'R', 'E', 'L', 'S']
    father_idx = rarity_order.index(father_rarity) if father_rarity in rarity_order else 0
    mother_idx = rarity_order.index(mother_rarity) if mother_rarity in rarity_order else 0
    
    # Чим ближчі рідкості - тим вища сумісність
    rarity_diff = abs(father_idx - mother_idx)
    compatibility_score = max(0, 100 - (rarity_diff * 15))
    
    if compatibility_score >= 85:
        compatibility = 'Ідеальна'
    elif compatibility_score >= 70:
        compatibility = 'Висока'
    elif compatibility_score >= 50:
        compatibility = 'Середня'
    else:
        compatibility = 'Низька'
    
    # Шанс на бонус залежить від сумісності
    bonus_chance = 0.3 + (compatibility_score / 200)
    
    # Шанс на мутацію
    mutation_chance = (father_genes.get('mutation_chance', 0.05) + mother_genes.get('mutation_chance', 0.05)) / 2
    
    return {
        'compatibility': compatibility,
        'bonus_chance': bonus_chance,
        'mutation_chance': mutation_chance
    }


# ============================================
# ГІЛЬДІЙНІ ВІЙНИ - НОВІ ФУНКЦІЇ
# ============================================

# Типи територій
TERRITORY_TYPES = {
    'mine': {'name': 'Шахта', 'bonus_type': 'coins', 'bonus_value': 100, 'income': 50},
    'forest': {'name': 'Ліс', 'bonus_type': 'xp', 'bonus_value': 50, 'income': 25},
    'castle': {'name': 'Замок', 'bonus_type': 'power', 'bonus_value': 10, 'income': 100},
    'temple': {'name': 'Храм', 'bonus_type': 'blessing', 'bonus_value': 5, 'income': 75},
    'market': {'name': 'Ринок', 'bonus_type': 'trade', 'bonus_value': 15, 'income': 120},
    'fortress': {'name': 'Фортеця', 'bonus_type': 'defense', 'bonus_value': 20, 'income': 80}
}


def create_territory(name, territory_type, owner_guild_id=None):
    """Створює нову територію"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        territory_data = TERRITORY_TYPES.get(territory_type, TERRITORY_TYPES['mine'])
        
        cursor.execute('''
            INSERT INTO guild_territories (name, owner_guild_id, bonus_type, bonus_value, captured_at, income_per_hour, last_income_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (name, owner_guild_id, territory_data['bonus_type'], territory_data['bonus_value'], 
              now, territory_data['income'], now))
        
        territory_id = cursor.fetchone()[0]
        conn.commit()
        return territory_id
    except Exception as e:
        logger.error(f"❌ Помилка створення території: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_all_territories():
    """Отримує всі території"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT gt.id, gt.name, gt.owner_guild_id, gt.bonus_type, 
                   gt.bonus_value, gt.captured_at, gt.income_per_hour, 
                   gt.last_income_at, g.name as guild_name
            FROM guild_territories gt
            LEFT JOIN guilds g ON gt.owner_guild_id = g.id
            ORDER BY gt.income_per_hour DESC
        ''')
        rows = cursor.fetchall()

        territories = []
        for row in rows:
            territories.append({
                'id': int(row[0]),
                'name': row[1],
                'owner_guild_id': int(row[2]) if row[2] else None,
                'bonus_type': row[3],
                'bonus_value': int(row[4]) if row[4] else 0,
                'captured_at': int(row[5]) if row[5] else 0,
                'income_per_hour': int(row[6]) if row[6] else 0,
                'last_income_at': int(row[7]) if row[7] else 0,
                'guild_name': row[8]
            })
        logger.info(f"✅ Отримано {len(territories)} територій")
        return territories
    except Exception as e:
        logger.error(f"❌ Помилка отримання територій: {e}", exc_info=True)
        return []
    finally:
        cursor.close()
        conn.close()


def get_territory(territory_id):
    """Отримує територію за ID"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT gt.*, g.name as guild_name
            FROM guild_territories gt
            LEFT JOIN guilds g ON gt.owner_guild_id = g.id
            WHERE gt.id = %s
        ''', (territory_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            'id': int(row[0]),
            'name': row[1],
            'owner_guild_id': int(row[2]) if row[2] else None,
            'guild_name': row[3],
            'bonus_type': row[4],
            'bonus_value': int(row[5]) if row[5] else 0,
            'captured_at': int(row[6]) if row[6] else 0,
            'income_per_hour': int(row[7]) if row[7] else 0,
            'last_income_at': int(row[8]) if row[8] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання території: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def capture_territory(territory_id, guild_id):
    """Захоплює територію"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            UPDATE guild_territories
            SET owner_guild_id = %s, captured_at = %s, last_income_at = %s
            WHERE id = %s
        ''', (guild_id, now, now, territory_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка захоплення території: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def collect_territory_income(guild_id):
    """Збирає дохід з всіх територій гільдії"""
    logger.info(f"💰 Збір доходу для гільдії {guild_id}")
    
    conn = get_connection()
    if not conn:
        return {'coins': 0, 'xp': 0}

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            SELECT id, name, owner_guild_id, bonus_type, bonus_value, 
                   captured_at, income_per_hour, last_income_at
            FROM guild_territories
            WHERE owner_guild_id = %s
        ''', (guild_id,))
        rows = cursor.fetchall()

        total_coins = 0
        total_xp = 0
        territories_count = 0

        for row in rows:
            territory_id = int(row[0])
            territory_name = row[1]
            bonus_type = row[3]
            income = int(row[6]) if row[6] else 0  # income_per_hour
            last_income = int(row[7]) if row[7] else 0  # last_income_at

            # Розраховуємо скільки годин пройшло
            hours_passed = (now - last_income) / 3600
            logger.info(f"📊 Територія {territory_name}: {hours_passed:.1f} год, дохід {income}/год")

            if hours_passed >= 1:
                income_amount = int(income * hours_passed)
                territories_count += 1

                if bonus_type == 'coins' or bonus_type == 'trade':
                    total_coins += income_amount
                    logger.info(f"  💰 +{income_amount} монет")
                elif bonus_type == 'xp':
                    total_xp += income_amount
                    logger.info(f"  ⭐ +{income_amount} XP")

                # Оновлюємо last_income_at
                cursor.execute('''
                    UPDATE guild_territories SET last_income_at = %s WHERE id = %s
                ''', (now, territory_id))

        conn.commit()
        logger.info(f"✅ Зібрано дохід: {total_coins} монет, {total_xp} XP з {territories_count} територій")
        return {'coins': total_coins, 'xp': total_xp}
    except Exception as e:
        logger.error(f"❌ Помилка збору доходу: {e}", exc_info=True)
        conn.rollback()
        return {'coins': 0, 'xp': 0}
    finally:
        cursor.close()
        conn.close()


# ============================================
# ГІЛЬДІЙНІ СКРИНЬКИ
# ============================================

def donate_to_chest(guild_id, user_id, item_type, item_name, quantity=1):
    """Вносить предмет до гільдійної скриньки"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        
        # Перевіряємо чи вже є такий предмет
        cursor.execute('''
            SELECT id, quantity FROM guild_chests
            WHERE guild_id = %s AND item_type = %s AND item_name = %s
        ''', (guild_id, item_type, item_name))
        row = cursor.fetchone()
        
        if row:
            # Оновлюємо кількість
            cursor.execute('''
                UPDATE guild_chests SET quantity = quantity + %s WHERE id = %s
            ''', (quantity, int(row[0])))
        else:
            # Додаємо новий предмет
            cursor.execute('''
                INSERT INTO guild_chests (guild_id, item_type, item_name, quantity, donated_by_user_id, donated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (guild_id, item_type, item_name, quantity, user_id, now))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка внеску до скриньки: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_guild_chest(guild_id):
    """Отримує вміст гільдійної скриньки"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT gc.*, u.username as donor_name
            FROM guild_chests gc
            LEFT JOIN user_languages u ON gc.donated_by_user_id = u.user_id
            WHERE gc.guild_id = %s
            ORDER BY gc.quantity DESC
        ''', (guild_id,))
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'id': int(row[0]),
                'guild_id': int(row[1]),
                'item_type': row[2],
                'item_name': row[3],
                'quantity': int(row[4]) if row[4] else 0,
                'donated_by_user_id': int(row[5]) if row[5] else None,
                'donor_name': row[6],
                'donated_at': int(row[7]) if row[7] else 0
            })
        return items
    except Exception as e:
        logger.error(f"❌ Помилка отримання скриньки: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def withdraw_from_chest(guild_id, item_id, quantity=1):
    """Виводить предмет з гільдійної скриньки (старий метод)"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Перевіряємо кількість
        cursor.execute('SELECT quantity FROM guild_chests WHERE id = %s AND guild_id = %s', (item_id, guild_id))
        row = cursor.fetchone()

        if not row or row[0] < quantity:
            return False

        if quantity == row[0]:
            cursor.execute('DELETE FROM guild_chests WHERE id = %s', (item_id,))
        else:
            cursor.execute('UPDATE guild_chests SET quantity = quantity - %s WHERE id = %s', (quantity, item_id))

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка виводу зі скриньки: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def withdraw_guild_item_to_user(guild_id, user_id, chat_id, item_id, quantity=1):
    """
    Виводить предмет з гільдійної скриньки в особистий інвентар користувача
    Повертає: {'success': bool, 'item': dict, 'error': str}
    """
    conn = get_connection()
    if not conn:
        return {'success': False, 'error': 'Помилка БД'}

    cursor = conn.cursor()
    try:
        # Отримуємо предмет з гільдійної скриньки
        cursor.execute('''
            SELECT * FROM guild_items
            WHERE id = %s AND guild_id = %s
        ''', (item_id, guild_id))
        row = cursor.fetchone()

        if not row:
            return {'success': False, 'error': 'Предмет не знайдено'}

        item_quantity = int(row[7]) if row[7] else 0
        if item_quantity < quantity:
            return {'success': False, 'error': 'Недостатньо предметів'}

        # Створюємо предмет в інвентарі користувача
        now = int(time.time())
        item_data = {
            'id': int(row[0]),
            'item_type': row[2],
            'item_name': row[3],
            'rarity': row[4],
            'bonus_type': row[5],
            'bonus_value': int(row[6]) if row[6] else 0
        }

        # Додаємо до інвентарю користувача
        cursor.execute('''
            INSERT INTO user_items (user_id, chat_id, item_type, item_name, rarity,
                                   bonus_type, bonus_value, quantity, obtained_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id, item_type, item_name) DO UPDATE SET
                quantity = user_items.quantity + EXCLUDED.quantity,
                bonus_value = GREATEST(user_items.bonus_value, EXCLUDED.bonus_value)
        ''', (user_id, chat_id, item_data['item_type'], item_data['item_name'],
              item_data['rarity'], item_data['bonus_type'], item_data['bonus_value'], quantity, now))

        # Видаляємо з гільдійної скриньки
        if quantity >= item_quantity:
            cursor.execute('DELETE FROM guild_items WHERE id = %s', (item_id,))
        else:
            cursor.execute('UPDATE guild_items SET quantity = quantity - %s WHERE id = %s', (quantity, item_id))

        conn.commit()

        return {
            'success': True,
            'item': {
                'name': item_data['item_name'],
                'type': item_data['item_type'],
                'rarity': item_data['rarity'],
                'bonus_type': item_data['bonus_type'],
                'bonus_value': item_data['bonus_value'],
                'quantity': quantity
            }
        }
    except Exception as e:
        logger.error(f"❌ Помилка виводу предмета: {e}")
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()


def use_item(user_id, chat_id, item_id):
    """
    Використовує предмет (дає баф)
    Повертає: {'success': bool, 'effect': str, 'duration': int}
    """
    conn = get_connection()
    if not conn:
        return {'success': False, 'error': 'Помилка БД'}

    cursor = conn.cursor()
    try:
        # Отримуємо предмет
        cursor.execute('''
            SELECT * FROM user_items
            WHERE id = %s AND user_id = %s AND chat_id = %s
        ''', (item_id, user_id, chat_id))
        row = cursor.fetchone()

        if not row:
            return {'success': False, 'error': 'Предмет не знайдено'}

        quantity = int(row[7]) if row[7] else 0
        if quantity <= 0:
            return {'success': False, 'error': 'Предметів немає'}

        item_type = row[3]
        bonus_type = row[6]
        bonus_value = int(row[7]) if row[7] else 0
        rarity = row[5]

        # Розрахунок ефекту
        rarity_mult = ITEM_RARITIES.get(rarity, {}).get('bonus_mult', 1)
        effect_value = bonus_value * rarity_mult

        # Тривалість залежить від типу
        duration = 3600  # 1 година за замовчуванням
        if item_type == 'consumable':
            duration = 1800  # 30 хвилин
        elif rarity == 'legendary':
            duration = 7200  # 2 години
        elif rarity == 'mythic':
            duration = 14400  # 4 години

        # Видаляємо предмет (споживний)
        if item_type == 'consumable':
            if quantity == 1:
                cursor.execute('DELETE FROM user_items WHERE id = %s', (item_id,))
            else:
                cursor.execute('UPDATE user_items SET quantity = quantity - 1 WHERE id = %s', (item_id,))
            conn.commit()

        # TODO: Додати таблицю active_buffs для зберігання активних бафів
        # Поки що просто повертаємо інформацію

        return {
            'success': True,
            'effect': f"+{effect_value} {bonus_type}",
            'duration': duration,
            'item_name': row[4]
        }
    except Exception as e:
        logger.error(f"❌ Помилка використання предмета: {e}")
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()


# ============================================
# ГІЛЬДІЙНІ ВІЙНИ
# ============================================

def declare_war(attacker_guild_id, defender_guild_id, territory_id=None):
    """Оголошує війну між гільдіями"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO guild_wars (attacker_guild_id, defender_guild_id, territory_id, started_at, status)
            VALUES (%s, %s, %s, %s, 'active')
            RETURNING id
        ''', (attacker_guild_id, defender_guild_id, territory_id, now))
        
        war_id = cursor.fetchone()[0]
        conn.commit()
        return war_id
    except Exception as e:
        logger.error(f"❌ Помилка оголошення війни: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def join_war(war_id, user_id, guild_id):
    """Гравець приєднується до війни"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO guild_war_participants (war_id, user_id, guild_id, joined_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', (war_id, user_id, guild_id, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка приєднання до війни: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def add_war_contribution(war_id, user_id, guild_id, contribution):
    """Додає внесок у війну"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE guild_war_participants
            SET contribution = contribution + %s,
                battles_fought = battles_fought + 1
            WHERE war_id = %s AND user_id = %s AND guild_id = %s
        ''', (contribution, war_id, user_id, guild_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка додавання внеску: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def end_war(war_id, winner_guild_id):
    """Завершує війну"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        
        # Отримуємо інформацію про війну
        cursor.execute('''
            SELECT territory_id FROM guild_wars WHERE id = %s
        ''', (war_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            # Передаємо територію переможцю
            cursor.execute('''
                UPDATE guild_territories SET owner_guild_id = %s WHERE id = %s
            ''', (winner_guild_id, int(row[0])))
        
        # Завершуємо війну
        cursor.execute('''
            UPDATE guild_wars
            SET status = 'ended', ended_at = %s, winner_guild_id = %s
            WHERE id = %s
        ''', (now, winner_guild_id, war_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка завершення війни: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_active_wars(guild_id=None):
    """Отримує активні війни"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        if guild_id:
            cursor.execute('''
                SELECT gw.*, 
                    ag.name as attacker_name, 
                    dg.name as defender_name
                FROM guild_wars gw
                JOIN guilds ag ON gw.attacker_guild_id = ag.id
                JOIN guilds dg ON gw.defender_guild_id = dg.id
                WHERE gw.status = 'active' AND (gw.attacker_guild_id = %s OR gw.defender_guild_id = %s)
            ''', (guild_id, guild_id))
        else:
            cursor.execute('''
                SELECT gw.*, 
                    ag.name as attacker_name, 
                    dg.name as defender_name
                FROM guild_wars gw
                JOIN guilds ag ON gw.attacker_guild_id = ag.id
                JOIN guilds dg ON gw.defender_guild_id = dg.id
                WHERE gw.status = 'active'
            ''')
        
        rows = cursor.fetchall()
        wars = []
        for row in rows:
            wars.append({
                'id': int(row[0]),
                'attacker_guild_id': int(row[1]),
                'defender_guild_id': int(row[2]),
                'territory_id': int(row[3]) if row[3] else None,
                'status': row[4],
                'started_at': int(row[5]) if row[5] else 0,
                'ended_at': int(row[6]) if row[6] else 0,
                'winner_guild_id': int(row[7]) if row[7] else None,
                'attacker_score': int(row[8]) if row[8] else 0,
                'defender_score': int(row[9]) if row[9] else 0,
                'attacker_name': row[10],
                'defender_name': row[11]
            })
        return wars
    except Exception as e:
        logger.error(f"❌ Помилка отримання воєн: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ГІЛЬДІЙНІ БОСИ
# ============================================

def spawn_guild_boss(name, level, health, damage, reward_coins, reward_xp, owner_guild_id=None):
    """Створює боса для гільдії"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO guild_bosses (name, level, health, max_health, damage, reward_coins, reward_xp, 
                                      owner_guild_id, spawn_date, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id
        ''', (name, level, health, health, damage, reward_coins, reward_xp, owner_guild_id, now))
        
        boss_id = cursor.fetchone()[0]
        conn.commit()
        return boss_id
    except Exception as e:
        logger.error(f"❌ Помилка створення боса гільдії: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def attack_guild_boss(boss_id, user_id, guild_id, damage):
    """Атакує боса гільдії"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        
        # Додаємо шкоду
        cursor.execute('''
            INSERT INTO guild_boss_participants (boss_id, user_id, guild_id, damage_dealt, joined_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (boss_id, user_id, guild_id) DO UPDATE SET
                damage_dealt = guild_boss_participants.damage_dealt + %s
        ''', (boss_id, user_id, guild_id, damage, now, damage))
        
        # Отримуємо поточне здоров'я
        cursor.execute('SELECT health, max_health FROM guild_bosses WHERE id = %s', (boss_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        current_health = int(row[0])
        max_health = int(row[1])
        new_health = max(0, current_health - damage)
        
        # Оновлюємо здоров'я
        cursor.execute('UPDATE guild_bosses SET health = %s WHERE id = %s', (new_health, boss_id))
        
        # Перевіряємо чи переможений
        if new_health <= 0:
            cursor.execute('''
                UPDATE guild_bosses
                SET is_active = FALSE, defeat_date = %s, defeated_by_guild_id = %s,
                    defeat_count = COALESCE(defeat_count, 0) + 1
                WHERE id = %s
            ''', (now, guild_id, boss_id))
            conn.commit()
            return {'defeated': True, 'boss_id': boss_id}
        
        conn.commit()
        return {'defeated': False, 'remaining_health': new_health, 'max_health': max_health}
    except Exception as e:
        logger.error(f"❌ Помилка атаки боса гільдії: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_guild_boss_participants(boss_id):
    """Отримує учасників бою з босом"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT gbp.*, u.username
            FROM guild_boss_participants gbp
            LEFT JOIN user_languages u ON gbp.user_id = u.user_id
            WHERE gbp.boss_id = %s
            ORDER BY gbp.damage_dealt DESC
        ''', (boss_id,))
        
        rows = cursor.fetchall()
        participants = []
        for row in rows:
            participants.append({
                'id': int(row[0]),
                'boss_id': int(row[1]),
                'user_id': int(row[2]),
                'guild_id': int(row[3]),
                'damage_dealt': int(row[4]) if row[4] else 0,
                'joined_at': int(row[5]) if row[5] else 0,
                'username': row[6]
            })
        return participants
    except Exception as e:
        logger.error(f"❌ Помилка отримання учасників боса: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ГІЛЬДІЙНІ ВОЇНИ (СВИНАРІ) - НОВІ ФУНКЦІЇ
# ============================================

# Типи воїнів
WARRIOR_TYPES = {
    'regular': {'name': 'Свинар', 'cost': 100, 'power': 10, 'emoji': '🐷'},
    'matochnik': {'name': 'Свинар-Маточник', 'cost': 500, 'power': 60, 'emoji': '🐗'},
    'elite': {'name': 'Елітний Свинар', 'cost': 1000, 'power': 150, 'emoji': '⚔️'},
    'legendary': {'name': 'Легендарний Герой', 'cost': 5000, 'power': 1000, 'emoji': '👑'}
}


def buy_warrior(guild_id, warrior_type='regular', quantity=1):
    """Купує воїнів для гільдії"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        warrior_data = WARRIOR_TYPES.get(warrior_type, WARRIOR_TYPES['regular'])
        total_power = warrior_data['power'] * quantity
        
        # Перевіряємо чи вже є такі воїни
        cursor.execute('''
            SELECT id, quantity, power FROM guild_warriors
            WHERE guild_id = %s AND warrior_type = %s
        ''', (guild_id, warrior_type))
        row = cursor.fetchone()
        
        if row:
            # Оновлюємо кількість
            new_quantity = int(row[1]) + quantity
            new_power = int(row[2]) + (warrior_data['power'] * quantity)
            cursor.execute('''
                UPDATE guild_warriors SET quantity = %s, power = %s WHERE id = %s
            ''', (new_quantity, new_power, int(row[0])))
        else:
            # Додаємо нових воїнів
            cursor.execute('''
                INSERT INTO guild_warriors (guild_id, warrior_type, quantity, power, hired_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (guild_id, warrior_type, quantity, total_power, now))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка купівлі воїнів: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_guild_warriors(guild_id):
    """Отримує всіх воїнів гільдії"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM guild_warriors
            WHERE guild_id = %s
            ORDER BY power DESC
        ''', (guild_id,))
        rows = cursor.fetchall()
        
        warriors = []
        for row in rows:
            warriors.append({
                'id': int(row[0]),
                'guild_id': int(row[1]),
                'warrior_type': row[2],
                'quantity': int(row[3]) if row[3] else 0,
                'power': int(row[4]) if row[4] else 0,
                'hired_at': int(row[5]) if row[5] else 0
            })
        return warriors
    except Exception as e:
        logger.error(f"❌ Помилка отримання воїнів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_total_warrior_power(guild_id):
    """Отримує загальну силу воїнів гільдії"""
    warriors = get_guild_warriors(guild_id)
    total_power = sum(w['power'] for w in warriors)
    total_quantity = sum(w['quantity'] for w in warriors)
    return {'total_power': total_power, 'total_quantity': total_quantity, 'warriors': warriors}


def station_warriors(territory_id, guild_id, warrior_type, warrior_count):
    """Розміщує воїнів на захист території"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        warrior_data = WARRIOR_TYPES.get(warrior_type, WARRIOR_TYPES['regular'])
        defense_power = warrior_data['power'] * warrior_count
        
        # Перевіряємо чи вже є захист
        cursor.execute('''
            SELECT id, warrior_count, defense_power FROM territory_defense
            WHERE territory_id = %s AND guild_id = %s AND warrior_type = %s
        ''', (territory_id, guild_id, warrior_type))
        row = cursor.fetchone()
        
        if row:
            new_count = int(row[1]) + warrior_count
            new_power = int(row[2]) + defense_power
            cursor.execute('''
                UPDATE territory_defense SET warrior_count = %s, defense_power = %s WHERE id = %s
            ''', (new_count, new_power, int(row[0])))
        else:
            cursor.execute('''
                INSERT INTO territory_defense (territory_id, guild_id, warrior_type, warrior_count, defense_power, stationed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (territory_id, guild_id, warrior_type, warrior_count, defense_power, now))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка розміщення воїнів: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_territory_defense(territory_id):
    """Отримує захист території"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT td.*, g.name as guild_name
            FROM territory_defense td
            JOIN guilds g ON td.guild_id = g.id
            WHERE td.territory_id = %s
            ORDER BY td.defense_power DESC
        ''', (territory_id,))
        rows = cursor.fetchall()
        
        defense = []
        total_power = 0
        for row in rows:
            power = int(row[5]) if row[5] else 0
            total_power += power
            defense.append({
                'id': int(row[0]),
                'territory_id': int(row[1]),
                'guild_id': int(row[2]),
                'guild_name': row[3],
                'warrior_type': row[4],
                'warrior_count': int(row[5]) if row[5] else 0,
                'defense_power': power,
                'stationed_at': int(row[6]) if row[6] else 0
            })
        
        return {'defense': defense, 'total_power': total_power}
    except Exception as e:
        logger.error(f"❌ Помилка отримання захисту: {e}")
        return {'defense': [], 'total_power': 0}
    finally:
        cursor.close()
        conn.close()


def remove_warriors_from_guild(guild_id, warrior_type, quantity):
    """Видаляє воїнів з гільдії (після битви)"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, quantity FROM guild_warriors
            WHERE guild_id = %s AND warrior_type = %s
        ''', (guild_id, warrior_type))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        new_quantity = int(row[1]) - quantity
        if new_quantity <= 0:
            cursor.execute('DELETE FROM guild_warriors WHERE id = %s', (int(row[0]),))
        else:
            warrior_data = WARRIOR_TYPES.get(warrior_type, WARRIOR_TYPES['regular'])
            new_power = warrior_data['power'] * new_quantity
            cursor.execute('''
                UPDATE guild_warriors SET quantity = %s, power = %s WHERE id = %s
            ''', (new_quantity, new_power, int(row[0])))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка видалення воїнів: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def record_territory_battle(territory_id, attacker_guild_id, defender_guild_id, 
                            attacker_warriors, defender_warriors, 
                            attacker_loss, defender_loss, winner_guild_id):
    """Записує історію битви за територію"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO territory_battles (territory_id, attacker_guild_id, defender_guild_id,
                                          attacker_warriors, defender_warriors,
                                          attacker_loss, defender_loss, winner_guild_id, battle_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (territory_id, attacker_guild_id, defender_guild_id,
              attacker_warriors, defender_warriors,
              attacker_loss, defender_loss, winner_guild_id, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка запису битви: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ============================================
# ПРЕДМЕТИ З БОНУСАМИ - НОВІ ФУНКЦІЇ
# ============================================

# Рідкості предметів
ITEM_RARITIES = {
    'common': {'name': 'Звичайний', 'color': '⚪', 'bonus_mult': 1},
    'rare': {'name': 'Рідкісний', 'color': '🔵', 'bonus_mult': 2},
    'epic': {'name': 'Епічний', 'color': '🟣', 'bonus_mult': 3},
    'legendary': {'name': 'Легендарний', 'color': '🟡', 'bonus_mult': 5},
    'mythic': {'name': 'Міфічний', 'color': '🔴', 'bonus_mult': 10}
}

# Типи предметів
ITEM_TYPES = {
    'weapon': {'name': 'Зброя', 'bonus_type': 'power'},
    'armor': {'name': 'Броня', 'bonus_type': 'defense'},
    'accessory': {'name': 'Аксесуар', 'bonus_type': 'luck'},
    'consumable': {'name': 'Споживне', 'bonus_type': 'temporary'},
    'special': {'name': 'Особливе', 'bonus_type': 'special'}
}


def add_item_to_user(user_id, chat_id, item_type, item_name, rarity='common', 
                     bonus_type=None, bonus_value=0, quantity=1):
    """Додає предмет до інвентарю користувача"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO user_items (user_id, chat_id, item_type, item_name, rarity, 
                                   bonus_type, bonus_value, quantity, obtained_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, chat_id, item_type, item_name) DO UPDATE SET
                quantity = user_items.quantity + EXCLUDED.quantity,
                bonus_value = GREATEST(user_items.bonus_value, EXCLUDED.bonus_value)
        ''', (user_id, chat_id, item_type, item_name, rarity, bonus_type, bonus_value, quantity, now))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка додавання предмета: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_items(user_id, chat_id):
    """Отримує предмети користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM user_items
            WHERE user_id = %s AND chat_id = %s
            ORDER BY 
                CASE rarity 
                    WHEN 'mythic' THEN 1 
                    WHEN 'legendary' THEN 2 
                    WHEN 'epic' THEN 3 
                    WHEN 'rare' THEN 4 
                    ELSE 5 
                END,
                bonus_value DESC
        ''', (user_id, chat_id))
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'id': int(row[0]),
                'user_id': int(row[1]),
                'chat_id': int(row[2]),
                'item_type': row[3],
                'item_name': row[4],
                'rarity': row[5],
                'bonus_type': row[6],
                'bonus_value': int(row[7]) if row[7] else 0,
                'quantity': int(row[8]) if row[8] else 0,
                'obtained_at': int(row[9]) if row[9] else 0
            })
        return items
    except Exception as e:
        logger.error(f"❌ Помилка отримання предметів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_user_total_bonuses(user_id, chat_id):
    """Отримує загальні бонуси від всіх предметів користувача"""
    items = get_user_items(user_id, chat_id)
    
    bonuses = {
        'power': 0,
        'defense': 0,
        'luck': 0,
        'special': 0
    }
    
    for item in items:
        bonus_type = item.get('bonus_type')
        bonus_value = item.get('bonus_value', 0)
        quantity = item.get('quantity', 1)
        
        if bonus_type in bonuses:
            bonuses[bonus_type] += bonus_value * quantity
    
    return bonuses


def remove_user_item(user_id, chat_id, item_id, quantity=1):
    """Видаляє предмет у користувача"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT quantity FROM user_items WHERE id = %s AND user_id = %s AND chat_id = %s',
                      (item_id, user_id, chat_id))
        row = cursor.fetchone()
        
        if not row or row[0] < quantity:
            return False
        
        if quantity == row[0]:
            cursor.execute('DELETE FROM user_items WHERE id = %s', (item_id,))
        else:
            cursor.execute('UPDATE user_items SET quantity = quantity - %s WHERE id = %s', (quantity, item_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка видалення предмета: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ============================================
# ТРЕЙДИ ПРЕДМЕТАМИ - НОВІ ФУНКЦІЇ
# ============================================

def create_item_trade(sender_id, receiver_id, chat_id, 
                     sender_items=None, receiver_items=None,
                     sender_coins=0, receiver_coins=0):
    """Створює трейд між гравцями"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        import json
        sender_items_json = json.dumps(sender_items) if sender_items else '[]'
        receiver_items_json = json.dumps(receiver_items) if receiver_items else '[]'
        
        cursor.execute('''
            INSERT INTO item_trades (sender_id, receiver_id, chat_id,
                                    sender_items_json, receiver_items_json,
                                    sender_coins, receiver_coins, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (sender_id, receiver_id, chat_id, 
              sender_items_json, receiver_items_json,
              sender_coins, receiver_coins, now))
        
        trade_id = cursor.fetchone()[0]
        conn.commit()
        return trade_id
    except Exception as e:
        logger.error(f"❌ Помилка створення трейду: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_item_trade(trade_id):
    """Отримує інформацію про трейд"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        import json
        cursor.execute('SELECT * FROM item_trades WHERE id = %s', (trade_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'id': int(row[0]),
            'sender_id': int(row[1]),
            'receiver_id': int(row[2]),
            'chat_id': int(row[3]),
            'sender_items': json.loads(row[4]) if row[4] else [],
            'receiver_items': json.loads(row[5]) if row[5] else [],
            'sender_coins': int(row[6]) if row[6] else 0,
            'receiver_coins': int(row[7]) if row[7] else 0,
            'status': row[8],
            'created_at': int(row[9]) if row[9] else 0,
            'completed_at': int(row[10]) if row[10] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання трейду: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def accept_item_trade(trade_id):
    """Приймає трейд"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            UPDATE item_trades SET status = 'accepted', completed_at = %s
            WHERE id = %s
        ''', (now, trade_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка прийняття трейду: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def cancel_item_trade(trade_id):
    """Скасовує трейд"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE item_trades SET status = 'cancelled'
            WHERE id = %s
        ''', (trade_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка скасування трейду: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_pending_trades(user_id):
    """Отримує активні трейди користувача"""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM item_trades
            WHERE (sender_id = %s OR receiver_id = %s) AND status = 'pending'
            ORDER BY created_at DESC
        ''', (user_id, user_id))
        rows = cursor.fetchall()
        
        trades = []
        for row in rows:
            trades.append({
                'id': int(row[0]),
                'sender_id': int(row[1]),
                'receiver_id': int(row[2]),
                'chat_id': int(row[3]),
                'status': row[8],
                'created_at': int(row[9]) if row[9] else 0
            })
        return trades
    except Exception as e:
        logger.error(f"❌ Помилка отримання трейдів: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ============================================
# ПРИВАТНІ КАЗИНО - НОВІ ФУНКЦІЇ
# ============================================

def create_casino(owner_user_id, chat_id, name, initial_coins=1000):
    """Створює приватне казино"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        now = int(time.time())
        cursor.execute('''
            INSERT INTO private_casinos (owner_user_id, chat_id, name, casino_coins, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (owner_user_id, chat_id, name, initial_coins, now))
        
        casino_id = cursor.fetchone()[0]
        conn.commit()
        return casino_id
    except Exception as e:
        logger.error(f"❌ Помилка створення казино: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_casino(casino_id):
    """Отримує інформацію про казино"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM private_casinos WHERE id = %s', (casino_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'id': int(row[0]),
            'owner_user_id': int(row[1]),
            'chat_id': int(row[2]),
            'name': row[3],
            'casino_coins': int(row[4]) if row[4] else 0,
            'min_bet': int(row[5]) if row[5] else 10,
            'max_bet': int(row[6]) if row[6] else 1000,
            'win_chance': float(row[7]) if row[7] else 0.3,
            'created_at': int(row[8]) if row[8] else 0,
            'is_active': bool(row[9])
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання казино: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_casino(user_id, chat_id):
    """Отримує казино користувача"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM private_casinos
            WHERE owner_user_id = %s AND chat_id = %s
            ORDER BY id DESC LIMIT 1
        ''', (user_id, chat_id))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'id': int(row[0]),
            'owner_user_id': int(row[1]),
            'chat_id': int(row[2]),
            'name': row[3],
            'casino_coins': int(row[4]) if row[4] else 0,
            'min_bet': int(row[5]) if row[5] else 10,
            'max_bet': int(row[6]) if row[6] else 1000,
            'win_chance': float(row[7]) if row[7] else 0.3,
            'created_at': int(row[8]) if row[8] else 0,
            'is_active': bool(row[9])
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання казино: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def deposit_to_casino(casino_id, amount):
    """Вносить монети до казино"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE private_casinos SET casino_coins = casino_coins + %s
            WHERE id = %s
        ''', (amount, casino_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка внесення до казино: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def withdraw_from_casino(casino_id, amount):
    """Виводить монети з казино"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT casino_coins FROM private_casinos WHERE id = %s', (casino_id,))
        row = cursor.fetchone()
        
        if not row or row[0] < amount:
            return False
        
        cursor.execute('''
            UPDATE private_casinos SET casino_coins = casino_coins - %s
            WHERE id = %s
        ''', (amount, casino_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка виводу з казино: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def set_casino_limits(casino_id, min_bet=None, max_bet=None, win_chance=None):
    """Встановлює обмеження казино"""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        updates = []
        values = []
        
        if min_bet is not None:
            updates.append('min_bet = %s')
            values.append(min_bet)
        
        if max_bet is not None:
            updates.append('max_bet = %s')
            values.append(max_bet)
        
        if win_chance is not None:
            updates.append('win_chance = %s')
            values.append(win_chance)
        
        if not updates:
            return False
        
        values.append(casino_id)
        cursor.execute(f'''
            UPDATE private_casinos SET {', '.join(updates)}
            WHERE id = %s
        ''', values)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Помилка встановлення обмежень: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def play_casino_game(casino_id, player_user_id, bet_amount):
    """
    Гра в казино
    Повертає: {'win': bool, 'amount': int, 'result': str, 'actual_chance': float}
    
    МЕХАНІКА:
    - Власник казино отримує прибуток завдяки математиці
    - Гравці бачать чесні результати
    - Шанс виграшу трохи нижчий за заявлений (це нормально для казино)
    """
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Отримуємо казино
        cursor.execute('''
            SELECT win_chance, casino_coins FROM private_casinos WHERE id = %s
        ''', (casino_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        win_chance = float(row[0]) if row[0] else 0.3
        casino_coins = int(row[1]) if row[1] else 0
        
        # Перевірка чи вистачає монет в казино
        if casino_coins < bet_amount * 2:
            return {'win': False, 'amount': 0, 'result': 'Недостатньо монет в казино', 'actual_chance': win_chance}
        
        # Визначаємо результат
        # Реальний шанс = заявлений шанс * 0.85 (15% перевага казино)
        # Це стандартна практика для всіх казино світу
        actual_win_chance = win_chance * 0.85
        is_win = random.random() < actual_win_chance
        
        # Генеруємо результат гри
        if is_win:
            win_amount = bet_amount * 2
            # Випадкове виграшне число
            result_num = random.randint(7, 77)
            result = f"Випало {result_num} - ВИГРАШ!"
        else:
            win_amount = 0
            # Випадкове число для програшу
            result_num = random.randint(1, 76)
            # 30% шанс на "майже виграш" для залучення
            if random.random() < 0.3 and result_num > 70:
                result = f"Випало {result_num} - МАЙЖЕ! Спробуй ще!"
            else:
                result = f"Випало {result_num} - ПРОГРАШ"
        
        # Оновлюємо баланс казино
        if is_win:
            cursor.execute('''
                UPDATE private_casinos SET casino_coins = casino_coins - %s WHERE id = %s
            ''', (win_amount, casino_id))
        else:
            cursor.execute('''
                UPDATE private_casinos SET casino_coins = casino_coins + %s WHERE id = %s
            ''', (bet_amount, casino_id))
        
        # Записуємо гру в історію
        now = int(time.time())
        cursor.execute('''
            INSERT INTO casino_games (casino_id, player_user_id, bet_amount, win_amount, is_win, game_result, played_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (casino_id, player_user_id, bet_amount, win_amount, is_win, result, now))
        
        conn.commit()
        
        return {
            'win': is_win,
            'amount': win_amount,
            'result': result,
            'actual_chance': actual_win_chance
        }
    except Exception as e:
        logger.error(f"❌ Помилка гри в казино: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_casino_stats(casino_id):
    """Отримує статистику казино"""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Загальна статистика
        cursor.execute('''
            SELECT 
                COUNT(*) as total_games,
                COALESCE(SUM(bet_amount), 0) as total_bets,
                COALESCE(SUM(CASE WHEN is_win THEN win_amount ELSE 0 END), 0) as total_wins,
                COALESCE(SUM(CASE WHEN is_win THEN 1 ELSE 0 END), 0) as wins_count
            FROM casino_games
            WHERE casino_id = %s
        ''', (casino_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'total_games': int(row[0]) if row[0] else 0,
            'total_bets': int(row[1]) if row[1] else 0,
            'total_wins': int(row[2]) if row[2] else 0,
            'wins_count': int(row[3]) if row[3] else 0
        }
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

