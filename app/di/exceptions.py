class ErrNotFound(Exception):
    def __init__(self, message: str = 'Not found'):
        self.message = message
        super().__init__(message)


class ErrAlreadyExists(Exception):
    def __init__(self, message: str = 'Already exists'):
        self.message = message
        super().__init__(message)


class ErrPermissionDenied(Exception):
    def __init__(self, message: str = 'Permission denied'):
        self.message = message
        super().__init__(message)
