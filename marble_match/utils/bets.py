import datetime
import logging
from dataclasses import dataclass, field

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler

import utils.account as account
import utils.discord_utils as du
import utils.matches as matches

logger = logging.getLogger(f'marble_match.{__name__}')


@dataclass(order=True)
class Bet:
    id: int
    _amount: int
    match: matches.Match
    _bettor: account.Account
    bet_target: account.Account
    _winner: account.Account = field(default=None)
    _bet_time: datetime.datetime = field(default=None)
    _is_history: bool = field(default=False)

    @property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, amount):
        logger.debug(f'amount_setter" {amount}')

        # TODO Update database, check if write was successful then set data in self
        self._amount = amount
