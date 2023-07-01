from sqlalchemy import Column, BigInteger, Boolean, DateTime, Integer, ARRAY, Text, MetaData
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class ActionLog(Base):
    __tablename__ = 't_actionlog'

    guild_id = Column(BigInteger, primary_key=True)
    member_id = Column(BigInteger, primary_key=True)
    action_type = Column(Integer)
    action_taken_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"Guild(id={self.guild_id!r}, member_id={self.member_id!r}, action_type={self.action_type!r}, action_taken_at={self.action_taken_at!r})"

class User(Base):
    __tablename__ = 't_users'

    guild_id = Column(BigInteger, primary_key=True)
    member_id = Column(BigInteger, primary_key=True)
    member_created_at = Column(DateTime)
    member_joined_at = Column(DateTime)
    member_left_at = Column(DateTime)
    is_whitelisted = Column(Boolean, default=False)

class Guild(Base):
    __tablename__ = 't_guilds'

    guild_id = Column(BigInteger, primary_key=True)
    guild_autoban = Column(Boolean, default=False)
    guild_interval = Column(Integer, default=30)
    guild_hours = Column(Integer, default=6)
    guild_min_members = Column(Integer, default=2)
    guild_notification_channel = Column(BigInteger)
    guild_bot_present = Column(Boolean)
    guild_url_filter = Column(Boolean)

class Log(Base):
    __tablename__ = 't_logs'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    raid_time = Column(DateTime)
    raiders_id = Column(ARRAY(BigInteger))

class Report(Base):
    __tablename__ = 't_reports'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    search_initiated_by_id = Column(BigInteger)
    search_initiated_by_name = Column(Text)
    search_initiated_at = Column(DateTime)
    search_from = Column(DateTime)
    search_until = Column(DateTime)
    found_ids = Column(ARRAY(BigInteger))

"""Wowhead exclusive table"""

class Article(Base):
    __tablename__ = 't_articles'

    article_url = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)
    total_comments = Column(Integer, nullable=False)
    last_checked = Column(DateTime, nullable=False)
