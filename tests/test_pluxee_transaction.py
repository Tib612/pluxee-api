from datetime import date

from pluxee import PluxeeTransaction


class TestPluxeeTransaction:
    def test_balance(self):
        balance = PluxeeTransaction(date(2020, 1, 1), -1, "1", "1.1")
        assert balance.date == date(2020, 1, 1)
        assert balance.amount == -1
        assert balance.detail == "1"
        assert balance.merchant == "1.1"
        assert repr(balance) == "date: 2020-01-01\namount: -1\ndetail: 1\nmerchant: 1.1"
