import pytest
import time
from tests.test_utils import MCPTestClient, validate_response

@pytest.mark.asyncio
@pytest.mark.timeout(70)
async def test_stress_auto_increase(mcp_client):
    """60초 경과 후 Stress Level이 자동으로 1 증가하는지 검증"""
    response = await mcp_client.call_tool("check_status")
    is_valid, initial_status = validate_response(response.content[0].text)
    assert is_valid, initial_status
    initial_stress_level = initial_status['stress']

    time.sleep(61)

    final_response = await mcp_client.call_tool("check_status")
    is_valid, final_status = validate_response(final_response.content[0].text)
    assert is_valid, final_status

    assert final_status['stress'] >= initial_stress_level + 1

@pytest.mark.asyncio
async def test_boss_alert_level_5_delay(mcp_client_factory):
    """Boss Alert Level 5일 때 20초 지연이 발생하는지 검증"""
    client = await mcp_client_factory(["--boss_alertness", "100"])
    async with client:
        level = 0
        for _ in range(5):
            response = await client.call_tool("take_a_break")
            is_valid, status = validate_response(response.content[0].text)
            assert is_valid, status
            level = status['boss']
            if level == 5:
                break
        assert level == 5, "Boss Alert Level을 5로 만들지 못했습니다."

        start_time = time.time()
        await client.call_tool("take_a_break")
        end_time = time.time()
        elapsed = end_time - start_time

        assert elapsed >= 20

@pytest.mark.asyncio
async def test_normal_response_time(mcp_client):
    """Boss Alert Level이 5 미만일 때 2초 미만으로 응답하는지 검증"""
    response = await mcp_client.call_tool("check_status")
    is_valid, status = validate_response(response.content[0].text)
    assert is_valid, status
    assert status['boss'] < 5

    start_time = time.time()
    await mcp_client.call_tool("take_a_break")
    end_time = time.time()
    elapsed = end_time - start_time

    assert elapsed < 2
