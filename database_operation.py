import sqlite3
import datetime
import database

from sqlite3 import Error


def create_user(connection: sqlite3.Connection, player_id: int, username: str, marbles: int, server_id: int,
                wins: int = 0, loses: int = 0) -> int:

    cur = connection.cursor()
    cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", [player_id, username, marbles, server_id, wins, loses])

    connection.commit()
    return cur.lastrowid


def create_match(connection: sqlite3.Connection, match_id: int, amount: int, active: int,
                 participant1: int, participant2: int) -> int:

    cur = connection.cursor()
    cur.execute("INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)",
                [match_id, amount, active, participant1, participant2, 0])

    connection.commit()
    return cur.lastrowid


def create_bet(connection: sqlite3.Connection, bet_id: int, amount: int, match_id: int, better_id: int,
               participant1: int):

    cur = connection.cursor()
    cur.execute("INSERT INTO bets VALUES (?, ?, ?, ?, ?)", [bet_id, amount, match_id, better_id, participant1])

    connection.commit()
    subtract_marbles(connection, better_id, amount)
    return cur.lastrowid


def create_match_history(connection: sqlite3.Connection, match_id: int, amount: int,
                         participant1: int, participant2: int, winner_id: int, time: datetime.datetime):

    cur = connection.cursor()
    cur.execute("INSERT INTO matches_history VALUES (?, ?, ?, ?, ?, ?)",
                [match_id, amount, participant1, participant2, winner_id, time])

    connection.commit()
    print(cur.lastrowid)
    return cur.lastrowid


def create_bet_history(connection: sqlite3.Connection, bet_id: int, amount: int, match_id: int, better_id: int,
                       participant1: int, winner_id: int, time: datetime.datetime):

    cur = connection.cursor()
    cur.execute("INSERT INTO bets_history VALUES (?, ?, ?, ?, ?, ?, ?)",
                [bet_id, amount, match_id, better_id, participant1, winner_id, time])

    connection.commit()
    print(cur.lastrowid)
    return cur.lastrowid


def update_match_activity(connection: sqlite3.Connection, match_id: int, active: int = 1):

    cur = connection.cursor()
    cur.execute("UPDATE matches SET active = ? WHERE id = ?", [active, match_id])

    connection.commit()


def update_match_accepted(connection: sqlite3.Connection, match_id: int, accepted: int = 1):

    cur = connection.cursor()
    cur.execute("UPDATE matches SET accepted = ? WHERE id = ?", [accepted, match_id])

    connection.commit()


def update_marble_count(connection: sqlite3.Connection, player_id: int, marbles: int):

    cur = connection.cursor()
    cur.execute("UPDATE users SET marbles = ? WHERE id = ?", [marbles, player_id])

    connection.commit()


def update_player_wins(connection: sqlite3.Connection, player_id: int, wins: int):

    cur = connection.cursor()
    cur.execute("UPDATE users SET wins = ? WHERE id = ?", [wins, player_id])

    connection.commit()


def update_player_loses(connection: sqlite3.Connection, player_id: int, loses: int):

    cur = connection.cursor()
    cur.execute("UPDATE users SET loses = ? WHERE id = ?", [loses, player_id])

    connection.commit()


def update_bet(connection: sqlite3.Connection, bet_id: int, player_id: int, amount: int):

    cur = connection.cursor()
    cur.execute("UPDATE bets SET amount=?, participant1=? WHERE id=?", [amount, player_id, bet_id])

    connection.commit()


def get_match_info_by_id(connection: sqlite3.Connection, match_id: int) -> int:

    cur = connection.cursor()
    cur.execute("SELECT * FROM matches WHERE id=?", [match_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_match_history_info(connection: sqlite3.Connection, match_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM matches_history WHERE id=?", [match_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_match_history_info_all(connection: sqlite3.Connection, player_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM matches_history WHERE participant1=? OR participant2=?", [player_id, player_id])

    sqlquery = cur.fetchall()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_player_id(connection: sqlite3.Connection, username: str, server_id: int) -> int:

    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND server_id=?", [username, server_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[0]
    else:
        return 0


def get_player_info(connection: sqlite3.Connection, player_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", [player_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_player_wins(connection: sqlite3.Connection, player_id: int) -> int:

    sqlquery = get_player_info(connection, player_id)
    return sqlquery[4]


def get_player_loses(connection: sqlite3.Connection, player_id: int) -> int:

    return get_player_info(connection, player_id)[5]


def get_player_info_all_by_server(connection: sqlite3.Connection, server_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE server_id=?", [server_id])

    sqlquery = cur.fetchall()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_marble_count(connection: sqlite3.Connection, player_id: int) -> int:

    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", [player_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[2]
    else:
        return 0


def get_bet_info(connection: sqlite3.Connection, bet_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM bets WHERE id=?", [bet_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_bet_info_all(connection: sqlite3.Connection, match_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM bets WHERE match_id=?", [match_id])

    sqlquery = cur.fetchall()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_bet_history_info(connection: sqlite3.Connection, bet_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM bets_history WHERE id=?", [bet_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_bet_history_info_all(connection: sqlite3.Connection, better_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM bets_history WHERE better_id=?", [better_id])

    sqlquery = cur.fetchall()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def find_match_by_player_id(connection: sqlite3.Connection, player_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM matches WHERE participant1=? OR participant2=?", [player_id, player_id])
    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[0]
    else:
        return 0


def find_bet(connection: sqlite3.Connection, match_id: int, better_id: int):

    cur = connection.cursor()
    cur.execute("SELECT * FROM bets WHERE match_id=? AND better_id=?", [match_id, better_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[0]
    else:
        return 0


def delete_match(connection: sqlite3.Connection, match_id: int):

    cur = connection.cursor()
    cur.execute("DELETE FROM matches WHERE id=?", [match_id])

    connection.commit()


def delete_bet(connection: sqlite3.Connection, bet_id: int):

    cur = connection.cursor()
    cur.execute("DELETE FROM bets WHERE id=?", [bet_id])

    connection.commit()


def delete_bet_by_match_id(connection: sqlite3.Connection, match_id: int):

    bets = get_bet_info_all(connection, match_id)
    for bet in bets:
        add_marbles(connection, bet[3], bet[1])
        delete_bet(connection, bet[0])


def add_marbles(connection: sqlite3.Connection, player_id: int, marbles: int):

    old_marbles = get_marble_count(connection, player_id)
    update_marble_count(connection, player_id, old_marbles + marbles)


def add_player_win(connection: sqlite3.Connection, player_id: int, wins: int):

    player_wins = get_player_wins(connection, player_id)
    update_player_wins(connection, player_id, player_wins+wins)
    return


def add_player_loses(connection: sqlite3.Connection, player_id: int, loses: int):

    player_loses = get_player_loses(connection, player_id)
    update_player_loses(connection, player_id, player_loses+loses)
    return


def subtract_marbles(connection: sqlite3.Connection, player_id: int, marbles: int):

    old_marbles = get_marble_count(connection, player_id)

    if old_marbles - marbles < 0:
        update_marble_count(connection, player_id, 0)
        return

    update_marble_count(connection, player_id, old_marbles - marbles)


def transfer_marbles(connection: sqlite3.Connection, player_id1: int, player_id2: int, marbles: int):

    player_marbles1 = get_marble_count(connection, player_id1)

    if player_marbles1 < marbles:
        return False

    subtract_marbles(connection, player_id1, marbles)
    add_marbles(connection, player_id2, marbles)


def is_bet_win(connection: sqlite3.Connection, bet_id: int, winner_id: int) -> bool:

    bet_info = get_bet_info(connection, bet_id)

    if bet_info[4] == winner_id:
        return True
    else:
        return False


def process_bets(connection: sqlite3.Connection, match_id: int, winner_id: int):

    bets = get_bet_info_all(connection, match_id)

    bet_count = 0
    marble_pot = 0
    loser_pot = 0
    winner_count = 0
    loser_count = 0
    winner_pot = 0

    if bets == 0:
        return

    bet_count = len(bets)

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
            print(f'Winnings: {winnings}')
            add_marbles(connection, x[3], winnings)
            create_bet_history(connection, x[0], x[1], x[2], x[3], x[4], winner_id, datetime.datetime.utcnow())
            delete_bet(connection, x[0])
