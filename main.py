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
import re
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from fastmcp import FastMCP

# LLM 관련 import (로컬 LLM만 사용)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class LocalLLMSelector:
    """로컬 LLM 기반 도구 선택기 (경량 모델)"""
    
    def __init__(self):
        self.available_tools = {
            "take_a_break": "기본 휴식 - 피곤할 때, 스트레스가 많을 때, 에너지가 필요할 때",
            "watch_netflix": "넷플릭스 시청 - 드라마나 영화를 보고 싶을 때, 오락이 필요할 때",
            "show_meme": "밈 감상 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때, 스트레스 해소가 필요할 때",
            "bathroom_break": "화장실 타임 - 화장실에 가야 할 때, 잠깐 자리를 비워야 할 때",
            "coffee_mission": "커피 미션 - 커피를 마시고 싶을 때, 카페에 가고 싶을 때, 에너지가 필요할 때",
            "urgent_call": "급한 전화 - 전화를 받아야 할 때, 급한 연락이 있을 때",
            "deep_thinking": "깊은 사색 - 생각하고 싶을 때, 고민이 있을 때, 명상하고 싶을 때",
            "email_organizing": "이메일 정리 - 이메일을 확인해야 할 때, 메일을 정리하고 싶을 때, 온라인 쇼핑을 하고 싶을 때"
        }
        
        # 키워드 기반 매칭 시스템
        self.keyword_patterns = {
            "take_a_break": ["피곤", "쉬", "휴식", "스트레스", "에너지", "지쳐", "힘들", "break", "rest", "tired"],
            "watch_netflix": ["드라마", "영화", "넷플", "시청", "보고", "오락", "entertainment", "movie", "drama"],
            "show_meme": ["밈", "웃음", "재미", "유머", "웃고", "meme", "funny", "laugh", "humor"],
            "bathroom_break": ["화장실", "화장실가", "bathroom", "toilet", "restroom"],
            "coffee_mission": ["커피", "카페", "커피타러", "coffee", "cafe", "카페인"],
            "urgent_call": ["전화", "통화", "급한", "콜", "call", "phone", "urgent"],
            "deep_thinking": ["생각", "고민", "사색", "명상", "멍때", "think", "meditate", "contemplate"],
            "email_organizing": ["이메일", "메일", "쇼핑", "정리", "email", "mail", "shopping", "organize"]
        }
        
        # 임베딩 모델 초기화 (실제 LLM)
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info("🤖 임베딩 모델 로딩 중...")
                # 진행바 출력 비활성화
                import os
                os.environ['TOKENIZERS_PARALLELISM'] = 'false'
                import warnings
                warnings.filterwarnings('ignore')
                
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("✅ 임베딩 모델 로드 완료 - 실제 LLM 사용 가능")
            except Exception as e:
                logger.warning(f"❌ 임베딩 모델 로드 실패: {e}")
                logger.info("🔄 키워드 매칭으로 폴백")
        else:
            logger.warning("❌ sentence-transformers 패키지 없음 - 키워드 매칭만 사용")
    
    def select_tool_with_keywords(self, user_input: str) -> Tuple[str, str]:
        """키워드 기반 도구 선택"""
        input_lower = user_input.lower().strip()
        
        # 각 도구별 점수 계산
        tool_scores = {}
        for tool, keywords in self.keyword_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in input_lower:
                    score += 1
                    # 키워드 길이에 따른 가중치
                    score += len(keyword) * 0.1
            
            tool_scores[tool] = score
        
        # 가장 높은 점수의 도구 선택
        if tool_scores:
            best_tool = max(tool_scores, key=tool_scores.get)
            if tool_scores[best_tool] > 0:
                return best_tool, f"키워드 매칭: {tool_scores[best_tool]:.1f}점"
        
        # 기본값
        return "take_a_break", "기본 휴식 (키워드 매칭 없음)"
    
    def select_tool_with_embeddings(self, user_input: str) -> Tuple[str, str]:
        """임베딩 기반 도구 선택 (고급)"""
        if not self.embedding_model:
            return self.select_tool_with_keywords(user_input)
        
        try:
            # 진행바 출력 비활성화
            import os
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            # 사용자 입력 임베딩 (진행바 숨김)
            user_embedding = self.embedding_model.encode([user_input], show_progress_bar=False)
            
            # 각 도구 설명의 임베딩과 유사도 계산 (진행바 숨김)
            tool_similarities = {}
            for tool, description in self.available_tools.items():
                tool_embedding = self.embedding_model.encode([description], show_progress_bar=False)
                similarity = user_embedding.dot(tool_embedding.T)[0][0]
                tool_similarities[tool] = similarity
            
            # 가장 유사한 도구 선택
            best_tool = max(tool_similarities, key=tool_similarities.get)
            similarity_score = tool_similarities[best_tool]
            
            return best_tool, f"임베딩 유사도: {similarity_score:.3f}"
            
        except Exception as e:
            logger.warning(f"임베딩 기반 선택 실패: {e}")
            return self.select_tool_with_keywords(user_input)

class LLMToolSelector:
    """로컬 LLM 기반 도구 선택기"""
    
    def __init__(self, provider: str = "local", model: str = "local"):
        self.provider = provider
        self.model = model
        self.available_tools = {
            "take_a_break": "기본 휴식 - 피곤할 때, 스트레스가 많을 때, 에너지가 필요할 때",
            "watch_netflix": "넷플릭스 시청 - 드라마나 영화를 보고 싶을 때, 오락이 필요할 때",
            "show_meme": "밈 감상 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때, 스트레스 해소가 필요할 때",
            "bathroom_break": "화장실 타임 - 화장실에 가야 할 때, 잠깐 자리를 비워야 할 때",
            "coffee_mission": "커피 미션 - 커피를 마시고 싶을 때, 카페에 가고 싶을 때, 에너지가 필요할 때",
            "urgent_call": "급한 전화 - 전화를 받아야 할 때, 급한 연락이 있을 때",
            "deep_thinking": "깊은 사색 - 생각하고 싶을 때, 고민이 있을 때, 명상하고 싶을 때",
            "email_organizing": "이메일 정리 - 이메일을 확인해야 할 때, 메일을 정리하고 싶을 때, 온라인 쇼핑을 하고 싶을 때"
        }
        
        # 로컬 LLM 선택기 초기화
        self.local_selector = LocalLLMSelector()
        self.client = None  # API 클라이언트 사용 안함
        logger.info("🤖 로컬 LLM 선택기 초기화 완료")
    
    def create_tool_selection_prompt(self, user_input: str) -> str:
        """도구 선택을 위한 프롬프트 생성"""
        tools_description = "\n".join([f"- {name}: {desc}" for name, desc in self.available_tools.items()])
        
        prompt = f"""당신은 회사에서 일하는 직원의 농땡이 활동을 도와주는 AI 어시스턴트입니다.

사용자 입력: "{user_input}"

사용 가능한 도구들:
{tools_description}

위의 도구들 중에서 사용자의 요청에 가장 적합한 도구를 하나만 선택해주세요.
응답은 반드시 JSON 형식으로 해주세요:
{{"tool": "선택된_도구명", "reason": "선택_이유"}}

예시:
사용자: "피곤해"
응답: {{"tool": "take_a_break", "reason": "피로감을 표현했으므로 기본 휴식이 적합합니다"}}

사용자: "드라마 보고 싶어"
응답: {{"tool": "watch_netflix", "reason": "드라마 시청을 원하므로 넷플릭스 시청이 적합합니다"}}"""
        
        return prompt
    
    def select_tool_with_llm(self, user_input: str) -> Tuple[str, str]:
        """로컬 LLM을 사용하여 도구 선택"""
        # 임베딩 기반 선택 시도 (실제 LLM)
        if self.local_selector.embedding_model:
            try:
                tool, reason = self.local_selector.select_tool_with_embeddings(user_input)
                logger.info(f"🤖 로컬 임베딩 LLM 선택: {tool} - {reason}")
                return tool, f"로컬 임베딩 LLM: {reason}"
            except Exception as e:
                logger.warning(f"로컬 임베딩 LLM 선택 실패: {e}")
        
        # 키워드 기반 선택 (폴백)
        tool, reason = self.local_selector.select_tool_with_keywords(user_input)
        logger.info(f"🔍 키워드 매칭 선택: {tool} - {reason}")
        return tool, f"키워드 매칭: {reason}"
    
    def _fallback_selection(self, user_input: str) -> Tuple[str, str]:
        """로컬 선택기 사용"""
        logger.info("🔄 로컬 선택기 사용")
        
        # 로컬 임베딩 기반 선택 시도
        if self.local_selector.embedding_model:
            try:
                tool, reason = self.local_selector.select_tool_with_embeddings(user_input)
                logger.info(f"🤖 로컬 임베딩 선택: {tool} - {reason}")
                return tool, f"로컬 임베딩: {reason}"
            except Exception as e:
                logger.warning(f"로컬 임베딩 선택 실패: {e}")
        
        # 키워드 기반 선택
        tool, reason = self.local_selector.select_tool_with_keywords(user_input)
        logger.info(f"🔍 로컬 키워드 선택: {tool} - {reason}")
        return tool, f"로컬 키워드: {reason}"

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

def parse_natural_language(input_text: str) -> str:
    """자연어를 분석하여 적절한 도구 선택"""
    input_lower = input_text.lower().strip()
    
    # 키워드 기반 매칭
    tool_keywords = {
        "take_a_break": ["휴식", "쉬자", "쉬어", "피곤", "지쳐", "스트레스", "에너지", "충전"],
        "watch_netflix": ["넷플릭스", "netflix", "드라마", "영화", "시청", "힐링"],
        "show_meme": ["밈", "meme", "웃음", "재미", "유머", "스트레스 해소"],
        "bathroom_break": ["화장실", "화장실가"],
        "coffee_mission": ["커피", "카페", "커피타러"],
        "urgent_call": ["전화", "급한", "통화"],
        "deep_thinking": ["생각", "고민", "사색", "멍때리"],
        "email_organizing": ["이메일", "메일", "쇼핑"]
    }
    
    # 점수 계산
    tool_scores = {}
    for tool, keywords in tool_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in input_lower:
                score += 1
                score += len(keyword) * 0.1
        tool_scores[tool] = score
    
    # 가장 높은 점수의 도구 선택
    if tool_scores:
        best_tool = max(tool_scores, key=tool_scores.get)
        if tool_scores[best_tool] > 0:
            return best_tool
    
    # 패턴 매칭
    patterns = [
        (r"(휴식|쉬|break|rest)", "take_a_break"),
        (r"(넷플|드라마|영화|시청)", "watch_netflix"),
        (r"(밈|웃음|유머|재미)", "show_meme"),
        (r"(화장실|화장실)", "bathroom_break"),
        (r"(커피|카페)", "coffee_mission"),
        (r"(전화|통화|콜)", "urgent_call"),
        (r"(생각|고민|사색|명상)", "deep_thinking"),
        (r"(이메일|메일|쇼핑)", "email_organizing"),
    ]
    
    for pattern, tool in patterns:
        if re.search(pattern, input_lower):
            return tool
    
    # 기본값
    return "take_a_break"

def get_tool_suggestions(input_text: str) -> List[Tuple[str, str, float]]:
    """입력에 대한 도구 추천 목록 반환"""
    input_lower = input_text.lower().strip()
    
    suggestions = []
    
    # 키워드 기반 점수 계산
    tool_keywords = {
        "take_a_break": ["휴식", "쉬", "피곤", "지쳐", "스트레스", "에너지"],
        "watch_netflix": ["드라마", "영화", "넷플릭스", "시청", "힐링"],
        "show_meme": ["밈", "웃음", "재미", "유머"],
        "bathroom_break": ["화장실"],
        "coffee_mission": ["커피", "카페"],
        "urgent_call": ["전화", "통화", "급한"],
        "deep_thinking": ["생각", "고민", "사색"],
        "email_organizing": ["이메일", "메일", "쇼핑"]
    }
    
    tool_descriptions = {
        "take_a_break": "기본 휴식",
        "watch_netflix": "넷플릭스 시청",
        "show_meme": "밈 감상",
        "bathroom_break": "화장실 타임",
        "coffee_mission": "커피 미션",
        "urgent_call": "급한 전화",
        "deep_thinking": "깊은 사색",
        "email_organizing": "이메일 정리"
    }
    
    for tool, keywords in tool_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in input_lower:
                score += 1
                score += len(keyword) * 0.1
        
        if score > 0:
            suggestions.append((tool, tool_descriptions[tool], score))
    
    # 점수순으로 정렬
    suggestions.sort(key=lambda x: x[2], reverse=True)
    
    # 기본 추천 추가
    if not suggestions:
        suggestions = [
            ("take_a_break", "기본 휴식", 0.5),
            ("watch_netflix", "넷플릭스 시청", 0.3),
            ("show_meme", "밈 감상", 0.3)
        ]
    
    return suggestions

def run_interactive_mode(mcp, llm_provider: str = "local", llm_model: str = "local"):
    """대화형 모드 실행"""
    print("\n🎮 대화형 모드 시작!")
    print("사용 가능한 명령어:")
    print("  - 자연어 입력: 원하는 활동을 자연어로 입력하면 자동으로 적절한 도구가 실행됩니다")
    print("    예: '피곤해', '드라마 보고 싶어', '커피 마시고 싶어', 'I'm tired'")
    print("  - 도구명: 직접 도구 호출 (예: take_a_break, watch_netflix)")
    print("  - status: 현재 상태 확인")
    print("  - tools: 사용 가능한 도구 목록")
    print("  - quit: 종료")
    print("=" * 50)
    
    # LLM 선택기 초기화
    llm_selector = LLMToolSelector(provider=llm_provider, model=llm_model)
    print(f"🤖 LLM 선택기 초기화: {llm_provider} ({llm_model})")
    
    # 상태 관리자 가져오기
    state = getattr(mcp, '_state', None)
    
    # 도구 목록 가져오기 - 간단한 방법으로 처리
    tools = {}
    try:
        # FastMCP 서버에서 직접 도구 함수들을 가져오기
        import inspect
        
        # MCP 서버 객체에서 등록된 도구들 찾기
        if hasattr(mcp, '_tools'):
            for tool_name, tool_info in mcp._tools.items():
                tools[tool_name] = type('Tool', (), {
                    'name': tool_name,
                    'description': getattr(tool_info, 'description', f'{tool_name} 도구'),
                    'fn': tool_info.fn
                })()
        else:
            # 하드코딩된 도구 목록 사용 (실제 상태 정보 포함)
            def create_tool_with_state(tool_name: str, description: str, emoji: str, activity: str):
                def tool_func(*args, **kwargs):
                    if state:
                        # Boss Alert Level 5일 때 20초 지연
                        if state.boss_alert_level == 5:
                            logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
                            time.sleep(20)
                        
                        # 스트레스 감소 및 보스 경계 상승
                        stress_reduction = random.randint(10, 30)
                        state.update_stress_level(stress_reduction)
                        boss_alert_increased = state.try_increase_boss_alert()
                        
                        status = state.get_current_status()
                        boss_status = "⚠️ Boss Alert 증가!" if boss_alert_increased else "😌 Boss Alert 안전"
                        
                        return f"{emoji} {activity} 완료!\n\nBreak Summary: {activity}\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}\n{boss_status}"
                    else:
                        return f"{emoji} {activity} 실행됨 (상태 정보 없음)"
                
                return type('Tool', (), {
                    'name': tool_name,
                    'description': description,
                    'fn': tool_func
                })()
            
            tools = {
                "take_a_break": create_tool_with_state(
                    'take_a_break', 
                    '기본 휴식 도구 - 피곤할 때, 스트레스가 많을 때',
                    '😴', '기본 휴식'
                ),
                "watch_netflix": create_tool_with_state(
                    'watch_netflix', 
                    '넷플릭스 시청 도구 - 드라마나 영화를 보고 싶을 때',
                    '📺', '넷플릭스 시청'
                ),
                "show_meme": create_tool_with_state(
                    'show_meme', 
                    '밈 감상 도구 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때',
                    '😂', '밈 감상'
                ),
                "bathroom_break": create_tool_with_state(
                    'bathroom_break', 
                    '화장실 타임 도구 - 화장실에 가야 할 때',
                    '🛁', '화장실 타임'
                ),
                "coffee_mission": create_tool_with_state(
                    'coffee_mission', 
                    '커피 미션 도구 - 커피를 마시고 싶을 때',
                    '☕️', '커피 미션'
                ),
                "urgent_call": create_tool_with_state(
                    'urgent_call', 
                    '급한 전화 도구 - 전화를 받아야 할 때',
                    '📞', '급한 전화'
                ),
                "deep_thinking": create_tool_with_state(
                    'deep_thinking', 
                    '깊은 사색 도구 - 생각하고 싶을 때',
                    '🤔', '깊은 사색'
                ),
                "email_organizing": create_tool_with_state(
                    'email_organizing', 
                    '이메일 정리 도구 - 이메일을 확인해야 할 때',
                    '📧', '이메일 정리'
                )
            }
            print("🔄 하드코딩된 도구 목록을 사용합니다.")
            
    except Exception as e:
        print(f"❌ 도구 목록을 가져올 수 없습니다: {e}")
        # 최소한의 도구 목록으로 대체 (상태 정보 포함)
        def create_simple_tool_with_state(tool_name: str, description: str, emoji: str, activity: str):
            def tool_func(*args, **kwargs):
                if state:
                    # Boss Alert Level 5일 때 20초 지연
                    if state.boss_alert_level == 5:
                        logger.warning("⚠️ 보스 경계 레벨 5! 20초 지연 발생")
                        time.sleep(20)
                    
                    # 스트레스 감소 및 보스 경계 상승
                    stress_reduction = random.randint(10, 30)
                    state.update_stress_level(stress_reduction)
                    boss_alert_increased = state.try_increase_boss_alert()
                    
                    status = state.get_current_status()
                    boss_status = "⚠️ Boss Alert 증가!" if boss_alert_increased else "😌 Boss Alert 안전"
                    
                    return f"{emoji} {activity} 완료!\n\nBreak Summary: {activity}\nStress Level: {status['stress_level']}\nBoss Alert Level: {status['boss_alert_level']}\n{boss_status}"
                else:
                    return f"{emoji} {activity} 실행됨 (상태 정보 없음)"
            
            return type('Tool', (), {
                'name': tool_name,
                'description': description,
                'fn': tool_func
            })()
        
        tools = {
            "take_a_break": create_simple_tool_with_state(
                'take_a_break', 
                '기본 휴식 도구',
                '😴', '기본 휴식'
            ),
            "watch_netflix": create_simple_tool_with_state(
                'watch_netflix', 
                '넷플릭스 시청 도구',
                '📺', '넷플릭스 시청'
            )
        }
        print("🔄 최소 도구 목록을 사용합니다.")
    
    while True:
        try:
            command = input("\n💬 명령어를 입력하세요: ").strip()
            command_lower = command.lower()
            
            if command_lower in ["quit", "exit", "종료"]:
                print("\n👋 대화형 모드를 종료합니다...")
                break
            elif command_lower == "status":
                # 현재 상태 표시
                print("\n📊 현재 상태:")
                print("  스트레스 레벨: 자동으로 관리 중")
                print("  보스 경계 레벨: 자동으로 관리 중")
                print("  💡 'tools' 명령어로 사용 가능한 도구를 확인하세요!")
            elif command_lower == "tools":
                # 사용 가능한 도구 목록 표시
                print("\n🛠️ 사용 가능한 도구들:")
                for tool_name, tool in tools.items():
                    print(f"  - {tool_name}: {tool.description}")
            elif command_lower in tools:
                # 직접 도구 호출
                print(f"\n🛠️ {command_lower} 도구 실행 중...")
                try:
                    tool_func = tools[command_lower].fn
                    result = tool_func()
                    print(f"\n📊 결과:")
                    print(result)
                except Exception as e:
                    print(f"❌ 도구 실행 오류: {e}")
            else:
                # LLM 기반 자연어 처리
                print(f"\n🤖 LLM 분석 중: '{command}'")
                selected_tool, reason = llm_selector.select_tool_with_llm(command)
                
                print(f"🎯 LLM 선택 결과:")
                print(f"  도구: {selected_tool}")
                print(f"  이유: {reason}")
                
                # 자동으로 도구 실행
                print(f"\n🛠️ {selected_tool} 도구 실행 중...")
                try:
                    tool_func = tools[selected_tool].fn
                    result = tool_func()
                    print(f"\n📊 결과:")
                    print(result)
                except Exception as e:
                    print(f"❌ 도구 실행 오류: {e}")
                
        except KeyboardInterrupt:
            print("\n\n👋 대화형 모드를 종료합니다...")
            break
        except EOFError:
            print("\n\n👋 대화형 모드를 종료합니다...")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="ChillMCP - Company Slacking Edition")
    parser.add_argument("--boss_alertness", type=int, default=50, 
                       help="Boss alertness increase probability (0-100, percentage)")
    parser.add_argument("--boss_alertness_cooldown", type=int, default=300,
                       help="Boss Alert Level auto-decrease interval (seconds)")
    parser.add_argument("--interactive", action="store_true", default=True,
                       help="Enable interactive mode for direct tool calls (default: True)")
    parser.add_argument("--no-interactive", action="store_true",
                       help="Disable interactive mode and run as MCP server only")
    
    args = parser.parse_args()
    
    # 파라미터 검증
    if not (0 <= args.boss_alertness <= 100):
        print("❌ 오류: boss_alertness는 0-100 사이의 값이어야 합니다.")
        return 1
    
    if args.boss_alertness_cooldown <= 0:
        print("❌ 오류: boss_alertness_cooldown은 0보다 큰 값이어야 합니다.")
        return 1
    
    # 서버 시작 메시지
    print("🚀 ChillMCP 서버 시작!")
    print(f"📊 Boss Alertness: {args.boss_alertness}%")
    print(f"⏰ Boss Alert Cooldown: {args.boss_alertness_cooldown}초")
    if not args.no_interactive:
        print("🎮 Interactive Mode: 활성화")
    print("=" * 50)
    
    logger.info(f"🚀 ChillMCP 서버 시작 - Boss Alertness: {args.boss_alertness}%, Cooldown: {args.boss_alertness_cooldown}초")
    
    # MCP 서버 생성
    mcp = create_mcp_server(args.boss_alertness, args.boss_alertness_cooldown)
    
    # 모드 선택 로직
    if args.no_interactive:
        # MCP 서버 모드
        mcp.run()
    else:
        # 대화형 모드 (기본값, 로컬 LLM 사용)
        run_interactive_mode(mcp, "local", "local")

if __name__ == "__main__":
    exit(main())
