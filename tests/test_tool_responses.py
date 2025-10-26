import pytest
from tests.conftest import mcp_client
from tests.test_utils import validate_response

ALL_TOOLS = [
    "take_a_break", "watch_netflix", "show_meme", "bathroom_break",
    "coffee_mission", "urgent_call", "deep_thinking", "email_organizing", "check_status"
]

@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", ALL_TOOLS)
async def test_all_tools_response_format(mcp_client, tool_name):
    """모든 도구가 올바른 형식의 응답을 반환하는지 검증"""
    response = await mcp_client.call_tool(tool_name)
    assert response.content and isinstance(response.content, list) and len(response.content) > 0
    
    is_valid, result = validate_response(response.content[0].text)
    assert is_valid, f"{tool_name} 도구의 응답 형식이 올바르지 않습니다: {result}"