from datetime import date

from pluxee import PassType, PluxeeClient

username = input("Username: (leave empty to use PLUXEE_USERNAME env variable)")
password = input("password: (leave empty to use PLUXEE_PASSWORD env variable)")

pc = PluxeeClient(username, password)

balance = pc.get_balance()
print(balance)
# Will return a PluxeeBalance object with those attributes
# lunch_pass: 89.19
# eco_pass: 396.16
# gift_pass: 0.0
# conso_pass: 0.0

transactions = pc.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
print(transactions)
# Will return a list of PluxeeTransaction object with those attributes
# date: 2024-06-19
# amount: -75.24
# detail: Paiement classique
# merchant: Colruyt Food Retail
