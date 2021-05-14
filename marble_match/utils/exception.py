import discord
import discord.ext.commands as commands


class DiscordDM(commands.CommandError):
    """Raised when channel is a dm, when expected not to be

    **Attributes**

    - `message` - Main message to print

    """
    def __init__(self, message='Action unable to be done in dm', *args, **kwargs):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        print(self)


class UnableToWrite(commands.CommandError):
    """Raised when unable to write to database

    **Attributes**

    - `message` Main message to display
    - `class_` Class where exception occurred
    - `attribute` Attribute that exception occurred on
    - `value` Value during exception

    """
    def __init__(self, message='Unable to write to database', class_=None, attribute='', value=None, *args, **kwargs):
        self.message = message
        self.class_ = class_
        self.attribute = attribute
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self.class_}.{self.attribute} ({self.value})'


class UnableToRead(commands.CommandError):
    """Raised when unable to read from database

   **Attributes**

    - `message` Main message to display
    - `class_` Class where exception occurred
    - `attribute` Attribute that exception occurred on
    - `value` Value during exception

    """
    def __init__(self, message='Unable to read from database', class_=None, attribute='', value=None, *args, **kwargs):
        self.message = message
        self.class_ = class_
        self.attribute = attribute
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self.class_}.{self.attribute} ({self.value})'


class UnableToDelete(commands.CommandError):
    """Raised when unable to delete row from table

    **Attributes**

    - `message` Main message to display
    - `class_` Class where exception occurred
    - `attribute` Attribute that exception occurred on
    - `value` Value during exception

    """
    def __init__(self, message='Unable to delete from database', class_=None, attribute='', value=None, *args, **kwargs):
        self.message = message
        self.class_ = class_
        self.attribute = attribute
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self.class_}.{self.attribute} ({self.value})'


class UnexpectedEmpty(commands.CommandError):
    """Raised when a value should've been gotten but was empty

    **Attributes**

    - `message` Main message to display
    - `class_` Class where exception occurred
    - `attribute` Attribute that exception occurred on
    - `value` Value during exception

    """

    def __init__(self, message='Unexpected empty value', class_=None, attribute='', value=None, *args, **kwargs):
        self.message = message
        self.class_ = class_
        self.attribute = attribute
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self.class_}.{self.attribute} ({self.value})'


class UnexpectedValue(commands.CommandError):
    """Raised when a value should've been gotten but was empty

    **Attributes**

    - `message` Main message to display
    - `class_` Class where exception occurred
    - `attribute` Attribute that exception occurred on
    - `value` Value that caused exception
    - `expected_values` Values expected

    """

    def __init__(self, message='Unexpected value for attribute', class_=None, attribute='', value=None,
                 expected_values=None, *args, **kwargs):

        self.message = message
        self.class_ = class_
        self.attribute = attribute
        self.value = value
        self.expected_values = expected_values
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: {self.class_}.{self.attribute} ({self.value}) -> ({self.expected_values})'


class InvalidNickname(commands.CommandError):
    """Raised when a nickname is invalid"""

    def __init__(self, message='Invalid nickname'):
        self.message = message
        super().__init__(self.message)
