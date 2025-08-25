import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_get_hello(async_client: AsyncClient):
    response = await async_client.get(
        "/helloworld",
    )
    data = response.json()
    assert data["message"] == "Hello World"