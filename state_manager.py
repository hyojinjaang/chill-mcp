import time
import threading
import random
import logging

logger = logging.getLogger(__name__)

class ChillMCPState:
    """농땡이 상태 관리 클래스"""

    def __init__(self, boss_alertness: int = 50, boss_alertness_cooldown: int = 300):
        self.stress_level = 50
        self.boss_alert_level = 0
        self.boss_alertness = boss_alertness
        self.boss_alertness_cooldown = boss_alertness_cooldown
        self.last_stress_increase = time.time()
        self.last_boss_alert_decrease = time.time()
        self._lock = threading.Lock()

        self._start_boss_alert_cooldown_thread()
        self._start_stress_increase_thread()

    def _start_boss_alert_cooldown_thread(self):
        """Boss Alert Level 자동 감소를 위한 백그라운드 스레드"""
        def cooldown_worker():
            while True:
                time.sleep(1)
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
                time.sleep(60)
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
