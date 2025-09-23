"""
KT EDU 자동재생 스크립트
분석 결과를 바탕으로 영상을 자동으로 재생하고 다음 영상으로 이동합니다.
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
import os

class KTEduAutoPlayer:
    def __init__(self, headless=False, log_queue=None):
        """
        스마트 학습 도우미 초기화
        
        Args:
            headless (bool): 브라우저를 숨김 모드로 실행할지 여부
            log_queue: GUI로 로그를 전달할 큐
        """
        self.driver = None
        self.headless = headless
        self.log_queue = log_queue  # GUI로 로그 전달용 큐
        self.video_count = 0
        self.max_videos = 100  # 최대 학습할 강의 수 (무한루프 방지)
        
    def log_print(self, message):
        """로그 출력 함수 - GUI와 터미널 모두에 출력"""
        # GUI로 로그 전달
        if self.log_queue:
            try:
                self.log_queue.put(message)
            except:
                pass
        
        # 터미널에도 출력 (Windows 호환성을 위해 인코딩 처리)
        try:
            # Windows 환경에서 안전한 출력
            import sys
            import os
            
            # Windows에서는 cp949 인코딩 사용
            if os.name == 'nt':
                try:
                    # 이모지 문자를 안전한 문자로 변환
                    safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
                    # 이모지를 제거하거나 대체
                    safe_message = safe_message.replace('🚀', '[시작]').replace('✅', '[완료]').replace('❌', '[오류]')
                    print(safe_message, flush=True)
                except:
                    # 인코딩 실패 시 이모지 제거
                    import re
                    safe_message = re.sub(r'[^\x00-\x7F]+', '[이모지]', message)
                    print(safe_message, flush=True)
            else:
                print(message, flush=True)
        except:
            # 모든 출력 실패 시 기본 메시지
            print("로그 메시지 출력됨", flush=True)
        
    def setup_driver(self):
        """Chrome 드라이버 설정 및 초기화"""
        self.log_print("🔧 ChromeDriver 설정 시작...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            self.log_print("👻 헤드리스 모드 활성화")
        
        # 일반적인 브라우저처럼 보이게 설정
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent 설정
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        
        # Wine 환경에서 Chrome 경로 설정
        import os
        if os.name == 'nt':  # Windows 환경 (Wine 포함)
            # Wine 환경에서 Chrome 경로 찾기
            possible_chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USER', '')),
            ]
            
            chrome_found = False
            for chrome_path in possible_chrome_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    self.log_print(f"✅ Chrome 경로 설정: {chrome_path}")
                    chrome_found = True
                    break
            
            if not chrome_found:
                self.log_print("⚠️ Chrome을 찾을 수 없습니다. Wine 환경에 Chrome을 설치해주세요.")
                self.log_print("💡 해결방법: wine chrome_installer.exe 실행하여 Chrome 설치")
        
        self.log_print("✅ Chrome 옵션 설정 완료")
        
        # 실행파일인지 확인하여 chromedriver 경로 설정
        if getattr(sys, 'frozen', False):
            # 실행파일인 경우: 임시 디렉토리에서 chromedriver 찾기
            import tempfile
            import shutil
            
            self.log_print("🔍 실행파일 모드에서 ChromeDriver 경로 설정 중...")
            
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            chromedriver_path = os.path.join(temp_dir, "chromedriver")
            self.log_print(f"📁 임시 디렉토리: {temp_dir}")
            
            # 실행파일 내부의 chromedriver를 임시 디렉토리로 복사
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller로 빌드된 경우
                source_path = os.path.join(sys._MEIPASS, "chromedriver_140")
                self.log_print(f"📂 PyInstaller _MEIPASS: {sys._MEIPASS}")
            else:
                # 일반적인 경우
                source_path = "./chromedriver_140"
                self.log_print(f"📂 일반 경로: {source_path}")
            
            self.log_print(f"🔍 ChromeDriver 소스 경로: {source_path}")
            self.log_print(f"📋 소스 파일 존재 여부: {os.path.exists(source_path)}")
            
            if os.path.exists(source_path):
                try:
                    shutil.copy2(source_path, chromedriver_path)
                    os.chmod(chromedriver_path, 0o755)
                    self.log_print(f"✅ ChromeDriver 복사 완료: {chromedriver_path}")
                except Exception as e:
                    self.log_print(f"❌ ChromeDriver 복사 실패: {str(e)}")
                    raise
            else:
                # _MEIPASS 디렉토리 내용 확인
                if hasattr(sys, '_MEIPASS'):
                    try:
                        meipass_contents = os.listdir(sys._MEIPASS)
                        self.log_print(f"📋 _MEIPASS 디렉토리 내용: {meipass_contents}")
                    except:
                        self.log_print("❌ _MEIPASS 디렉토리 접근 실패")
                
                raise FileNotFoundError(f"ChromeDriver를 찾을 수 없습니다: {source_path}")
        else:
            # 개발 환경인 경우
            chromedriver_path = os.path.join(os.getcwd(), 'chromedriver_140')
            self.log_print(f"🔍 개발 환경 ChromeDriver 경로: {chromedriver_path}")
            
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(f"ChromeDriver를 찾을 수 없습니다: {chromedriver_path}")
            
            # 실행 권한 확인 및 설정
            if not os.access(chromedriver_path, os.X_OK):
                os.chmod(chromedriver_path, 0o755)
                self.log_print("✅ ChromeDriver 실행 권한 설정 완료")
        
        try:
            self.log_print(f"🚀 ChromeDriver 서비스 시작: {chromedriver_path}")
            service = Service(chromedriver_path)
            
            self.log_print("🌐 Chrome 브라우저 시작 중...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.log_print("✅ Chrome 브라우저 시작 완료!")
            
            # 자동화 탐지 회피
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log_print("🛡️ 자동화 탐지 회피 설정 완료")
            
            return self.driver
            
        except Exception as e:
            self.log_print(f"❌ ChromeDriver 실행 실패: {str(e)}")
            self.log_print(f"📋 ChromeDriver 경로: {chromedriver_path}")
            self.log_print(f"📋 파일 존재 여부: {os.path.exists(chromedriver_path)}")
            if os.path.exists(chromedriver_path):
                self.log_print(f"📋 파일 권한: {oct(os.stat(chromedriver_path).st_mode)}")
            raise
    
    def wait_for_video_ready(self, timeout=60):
        """영상 플레이어를 찾고 재생 준비"""
        self.log_print("🎬 영상 플레이어 찾는 중...")
        try:
            # 페이지 로딩 대기
            self.log_print("⏳ 페이지 완전 로딩 대기 중... (5초)")
            time.sleep(5)
            
            # 현재 페이지 정보 출력
            self.log_print(f"🔍 현재 URL: {self.driver.current_url}")
            self.log_print(f"🔍 페이지 제목: {self.driver.title}")
            
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
                                self.log_print(f"✅ 실제 video 태그 발견: {selector}")
                                break
                            else:
                                container = elem
                                self.log_print(f"📦 영상 컨테이너 발견: {selector} (태그: {tag_name})")
                    if actual_video:
                        break
                except:
                    continue
            
            # 실제 video 태그를 우선 사용, 없으면 컨테이너 사용
            video_element = actual_video or container
            
            if not video_element:
                self.log_print("❌ 영상 요소를 찾을 수 없습니다.")
                return None, None
            
            # 영상 재생 시작 시도
            self.log_print("▶️ 영상 재생 시작 시도...")
            
            # 방법 1: 실제 video 태그에 play() 호출
            if actual_video:
                try:
                    self.driver.execute_script("arguments[0].play()", actual_video)
                    self.log_print("✅ video.play() 성공!")
                    time.sleep(2)
                    return actual_video, None
                except Exception as e:
                    self.log_print(f"⚠️ video.play() 실패: {str(e)}")
            
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
                self.log_print(f"🎮 Video.js API 시도: {result}")
                if "성공" in result:
                    time.sleep(2)
                    return video_element, None
            except Exception as e:
                self.log_print(f"⚠️ Video.js API 실패: {str(e)}")
            
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
                            self.log_print(f"✅ 재생 버튼 클릭 성공: {btn_selector}")
                            time.sleep(2)
                            return video_element, None
                    except:
                        continue
            except Exception as e:
                self.log_print(f"⚠️ 재생 버튼 클릭 실패: {str(e)}")
            
            # 방법 4: 영상 영역 직접 클릭
            try:
                video_element.click()
                self.log_print("✅ 영상 영역 클릭으로 재생 시도")
                time.sleep(2)
                return video_element, None
            except Exception as e:
                self.log_print(f"⚠️ 영상 영역 클릭 실패: {str(e)}")
            
            self.log_print("⚠️ 자동 재생 실패. 수동으로 재생을 시작해주세요.")
            return video_element, None
            
        except Exception as e:
            self.log_print(f"❌ 영상 준비 실패: {str(e)}")
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
            self.log_print(f"⚠️ 영상 상태 확인 실패: {str(e)}")
            return None
    
    def start_video_if_paused(self, video_element):
        """영상이 멈춰있으면 재생 시작"""
        try:
            status = self.get_video_progress(video_element)
            if status and status['paused'] and not status['ended']:
                self.log_print("▶️ 영상 재생 시작...")
                self.driver.execute_script("arguments[0].play()", video_element)
                time.sleep(2)
        except Exception as e:
            self.log_print(f"⚠️ 영상 재생 시작 실패: {str(e)}")
    
    def wait_for_video_end(self, video_element):
        """영상이 끝날 때까지 대기 (실시간 길이 체크)"""
        self.log_print("⏰ 영상 재생 모니터링 시작... (길이는 실시간으로 확인)")
        
        start_time = time.time()
        last_progress = 0
        stuck_count = 0
        duration = None
        
        while True:
            try:
                status = self.get_video_progress(video_element)
                
                if not status:
                    self.log_print("⚠️ 영상 상태 확인 불가")
                    time.sleep(5)
                    continue
                
                current_progress = status['progress']
                current_time = status['current_time']
                current_duration = status['duration']
                
                # 영상 길이가 처음 로드되면 표시
                if current_duration and not duration:
                    duration = current_duration
                    self.log_print(f"📏 영상 길이 확인: {duration:.1f}초")
                
                # 영상 종료 확인 (100% + 10초 버퍼)
                if status['ended']:
                    self.log_print("✅ 영상 재생 완료! (ended 이벤트)")
                    return True
                elif current_progress >= 100 and current_progress > 0:
                    # 100% 도달 후 10초 버퍼 대기
                    if not hasattr(self, '_buffer_start_time'):
                        self._buffer_start_time = time.time()
                        self.log_print(f"🎯 영상 100% 도달! 10초 버퍼 대기 중...")
                    
                    buffer_elapsed = time.time() - self._buffer_start_time
                    if buffer_elapsed >= 10:
                        self.log_print("✅ 영상 재생 완료! (100% + 10초 버퍼)")
                        self._buffer_start_time = None  # 리셋
                        return True
                else:
                    # 100% 미만이면 버퍼 타이머 리셋
                    if hasattr(self, '_buffer_start_time'):
                        self._buffer_start_time = None
                
                # 영상이 멈춰있는지 확인
                if status['paused'] and current_time > 1:  # 1초 이후에만 체크
                    self.log_print("⏸️ 영상이 일시정지됨. 재생 재시작...")
                    self.start_video_if_paused(video_element)
                
                # 진행률 업데이트 (길이가 있을 때만)
                if current_progress - last_progress > 1 and current_progress > 0:
                    if duration:
                        self.log_print(f"📈 재생 진행률: {current_progress:.1f}% ({current_time:.1f}/{duration:.1f}초)")
                    else:
                        self.log_print(f"📈 재생 중: {current_time:.1f}초 (총 길이 로딩 중...)")
                    last_progress = current_progress
                    stuck_count = 0
                    
                    # GUI 진행률 바 업데이트를 위한 신호 전송
                    if self.log_queue:
                        try:
                            self.log_queue.put(f"PROGRESS_UPDATE:{current_progress:.1f}")
                        except:
                            pass
                else:
                    stuck_count += 1
                
                # 영상이 너무 오랫동안 멈춰있으면 강제 진행
                if stuck_count > 15:  # 15번 (45초) 체크 후 포기
                    self.log_print("⚠️ 영상이 멈춰있거나 로드되지 않습니다. 다음 영상으로 이동...")
                    return False
                
                # 최대 대기 시간 초과 확인 (30분)
                elapsed = time.time() - start_time
                max_wait = (duration * 1.5 + 120) if duration else 1800  # 영상길이*1.5+2분 또는 최대 30분
                if elapsed > max_wait:
                    self.log_print(f"⏰ 최대 대기 시간({max_wait/60:.1f}분) 초과. 다음 영상으로 이동...")
                    return False
                
                time.sleep(3)  # 3초마다 확인
                
            except Exception as e:
                self.log_print(f"⚠️ 대기 중 오류: {str(e)}")
                time.sleep(5)
                continue
    
    def click_next_video(self):
        """다음 영상 버튼 클릭"""
        self.log_print("⏭️ 다음 영상으로 이동 중...")
        
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
                self.log_print("❌ 다음 영상 버튼을 찾을 수 없습니다.")
                return False
            
            # 버튼 정보 확인
            button_text = next_button.text.strip()
            onclick = next_button.get_attribute('onclick')
            
            self.log_print(f"🎯 다음 버튼 발견: '{button_text}' (onclick: {onclick})")
            
            # 스크롤해서 버튼이 보이도록 함
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            # 버튼 클릭
            next_button.click()
            self.log_print("✅ 다음 영상 버튼 클릭 성공!")
            
            # 페이지 로딩 대기
            time.sleep(5)
            return True
            
        except Exception as e:
            self.log_print(f"❌ 다음 영상 이동 실패: {str(e)}")
            return False
    
    def handle_alerts(self):
        """알림창 처리"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.log_print(f"🚨 알림창 감지: '{alert_text}'")
            alert.accept()
            time.sleep(2)
            return True
        except:
            return False
    
    def play_videos_automatically(self, start_url=None, max_videos=None):
        """영상 자동재생 시작"""
        if max_videos:
            self.max_videos = max_videos
            
        self.log_print("🚀 스마트 학습을 시작합니다!")
        self.log_print(f"📊 최대 학습 강의 수: {self.max_videos}개")
        
        try:
            # 드라이버가 초기화되지 않았다면 초기화
            if not self.driver:
                self.log_print("🔧 드라이버 초기화 중...")
                self.setup_driver()
            
            if start_url:
                self.log_print(f"📱 시작 URL로 이동: {start_url}")
                self.driver.get(start_url)
                self.log_print("⏳ 페이지 로딩 대기 중... (5초)")
                time.sleep(5)
                self.log_print(f"🔍 페이지 로딩 완료, 현재 URL: {self.driver.current_url}")
                self.log_print(f"🔍 페이지 제목: {self.driver.title}")
                self.log_print("🔐 브라우저에서 로그인을 완료한 후 GUI의 '로그인 완료' 버튼을 클릭하세요!")
                self.log_print("⏳ 로그인 완료 대기 중... (무기한 대기)")
                return  # 로그인 완료를 기다리기 위해 여기서 대기
            
            while self.video_count < self.max_videos:
                self.video_count += 1
                self.log_print(f"\n🎬 === 강의 #{self.video_count} 학습 시작 ===")
                
                # 알림창 처리
                self.handle_alerts()
                
                # 영상 플레이어 준비
                video_element, _ = self.wait_for_video_ready()
                
                if not video_element:
                    self.log_print("❌ 강의 플레이어를 찾을 수 없습니다. 다음 강의로 이동...")
                    if not self.click_next_video():
                        self.log_print("❌ 더 이상 학습할 강의가 없습니다.")
                        break
                    continue
                
                # 영상 재생 상태 확인 및 시작
                self.start_video_if_paused(video_element)
                
                # 영상 재생 완료까지 실시간 모니터링
                success = self.wait_for_video_end(video_element)
                
                if success:
                    self.log_print(f"✅ 강의 #{self.video_count} 학습 완료!")
                else:
                    self.log_print(f"⚠️ 강의 #{self.video_count} 학습 중단됨")
                
                # 다음 영상으로 이동
                if not self.click_next_video():
                    self.log_print("❌ 더 이상 학습할 강의가 없습니다.")
                    break
                    
                # 잠시 대기
                time.sleep(3)
                
        except KeyboardInterrupt:
            self.log_print("\n⏹️ 사용자에 의해 중단되었습니다.")
        except Exception as e:
            self.log_print(f"❌ 학습 중 오류 발생: {str(e)}")
        finally:
            self.log_print(f"📊 총 학습한 강의 수: {self.video_count}개")
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.log_print("✅ 브라우저가 종료되었습니다.")

def main_with_args(url, count, headless=False, log_queue=None):
    """GUI에서 호출하는 함수"""
    def log_print(message):
        # GUI 큐로 로그 전달
        if log_queue:
            try:
                log_queue.put(message)
            except:
                pass
        
        # 터미널에도 출력
        print(message, flush=True)
        try:
            import sys
            sys.stdout.write(f"{message}\n")
            sys.stdout.flush()
        except:
            pass
    
    log_print("📚 스마트 학습 도우미")
    log_print("=" * 50)
    
    log_print(f"시작 URL: {url}")
    log_print(f"최대 학습 강의 수: {count}개")
    
    player = KTEduAutoPlayer(headless=headless, log_queue=log_queue)
    
    try:
        # 드라이버 설정 및 브라우저 열기
        log_print("🚀 브라우저를 실행하고 사이트에 접속합니다...")
        player.setup_driver()
        
        # 시작 URL로 이동
        log_print(f"📱 사이트 접속 중: {url}")
        try:
            player.driver.get(url)
            log_print("✅ 사이트 접속 완료!")
            time.sleep(3)
            
            # 페이지 로딩 확인
            log_print("🔍 페이지 로딩 상태 확인 중...")
            current_url = player.driver.current_url
            log_print(f"📍 현재 URL: {current_url}")
            
            # 페이지 제목 확인
            try:
                page_title = player.driver.title
                log_print(f"📄 페이지 제목: {page_title}")
            except Exception as e:
                log_print(f"⚠️ 페이지 제목 확인 실패: {str(e)}")
            
        except Exception as e:
            log_print(f"❌ 사이트 접속 실패: {str(e)}")
            raise
        
        # 사용자에게 로그인 안내
        log_print("\n" + "="*60)
        log_print("🔐 브라우저 창에서 KT EDU에 로그인해주세요!")
        log_print("📍 로그인 후 원하는 강의 페이지로 이동하세요.")
        log_print("✅ 준비가 완료되면 GUI에서 '로그인 완료' 버튼을 클릭하세요.")
        log_print("⏳ GUI에서 로그인 완료 신호를 기다리는 중...")
        log_print("="*60)
        
        # GUI에서 로그인 완료 신호를 기다림
        if log_queue:
            log_print("🔐 로그인 대기 상태 - GUI에서 '로그인 완료' 버튼을 클릭해주세요!")
            # GUI 모드에서는 큐를 통해 신호 대기
            while True:
                try:
                    time.sleep(0.1)
                    # 로그인 완료는 GUI에서 처리됨
                    # 브라우저가 살아있는지 확인
                    try:
                        current_url = player.driver.current_url
                        # 너무 자주 상태 확인하지 않도록 5초마다만 출력
                        if not hasattr(player, '_last_status_time') or time.time() - player._last_status_time > 5:
                            log_print(f"🔍 브라우저 상태 확인: {current_url}")
                            player._last_status_time = time.time()
                    except Exception as e:
                        log_print(f"❌ 브라우저 연결 끊어짐: {str(e)}")
                        break
                except Exception as e:
                    log_print(f"❌ 로그인 대기 중 오류: {str(e)}")
                    break
        
        log_print("\n🎬 자동재생을 시작합니다!")
        
        # 자동재생 시작 (현재 페이지에서)
        player.play_videos_automatically(start_url=None, max_videos=count)
        
    except KeyboardInterrupt:
        log_print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        log_print(f"❌ 오류 발생: {str(e)}")
    finally:
        player.close()

def main():
    """메인 실행 함수"""
    import argparse
    
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='KT EDU 자동재생기')
    parser.add_argument('--url', default='https://ktedu.kt.com/education/courseContents.do?classId=200094625_2025_0001_01', 
                       help='시작 URL')
    parser.add_argument('--count', type=int, default=100, 
                       help='최대 재생할 영상 수')
    parser.add_argument('--headless', action='store_true', 
                       help='헤드리스 모드로 실행')
    
    args = parser.parse_args()
    
    main_with_args(args.url, args.count, args.headless)

if __name__ == "__main__":
    main()
