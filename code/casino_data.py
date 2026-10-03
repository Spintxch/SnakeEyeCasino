import json
import os
from pathlib import Path

SAVE_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Snake Eye Casino"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SAVE_FILE = SAVE_DIR / "players.json"


def load_players():
    if not SAVE_FILE.exists():
        return {}

    with SAVE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_players(players):
    with SAVE_FILE.open("w", encoding="utf-8") as file:
        json.dump(players, file, indent=4)


def new_player():
    return {
        "chips": 100,
        "loans_taken": 0,
        "loans": [],
        "temp_powerups": [],
        "perma_powerups": [],
    }

SINGLE_PLAYER_KEY = "_single_player"


def load_single_player():
    players = load_players()
    player = players.get(SINGLE_PLAYER_KEY)

    if player is None:
        player = new_player()
        players[SINGLE_PLAYER_KEY] = player
        save_players(players)

    return player


def save_single_player(player):
    players = load_players()
    players[SINGLE_PLAYER_KEY] = player
    save_players(players)