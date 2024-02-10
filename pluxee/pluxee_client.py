import os
from datetime import date
from enum import Enum
from typing import List

import requests
from requests import Response

from .base_pluxee_client import PassType, PluxeeBalance, PluxeeTransaction, ResponseWrapper, _PluxeeClient
from .exceptions import PluxeeAPIError, PluxeeLoginError


class PluxeeClient(_PluxeeClient):
    def _login(self, session):
        # call login
        response = session.post(**self.gen_login_post_args())
        # Check if we are logged in
        if response.status_code != 303:
            if response.status_code == 302:
                raise PluxeeLoginError(f"Bad username/password. {response.status_code}")
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        # Setting the cookie
        try:
            key, value = response.headers["set-cookie"].split(";")[0].split("=")
            session.cookies.set(key, value)
        except Exception as e:
            raise PluxeeLoginError("Could not find the cookie in the login response") from e

    @staticmethod
    def _price_to_float(price) -> float:
        return float(price.replace("€", "").replace(",", ".").replace("EUR", "").strip().replace(" ", ""))

    def _make_request(self, url, params, session) -> Response:
        response = session.get(url, params=params)
        if 'href="/fr/user/logout"' in response.content.decode():
            return response

        # We got disconnected, the cookies expired
        self._login(session)

        response = session.get(url, params=params)
        if response.status_code != 200:
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        return response

    def get_balance(self) -> PluxeeBalance:
        session = requests.Session()
        response = self._make_request(self.BASE_URL_LOCALIZED, {"check_logged_in": "1"}, session)
        return self._parse_balance_from_reponse(response)

    def get_transactions(
        self, pass_type: PassType, since: date | None = None, until: date | None = None
    ) -> List[PluxeeTransaction]:
        """ "Since must be smaller that until.
        The list is retured with the oldest elements first."""
        session = requests.Session()
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
