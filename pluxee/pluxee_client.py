import os
from datetime import date, datetime
from enum import Enum
from typing import List

import requests
from bs4 import BeautifulSoup
from requests import Response

# TODO: async client !!!!!

DOMAIN = "www.sodexo4you.be"
LANGUAGE = "fr"
BASE_URL_LOCALIZED = f"https://{DOMAIN}/{LANGUAGE}"

LUNCH_PASS_SELECTOR = (
    'body > div > header > div.header-fixed > div.balance-block > div > ul > li > a[href*="LUNCH"] > span.balance--price'
)
ECO_PASS_SELECTOR = (
    'body > div > header > div.header-fixed > div.balance-block > div > ul > li > a[href*="ECO"] > span.balance--price'
)
GIFT_PASS_SELECTOR = (
    'body > div > header > div.header-fixed > div.balance-block > div > ul > li > a[href*="GIFT"] > span.balance--price'
)
CONSO_PASS_SELECTOR = (
    'body > div > header > div.header-fixed > div.balance-block > div > ul > li > a[href*="CONSO"] > span.balance--price'
)
TRANSACTION_SELECTOR = "body > div.dialog-off-canvas-main-canvas > div > div > div.transaction--section > div.transaction-list--section > div.transactions-list--table > div > table > tbody > tr"
TRANSACTION_TABLE_SELECTOR = "body > div.dialog-off-canvas-main-canvas > div > div > div.transaction--section > div.transaction-list--section > div.transactions-list--table > div > table"


class PassType(str, Enum):
    LUNCH = "LUNCH"
    ECO = "ECO"
    CONSO = "CONSO"
    GIFT = "GIFT"


class PluxeeLoginError(Exception):
    pass


class PluxeeAPIError(Exception):
    pass


class PluxeeBalance:
    def __init__(self, lunch_pass: float, eco_pass: float, gift_pass: float, conso_pass: float):
        self.lunch_pass = lunch_pass
        self.eco_pass = eco_pass
        self.gift_pass = gift_pass
        self.conso_pass = conso_pass

    def __str__(self):
        return f"lunch_pass: {self.lunch_pass}\neco_pass: {self.eco_pass}\ngift_pass: {self.gift_pass}\nconso_pass: {self.conso_pass}"

    def __repr__(self):
        return self.__str__()


class PluxeeTransaction:
    def __init__(self, date: date, amount: float, detail: str, merchant: str):
        self.date = date
        self.amount = amount
        self.detail = detail
        self.merchant = merchant

    def __str__(self):
        return f"date: {self.date}\namount: {self.amount}\ndetail: {self.detail}\nmerchant: {self.merchant}"

    def __repr__(self):
        return self.__str__()


class PluxeeClient:
    def __init__(self, username: str, password: str) -> None:
        self._username = username or os.environ.get("PLUXEE_USERNAME")
        self._password = password or os.environ.get("PLUXEE_PASSWORD")
        self._session = requests.Session()

    def _login(self):
        self._session.cookies.set("MOBILE_APP", "1", domain=DOMAIN, path=LANGUAGE)

        # call login
        response = self._session.post(
            BASE_URL_LOCALIZED + "/frontpage",
            params={
                "destination": f"/{LANGUAGE}/frontpage",
            },
            allow_redirects=False,
            data={
                "name": self._username,
                "pass": self._password,
                "form_build_id": "form_build_id",
                "form_id": "user_login_form",
                "op": "Se connecter",
            },
        )
        # Check if we are logged in
        if response.status_code != 303:
            if response.status_code == 302:
                raise PluxeeLoginError(f"Bad username/password. {response.status_code}")
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        # Setting the cookie
        try:
            key, value = response.headers["set-cookie"].split(";")[0].split("=")
            self._session.cookies.set(key, value, domain="." + DOMAIN, secure="HttpOnly", path="/")
        except Exception as e:
            raise PluxeeLoginError("Could not find the cookie in the login response") from e

    @staticmethod
    def _price_to_float(price) -> float:
        return float(price.replace("€", "").replace(",", ".").replace("EUR", "").strip().replace(" ", ""))

    def _make_request(self, url, params) -> Response:
        response = self._session.get(url, params=params)
        if 'href="/fr/user/logout"' in response.content.decode():
            return response

        # We got disconnected, the cookies expired
        self._session = requests.Session()
        self._login()

        response = self._session.get(url, params=params)
        if response.status_code != 200:
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {response.status_code}")

        return response

    def get_balance(self) -> PluxeeBalance:
        response = self._make_request(BASE_URL_LOCALIZED, {"check_logged_in": "1"})

        soup = BeautifulSoup(response.content, features="html.parser")

        lunch_tag = soup.select_one(LUNCH_PASS_SELECTOR)
        lunch = self._price_to_float(lunch_tag.text) if lunch_tag is not None else 0

        eco_tag = soup.select_one(ECO_PASS_SELECTOR)
        eco = self._price_to_float(eco_tag.text) if eco_tag is not None else 0

        gift_tag = soup.select_one(GIFT_PASS_SELECTOR)
        gift = self._price_to_float(gift_tag.text) if gift_tag is not None else 0

        conso_tag = soup.select_one(CONSO_PASS_SELECTOR)
        conso = self._price_to_float(conso_tag.text) if conso_tag is not None else 0

        if (lunch_tag, eco_tag, gift_tag, conso_tag) == (None, None, None, None):
            raise PluxeeAPIError("Could not find the balance in the response")

        return PluxeeBalance(lunch, eco, gift, conso)

    def get_transactions(
        self, pass_type: PassType, since: date | None = None, until: date | None = None
    ) -> List[PluxeeTransaction]:
        """ "Since must be smaller that until.
        The list is retured with the oldest elements first."""
        transactions = []
        page_number = 0
        complete = False
        while not complete:
            response = self._make_request(
                BASE_URL_LOCALIZED + "/mon-solde-sodexo-card",
                {"type": pass_type.value, "page": page_number},
            )

            dom = BeautifulSoup(response.content, features="html.parser")

            table = dom.select_one(TRANSACTION_TABLE_SELECTOR)
            if not table:
                # If there is not table, it means something unexpected appen.
                raise PluxeeAPIError()

            entries = dom.select(TRANSACTION_SELECTOR)
            for entry in entries:
                date_dom = entry.select_one("td.views-field-date")
                merchant_dom = entry.select_one("td.views-field-description")
                description_dom = entry.select_one("td.views-field-detail")
                amount_dom = entry.select_one("td.views-field-amount > span")

                if None in [date_dom, merchant_dom, description_dom, amount_dom]:
                    raise PluxeeAPIError("Could not find the transactions in the response")

                date = datetime.strptime(date_dom.text.strip(), "%d.%m.%Y").date()
                merchant = merchant_dom.text.strip()
                description = description_dom.text.strip()
                amount = self._price_to_float(amount_dom.text)
                if since and date < since:
                    complete = True
                    break
                if until and date < until:
                    transactions.append(PluxeeTransaction(date, amount, description, merchant))

            if len(entries) < 10:
                complete = True
                # TODO
                # What if there is 10 elements in the last page, the following page will return a 200 but no table
                # <a href="?type=LUNCH&amp;page=1" class="pager-link">
            page_number += 1

        return transactions[::-1]
