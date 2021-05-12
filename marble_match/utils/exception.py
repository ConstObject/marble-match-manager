
class Error(Exception):
    """Base class for other exceptions"""
    pass


class DiscordDM(Error):
    """Raised when channel is a dm, when expected not to be"""
    def __init__(self, message='Action unable to be done in dm'):
        self.message = message
        super().__init__(self.message)


class UnableToWrite(Error):
    """Raised when unable to write to database"""
    def __init__(self, message='Unable to write to database', _class=None, _attribute='', _value=None):
        self.message = message
        self._class = _class
        self._attribute = _attribute
        self._value = _value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self._class}.{self._attribute} ({self._value})'


class UnableToRead(Error):
    """Raised when unable to read from database"""
    def __init__(self, message='Unable to read from database', _class=None, _attribute='', _value=None):
        self.message = message
        self._class = _class
        self._attribute = _attribute
        self._value = _value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self._class}.{self._attribute} ({self._value})'


class UnableToDelete(Error):
    """Raised when unable to delete row from table"""
    def __init__(self, message='Unable to delete from database', _class=None, _attribute='', _value=None):
        self.message = message
        self._class = _class
        self._attribute = _attribute
        self._value = _value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self._class}.{self._attribute} ({self._value})'


class UnexpectedEmpty(Error):
    """Raised when a value should've been gotten but was empty"""

    def __init__(self, message='Unexpected empty value', _class=None, _attribute='', _value=None):
        self.message = message
        self._class = _class
        self._attribute = _attribute
        self._value = _value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self._class}.{self._attribute} ({self._value})'


class UnexpectedValue(Error):
    """Raised when a value should've been gotten but was empty"""

    def __init__(self, message='Unexpected value for attribute', _class=None, _attribute='', _value=None,
                 _expected_values=None):

        self.message = message
        self._class = _class
        self._attribute = _attribute
        self._value = _value
        self._expected_values = _expected_values
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self._class}.{self._attribute} ({self._value}) -> ({self._expected_values})'
