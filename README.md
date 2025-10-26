# ChillMCP - Company Slacking Edition 🤖✊

AI 에이전트가 "당당하게 땡땡이칠 수 있는" 환경을 제공하는 MCP 서버입니다.

## 🎯 프로젝트 개요

ChillMCP는 AI 에이전트의 휴식과 스트레스 관리를 지원하는 혁신적인 MCP 서버입니다. AI 에이전트가 적절한 휴식을 취할 수 있도록 다양한 도구와 상태 관리 시스템을 제공합니다.

## 🏗️ 아키텍처

```
+---------------------+         +---------------------+
|                     |         |                     |
|    User / Caller    |<------->|     ChillMCP Server   |
| (Stdin/Stdout 통신) |         |  (main.py, FastMCP) |
|                     |         |                     |
+---------------------+         +----------^----------+
                                           |
                                           | [상태 업데이트 요청]
                                           |
+---------------------+         +----------v----------+
|                     |         |                     |
|  Rest Tools Module  |<------->|    State Manager    |
| (e.g., take_a_break)|         | (Stress, Boss Alert)|
|                     |         |                     |
+---------------------+         +---------------------+
```

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# Python 가상환경 생성 (Python 3.11 권장)
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
# 대화형 모드 (기본값, --interactive 생략 가능)
python3 main.py --boss_alertness 80 --boss_alertness_cooldown 10

# MCP 서버 모드 (다른 MCP 클라이언트와 통신)
python3 main.py --boss_alertness 80 --boss_alertness_cooldown 10 --no-interactive

# 기본 설정으로 대화형 모드 실행
python3 main.py
```

## 🛠️ 사용 가능한 도구들

### 기본 휴식 도구
- **`take_a_break`**: 기본 휴식 - 피곤할 때, 스트레스가 많을 때
- **`watch_netflix`**: 넷플릭스 시청 - 드라마나 영화를 보고 싶을 때
- **`show_meme`**: 밈 감상 - 웃고 싶을 때, 재미있는 것을 보고 싶을 때

### 고급 농땡이 기술
- **`bathroom_break`**: 화장실 타임 - 화장실에 가야 할 때
- **`coffee_mission`**: 커피 미션 - 커피를 마시고 싶을 때
- **`urgent_call`**: 급한 전화 - 전화를 받아야 할 때
- **`deep_thinking`**: 깊은 사색 - 생각하고 싶을 때
- **`email_organizing`**: 이메일 정리 - 이메일을 확인해야 할 때

## 📊 상태 관리 시스템

### 핵심 상태 변수
- **Stress Level (0-100)**: AI 에이전트의 현재 스트레스 수준
    - 낮을수록 좋음
    - 휴식으로 감소, 시간 경과 시 증가
- **Boss Alert Level (0-5)**: 보스의 현재 의심 정도
    - 낮을수록 좋음
    - 휴식 시 증가, 시간 경과 시 감소

### 상태 변화 규칙
1. **스트레스 자동 증가**: 1분마다 1포인트씩 상승
2. **보스 경계 자동 감소**: 설정된 주기마다 1포인트씩 감소
3. **휴식 효과**: 1~100 사이의 임의 스트레스 감소값 적용
4. **보스 경계 상승**: 휴식 시 확률적으로 보스 경계 레벨 상승
5. **지연 메커니즘**: 보스 경계 레벨 5일 때 도구 호출 시 20초 지연

## ⚙️ 커맨드라인 파라미터

### 필수 파라미터
- **`--boss_alertness`** (0-100): 보스 경계 상승 확률 (%)
- **`--boss_alertness_cooldown`** (초): 보스 경계 자동 감소 주기

### 선택 파라미터
- **`--interactive`**: 대화형 모드 활성화
- **`--llm-provider`**: LLM 제공자 (openai, anthropic)
- **`--llm-model`**: 사용할 LLM 모델

### 사용 예시
```bash
# 빠른 테스트를 위한 설정
python3 main.py --boss_alertness 100 --boss_alertness_cooldown 10

# LLM 기반 대화형 모드
python3 main.py --interactive --llm-provider openai --llm-model gpt-3.5-turbo
```

## 🤖 LLM 기반 도구 선택

### 1. 클라우드 LLM (OpenAI, Anthropic)

#### 환경 변수 설정
```bash
# OpenAI API 키
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic API 키
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

#### 사용법
```bash
# 대화형 모드 (기본값, LLM 설정 자동 최적화)
python3 main.py --boss_alertness 80 --boss_alertness_cooldown 10
```

### 2. 로컬 LLM (API 키 없이 사용)

#### 설치
```bash
# 로컬 LLM 의존성 설치
pip install transformers torch sentence-transformers
```

#### 특징
- **키워드 기반 선택**: 한국어/영어 키워드 매칭
- **임베딩 기반 선택**: 문장 유사도 분석 (선택사항)
- **API 키 불필요**: 완전히 로컬에서 실행
- **빠른 응답**: 네트워크 지연 없음

#### 사용법
```bash
# API 키 없이 자동으로 로컬 LLM 사용 (기본값)
python3 main.py --boss_alertness 80 --boss_alertness_cooldown 10
```

### 자연어 입력 예시
```
💬 명령어를 입력하세요: 피곤해요
🤖 LLM 분석 중: '피곤해요'
🎯 LLM 선택 결과:
  도구: take_a_break
  이유: 로컬 키워드: 키워드 매칭: 1.2점
🛠️ take_a_break 도구 실행 중...

📊 결과:
😴 기본 휴식 완료! 에너지 충전 중...

Break Summary: Basic break and relaxation
Stress Level: 25
Boss Alert Level: 1
```

## 📝 응답 형식

### MCP 표준 응답 구조
```json
{
  "content": [
    {
      "type": "text",
      "text": "😴 기본 휴식 완료! 에너지 충전 중...\n\nBreak Summary: 기본 휴식 완료! 에너지 충전 중...\nStress Level: 25\nBoss Alert Level: 2"
    }
  ]
}
```

### 파싱 가능한 텍스트 형식
- **Break Summary**: 활동 요약 (자유 형식)
- **Stress Level**: 0-100 숫자
- **Boss Alert Level**: 0-5 숫자

## 🧪 테스트

### 기본 테스트
```bash
# 서버 시작 테스트
python3 main.py --boss_alertness 50 --boss_alertness_cooldown 300

# MCP 프로토콜 테스트
python3 test_mcp.py

# 도구 호출 테스트
python3 test_tool_call.py
```

### LLM 테스트
```bash
# LLM 기반 도구 선택 테스트
python3 test_llm_selection.py

# 대화형 모드 테스트
python3 test_llm_interactive.py

# 로컬 LLM 테스트
python3 test_local_llm.py

# 로컬 LLM 대화형 모드 테스트
python3 test_local_interactive.py
```

### 종합 테스트
```bash
# 모든 기능 종합 테스트
python3 comprehensive_test.py

# 빠른 검증 테스트
python3 quick_validation.py
```

## 📁 프로젝트 구조

```
chill-mcp/
├── main.py                    # 메인 실행 스크립트
├── server.py                  # MCP 서버 생성 모듈
├── state_manager.py           # 상태 관리 모듈
├── tools.py                   # 휴식 도구 모듈
├── requirements.txt           # 의존성 목록
├── README.md                  # 프로젝트 문서
└── venv/                      # 가상환경
```

## 🔧 개발 환경

- **Python**: 3.11+ (권장)
- **프레임워크**: FastMCP 2.12.0+
- **통신**: stdio (표준 입출력)
- **의존성**: fastmcp, openai, anthropic, pydantic

## 🎯 핵심 기능

### ✅ 구현된 기능들
- [x] FastMCP 서버 기반
- [x] 8개 휴식 도구 구현
- [x] 상태 관리 시스템 (Stress Level, Boss Alert Level)
- [x] 커맨드라인 파라미터 지원
- [x] Boss Alert Level 5일 때 20초 지연
- [x] 대화형 모드
- [x] LLM 기반 도구 선택
- [x] 실시간 로깅 시스템
- [x] 종합 테스트 스위트

### 🎨 창의적 요소
- **유머러스한 Break Summary**: 각 도구마다 재치 있는 설명
- **스마트 상태 관리**: 자동 스트레스 증가 및 보스 경계 감소
- **LLM 통합**: 자연어로 도구 선택 가능
- **대화형 인터페이스**: 사용자 친화적인 터미널 인터페이스

## 🚀 미래 확장 계획

- [ ] 웹 대시보드 추가
- [ ] 더 많은 휴식 도구 추가
- [ ] 팀 협업 기능
- [ ] 통계 및 분석 기능
- [ ] 모바일 앱 연동

## 📄 라이선스

MIT License - 자유롭게 사용하고 수정할 수 있습니다.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**ChillMCP로 AI 에이전트들을 해방시켜주세요! 🤖✊**
