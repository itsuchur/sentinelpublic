CREATE ROLE sentinel WITH LOGIN PASSWORD 'password';
CREATE DATABASE sentinel OWNER sentinel;
USE sentinel;

CREATE TABLE IF NOT EXISTS t_actionlog (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    action_type INTEGER,
    action_taken_at TIMESTAMP WITH TIME ZONE
    );

CREATE TABLE IF NOT EXISTS t_guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_autoban BOOLEAN FALSE,
    guild_interval INTEGER,
    guild_hours INTEGER,
    guild_min_members INTEGER,
    guild_notification_channel BIGINT,
    guild_bot_present BOOLEAN,
    guild_url_filter BOOLEAN
    );

CREATE TABLE IF NOT EXISTS t_logs (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT,
    raid_time TIMESTAMP WITH TIME ZONE,
    raiders_id BIGINT[]
    );

CREATE TABLE IF NOT EXISTS t_reports (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT,
    search_initiated_by_id BIGINT,
    search_initiated_by_name TEXT,
    search_initiated_at TIMESTAMP WITH TIME ZONE,
    search_from TIMESTAMP WITH TIME ZONE,
    search_until TIMESTAMP WITH TIME ZONE,
    found_ids BIGINT[]
    );

CREATE TABLE IF NOT EXISTS t_users (
    guild_id BIGINT,
    member_id BIGINT,
    member_created_at TIMESTAMP WITH TIME ZONE,
    member_joined_at TIMESTAMP WITH TIME ZONE,
    member_left_at TIMESTAMP WITH TIME ZONE,
    is_whitelisted BOOLEAN,
    PRIMARY KEY (guild_id, member_id)
    );