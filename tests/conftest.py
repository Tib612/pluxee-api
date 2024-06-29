class MockAPIResponse:
    """To mock requests response"""
    def __init__(self, status_code: int, content: str, headers: dict = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers

class AsyncMockAPIResponse:
    """To mock aiohttp async response"""
    def __init__(self, status_code: int, content: str, headers: dict = None):
        self.status = status_code
        self.content = content
        self.headers = headers

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def text(self):
        return self.content

async def async_mock(*arg, **kwargs):
    pass
