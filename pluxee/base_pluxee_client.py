import os
from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Tuple

from bs4 import BeautifulSoup

from .exceptions import PluxeeAPIError, PluxeeLoginError


class PassType(str, Enum):
    """The different types of pass that are provided."""
    LUNCH = "LUNCH"
    ECO = "ECO"
    CONSO = "CONSO"
    GIFT = "GIFT"


class PluxeeBalance:
    """The balance of each pass."""
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
    """A payment or the reception of your pass."""
    def __init__(self, date: date, amount: float, detail: str, merchant: str):
        self.date = date
        self.amount = amount
        self.detail = detail
        self.merchant = merchant

    def __str__(self):
        return f"date: {self.date}\namount: {self.amount}\ndetail: {self.detail}\nmerchant: {self.merchant}"

    def __repr__(self):
        return self.__str__()


class _ResponseWrapper:
    def __init__(self, content: str, status_code: int):
        self.content = content
        self.status_code = status_code


class _PluxeeClient:
    """
    The business logic, how to parse and what information to extract.

    Args:
        username: The pluxee username.
        password: The pluxee password.

    Attrs:
        username: The pluxee username.
        password: The pluxee password.
    """

    DOMAIN = "www.sodexo4you.be"
    LANGUAGE = "fr"
    BASE_URL_LOCALIZED = f"https://{DOMAIN}/{LANGUAGE}"
    BASE_URL_TRANSACTIONS = f"{BASE_URL_LOCALIZED}/mon-solde-sodexo-card"

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

    def __init__(self, username: str, password: str) -> None:
        self._username = username or os.environ.get("PLUXEE_USERNAME")
        self._password = password or os.environ.get("PLUXEE_PASSWORD")

    @staticmethod
    def _price_to_float(price) -> float:
        return float(price.replace("€", "").replace(",", ".").replace("EUR", "").strip().replace(" ", ""))

    def _parse_balance_from_reponse(self, response: _ResponseWrapper) -> PluxeeBalance:
        soup = BeautifulSoup(response.content, features="html.parser")

        lunch_tag = soup.select_one(self.LUNCH_PASS_SELECTOR)
        lunch = self._price_to_float(lunch_tag.text) if lunch_tag is not None else 0

        eco_tag = soup.select_one(self.ECO_PASS_SELECTOR)
        eco = self._price_to_float(eco_tag.text) if eco_tag is not None else 0

        gift_tag = soup.select_one(self.GIFT_PASS_SELECTOR)
        gift = self._price_to_float(gift_tag.text) if gift_tag is not None else 0

        conso_tag = soup.select_one(self.CONSO_PASS_SELECTOR)
        conso = self._price_to_float(conso_tag.text) if conso_tag is not None else 0

        if (lunch_tag, eco_tag, gift_tag, conso_tag) == (None, None, None, None):
            raise PluxeeAPIError("Could not find the balance in the response")

        return PluxeeBalance(lunch, eco, gift, conso)

    def _parse_transactions_from_reponse(
        self, response: _ResponseWrapper, since: Optional[date] = None, until: Optional[date] = None
    ) -> Tuple[List[PluxeeTransaction], bool]:
        dom = BeautifulSoup(response.content, features="html.parser")

        table = dom.select_one(self.TRANSACTION_TABLE_SELECTOR)
        if not table:
            # If there is not table, it means something unexpected appen.
            raise PluxeeAPIError()

        entries = dom.select(self.TRANSACTION_SELECTOR)
        transactions = []
        complete = False
        for entry in entries:
            date_dom = entry.select_one("td.views-field-date")
            merchant_dom = entry.select_one("td.views-field-description")
            description_dom = entry.select_one("td.views-field-detail")
            amount_dom = entry.select_one("td.views-field-amount > span")

            if date_dom is None or merchant_dom is None or description_dom is None or amount_dom is None:
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
            if len(transactions) < 10:
                complete = True
                # TODO
                # What if there is 10 elements in the last page, the following page will return a 200 but no table
                # <a href="?type=LUNCH&amp;page=1" class="pager-link">
        return transactions, complete

    def gen_login_post_args(self):
        return {
            "url": self.BASE_URL_LOCALIZED + "/frontpage",
            "params": {
                "destination": f"/{self.LANGUAGE}/frontpage",
            },
            "allow_redirects": False,
            "data": {
                "name": self._username,
                "pass": self._password,
                "form_build_id": "form_build_id",
                "form_id": "user_login_form",
                "op": "Se connecter",
            },
        }

    @staticmethod
    def handle_login_status(status):
        if status != 303:
            if status == 302:
                raise PluxeeLoginError(f"Bad username/password. {status}")
            raise PluxeeAPIError(f"Pluxee webpage did not respond with the expected status. {status}")
