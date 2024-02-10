from datetime import date

from pluxee import PassType, PluxeeClient

username = input("Username: (leave empty to use PLUXEE_USERNAME env variable)")
password = input("password: (leave empty to use PLUXEE_PASSWORD env variable)")

pc = PluxeeClient(username, password)

balance = pc.get_balance()
print(balance)

transactions = pc.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
print(transactions)
