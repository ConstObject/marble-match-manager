import sqlite3
import database

from sqlite3 import Error


def create_user(connection, player_id, username, marbles, server_id, wins=0, loses=0):
    cur = connection.cursor()
    cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", [player_id, username, marbles, server_id, wins, loses])

    connection.commit()
    return cur.lastrowid


def create_match(connection, match_id, amount, active, participant1, participant2):
    cur = connection.cursor()
    cur.execute("INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)",
                [match_id, amount, active, participant1, participant2, 0])

    connection.commit()
    return cur.lastrowid


def create_bet(connection, bet_id, amount, match_id, participant1):
    cur = connection.cursor()
    cur.execute("INSERT INTO bets VALUES (?, ?, ?, ?)", [bet_id, amount, match_id, participant1])

    connection.commit()
    return cur.lastrowid


def update_match_activity(connection, match_id, active=1):
    cur = connection.cursor()
    cur.execute("UPDATE matches SET active = ? WHERE id = ?", [active, match_id])

    connection.commit()


def update_match_accepted(connection, match_id, accepted=1):
    cur = connection.cursor()
    cur.execute("UPDATE matches SET accepted = ? WHERE id = ?", [accepted, match_id])

    connection.commit()


def update_marble_count(connection, player_id, marbles):
    cur = connection.cursor()
    cur.execute("UPDATE users SET marbles = ? WHERE id = ?", [marbles, player_id])

    connection.commit()


def update_player_wins(connection, player_id, wins):
    cur = connection.cursor()
    cur.execute("UPDATE users SET wins = ? WHERE id = ?", [wins, player_id])

    connection.commit()


def update_player_loses(connection, player_id, loses):
    cur = connection.cursor()
    cur.execute("UPDATE users SET loses = ? WHERE id = ?", [loses, player_id])

    connection.commit()


def get_match_info_by_id(connection, match_id):
    cur = connection.cursor()
    cur.execute("SELECT * FROM matches WHERE id=?", [match_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_player_id(connection, username, server_id):
    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND server_id=?", [username, server_id])
    return cur.fetchone()


def get_player_info(connection, player_id):
    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", [player_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery
    else:
        return 0


def get_player_wins(connection, player_id):
    sqlquery = get_player_info(connection, player_id)
    return sqlquery[4]


def get_player_loses(connection, player_id):
    return get_player_info(connection, player_id)[5]


def get_marble_count(connection, player_id):
    cur = connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", [player_id])

    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[2]
    else:
        return 0


def find_match_by_player_id(connection, player_id):
    cur = connection.cursor()
    cur.execute("SELECT * FROM matches WHERE participant1=? OR participant2=?", [player_id, player_id])
    sqlquery = cur.fetchone()

    if sqlquery is not None:
        return sqlquery[0]
    else:
        return 0


def delete_match(connection, match_id):
    cur = connection.cursor()
    cur.execute("DELETE FROM matches WHERE id=?", [match_id])

    connection.commit()


def add_marbles(connection, player_id, marbles):
    old_marbles = get_marble_count(connection, player_id)
    update_marble_count(connection, player_id, old_marbles + marbles)


def add_player_win(connection, player_id, wins):
    player_wins = get_player_wins(connection, player_id)
    update_player_wins(connection, player_id, player_wins+wins)
    return


def add_player_loses(connection, player_id, loses):
    player_loses = get_player_loses(connection, player_id)
    update_player_loses(connection, player_id, player_loses+loses)
    return


def subtract_marbles(connection, player_id, marbles):
    old_marbles = get_marble_count(connection, player_id)
    update_marble_count(connection, player_id, old_marbles - marbles)


def transfer_marbles(connection, player_id1, player_id2, marbles):
    player_marbles1 = get_marble_count(connection, player_id1)

    if player_marbles1 < marbles:
        return False

    subtract_marbles(connection, player_id1, marbles)
    add_marbles(connection, player_id2, marbles)
