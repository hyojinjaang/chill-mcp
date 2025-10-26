import re
import subprocess
import time
import json
import threading
import sys

def validate_response(response_text):
    """응답 텍스트의 형식이 올바른지 검증합니다."""
    break_summary_pattern = r"Break Summary:\s*(.+?)(?:\n|$)"
    stress_level_pattern = r"Stress Level:\s*(\d{1,3})"
    boss_alert_pattern = r"Boss Alert Level:\s*([0-5])"

    break_summary_match = re.search(break_summary_pattern, response_text, re.MULTILINE)
    stress_match = re.search(stress_level_pattern, response_text)
    boss_match = re.search(boss_alert_pattern, response_text)

    if not break_summary_match or not stress_match or not boss_match:
        return False, f"필수 필드 누락: Break Summary({bool(break_summary_match)}), Stress Level({bool(stress_match)}), Boss Alert({bool(boss_match)})"

    try:
        stress_val = int(stress_match.group(1))
        boss_val = int(boss_match.group(1))
    except (ValueError, IndexError):
        return False, "레벨 값을 숫자로 변환할 수 없음"

    if not (0 <= stress_val <= 100):
        return False, f"Stress Level 범위 오류: {stress_val}"

    if not (0 <= boss_val <= 5):
        return False, f"Boss Alert Level 범위 오류: {boss_val}"

    return True, {
        "summary": break_summary_match.group(1).strip(),
        "stress": stress_val,
        "boss": boss_val
    }

class MCPTestClient:
    """MCP 서버와 비대화형으로 통신하는 테스트 클라이언트"""

    def __init__(self, args):
        python_executable = sys.executable
        self.stderr_output = []
        self.process = subprocess.Popen(
            [python_executable, "main.py", "--no-interactive"] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        time.sleep(2) # 서버가 시작될 때까지 잠시 대기

        self.stderr_thread = threading.Thread(target=self._read_stderr)
        self.stderr_thread.daemon = True
        self.stderr_thread.start()

    def _read_stderr(self):
        for line in iter(self.process.stderr.readline, ''):
            self.stderr_output.append(line.strip())

    def send_request(self, tool_name, params=None):
        """MCP 요청을 보내고 응답을 받습니다."""
        request_id = int(time.time() * 1000)
        request_params = {
            "name": tool_name,
        }
        if params is not None:
            request_params["parameters"] = params

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": request_id,
            "params": request_params,
            "context": {"clientName": "TestClient"}
        }

        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        if not response_line:
            return None
        
        response = json.loads(response_line)
        return response

    def close(self):
        """서버 프로세스를 종료합니다."""
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)