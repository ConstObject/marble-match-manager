import logging
from configparser import ConfigParser

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
