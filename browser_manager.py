"""
브라우저 관리 모듈
Chrome 드라이버 설정 및 초기화를 담당합니다.
"""

import os
import sys
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
try:
    from webdriver_manager.chrome import ChromeDriverManager
    _WDM_AVAILABLE = True
except ImportError:
    _WDM_AVAILABLE = False

class BrowserManager:
    def __init__(self, headless=False, log_callback=None):
        """
        브라우저 관리자 초기화
        
        Args:
            headless (bool): 브라우저를 숨김 모드로 실행할지 여부
            log_callback (function): 로그 출력 콜백 함수
        """
        self.driver = None
        self.headless = headless
        self.log_callback = log_callback
        
    def log(self, message):
        """로그 출력"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def setup_driver(self):
        """Chrome 드라이버 설정 및 초기화"""
        self.log("🔧 ChromeDriver 설정 시작...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            self.log("👻 헤드리스 모드 활성화")
        
        # 일반적인 브라우저처럼 보이게 설정
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent 설정
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        
        # Wine 환경에서 Chrome 경로 설정
        if os.name == 'nt':  # Windows 환경 (Wine 포함)
            self._setup_chrome_path(chrome_options)
        
        self.log("✅ Chrome 옵션 설정 완료")
        
        # ChromeDriver 경로 설정
        chromedriver_path = self._get_chromedriver_path()
        
        # 1순위: webdriver-manager로 자동 다운로드/캐시 사용
        if _WDM_AVAILABLE:
            try:
                self.log("🔄 webdriver-manager로 현재 Chrome에 맞는 드라이버 자동 설치 중...")
                wdm_path = ChromeDriverManager().install()
                self.log(f"✅ 드라이버 경로: {wdm_path}")
                service = Service(wdm_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.log("✅ Chrome 브라우저 시작 완료! (webdriver-manager)")
                self._apply_stealth()
                return self.driver
            except Exception as e_wdm:
                self.log(f"⚠️ webdriver-manager 실패, 로컬 드라이버로 재시도: {str(e_wdm)}")

        # 2순위: 기존 로컬 chromedriver_140 사용
        try:
            self.log(f"🚀 로컬 ChromeDriver 서비스 시작: {chromedriver_path}")
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.log("✅ Chrome 브라우저 시작 완료! (로컬 드라이버)")
            self._apply_stealth()
            return self.driver
        except Exception as e:
            self.log(f"❌ 로컬 ChromeDriver 실행 실패: {str(e)}")
            self.log(f"📋 ChromeDriver 경로: {chromedriver_path}")
            self.log(f"📋 파일 존재 여부: {os.path.exists(chromedriver_path)}")
            if os.path.exists(chromedriver_path):
                self.log(f"📋 파일 권한: {oct(os.stat(chromedriver_path).st_mode)}")

        # 3순위: Selenium 내장 selenium-manager 폴백
        try:
            self.log("🔁 Selenium-manager로 ChromeDriver 자동 설치/사용 시도 중...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.log("✅ Chrome 브라우저 시작 완료! (selenium-manager)")
            self._apply_stealth()
            return self.driver
        except Exception as e3:
            self.log(f"❌ 모든 드라이버 시도 실패: {str(e3)}")
            raise
    
    def _setup_chrome_path(self, chrome_options):
        """Wine 환경에서 Chrome 경로 설정"""
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
                self.log(f"✅ Chrome 경로 설정: {chrome_path}")
                chrome_found = True
                break
        
        if not chrome_found:
            self.log("⚠️ Chrome을 찾을 수 없습니다. Wine 환경에 Chrome을 설치해주세요.")
            self.log("💡 해결방법: wine chrome_installer.exe 실행하여 Chrome 설치")
    
    def _get_chromedriver_path(self):
        """ChromeDriver 경로 반환"""
        if getattr(sys, 'frozen', False):
            # 실행파일인 경우: 임시 디렉토리에서 chromedriver 찾기
            return self._setup_executable_chromedriver()
        else:
            # 개발 환경인 경우
            chromedriver_path = os.path.join(os.getcwd(), 'chromedriver_140')
            self.log(f"🔍 개발 환경 ChromeDriver 경로: {chromedriver_path}")
            
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(f"ChromeDriver를 찾을 수 없습니다: {chromedriver_path}")
            
            # 실행 권한 확인 및 설정
            if not os.access(chromedriver_path, os.X_OK):
                os.chmod(chromedriver_path, 0o755)
                self.log("✅ ChromeDriver 실행 권한 설정 완료")
            
            return chromedriver_path
    
    def _setup_executable_chromedriver(self):
        """실행파일 모드에서 ChromeDriver 설정"""
        self.log("🔍 실행파일 모드에서 ChromeDriver 경로 설정 중...")
        
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        chromedriver_path = os.path.join(temp_dir, "chromedriver")
        self.log(f"📁 임시 디렉토리: {temp_dir}")
        
        # 실행파일 내부의 chromedriver를 임시 디렉토리로 복사
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 경우
            source_path = os.path.join(sys._MEIPASS, "chromedriver_140")
            self.log(f"📂 PyInstaller _MEIPASS: {sys._MEIPASS}")
        else:
            # 일반적인 경우
            source_path = "./chromedriver_140"
            self.log(f"📂 일반 경로: {source_path}")
        
        self.log(f"🔍 ChromeDriver 소스 경로: {source_path}")
        self.log(f"📋 소스 파일 존재 여부: {os.path.exists(source_path)}")
        
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, chromedriver_path)
                os.chmod(chromedriver_path, 0o755)
                self.log(f"✅ ChromeDriver 복사 완료: {chromedriver_path}")
            except Exception as e:
                self.log(f"❌ ChromeDriver 복사 실패: {str(e)}")
                raise
        else:
            # _MEIPASS 디렉토리 내용 확인
            if hasattr(sys, '_MEIPASS'):
                try:
                    meipass_contents = os.listdir(sys._MEIPASS)
                    self.log(f"📋 _MEIPASS 디렉토리 내용: {meipass_contents}")
                except:
                    self.log("❌ _MEIPASS 디렉토리 접근 실패")
            
            raise FileNotFoundError(f"ChromeDriver를 찾을 수 없습니다: {source_path}")
        
        return chromedriver_path
    
    def _apply_stealth(self):
        """자동화 탐지 회피 스크립트 실행"""
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log("🛡️ 자동화 탐지 회피 설정 완료")
        except Exception:
            pass

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.log("✅ 브라우저가 종료되었습니다.")
