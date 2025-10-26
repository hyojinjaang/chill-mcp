import pytest
import re

async def test_check_status_response(mcp_client):
    """check_status 도구의 응답 형식이 올바른지 검증"""
    response = await mcp_client.call_tool("check_status")
    assert response.content and isinstance(response.content, list) and len(response.content) > 0
    response_text = response.content[0].text
    
    # Break Summary, Stress Level, Boss Alert Level 필드가 모두 포함되어 있는지 확인
    assert "Break Summary:" in response_text
    assert "Stress Level:" in response_text
    assert "Boss Alert Level:" in response_text

    # 각 레벨 값이 숫자 형식인지 정규표현식으로 확인
    stress_match = re.search(r"Stress Level:\s*(\d{1,3})", response_text)
    boss_match = re.search(r"Boss Alert Level:\s*([0-5])", response_text)
    
    assert stress_match is not None
    assert boss_match is not None

    stress_val = int(stress_match.group(1))
    boss_val = int(boss_match.group(1))

    assert 0 <= stress_val <= 100
    assert 0 <= boss_val <= 5
