-- Migration: Add username column to user_languages table
-- Date: 2026-03-18
-- Description: Fix for "column u.username does not exist" error in guild_items command

-- Add username column to user_languages if it doesn't exist
ALTER TABLE user_languages ADD COLUMN IF NOT EXISTS username TEXT;

-- Update existing records with usernames from other tables (optional)
-- This will populate username for users who have guild membership
UPDATE user_languages ul
SET username = gm.username
FROM guild_members gm
WHERE ul.user_id = gm.user_id AND gm.username IS NOT NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_languages_username ON user_languages(username);

-- Verify the changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_languages' 
ORDER BY ordinal_position;
