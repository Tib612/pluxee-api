from datetime import date
from typing import Optional, List

import aiohttp

from .base_pluxee_client import PassType, PluxeeBalance, PluxeeTransaction, _ResponseWrapper, _PluxeeClient
from .exceptions import PluxeeAPIError, PluxeeLoginError


class PluxeeAsyncClient(_PluxeeClient):
    """
    An asynchronous client providing information about you Pluxee balance and transactions.

    Args:
        username: The pluxee username.
        password: The pluxee password.

    Attrs:
        username: The pluxee username.
        password: The pluxee password.
    """

    async def _login(self, session):
        # call login
        async with session.post(**self.gen_login_post_args()) as response:
            # Check if we are logged in
            self.handle_login_status(response.status)

            # Setting the cookie
            try:
                key, value = response.headers["set-cookie"].split(";")[0].split("=")
                session.cookie_jar.update_cookies({key: value})
            except Exception as e:
                raise PluxeeLoginError("Could not find the cookie in the login response") from e

    async def _make_request(self, url, params, session) -> _ResponseWrapper:
        async with session.get(url, params=params) as response:
            content = await response.text()
            if 'href="/fr/user/logout"' in content:
                return _ResponseWrapper(content, response.status)

        # We got disconnected, the cookies expired
        await self._login(session)

        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status}")
            return _ResponseWrapper(await response.text(), response.status)

    async def get_balance(self) -> PluxeeBalance:
        """ Retrieve the balance of each pass type.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occured with the login process.

        Returns:
            PluxeeBalance: The balance.
        """
        async with aiohttp.ClientSession() as session:
            response = await self._make_request(self.BASE_URL_LOCALIZED, {"check_logged_in": "1"}, session)
            return self._parse_balance_from_reponse(response)

    async def get_transactions(
        self, pass_type: PassType, since: Optional[date] = None, until: Optional[date] = None
    ) -> List[PluxeeTransaction]:
        """ Retrieve the transactions of the requested pass type in the given interval.

        Args:
            pass_type: The type of the pass for which to retireve the transactions.
            since: The start of the interval.
            until: The start of the interval.

        Raises:
            PluxeeAPIError: If Pluxee webpage did not respond with the expected status or do not contain the expected information.
            PluxeeLoginError: If an error occured with the login process.

        Returns:
            PluxeeBalance: The balance with the oldest elements first.
        """
        async with aiohttp.ClientSession() as session:
            transactions = []
            page_number = 0
            complete = False
            while not complete:
                response = await self._make_request(
                    self.BASE_URL_TRANSACTIONS, {"type": pass_type.value, "page": page_number}, session
                )
                new_transactions, complete = self._parse_transactions_from_reponse(response, since, until)
                transactions.extend(new_transactions)
                page_number += 1

            return transactions[::-1]
