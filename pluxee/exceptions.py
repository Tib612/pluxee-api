class PluxeeLoginError(Exception):
    """An error occured with the login process."""
    pass


class PluxeeAPIError(Exception):
    """Pluxee webpage did not respond with the expected status or do not contain the expected information."""
    pass
