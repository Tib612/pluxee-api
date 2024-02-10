from pluxee import PluxeeBalance


class TestPluxeeBalance:
    def test_balance(self):
        balance = PluxeeBalance(-1.1, -1, 1, 1.1)
        assert balance.lunch_pass == -1.1
        assert balance.eco_pass == -1
        assert balance.gift_pass == 1
        assert balance.conso_pass == 1.1
        assert repr(balance) == "lunch_pass: -1.1\neco_pass: -1\ngift_pass: 1\nconso_pass: 1.1"
