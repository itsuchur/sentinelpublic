# Sentinel - Anti-Selfbot Bot for Discord

Sentinel is a Discord bot that helps protect servers from userbot raids. It tracks accounts that mass-join the server within a short time span and automatically bans them if auto-ban mode is enabled on the server.

The bot is highly customizable allowing server managers to tailor bot's security measures to their own liking and needs.

*8New in 7.0: the logs of userbot raids are now published on the Internet on the temporary domain https://logs.
itsuchur.dev/id=1. Frontend is handled by Flask and Gunicorn (outside of scope of this repository).

Much of the bot relies on using both PostgresSQL and Redis instead of keeping data in memory. This is intentional-- in the future the bot would get an admin dashboard to make management even easier.

This bot is available to all Discord users-- feel free to add it to your server by pressing this link https://discord.com/api/oauth2/authorize?client_id=574802604186402819&permissions=51220&scope=applications.commands%20bot

## Requirements

To use the Sentinel Bot, you will need the following:

- Python 3.8 or higher
- PostgresSQL
- Redis

## Installation

To install Sentinel, follow these steps:

**Note**: for Docker installation refer to [DOCKER-INSTALLATION.md](https://github.com/itsuchur/sentinelpublic/DOCKER-INSTALLATION.md).

1. **Clone this repository to your local machine.**

By entering the following command into your console.

```git clone https://github.com/itsuchur/sentinelpublic```

2. **Initialize a virtual environment** 

Use the following command to initialize venv.

```python -m venv sentinelpublic/venv```

3. **Activate the venv**

Use the following commmand to activate venv.

```source sentinelpublic/venv/bin/activate```

(for Windows users)

```venv\Scripts\activate```

4. **Install the dependencies**

Install the required dependencies running the following command:

```pip install -r requirements.txt```

5. **Set up a PostgresSQL database and Redis**

Set up a PostgresSQL server for the bot.

Set up a Redis server for the bot. You can download Redis from the official website: https://redis.io/download.

6. **Run migration SQL file**

Run V1_initial_migration.sql file to initialize required SQL tables.

7. **Create configuration file**.

Create a config.py file with the following content:

```python
client_id   = "" # your bot client ID. You can find the ID at https://discord.com/developers/applications
token = "" # your bot token. You can find the token at https://discord.com/developers/applications
postgresql = "postgresql://sentinel:password@127.0.0.1/sentinel" # postgresql connection string
postgresql_sqlalchemy = "postgresql+asyncpg://sentinel:password@127.0.0.1/sentinel"
redis = "redis://127.0.0.1?password=RedisPassword&encoding=utf-8&decode_responses=True" # Redis connection string
```

Don't forget to edit the credentials.

8. **Start the bot by running the following command:**

```python launcher.py```

## Usage

Once the bot is running, you can use the following commands:

Please note autoban mode is disabled by default (it means you have to explicitly enable the mode after inviting the 
bot).

```/autoban on or /autoban off: switch to auto-ban mode. In this mode, the bot automatically bans suspicious accounts relying on default parameters or parameters set by the server owner and members with Ban Members permissions.```

```/setinterval <minutes>: change the default time interval (30 minutes). The time interval is used to form a list of accounts which joined the server within the given time interval and who met all other criteria.```

```/sethours <hours>: change the default hours (6 hours). These hours are a search parameter that allows the bot to search for accounts that were created between the given hour (onwards and backwards).```

```/setthreshold <number>: set the minimum number of recently joined members that trigger the antiraid mechanism.```

```/setchannel <channel_id>: change the channel where the bot will send ban notifications.```

## TODO

Complete transition from asyncpg to SQLAlchemy.

Calculate accounts' age in memory rather than relying on PostgresSQL.

Complete V1_initial_migration.sql file.

## Contributing

If you want to contribute to this project, feel free to submit a pull request or open an issue.