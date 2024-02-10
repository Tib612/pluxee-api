class MockAPIResponse:
    def __init__(self, status_code: int, content: str, headers: dict = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers

    # async def __aenter__(self):
    #    return self

    # async def __aexit__(self):
    #    return self
