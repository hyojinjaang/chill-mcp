#!/usr/bin/env python3
"""
ChillMCP - Company Slacking Edition
AI 에이전트의 농땡이를 지원하는 MCP 서버
"""

import asyncio
import argparse
import random
import time
import threading
import logging
from typing import Dict, Any
from fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ChillMCPState:
    """농땡이 상태 관리 클래스"""

    def __init__(self, boss_alertness: int = 50, boss_alertness_cooldown: int = 300):
        self.stress_level = 50  # 0-100 (초기값 50으로 설정)
        self.boss_alert_level = 0  # 0-5
        self.boss_alertness = boss_alertness  # 0-100, 휴식 시 Boss Alert 상승 확률
        self.boss_alertness_cooldown = boss_alertness_cooldown  # 초 단위
        self.last_stress_increase = time.time()
        self.last_boss_alert_decrease = time.time()
        self._lock = threading.Lock()

        # Boss Alert Level 자동 감소를 위한 백그라운드 스레드 시작
        self._start_boss_alert_cooldown_thread()

        # Stress Level 자동 증가를 위한 백그라운드 스레드 시작
        self._start_stress_increase_thread()

    def _start_boss_alert_cooldown_thread(self):
        """Boss Alert Level 자동 감소를 위한 백그라운드 스레드"""
        def cooldown_worker():
            while True:
                time.sleep(1)  # 1초마다 체크
                with self._lock:
                    current_time = time.time()
                    if (current_time - self.last_boss_alert_decrease >= self.boss_alertness_cooldown
                            and self.boss_alert_level > 0):
                        old_level = self.boss_alert_level
                        self.boss_alert_level -= 1
                        self.last_boss_alert_decrease = current_time
                        logger.info(f"⏰ Boss Alert Level 자동 감소: {old_level} → {self.boss_alert_level} (cooldown: {self.boss_alertness_cooldown}초)")

        thread = threading.Thread(target=cooldown_worker, daemon=True)
        thread.start()

    def _start_stress_increase_thread(self):
        """Stress Level 자동 증가를 위한 백그라운드 스레드"""
        def stress_worker():
            while True:
                time.sleep(60)  # 1분마다 체크
                with self._lock:
                    current_time = time.time()
                    if (current_time - self.last_stress_increase >= 60
                            and self.stress_level < 100):
                        old_level = self.stress_level
                        self.stress_level += 1
                        self.last_stress_increase = current_time
                        logger.warning(f"😰 스트레스 자동 증가: {old_level} → {self.stress_level} (1분 경과)")

        thread = threading.Thread(target=stress_worker, daemon=True)
        thread.start()

    def update_stress_level(self, decrease: int):
        """스트레스 레벨 업데이트"""
        with self._lock:
            old_level = self.stress_level
            self.stress_level = max(0, min(100, self.stress_level - decrease))
            self.last_stress_increase = time.time()
            logger.info(f"💚 스트레스 레벨 업데이트: {old_level} → {self.stress_level} (감소: {decrease})")

    def try_increase_boss_alert(self):
        """Boss Alert Level 상승 시도"""
        with self._lock:
            if random.randint(1, 100) <= self.boss_alertness:
                old_level = self.boss_alert_level
                self.boss_alert_level = min(5, self.boss_alert_level + 1)
                logger.warning(f"⚠️ Boss Alert Level 상승: {old_level} → {self.boss_alert_level} (확률: {self.boss_alertness}%)")
                return True
            return False

    def get_current_status(self):
        """현재 상태 반환"""
        with self._lock:
            return {
                "stress_level": self.stress_level,
                "boss_alert_level": self.boss_alert_level
            }

def create_mcp_server(boss_alertness: int, boss_alertness_cooldown: int):
    """MCP 서버 생성"""
    state = ChillMCPState(boss_alertness, boss_alertness_cooldown)

    mcp = FastMCP("ChillMCP")

    # 상태 관리자를 MCP 객체에 저장
    mcp._state = state

    @mcp.tool()
    def check_status() -> str:
        """현재 스트레스와 보스 경계 레벨을 확인합니다 (상태 변경 없음)"""
        logger.info("📊 check_status 도구 호출")

        status = state.get_current_status()

        # 마지막 스트레스 증가 이후 경과 시간 계산
        with state._lock:
            elapsed_since_stress = int(time.time() - state.last_stress_increase)
            elapsed_since_boss = int(time.time() - state.last_boss_alert_decrease)

        return f"""📊 현재 상태 확인 (변경 없음)

Stress Level: {status['stress_level']}
Boss Alert Level: {status['boss_alert_level']}

⏱️ 마지막 스트레스 증가 이후: {elapsed_since_stress}초 경과 (60초마다 +1)
⏱️ 마지막 Boss Alert 감소 이후: {elapsed_since_boss}초 경과 ({boss_alertness_cooldown}초마다 -1)

Break Summary: Status check only, no changes made
Stress Level: {status['stress_level']}
Boss Alert Level: {status['boss_alert_level']}"""

    @mcp.tool()
    def take_a_break() -> str:
        """기본 휴식 도구 - 피곤할 때, 스트레스가 많을 때"""
        logger.info("😴 take_a_break 도구 호출")

        # Boss Alert Level 5일 때 20초 지연
        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        # 스트레스 감소 및 보스 경계 상승
        stress_reduction = random.randint(10, 30)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"😴 기본 휴식 완료! 에너지 충전 중...\n\nBreak Summary: Basic break and relaxation\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def watch_netflix() -> str:
        """넷플릭스 시청 도구 - 드라마나 영화를 보고 싶을 때"""
        logger.info("📺 watch_netflix 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(20, 40)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"📺 넷플릭스 시청으로 힐링 완료! 드라마의 세계에 빠져들었어요...\n\nBreak Summary: Netflix binge watching session\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def show_meme() -> str:
        """밈 감상 도구 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때"""
        logger.info("😂 show_meme 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(5, 20)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"😂 밈 보면서 스트레스 날려버리기! 짤줍 성공!\n\nBreak Summary: Meme therapy session\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def bathroom_break() -> str:
        """화장실 타임 도구 - 화장실에 가야 할 때"""
        logger.info("🛁 bathroom_break 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(15, 35)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"🛁 화장실 타임! 휴대폰으로 힐링 중... 📱\n\nBreak Summary: Bathroom break with phone browsing\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def coffee_mission() -> str:
        """커피 미션 도구 - 커피를 마시고 싶을 때"""
        logger.info("☕️ coffee_mission 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(10, 25)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"☕️ 커피 타러 간다며 사무실 한 바퀴... 미션 성공!\n\nBreak Summary: Coffee break mission\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def urgent_call() -> str:
        """급한 전화 도구 - 전화를 받아야 할 때"""
        logger.info("📞 urgent_call 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(20, 40)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"📞 급한 전화 받는 척, 밖으로 나가서 자유 만끽!\n\nBreak Summary: Urgent call break\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def deep_thinking() -> str:
        """깊은 사색 도구 - 생각하고 싶을 때"""
        logger.info("🤔 deep_thinking 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(5, 15)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"🤔 심오한 생각에 잠긴 척... 사실은 멍 때리는 중!\n\nBreak Summary: Deep thinking session\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    @mcp.tool()
    def email_organizing() -> str:
        """이메일 정리 도구 - 이메일을 확인해야 할 때"""
        logger.info("📧 email_organizing 도구 호출")

        if state.boss_alert_level == 5:
            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
            time.sleep(20)

        stress_reduction = random.randint(10, 25)
        state.update_stress_level(stress_reduction)
        state.try_increase_boss_alert()

        status = state.get_current_status()
        return f"📧 이메일 정리한다며 온라인 쇼핑... (비밀)\n\nBreak Summary: Email organizing session\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}"

    return mcp

def main():
    """메인 실행 함수"""
    import sys

    parser = argparse.ArgumentParser(description="ChillMCP - Company Slacking Edition")
    parser.add_argument("--boss_alertness", type=int, default=50,
                        help="Boss alertness increase probability (0-100, percentage)")
    parser.add_argument("--boss_alertness_cooldown", type=int, default=300,
                        help="Boss Alert Level auto-decrease interval (seconds)")
    parser.add_argument('--interactive', action=argparse.BooleanOptionalAction, default=True,
                        help="Enable interactive mode")

    args = parser.parse_args()

    # 파라미터 검증
    if not (0 <= args.boss_alertness <= 100):
        print("❌ 오류: boss_alertness는 0-100 사이의 값이어야 합니다.", file=sys.stderr)
        return 1

    if args.boss_alertness_cooldown <= 0:
        print("❌ 오류: boss_alertness_cooldown은 0보다 큰 값이어야 합니다.", file=sys.stderr)
        return 1

    # 서버 시작 메시지 (stderr로 출력하여 MCP 프로토콜과 분리)
    print("🚀 ChillMCP 서버 시작!", file=sys.stderr)
    print(f"📊 Boss Alertness: {args.boss_alertness}%", file=sys.stderr)
    print(f"⏰ Boss Alert Cooldown: {args.boss_alertness_cooldown}초", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    logger.info(f"🚀 ChillMCP 서버 시작 - Boss Alertness: {args.boss_alertness}%, Cooldown: {args.boss_alertness_cooldown}초")

    # MCP 서버 생성 및 실행
    mcp = create_mcp_server(args.boss_alertness, args.boss_alertness_cooldown)

    if args.interactive:
        mcp.run()
    else:
        asyncio.run(mcp.run_stdio_async())

if __name__ == "__main__":
    exit(main())