class DBFunctionException(Exception):
    pass


class BadDBFunctionFormat(DBFunctionException):
    pass


class UnknownDBFunctionId(BadDBFunctionFormat):
    pass


class ReferencedColumnsDontExist(BadDBFunctionFormat):
    pass
