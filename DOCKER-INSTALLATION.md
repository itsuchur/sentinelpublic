If you prefer to use Docker to deploy the bot, follow the steps outlined below.

1. **Clone the repository to your local machine.**

By entering the following command into your console.

``git clone https://github.com/itsuchur/sentinelpublic``

2. **Open the cloned directory and create .env file with the following content:**

```python
POSTGRES_PASSWORD=PostgresPassword
REDIS_PASSWORD=RedisPassword
```

3. **Edit or create config.py Python file with the following content:**

```python
client_id   = "" # your bot client ID
token = "" # your bot token
postgresql_docker = "postgresql://sentinel:password@host.docker.internal/sentinel"
postgresql_sqlalchemy_docker = 'postgresql+asyncpg://sentinel:password@host.docker.internal/sentinel'
redis_docker = "redis://host.docker.internal?password=RedisPassword&encoding=utf-8&decode_responses=True"
```
**Note**: this .md assumes you didn't change password for user sentinel in sql_init.sh and also didn't change Redis 
password in *.env file.

Feel free to edit credentials, but **you must not** change `host.docker.internal` part of the connection strings.

4. **Edit db.py and memorycache.py files**

Open both `cogs/utils/db.py` and `cogs/utils/memorycache.py` and follow instructions outlined in these files to 
ensure the bot will be able to connect to PostgresSQL and Redis.

5. **Build Docker image**

Open the directory in your console
``cd sentinelpublic``

Build the image
``docker build -t sentinelpublic .``

6. Launch the bot.

This command will launch the bot as well as download required services.

``docker compose up -d``

