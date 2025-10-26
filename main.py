#!/usr/bin/env python3
"""
ChillMCP - Company Slacking Edition
AI 에이전트의 농땡이를 지원하는 MCP 서버
"""

import asyncio
import argparse
import logging
import sys

from server import create_mcp_server

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="ChillMCP - Company Slacking Edition")
    parser.add_argument("--boss_alertness", type=int, default=50,
                        help="Boss alertness increase probability (0-100, percentage)")
    parser.add_argument("--boss_alertness_cooldown", type=int, default=300,
                        help="Boss Alert Level auto-decrease interval (seconds)")

    args = parser.parse_args()

    # 파라미터 검증
    if not (0 <= args.boss_alertness <= 100):
        print("❌ 오류: boss_alertness는 0-100 사이의 값이어야 합니다.", file=sys.stderr)
        sys.exit(1)

    if args.boss_alertness_cooldown <= 0:
        print("❌ 오류: boss_alertness_cooldown은 0보다 큰 값이어야 합니다.", file=sys.stderr)
        sys.exit(1)

    # 서버 시작 메시지 (stderr로 출력하여 MCP 프로토콜과 분리)
    print("🚀 ChillMCP 서버 시작!", file=sys.stderr)
    print(f"📊 Boss Alertness: {args.boss_alertness}%", file=sys.stderr)
    print(f"⏰ Boss Alert Cooldown: {args.boss_alertness_cooldown}초", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # MCP 서버 생성 및 실행
    mcp = create_mcp_server(args.boss_alertness, args.boss_alertness_cooldown)
    mcp.run()

if __name__ == "__main__":
    main()
