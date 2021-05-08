
class Error(Exception):
    """Base class for other exceptions"""
    pass


class UnableToWrite(Error):
    """Raised when unable to write to database"""
    def __init__(self, message='Unable to write to database'):
        self.message = message
        super().__init__(self.message)


class UnableToRead(Error):
    """Raised when unable to read from database"""
    def __init__(self, message='Unable to read from database'):
        self.message = message
        super().__init__(self.message)


class UnableToDelete(Error):
    """Raised when unable to delete row from table"""
    def __init__(self, message='Unable to delete from database'):
        self.message = message
        super().__init__(self.message)
