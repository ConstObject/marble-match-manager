import sqlite3
import logging

from sqlite3 import Error

db_connection = None

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('database.log')
formatter = logging.Formatter('%(asctime)s : %(module)s : %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def create_connection(db_file):
    logger.debug(f'create_connection: {db_file}')
    try:
        con = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        logger.debug(f'connection created: {con}')
        return con
    except Error as e:
        logger.error(f'Failed to create connection: {e}')
        raise e


def create_tables(connection):
    logger.debug(f'create_tables: {connection}')
    try:
        cur = connection.cursor()
        logger.debug(f'Created cursor: {cur}')
        cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "username TEXT NOT NULL, marbles INTEGER NOT NULL, server_id INTEGER NOT NULL, "
                    "wins INTEGER NOT NULL, loses INTEGER NOT NULL)")

        cur.execute("CREATE TABLE IF NOT EXISTS matches(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "amount INTEGER NOT NULL, active INTEGER NOT NULL, participant1 INTEGER NOT NULL, "
                    "participant2 INTEGER NOT NULL, accepted INTEGER NOT NULL, FOREIGN KEY(participant1) "
                    "REFERENCES users(id), FOREIGN KEY(participant2) REFERENCES users(id))")

        cur.execute("CREATE TABLE IF NOT EXISTS matches_history(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "amount INTEGER NOT NULL, participant1 INTEGER NOT NULL, "
                    "participant2 INTEGER NOT NULL, winner_id INTEGER NOT NULL, match_time timestamp, "
                    "FOREIGN KEY(participant1) REFERENCES users(id), "
                    "FOREIGN KEY(participant2) REFERENCES users(id), "
                    "FOREIGN KEY(winner_id) REFERENCES users(id))")

        cur.execute("CREATE TABLE IF NOT EXISTS bets(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "amount INTEGER NOT NULL, match_id INTEGER NOT NULL, better_id INTEGER NOT NULL, "
                    "participant1 INTEGER NOT NULL, FOREIGN KEY(match_id) REFERENCES matches(id), "
                    "FOREIGN KEY(better_id) REFERENCES users(id) FOREIGN KEY(participant1) REFERENCES users(id))")

        cur.execute("CREATE TABLE IF NOT EXISTS bets_history(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "amount INTEGER NOT NULL, match_id INTEGER NOT NULL, better_id INTEGER NOT NULL, "
                    "participant1 INTEGER NOT NULL, winner_id INTEGER NOT NULL, bet_time timestamp, "
                    "FOREIGN KEY(match_id) REFERENCES matches_history(id), FOREIGN KEY(better_id) REFERENCES users(id),"
                    " FOREIGN KEY(participant1) REFERENCES users(id), "
                    "FOREIGN KEY(winner_id) REFERENCES users(id))")
        connection.commit()
    except Error as e:
        logger.error(f'Failed to create tables: {e}')
        raise e
