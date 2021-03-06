# banbot
Automatically sync bans between [matrix](https://matrix.org/) rooms

## Installing dependencies
Install [poetry](https://python-poetry.org/docs/#installation), then `git clone` this repository.
Then run `poetry install` to install the dependencies listed in the `pyproject.toml` file.

## Configuring
Create a `.env` file with the following content:
```
# Homeserver that the bot logs into
HOMESERVER=https://matrix.example.org
# Full user identifier of the bot's account
BOT_USER=@bot:example.org
# Password for the bot's account
BOT_PASSWORD=SecUre_p@ssw0rd123123

# Full user identifier of the bot's owner
BOT_OWNER=@owner:example.org
```
The bot's owner is the only account that is allowed to invite the bot to rooms or issue the linking commands

## Running
`poetry run python src/main.py` to launch the bot.

## Linking rooms
To manage links between rooms, the bot owner can use the following commands:
Create a link to another room
```
!ban-sync link #example-room:example.com
```
Remove all links that the room is part of
```
!ban-sync unlink
```
