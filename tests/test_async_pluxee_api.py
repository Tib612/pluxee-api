import pathlib
from datetime import date
import pytest
from pytest_mock import MockerFixture
import aiohttp

from pluxee import PassType, PluxeeAPIError, PluxeeBalance, PluxeeAsyncClient, PluxeeLoginError, PluxeeTransaction

from .conftest import AsyncMockAPIResponse

test_data_dir = pathlib.Path(__file__).parent / "test_data"

CONTENT_BALANCE = open(test_data_dir / "content_balance.html", "r", encoding="utf-8").read()
CONTENT_EXPIRED_COOKIES = open(test_data_dir / "content_empty_balance.html", "r", encoding="utf-8").read()
CONTENT_TRANSACTIONS = open(test_data_dir / "content_transactions.html", "r", encoding="utf-8").read()
CONTENT_EMPTY_BALANCE = CONTENT_EMPTY_TRANSACTIONS = 'href="/fr/user/logout"'
CONTENT_MALFORMED_TRANSACTIONS = open(test_data_dir / "content_malformed_transactions.html", "r", encoding="utf-8").read()



@pytest.fixture(scope="function")
def client():
    return PluxeeAsyncClient("Foo", "Bar")


class TestPluxeeAsyncClient:
    def test_aiohttp_not_present(self, mocker):
        mocker.patch('builtins.__import__', side_effect=ImportError)
        try:
            from pluxee import PluxeeAsyncClient # noqa
            assert False
        except ImportError:
            pass
        


    @pytest.mark.asyncio
    async def test_login(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as session:
            mock_post: MockerFixture = mocker.patch(
                "aiohttp.ClientSession.post",
                return_value=AsyncMockAPIResponse(303, content="coucou", headers={"set-cookie": "key=value;..."}),
            )
            await client._login(session) 
            mock_post.assert_called_once()
            assert session.cookie_jar


    @pytest.mark.asyncio
    async def test_login_bad_password(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as session:
            mock_post = mocker.patch(
                "aiohttp.ClientSession.post",
                return_value=AsyncMockAPIResponse(302, content="coucou", headers={"set-cookie": "key=value;..."}),
            )

            with pytest.raises(PluxeeLoginError):
                await client._login(session)
            mock_post.assert_called_once()


    @pytest.mark.asyncio
    async def test_login_unknown_error(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as session:
            mock_post = mocker.patch(
                "aiohttp.ClientSession.post",
                return_value=AsyncMockAPIResponse(200, content="coucou", headers={"set-cookie": "key=value;..."}),
            )

            with pytest.raises(PluxeeAPIError):
                await client._login(session)
            mock_post.assert_called_once()


    @pytest.mark.asyncio
    async def test_login_bad_cookie(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as session:
            mock_post = mocker.patch(
                "aiohttp.ClientSession.post",
                return_value=AsyncMockAPIResponse(303, content="coucou", headers={"set-cookie": "...;..."}),
            )

            with pytest.raises(PluxeeLoginError):
                await client._login(session)
            mock_post.assert_called_once()


    @pytest.mark.asyncio
    async def test_get_balance(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(303, content=CONTENT_BALANCE),
            )

            result = await client.get_balance()
            mock_get.assert_called_once()
            assert isinstance(result, PluxeeBalance)
            assert result.lunch_pass == 1
            assert result.eco_pass == 2
            assert result.gift_pass == 3
            assert result.conso_pass == 4


    @pytest.mark.asyncio
    async def test_get_balance_expired_cookie(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                side_effect=[
                    AsyncMockAPIResponse(200, content=CONTENT_EXPIRED_COOKIES),
                    AsyncMockAPIResponse(200, content=CONTENT_BALANCE),
                ],
            )
            mock_login = mocker.patch("pluxee.PluxeeAsyncClient._login", side_effect=lambda _: 1 + 1)

            result = await client.get_balance()
            assert mock_get.call_count == 2
            mock_login.assert_called_once()
            assert isinstance(result, PluxeeBalance)
            assert result.lunch_pass == 1
            assert result.eco_pass == 2
            assert result.gift_pass == 3
            assert result.conso_pass == 4


    @pytest.mark.asyncio
    async def test_login_balances_not_found(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(200, content=CONTENT_EMPTY_BALANCE),
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_balance()
            mock_get.assert_called_once()


    @pytest.mark.asyncio
    async def test_get_transactions(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(303, content=CONTENT_TRANSACTIONS),
            )

            transactions = await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()

            assert isinstance(transactions, list)
            assert len(transactions) == 2

            transaction = transactions[1]
            assert isinstance(transaction, PluxeeTransaction)
            assert transaction.date == date(2024, 2, 6)
            assert transaction.amount == -6.10
            assert transaction.detail == "Paiement detail"
            assert transaction.merchant == "THE MERCHANT"

            transaction = transactions[0]
            assert isinstance(transaction, PluxeeTransaction)
            assert transaction.date == date(2024, 1, 28)
            assert transaction.amount == 144
            assert transaction.detail.replace("\r\n", "\n") == "18 cheques de 8 € = 144 €. Expiry date: \n28.01.2025"
            assert transaction.merchant == "YOUR EMPLOYER"


    @pytest.mark.asyncio
    async def test_get_transactions_expired_cookie(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                side_effect=[
                    AsyncMockAPIResponse(200, content=CONTENT_EXPIRED_COOKIES),
                    AsyncMockAPIResponse(200, content=CONTENT_TRANSACTIONS),
                ],
            )
            mock_login = mocker.patch("pluxee.PluxeeAsyncClient._login", side_effect=lambda _: 1 + 1)

            transactions = await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            assert mock_get.call_count == 2
            mock_login.assert_called_once()
            assert isinstance(transactions, list)
            assert len(transactions) == 2

            transaction = transactions[1]
            assert isinstance(transaction, PluxeeTransaction)
            assert transaction.date == date(2024, 2, 6)
            assert transaction.amount == -6.10
            assert transaction.detail == "Paiement detail"
            assert transaction.merchant == "THE MERCHANT"

            transaction = transactions[0]
            assert isinstance(transaction, PluxeeTransaction)
            assert transaction.date == date(2024, 1, 28)
            assert transaction.amount == 144
            assert transaction.detail.replace("\r\n", "\n") == "18 cheques de 8 € = 144 €. Expiry date: \n28.01.2025"
            assert transaction.merchant == "YOUR EMPLOYER"


    @pytest.mark.asyncio
    async def test_login_transactions_not_found(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(200, content=CONTENT_EMPTY_TRANSACTIONS),
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()


    @pytest.mark.asyncio
    async def test_login_transactions_malformed(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(200, content=CONTENT_MALFORMED_TRANSACTIONS),
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()
