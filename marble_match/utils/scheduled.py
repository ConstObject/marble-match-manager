from datetime import datetime
import configparser
import logging
import sqlite3
from sqlite3 import Error

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from database import database_operation

stats_queries = {
    "most_marbles": "SELECT users.id, users.marbles FROM users "
                    "WHERE users.server_id == ? "
                    "ORDER BY users.marbles DESC",

    "total_marbles": "SELECT SUM(users.marbles) FROM users "
                     "WHERE users.server_id == ? "
                     "GROUP BY users.server_id"
}

scheduler = AsyncIOScheduler()
logger = logging.getLogger(f'marble_match.{__name__}')


def is_stat_tracked(server: int, stat: str) -> bool:
    logger.debug(f'is_stat_tracked: {server}, {stat}')

    # Setup config parser and get sections
    config = configparser.ConfigParser()
    config.read('marble_bot.ini')
    sections = config.sections()
    server_string = str(server)

    for servers in sections:
        if servers == server_string:
            # Get stats tracked for server, then split into a list to process
            tracked_stats = config[servers]['tracked_stats']
            # Check if stat is in tracked stats
            if stat in tracked_stats:
                return True

    return False


def create_table_by_stat(connection, stat):
    logger.debug(f'create_tables_by_stat: {connection}')
    query = f'CREATE TABLE IF NOT EXISTS {stat}(' \
            f'id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, ' \
            f'server_id INTEGER NOT NULL, ' \
            f'date timestamp, ' \
            f'data TEXT NOT NULL)'
    try:
        cur = connection.cursor()
        logger.debug(f'Created cursor: {cur}')

        cur.execute(query)

        connection.commit()
        logger.debug(f'query: {query}')
    except Error as e:
        logger.error(f'Failed to create tables: {e}')
        raise e


def create_entry(connection, stat, entry_data):
    logger.debug(f'create_entry')

    query = f"INSERT INTO {stat} VALUES ( ?, ?, ?, ? )"

    # Making table if it doesn't exist
    create_table_by_stat(connection, stat)

    try:
        cur = connection.cursor()
        logger.debug(f'Created cursor: {cur}')
        cur.execute(query, entry_data)
        connection.commit()

        logger.debug(database_operation.replace_char_list(query, entry_data))
        logger.debug(f'lastrowid: {cur.lastrowid}')

    except Error as e:
        logger.error(f'Failed to create entry: {e}')
        raise e


@scheduler.scheduled_job(CronTrigger(hour=5))
def daily_task():
    config = configparser.ConfigParser()
    config.read('marble_bot.ini')
    sections = config.sections()

    db = sqlite3.connect(config['DEFAULT']['database'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    # For server in marble_bot.ini
    for server in sections:
        # Get stats tracked for server, then split into a list to process
        stats = config[server]['tracked_stats']
        # Skip if empty
        if not stats:
            continue
        stats = stats.split(',')

        for stat in stats:
            if stat in stats_queries:
                query_results = database_operation.raw_query(db, stats_queries[stat], [int(server)])
                # Skip if query_results are empty
                if not query_results:
                    continue

                if stat == 'most_marbles':
                    # TODO Append users who are tied in the data
                    # Create table if it doesn't exist
                    create_table_by_stat(db, 'most_marbles')
                    # Get first index, highest marble count result
                    # query_results format [ (player_id, marble_count), ... ]
                    highest_user = query_results[0]
                    # Insert stat entry into database
                    create_entry(db, 'most_marbles', [None, int(server), datetime.utcnow(),
                                                      f'{highest_user[0]},{highest_user[1]}'])
                elif stat == 'total_marbles':
                    # Create database table
                    create_table_by_stat(db, 'total_marbles')
                    # Get first index, total marble results
                    # query_results format [ (total_marbles) ]
                    marble_sum = query_results[0][0]
                    # Insert stat entry into database
                    create_entry(db, 'total_marbles', [None, int(server), datetime.utcnow(), str(marble_sum)])

    db.close()
    print(f'daily_task: {datetime.utcnow()}')


# TODO Switch over to CronTrigger, when done testing
"""
@scheduler.scheduled_job(IntervalTrigger(seconds=10))
def task_todo():
    config = configparser.ConfigParser()
    config.read('marble_bot.ini')
    sections = config.sections()

    db = sqlite3.connect(config['DEFAULT']['database'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    # For server in marble_bot.ini
    for server in sections:
        # Get stats tracked for server, then split into a list to process
        stats = config[server]['tracked_stats']
        # Skip if empty
        if not stats:
            continue
        stats = stats.split(',')

        for stat in stats:
            if stat in stats_queries:
                query_results = database_operation.raw_query(db, stats_queries[stat], [int(server)])
                # Skip if query_results are empty
                if not query_results:
                    continue

                if stat == 'most_marbles':
                    # TODO Append users who are tied in the data
                    # Create table if it doesn't exist
                    create_table_by_stat(db, 'most_marbles')
                    # Get first index, highest marble count result
                    # query_results format [ (player_id, marble_count), ... ]
                    highest_user = query_results[0]
                    # Insert stat entry into database
                    create_entry(db, 'most_marbles', [None, int(server), datetime.utcnow(),
                                                      f'{highest_user[0]},{highest_user[1]}'])
                elif stat == 'total_marbles':
                    # Create database table
                    create_table_by_stat(db, 'total_marbles')
                    # Get first index, total marble results
                    # query_results format [ (total_marbles) ]
                    marble_sum = query_results[0][0]
                    # Insert stat entry into database
                    create_entry(db, 'total_marbles', [None, int(server), datetime.utcnow(), str(marble_sum)])

    db.close()
    print(f'task_todo: {datetime.utcnow()}')
"""


def start_scheduler():
    scheduler.start()
