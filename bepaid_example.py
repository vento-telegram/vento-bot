import asyncio
from random import randint
import base64
import json
import aiohttp
import requests
from typing import Optional

# Load and validate required environment variables
TOKEN="163545849c00bff79922d92c52a35c9c44c50e46517f1e57ba3b220aa54563c6"
SHOP_ID=32569
SITE_URL="https://bukhavets.com/bepaid"



DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}


class HttpClient:
    """
    ✅ Пример использования:

    Асинхронный:

        import asyncio

        async def main():
            async with HttpClient() as client:
                response = await client.async_get("https://example.com")
                text = await response.text()
                print(text)

        asyncio.run(main())

    Синхронный:

        client = HttpClient()
        response = client.get("https://example.com")
        print(response.text)
    """

    def __init__(self, headers: dict = DEFAULT_HEADERS):
        self._session: Optional[aiohttp.ClientSession] = None
        self.headers = headers

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    # -------- Async methods --------

    async def async_get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        self._ensure_session()
        return await self._session.get(url, **kwargs)

    async def async_post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        self._ensure_session()
        return await self._session.post(url, **kwargs)

    def _ensure_session(self):
        if not self._session:
            raise RuntimeError("ClientSession is not initialized. Use 'async with HttpClient()'.")

    # -------- Sync methods --------

    def get(self, url: str, **kwargs) -> requests.Response:
        return requests.get(url, headers=self.headers, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return requests.post(url, headers=self.headers, **kwargs)


class BepaidClient:
    API_BASE_URL = 'https://checkout.bepaid.by/ctp/api'

    def __init__(self, token: str, shop_id: int, site_url: str):
        self.token = token
        self.shop_id = shop_id
        self.site_url = site_url

    @property
    def auth_header(self) -> str:
        credentials = f"{self.shop_id}:{self.token}"
        return base64.b64encode(credentials.encode()).decode()

    @property
    def headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Version': '2',
            'Authorization': f'Basic {self.auth_header}'
        }

    def build_param(self, data: dict) -> dict:
        return {
            "wallet_token": self.token,
            "wallet_shop_id": self.shop_id,
            "bot": data.get("bot", "BepaidClient"),
            "pay_id": data.get("pay_id", 0),
            "description": data.get("description", ""),
            "user_id": data.get("user_id", 0),
            "web_site": self.site_url,
            "user": data.get("user", "")
        }

    def build_payload(self, data: dict, param: dict) -> dict:
        return {
            'checkout': {
                'transaction_type': data.get("transaction_type", "payment"),
                'test': data.get("test", False),
                'order': {
                    'amount': data.get("amount", 1),
                    'currency': data.get("currency", "BYN"),
                    'description': data.get("order_description", "Оплата абонемента"),
                    'tracking_id': data.get("tracking_id", 0)
                },
                'customer': {
                    'first_name': str(param['user']),
                },
                'settings': {
                    'notification_url': f"{param['web_site']}/BepaidBy",
                    'success_url': f"{param['web_site']}/success?bot={param['bot']}",
                    'decline_url': f"{param['web_site']}/fail",
                    'fail_url': f"{param['web_site']}/fail",
                    'cancel_url': f"{param['web_site']}/fail",
                    'language': data.get("language", "ru")
                }
            }
        }

    async def parse_response(self, response: aiohttp.ClientResponse, expected_status: int = 200, debug: bool = False) -> dict:
        try:
            payload = await response.json()
        except Exception:
            payload = {"error": "Invalid JSON response"}

        if debug:
            print(json.dumps(payload, indent=2, ensure_ascii=False))

        return {
            "ok": response.status == expected_status,
            "response": payload
        }

    async def create_payment(self, data: Optional[dict] = None, debug: bool = False) -> dict:
        if data is None:
            data = {}

        param = self.build_param(data)
        payload = self.build_payload(data, param)

        async with HttpClient() as client:
            response = await client.async_post(
                url=f'{self.API_BASE_URL}/checkouts',
                json=payload,
                headers=self.headers
            )
            return await self.parse_response(response, expected_status=201, debug=debug)

    async def get_payment_status(self, checkout_token: str, debug: bool = False) -> dict:
        async with HttpClient() as client:
            response = await client.async_get(
                url=f'{self.API_BASE_URL}/checkouts/{checkout_token}/status',
                headers=self.headers
            )
            return await self.parse_response(response, expected_status=200, debug=debug)

if not all([TOKEN, SHOP_ID, SITE_URL]):
    raise EnvironmentError("Missing required environment variables: TOKEN, SHOP_ID, or SITE_URL")

bepaid = BepaidClient(token=TOKEN, shop_id=int(SHOP_ID), site_url=SITE_URL)


def generate_payment_data() -> dict:
    return {
        "test": True,
        "transaction_type": "payment",
        "bot": "BepaidClientSimple",
        "pay_id": randint(1000000, 9000000),
        "tracking_id": randint(1000000, 9000000),
        "user_id": 7777777,
        "user": "SevaShpun",
        "amount": 1*100,  # 1.00 BYN
        "currency": "BYN",
        "order_description": "Оплата",
        "description": "Оплата товара",
        "language": "ru"
    }


async def create_payment_link():
    data = generate_payment_data()
    await bepaid.create_payment(data=data, debug=True)


async def get_payment_status():
    checkout_token = '5afba1ddc460c9aaee582eb962g7cab6fb151965e4e8d5afca49e9df1e1fa50f'
    await bepaid.get_payment_status(checkout_token=checkout_token, debug=True)


async def main():
    # Choose what to run:
    # await create_payment_link()
    await get_payment_status()

if __name__ == "__main__":
    asyncio.run(main())