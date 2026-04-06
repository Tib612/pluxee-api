import os
import tempfile
from datetime import date
from typing import Dict, List, Optional, Union

import requests

from .aia_chaser import AIASession
from .base_pluxee_client import PassType, PluxeeBalance, PluxeeTransaction, _PluxeeClient, _ResponseWrapper
from .exceptions import PluxeeAPIError, PluxeeLoginError


class PluxeeClient(_PluxeeClient):
    """
    A synchronous client providing information about you Pluxee balance and transactions.

    Args:
        username: The pluxee username.
        password: The pluxee password.
        language: The pluxee website language (either 'fr' or 'nl', defaults to 'fr').
        timeout: Request timeout in seconds (defaults to 30).

    Attrs:
        username: The pluxee username.
        password: The pluxee password.
        language: The pluxee website language (either 'fr' or 'nl', defaults to 'fr').
    """

    def __init__(
        self, username: str, password: str, language: str = 'fr', session: Optional[requests.Session] = None, timeout: int = 30
    ):
        super().__init__(username, password, language, session, timeout)
        self._aia_session = AIASession()

    def _login(self, session):
        # call login
        response = session.post(**self.gen_login_post_args(), timeout=self._timeout)
        # Check if we are logged in
        self.handle_login_status(response.status_code)

        # Setting the cookie
        try:
            key, value = response.headers["set-cookie"].split(";")[0].split("=")
            session.cookies.set(key, value)
        except (KeyError, ValueError, AttributeError) as e:
            raise PluxeeLoginError("Could not find the cookie in the login response") from e

    def _make_request(self, url: str, params: Dict[str, Union[str, int]], session) -> _ResponseWrapper:
        response = session.get(url, params=params, timeout=self._timeout)
        if 'logout' in response.content.decode().lower():
            return _ResponseWrapper(response.content.decode(), response.status_code)

        # We got disconnected, the cookies expired
        self._login(session)

        response = session.get(url, params=params, timeout=self._timeout)
        if response.status_code != 200:
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        return _ResponseWrapper(response.content.decode(), response.status_code)

    class TemporaryPEMFile:
        # Using a temporary file implies we need to delete it after use. Therefore I use a context manager.
        def __init__(self, aia_session: 'AIASession', url: str):
            ca_data = aia_session.cadata_from_url(url)
            fd, self._path = tempfile.mkstemp(suffix='.pem')
            try:
                os.write(fd, ca_data.encode('utf-8'))
            finally:
                os.close(fd)

        def __enter__(self) -> str:
            return self._path

        def __exit__(self, exc_type, exc_val, exc_tb):
            os.unlink(self._path)

    def get_balance(self) -> PluxeeBalance:
        """Retrieve the balance of each pass type.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occurred with the login process.

        Returns:
            PluxeeBalance: The balance.
        """
        with self.TemporaryPEMFile(self._aia_session, self._base_url_localized) as ssl_context:
            session: requests.Session = self._session or requests.Session()
            session.verify = ssl_context
            response = self._make_request(self._base_url_balance, {"check_logged_in": "1"}, session)
            return self._parse_balance_from_response(response)

    def get_transactions(
        self, pass_type: PassType, since: Optional[date] = None, until: Optional[date] = None
    ) -> List[PluxeeTransaction]:
        """Retrieve the transactions of the requested pass type in the given interval.

        Args:
            pass_type: The type of the pass for which to retrieve the transactions.
            since: The start of the interval (inclusive). Only transactions on or after this date are returned.
            until: The end of the interval (exclusive). Only transactions before this date are returned.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occurred with the login process.

        Returns:
            List[PluxeeTransaction]: The transactions with the oldest elements first.
        """
        with self.TemporaryPEMFile(self._aia_session, self._base_url_localized) as ssl_context:
            session: requests.Session = self._session or requests.Session()
            session.verify = ssl_context
            transactions: List[PluxeeTransaction] = []
            page_number = 0
            complete = False
            while not complete:
                response = self._make_request(
                    self._base_url_transactions,
                    {"type": pass_type.value, "page": page_number},
                    session,
                )

                complete = self._parse_transactions_from_response(response, transactions, since, until)
                page_number += 1

            return transactions[::-1]
