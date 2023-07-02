#!/bin/bash

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
CREATE DATABASE sentinel;
\c sentinel
CREATE ROLE sentinel WITH PASSWORD 'password';
ALTER ROLE sentinel WITH LOGIN;
GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel;

CREATE TABLE IF NOT EXISTS t_actionlog (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    action_type INTEGER,
    action_taken_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE t_actionlog OWNER TO sentinel;

CREATE TABLE IF NOT EXISTS t_guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_autoban BOOLEAN,
    guild_interval INTEGER,
    guild_hours INTEGER,
    guild_min_members INTEGER,
    guild_notification_channel BIGINT,
    guild_bot_present BOOLEAN,
    guild_url_filter BOOLEAN
 );

ALTER TABLE t_guilds OWNER TO sentinel;

CREATE TABLE IF NOT EXISTS t_logs (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT,
    raid_time TIMESTAMP WITH TIME ZONE,
    raiders_id BIGINT[]
);

ALTER TABLE t_logs OWNER TO sentinel;

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

ALTER TABLE t_reports OWNER TO sentinel;

CREATE TABLE IF NOT EXISTS t_users (
    guild_id BIGINT,
    member_id BIGINT,
    member_created_at TIMESTAMP WITH TIME ZONE,
    member_joined_at TIMESTAMP WITH TIME ZONE,
    member_left_at TIMESTAMP WITH TIME ZONE,
    is_whitelisted BOOLEAN,
    PRIMARY KEY (guild_id, member_id)
);

ALTER TABLE t_users OWNER TO sentinel;
EOSQL