"""
동영상 플레이어 모듈
동영상 재생, 상태 확인, 다음 영상 이동 등을 담당합니다.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VideoPlayer:
    def __init__(self, driver, log_callback=None):
        """
        동영상 플레이어 초기화
        
        Args:
            driver: Selenium WebDriver 인스턴스
            log_callback (function): 로그 출력 콜백 함수
        """
        self.driver = driver
        self.log_callback = log_callback
        
    def log(self, message):
        """로그 출력"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def wait_for_video_ready(self, timeout=60):
        """영상 플레이어를 찾고 재생 준비"""
        self.log("🎬 영상 플레이어 찾는 중...")
        try:
            # 페이지 로딩 대기
            self.log("⏳ 페이지 완전 로딩 대기 중... (5초)")
            time.sleep(5)
            
            # 현재 페이지 정보 출력
            self.log(f"🔍 현재 URL: {self.driver.current_url}")
            self.log(f"🔍 페이지 제목: {self.driver.title}")
            
            # Video.js에서 실제 video 태그 찾기 (우선순위 순)
            video_selectors = [
                "#myvideo video",     # Video.js 컨테이너 내부의 실제 video
                "#myvideo .vjs-tech", # Video.js 기술 레이어
                ".vjs-tech",          # Video.js 기술 레이어 (일반)
                "video",              # HTML5 video 태그 (일반)
                "#myvideo",           # Video.js 컨테이너 (마지막 시도)
                "iframe",             # iframe 내부 영상
                ".video-player",      # 일반적인 비디오 플레이어 클래스
                "[class*='video']",   # video가 포함된 클래스
                "[id*='video']",      # video가 포함된 ID
            ]
            
            actual_video = None
            container = None
            
            for selector in video_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            # video 태그인지 확인
                            tag_name = elem.tag_name.lower()
                            if tag_name == "video":
                                actual_video = elem
                                self.log(f"✅ 실제 video 태그 발견: {selector}")
                                break
                            else:
                                container = elem
                                self.log(f"📦 영상 컨테이너 발견: {selector} (태그: {tag_name})")
                    if actual_video:
                        break
                except:
                    continue
            
            # 실제 video 태그를 우선 사용, 없으면 컨테이너 사용
            video_element = actual_video or container
            
            if not video_element:
                self.log("❌ 영상 요소를 찾을 수 없습니다.")
                return None, None
            
            # 영상 재생 시작 시도
            self.log("▶️ 영상 재생 시작 시도...")
            
            # 방법 1: 실제 video 태그에 play() 호출
            if actual_video:
                try:
                    self.driver.execute_script("arguments[0].play()", actual_video)
                    self.log("✅ video.play() 성공!")
                    time.sleep(2)
                    return actual_video, None
                except Exception as e:
                    self.log(f"⚠️ video.play() 실패: {str(e)}")
            
            # 방법 2: Video.js API 사용
            try:
                result = self.driver.execute_script("""
                    var player = videojs('myvideo');
                    if (player && typeof player.play === 'function') {
                        player.play();
                        return 'videojs.play() 성공';
                    }
                    return 'Video.js 플레이어를 찾을 수 없음';
                """)
                self.log(f"🎮 Video.js API 시도: {result}")
                if "성공" in result:
                    time.sleep(2)
                    return video_element, None
            except Exception as e:
                self.log(f"⚠️ Video.js API 실패: {str(e)}")
            
            # 방법 3: 재생 버튼 클릭
            try:
                play_buttons = [
                    ".vjs-big-play-button",  # Video.js 큰 재생 버튼
                    ".vjs-play-control",     # Video.js 재생 컨트롤
                    ".play-button",          # 일반적인 재생 버튼
                    "#myvideo .vjs-big-play-button"  # myvideo 내부 재생 버튼
                ]
                
                for btn_selector in play_buttons:
                    try:
                        play_btn = self.driver.find_element(By.CSS_SELECTOR, btn_selector)
                        if play_btn.is_displayed():
                            play_btn.click()
                            self.log(f"✅ 재생 버튼 클릭 성공: {btn_selector}")
                            time.sleep(2)
                            return video_element, None
                    except:
                        continue
            except Exception as e:
                self.log(f"⚠️ 재생 버튼 클릭 실패: {str(e)}")
            
            # 방법 4: 영상 영역 직접 클릭
            try:
                video_element.click()
                self.log("✅ 영상 영역 클릭으로 재생 시도")
                time.sleep(2)
                return video_element, None
            except Exception as e:
                self.log(f"⚠️ 영상 영역 클릭 실패: {str(e)}")
            
            self.log("⚠️ 자동 재생 실패. 수동으로 재생을 시작해주세요.")
            return video_element, None
            
        except Exception as e:
            self.log(f"❌ 영상 준비 실패: {str(e)}")
            return None, None
    
    def get_video_progress(self, video_element):
        """현재 영상 재생 상태 확인"""
        try:
            current_time = self.driver.execute_script("return arguments[0].currentTime", video_element)
            duration = self.driver.execute_script("return arguments[0].duration", video_element)
            paused = self.driver.execute_script("return arguments[0].paused", video_element)
            ended = self.driver.execute_script("return arguments[0].ended", video_element)
            
            return {
                'current_time': current_time,
                'duration': duration,
                'paused': paused,
                'ended': ended,
                'progress': (current_time / duration * 100) if duration else 0
            }
        except Exception as e:
            self.log(f"⚠️ 영상 상태 확인 실패: {str(e)}")
            return None
    
    def start_video_if_paused(self, video_element):
        """영상이 멈춰있으면 재생 시작"""
        try:
            status = self.get_video_progress(video_element)
            if status and status['paused'] and not status['ended']:
                self.log("▶️ 영상 재생 시작...")
                self.driver.execute_script("arguments[0].play()", video_element)
                time.sleep(2)
        except Exception as e:
            self.log(f"⚠️ 영상 재생 시작 실패: {str(e)}")
    
    def wait_for_video_end(self, video_element, log_queue=None):
        """영상이 끝날 때까지 대기 (실시간 길이 체크)"""
        self.log("⏰ 영상 재생 모니터링 시작... (길이는 실시간으로 확인)")
        
        start_time = time.time()
        last_progress = 0
        stuck_count = 0
        duration = None
        
        while True:
            try:
                status = self.get_video_progress(video_element)
                
                if not status:
                    self.log("⚠️ 영상 상태 확인 불가")
                    time.sleep(5)
                    continue
                
                current_progress = status['progress']
                current_time = status['current_time']
                current_duration = status['duration']
                
                # 영상 길이가 처음 로드되면 표시
                if current_duration and not duration:
                    duration = current_duration
                    self.log(f"📏 영상 길이 확인: {duration:.1f}초")
                
                # 영상 종료 확인 (100% + 10초 버퍼)
                if status['ended']:
                    self.log("✅ 영상 재생 완료! (ended 이벤트)")
                    return True
                elif current_progress >= 100 and current_progress > 0:
                    # 100% 도달 후 10초 버퍼 대기
                    if not hasattr(self, '_buffer_start_time'):
                        self._buffer_start_time = time.time()
                        self.log(f"🎯 영상 100% 도달! 10초 버퍼 대기 중...")
                    
                    buffer_elapsed = time.time() - self._buffer_start_time
                    if buffer_elapsed >= 10:
                        self.log("✅ 영상 재생 완료! (100% + 10초 버퍼)")
                        self._buffer_start_time = None  # 리셋
                        return True
                else:
                    # 100% 미만이면 버퍼 타이머 리셋
                    if hasattr(self, '_buffer_start_time'):
                        self._buffer_start_time = None
                
                # 영상이 멈춰있는지 확인
                if status['paused'] and current_time > 1:  # 1초 이후에만 체크
                    self.log("⏸️ 영상이 일시정지됨. 재생 재시작...")
                    self.start_video_if_paused(video_element)
                
                # 진행률 업데이트 (길이가 있을 때만)
                if current_progress - last_progress > 1 and current_progress > 0:
                    if duration:
                        self.log(f"📈 재생 진행률: {current_progress:.1f}% ({current_time:.1f}/{duration:.1f}초)")
                    else:
                        self.log(f"📈 재생 중: {current_time:.1f}초 (총 길이 로딩 중...)")
                    last_progress = current_progress
                    stuck_count = 0
                    
                    # GUI 진행률 바 업데이트를 위한 신호 전송
                    if log_queue:
                        try:
                            log_queue.put(f"PROGRESS_UPDATE:{current_progress:.1f}")
                        except:
                            pass
                else:
                    stuck_count += 1
                
                # 영상이 너무 오랫동안 멈춰있으면 강제 진행
                if stuck_count > 15:  # 15번 (45초) 체크 후 포기
                    self.log("⚠️ 영상이 멈춰있거나 로드되지 않습니다. 다음 영상으로 이동...")
                    return False
                
                # 최대 대기 시간 초과 확인 (30분)
                elapsed = time.time() - start_time
                max_wait = (duration * 1.5 + 120) if duration else 1800  # 영상길이*1.5+2분 또는 최대 30분
                if elapsed > max_wait:
                    self.log(f"⏰ 최대 대기 시간({max_wait/60:.1f}분) 초과. 다음 영상으로 이동...")
                    return False
                
                time.sleep(3)  # 3초마다 확인
                
            except Exception as e:
                self.log(f"⚠️ 대기 중 오류: {str(e)}")
                time.sleep(5)
                continue
    
    def click_next_video(self):
        """다음 영상 버튼 클릭"""
        self.log("⏭️ 다음 영상으로 이동 중...")
        
        try:
            # 다음 영상 버튼 찾기
            selectors = [
                ".btn-next-page",  # 클래스 기반
                "//a[contains(text(), '다음영상')]",  # 텍스트 기반
                "//a[contains(@class, 'btn-next-page')]"  # XPath 기반
            ]
            
            next_button = None
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        next_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if next_button and next_button.is_displayed():
                        break
                        
                except NoSuchElementException:
                    continue
            
            if not next_button:
                self.log("❌ 다음 영상 버튼을 찾을 수 없습니다.")
                return False
            
            # 버튼 정보 확인
            button_text = next_button.text.strip()
            onclick = next_button.get_attribute('onclick')
            
            self.log(f"🎯 다음 버튼 발견: '{button_text}' (onclick: {onclick})")
            
            # 스크롤해서 버튼이 보이도록 함
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            # 버튼 클릭
            next_button.click()
            self.log("✅ 다음 영상 버튼 클릭 성공!")
            
            # 페이지 로딩 대기
            time.sleep(5)
            return True
            
        except Exception as e:
            self.log(f"❌ 다음 영상 이동 실패: {str(e)}")
            return False
    
    def handle_alerts(self):
        """알림창 처리"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.log(f"🚨 알림창 감지: '{alert_text}'")
            alert.accept()
            time.sleep(2)
            return True
        except:
            return False
