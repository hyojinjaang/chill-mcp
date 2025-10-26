import pytest
from fastmcp.client import Client
from server import create_mcp_server

@pytest.fixture
def mcp_client_factory():
    """다양한 파라미터로 클라이언트를 생성하는 팩토리 Fixture"""
    clients = []
    async def _factory(args=None):
        server = create_mcp_server(
            boss_alertness=int(next((args[i+1] for i, x in enumerate(args) if x == "--boss_alertness"), 50)),
            boss_alertness_cooldown=int(next((args[i+1] for i, x in enumerate(args) if x == "--boss_alertness_cooldown"), 300))
        )
        client = Client(server)
        clients.append(client)
        return client
    
    yield _factory

    # 모든 테스트가 끝난 후 클라이언트 정리
    for client in clients:
        # 클라이언트 종료 로직이 있다면 여기에 추가
        pass

@pytest.fixture
async def mcp_client(mcp_client_factory):
    """기본 설정 클라이언트를 제공하는 Fixture"""
    client = await mcp_client_factory([])
    async with client:
        yield client