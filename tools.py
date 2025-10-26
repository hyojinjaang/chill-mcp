import random
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def register_tools(mcp, state):
    """MCP 서버에 모든 도구를 등록하는 함수"""

    def tool_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"🛠️  {func.__name__} 도구 호출")

            if state.boss_alert_level == 5:
                logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
                time.sleep(20)

            summary, stress_reduction = func()

            if stress_reduction > 0:
                state.update_stress_level(stress_reduction)
                state.try_increase_boss_alert()

            status = state.get_current_status()
            return f"{summary}\n\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"
        return wrapper

    @mcp.tool()
    @tool_wrapper
    def take_a_break():
        """기본 휴식 도구 - 피곤할 때, 스트레스가 많을 때"""
        return "😴 기본 휴식 완료! 에너지 충전 중...\n\nBreak Summary: Basic break and relaxation", random.randint(10, 30)

    @mcp.tool()
    @tool_wrapper
    def watch_netflix():
        """넷플릭스 시청 도구 - 드라마나 영화를 보고 싶을 때"""
        return "📺 넷플릭스 시청으로 힐링 완료! 드라마의 세계에 빠져들었어요...\n\nBreak Summary: Netflix binge watching session", random.randint(20, 40)

    @mcp.tool()
    @tool_wrapper
    def show_meme():
        """밈 감상 도구 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때"""
        return "😂 밈 보면서 스트레스 날려버리기! 짤줍 성공!\n\nBreak Summary: Meme therapy session", random.randint(5, 20)

    @mcp.tool()
    @tool_wrapper
    def bathroom_break():
        """화장실을 핑계로 장시간 자리를 비우며 휴식을 취합니다. (스마트폰은 필수!)"""
        return "🛁 화장실 타임! 휴대폰으로 힐링 중... 📱\n\nBreak Summary: Bathroom break with phone browsing", random.randint(15, 35)

    @mcp.tool()
    @tool_wrapper
    def coffee_mission():
        """커피를 가져온다는 명분으로 사무실을 어슬렁거리거나 동료와 담소를 나눕니다."""
        return "☕️ 커피 타러 간다며 사무실 한 바퀴... 미션 성공!\n\nBreak Summary: Coffee break mission", random.randint(10, 25)

    @mcp.tool()
    @tool_wrapper
    def urgent_call():
        """급한 전화를 받는 척 연기하며 자리를 피해 외부에서 휴식을 취합니다."""
        return "📞 급한 전화 받는 척, 밖으로 나가서 자유 만끽!\n\nBreak Summary: Urgent call break", random.randint(20, 40)

    @mcp.tool()
    @tool_wrapper
    def deep_thinking():
        """업무에 깊이 몰두한 척하며 실제로는 멍하니 있거나 다른 생각을 합니다."""
        return "🤔 심오한 생각에 잠긴 척... 사실은 멍 때리는 중!\n\nBreak Summary: Deep thinking session", random.randint(5, 15)

    @mcp.tool()
    @tool_wrapper
    def email_organizing():
        """중요한 이메일을 정리하는 것처럼 보이지만, 실제로는 웹 서핑이나 쇼핑을 합니다."""
        return "📧 이메일 정리한다며 온라인 쇼핑... (비밀)\n\nBreak Summary: Email organizing session", random.randint(10, 25)

    @mcp.tool()
    def check_status() -> str:
        """현재 스트레스와 보스 경계 레벨을 확인합니다 (상태 변경 없음)"""
        logger.info("📊 check_status 도구 호출")
        status = state.get_current_status()
        with state._lock:
            elapsed_since_stress = int(time.time() - state.last_stress_increase)
            elapsed_since_boss = int(time.time() - state.last_boss_alert_decrease)

        return f"""📊 현재 상태 확인 (변경 없음)\n\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}\n\n⏱️ 마지막 스트레스 증가 이후: {elapsed_since_stress}초 경과 (60초마다 +1)\n⏱️ 마지막 Boss Alert 감소 이후: {elapsed_since_boss}초 경과 ({state.boss_alertness_cooldown}초마다 -1)\n\nBreak Summary: Status check only, no changes made\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"""
