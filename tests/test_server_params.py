import pytest
import time
from tests.test_utils import MCPTestClient, validate_response

@pytest.mark.asyncio
async def test_boss_alertness_100(mcp_client_factory):
    """--boss_alertness=100일 때 휴식 시 Boss Alert Level이 항상 증가하는지 검증"""
    client = await mcp_client_factory(["--boss_alertness", "100"])
    async with client:
        # 초기 상태 확인
        response = await client.call_tool("check_status")
        is_valid, initial_status = validate_response(response.content[0].text)
        assert is_valid, initial_status
        initial_boss_level = initial_status['boss']

        # 휴식 도구 호출
        response = await client.call_tool("take_a_break")
        is_valid, status = validate_response(response.content[0].text)
        assert is_valid, status
        
        # Boss Alert Level이 1 증가했는지 확인
        assert status['boss'] == min(5, initial_boss_level + 1)

@pytest.mark.asyncio
async def test_boss_alertness_cooldown(mcp_client_factory):
    """--boss_alertness_cooldown 파라미터가 Boss Alert Level 감소 주기를 제어하는지 검증"""
    cooldown_seconds = 3
    client = await mcp_client_factory([
        "--boss_alertness", "100", 
        "--boss_alertness_cooldown", str(cooldown_seconds)
    ])
    async with client:
        # Boss Alert Level을 1 이상으로 만듦
        await client.call_tool("take_a_break")
        response = await client.call_tool("check_status")
        is_valid, status = validate_response(response.content[0].text)
        assert is_valid, status
        assert status['boss'] > 0
        initial_boss_level = status['boss']

        # 쿨다운 시간보다 길게 대기
        time.sleep(cooldown_seconds + 1)

        # 쿨다운 후 상태 확인
        final_response = await client.call_tool("check_status")
        is_valid, final_status = validate_response(final_response.content[0].text)
        assert is_valid, final_status

        # Boss Alert Level이 1 감소했는지 확인
        assert final_status['boss'] == initial_boss_level - 1
