import sqlite3
import datetime
import logging

from sqlite3 import Error

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('db_op.log')
formatter = logging.Formatter('%(asctime)s : %(module)s : %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def replace_char_list(_old: str, _replacement: list,  _replace: str = '?') -> str:

    for i in _replacement:
        _old = _old.replace(_replace, str(i), 1)

    return _old


def create_user(connection: sqlite3.Connection, player_id: int, username: str, marbles: int, server_id: int,
                wins: int = 0, loses: int = 0) -> int:

    logger.debug(f'create_user: {player_id}, {username}, {marbles}, {server_id}, {wins}, {loses}')

    query = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)"
    query_param = [player_id, username, marbles, server_id, wins, loses]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return cur.lastrowid
    except Error as e:
        logger.error(f'There was an error inserting a user into users: {e}')
        return 0


def create_match(connection: sqlite3.Connection, match_id: int, amount: int, active: int,
                 participant1: int, participant2: int) -> int:

    logger.debug(f'create_match: {match_id}, {amount}, {active}, {participant1}, {participant2}')

    query = "INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)"
    query_param = [match_id, amount, active, participant1, participant2, 0]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return cur.lastrowid
    except Error as e:
        logger.error(f'There was an error inserting a match into matches: {e}')
        return 0


def create_bet(connection: sqlite3.Connection, bet_id: int, amount: int, match_id: int, better_id: int,
               participant1: int) -> int:

    logger.debug(f'create_bet: {bet_id}, {amount}, {match_id}, {better_id}, {participant1}')

    query = "INSERT INTO bets VALUES (?, ?, ?, ?, ?)"
    query_param = [bet_id, amount, match_id, better_id, participant1]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        subtract_marbles(connection, better_id, amount)

        logger.debug(f'subtract_marbles called')

        return cur.lastrowid
    except Error as e:
        logger.error(f'There was an error inserting a bet into bets: {e}')
        return 0


def create_match_history(connection: sqlite3.Connection, match_id: int, amount: int,
                         participant1: int, participant2: int, winner_id: int,
                         time: datetime.datetime = datetime.datetime.utcnow()) -> int:

    logger.debug(f'create_match_history: {match_id}, {amount}, {participant1}, {participant2}, {winner_id}, {time}')

    query = "INSERT INTO matches_history VALUES (?, ?, ?, ?, ?, ?)"
    query_param = [match_id, amount, participant1, participant2, winner_id, time]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return cur.lastrowid
    except Error as e:
        logger.error(f'There was an error inserting a match into match_history: {e}')
        return 0


def create_bet_history(connection: sqlite3.Connection, bet_id: int, amount: int, match_id: int, better_id: int,
                       participant1: int, winner_id: int, time: datetime.datetime = datetime.datetime.utcnow()) -> int:

    logger.debug(f'create_bet_history: '
                 f'{bet_id}, {amount}, {match_id}, {better_id}, {participant1}, {winner_id}, {time}')

    query = "INSERT INTO bets_history VALUES (?, ?, ?, ?, ?, ?, ?)"
    query_param = [bet_id, amount, match_id, better_id, participant1, winner_id, time]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return cur.lastrowid
    except Error as e:
        logger.error(f'There was an error inserting a bet into bet_history: {e}')
        return 0


def update_match_activity(connection: sqlite3.Connection, match_id: int, active: int = 1) -> bool:

    logger.debug(f'update_match_activity: {match_id}, {active}')

    query = "UPDATE matches SET active = ? WHERE id = ?"
    query_param = [active, match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating activity in matches: {e}')
        return False


def update_match_accepted(connection: sqlite3.Connection, match_id: int, accepted: int = 1) -> bool:

    logger.debug(f'update_match_accepted: {match_id}, {accepted}')

    query = "UPDATE matches SET accepted = ? WHERE id = ?"
    query_param = [accepted, match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating accepted in matches: {e}')
        return False


def update_marble_count(connection: sqlite3.Connection, player_id: int, marbles: int) -> bool:

    logger.debug(f'update_marble_count: {player_id}, {marbles}')

    query = "UPDATE users SET marbles = ? WHERE id = ?"
    query_param = [marbles, player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating marbles in user: {e}')
        return False


def update_player_wins(connection: sqlite3.Connection, player_id: int, wins: int) -> bool:

    logger.debug(f'update_player_wins: {player_id}, {wins}')

    query = "UPDATE users SET wins = ? WHERE id = ?"
    query_param = [wins, player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating wins in user: {e}')
        return False


def update_player_loses(connection: sqlite3.Connection, player_id: int, loses: int) -> bool:

    logger.debug(f'update_player_loses: {player_id}, {loses}')

    query = "UPDATE users SET loses = ? WHERE id = ?"
    query_param = [loses, player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating loses in user: {e}')
        return False


def update_bet(connection: sqlite3.Connection, bet_id: int, player_id: int, amount: int) -> bool:

    logger.debug(f'update_bet: {bet_id}, {player_id}, {amount}')

    query = "UPDATE bets SET amount=?, participant1=? WHERE id=?"
    query_param = [amount, player_id, bet_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')

        return True
    except Error as e:
        logger.error(f'There was an error updating bet in bets: {e}')
        return False


def get_match_info_by_id(connection: sqlite3.Connection, match_id: int):

    logger.debug(f'get_match_info_by_id: {match_id}')

    query = "SELECT * FROM matches WHERE id=?"
    query_param = [match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(query, query_param)
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting a match from matches: {e}')
        return 0


def get_match_history_info(connection: sqlite3.Connection, match_id: int):
    logger.debug(f'get_match_history_info: {match_id}')

    query = "SELECT * FROM matches_history WHERE id=?"
    query_param = [match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting matches from match_history: {e}')
        return 0


def get_match_history_info_all(connection: sqlite3.Connection, player_id: int):

    logger.debug(f'get_match_history_info_all: {player_id}')

    query = "SELECT * FROM matches_history WHERE participant1=? OR participant2=?"
    query_param = [player_id, player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchall()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting all matches from match_history: {e}')
        return 0


def get_player_id(connection: sqlite3.Connection, username: str, server_id: int) -> int:

    logger.debug(f'get_player_id: {username}, {server_id}')

    query = "SELECT * FROM users WHERE username=? AND server_id=?"
    query_param = [username, server_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results[0]
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting player_id in users: {e}')
        return 0


def get_player_info(connection: sqlite3.Connection, player_id: int):

    logger.debug(f'get_player_info: {player_id}')

    query = "SELECT * FROM users WHERE id=?"
    query_param = [player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting player_info in users: {e}')
        return 0


def get_player_wins(connection: sqlite3.Connection, player_id: int) -> int:

    logger.debug(f'get_player_wins: {player_id}')
    return get_player_info(connection, player_id)


def get_player_loses(connection: sqlite3.Connection, player_id: int) -> int:

    logger.debug(f'get_player_loses: {player_id}')
    return get_player_info(connection, player_id)[5]


def get_player_info_all_by_server(connection: sqlite3.Connection, server_id: int):

    logger.debug(f'get_player_info_all_by_server: {server_id}')

    query = "SELECT * FROM users WHERE server_id=?"
    query_param = [server_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchall()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting all player_info in users: {e}')
        return 0


def get_marble_count(connection: sqlite3.Connection, player_id: int) -> int:

    logger.debug(f'get_marble_count: {player_id}')

    query = "SELECT * FROM users WHERE id=?"
    query_param = [player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results[2]
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting marbles from users: {e}')
        return 0


def get_bet_info(connection: sqlite3.Connection, bet_id: int):

    logger.debug(f'get_bet_info: {bet_id}')

    query = "SELECT * FROM bets WHERE id=?"
    query_param = [bet_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting bet_info from bets: {e}')
        return 0


def get_bet_info_all(connection: sqlite3.Connection, match_id: int):

    logger.debug(f'get_bet_info_all: {match_id}')

    query = "SELECT * FROM bets WHERE match_id=?"
    query_param = [match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchall()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting all bet_info from bets: {e}')
        return 0


def get_bet_history_info(connection: sqlite3.Connection, bet_id: int):

    logger.debug(f'get_bet_history_info: {bet_id}')

    query = "SELECT * FROM bets_history WHERE id=?"
    query_param = [bet_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting bet_history_info from bets_history: {e}')
        return 0


def get_bet_history_info_all(connection: sqlite3.Connection, better_id: int):

    logger.debug(f'get_bet_history_info_all: {better_id}')

    query = "SELECT * FROM bets_history WHERE better_id=?"
    query_param = [better_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchall()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting all bet_history_info from bet_history: {e}')
        return 0


def find_match_by_player_id(connection: sqlite3.Connection, player_id: int):

    logger.debug(f'find_match_by_player_id: {player_id}')

    query = "SELECT * FROM matches WHERE participant1=? OR participant2=?"
    query_param = [player_id, player_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results[0]
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting match_id from matches: {e}')
        return 0


def find_bet(connection: sqlite3.Connection, match_id: int, better_id: int):

    logger.debug(f'find_bet: {match_id}, {better_id}')

    query = "SELECT * FROM bets WHERE match_id=? AND better_id=?"
    query_param = [match_id, better_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        results = cur.fetchone()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'results: {results}')

        if results is not None:
            return results[0]
        else:
            return 0
    except Error as e:
        logger.error(f'There was an error selecting bet from bets: {e}')
        return 0


def delete_match(connection: sqlite3.Connection, match_id: int) -> bool:

    logger.debug(f'delete_match: {match_id}')

    query = "DELETE FROM matches WHERE id=?"
    query_parm = [match_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_parm)
        connection.commit()

        logger.debug(replace_char_list(query, query_parm))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'match deleted')

        return True
    except Error as e:
        logger.error(f'There was an error deleting match from matches: {e}')
        return False


def delete_bet(connection: sqlite3.Connection, bet_id: int) -> bool:

    logger.debug(f'delete_bet: {bet_id}')

    query = "DELETE FROM bets WHERE id=?"
    query_param = [bet_id]

    try:
        cur = connection.cursor()
        cur.execute(query, query_param)
        connection.commit()

        logger.debug(replace_char_list(query, query_param))
        logger.debug(f'lastrowid: {cur.lastrowid}')
        logger.debug(f'bet deleted')

        return True
    except Error as e:
        logger.error(f'There was an error deleting bet from bets: {e}')
        return False


def delete_bet_by_match_id(connection: sqlite3.Connection, match_id: int):

    logger.debug(f'delete_bet_by_match_id: {match_id}')
    bets = get_bet_info_all(connection, match_id)
    for bet in bets:
        add_marbles(connection, bet[3], bet[1])
        delete_bet(connection, bet[0])


def add_marbles(connection: sqlite3.Connection, player_id: int, marbles: int) -> bool:

    logger.debug(f'add_marbles: {player_id}, {marbles}')
    old_marbles = get_marble_count(connection, player_id)
    return update_marble_count(connection, player_id, old_marbles + marbles)


def add_player_win(connection: sqlite3.Connection, player_id: int, wins: int) -> bool:

    logger.debug(f'add_player_win: {player_id}, {wins}')
    player_wins = get_player_wins(connection, player_id)
    return update_player_wins(connection, player_id, player_wins+wins)


def add_player_loses(connection: sqlite3.Connection, player_id: int, loses: int) -> bool:

    logger.debug(f'add_player_loses: {player_id}, {loses}')
    player_loses = get_player_loses(connection, player_id)
    return update_player_loses(connection, player_id, player_loses+loses)


def subtract_marbles(connection: sqlite3.Connection, player_id: int, marbles: int) -> bool:

    logger.debug(f'subtract_marbles: {player_id}, {marbles}')
    old_marbles = get_marble_count(connection, player_id)

    if old_marbles - marbles < 0:
        return update_marble_count(connection, player_id, 0)

    return update_marble_count(connection, player_id, old_marbles - marbles)


def transfer_marbles(connection: sqlite3.Connection, player_id1: int, player_id2: int, marbles: int) -> bool:

    logger.debug(f'transfer_marbles: {player_id1}, {player_id2}, {marbles}')
    player_marbles1 = get_marble_count(connection, player_id1)

    if player_marbles1 < marbles:
        return False

    if subtract_marbles(connection, player_id1, marbles) and add_marbles(connection, player_id2, marbles):
        return True
    return False


def is_bet_win(connection: sqlite3.Connection, bet_id: int, winner_id: int) -> bool:

    logger.debug(f'is_bet_win: {bet_id}, {winner_id}')
    bet_info = get_bet_info(connection, bet_id)

    logger.debug(f'bet_info: {bet_info}')
    if bet_info[4] == winner_id:
        return True
    else:
        return False


def process_bets(connection: sqlite3.Connection, match_id: int, winner_id: int):

    logger.debug(f'process_bets: {match_id}, {winner_id}')
    bets = get_bet_info_all(connection, match_id)

    logger.debug(f'bets: {bets}')
    marble_pot = 0
    loser_pot = 0
    winner_count = 0
    loser_count = 0
    winner_pot = 0

    if bets == 0:
        logger.debug(f'No bets to process')
        return

    for x in bets:
        if is_bet_win(connection, x[0], winner_id):
            winner_count += 1
            winner_pot += x[1]
        else:
            subtract_marbles(connection, x[3], x[1])
            loser_count += 1
            loser_pot += x[1]
            delete_bet(connection, x[0])
        marble_pot += x[1]

    bets = get_bet_info_all(connection, match_id)

    for x in bets:
        if is_bet_win(connection, x[0], winner_id):
            winner_pot_ratio = x[1]/winner_pot
            if (loser_pot*winner_pot_ratio) < 1:
                winnings = x[1]+1
            else:
                winnings = int(x[1] + (loser_pot*winner_pot_ratio))
            if loser_count < 1:
                winnings = x[1]*2
            logger.debug(f'Winnings: {winnings}')
            add_marbles(connection, x[3], winnings)
            create_bet_history(connection, x[0], x[1], x[2], x[3], x[4], winner_id, datetime.datetime.utcnow())
            delete_bet(connection, x[0])
