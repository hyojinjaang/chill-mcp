from fastmcp import FastMCP
from state_manager import ChillMCPState
from tools import register_tools

def create_mcp_server(boss_alertness: int, boss_alertness_cooldown: int):
    """MCP 서버를 생성하고 모든 도구를 등록합니다."""
    state = ChillMCPState(boss_alertness, boss_alertness_cooldown)
    mcp = FastMCP("ChillMCP")
    
    # 상태 관리자와 도구를 MCP 서버에 등록
    register_tools(mcp, state)
    
    return mcp
