# Fix for "column u.username does not exist" Error

## Problem
The `/guild_items` command was failing with error:
```
❌ Помилка: column u.username does not exist
LINE 2: SELECT gi.*, u.username as donor_name
```

The query was trying to JOIN `guild_items` with `user_languages` table and select `username`, but the `user_languages` table didn't have a `username` column.

## Solution

### 1. Database Schema Changes
**File: `db.py`** (line ~778)
- Added `username TEXT` column to the `user_languages` table creation
- Added migration code to add the column to existing tables:
  ```python
  cursor.execute('ALTER TABLE user_languages ADD COLUMN IF NOT EXISTS username TEXT')
  ```

### 2. New Database Function
**File: `db.py`** (line ~4465)
- Added `update_user_username(user_id, username)` function to update user's username in the database

### 3. Updated Functions
**File: `db.py`**:
- `set_user_language(user_id, language, username=None)` - now accepts username parameter
- `donate_to_chest(guild_id, user_id, item_type, item_name, quantity=1, username=None)` - now updates username when donating
- `get_guild_chest(guild_id)` - fixed column indices in result processing

**File: `bot.py`**:
- `guild_items_cmd(message)` - now updates user's username before querying
- `guild_donate_cmd(message)` - now passes username to `donate_to_chest()`

### 4. Migration Script
**File: `migrations/add_username_to_user_languages.sql`**
- SQL script to add username column to existing databases
- Can be run manually on production databases

## Testing
After deploying these changes:
1. The bot will automatically add the `username` column on startup
2. Users' usernames will be updated when they use `/guild_items` or `/guild_donate`
3. The `/guild_items` command will now show donor names instead of just IDs

## Files Changed
- `db.py` - Database schema and functions
- `bot.py` - Command handlers
- `migrations/add_username_to_user_languages.sql` - Migration script (new file)
