from datetime import date
from typing import Optional, List
from tempfile import NamedTemporaryFile
import os

import requests
from aia import AIASession

from .base_pluxee_client import PassType, PluxeeBalance, PluxeeTransaction, _ResponseWrapper, _PluxeeClient
from .exceptions import PluxeeAPIError, PluxeeLoginError


class PluxeeClient(_PluxeeClient):
    """
    A synchronous client providing information about you Pluxee balance and transactions.

    Args:
        username: The pluxee username.
        password: The pluxee password.

    Attrs:
        username: The pluxee username.
        password: The pluxee password.
    """
    def _login(self, session):
        # call login
        response = session.post(**self.gen_login_post_args())
        # Check if we are logged in
        self.handle_login_status(response.status_code)

        # Setting the cookie
        try:
            key, value = response.headers["set-cookie"].split(";")[0].split("=")
            session.cookies.set(key, value)
        except Exception as e:
            raise PluxeeLoginError("Could not find the cookie in the login response") from e

    def _make_request(self, url: str, params: dict[str, str], session) -> _ResponseWrapper:
        response = session.get(url, params=params)
        if 'logout' in response.content.decode().lower():
            return _ResponseWrapper(response.content.decode(), response.status_code)

        # We got disconnected, the cookies expired
        self._login(session)

        response = session.get(url, params=params)
        if response.status_code != 200:
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        return _ResponseWrapper(response.content.decode(), response.status_code)

    class TemporaryPEMFile:
        # Using a temporary file implies we need to close it. Therefore I use a context manager.
        def __init__(self, url):
            aia_session = AIASession()
            ca_data = aia_session.cadata_from_url(url)  # Validated PEM certificate chain
            self.pem_file = NamedTemporaryFile("w", delete=False)
            self.pem_file.write(ca_data)
            self.pem_file.flush()

        def __enter__(self) -> str:
            return self.pem_file.name

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.pem_file.close()
            os.unlink(self.pem_file.name)


    def get_balance(self) -> PluxeeBalance:
        """ Retrieve the balance of each pass type.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occurred with the login process.

        Returns:
            PluxeeBalance: The balance.
        """
        with self.TemporaryPEMFile(self.BASE_URL_LOCALIZED) as ssl_context:
            session = requests.Session()
            session.verify = ssl_context
            response = self._make_request(self.BASE_URL_LOCALIZED, {"check_logged_in": "1"}, session)
            return self._parse_balance_from_reponse(response)

    def get_transactions(
        self, pass_type: PassType, since: Optional[date] = None, until: Optional[date] = None
    ) -> List[PluxeeTransaction]:
        """ Retrieve the transactions of the requested pass type in the given interval.

        Args:
            pass_type: The type of the pass for which to retrieve the transactions.
            since: The start of the interval.
            until: The start of the interval.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occurred with the login process.

        Returns:
            PluxeeBalance: The balance with the oldest elements first.
        """
        with self.TemporaryPEMFile(self.BASE_URL_LOCALIZED) as ssl_context:
            session = requests.Session()
            session.verify = ssl_context
            transactions = []
            page_number = 0
            complete = False
            while not complete:
                response = self._make_request(
                    self.BASE_URL_TRANSACTIONS,
                    {"type": pass_type.value, "page": page_number},
                    session,
                )

                new_transactions, complete = self._parse_transactions_from_reponse(response, since, until)
                transactions.extend(new_transactions)
                page_number += 1

            return transactions[::-1]
