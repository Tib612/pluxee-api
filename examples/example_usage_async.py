import asyncio
from datetime import date

from pluxee import PassType, PluxeeAsyncClient


async def main():
    username = input("Username: (leave empty to use PLUXEE_USERNAME env variable)")
    password = input("password: (leave empty to use PLUXEE_PASSWORD env variable)")

    pc = PluxeeAsyncClient(username, password)

    balance = await pc.get_balance()
    print(balance)

    transactions = await pc.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
    print(transactions)


if __name__ == "__main__":
    asyncio.run(main())
