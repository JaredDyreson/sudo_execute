"""
MessageException from Kevin Wortman
"""

class MessageException(Exception):
    def __init__(self, message):
        if not (isinstance(message, str)):
            raise ValueError
        self.message = message

# issue reported when sudo_execute class cannot find a given user
# use for internal API
class UnknownUserException(MessageException):
    def __init__(self, message):
        super().__init__(message)

# issue reported when root code execution is invoked by non privilaged user
# use for internal API
class PrivilageExecutionException(MessageException):
    def __init__(self, message):
        super().__init__(message)
