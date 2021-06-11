import logging
import sqlite3
from datetime import datetime
from configparser import ConfigParser

from database import database_operation

logger = logging.getLogger(f'marble_match.{__name__}')


def is_season_active(server: int) -> bool:
    logger.debug(f'is_season_active: {server}')

    # Get config
    config = ConfigParser()
    config.read('marble_bot.ini')
    is_active = config[str(server)]['season_active']
    logger.debug(f'is_active: {is_active}')

    # if is numeric return else 0
    return bool(int(is_active)) if is_active.isnumeric() else 0


def current_season(server: int) -> int:
    logger.debug(f'current_season" {server}')

    # Get config
    config = ConfigParser()
    config.read('marble_bot.ini')
    season = config[str(server)]['season']
    logger.debug(f'season: {season}')

    # if numeric return else 0
    return int(season) if season.isnumeric() else 0


def create_season_entry(connection: sqlite3.Connection, server: int, player_id: int, marble_change: int, match_id: int,
                        change_time: datetime = datetime.utcnow()):
    logger.debug(f'create_season_entry: {server}, {player_id}, {marble_change}, {match_id}, {change_time}')

    # Get current season, exit if unable to get or 0
    cur_season = current_season(server)
    if not cur_season:
        logger.debug(f'Unable to get current season')
        return

    query = "INSERT INTO seasons VALUES (?, ?, ?, ?, ?, ?, ?)"
    query_param = [None, server, cur_season, player_id, marble_change, match_id, change_time]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(database_operation.replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return cur.lastrowid
    except sqlite3.Error as e:
        logger.error(f'There was an error inserting a entry into seasons: {e}')
        return
