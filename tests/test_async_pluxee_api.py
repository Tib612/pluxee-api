import pathlib
import ssl
from datetime import date

import aiohttp
import pytest
from pytest_mock import MockerFixture

from pluxee import PassType, PluxeeAPIError, PluxeeAsyncClient, PluxeeBalance, PluxeeLoginError, PluxeeTransaction

from .conftest import AsyncMockAPIResponse, async_mock

test_data_dir = pathlib.Path(__file__).parent / "test_data"

CONTENT_BALANCE = open(test_data_dir / "content_balance.html", "r", encoding="utf-8").read()
CONTENT_EXPIRED_COOKIES = open(test_data_dir / "content_empty_balance.html", "r", encoding="utf-8").read()
CONTENT_TRANSACTIONS = open(test_data_dir / "content_transactions.html", "r", encoding="utf-8").read()
CONTENT_MALFORMED_TRANSACTIONS = open(test_data_dir / "content_malformed_transactions.html", "r", encoding="utf-8").read()


@pytest.fixture(scope="function")
def client():
    return PluxeeAsyncClient("Foo", "Bar")


class TestPluxeeAsyncClient:
    def test_aiohttp_not_present(self, mocker):
        mocker.patch('builtins.__import__', side_effect=ImportError)
        try:
            from pluxee import PluxeeAsyncClient  # noqa

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
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )

            result = await client.get_balance()
            mock_get.assert_called_once()
            mock_aia.assert_called_once()
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
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )
            mock_login = mocker.patch("pluxee.PluxeeAsyncClient._login", side_effect=async_mock)

            result = await client.get_balance()
            assert mock_get.call_count == 2
            mock_login.assert_called_once()
            mock_aia.assert_called_once()
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
                return_value=AsyncMockAPIResponse(200, content=f"href=\"/{client.get_language()}/user/logout\""),
            )
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_balance()
            mock_get.assert_called_once()
            mock_aia.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transactions(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(303, content=CONTENT_TRANSACTIONS),
            )
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )

            transactions = await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()
            mock_aia.assert_called_once()

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
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )
            mock_login = mocker.patch("pluxee.PluxeeAsyncClient._login", side_effect=async_mock)

            transactions = await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            assert mock_get.call_count == 2
            mock_login.assert_called_once()
            mock_aia.assert_called_once()
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
                return_value=AsyncMockAPIResponse(200, content=f"href=\"/{client.get_language()}/user/logout\""),
            )
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()
            mock_aia.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_transactions_malformed(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mock_get = mocker.patch(
                "aiohttp.ClientSession.get",
                return_value=AsyncMockAPIResponse(200, content=CONTENT_MALFORMED_TRANSACTIONS),
            )
            mock_aia: MockerFixture = mocker.patch(
                "pluxee.PluxeeAsyncClient.get_ssl_context",
                side_effect=async_mock,
            )

            with pytest.raises(PluxeeAPIError):
                await client.get_transactions(PassType.LUNCH, date(2024, 1, 25), date(2024, 3, 1))
            mock_get.assert_called_once()
            mock_aia.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transactions_no_filter(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mocker.patch("aiohttp.ClientSession.get", return_value=AsyncMockAPIResponse(303, content=CONTENT_TRANSACTIONS))
            mocker.patch("pluxee.PluxeeAsyncClient.get_ssl_context", side_effect=async_mock)

            transactions = await client.get_transactions(PassType.LUNCH)
            assert len(transactions) == 3
            assert transactions[0].date == date(2024, 1, 24)
            assert transactions[1].date == date(2024, 1, 28)
            assert transactions[2].date == date(2024, 2, 6)

    @pytest.mark.asyncio
    async def test_get_transactions_only_since(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mocker.patch("aiohttp.ClientSession.get", return_value=AsyncMockAPIResponse(303, content=CONTENT_TRANSACTIONS))
            mocker.patch("pluxee.PluxeeAsyncClient.get_ssl_context", side_effect=async_mock)

            transactions = await client.get_transactions(PassType.LUNCH, since=date(2024, 1, 27))
            assert len(transactions) == 2
            assert transactions[0].date == date(2024, 1, 28)
            assert transactions[1].date == date(2024, 2, 6)

    @pytest.mark.asyncio
    async def test_get_transactions_only_until(self, mocker, client: PluxeeAsyncClient):
        async with aiohttp.ClientSession() as _:
            mocker.patch("aiohttp.ClientSession.get", return_value=AsyncMockAPIResponse(303, content=CONTENT_TRANSACTIONS))
            mocker.patch("pluxee.PluxeeAsyncClient.get_ssl_context", side_effect=async_mock)

            transactions = await client.get_transactions(PassType.LUNCH, until=date(2024, 2, 1))
            assert len(transactions) == 2
            assert transactions[0].date == date(2024, 1, 24)
            assert transactions[1].date == date(2024, 1, 28)

    def test_invalid_language(self):
        with pytest.raises(ValueError):
            PluxeeAsyncClient("Foo", "Bar", language="de")

    @pytest.mark.asyncio
    async def test_get_ssl_context(self, mocker, client: PluxeeAsyncClient):
        mock_ssl_ctx = ssl.create_default_context()
        mock_aia = mocker.patch.object(
            client._aia_session,
            'ssl_context_from_url',
            return_value=mock_ssl_ctx,
        )
        result = await client.get_ssl_context(client._base_url_localized)
        mock_aia.assert_called_once_with(client._base_url_localized)
        assert result is mock_ssl_ctx
